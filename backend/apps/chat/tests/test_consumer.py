"""
Testes do WebSocket do chat: autenticação JWT e protocolo de eventos.
"""
from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase, override_settings
from rest_framework_simplejwt.tokens import AccessToken

from apps.chat.middleware import JWTAuthMiddleware
from apps.rentals.tests.conftest import LocacaoFactory
from config.routing import websocket_urlpatterns

aplicacao = JWTAuthMiddleware(URLRouter(websocket_urlpatterns))


def _conectar(locacao_id, usuario=None):
    url = f"/ws/chat/{locacao_id}/"
    if usuario is not None:
        url += f"?token={AccessToken.for_user(usuario)}"
    return WebsocketCommunicator(aplicacao, url)


# Camada em memória: o teste não depende de um Redis rodando
@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
class ChatConsumerTests(TransactionTestCase):
    async def test_sem_token_a_conexao_e_recusada(self):
        locacao = await sync_to_async(LocacaoFactory)()
        comunicador = _conectar(locacao.id)
        conectado, codigo = await comunicador.connect()
        self.assertFalse(conectado)
        self.assertEqual(codigo, 4001)

    async def test_mensagem_chega_aos_dois_participantes_no_formato_da_api(self):
        locacao = await sync_to_async(LocacaoFactory)()
        locador = await sync_to_async(lambda: locacao.item.locador)()
        locatario = await sync_to_async(lambda: locacao.locatario)()

        ws_locatario = _conectar(locacao.id, locatario)
        ws_locador = _conectar(locacao.id, locador)
        self.assertTrue((await ws_locatario.connect())[0])
        self.assertTrue((await ws_locador.connect())[0])

        await ws_locatario.send_json_to({"acao": "mensagem", "conteudo": "Posso buscar amanhã?"})

        for ws in (ws_locatario, ws_locador):
            evento = await ws.receive_json_from(timeout=5)
            self.assertEqual(evento["evento"], "mensagem")
            mensagem = evento["mensagem"]
            self.assertEqual(mensagem["conteudo"], "Posso buscar amanhã?")
            self.assertEqual(mensagem["remetente"], str(locatario.id))
            self.assertIn("created_at", mensagem)

        await ws_locatario.disconnect()
        await ws_locador.disconnect()

    async def test_digitando_vai_so_para_o_outro_participante(self):
        locacao = await sync_to_async(LocacaoFactory)()
        locador = await sync_to_async(lambda: locacao.item.locador)()
        locatario = await sync_to_async(lambda: locacao.locatario)()

        ws_locatario = _conectar(locacao.id, locatario)
        ws_locador = _conectar(locacao.id, locador)
        await ws_locatario.connect()
        await ws_locador.connect()

        await ws_locatario.send_json_to({"acao": "digitando"})
        evento = await ws_locador.receive_json_from(timeout=5)
        self.assertEqual(evento, {"evento": "digitando", "usuario_id": str(locatario.id)})
        self.assertTrue(await ws_locatario.receive_nothing(timeout=0.3))

        await ws_locatario.disconnect()
        await ws_locador.disconnect()
