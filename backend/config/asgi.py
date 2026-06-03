"""
Configuração ASGI do projeto Aloogaí.

Configura o Django Channels com roteamento de WebSocket para o chat
em tempo real. Usa ProtocolTypeRouter para diferenciar HTTP e WebSocket.

Para mais informações, consulte:
https://channels.readthedocs.io/en/stable/deploying.html
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# Inicializa o Django ANTES de importar as rotas
django_asgi_app = get_asgi_application()

# Importação tardia para garantir que o Django já foi inicializado
from config.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        # Requisições HTTP tradicionais — tratadas pelo Django
        "http": django_asgi_app,
        # Conexões WebSocket — roteadas para os consumers do chat
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        ),
    }
)
