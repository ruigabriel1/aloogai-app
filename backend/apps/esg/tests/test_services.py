"""
Testes unitários do módulo ESG do Aloogaí.

Cobre: cálculos de CO₂, atualização de scores, verificação
de selos, e o pipeline completo de locação concluída.
"""
from decimal import Decimal

from django.test import TestCase

from apps.esg.models import (
    FatorESGCategoria,
    HistoricoESG,
    SeloESG,
    UsuarioSelo,
)
from apps.esg.services import ESGService
from apps.rentals.tests.conftest import (
    CategoriaFactory,
    ItemFactory,
    LocacaoFactory,
    UsuarioFactory,
)


class TestFatorESGCategoria(TestCase):
    """Testes para o modelo FatorESGCategoria."""

    def test_calcular_co2_com_valores_padrao(self):
        """Fórmula: (co2_fabricacao × fator_reuso) + reducao_frete."""
        categoria = CategoriaFactory()
        fator = FatorESGCategoria.objects.create(
            categoria=categoria,
            co2_fabricacao_kg=10.0,
            fator_reuso=0.7,
            reducao_frete_kg=2.0,
        )
        # 10 * 0.7 + 2 = 9.0
        self.assertAlmostEqual(fator.calcular_co2(), 9.0)

    def test_calcular_co2_sem_reducao_frete(self):
        """Frete zero deve retornar apenas fabricação × reuso."""
        categoria = CategoriaFactory()
        fator = FatorESGCategoria.objects.create(
            categoria=categoria,
            co2_fabricacao_kg=20.0,
            fator_reuso=0.5,
            reducao_frete_kg=0.0,
        )
        # 20 * 0.5 + 0 = 10.0
        self.assertAlmostEqual(fator.calcular_co2(), 10.0)

    def test_str(self):
        """__str__ deve conter nome da categoria."""
        categoria = CategoriaFactory()
        fator = FatorESGCategoria.objects.create(
            categoria=categoria,
            co2_fabricacao_kg=5.0,
        )
        self.assertIn('Fator ESG', str(fator))


class TestESGServiceCalculo(TestCase):
    """Testes para o serviço de cálculo de CO₂."""

    def test_calcular_co2_com_fator_existente(self):
        """Deve usar os fatores da categoria para calcular CO₂."""
        locacao = LocacaoFactory()
        FatorESGCategoria.objects.create(
            categoria=locacao.item.categoria,
            co2_fabricacao_kg=10.0,
            fator_reuso=0.7,
            reducao_frete_kg=1.0,
        )
        # (10 * 0.7 + 1) * dias
        dias = (locacao.data_fim - locacao.data_inicio).days or 1
        esperado = round((10.0 * 0.7 + 1.0) * dias, 2)
        resultado = ESGService.calcular_co2_economizado(locacao)
        self.assertAlmostEqual(resultado, esperado)

    def test_calcular_co2_sem_fator_usa_padrao(self):
        """Sem fator para a categoria, deve usar valores padrão."""
        locacao = LocacaoFactory()
        # Padrões: co2=5.0, fator=0.7, frete=1.0
        dias = (locacao.data_fim - locacao.data_inicio).days or 1
        esperado = round((5.0 * 0.7 + 1.0) * dias, 2)
        resultado = ESGService.calcular_co2_economizado(locacao)
        self.assertAlmostEqual(resultado, esperado)

    def test_calcular_co2_minimo_1_dia(self):
        """Mesmo com 0 dias, deve calcular para no mínimo 1 dia."""
        locacao = LocacaoFactory()
        # Forçar data_inicio == data_fim
        locacao.data_fim = locacao.data_inicio
        locacao.save()

        resultado = ESGService.calcular_co2_economizado(locacao)
        self.assertGreater(resultado, 0)


class TestESGServiceScore(TestCase):
    """Testes para atualização de score ESG."""

    def test_atualizar_score_incrementa(self):
        """Score deve ser incrementado pelo CO₂ economizado."""
        usuario = UsuarioFactory()
        score_inicial = usuario.score_esg
        co2 = 5.5

        anterior, novo = ESGService.atualizar_score_usuario(usuario, co2)

        self.assertEqual(anterior, score_inicial)
        self.assertAlmostEqual(novo, score_inicial + co2)

    def test_atualizar_score_acumulativo(self):
        """Múltiplas atualizações devem acumular."""
        usuario = UsuarioFactory()

        ESGService.atualizar_score_usuario(usuario, 3.0)
        ESGService.atualizar_score_usuario(usuario, 7.0)

        usuario.refresh_from_db()
        self.assertAlmostEqual(usuario.score_esg, 10.0)


