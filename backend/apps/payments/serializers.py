"""Serializers do módulo de Pagamentos do Aloogaí."""

from rest_framework import serializers

from .models import ContaConectada, TransacaoStripe


class ContaConectadaSerializer(serializers.ModelSerializer):
    """Serializer para conta Stripe Connect do locador."""

    usuario_nome = serializers.CharField(
        source='usuario.get_full_name', read_only=True
    )

    class Meta:
        model = ContaConectada
        fields = [
            'id',
            'usuario',
            'usuario_nome',
            'stripe_account_id',
            'tipo_conta',
            'status_onboarding',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'stripe_account_id',
            'status_onboarding',
            'created_at',
        ]


class TransacaoStripeSerializer(serializers.ModelSerializer):
    """Serializer para transações Stripe (somente leitura)."""

    tipo_display = serializers.CharField(
        source='get_tipo_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = TransacaoStripe
        fields = [
            'id',
            'locacao',
            'tipo',
            'tipo_display',
            'stripe_payment_intent_id',
            'valor',
            'status',
            'status_display',
            'created_at',
        ]
        read_only_fields = fields


class OnboardingSerializer(serializers.Serializer):
    """Serializer para iniciar onboarding Stripe Connect."""

    onboarding_url = serializers.URLField(read_only=True)
    account_id = serializers.CharField(read_only=True)
