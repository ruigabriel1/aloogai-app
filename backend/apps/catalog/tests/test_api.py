"""
Testes de API do catálogo: permissões (IDOR), publicação, regra PRO e avaliações.
"""
from rest_framework.test import APITestCase

from apps.catalog.models import Avaliacao, Item
from apps.rentals.models import StatusLocacao
from apps.rentals.tests.conftest import (
    CategoriaFactory,
    ItemFactory,
    LocacaoFactory,
    UsuarioFactory,
)

ITENS = '/api/v1/catalog/itens/'
AVALIACOES = '/api/v1/catalog/avaliacoes/'
FOTOS = '/api/v1/catalog/fotos/'


class PermissaoItemTests(APITestCase):
    def setUp(self):
        self.dono = UsuarioFactory()
        self.outro = UsuarioFactory()
        self.item = ItemFactory(locador=self.dono)

    def test_outro_usuario_nao_edita_item_alheio(self):
        self.client.force_authenticate(self.outro)
        resposta = self.client.patch(f'{ITENS}{self.item.id}/', {'titulo': 'invadido'})
        self.assertEqual(resposta.status_code, 404)
        self.item.refresh_from_db()
        self.assertNotEqual(self.item.titulo, 'invadido')

    def test_outro_usuario_nao_apaga_item_alheio(self):
        self.client.force_authenticate(self.outro)
        resposta = self.client.delete(f'{ITENS}{self.item.id}/')
        self.assertEqual(resposta.status_code, 404)
        self.assertTrue(Item.objects.filter(id=self.item.id).exists())

    def test_dono_edita_o_proprio_item(self):
        self.client.force_authenticate(self.dono)
        resposta = self.client.patch(f'{ITENS}{self.item.id}/', {'titulo': 'Furadeira nova'})
        self.assertEqual(resposta.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.titulo, 'Furadeira nova')

    def test_anonimo_nao_ve_rascunho_pelo_id(self):
        rascunho = ItemFactory(locador=self.dono, status='RASCUNHO')
        resposta = self.client.get(f'{ITENS}{rascunho.id}/')
        self.assertEqual(resposta.status_code, 404)

    def test_meus_itens_traz_so_os_do_usuario_em_qualquer_status(self):
        ItemFactory(locador=self.dono, status='RASCUNHO')
        ItemFactory(locador=self.outro)
        self.client.force_authenticate(self.dono)
        resposta = self.client.get(ITENS, {'meus': 'true'})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['count'], 2)


class CriacaoItemTests(APITestCase):
    def setUp(self):
        self.usuario = UsuarioFactory()
        self.categoria = CategoriaFactory()
        self.client.force_authenticate(self.usuario)

    def _payload(self, **extra):
        dados = {
            'titulo': 'Barraca 4 pessoas',
            'descricao': 'Barraca para camping',
            'categoria': str(self.categoria.id),
            'preco_diaria': '30.00',
            'valor_caucao': '200.00',
            'latitude': -27.59,
            'longitude': -48.55,
        }
        dados.update(extra)
        return dados

    def test_item_criado_ja_aparece_na_listagem(self):
        resposta = self.client.post(ITENS, self._payload(), format='json')
        self.assertEqual(resposta.status_code, 201, resposta.data)
        item = Item.objects.get(id=resposta.data['id'])
        self.assertEqual(item.status, 'ATIVO')
        self.assertEqual(item.locador, self.usuario)
        self.assertTrue(item.visivel_no_mapa)

    def test_item_pro_nasce_sem_aprovacao(self):
        resposta = self.client.post(ITENS, self._payload(camada='PRO'), format='json')
        self.assertEqual(resposta.status_code, 201, resposta.data)
        item = Item.objects.get(id=resposta.data['id'])
        self.assertFalse(item.aprovado_para_uso)
        self.assertTrue(item.requer_licenca)
        self.assertFalse(item.visivel_no_mapa)

    def test_trocar_camada_para_pro_exige_nova_aprovacao(self):
        item = ItemFactory(locador=self.usuario, camada='ESSENTIAL', aprovado_para_uso=True)
        resposta = self.client.patch(f'{ITENS}{item.id}/', {'camada': 'PRO'}, format='json')
        self.assertEqual(resposta.status_code, 200, resposta.data)
        item.refresh_from_db()
        self.assertFalse(item.aprovado_para_uso)


class FotoItemTests(APITestCase):
    def test_nao_adiciona_foto_em_item_alheio(self):
        dono = UsuarioFactory()
        intruso = UsuarioFactory()
        item = ItemFactory(locador=dono)
        self.client.force_authenticate(intruso)
        resposta = self.client.post(FOTOS, {'item': str(item.id)}, format='multipart')
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('item', resposta.data)


class AvaliacaoTests(APITestCase):
    def setUp(self):
        self.locatario = UsuarioFactory()
        self.locacao = LocacaoFactory(locatario=self.locatario, status=StatusLocacao.CONCLUIDO)

    def test_locatario_avalia_locacao_concluida_e_media_atualiza(self):
        self.client.force_authenticate(self.locatario)
        resposta = self.client.post(
            AVALIACOES, {'locacao': str(self.locacao.id), 'nota': 4}, format='json',
        )
        self.assertEqual(resposta.status_code, 201, resposta.data)
        item = self.locacao.item
        item.refresh_from_db()
        self.assertEqual(item.total_avaliacoes, 1)
        self.assertEqual(item.avaliacao_media, 4.0)

    def test_terceiro_nao_avalia_locacao_alheia(self):
        self.client.force_authenticate(UsuarioFactory())
        resposta = self.client.post(
            AVALIACOES, {'locacao': str(self.locacao.id), 'nota': 1}, format='json',
        )
        self.assertEqual(resposta.status_code, 400)

    def test_nao_avalia_locacao_nao_concluida(self):
        ativa = LocacaoFactory(locatario=self.locatario, status=StatusLocacao.ATIVO)
        self.client.force_authenticate(self.locatario)
        resposta = self.client.post(AVALIACOES, {'locacao': str(ativa.id), 'nota': 5}, format='json')
        self.assertEqual(resposta.status_code, 400)

    def test_terceiro_nao_apaga_avaliacao_alheia(self):
        avaliacao = Avaliacao.objects.create(
            item=self.locacao.item, avaliador=self.locatario, locacao=self.locacao, nota=5,
        )
        self.client.force_authenticate(UsuarioFactory())
        resposta = self.client.delete(f'{AVALIACOES}{avaliacao.id}/')
        self.assertEqual(resposta.status_code, 403)
        self.assertTrue(Avaliacao.objects.filter(id=avaliacao.id).exists())
