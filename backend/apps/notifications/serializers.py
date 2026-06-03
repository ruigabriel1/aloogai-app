"""Serializers do módulo de Notificações do Aloogaí."""

from rest_framework import serializers

from .models import Notificacao


class NotificacaoSerializer(serializers.ModelSerializer):
    """Serializer para notificações do usuário."""

    tipo_display = serializers.CharField(
        source='get_tipo_display', read_only=True
    )

    class Meta:
        model = Notificacao
        fields = [
            'id',
            'titulo',
            'mensagem',
            'tipo',
            'tipo_display',
            'lida',
            'dados_extras',
            'created_at',
        ]
        read_only_fields = fields
