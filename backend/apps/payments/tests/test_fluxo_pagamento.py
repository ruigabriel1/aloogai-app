"""
Fluxo de pagamento da locação com o Stripe mockado.

Cobre: criação com pré-autorização, confirmação, conclusão (captura só do devido,
sem cancelar depois), cancelamento e webhook de autorização.
"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import stripe
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.payments.services import StripeService
from apps.rentals.models import Locacao, StatusLocacao
from apps.rentals.tests.conftest import ItemFactory, LocacaoFactory, UsuarioFactory

LOCACOES = '/api/v1/rentals/locacoes/'
PI = 'apps.payments.services.stripe.PaymentIntent'


def _pi(**campos):
    """Simula um objeto PaymentIntent do Stripe (atributos e .get())."""
    obj = MagicMock()
    for chave, valor in campos.items():
        setattr(obj, chave, valor)
    obj.get.side_effect = lambda chave, padrao=None: campos.get(chave, padrao)
    return obj


class CriacaoLocacaoTests(APITestCase):
    def setUp(self):
        self.locatario = UsuarioFactory()
        self.item = ItemFactory(preco_diaria=Decimal('40.00'), valor_caucao=Decimal('200.00'))
        self.client.force_authenticate(self.locatario)
        inicio = date.today() + timedelta(days=2)
        self.payload = {
            'item': str(self.item.id),
            'data_inicio': inicio.isoformat(),
            'data_fim': (inicio + timedelta(days=3)).isoformat(),
        }

    @patch(PI)
    def test_cria_locacao_com_pre_autorizacao_de_diarias_taxa_e_caucao(self, pi_mock):
        pi_mock.create.return_value = _pi(id='pi_123', client_secret='pi_123_secret')
        resposta = self.client.post(LOCACOES, self.payload, format='json')

        self.assertEqual(resposta.status_code, 201, resposta.data)
        self.assertEqual(resposta.data['pagamento']['client_secret'], 'pi_123_secret')
        locacao = Locacao.objects.get(id=resposta.data['id'])
        self.assertEqual(locacao.status, StatusLocacao.SOLICITADO)
        self.assertEqual(locacao.payment_intent_id, 'pi_123')

        # 3 diárias de 40 = 120; taxa de 10% = 12; caução 200 → autoriza R$ 332,00
        kwargs = pi_mock.create.call_args.kwargs
        self.assertEqual(kwargs['amount'], 33200)
        self.assertEqual(kwargs['capture_method'], 'manual')
        self.assertIn('transfer_data', kwargs)  # locador da factory tem conta Connect

    @patch(PI)
    def test_sem_conta_connect_nao_ha_repasse(self, pi_mock):
        self.item.locador.stripe_onboarding_complete = False
        self.item.locador.save()
        pi_mock.create.return_value = _pi(id='pi_1', client_secret='s')
        self.client.post(LOCACOES, self.payload, format='json')
        self.assertNotIn('transfer_data', pi_mock.create.call_args.kwargs)

    @patch(PI)
    def test_falha_no_stripe_nao_deixa_locacao_orfa(self, pi_mock):
        pi_mock.create.side_effect = stripe.APIConnectionError('sem rede')
        resposta = self.client.post(LOCACOES, self.payload, format='json')
        self.assertEqual(resposta.status_code, 502)
        self.assertFalse(Locacao.objects.exists())

    def test_nao_aluga_item_pausado(self):
        self.item.status = 'PAUSADO'
        self.item.save()
        resposta = self.client.post(LOCACOES, self.payload, format='json')
        self.assertEqual(resposta.status_code, 400)


class ConfirmacaoPagamentoTests(APITestCase):
    def setUp(self):
        self.locacao = LocacaoFactory(payment_intent_id='pi_abc')
        self.client.force_authenticate(self.locacao.locatario)
        self.url = f'{LOCACOES}{self.locacao.id}/confirmar-pagamento/'

    @patch(PI)
    def test_cartao_autorizado_passa_para_caucao_retida(self, pi_mock):
        pi_mock.retrieve.return_value = _pi(id='pi_abc', status='requires_capture')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.locacao = Locacao.objects.get(id=self.locacao.id)
        self.assertEqual(self.locacao.status, StatusLocacao.CAUCAO_RETIDA)

    @patch(PI)
    def test_cartao_ainda_nao_autorizado_retorna_409(self, pi_mock):
        pi_mock.retrieve.return_value = _pi(id='pi_abc', status='requires_payment_method')
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, 409)
        self.locacao = Locacao.objects.get(id=self.locacao.id)
        self.assertEqual(self.locacao.status, StatusLocacao.SOLICITADO)

    def test_webhook_de_autorizacao_tem_o_mesmo_efeito(self):
        StripeService._handle_autorizado({'id': 'pi_abc', 'status': 'requires_capture'})
        self.locacao = Locacao.objects.get(id=self.locacao.id)
        self.assertEqual(self.locacao.status, StatusLocacao.CAUCAO_RETIDA)


class ConclusaoTests(APITestCase):
    def setUp(self):
        self.locacao = LocacaoFactory(
            status=StatusLocacao.DEVOLVIDO,
            payment_intent_id='pi_xyz',
            total_locatario=Decimal('55.00'),
            valor_taxa_servico=Decimal('5.00'),
            valor_taxa_sucesso=Decimal('7.50'),
        )
        self.locador = self.locacao.item.locador
        self.url = f'{LOCACOES}{self.locacao.id}/concluir/'

    @patch(PI)
    def test_captura_so_o_devido_com_taxas_e_nao_cancela_depois(self, pi_mock):
        pi_mock.retrieve.return_value = _pi(id='pi_xyz', transfer_data={'destination': 'acct_1'})
        pi_mock.capture.return_value = _pi(id='pi_xyz', status='succeeded')
        self.client.force_authenticate(self.locador)

        resposta = self.client.post(self.url)

        self.assertEqual(resposta.status_code, 200, resposta.data)
        kwargs = pi_mock.capture.call_args.kwargs
        self.assertEqual(kwargs['amount_to_capture'], 5500)
        self.assertEqual(kwargs['application_fee_amount'], 1250)  # 5,00 + 7,50
        pi_mock.cancel.assert_not_called()
        self.locacao = Locacao.objects.get(id=self.locacao.id)
        self.assertEqual(self.locacao.status, StatusLocacao.CONCLUIDO)

    @patch(PI)
    def test_locatario_nao_conclui(self, pi_mock):
        self.client.force_authenticate(self.locacao.locatario)
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, 403)
        pi_mock.capture.assert_not_called()

    @patch(PI)
    def test_nao_cobra_antes_da_devolucao(self, pi_mock):
        ativa = LocacaoFactory(status=StatusLocacao.ATIVO, payment_intent_id="pi_a")
        self.url = f"{LOCACOES}{ativa.id}/concluir/"
        self.locador = ativa.item.locador
        self.client.force_authenticate(self.locador)
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, 409)
        pi_mock.capture.assert_not_called()

    @patch(PI)
    def test_falha_na_captura_mantem_a_locacao_devolvida(self, pi_mock):
        pi_mock.retrieve.return_value = _pi(id='pi_xyz')
        pi_mock.capture.side_effect = stripe.APIConnectionError('sem rede')
        self.client.force_authenticate(self.locador)
        resposta = self.client.post(self.url)
        self.assertEqual(resposta.status_code, 502)
        self.locacao = Locacao.objects.get(id=self.locacao.id)
        self.assertEqual(self.locacao.status, StatusLocacao.DEVOLVIDO)


class CancelamentoTests(APITestCase):
    @patch(PI)
    def test_cancelar_apos_autorizar_libera_o_cartao(self, pi_mock):
        locacao = LocacaoFactory(status=StatusLocacao.CAUCAO_RETIDA, payment_intent_id='pi_c')
        self.client.force_authenticate(locacao.locatario)
        resposta = self.client.post(f'{LOCACOES}{locacao.id}/cancelar/')
        self.assertEqual(resposta.status_code, 200, resposta.data)
        pi_mock.cancel.assert_called_once_with('pi_c')
        locacao = Locacao.objects.get(id=locacao.id)
        self.assertEqual(locacao.status, StatusLocacao.CANCELADO)


class WebhookTests(APITestCase):
    @override_settings(STRIPE_WEBHOOK_SECRET='')
    def test_sem_segredo_configurado_o_webhook_e_recusado(self):
        resposta = self.client.post(
            '/api/v1/payments/webhooks/stripe/', data='{}', content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=1,v1=falso',
        )
        self.assertEqual(resposta.status_code, 400)
