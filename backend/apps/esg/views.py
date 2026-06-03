"""Views do módulo ESG do Aloogaí."""

from django.db.models import Sum
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import HistoricoESG, SeloESG, UsuarioSelo
from .serializers import (
    DashboardESGSerializer,
    HistoricoESGSerializer,
    SeloESGSerializer,
    UsuarioSeloSerializer,
)


class DashboardESGView(APIView):
    """
    Dashboard ESG do usuário autenticado.

    Retorna: score atual, total de CO₂ economizado,
    selos desbloqueados e histórico recente.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user

        # Total de CO₂ economizado
        total_co2 = HistoricoESG.objects.filter(
            usuario=usuario
        ).aggregate(
            total=Sum('co2_economizado')
        )['total'] or 0.0

        # Locações concluídas
        from apps.rentals.models import Locacao
        total_locacoes = Locacao.objects.filter(
            locatario=usuario, status='CONCLUIDO'
        ).count()

        # Selos
        selos = UsuarioSelo.objects.filter(
            usuario=usuario
        ).select_related('selo').order_by('-desbloqueado_em')

        # Histórico recente (últimos 10)
        historico = HistoricoESG.objects.filter(
            usuario=usuario
        ).select_related(
            'locacao', 'locacao__item'
        ).order_by('-created_at')[:10]

        # Ranking (posição do usuário)
        from apps.users.models import Usuario
        ranking = Usuario.objects.filter(
            score_esg__gt=usuario.score_esg
        ).count() + 1

        data = {
            'score_esg': usuario.score_esg,
            'total_co2_economizado': total_co2,
            'total_locacoes_concluidas': total_locacoes,
            'selos': UsuarioSeloSerializer(selos, many=True).data,
            'historico_recente': HistoricoESGSerializer(historico, many=True).data,
            'ranking_posicao': ranking,
        }

        return Response(data)


class SelosListView(ListAPIView):
    """Lista todos os selos ecológicos disponíveis."""

    serializer_class = SeloESGSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SeloESG.objects.all().order_by('requisito_locacoes', 'requisito_score')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class HistoricoESGView(ListAPIView):
    """Lista o histórico completo de cálculos ESG do usuário."""

    serializer_class = HistoricoESGSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return HistoricoESG.objects.filter(
            usuario=self.request.user
        ).select_related(
            'locacao', 'locacao__item'
        ).order_by('-created_at')
