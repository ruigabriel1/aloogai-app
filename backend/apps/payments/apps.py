"""
Configuração do app Pagamentos (payments).

Registra o app Django responsável pela integração com Stripe Connect,
transações financeiras, pré-autorizações e split de pagamentos.
"""
from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """Configuração do app de Pagamentos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.payments"
    verbose_name = "Pagamentos"
