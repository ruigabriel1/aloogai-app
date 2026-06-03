"""
Middleware de autenticação JWT para WebSocket do Aloogaí.

Extrai o token JWT do query string da conexão WebSocket e
injeta o usuário autenticado no scope do Channels.

Uso no ASGI config:
    application = ProtocolTypeRouter({
        "websocket": JWTAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        ),
    })
"""

import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


@database_sync_to_async
def _obter_usuario_por_token(token):
    """
    Valida o token JWT e retorna o usuário associado.

    Usa a mesma lógica do Simple JWT para validar o access token
    e obter o usuário.

    Args:
        token: String do token JWT (access token).

    Retorna:
        Instância do modelo Usuario ou AnonymousUser se inválido.
    """
    try:
        from rest_framework_simplejwt.tokens import AccessToken

        access_token = AccessToken(token)
        user_id = access_token["user_id"]

        from django.contrib.auth import get_user_model

        User = get_user_model()
        return User.objects.get(id=user_id)

    except Exception as e:
        logger.warning("Falha na autenticação JWT WebSocket: %s", str(e))
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware de autenticação JWT para conexões WebSocket.

    Extrai o token do query string no formato:
        ws://host/ws/chat/{locacao_id}/?token=<jwt_access_token>

    O usuário autenticado é injetado em self.scope['user'].
    """

    async def __call__(self, scope, receive, send):
        """
        Processa a conexão WebSocket e injeta o usuário autenticado.

        Args:
            scope: Dicionário do escopo da conexão ASGI.
            receive: Callable para receber mensagens.
            send: Callable para enviar mensagens.
        """
        # Extrair query string
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)

        # Extrair token do query string
        token_list = query_params.get("token", [])
        token = token_list[0] if token_list else None

        if token:
            scope["user"] = await _obter_usuario_por_token(token)
            logger.debug(
                "JWT WebSocket: Usuário %s autenticado",
                scope["user"],
            )
        else:
            scope["user"] = AnonymousUser()
            logger.debug("JWT WebSocket: Nenhum token fornecido")

        return await super().__call__(scope, receive, send)
