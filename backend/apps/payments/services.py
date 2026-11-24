"""
Serviço de integração com Stripe Connect para o Aloogaí.

Gerencia: contas conectadas, pré-autorizações (caução),
captura parcial (diárias), liberação de caução e webhooks.
"""

import logging
from decimal import ROUND_HALF_UP, Decimal

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)

# Inicializar Stripe com a chave secreta
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Serviço centralizado para operações Stripe Connect."""

    # ─────────────────────────────────────────────
    # Registro de Transações (Rastreabilidade)
    # ─────────────────────────────────────────────

    @staticmethod
    def _registrar_transacao(
        locacao,
        tipo: str,
        valor,
        stripe_payment_intent_id: str = "",
        status_transacao: str = "PENDENTE",
        metadata: dict | None = None,
    ):
        """
        Registra uma transação financeira no banco de dados.

        Garante rastreabilidade completa de todas as operações
        Stripe associadas a uma locação.
        """
        from apps.payments.models import TransacaoStripe

        return TransacaoStripe.objects.create(
            locacao=locacao,
            tipo=tipo,
            valor=valor,
            stripe_payment_intent_id=stripe_payment_intent_id,
            status=status_transacao,
            metadata=metadata or {},
        )

    # ─────────────────────────────────────────────
    # Contas Conectadas (Onboarding do Locador)
    # ─────────────────────────────────────────────

    @staticmethod
    def criar_conta_conectada(usuario):
        """
        Cria uma conta Stripe Connect Express para o locador.
        Retorna o account_id e o link de onboarding.
        """
        try:
            account = stripe.Account.create(
                type='express',
                country='BR',
                email=usuario.email,
                capabilities={
                    'card_payments': {'requested': True},
                    'transfers': {'requested': True},
                },
                business_type='individual',
                metadata={
                    'aloogai_usuario_id': str(usuario.id),
                    'tipo_usuario': usuario.tipo_usuario,
                },
            )

            # Criar link de onboarding
            account_link = stripe.AccountLink.create(
                account=account.id,
                refresh_url=f'{settings.FRONTEND_URL}/stripe/refresh',
                return_url=f'{settings.FRONTEND_URL}/stripe/return',
                type='account_onboarding',
            )

            logger.info(
                'Conta Stripe Connect criada: %s para usuário %s',
                account.id, usuario.id
            )

            return {
                'account_id': account.id,
                'onboarding_url': account_link.url,
            }

        except stripe.error.StripeError as e:
            logger.error('Erro ao criar conta Stripe: %s', str(e))
            raise

    @staticmethod
    def obter_link_onboarding(stripe_account_id):
        """Gera novo link de onboarding para conta existente."""
        try:
            account_link = stripe.AccountLink.create(
                account=stripe_account_id,
                refresh_url=f'{settings.FRONTEND_URL}/stripe/refresh',
                return_url=f'{settings.FRONTEND_URL}/stripe/return',
                type='account_onboarding',
            )
            return account_link.url
        except stripe.error.StripeError as e:
            logger.error('Erro ao gerar link onboarding: %s', str(e))
            raise

    @staticmethod
    def verificar_status_conta(stripe_account_id):
        """Verifica se a conta conectada completou o onboarding."""
        try:
            account = stripe.Account.retrieve(stripe_account_id)
            return {
                'charges_enabled': account.charges_enabled,
                'payouts_enabled': account.payouts_enabled,
                'details_submitted': account.details_submitted,
                'onboarding_completo': (
                    account.charges_enabled and account.payouts_enabled
                ),
            }
        except stripe.error.StripeError as e:
            logger.error('Erro ao verificar conta: %s', str(e))
            raise

    # ─────────────────────────────────────────────
    # Pagamento da Locação (PaymentIntent com captura manual)
    # ─────────────────────────────────────────────
    #
    # Fluxo (os valores vêm da própria Locacao, calculados pelo LocacaoService):
    #   1. criar_pre_autorizacao: autoriza diárias + taxa de serviço + caução no cartão
    #      (nada é cobrado ainda). O app confirma com a PaymentSheet usando o client_secret.
    #   2. sincronizar_pagamento: quando o Stripe diz "requires_capture" (webhook ou
    #      consulta direta), a locação passa de SOLICITADO para CAUCAO_RETIDA.
    #   3. capturar_valor_devido (ao concluir): captura só diárias + taxa. O Stripe
    #      libera o restante da autorização (a caução) automaticamente.
    #   4. cancelar_pre_autorizacao: cancela a autorização inteira (locação cancelada).

    @staticmethod
    def _centavos(valor) -> int:
        """Converte reais (Decimal) para centavos, arredondando meio para cima."""
        return int((Decimal(valor) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @staticmethod
    def _conta_destino(locacao) -> str | None:
        """Conta Connect do locador, se o onboarding estiver completo (senão, sem repasse)."""
        locador = locacao.item.locador
        if locador.stripe_account_id and locador.stripe_onboarding_complete:
            return locador.stripe_account_id
        return None

    @staticmethod
    def criar_pre_autorizacao(locacao):
        """
        Cria o PaymentIntent (captura manual) para diárias + taxa + caução.

        Returns:
            dict com payment_intent_id e client_secret (para a PaymentSheet do app).
        """
        valor_autorizado = locacao.total_locatario + locacao.valor_caucao
        params = {
            "amount": StripeService._centavos(valor_autorizado),
            "currency": "brl",
            "capture_method": "manual",
            "payment_method_types": ["card"],
            "metadata": {
                "aloogai_locacao_id": str(locacao.id),
                "aloogai_item_id": str(locacao.item_id),
                "valor_devido": str(locacao.total_locatario),
                "valor_caucao": str(locacao.valor_caucao),
            },
        }
        destino = StripeService._conta_destino(locacao)
        if destino:
            params["transfer_data"] = {"destination": destino}

        payment_intent = stripe.PaymentIntent.create(
            **params, idempotency_key=f"aloogai-preauth-{locacao.id}",
        )
        logger.info(
            "Pré-autorização criada: %s (R$ %s) para locação %s",
            payment_intent.id, valor_autorizado, locacao.id,
        )

        StripeService._registrar_transacao(
            locacao=locacao, tipo="PRE_AUTH", valor=locacao.total_locatario,
            stripe_payment_intent_id=payment_intent.id,
        )
        StripeService._registrar_transacao(
            locacao=locacao, tipo="CAUCAO_PRE_AUTH", valor=locacao.valor_caucao,
            stripe_payment_intent_id=payment_intent.id,
        )
        return {
            "payment_intent_id": payment_intent.id,
            "client_secret": payment_intent.client_secret,
        }

    @staticmethod
    def sincronizar_pagamento(locacao, status_stripe: str | None = None) -> bool:
        """
        Passa a locação para CAUCAO_RETIDA quando o cartão foi autorizado.

        Idempotente: pode ser chamado pelo webhook e pelo app (depois da PaymentSheet).
        Se `status_stripe` não vier, consulta o PaymentIntent no Stripe.

        Returns:
            True se a locação está com o pagamento autorizado (ou já passou dessa etapa).
        """
        from apps.payments.models import TransacaoStripe
        from apps.rentals.models import StatusLocacao

        if locacao.status != StatusLocacao.SOLICITADO:
            return locacao.status != StatusLocacao.CANCELADO
        if not locacao.payment_intent_id:
            return False

        if status_stripe is None:
            status_stripe = stripe.PaymentIntent.retrieve(locacao.payment_intent_id).status
        if status_stripe != "requires_capture":
            return False

        locacao.reter_caucao(caucao_auth_id=locacao.payment_intent_id)
        locacao.save()
        TransacaoStripe.objects.filter(
            locacao=locacao, tipo__in=["PRE_AUTH", "CAUCAO_PRE_AUTH"],
        ).update(status="SUCESSO")
        logger.info("Locação %s: cartão autorizado, caução retida.", locacao.id)
        return True

    @staticmethod
    def capturar_valor_devido(locacao):
        """
        Captura só o valor devido (diárias + taxa de serviço).

        A parte não capturada (caução) é liberada pelo Stripe na mesma operação,
        então não há cancelamento depois. Com repasse Connect, a plataforma retém
        taxa de serviço + taxa de sucesso como application fee.
        """
        payment_intent = stripe.PaymentIntent.retrieve(locacao.payment_intent_id)
        params = {"amount_to_capture": StripeService._centavos(locacao.total_locatario)}
        if payment_intent.get("transfer_data"):
            params["application_fee_amount"] = StripeService._centavos(
                locacao.valor_taxa_servico + locacao.valor_taxa_sucesso
            )

        payment_intent = stripe.PaymentIntent.capture(
            locacao.payment_intent_id, **params,
            idempotency_key=f"aloogai-captura-{locacao.id}",
        )
        logger.info(
            "Captura de R$ %s (caução liberada) para locação %s",
            locacao.total_locatario, locacao.id,
        )
        StripeService._registrar_transacao(
            locacao=locacao, tipo="CAPTURA", valor=locacao.total_locatario,
            stripe_payment_intent_id=payment_intent.id, status_transacao="SUCESSO",
        )
        StripeService._registrar_transacao(
            locacao=locacao, tipo="CAUCAO_LIBERADA", valor=locacao.valor_caucao,
            stripe_payment_intent_id=payment_intent.id, status_transacao="SUCESSO",
        )
        return {"status": payment_intent.status, "valor_capturado": locacao.total_locatario}

    @staticmethod
    def cancelar_pre_autorizacao(locacao):
        """Cancela a autorização inteira (nada é cobrado do locatário)."""
        if not locacao.payment_intent_id:
            return
        try:
            stripe.PaymentIntent.cancel(locacao.payment_intent_id)
        except stripe.InvalidRequestError as e:
            # Já cancelado/expirado no Stripe: para nós o resultado é o mesmo.
            if getattr(e, "code", "") != "payment_intent_unexpected_state":
                raise
            logger.info("PI %s já não estava cancelável: %s", locacao.payment_intent_id, e)
        StripeService._registrar_transacao(
            locacao=locacao, tipo="CAUCAO_LIBERADA", valor=locacao.valor_caucao,
            stripe_payment_intent_id=locacao.payment_intent_id, status_transacao="SUCESSO",
        )

    # ─────────────────────────────────────────────
    # Captura da Caução (Sinistro — Mediação Humana)
    # ─────────────────────────────────────────────

    @staticmethod
    def capturar_caucao(locacao, valor_captura=None):
        """
        Captura total ou parcial da caução em caso de sinistro.

        ⚠️ REGRA INVARIANTE: Esta função SÓ pode ser chamada
        por um admin após mediação humana quando a locação
        está em status CONTESTADO.

        Args:
            locacao: Instância da Locacao com status CONTESTADO
            valor_captura: Valor em reais a capturar (None = total)
        """
        if locacao.status != 'CONTESTADO':
            raise ValueError(
                'Caução só pode ser capturada com status CONTESTADO. '
                f'Status atual: {locacao.status}'
            )

        try:
            kwargs = {}
            if valor_captura is not None:
                kwargs['amount_to_capture'] = int(valor_captura * 100)

            payment_intent = stripe.PaymentIntent.capture(
                locacao.caucao_auth_id,
                **kwargs,
            )

            valor_final = valor_captura or locacao.valor_caucao

            logger.warning(
                'CAUÇÃO CAPTURADA: %s (R$ %s) para locação %s — SINISTRO',
                locacao.caucao_auth_id,
                valor_final,
                locacao.id
            )

            # Registrar captura de caução (sinistro)
            StripeService._registrar_transacao(
                locacao=locacao,
                tipo='CAUCAO_CAPTURA',
                valor=valor_final,
                stripe_payment_intent_id=locacao.caucao_auth_id,
                status_transacao='SUCESSO',
                metadata={'sinistro': True},
            )

            return {
                'status': payment_intent.status,
                'valor_capturado': valor_final,
            }

        except stripe.error.StripeError as e:
            logger.error('Erro ao capturar caução: %s', str(e))
            raise

    # ─────────────────────────────────────────────
    # Webhook Handler
    # ─────────────────────────────────────────────

    @staticmethod
    def processar_webhook(payload, sig_header):
        """
        Processa eventos recebidos do Stripe via webhook.
        Verifica a assinatura e despacha para o handler correto.
        """
        if not settings.STRIPE_WEBHOOK_SECRET:
            # Sem segredo, a assinatura não prova nada: recusar em vez de aceitar forjado.
            raise ValueError('STRIPE_WEBHOOK_SECRET não configurado.')

        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except ValueError:
            logger.error('Webhook: payload inválido')
            raise
        except stripe.error.SignatureVerificationError:
            logger.error('Webhook: assinatura inválida')
            raise

        event_type = event['type']
        data = event['data']['object']

        logger.info('Webhook recebido: %s', event_type)

        handlers = {
            'payment_intent.amount_capturable_updated': StripeService._handle_autorizado,
            'payment_intent.succeeded': StripeService._handle_payment_succeeded,
            'payment_intent.payment_failed': StripeService._handle_payment_failed,
            'account.updated': StripeService._handle_account_updated,
        }

        handler = handlers.get(event_type)
        if handler:
            handler(data)
        else:
            logger.debug('Evento Stripe não tratado: %s', event_type)

        return {'status': 'ok', 'event_type': event_type}

    @staticmethod
    def _handle_autorizado(data):
        """Cartão autorizado (requires_capture): a locação passa para CAUCAO_RETIDA."""
        from apps.rentals.models import Locacao

        locacao = Locacao.objects.filter(payment_intent_id=data["id"]).first()
        if locacao is None:
            logger.warning("Webhook: nenhuma locação para o PI %s", data["id"])
            return
        StripeService.sincronizar_pagamento(locacao, status_stripe=data.get("status"))

    @staticmethod
    def _handle_payment_succeeded(data):
        """Trata pagamento bem-sucedido."""
        from apps.payments.models import TransacaoStripe

        TransacaoStripe.objects.filter(
            stripe_payment_intent_id=data['id']
        ).update(status='SUCESSO')

        logger.info('Pagamento confirmado: %s', data['id'])

    @staticmethod
    def _handle_payment_failed(data):
        """Trata falha no pagamento."""
        from apps.payments.models import TransacaoStripe

        TransacaoStripe.objects.filter(
            stripe_payment_intent_id=data['id']
        ).update(status='FALHA')

        logger.warning('Pagamento falhou: %s', data['id'])

    @staticmethod
    def _handle_account_updated(data):
        """Trata atualização de conta conectada."""
        from apps.payments.models import ContaConectada

        try:
            conta = ContaConectada.objects.get(
                stripe_account_id=data['id']
            )
            onboarding_completo = (
                data.get('charges_enabled', False)
                and data.get('payouts_enabled', False)
            )
            if onboarding_completo:
                conta.status_onboarding = 'COMPLETO'
                conta.save(update_fields=['status_onboarding'])

                # Atualizar usuário
                conta.usuario.stripe_onboarding_complete = True
                conta.usuario.save(update_fields=['stripe_onboarding_complete'])

            logger.info(
                'Conta atualizada: %s (onboarding: %s)',
                data['id'], onboarding_completo
            )
        except ContaConectada.DoesNotExist:
            logger.warning('Conta Stripe não encontrada: %s', data['id'])
