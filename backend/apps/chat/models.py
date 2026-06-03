"""
Modelos do app de Chat do Aloogaí.

Implementa salas de chat vinculadas a locações e mensagens com
criptografia AES-256 em repouso. O chat só é habilitado após uma
solicitação de locação (status >= SOLICITADO), conforme regra
comportamental #3 do gemini.md.
"""

import base64
import uuid

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# Campo Criptografado (AES-256 via Fernet — symmetric encryption)
# =============================================================================


def _get_fernet():
    """
    Retorna instância do Fernet usando a chave de criptografia do settings.

    A chave CHAT_ENCRYPTION_KEY deve ser uma chave Fernet válida (base64 de
    32 bytes), armazenada em variável de ambiente.
    """
    key = getattr(settings, "CHAT_ENCRYPTION_KEY", None)
    if not key:
        raise ValueError(
            "CHAT_ENCRYPTION_KEY não configurada nas variáveis de ambiente. "
            "Gere uma chave com: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    if isinstance(key, str):
        key = key.encode("utf-8")
    return Fernet(key)


class CampoEncriptado(models.TextField):
    """
    Campo de texto que armazena dados criptografados com AES-256 (Fernet).

    Os dados são criptografados antes de salvar no banco e descriptografados
    ao serem lidos. Garante proteção dos conteúdos das mensagens em repouso.
    """

    description = "Campo de texto criptografado com AES-256 (Fernet)"

    def get_prep_value(self, value):
        """Criptografa o valor antes de salvar no banco de dados."""
        if value is None:
            return value
        f = _get_fernet()
        valor_bytes = value.encode("utf-8") if isinstance(value, str) else value
        return f.encrypt(valor_bytes).decode("utf-8")

    def from_db_value(self, value, expression, connection):
        """Descriptografa o valor ao ler do banco de dados."""
        if value is None:
            return value
        f = _get_fernet()
        try:
            return f.decrypt(value.encode("utf-8")).decode("utf-8")
        except Exception:
            # Se falhar na descriptografia, retorna valor original
            # (pode acontecer com dados legados ou corrompidos)
            return value

    def value_from_object(self, obj):
        """Retorna o valor descriptografado do objeto."""
        value = super().value_from_object(obj)
        return value


# =============================================================================
# Status da Locação — Constantes para validação de acesso ao chat
# =============================================================================

# Ordem dos status do FSM para comparação
STATUS_ORDEM = {
    "SOLICITADO": 1,
    "CAUCAO_RETIDA": 2,
    "ATIVO": 3,
    "DEVOLVIDO": 4,
    "CONCLUIDO": 5,
    "CONTESTADO": 6,
    "CANCELADO": 0,
}

# Status mínimo para habilitar o chat
STATUS_MINIMO_CHAT = "SOLICITADO"


# =============================================================================
# Modelos
# =============================================================================


class SalaChat(models.Model):
    """
    Sala de chat vinculada a uma locação.

    Cada locação possui exatamente uma sala de chat (OneToOne).
    O chat só é acessível quando a locação tem status >= SOLICITADO.
    """

    class Meta:
        verbose_name = "Sala de Chat"
        verbose_name_plural = "Salas de Chat"
        ordering = ["-created_at"]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    locacao = models.OneToOneField(
        "rentals.Locacao",
        on_delete=models.CASCADE,
        related_name="sala_chat",
        verbose_name="Locação",
        help_text="Locação vinculada a esta sala de chat.",
    )
    locador = models.ForeignKey(
        "users.Usuario",
        on_delete=models.CASCADE,
        related_name="salas_como_locador",
        verbose_name="Locador",
        help_text="Proprietário do item locado.",
    )
    locatario = models.ForeignKey(
        "users.Usuario",
        on_delete=models.CASCADE,
        related_name="salas_como_locatario",
        verbose_name="Locatário",
        help_text="Pessoa que alugou o item.",
    )
    ativa = models.BooleanField(
        default=True,
        verbose_name="Ativa",
        help_text="Indica se a sala de chat está ativa para troca de mensagens.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    @property
    def chat_permitido(self):
        """
        Verifica se o chat é permitido com base no status da locação.

        Regra comportamental #3 do gemini.md:
        O chat entre locador e locatário só é habilitado APÓS uma
        solicitação de locação (Locacao.status >= SOLICITADO).

        Retorna:
            bool: True se o status da locação permite chat.
        """
        if not self.ativa:
            return False

        status_locacao = self.locacao.status
        ordem_atual = STATUS_ORDEM.get(status_locacao, -1)
        ordem_minima = STATUS_ORDEM.get(STATUS_MINIMO_CHAT, 1)

        return ordem_atual >= ordem_minima

    def usuario_pertence(self, usuario):
        """
        Verifica se um usuário é participante desta sala de chat.

        Args:
            usuario: Instância do modelo Usuario.

        Retorna:
            bool: True se o usuário é locador ou locatário.
        """
        return usuario.id in (self.locador_id, self.locatario_id)

    def __str__(self):
        return f"Chat — Locação {self.locacao_id}"


class Mensagem(models.Model):
    """
    Mensagem enviada em uma sala de chat.

    O conteúdo da mensagem é criptografado em repouso usando AES-256
    (Fernet) para garantir privacidade das conversas.
    """

    class TipoMensagem(models.TextChoices):
        """Tipos de mensagem suportados."""

        TEXTO = "TEXTO", "Texto"
        IMAGEM = "IMAGEM", "Imagem"
        SISTEMA = "SISTEMA", "Sistema"

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["sala", "created_at"],
                name="idx_msg_sala_created",
            ),
        ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    sala = models.ForeignKey(
        SalaChat,
        on_delete=models.CASCADE,
        related_name="mensagens",
        verbose_name="Sala de Chat",
    )
    remetente = models.ForeignKey(
        "users.Usuario",
        on_delete=models.CASCADE,
        related_name="mensagens_enviadas",
        verbose_name="Remetente",
    )
    conteudo = CampoEncriptado(
        verbose_name="Conteúdo",
        help_text="Conteúdo da mensagem (criptografado em repouso).",
    )
    tipo = models.CharField(
        max_length=10,
        choices=TipoMensagem.choices,
        default=TipoMensagem.TEXTO,
        verbose_name="Tipo",
    )
    lida_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Lida em",
        help_text="Data/hora em que a mensagem foi lida pelo destinatário.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    def marcar_como_lida(self):
        """Marca a mensagem como lida com o timestamp atual."""
        if self.lida_em is None:
            self.lida_em = timezone.now()
            self.save(update_fields=["lida_em"])

    def __str__(self):
        return f"Msg de {self.remetente_id} em {self.sala_id} ({self.tipo})"
