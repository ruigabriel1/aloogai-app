"""
Views do app de Locações.

ViewSet principal para CRUD de locações com ações customizadas
para cada transição de status da FSM.

Ações disponíveis:
    - create: Criar nova locação (com pré-autorização Stripe)
    - list: Listar locações do usuário autenticado
    - retrieve: Detalhar uma locação
    - confirmar_entrega: CAUCAO_RETIDA → ATIVO
    - confirmar_devolucao: ATIVO → DEVOLVIDO
    - concluir: DEVOLVIDO → CONCLUIDO
    - contestar: (estado ativo) → CONTESTADO
    - cancelar: SOLICITADO → CANCELADO
"""
import logging

from django.db import transaction
from django.db.models import Q
from django_fsm import TransitionNotAllowed
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.payments.services import StripeService
from apps.rentals.models import Locacao, StatusLocacao
from apps.rentals.serializers import (
    LocacaoCreateSerializer,
    LocacaoDetailSerializer,
    LocacaoListSerializer,
    TransicaoSerializer,
)

logger = logging.getLogger(__name__)


class LocacaoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de Locações.

    Permissões:
        - Apenas usuários autenticados podem acessar.
        - Cada usuário só vê suas próprias locações
          (como locatário ou locador).
    """

    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        """Retorna o serializer adequado para cada ação."""
        if self.action == "create":
            return LocacaoCreateSerializer
        if self.action == "list":
            return LocacaoListSerializer
        return LocacaoDetailSerializer

    def get_queryset(self):
        """Retorna locações onde o usuário é locador ou locatário."""
        user = self.request.user
        qs = Locacao.objects.all()

        tipo = self.request.query_params.get('tipo', None)
        if tipo == 'locatario':
            qs = qs.filter(locatario=user)
        elif tipo == 'locador':
            qs = qs.filter(item__locador=user)
        else:
            qs = qs.filter(Q(locatario=user) | Q(item__locador=user))

        return qs.select_related('item', 'item__locador', 'locatario').prefetch_related("timeline")

    @transaction.atomic
    def perform_create(self, serializer):
        """
        Cria a locação e inicia o fluxo de pré-autorização Stripe.

        Fluxo:
            1. Salva a locação com status SOLICITADO
            2. Chama StripeService.criar_pre_autorizacao()
            3. Salva payment_intent_id na locação
            4. Transiciona para CAUCAO_RETIDA
        """
        locacao = serializer.save()
        logger.info(
            "Locação %s criada: item=%s, locatário=%s",
            locacao.id,
            locacao.item_id,
            locacao.locatario_id,
        )

        try:
            resultado = StripeService.criar_pre_autorizacao(locacao)

            # Atualizar locação com dados do Stripe
            locacao.payment_intent_id = resultado['payment_intent_id']

            # Transicionar FSM: SOLICITADO → CAUCAO_RETIDA
            locacao.reter_caucao(
                caucao_auth_id=resultado['payment_intent_id']
            )
            locacao.save()

            logger.info(
                "Locação %s: pré-autorização criada e caução retida (PI: %s)",
                locacao.id,
                resultado['payment_intent_id'],
            )
        except Exception as e:
            logger.error(
                "Erro na pré-autorização da locação %s: %s",
                locacao.id, str(e)
            )
            # A locação permanece como SOLICITADO para retry
            # O locatário verá o status e poderá tentar novamente

    # ──────────────────────────────────────────────────────────
    # Ações de transição FSM
    # ──────────────────────────────────────────────────────────

    def _executar_transicao(self, request, pk, metodo_transicao: str, descricao: str):
        """
        Método auxiliar para executar transições FSM com tratamento de erros.

        Args:
            request: Request DRF.
            pk: ID da locação.
            metodo_transicao: Nome do método de transição no modelo.
            descricao: Descrição da ação para logs e mensagens.

        Returns:
            Response com os dados atualizados ou erro.
        """
        locacao = self.get_object()
        serializer = TransicaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        observacao = serializer.validated_data.get("observacao", "")

        try:
            # Chamar o método de transição
            metodo = getattr(locacao, metodo_transicao)
            if metodo_transicao == "contestar":
                metodo(observacao=observacao)
            elif metodo_transicao == "reter_caucao":
                metodo(caucao_auth_id=request.data.get("caucao_auth_id", ""))
            else:
                metodo()

            locacao.save()
            logger.info(
                "Locação %s: %s executado por %s",
                locacao.id,
                descricao,
                request.user.id,
            )
            return Response(
                LocacaoDetailSerializer(locacao).data,
                status=status.HTTP_200_OK,
            )

        except TransitionNotAllowed:
            logger.warning(
                "Transição inválida em locação %s: %s (status atual: %s)",
                locacao.id,
                descricao,
                locacao.status,
            )
            return Response(
                {
                    "erro": f"Transição '{descricao}' não permitida "
                    f"para o status atual '{locacao.get_status_display()}'."
                },
                status=status.HTTP_409_CONFLICT,
            )

    @action(detail=True, methods=["post"], url_path="confirmar-entrega")
    def confirmar_entrega(self, request, pk=None):
        """
        Confirma a entrega do item ao locatário.

        Transição: CAUCAO_RETIDA → ATIVO.
        Apenas o locador pode confirmar a entrega.
        """
        locacao = self.get_object()

        # Validar que é o locador
        if request.user != locacao.locador:
            return Response(
                {"erro": "Apenas o locador pode confirmar a entrega."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return self._executar_transicao(
            request, pk, "confirmar_entrega", "Confirmar Entrega"
        )

    @action(detail=True, methods=["post"], url_path="confirmar-devolucao")
    def confirmar_devolucao(self, request, pk=None):
        """
        Confirma a devolução do item pelo locatário.

        Transição: ATIVO → DEVOLVIDO.
        Apenas o locador pode confirmar a devolução.
        """
        locacao = self.get_object()

        if request.user != locacao.locador:
            return Response(
                {"erro": "Apenas o locador pode confirmar a devolução."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return self._executar_transicao(
            request, pk, "confirmar_devolucao", "Confirmar Devolução"
        )

    @action(detail=True, methods=["post"], url_path="concluir")
    def concluir(self, request, pk=None):
        """
        Conclui a locação: captura diárias e libera caução.

        Transição: DEVOLVIDO → CONCLUIDO.
        Fluxo:
            1. Captura pagamento das diárias via Stripe
            2. Libera pré-autorização da caução
            3. Transiciona FSM para CONCLUIDO
        """
        locacao = self.get_object()

        # Capturar pagamento e liberar caução antes da transição
        try:
            if locacao.payment_intent_id:
                StripeService.capturar_pagamento_diarias(locacao)
            if locacao.caucao_auth_id:
                StripeService.liberar_caucao(locacao)
        except Exception as e:
            logger.error(
                "Erro financeiro ao concluir locação %s: %s",
                locacao.id, str(e)
            )
            return Response(
                {"erro": f"Erro ao processar pagamento: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return self._executar_transicao(
            request, pk, "concluir", "Concluir Locação"
        )

    @action(detail=True, methods=["post"], url_path="contestar")
    def contestar(self, request, pk=None):
        """
        Abre uma contestação/disputa na locação.

        Transição: (CAUCAO_RETIDA | ATIVO | DEVOLVIDO) → CONTESTADO.
        Ambas as partes (locador e locatário) podem contestar.
        A caução só poderá ser capturada após mediação humana.
        """
        return self._executar_transicao(
            request, pk, "contestar", "Contestar Locação"
        )

    @action(detail=True, methods=["post"], url_path="cancelar")
    def cancelar(self, request, pk=None):
        """
        Cancela a locação.

        Transição: SOLICITADO → CANCELADO.
        Apenas permitido antes da retenção de caução.
        """
        locacao = self.get_object()

        # Validar que é o locatário ou locador
        if request.user not in (locacao.locatario, locacao.locador):
            return Response(
                {"erro": "Apenas o locador ou locatário pode cancelar."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return self._executar_transicao(
            request, pk, "cancelar", "Cancelar Locação"
        )
