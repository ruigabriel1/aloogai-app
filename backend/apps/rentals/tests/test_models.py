"""
Testes unitários para o modelo Locacao (FSM).

Cobre todas as transições de status da máquina de estados,
incluindo transições válidas e inválidas.
"""
from django.test import TestCase
from django_fsm import TransitionNotAllowed

from apps.rentals.models import Locacao, StatusLocacao

from .conftest import LocacaoFactory


class TestFSMTransicoes(TestCase):
    """Testes para as transições FSM do modelo Locacao."""

    def test_transicao_solicitado_para_caucao_retida(self):
        """SOLICITADO → CAUCAO_RETIDA deve funcionar."""
        locacao = LocacaoFactory()
        self.assertEqual(locacao.status, StatusLocacao.SOLICITADO)

        locacao.reter_caucao(caucao_auth_id='pi_test_123')
        locacao.save()

        self.assertEqual(locacao.status, StatusLocacao.CAUCAO_RETIDA)
        self.assertEqual(locacao.caucao_auth_id, 'pi_test_123')

    def test_transicao_caucao_retida_para_ativo(self):
        """CAUCAO_RETIDA → ATIVO deve funcionar."""
        locacao = LocacaoFactory()
        locacao.reter_caucao(caucao_auth_id='pi_test_123')
        locacao.save()

        locacao.confirmar_entrega()
        locacao.save()

        self.assertEqual(locacao.status, StatusLocacao.ATIVO)

    def test_transicao_ativo_para_devolvido(self):
        """ATIVO → DEVOLVIDO deve funcionar."""
        locacao = LocacaoFactory()
        locacao.reter_caucao(caucao_auth_id='pi_test_123')
        locacao.save()
        locacao.confirmar_entrega()
        locacao.save()

        locacao.confirmar_devolucao()
        locacao.save()

        self.assertEqual(locacao.status, StatusLocacao.DEVOLVIDO)

    def test_transicao_devolvido_para_concluido(self):
        """DEVOLVIDO → CONCLUIDO deve funcionar."""
        locacao = LocacaoFactory()
        locacao.reter_caucao(caucao_auth_id='pi_test_123')
        locacao.save()
        locacao.confirmar_entrega()
        locacao.save()
        locacao.confirmar_devolucao()
        locacao.save()

        locacao.concluir()
        locacao.save()

        self.assertEqual(locacao.status, StatusLocacao.CONCLUIDO)

    def test_ciclo_completo(self):
        """Fluxo completo: SOLICITADO → ... → CONCLUIDO."""
        locacao = LocacaoFactory()

        # SOLICITADO → CAUCAO_RETIDA
        locacao.reter_caucao(caucao_auth_id='pi_test_completo')
        locacao.save()
        self.assertEqual(locacao.status, StatusLocacao.CAUCAO_RETIDA)

        # CAUCAO_RETIDA → ATIVO
        locacao.confirmar_entrega()
        locacao.save()
        self.assertEqual(locacao.status, StatusLocacao.ATIVO)

        # ATIVO → DEVOLVIDO
        locacao.confirmar_devolucao()
        locacao.save()
        self.assertEqual(locacao.status, StatusLocacao.DEVOLVIDO)

        # DEVOLVIDO → CONCLUIDO
        locacao.concluir()
        locacao.save()
        self.assertEqual(locacao.status, StatusLocacao.CONCLUIDO)


class TestFSMTransicoesInvalidas(TestCase):
    """Testes para transições FSM que devem ser REJEITADAS."""

    def test_transicao_invalida_solicitado_para_ativo(self):
        """SOLICITADO → ATIVO deve falhar (precisa passar por CAUCAO_RETIDA)."""
        locacao = LocacaoFactory()

        with self.assertRaises(TransitionNotAllowed):
            locacao.confirmar_entrega()

    def test_transicao_invalida_solicitado_para_devolvido(self):
        """SOLICITADO → DEVOLVIDO deve falhar."""
        locacao = LocacaoFactory()

        with self.assertRaises(TransitionNotAllowed):
            locacao.confirmar_devolucao()

    def test_transicao_invalida_solicitado_para_concluido(self):
        """SOLICITADO → CONCLUIDO deve falhar."""
        locacao = LocacaoFactory()

        with self.assertRaises(TransitionNotAllowed):
            locacao.concluir()

    def test_cancelar_apos_caucao_retida_deve_falhar(self):
        """Cancelar após caução retida NÃO é permitido pela FSM."""
        locacao = LocacaoFactory()
        locacao.reter_caucao(caucao_auth_id='pi_test_123')
        locacao.save()

        with self.assertRaises(TransitionNotAllowed):
            locacao.cancelar()

    def test_cancelar_apos_ativo_deve_falhar(self):
        """Cancelar após ATIVO não é permitido."""
        locacao = LocacaoFactory()
        locacao.reter_caucao(caucao_auth_id='pi_test_123')
        locacao.save()
        locacao.confirmar_entrega()
        locacao.save()

        with self.assertRaises(TransitionNotAllowed):
            locacao.cancelar()


