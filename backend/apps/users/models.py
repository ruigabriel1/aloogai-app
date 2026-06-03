import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.geo_compat import PointField

from apps.users.managers import UsuarioManager


class Usuario(AbstractUser):
    """
    Usuário do Aloogaí — Locador ou Locatário.

    Estende AbstractUser para incluir campos específicos do marketplace:
    tipo de usuário (P2P/B2B), KYC progressivo, integração Stripe Connect
    e pontuação ESG.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    TIPO_CHOICES = [
        ('P2P', 'Pessoa Física'),
        ('B2B', 'Lojista / Pessoa Jurídica'),
    ]
    tipo_usuario = models.CharField(
        'Tipo de usuário',
        max_length=3,
        choices=TIPO_CHOICES,
        default='P2P',
    )

    cpf_cnpj = models.CharField(
        'CPF/CNPJ',
        max_length=18,
        unique=True,
    )

    telefone = models.CharField(
        'Telefone',
        max_length=20,
    )

    foto_perfil = models.ImageField(
        'Foto de perfil',
        upload_to='perfis/',
        blank=True,
        null=True,
    )

    KYC_STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('EM_ANALISE', 'Em Análise'),
        ('APROVADO', 'Aprovado'),
        ('REJEITADO', 'Rejeitado'),
    ]
    kyc_status = models.CharField(
        'Status KYC',
        max_length=20,
        choices=KYC_STATUS_CHOICES,
        default='PENDENTE',
    )

    score_esg = models.FloatField(
        'Score ESG',
        default=0.0,
        help_text='Pontuação de impacto ambiental acumulada.',
    )

    # Stripe Connect
    stripe_account_id = models.CharField(
        'ID Stripe Connect',
        max_length=100,
        blank=True,
        help_text='ID da conta Stripe Connect do locador.',
    )
    stripe_onboarding_complete = models.BooleanField(
        'Onboarding Stripe concluído',
        default=False,
    )

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    objects = UsuarioManager()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_full_name()} ({self.tipo_usuario})'

    @property
    def is_locador_ativo(self) -> bool:
        """
        Verifica se o usuário pode atuar como locador.

        Retorna True apenas se o KYC está aprovado E o onboarding
        do Stripe Connect foi concluído.
        """
        return self.kyc_status == 'APROVADO' and self.stripe_onboarding_complete


class Endereco(models.Model):
    """
    Endereço do usuário com geolocalização.

    Utiliza PostGIS PointField com SRID 4326 (WGS84) e geography=True
    para buscas por proximidade precisas em metros.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='enderecos',
        verbose_name='Usuário',
    )
    apelido = models.CharField(
        'Apelido',
        max_length=50,
        default='Casa',
        help_text='Ex: Casa, Trabalho',
    )
    logradouro = models.CharField('Logradouro', max_length=255)
    numero = models.CharField('Número', max_length=20)
    complemento = models.CharField('Complemento', max_length=100, blank=True)
    bairro = models.CharField('Bairro', max_length=100)
    cidade = models.CharField('Cidade', max_length=100)
    estado = models.CharField('Estado', max_length=2)
    cep = models.CharField('CEP', max_length=9)
    localizacao = PointField(
        'Localização',
        geography=True,
        spatial_index=True,
        srid=4326,
    )
    is_principal = models.BooleanField('Endereço principal', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'
        ordering = ['-is_principal', '-created_at']

    def __str__(self):
        return f'{self.apelido} — {self.logradouro}, {self.cidade}/{self.estado}'


class DocumentoKYC(models.Model):
    """
    Documento de verificação de identidade (KYC progressivo).

    Níveis de KYC conforme gemini.md:
    - P2P Essential: CPF + selfie
    - P2P Pro: CPF + selfie + licença do item
    - B2B: CNPJ + contrato social + selfie do responsável
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    TIPO_DOC_CHOICES = [
        ('CPF', 'CPF'),
        ('CNPJ', 'CNPJ'),
        ('SELFIE', 'Selfie'),
        ('LICENCA', 'Licença/Habilitação'),
        ('CONTRATO_SOCIAL', 'Contrato Social'),
    ]
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='documentos_kyc',
        verbose_name='Usuário',
    )
    tipo_documento = models.CharField(
        'Tipo de documento',
        max_length=20,
        choices=TIPO_DOC_CHOICES,
    )
    arquivo = models.FileField(
        'Arquivo',
        upload_to='kyc/%Y/%m/',
    )

    STATUS_CHOICES = [
        ('ENVIADO', 'Enviado'),
        ('EM_ANALISE', 'Em Análise'),
        ('APROVADO', 'Aprovado'),
        ('REJEITADO', 'Rejeitado'),
    ]
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='ENVIADO',
    )
    motivo_rejeicao = models.TextField('Motivo da rejeição', blank=True)
    analisado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_analisados',
        verbose_name='Analisado por',
    )

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Documento KYC'
        verbose_name_plural = 'Documentos KYC'

    def __str__(self):
        return f'{self.tipo_documento} — {self.usuario.get_full_name()} ({self.status})'
