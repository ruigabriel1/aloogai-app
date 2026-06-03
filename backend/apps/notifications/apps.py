"""Configuração do app de Notificações do Aloogaí."""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Configuração do aplicativo de notificações push e e-mail."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    verbose_name = "Notificações"
