"""URLs do módulo de Notificações do Aloogaí."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'notifications'

router = DefaultRouter()
router.register('', views.NotificacaoViewSet, basename='notificacoes')

urlpatterns = [
    path('', include(router.urls)),
]
