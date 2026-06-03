"""
Serviço de notificações do Aloogaí.

Centraliza a criação de notificações para todos os módulos do sistema.
Futuramente integrará com Firebase Cloud Messaging (FCM) para push.
"""

import logging

logger = logging.getLogger(__name__)


class NotificacaoService:
    """Serviço centralizado para criação e envio de notificações."""

    @staticmethod
    def criar_notificacao(usuario, titulo, mensagem, tipo, dados_extras=None):
        """
        Cria uma notificação no banco de dados.

        Args:
            usuario: Instância do Usuario destinatário
            titulo: Título curto da notificação
            mensagem: Corpo da mensagem
            tipo: Tipo (LOCACAO, CHAT, PAGAMENTO, ESG, SISTEMA)
            dados_extras: Dict com dados adicionais (opcional)

        Returns:
            Notificacao: Instância criada
        """
        from apps.notifications.models import Notificacao

        notificacao = Notificacao.objects.create(
            usuario=usuario,
            titulo=titulo,
            mensagem=mensagem,
            tipo=tipo,
            dados_extras=dados_extras or {},
        )

        logger.info(
            'Notificação criada: [%s] "%s" para %s',
            tipo, titulo, usuario.get_full_name()
        )

        # TODO: Integrar com FCM para push notification
        # NotificacaoService._enviar_push(usuario, titulo, mensagem, dados_extras)

        return notificacao

    @staticmethod
    def notificar_nova_locacao(locacao):
        """Notifica o locador sobre uma nova solicitação de locação."""
        return NotificacaoService.criar_notificacao(
            usuario=locacao.item.locador,
            titulo='📦 Nova solicitação de aluguel!',
            mensagem=(
                f'{locacao.locatario.get_full_name()} quer alugar '
                f'"{locacao.item.titulo}" de {locacao.data_inicio} '
                f'a {locacao.data_fim}.'
            ),
            tipo='LOCACAO',
            dados_extras={
                'locacao_id': str(locacao.id),
                'item_id': str(locacao.item.id),
            },
        )

    @staticmethod
    def notificar_status_locacao(locacao, status_anterior):
        """Notifica o locatário sobre mudança de status da locação."""
        mensagens = {
            'CAUCAO_RETIDA': '💳 Caução retida com sucesso! Aguardando entrega.',
            'ATIVO': '✅ Item entregue! Aproveite sua locação.',
            'DEVOLVIDO': '📥 Devolução registrada. Aguardando vistoria.',
            'CONCLUIDO': '🎉 Locação concluída com sucesso!',
            'CONTESTADO': '⚠️ Uma disputa foi aberta nesta locação.',
            'CANCELADO': '❌ Locação cancelada.',
        }

        mensagem = mensagens.get(
            locacao.status,
            f'Status atualizado para {locacao.get_status_display()}.'
        )

        return NotificacaoService.criar_notificacao(
            usuario=locacao.locatario,
            titulo=f'Atualização: {locacao.item.titulo}',
            mensagem=mensagem,
            tipo='LOCACAO',
            dados_extras={
                'locacao_id': str(locacao.id),
                'status': locacao.status,
                'status_anterior': status_anterior,
            },
        )

    @staticmethod
    def notificar_nova_mensagem(mensagem_chat):
        """Notifica o destinatário de uma nova mensagem no chat."""
        # Determinar o destinatário (quem não enviou a mensagem)
        sala = mensagem_chat.sala
        if mensagem_chat.remetente == sala.locador:
            destinatario = sala.locatario
        else:
            destinatario = sala.locador

        return NotificacaoService.criar_notificacao(
            usuario=destinatario,
            titulo=f'💬 Nova mensagem de {mensagem_chat.remetente.first_name}',
            mensagem=mensagem_chat.conteudo[:100],
            tipo='CHAT',
            dados_extras={
                'sala_id': str(sala.id),
                'locacao_id': str(sala.locacao.id),
                'remetente_id': str(mensagem_chat.remetente.id),
            },
        )

    @staticmethod
    def marcar_como_lida(notificacao_id, usuario):
        """Marca uma notificação específica como lida."""
        from apps.notifications.models import Notificacao

        return Notificacao.objects.filter(
            id=notificacao_id, usuario=usuario, lida=False
        ).update(lida=True)

    @staticmethod
    def marcar_todas_como_lidas(usuario):
        """Marca todas as notificações do usuário como lidas."""
        from apps.notifications.models import Notificacao

        return Notificacao.objects.filter(
            usuario=usuario, lida=False
        ).update(lida=True)
