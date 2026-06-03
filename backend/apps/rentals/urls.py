"""
Configuração de URLs do app de Locações.

Registra o router DRF para o ViewSet de Locações.
Todas as rotas são prefixadas com ``/api/v1/`` no URLConf raiz.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.rentals.views import LocacaoViewSet

app_name = "rentals"

router = DefaultRouter()
router.register(r"locacoes", LocacaoViewSet, basename="locacao")

urlpatterns = [
    path("", include(router.urls)),
]
