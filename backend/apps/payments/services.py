"""
Serviço de integração com Stripe Connect para o Aloogaí.

Gerencia: contas conectadas, pré-autorizações (caução),
captura parcial (diárias), liberação de caução e webhooks.
"""

import logging
from decimal import Decimal

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
    # Pré-Autorização (Caução Digital)
    # ─────────────────────────────────────────────

    @staticmethod
    def criar_pre_autorizacao(locacao):
        """
        Cria uma pré-autorização (PaymentIntent com captura manual)
        para o valor total: diárias + caução.

        O valor fica retido no cartão do locatário mas NÃO é cobrado.
        A captura só acontece quando o locador confirmar a entrega.
        """
        taxa_servico = settings.ALOOGAI_TAXA_SERVICO_LOCATARIO
        taxa_sucesso = settings.ALOOGAI_TAXA_SUCESSO_LOCADOR

        # Cálculos financeiros
        dias = (locacao.data_fim - locacao.data_inicio).days
        if dias < 1:
            dias = 1

        valor_diarias = locacao.item.preco_diaria * dias
        valor_taxa_servico = valor_diarias * Decimal(str(taxa_servico))
        total_locatario = valor_diarias + valor_taxa_servico + locacao.item.valor_caucao

        # Stripe trabalha em centavos
        total_centavos = int(total_locatario * 100)

        # Taxa de sucesso do Aloogaí (retida do locador no split)
        taxa_sucesso_centavos = int(valor_diarias * Decimal(str(taxa_sucesso)) * 100)

        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=total_centavos,
                currency='brl',
                capture_method='manual',  # Captura tardia (caução)
                payment_method_types=['card'],
                transfer_data={
                    'destination': locacao.item.locador.stripe_account_id,
                },
                application_fee_amount=int(valor_taxa_servico * 100) + taxa_sucesso_centavos,
                metadata={
                    'aloogai_locacao_id': str(locacao.id),
                    'aloogai_item_id': str(locacao.item.id),
                    'aloogai_locador_id': str(locacao.item.locador.id),
                    'aloogai_locatario_id': str(locacao.locatario.id),
                    'valor_diarias': str(valor_diarias),
                    'valor_caucao': str(locacao.item.valor_caucao),
                    'valor_taxa_servico': str(valor_taxa_servico),
                    'dias': str(dias),
                },
            )

            logger.info(
                'Pré-autorização criada: %s (R$ %.2f) para locação %s',
                payment_intent.id, total_locatario, locacao.id
            )

            # Registrar transação de pré-autorização (diárias)
            StripeService._registrar_transacao(
                locacao=locacao,
                tipo='PRE_AUTH',
                valor=valor_diarias + valor_taxa_servico,
                stripe_payment_intent_id=payment_intent.id,
                status_transacao='PENDENTE',
                metadata={
                    'dias': dias,
                    'valor_taxa_servico': str(valor_taxa_servico),
                },
            )

            # Registrar transação de pré-autorização (caução)
            StripeService._registrar_transacao(
                locacao=locacao,
                tipo='CAUCAO_PRE_AUTH',
                valor=locacao.item.valor_caucao,
                stripe_payment_intent_id=payment_intent.id,
                status_transacao='PENDENTE',
            )

            return {
                'payment_intent_id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'valor_diarias': valor_diarias,
                'valor_taxa_servico': valor_taxa_servico,
                'valor_caucao': locacao.item.valor_caucao,
                'total_locatario': total_locatario,
            }

        except stripe.error.StripeError as e:
            logger.error('Erro ao criar pré-autorização: %s', str(e))
            raise

    # ─────────────────────────────────────────────
    # Captura Parcial (Somente Diárias)
    # ─────────────────────────────────────────────

    @staticmethod
    def capturar_pagamento_diarias(locacao):
        """
        Captura apenas o valor das diárias + taxas.
        A caução permanece retida como pré-autorização separada.

        Regra de negócio: Só é chamado quando o locador confirma
        a entrega do item (transição para ATIVO).
        """
        try:
            taxa_servico = settings.ALOOGAI_TAXA_SERVICO_LOCATARIO

            dias = (locacao.data_fim - locacao.data_inicio).days
            if dias < 1:
                dias = 1

            valor_diarias = locacao.item.preco_diaria * dias
            valor_taxa_servico = valor_diarias * Decimal(str(taxa_servico))
            valor_captura = valor_diarias + valor_taxa_servico

            # Captura parcial — somente as diárias
            payment_intent = stripe.PaymentIntent.capture(
                locacao.payment_intent_id,
                amount_to_capture=int(valor_captura * 100),
            )

            logger.info(
                'Captura parcial realizada: %s (R$ %.2f) para locação %s',
                payment_intent.id, valor_captura, locacao.id
            )

            # Registrar transação de captura
            StripeService._registrar_transacao(
                locacao=locacao,
                tipo='CAPTURA',
                valor=valor_captura,
                stripe_payment_intent_id=payment_intent.id,
                status_transacao='SUCESSO',
            )

            return {
                'status': payment_intent.status,
                'valor_capturado': valor_captura,
            }

        except stripe.error.StripeError as e:
            logger.error('Erro ao capturar diárias: %s', str(e))
            raise

    # ─────────────────────────────────────────────
    # Liberação da Caução (Devolução sem danos)
    # ─────────────────────────────────────────────

    @staticmethod
    def liberar_caucao(locacao):
        """
        Cancela a pré-autorização da caução, liberando o limite
        do cartão do locatário sem cobrança.

        Regra de negócio: Chamado quando a devolução é confirmada
        sem avarias (transição para CONCLUIDO).
        """
        try:
            # Se temos um ID de caução separado, cancelar
            if locacao.caucao_auth_id:
                payment_intent = stripe.PaymentIntent.cancel(
                    locacao.caucao_auth_id,
                )
                logger.info(
                    'Caução liberada: %s para locação %s',
                    locacao.caucao_auth_id, locacao.id
                )

                # Registrar liberação da caução
                StripeService._registrar_transacao(
                    locacao=locacao,
                    tipo='CAUCAO_LIBERADA',
                    valor=locacao.valor_caucao,
                    stripe_payment_intent_id=locacao.caucao_auth_id,
                    status_transacao='SUCESSO',
                )

                return {'status': 'cancelada', 'caucao_liberada': True}

            logger.warning(
                'Nenhum caucao_auth_id encontrado para locação %s',
                locacao.id
            )
            return {'status': 'sem_caucao', 'caucao_liberada': False}

        except stripe.error.StripeError as e:
            logger.error('Erro ao liberar caução: %s', str(e))
            raise

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
