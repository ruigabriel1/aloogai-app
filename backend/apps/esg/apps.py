"""Configuração do app de ESG e Sustentabilidade do Aloogaí."""

from django.apps import AppConfig


class EsgConfig(AppConfig):
    """Configuração do aplicativo de ESG, cálculo de CO₂ e gamificação."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.esg"
    verbose_name = "ESG e Sustentabilidade"

    def ready(self):
        """Registra os signals do app ESG ao iniciar."""
        import apps.esg.signals  # noqa: F401
