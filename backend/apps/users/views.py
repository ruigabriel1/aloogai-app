from rest_framework import generics, permissions, viewsets

from apps.users.models import DocumentoKYC, Endereco, Usuario
from apps.users.serializers import (
    DocumentoKYCSerializer,
    EnderecoSerializer,
    UsuarioPerfilSerializer,
    UsuarioRegistroSerializer,
)


class RegistroView(generics.CreateAPIView):
    """
    Endpoint de registro de novo usuário.

    POST /api/v1/users/registro/

    Permite criação de conta sem autenticação.
    Valida CPF/CNPJ, senha segura e dados obrigatórios.
    """

    queryset = Usuario.objects.all()
    serializer_class = UsuarioRegistroSerializer
    permission_classes = [permissions.AllowAny]


class PerfilView(generics.RetrieveUpdateAPIView):
    """
    Endpoint de perfil do usuário autenticado.

    GET /api/v1/users/perfil/ — Retorna dados do perfil
    PATCH /api/v1/users/perfil/ — Atualiza dados editáveis

    Campos como kyc_status, score_esg e stripe_onboarding_complete
    são somente-leitura (gerenciados pelo sistema/admin).
    """

    serializer_class = UsuarioPerfilSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> Usuario:
        """Retorna o usuário autenticado."""
        return self.request.user


class EnderecoViewSet(viewsets.ModelViewSet):
    """
    CRUD de endereços do usuário autenticado.

    GET    /api/v1/users/enderecos/       — Lista endereços
    POST   /api/v1/users/enderecos/       — Cria endereço
    GET    /api/v1/users/enderecos/{id}/   — Detalhe do endereço
    PATCH  /api/v1/users/enderecos/{id}/   — Atualiza endereço
    DELETE /api/v1/users/enderecos/{id}/   — Remove endereço

    Cada usuário só acessa seus próprios endereços.
    Aceita latitude/longitude separados (convertidos para PointField).
    """

    serializer_class = EnderecoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Retorna apenas endereços do usuário autenticado."""
        return Endereco.objects.filter(usuario=self.request.user)


class DocumentoKYCViewSet(viewsets.ModelViewSet):
    """
    CRUD de documentos KYC do usuário autenticado.

    GET    /api/v1/users/documentos-kyc/       — Lista documentos
    POST   /api/v1/users/documentos-kyc/       — Envia documento
    GET    /api/v1/users/documentos-kyc/{id}/   — Detalhe do documento
    DELETE /api/v1/users/documentos-kyc/{id}/   — Remove documento

    Status, motivo de rejeição e analista são gerenciados
    exclusivamente pelo admin. Usuário só faz upload e consulta.
    """

    serializer_class = DocumentoKYCSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        """Retorna apenas documentos do usuário autenticado."""
        return DocumentoKYC.objects.filter(usuario=self.request.user)
