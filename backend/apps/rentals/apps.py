"""
Configuração do app Locações (rentals).

Registra o app Django responsável pelo ciclo de vida completo
das locações: FSM de status, timeline e regras de negócio.
"""
from django.apps import AppConfig


class RentalsConfig(AppConfig):
    """Configuração do app de Locações."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.rentals"
    verbose_name = "Locações"

    def ready(self):
        """Importa signals ao inicializar o app."""
        import apps.rentals.signals  # noqa: F401
