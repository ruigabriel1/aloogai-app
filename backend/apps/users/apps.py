from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Configuração do app de Usuários do Aloogaí."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Usuários'