class TestESGServiceHistorico(TestCase):
    """Testes para registro de histórico ESG."""

    def test_registrar_historico(self):
        """Deve criar registro no HistoricoESG."""
        locacao = LocacaoFactory()
        usuario = locacao.locatario

        historico = ESGService.registrar_historico(
            usuario=usuario,
            locacao=locacao,
            co2_economizado=5.0,
            score_anterior=0.0,
            score_novo=5.0,
        )

        self.assertEqual(historico.co2_economizado, 5.0)
        self.assertEqual(historico.score_anterior, 0.0)
        self.assertEqual(historico.score_novo, 5.0)

    def test_historico_str(self):
        """__str__ deve conter dados relevantes."""
        locacao = LocacaoFactory()
        historico = ESGService.registrar_historico(
            usuario=locacao.locatario,
            locacao=locacao,
            co2_economizado=3.5,
            score_anterior=0.0,
            score_novo=3.5,
        )
        self.assertIn('CO₂', str(historico))


class TestESGServiceSelos(TestCase):
    """Testes para verificação de selos."""

    def setUp(self):
        """Criar selos de teste."""
        self.selo_verde = SeloESG.objects.create(
            nome='Vizinho Verde',
            descricao='10 locações concluídas',
            icone='🌱',
            requisito_locacoes=10,
            requisito_score=0.0,
        )
        self.selo_heroi = SeloESG.objects.create(
            nome='Herói Circular',
            descricao='50 locações concluídas',
            icone='♻️',
            requisito_locacoes=50,
            requisito_score=0.0,
        )
        self.selo_estrela = SeloESG.objects.create(
            nome='Estrela Sustentável',
            descricao='Score ESG >= 100',
            icone='⭐',
            requisito_locacoes=0,
            requisito_score=100.0,
        )

    def test_usuario_sem_selos_inicialmente(self):
        """Usuário novo não deve ter nenhum selo."""
        usuario = UsuarioFactory()
        selos = ESGService.verificar_selos(usuario)
        self.assertEqual(len(selos), 0)

    def test_desbloquear_selo_por_score(self):
        """Deve desbloquear selo quando score é suficiente."""
        usuario = UsuarioFactory()
        usuario.score_esg = 150.0
        usuario.save()

        selos = ESGService.verificar_selos(usuario)
        nomes = [s.nome for s in selos]
        self.assertIn('Estrela Sustentável', nomes)

    def test_nao_desbloquear_selo_duplicado(self):
        """Selo já desbloqueado não deve ser desbloqueado novamente."""
        usuario = UsuarioFactory()
        usuario.score_esg = 150.0
        usuario.save()

        ESGService.verificar_selos(usuario)
        selos_segunda_vez = ESGService.verificar_selos(usuario)
        self.assertEqual(len(selos_segunda_vez), 0)

    def test_selo_str(self):
        """__str__ do selo deve conter ícone e nome."""
        self.assertIn('🌱', str(self.selo_verde))
        self.assertIn('Vizinho Verde', str(self.selo_verde))


class TestESGPipelineCompleto(TestCase):
    """Testes para o pipeline completo de processamento ESG."""

    def setUp(self):
        """Criar selo para teste de pipeline."""
        SeloESG.objects.create(
            nome='Estrela Sustentável',
            descricao='Score ESG >= 100',
            icone='⭐',
            requisito_locacoes=0,
            requisito_score=100.0,
        )

    def test_processar_locacao_retorna_resumo(self):
        """Pipeline deve retornar resumo com co2, scores e selos."""
        locacao = LocacaoFactory()
        resultado = ESGService.processar_locacao_concluida(locacao)

        self.assertIn('co2_economizado', resultado)
        self.assertIn('locatario', resultado)
        self.assertIn('locador', resultado)
        self.assertGreater(resultado['co2_economizado'], 0)

    def test_processar_locacao_atualiza_co2_evitado(self):
        """Pipeline deve salvar co2_evitado na locação."""
        locacao = LocacaoFactory()
        self.assertEqual(locacao.co2_evitado, 0.0)

        ESGService.processar_locacao_concluida(locacao)
        # Usar query direta em vez de refresh_from_db() para evitar
        # conflito com django-fsm no campo status
        from apps.rentals.models import Locacao
        co2 = Locacao.objects.filter(id=locacao.id).values_list(
            'co2_evitado', flat=True
        ).first()
        self.assertGreater(co2, 0)

    def test_processar_locacao_cria_historico(self):
        """Pipeline deve criar registro no HistoricoESG."""
        locacao = LocacaoFactory()
        ESGService.processar_locacao_concluida(locacao)

        self.assertTrue(
            HistoricoESG.objects.filter(locacao=locacao).exists()
        )

    def test_locador_recebe_metade_co2(self):
        """Locador deve receber 50% do CO₂ economizado."""
        locacao = LocacaoFactory()
        resultado = ESGService.processar_locacao_concluida(locacao)

        co2_total = resultado['co2_economizado']
        co2_locador = resultado['locador']['co2_creditado']
        self.assertAlmostEqual(co2_locador, round(co2_total * 0.5, 2))
