"""
Testes unitários para LocacaoService.

Cobre: cálculo de valores, validação de datas e
verificação de disponibilidade de itens.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from apps.rentals.services import LocacaoService

from .conftest import ItemFactory, LocacaoFactory, UsuarioFactory


class TestCalcularNumeroDiarias(TestCase):
    """Testes para LocacaoService.calcular_numero_diarias."""

    def test_calcular_numero_diarias_periodo_normal(self):
        """Período de 3 dias deve retornar 3."""
        inicio = date(2026, 6, 10)
        fim = date(2026, 6, 13)
        resultado = LocacaoService.calcular_numero_diarias(inicio, fim)
        self.assertEqual(resultado, 3)

    def test_calcular_numero_diarias_mesmo_dia(self):
        """Mesmo dia deve retornar mínimo de 1 diária."""
        inicio = date(2026, 6, 10)
        fim = date(2026, 6, 10)
        resultado = LocacaoService.calcular_numero_diarias(inicio, fim)
        self.assertEqual(resultado, 1)

    def test_calcular_numero_diarias_uma_diaria(self):
        """Um dia de diferença deve retornar 1."""
        inicio = date(2026, 6, 10)
        fim = date(2026, 6, 11)
        resultado = LocacaoService.calcular_numero_diarias(inicio, fim)
        self.assertEqual(resultado, 1)


class TestCalcularValores(TestCase):
    """Testes para LocacaoService.calcular_valores."""

    def test_calcular_valores_uma_diaria(self):
        """Uma diária de R$ 25 deve calcular taxas corretamente."""
        resultado = LocacaoService.calcular_valores(
            preco_diaria=Decimal('25.00'),
            data_inicio=date(2026, 6, 10),
            data_fim=date(2026, 6, 11),
            valor_caucao=Decimal('150.00'),
        )

        self.assertEqual(resultado['numero_diarias'], 1)
        self.assertEqual(resultado['valor_diarias'], Decimal('25.00'))
        # Taxa serviço: 25 * 0.10 = 2.50
        self.assertEqual(resultado['valor_taxa_servico'], Decimal('2.50'))
        # Taxa sucesso: 25 * 0.15 = 3.75
        self.assertEqual(resultado['valor_taxa_sucesso'], Decimal('3.75'))
        # Total locatário: 25 + 2.50 = 27.50
        self.assertEqual(resultado['total_locatario'], Decimal('27.50'))
        self.assertEqual(resultado['valor_caucao'], Decimal('150.00'))

    def test_calcular_valores_multiplas_diarias(self):
        """Cinco diárias de R$ 50 deve calcular taxas proporcionalmente."""
        resultado = LocacaoService.calcular_valores(
            preco_diaria=Decimal('50.00'),
            data_inicio=date(2026, 6, 10),
            data_fim=date(2026, 6, 15),
            valor_caucao=Decimal('200.00'),
        )

        self.assertEqual(resultado['numero_diarias'], 5)
        self.assertEqual(resultado['valor_diarias'], Decimal('250.00'))
        # Taxa serviço: 250 * 0.10 = 25.00
        self.assertEqual(resultado['valor_taxa_servico'], Decimal('25.00'))
        # Taxa sucesso: 250 * 0.15 = 37.50
        self.assertEqual(resultado['valor_taxa_sucesso'], Decimal('37.50'))
        # Total locatário: 250 + 25 = 275.00
        self.assertEqual(resultado['total_locatario'], Decimal('275.00'))

    def test_calcular_valores_arredondamento(self):
        """Valores com centavos devem ser arredondados corretamente."""
        resultado = LocacaoService.calcular_valores(
            preco_diaria=Decimal('33.33'),
            data_inicio=date(2026, 6, 10),
            data_fim=date(2026, 6, 13),  # 3 dias
            valor_caucao=Decimal('100.00'),
        )

        self.assertEqual(resultado['numero_diarias'], 3)
        self.assertEqual(resultado['valor_diarias'], Decimal('99.99'))
        # Taxa serviço: 99.99 * 0.10 = 9.999 → 10.00
        self.assertEqual(resultado['valor_taxa_servico'], Decimal('10.00'))


class TestValidarDatas(TestCase):
    """Testes para LocacaoService.validar_datas."""

    def test_validar_datas_validas(self):
        """Datas futuras válidas não devem retornar erros."""
        inicio = date.today() + timedelta(days=1)
        fim = inicio + timedelta(days=3)
        erros = LocacaoService.validar_datas(inicio, fim)
        self.assertEqual(erros, [])

    def test_validar_datas_inicio_no_passado(self):
        """Data de início no passado deve retornar erro."""
        inicio = date.today() - timedelta(days=1)
        fim = date.today() + timedelta(days=3)
        erros = LocacaoService.validar_datas(inicio, fim)
        self.assertTrue(any('passado' in e for e in erros))

    def test_validar_datas_fim_antes_inicio(self):
        """Data de fim antes de início deve retornar erro."""
        inicio = date.today() + timedelta(days=5)
        fim = date.today() + timedelta(days=2)
        erros = LocacaoService.validar_datas(inicio, fim)
        self.assertTrue(any('posterior' in e for e in erros))

    def test_validar_datas_periodo_maior_30_dias(self):
        """Período maior que 30 dias deve retornar erro."""
        inicio = date.today() + timedelta(days=1)
        fim = inicio + timedelta(days=31)
        erros = LocacaoService.validar_datas(inicio, fim)
        self.assertTrue(any('30 dias' in e for e in erros))

    def test_validar_datas_mesmo_dia(self):
        """Mesmo dia (início = fim) deve ser válido."""
        dia = date.today() + timedelta(days=1)
        erros = LocacaoService.validar_datas(dia, dia)
        self.assertEqual(erros, [])


class TestVerificarDisponibilidade(TestCase):
    """Testes para LocacaoService.verificar_disponibilidade."""

    def test_disponivel_sem_conflitos(self):
        """Item sem locações no período deve estar disponível."""
        item = ItemFactory()
        disponivel = LocacaoService.verificar_disponibilidade(
            item_id=item.id,
            data_inicio=date.today() + timedelta(days=10),
            data_fim=date.today() + timedelta(days=12),
        )
        self.assertTrue(disponivel)

    def test_indisponivel_com_conflito(self):
        """Item com locação ativa no mesmo período deve estar indisponível."""
        locacao = LocacaoFactory(
            data_inicio=date.today() + timedelta(days=5),
            data_fim=date.today() + timedelta(days=10),
        )
        disponivel = LocacaoService.verificar_disponibilidade(
            item_id=locacao.item.id,
            data_inicio=date.today() + timedelta(days=7),
            data_fim=date.today() + timedelta(days=12),
        )
        self.assertFalse(disponivel)

    def test_disponivel_periodos_nao_sobrepostos(self):
        """Item com locação em período diferente deve estar disponível."""
        locacao = LocacaoFactory(
            data_inicio=date.today() + timedelta(days=1),
            data_fim=date.today() + timedelta(days=3),
        )
        disponivel = LocacaoService.verificar_disponibilidade(
            item_id=locacao.item.id,
            data_inicio=date.today() + timedelta(days=5),
            data_fim=date.today() + timedelta(days=7),
        )
        self.assertTrue(disponivel)

    def test_disponivel_excluindo_propria_locacao(self):
        """Ao editar, a própria locação não deve contar como conflito."""
        locacao = LocacaoFactory(
            data_inicio=date.today() + timedelta(days=5),
            data_fim=date.today() + timedelta(days=10),
        )
        disponivel = LocacaoService.verificar_disponibilidade(
            item_id=locacao.item.id,
            data_inicio=date.today() + timedelta(days=5),
            data_fim=date.today() + timedelta(days=10),
            excluir_locacao_id=str(locacao.id),
        )
        self.assertTrue(disponivel)
