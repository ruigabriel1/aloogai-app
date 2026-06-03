"""Views do módulo de Notificações do Aloogaí."""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Notificacao
from .serializers import NotificacaoSerializer
from .services import NotificacaoService


class NotificacaoViewSet(ReadOnlyModelViewSet):
    """
    ViewSet de notificações do usuário autenticado.

    list: Lista todas as notificações (filtráveis por ?lida=true/false)
    retrieve: Detalhe de uma notificação
    marcar_lida: Marca uma notificação como lida
    marcar_todas_lidas: Marca todas como lidas
    nao_lidas_count: Retorna contagem de não lidas
    """

    serializer_class = NotificacaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Notificacao.objects.filter(
            usuario=self.request.user
        ).order_by('-created_at')

        # Filtro por lida
        lida = self.request.query_params.get('lida')
        if lida is not None:
            qs = qs.filter(lida=lida.lower() in ('true', '1', 'sim'))

        # Filtro por tipo
        tipo = self.request.query_params.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo.upper())

        return qs

    @action(detail=True, methods=['post'], url_path='marcar-lida')
    def marcar_lida(self, request, pk=None):
        """Marca uma notificação específica como lida."""
        NotificacaoService.marcar_como_lida(pk, request.user)
        return Response({'status': 'ok'})

    @action(detail=False, methods=['post'], url_path='marcar-todas-lidas')
    def marcar_todas_lidas(self, request):
        """Marca todas as notificações do usuário como lidas."""
        total = NotificacaoService.marcar_todas_como_lidas(request.user)
        return Response({'status': 'ok', 'total_marcadas': total})

    @action(detail=False, methods=['get'], url_path='nao-lidas')
    def nao_lidas_count(self, request):
        """Retorna a contagem de notificações não lidas."""
        count = Notificacao.objects.filter(
            usuario=request.user, lida=False
        ).count()
        return Response({'nao_lidas': count})