class TestFSMCancelamento(TestCase):
    """Testes para cancelamento de locação."""

    def test_cancelar_solicitado(self):
        """SOLICITADO → CANCELADO deve funcionar."""
        locacao = LocacaoFactory()

        locacao.cancelar()
        locacao.save()

        self.assertEqual(locacao.status, StatusLocacao.CANCELADO)


class TestFSMContestacao(TestCase):
    """Testes para contestação de locação."""

    def test_contestar_a_partir_de_caucao_retida(self):
        """CAUCAO_RETIDA → CONTESTADO deve funcionar."""
        locacao = LocacaoFactory()
        locacao.reter_caucao(caucao_auth_id='pi_test_123')
        locacao.save()

        locacao.contestar(observacao='Item com defeito.')
        locacao.save()

        self.assertEqual(locacao.status, StatusLocacao.CONTESTADO)

    def test_contestar_a_partir_de_ativo(self):
        """ATIVO → CONTESTADO deve funcionar."""
        locacao = LocacaoFactory()
        locacao.reter_caucao(caucao_auth_id='pi_test_123')
        locacao.save()
        locacao.confirmar_entrega()
        locacao.save()

        locacao.contestar(observacao='Dano no item.')
        locacao.save()

        self.assertEqual(locacao.status, StatusLocacao.CONTESTADO)

    def test_contestar_a_partir_de_devolvido(self):
        """DEVOLVIDO → CONTESTADO deve funcionar."""
        locacao = LocacaoFactory()
        locacao.reter_caucao(caucao_auth_id='pi_test_123')
        locacao.save()
        locacao.confirmar_entrega()
        locacao.save()
        locacao.confirmar_devolucao()
        locacao.save()

        locacao.contestar(observacao='Item devolvido com arranhões.')
        locacao.save()

        self.assertEqual(locacao.status, StatusLocacao.CONTESTADO)

    def test_contestar_a_partir_de_solicitado_deve_falhar(self):
        """SOLICITADO → CONTESTADO não é permitido."""
        locacao = LocacaoFactory()

        with self.assertRaises(TransitionNotAllowed):
            locacao.contestar()

    def test_contestar_a_partir_de_concluido_deve_falhar(self):
        """CONCLUIDO → CONTESTADO não é permitido."""
        locacao = LocacaoFactory()
        locacao.reter_caucao(caucao_auth_id='pi_test_123')
        locacao.save()
        locacao.confirmar_entrega()
        locacao.save()
        locacao.confirmar_devolucao()
        locacao.save()
        locacao.concluir()
        locacao.save()

        with self.assertRaises(TransitionNotAllowed):
            locacao.contestar()


class TestLocacaoPropriedades(TestCase):
    """Testes para propriedades do modelo Locacao."""

    def test_numero_diarias(self):
        """Propriedade numero_diarias deve calcular corretamente."""
        from datetime import date, timedelta

        locacao = LocacaoFactory(
            data_inicio=date.today() + timedelta(days=1),
            data_fim=date.today() + timedelta(days=4),
        )
        self.assertEqual(locacao.numero_diarias, 3)

    def test_numero_diarias_minimo_1(self):
        """Número mínimo de diárias deve ser 1."""
        from datetime import date, timedelta

        dia = date.today() + timedelta(days=1)
        locacao = LocacaoFactory(data_inicio=dia, data_fim=dia)
        self.assertEqual(locacao.numero_diarias, 1)

    def test_locador_property(self):
        """Propriedade locador deve retornar o dono do item."""
        locacao = LocacaoFactory()
        self.assertEqual(locacao.locador, locacao.item.locador)

    def test_str(self):
        """__str__ deve retornar representação legível."""
        locacao = LocacaoFactory()
        texto = str(locacao)
        self.assertIn('Locação', texto)
        self.assertIn('Solicitado', texto)
