"""
URLs REST do app de Chat do Aloogaí.

Endpoints de fallback HTTP para histórico de chat e
criação de mensagens (quando WebSocket não está disponível).
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.chat.views import MensagemViewSet, SalaChatViewSet

app_name = "chat"

router = DefaultRouter()
router.register(r"salas", SalaChatViewSet, basename="sala-chat")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "salas/<uuid:sala_id>/mensagens/",
        MensagemViewSet.as_view({"get": "list", "post": "create"}),
        name="mensagens-list",
    ),
    path(
        "salas/<uuid:sala_id>/mensagens/marcar-lidas/",
        MensagemViewSet.as_view({"post": "marcar_lidas"}),
        name="mensagens-marcar-lidas",
    ),
]
