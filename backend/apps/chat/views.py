"""
Views do app de Chat do Aloogaí.

Implementa os ViewSets REST para histórico de chat (fallback HTTP)
e criação de mensagens. O acesso ao chat é condicionado ao status
da locação (>= SOLICITADO).
"""

from django.db.models import Q
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.chat.models import Mensagem, SalaChat, STATUS_ORDEM, STATUS_MINIMO_CHAT
from apps.chat.serializers import (
    MensagemCreateSerializer,
    MensagemSerializer,
    SalaChatSerializer,
)


class SalaChatViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para salas de chat do usuário autenticado.

    Endpoints:
        GET /api/v1/chat/salas/ — Lista salas do usuário
        GET /api/v1/chat/salas/{id}/ — Detalhe de uma sala
    """

    serializer_class = SalaChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        """
        Retorna salas de chat do usuário autenticado.

        Filtra salas onde o usuário é locador ou locatário.
        """
        usuario = self.request.user
        return (
            SalaChat.objects.filter(
                Q(locador=usuario) | Q(locatario=usuario)
            )
            .select_related("locacao", "locador", "locatario")
            .order_by("-created_at")
        )


class MensagemViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para mensagens de chat.

    Endpoints:
        GET /api/v1/chat/salas/{sala_id}/mensagens/ — Histórico paginado
        POST /api/v1/chat/salas/{sala_id}/mensagens/ — Enviar mensagem

    O acesso é validado: o usuário deve pertencer à sala e o chat
    deve estar permitido (Locacao.status >= SOLICITADO).
    """

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_serializer_class(self):
        """Retorna o serializer adequado para a ação."""
        if self.action == "create":
            return MensagemCreateSerializer
        return MensagemSerializer

    def get_queryset(self):
        """
        Retorna mensagens da sala especificada na URL.

        Valida que o usuário pertence à sala antes de retornar
        as mensagens.
        """
        sala_id = self.kwargs.get("sala_id")
        usuario = self.request.user

        return Mensagem.objects.filter(
            sala_id=sala_id,
            sala__locador=usuario,
        ) | Mensagem.objects.filter(
            sala_id=sala_id,
            sala__locatario=usuario,
        )

    def get_serializer_context(self):
        """Adiciona o request ao contexto do serializer."""
        context = super().get_serializer_context()
        return context

    def perform_create(self, serializer):
        """
        Cria mensagem validando acesso à sala.

        A validação do chat_permitido é feita no serializer.
        """
        sala_id = self.kwargs.get("sala_id")

        try:
            sala = SalaChat.objects.get(id=sala_id)
        except SalaChat.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Sala de chat não encontrada.")

        if not sala.usuario_pertence(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Você não tem permissão para enviar mensagens nesta sala."
            )

        if not sala.chat_permitido:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "O chat não está habilitado para esta locação. "
                "O chat só é acessível após uma solicitação de locação."
            )

        serializer.save(sala=sala, remetente=self.request.user)

    @action(detail=False, methods=["post"], url_path="marcar-lidas")
    def marcar_lidas(self, request, sala_id=None):
        """
        Marca todas as mensagens não lidas da sala como lidas.

        Endpoint: POST /api/v1/chat/salas/{sala_id}/mensagens/marcar-lidas/
        """
        from django.utils import timezone

        usuario = request.user
        mensagens_atualizadas = Mensagem.objects.filter(
            sala_id=sala_id,
            lida_em__isnull=True,
        ).exclude(
            remetente=usuario,
        ).update(
            lida_em=timezone.now(),
        )

        return Response(
            {
                "mensagem": f"{mensagens_atualizadas} mensagem(ns) marcada(s) como lida(s).",
                "total": mensagens_atualizadas,
            },
            status=status.HTTP_200_OK,
        )
