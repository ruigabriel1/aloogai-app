from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.users.views import (
    DocumentoKYCViewSet,
    EnderecoViewSet,
    PerfilView,
    RegistroView,
)

app_name = 'users'

router = DefaultRouter()
router.register(r'enderecos', EnderecoViewSet, basename='endereco')
router.register(r'documentos-kyc', DocumentoKYCViewSet, basename='documento-kyc')

urlpatterns = [
    path('registro/', RegistroView.as_view(), name='registro'),
    path('perfil/', PerfilView.as_view(), name='perfil'),
    path('', include(router.urls)),
]
