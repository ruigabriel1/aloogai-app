"""
Configuração do Django Admin para o app de Chat.

Registra SalaChat e Mensagem no painel administrativo.
"""

from django.contrib import admin

from apps.chat.models import Mensagem, SalaChat


@admin.register(SalaChat)
class SalaChatAdmin(admin.ModelAdmin):
    """Administração de Salas de Chat."""

    list_display = (
        "id",
        "locacao",
        "locador",
        "locatario",
        "ativa",
        "chat_permitido",
        "created_at",
    )
    list_filter = ("ativa", "created_at")
    search_fields = (
        "locacao__id",
        "locador__email",
        "locatario__email",
    )
    readonly_fields = ("id", "created_at", "chat_permitido")
    raw_id_fields = ("locacao", "locador", "locatario")

    @admin.display(boolean=True, description="Chat Permitido")
    def chat_permitido(self, obj):
        """Exibe se o chat está permitido com base no status da locação."""
        return obj.chat_permitido


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    """Administração de Mensagens de Chat."""

    list_display = (
        "id",
        "sala",
        "remetente",
        "tipo",
        "lida_em",
        "created_at",
    )
    list_filter = ("tipo", "created_at")
    search_fields = (
        "sala__id",
        "remetente__email",
    )
    readonly_fields = ("id", "created_at")
    raw_id_fields = ("sala", "remetente")

    # Não exibir conteúdo da mensagem no admin por segurança
    exclude = ("conteudo",)
