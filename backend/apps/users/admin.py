from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.users.models import DocumentoKYC, Endereco, Usuario


class EnderecoInline(admin.TabularInline):
    """Inline de endereços na página do usuário."""

    model = Endereco
    extra = 0
    fields = (
        'apelido',
        'logradouro',
        'numero',
        'bairro',
        'cidade',
        'estado',
        'cep',
        'is_principal',
    )
    readonly_fields = ('created_at',)


class DocumentoKYCInline(admin.TabularInline):
    """Inline de documentos KYC na página do usuário."""

    model = DocumentoKYC
    fk_name = 'usuario'
    extra = 0
    fields = (
        'tipo_documento',
        'arquivo',
        'status',
        'motivo_rejeicao',
        'analisado_por',
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Admin customizado para o modelo Usuario.

    Estende o UserAdmin padrão para incluir campos específicos
    do Aloogaí: tipo de usuário, KYC, Stripe, ESG.
    """

    list_display = (
        'username',
        'get_full_name',
        'email',
        'tipo_usuario',
        'kyc_status',
        'score_esg',
        'stripe_onboarding_complete',
        'is_active',
        'created_at',
    )
    list_filter = (
        'tipo_usuario',
        'kyc_status',
        'stripe_onboarding_complete',
        'is_active',
        'is_staff',
    )
    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email',
        'cpf_cnpj',
        'telefone',
    )
    ordering = ('-created_at',)
    inlines = [EnderecoInline, DocumentoKYCInline]

    # Adiciona campos do Aloogaí aos fieldsets do UserAdmin
    fieldsets = UserAdmin.fieldsets + (
        (
            'Dados Aloogaí',
            {
                'fields': (
                    'tipo_usuario',
                    'cpf_cnpj',
                    'telefone',
                    'foto_perfil',
                ),
            },
        ),
        (
            'KYC & Verificação',
            {
                'fields': (
                    'kyc_status',
                    'score_esg',
                ),
            },
        ),
        (
            'Stripe Connect',
            {
                'fields': (
                    'stripe_account_id',
                    'stripe_onboarding_complete',
                ),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'Dados Aloogaí',
            {
                'fields': (
                    'tipo_usuario',
                    'cpf_cnpj',
                    'telefone',
                ),
            },
        ),
    )


@admin.register(Endereco)
class EnderecoAdmin(admin.ModelAdmin):
    """Admin para o modelo Endereco."""

    list_display = (
        'apelido',
        'usuario',
        'logradouro',
        'cidade',
        'estado',
        'is_principal',
        'created_at',
    )
    list_filter = ('estado', 'is_principal')
    search_fields = (
        'logradouro',
        'bairro',
        'cidade',
        'cep',
        'usuario__username',
        'usuario__first_name',
    )
    raw_id_fields = ('usuario',)


@admin.register(DocumentoKYC)
class DocumentoKYCAdmin(admin.ModelAdmin):
    """Admin para o modelo DocumentoKYC."""

    list_display = (
        'usuario',
        'tipo_documento',
        'status',
        'analisado_por',
        'created_at',
        'updated_at',
    )
    list_filter = ('tipo_documento', 'status')
    search_fields = (
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
        'usuario__cpf_cnpj',
    )
    raw_id_fields = ('usuario', 'analisado_por')
    readonly_fields = ('created_at', 'updated_at')

    actions = ['marcar_em_analise', 'aprovar_documento', 'rejeitar_documento']

    @admin.action(description='Marcar como Em Análise')
    def marcar_em_analise(self, request, queryset):
        """Marca os documentos selecionados como Em Análise."""
        atualizado = queryset.update(status='EM_ANALISE')
        self.message_user(
            request,
            f'{atualizado} documento(s) marcado(s) como Em Análise.',
        )

    @admin.action(description='Aprovar documento(s)')
    def aprovar_documento(self, request, queryset):
        """Aprova os documentos selecionados e registra o analista."""
        atualizado = queryset.update(
            status='APROVADO',
            analisado_por=request.user,
        )
        self.message_user(
            request,
            f'{atualizado} documento(s) aprovado(s).',
        )

    @admin.action(description='Rejeitar documento(s)')
    def rejeitar_documento(self, request, queryset):
        """Rejeita os documentos selecionados e registra o analista."""
        atualizado = queryset.update(
            status='REJEITADO',
            analisado_por=request.user,
        )
        self.message_user(
            request,
            f'{atualizado} documento(s) rejeitado(s).',
        )
