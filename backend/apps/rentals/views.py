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
import stripe
from django_fsm import TransitionNotAllowed, can_proceed
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
    def create(self, request, *args, **kwargs):
        """
        Cria a locação (SOLICITADO) e a pré-autorização no Stripe, numa transação só.

        A resposta traz `pagamento.client_secret` para o app abrir a PaymentSheet.
        Se o Stripe falhar, nada é gravado e a resposta é 502 (sem locação órfã).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                locacao = serializer.save()
                pagamento = StripeService.criar_pre_autorizacao(locacao)
                locacao.payment_intent_id = pagamento["payment_intent_id"]
                locacao.save(update_fields=["payment_intent_id"])
        except stripe.StripeError as e:
            logger.error("Stripe recusou a pré-autorização: %s", e)
            return Response(
                {"erro": "Não foi possível iniciar o pagamento. Tente novamente."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        logger.info("Locação %s criada (PI %s)", locacao.id, locacao.payment_intent_id)
        dados = LocacaoDetailSerializer(locacao, context={"request": request}).data
        dados["pagamento"] = {
            "client_secret": pagamento["client_secret"],
            "payment_intent_id": pagamento["payment_intent_id"],
        }
        return Response(dados, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="confirmar-pagamento")
    def confirmar_pagamento(self, request, pk=None):
        """
        Confere no Stripe se o cartão foi autorizado e, se sim, passa para CAUCAO_RETIDA.

        O app chama depois da PaymentSheet; o webhook faz o mesmo. É idempotente.
        """
        locacao = self.get_object()
        if request.user != locacao.locatario:
            return Response(
                {"erro": "Apenas o locatário confirma o pagamento."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            autorizado = StripeService.sincronizar_pagamento(locacao)
        except stripe.StripeError as e:
            logger.error("Erro ao consultar pagamento da locação %s: %s", locacao.id, e)
            return Response(
                {"erro": "Não foi possível consultar o pagamento."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if not autorizado:
            return Response(
                {"erro": "O pagamento ainda não foi autorizado."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(LocacaoDetailSerializer(locacao).data, status=status.HTTP_200_OK)

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
        Conclui a locação: captura o valor devido e libera a caução.

        Transição: DEVOLVIDO → CONCLUIDO. Só o locador conclui.
        Estado e papel são validados ANTES de mexer no dinheiro; a captura e a
        transição acontecem juntas (se o Stripe falhar, a locação não muda).
        """
        locacao = self.get_object()

        if request.user != locacao.locador:
            return Response(
                {"erro": "Apenas o locador pode concluir a locação."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not can_proceed(locacao.concluir):
            return Response(
                {
                    "erro": "A locação só pode ser concluída depois da devolução "
                    f"(status atual: '{locacao.get_status_display()}')."
                },
                status=status.HTTP_409_CONFLICT,
            )

        try:
            with transaction.atomic():
                if locacao.payment_intent_id:
                    StripeService.capturar_valor_devido(locacao)
                locacao.concluir()
                locacao.save()
        except stripe.StripeError as e:
            logger.error("Erro financeiro ao concluir locação %s: %s", locacao.id, e)
            return Response(
                {"erro": "Não foi possível processar o pagamento. Tente novamente."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        logger.info("Locação %s concluída por %s", locacao.id, request.user.id)
        return Response(LocacaoDetailSerializer(locacao).data, status=status.HTTP_200_OK)

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

        if not can_proceed(locacao.cancelar):
            return Response(
                {"erro": f"Não é possível cancelar no status '{locacao.get_status_display()}'."},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            StripeService.cancelar_pre_autorizacao(locacao)
        except stripe.StripeError as e:
            logger.error("Erro ao cancelar autorização da locação %s: %s", locacao.id, e)
            return Response(
                {"erro": "Não foi possível cancelar o pagamento. Tente novamente."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return self._executar_transicao(
            request, pk, "cancelar", "Cancelar Locação"
        )
