from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """Configuração do app de Catálogo do Aloogaí."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.catalog'
    verbose_name = 'Catálogo'
