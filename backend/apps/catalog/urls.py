from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.catalog.views import (
    AvaliacaoViewSet,
    CategoriaListView,
    FotoItemViewSet,
    ItemViewSet,
)

app_name = 'catalog'

router = DefaultRouter()
router.register(r'itens', ItemViewSet, basename='item')
router.register(r'fotos', FotoItemViewSet, basename='foto')
router.register(r'avaliacoes', AvaliacaoViewSet, basename='avaliacao')

urlpatterns = [
    path('categorias/', CategoriaListView.as_view(), name='categorias'),
    path('', include(router.urls)),
]
