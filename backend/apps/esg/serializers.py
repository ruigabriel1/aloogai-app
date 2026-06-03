"""Serializers do módulo ESG do Aloogaí."""

from rest_framework import serializers

from .models import FatorESGCategoria, HistoricoESG, SeloESG, UsuarioSelo


class SeloESGSerializer(serializers.ModelSerializer):
    """Serializer para selos ecológicos."""

    desbloqueado = serializers.SerializerMethodField()

    class Meta:
        model = SeloESG
        fields = [
            'id',
            'nome',
            'descricao',
            'icone',
            'requisito_locacoes',
            'requisito_score',
            'desbloqueado',
        ]

    def get_desbloqueado(self, obj):
        """Verifica se o usuário atual desbloqueou este selo."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UsuarioSelo.objects.filter(
                usuario=request.user, selo=obj
            ).exists()
        return False


class UsuarioSeloSerializer(serializers.ModelSerializer):
    """Serializer para selos desbloqueados pelo usuário."""

    selo = SeloESGSerializer(read_only=True)

    class Meta:
        model = UsuarioSelo
        fields = ['selo', 'desbloqueado_em']


class HistoricoESGSerializer(serializers.ModelSerializer):
    """Serializer para histórico de cálculos ESG."""

    item_titulo = serializers.CharField(
        source='locacao.item.titulo', read_only=True
    )

    class Meta:
        model = HistoricoESG
        fields = [
            'id',
            'locacao',
            'item_titulo',
            'co2_economizado',
            'score_anterior',
            'score_novo',
            'created_at',
        ]


class DashboardESGSerializer(serializers.Serializer):
    """Serializer para o dashboard ESG do usuário."""

    score_esg = serializers.FloatField()
    total_co2_economizado = serializers.FloatField()
    total_locacoes_concluidas = serializers.IntegerField()
    selos = UsuarioSeloSerializer(many=True)
    historico_recente = HistoricoESGSerializer(many=True)
    ranking_posicao = serializers.IntegerField(required=False)
