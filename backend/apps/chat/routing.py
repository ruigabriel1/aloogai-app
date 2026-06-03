"""
Roteamento WebSocket do app de Chat do Aloogaí.

Define os padrões de URL para conexões WebSocket de chat.
"""

from django.urls import re_path

from apps.chat.consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/chat/(?P<locacao_id>[0-9a-f-]+)/$",
        ChatConsumer.as_asgi(),
    ),
]
