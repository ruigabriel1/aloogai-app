"""Admin do módulo de Pagamentos do Aloogaí."""

from django.contrib import admin

from .models import ContaConectada, TransacaoStripe


@admin.register(ContaConectada)
class ContaConectadaAdmin(admin.ModelAdmin):
    """Admin para contas Stripe Connect dos locadores."""

    list_display = [
        'usuario',
        'stripe_account_id',
        'tipo_conta',
        'status_onboarding',
        'created_at',
    ]
    list_filter = ['tipo_conta', 'status_onboarding']
    search_fields = [
        'usuario__first_name',
        'usuario__last_name',
        'usuario__email',
        'stripe_account_id',
    ]
    readonly_fields = ['stripe_account_id', 'created_at']
    raw_id_fields = ['usuario']


@admin.register(TransacaoStripe)
class TransacaoStripeAdmin(admin.ModelAdmin):
    """Admin para transações Stripe — somente leitura para dados sensíveis."""

    list_display = [
        'id_curto',
        'locacao',
        'tipo',
        'valor',
        'status',
        'created_at',
    ]
    list_filter = ['tipo', 'status', 'created_at']
    search_fields = [
        'stripe_payment_intent_id',
        'locacao__id',
    ]
    readonly_fields = [
        'stripe_payment_intent_id',
        'valor',
        'tipo',
        'status',
        'metadata',
        'created_at',
    ]
    raw_id_fields = ['locacao']

    def id_curto(self, obj):
        """Exibe os primeiros 8 caracteres do UUID."""
        return str(obj.id)[:8]
    id_curto.short_description = 'ID'

    def has_add_permission(self, request):
        """Transações são criadas apenas via código."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Transações nunca podem ser deletadas."""
        return False
