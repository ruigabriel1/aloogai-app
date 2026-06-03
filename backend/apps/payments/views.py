"""Views do módulo de Pagamentos do Aloogaí."""

import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ContaConectada, TransacaoStripe
from .serializers import (
    ContaConectadaSerializer,
    OnboardingSerializer,
    TransacaoStripeSerializer,
)
from .services import StripeService

logger = logging.getLogger(__name__)


class OnboardingView(APIView):
    """
    Iniciar ou continuar o onboarding Stripe Connect do locador.

    POST: Cria conta Stripe Connect e retorna URL de onboarding.
    GET: Retorna status do onboarding e novo link se necessário.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Criar nova conta Stripe Connect para o locador."""
        usuario = request.user

        # Verificar se já tem conta
        if hasattr(usuario, 'conta_conectada'):
            conta = usuario.conta_conectada
            if conta.status_onboarding == 'COMPLETO':
                return Response(
                    {'detail': 'Onboarding já concluído.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Gerar novo link
            url = StripeService.obter_link_onboarding(conta.stripe_account_id)
            return Response({'onboarding_url': url, 'account_id': conta.stripe_account_id})

        # Criar nova conta
        resultado = StripeService.criar_conta_conectada(usuario)

        # Salvar no banco
        ContaConectada.objects.create(
            usuario=usuario,
            stripe_account_id=resultado['account_id'],
            tipo_conta='EXPRESS',
            status_onboarding='PENDENTE',
        )

        # Atualizar usuário
        usuario.stripe_account_id = resultado['account_id']
        usuario.save(update_fields=['stripe_account_id'])

        serializer = OnboardingSerializer(resultado)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        """Verificar status do onboarding."""
        usuario = request.user

        if not hasattr(usuario, 'conta_conectada'):
            return Response(
                {'detail': 'Nenhuma conta Stripe encontrada. Faça POST para iniciar.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        conta = usuario.conta_conectada
        status_stripe = StripeService.verificar_status_conta(
            conta.stripe_account_id
        )

        return Response({
            'account_id': conta.stripe_account_id,
            'status_onboarding': conta.status_onboarding,
            **status_stripe,
        })


class TransacoesLocacaoView(APIView):
    """Listar transações de uma locação específica."""

    permission_classes = [IsAuthenticated]

    def get(self, request, locacao_id):
        """Retorna todas as transações da locação."""
        transacoes = TransacaoStripe.objects.filter(
            locacao_id=locacao_id,
            locacao__locatario=request.user,
        ).union(
            TransacaoStripe.objects.filter(
                locacao_id=locacao_id,
                locacao__item__locador=request.user,
            )
        ).order_by('-created_at')

        serializer = TransacaoStripeSerializer(transacoes, many=True)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Endpoint para receber webhooks do Stripe.

    Este endpoint é público (sem autenticação JWT) pois o Stripe
    envia requests diretamente. A autenticação é feita via
    verificação de assinatura do webhook.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        """Processar evento webhook do Stripe."""
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

        try:
            resultado = StripeService.processar_webhook(payload, sig_header)
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError:
            return HttpResponse(status=400)
        except Exception as e:
            logger.error('Erro no webhook Stripe: %s', str(e))
            return HttpResponse(status=400)
