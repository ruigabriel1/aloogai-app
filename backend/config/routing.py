"""
Roteamento WebSocket do Django Channels — Projeto Aloogaí.

Define as rotas de WebSocket para o chat em tempo real.
O chat só é habilitado APÓS uma solicitação de locação
(Locacao.status >= SOLICITADO), conforme gemini.md.
"""

from django.urls import re_path

# Importação tardia do consumer — será criado no app de chat.
# Por enquanto, usamos um placeholder que será substituído
# quando o app apps.chat for implementado.
try:
    from apps.chat.consumers import ChatConsumer

    websocket_urlpatterns = [
        re_path(
            r"ws/chat/(?P<locacao_id>[0-9a-f-]+)/$",
            ChatConsumer.as_asgi(),
        ),
    ]
except ImportError:
    # Placeholder até o app de chat ser implementado
    websocket_urlpatterns = []
