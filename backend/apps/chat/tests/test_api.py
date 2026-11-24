"""
Testes de API do chat: acesso às salas.
"""
from rest_framework.test import APITestCase

from apps.chat.models import SalaChat
from apps.rentals.tests.conftest import LocacaoFactory, UsuarioFactory


class MarcarLidasTests(APITestCase):
    def test_quem_nao_participa_da_sala_recebe_404(self):
        locacao = LocacaoFactory()
        sala = SalaChat.objects.get(locacao=locacao)  # criada pelo signal da locação
        self.client.force_authenticate(UsuarioFactory())
        resposta = self.client.post(f'/api/v1/chat/salas/{sala.id}/mensagens/marcar-lidas/')
        self.assertEqual(resposta.status_code, 404)

    def test_participante_marca_como_lidas(self):
        locacao = LocacaoFactory()
        sala = SalaChat.objects.get(locacao=locacao)
        self.client.force_authenticate(locacao.locatario)
        resposta = self.client.post(f'/api/v1/chat/salas/{sala.id}/mensagens/marcar-lidas/')
        self.assertEqual(resposta.status_code, 200)
