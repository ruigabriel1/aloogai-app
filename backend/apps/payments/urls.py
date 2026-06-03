"""URLs do módulo de Pagamentos do Aloogaí."""

from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    # Onboarding Stripe Connect
    path(
        'onboarding/',
        views.OnboardingView.as_view(),
        name='onboarding',
    ),

    # Transações de uma locação
    path(
        'transacoes/<uuid:locacao_id>/',
        views.TransacoesLocacaoView.as_view(),
        name='transacoes-locacao',
    ),

    # Webhook Stripe (chamado pelo Stripe, não pelo app)
    path(
        'webhooks/stripe/',
        views.StripeWebhookView.as_view(),
        name='stripe-webhook',
    ),
]
