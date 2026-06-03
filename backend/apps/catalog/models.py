import uuid

from django.conf import settings
from django.db import models

from apps.core.geo_compat import PointField


class Categoria(models.Model):
    """
    Categoria de itens para locação.

    Exemplos: Ferramentas, Eletrônicos, Camping, Veículos, etc.
    Cada categoria possui um ícone para exibição no app mobile.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    nome = models.CharField('Nome', max_length=100, unique=True)
    slug = models.SlugField('Slug', max_length=100, unique=True)
    descricao = models.TextField('Descrição', blank=True)
    icone = models.CharField(
        'Ícone',
        max_length=50,
        blank=True,
        help_text='Nome do ícone (ex: wrench, car, tent)',
    )
    ordem = models.PositiveIntegerField('Ordem', default=0)
    ativa = models.BooleanField('Ativa', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class Item(models.Model):
    """
    Item disponível para locação no marketplace Aloogaí.

    Regras de negócio (gemini.md):
    - Itens PRO (requer_licenca=True) iniciam com aprovado_para_uso=False
    - Itens PRO NÃO aparecem no mapa até aprovação manual de admin
    - Geolocalização usa SRID 4326 (WGS84) com geography=True
    - Busca por raio via ST_DWithin + índice GiST
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    CAMADA_CHOICES = [
        ('ESSENTIAL', 'Essential'),
        ('PRO', 'Pro (Regulados)'),
        ('B2B', 'B2B (Lojistas)'),
    ]
    STATUS_CHOICES = [
        ('RASCUNHO', 'Rascunho'),
        ('ATIVO', 'Ativo'),
        ('PAUSADO', 'Pausado'),
        ('INATIVO', 'Inativo'),
    ]

    locador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Locador',
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='itens',
        verbose_name='Categoria',
    )
    titulo = models.CharField('Título', max_length=150)
    descricao = models.TextField('Descrição')
    camada = models.CharField(
        'Camada',
        max_length=10,
        choices=CAMADA_CHOICES,
        default='ESSENTIAL',
    )
    status = models.CharField(
        'Status',
        max_length=10,
        choices=STATUS_CHOICES,
        default='RASCUNHO',
    )

    preco_diaria = models.DecimalField(
        'Preço por diária',
        max_digits=10,
        decimal_places=2,
    )
    valor_caucao = models.DecimalField(
        'Valor da caução',
        max_digits=10,
        decimal_places=2,
    )

    # Geolocalização do item (SRID 4326 / WGS84, geography=True)
    localizacao = PointField(
        'Localização',
        geography=True,
        spatial_index=True,
        srid=4326,
    )
    endereco_texto = models.CharField(
        'Endereço',
        max_length=255,
        blank=True,
        help_text='Endereço legível para exibição.',
    )

    # Controle regulatório (Camada PRO)
    requer_licenca = models.BooleanField(
        'Requer licença',
        default=False,
    )
    documento_licenca = models.FileField(
        'Documento de licença',
        upload_to='licencas/%Y/%m/',
        blank=True,
        null=True,
    )
    aprovado_para_uso = models.BooleanField(
        'Aprovado para uso',
        default=True,
        help_text='Itens PRO iniciam como False até aprovação manual do admin.',
    )

    # Monetização
    is_destacado = models.BooleanField(
        'Destacado',
        default=False,
        help_text='Item impulsionado (pago).',
    )
    destaque_expira_em = models.DateTimeField(
        'Destaque expira em',
        null=True,
        blank=True,
    )

    # Avaliação agregada (cache desnormalizado)
    avaliacao_media = models.FloatField('Avaliação média', default=0.0)
    total_avaliacoes = models.PositiveIntegerField('Total de avaliações', default=0)
    total_locacoes = models.PositiveIntegerField('Total de locações', default=0)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Itens'
        ordering = ['-is_destacado', '-created_at']
        indexes = [
            models.Index(fields=['camada', 'status']),
            models.Index(fields=['-is_destacado', '-created_at']),
        ]

    def __str__(self):
        return f'{self.titulo} ({self.camada}) — {self.locador.get_full_name()}'

    def save(self, *args, **kwargs):
        """
        Aplica regra de negócio: Itens PRO iniciam não aprovados.

        Conforme gemini.md §4.2: Itens da Camada Pro (requer_licenca=True)
        NÃO aparecem no mapa até aprovado_para_uso=True ser setado
        manualmente por um admin.
        """
        if self.camada == 'PRO' and not self.pk:
            self.aprovado_para_uso = False
            self.requer_licenca = True
        super().save(*args, **kwargs)

    @property
    def visivel_no_mapa(self) -> bool:
        """
        Verifica se o item pode aparecer no mapa.

        Item só é visível se:
        1. Status == ATIVO
        2. aprovado_para_uso == True (bloqueio para PRO pendentes)
        """
        return self.status == 'ATIVO' and self.aprovado_para_uso


class FotoItem(models.Model):
    """
    Fotos do item para exibição no anúncio.

    Suporta múltiplas fotos com ordenação e marcação de capa.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='fotos',
        verbose_name='Item',
    )
    imagem = models.ImageField(
        'Imagem',
        upload_to='itens/%Y/%m/',
    )
    is_capa = models.BooleanField('Foto de capa', default=False)
    ordem = models.PositiveIntegerField('Ordem', default=0)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Foto do Item'
        verbose_name_plural = 'Fotos dos Itens'
        ordering = ['-is_capa', 'ordem']

    def __str__(self):
        return f'Foto {self.ordem} — {self.item.titulo}'


class Avaliacao(models.Model):
    """
    Avaliação de uma locação concluída.

    Vinculada a um Item e a uma Locação (OneToOne),
    garantindo uma avaliação por locação.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='avaliacoes',
        verbose_name='Item',
    )
    avaliador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='avaliacoes_feitas',
        verbose_name='Avaliador',
    )
    locacao = models.OneToOneField(
        'rentals.Locacao',
        on_delete=models.CASCADE,
        related_name='avaliacao',
        verbose_name='Locação',
    )
    nota = models.PositiveSmallIntegerField(
        'Nota',
        help_text='Nota de 1 a 5.',
    )
    comentario = models.TextField('Comentário', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        unique_together = ['avaliador', 'locacao']

    def __str__(self):
        return f'Avaliação {self.nota}★ — {self.item.titulo}'
