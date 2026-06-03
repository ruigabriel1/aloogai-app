"""
WebSocket Consumer do app de Chat do Aloogaí.

Implementa o ChatConsumer (AsyncWebsocketConsumer) para comunicação
em tempo real entre locador e locatário via Django Channels.

O canal utiliza o padrão: chat_{locacao_id}
"""

import json
import logging
from uuid import UUID

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket para chat em tempo real.

    Fluxo:
        1. connect: Autentica via JWT (query string), verifica acesso à sala
        2. receive: Parseia JSON, salva mensagem no DB, broadcast para sala
        3. disconnect: Remove do grupo do canal

    O nome do grupo é: chat_{locacao_id}
    """

    async def connect(self):
        """
        Estabelece conexão WebSocket.

        Autentica o usuário via JWT no query string, verifica se
        pertence à sala de chat e se o chat está permitido.
        """
        self.locacao_id = self.scope["url_route"]["kwargs"]["locacao_id"]
        self.room_group_name = f"chat_{self.locacao_id}"

        # Usuário é injetado pelo middleware JWT de WebSocket
        self.user = self.scope.get("user", None)

        if not self.user or self.user.is_anonymous:
            logger.warning(
                "Tentativa de conexão WebSocket sem autenticação — "
                "locação %s",
                self.locacao_id,
            )
            await self.close(code=4001)
            return

        # Verificar se o usuário pertence à sala e se o chat é permitido
        sala = await self._obter_sala()
        if sala is None:
            logger.warning(
                "Sala de chat não encontrada para locação %s",
                self.locacao_id,
            )
            await self.close(code=4004)
            return

        if not await self._verificar_acesso(sala):
            logger.warning(
                "Acesso negado ao chat — usuário %s, locação %s",
                self.user.id,
                self.locacao_id,
            )
            await self.close(code=4003)
            return

        self.sala_id = str(sala.id)

        # Entrar no grupo do canal
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        logger.info(
            "WebSocket conectado — usuário %s na sala %s",
            self.user.id,
            self.sala_id,
        )

    async def disconnect(self, close_code):
        """
        Desconecta do WebSocket e sai do grupo do canal.

        Args:
            close_code: Código de fechamento da conexão.
        """
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

        logger.info(
            "WebSocket desconectado — código %s, sala %s",
            close_code,
            getattr(self, "sala_id", "desconhecida"),
        )

    async def receive(self, text_data):
        """
        Recebe dados do WebSocket e roteia para a ação correta.

        Ações suportadas:
            - "mensagem" (default): Envia mensagem de chat
            - "digitando": Indica que o usuário está digitando
            - "marcar_lida": Marca mensagens como lidas

        Formato esperado do JSON:
        {
            "acao": "mensagem",  # mensagem | digitando | marcar_lida
            "conteudo": "Texto da mensagem",
            "tipo": "TEXTO"  # TEXTO | IMAGEM | SISTEMA
        }

        Args:
            text_data: String JSON com os dados.
        """
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "erro": "Formato JSON inválido.",
            }))
            return

        acao = data.get("acao", "mensagem")

        if acao == "digitando":
            await self._handle_digitando()
        elif acao == "marcar_lida":
            await self._handle_marcar_lida()
        elif acao == "mensagem":
            await self._handle_mensagem(data)
        else:
            await self.send(text_data=json.dumps({
                "erro": f"Ação desconhecida: {acao}",
            }))

    async def _handle_mensagem(self, data):
        """Processa envio de mensagem de chat."""
        conteudo = data.get("conteudo", "").strip()
        tipo = data.get("tipo", "TEXTO")

        if not conteudo:
            await self.send(text_data=json.dumps({
                "erro": "Conteúdo da mensagem não pode ser vazio.",
            }))
            return

        if tipo not in ("TEXTO", "IMAGEM", "SISTEMA"):
            await self.send(text_data=json.dumps({
                "erro": f"Tipo de mensagem inválido: {tipo}",
            }))
            return

        # Salvar mensagem no banco de dados
        mensagem = await self._salvar_mensagem(conteudo, tipo)

        if mensagem is None:
            await self.send(text_data=json.dumps({
                "erro": "Erro ao salvar mensagem. Chat pode estar desabilitado.",
            }))
            return

        # Broadcast para todos os membros do grupo
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "mensagem": {
                    "id": str(mensagem.id),
                    "sala_id": self.sala_id,
                    "remetente_id": str(self.user.id),
                    "conteudo": conteudo,  # Enviar texto limpo pelo WS
                    "tipo": tipo,
                    "created_at": mensagem.created_at.isoformat(),
                },
            },
        )

    async def _handle_digitando(self):
        """
        Broadcast do evento 'digitando' para os outros participantes.

        Não persiste no banco — é um evento efêmero.
        """
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_digitando",
                "usuario_id": str(self.user.id),
            },
        )

    async def _handle_marcar_lida(self):
        """Marca todas as mensagens não lidas como lidas para o usuário."""
        total = await self._marcar_mensagens_lidas()
        await self.send(text_data=json.dumps({
            "acao": "lidas_atualizadas",
            "total": total,
        }))

    async def chat_message(self, event):
        """
        Envia mensagem para o WebSocket do cliente.

        Handler chamado quando o grupo recebe um broadcast.

        Args:
            event: Dicionário com os dados da mensagem.
        """
        await self.send(text_data=json.dumps(
            event["mensagem"],
            ensure_ascii=False,
        ))

    async def chat_digitando(self, event):
        """
        Envia evento 'digitando' para o WebSocket do cliente.

        Só envia para o outro participante (não para quem está digitando).
        """
        if event["usuario_id"] != str(self.user.id):
            await self.send(text_data=json.dumps({
                "acao": "digitando",
                "usuario_id": event["usuario_id"],
            }))


    # =========================================================================
    # Métodos auxiliares (acesso ao banco via database_sync_to_async)
    # =========================================================================

    @database_sync_to_async
    def _obter_sala(self):
        """
        Busca a sala de chat associada à locação.

        Retorna:
            SalaChat ou None se não encontrada.
        """
        from apps.chat.models import SalaChat

        try:
            return SalaChat.objects.select_related(
                "locacao", "locador", "locatario"
            ).get(locacao_id=self.locacao_id)
        except SalaChat.DoesNotExist:
            return None

    @database_sync_to_async
    def _verificar_acesso(self, sala):
        """
        Verifica se o usuário tem acesso à sala e se o chat é permitido.

        Args:
            sala: Instância de SalaChat.

        Retorna:
            bool: True se o acesso é permitido.
        """
        return sala.usuario_pertence(self.user) and sala.chat_permitido

    @database_sync_to_async
    def _salvar_mensagem(self, conteudo, tipo):
        """
        Salva a mensagem no banco de dados.

        Args:
            conteudo: Texto da mensagem.
            tipo: Tipo da mensagem (TEXTO, IMAGEM, SISTEMA).

        Retorna:
            Mensagem criada ou None se houver erro.
        """
        from apps.chat.models import Mensagem, SalaChat

        try:
            sala = SalaChat.objects.get(id=self.sala_id)

            if not sala.chat_permitido:
                return None

            return Mensagem.objects.create(
                sala=sala,
                remetente=self.user,
                conteudo=conteudo,
                tipo=tipo,
            )
        except Exception as e:
            logger.error(
                "Erro ao salvar mensagem na sala %s: %s",
                self.sala_id,
                str(e),
            )
            return None

    @database_sync_to_async
    def _marcar_mensagens_lidas(self):
        """
        Marca todas as mensagens não lidas da sala como lidas.

        Marca apenas mensagens enviadas pelo OUTRO participante,
        não as do próprio usuário.

        Retorna:
            int: Quantidade de mensagens marcadas como lidas.
        """
        from apps.chat.models import Mensagem
        from django.utils import timezone

        return Mensagem.objects.filter(
            sala_id=self.sala_id,
            lida_em__isnull=True,
        ).exclude(
            remetente=self.user,
        ).update(
            lida_em=timezone.now(),
        )
