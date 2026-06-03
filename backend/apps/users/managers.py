from django.contrib.auth.models import UserManager


class UsuarioManager(UserManager):
    """
    Manager customizado para o modelo Usuario.

    Estende o UserManager padrão do Django para garantir que
    o campo cpf_cnpj seja obrigatório na criação de usuários
    e superusuários.
    """

    def create_user(self, username, email=None, password=None, **extra_fields):
        """
        Cria e retorna um usuário comum.

        Garante que cpf_cnpj e telefone sejam fornecidos
        na criação do usuário.
        """
        if not extra_fields.get('cpf_cnpj'):
            raise ValueError('O campo CPF/CNPJ é obrigatório.')
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        Cria e retorna um superusuário.

        Define valores padrão para campos obrigatórios caso não
        sejam fornecidos (facilita criação via createsuperuser).
        """
        extra_fields.setdefault('cpf_cnpj', '00000000000')
        extra_fields.setdefault('telefone', '00000000000')
        extra_fields.setdefault('kyc_status', 'APROVADO')
        return super().create_superuser(username, email, password, **extra_fields)

    def locadores_ativos(self):
        """Retorna queryset de usuários aptos a serem locadores."""
        return self.filter(
            kyc_status='APROVADO',
            stripe_onboarding_complete=True,
            is_active=True,
        )

    def por_tipo(self, tipo: str):
        """Filtra usuários por tipo (P2P ou B2B)."""
        return self.filter(tipo_usuario=tipo, is_active=True)
