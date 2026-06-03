"""
Modelos do app de Notificações do Aloogaí.

Implementa notificações persistentes para diversos eventos do sistema:
locações, chat, pagamentos, ESG e alertas do sistema.
"""

import uuid

from django.db import models


class Notificacao(models.Model):
    """
    Notificação enviada a um usuário.

    Modelo genérico para todos os tipos de notificação do sistema.
    As notificações podem ser filtradas por tipo e status de leitura.
    O campo dados_extras permite armazenar contexto adicional em JSON
    (ex: ID da locação, nome do item, etc).
    """

    class TipoNotificacao(models.TextChoices):
        """Tipos de notificação suportados pelo sistema."""

        LOCACAO = "LOCACAO", "Locação"
        CHAT = "CHAT", "Chat"
        PAGAMENTO = "PAGAMENTO", "Pagamento"
        ESG = "ESG", "ESG"
        SISTEMA = "SISTEMA", "Sistema"

    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["usuario", "-created_at"],
                name="idx_notif_usuario_created",
            ),
            models.Index(
                fields=["usuario", "lida"],
                name="idx_notif_usuario_lida",
            ),
        ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    usuario = models.ForeignKey(
        "users.Usuario",
        on_delete=models.CASCADE,
        related_name="notificacoes",
        verbose_name="Usuário",
    )
    titulo = models.CharField(
        max_length=200,
        verbose_name="Título",
        help_text="Título resumido da notificação.",
    )
    mensagem = models.TextField(
        verbose_name="Mensagem",
        help_text="Corpo detalhado da notificação.",
    )
    tipo = models.CharField(
        max_length=15,
        choices=TipoNotificacao.choices,
        default=TipoNotificacao.SISTEMA,
        verbose_name="Tipo",
        help_text="Categoria da notificação para filtragem.",
    )
    lida = models.BooleanField(
        default=False,
        verbose_name="Lida",
        help_text="Indica se a notificação foi lida pelo usuário.",
    )
    dados_extras = models.JSONField(
        null=True,
        blank=True,
        default=None,
        verbose_name="Dados Extras",
        help_text=(
            "Dados adicionais em JSON para contexto da notificação "
            "(ex: {'locacao_id': 'uuid', 'item_titulo': '...'})."
        ),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    def marcar_como_lida(self):
        """Marca a notificação como lida."""
        if not self.lida:
            self.lida = True
            self.save(update_fields=["lida"])

    def __str__(self):
        status = "✓" if self.lida else "●"
        return f"{status} [{self.tipo}] {self.titulo}"
