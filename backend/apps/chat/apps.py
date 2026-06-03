"""Configuração do app de Chat do Aloogaí."""

from django.apps import AppConfig


class ChatConfig(AppConfig):
    """Configuração do aplicativo de chat em tempo real."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.chat"
    verbose_name = "Chat"

    def ready(self):
        """Registra os signals do app de chat."""
        import apps.chat.signals  # noqa: F401
