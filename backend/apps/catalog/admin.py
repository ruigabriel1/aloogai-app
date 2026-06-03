from django.contrib import admin

from apps.catalog.models import Avaliacao, Categoria, FotoItem, Item


class FotoItemInline(admin.TabularInline):
    """Inline de fotos na página do item."""

    model = FotoItem
    extra = 1
    fields = ('imagem', 'is_capa', 'ordem')
    readonly_fields = ('created_at',)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Admin para o modelo Categoria."""

    list_display = ('nome', 'slug', 'icone', 'ordem', 'ativa', 'created_at')
    list_filter = ('ativa',)
    search_fields = ('nome', 'descricao')
    prepopulated_fields = {'slug': ('nome',)}
    ordering = ('ordem', 'nome')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """
    Admin para o modelo Item.

    Inclui ação para aprovar itens PRO pendentes e filtros
    estratégicos para gestão do catálogo.
    """

    list_display = (
        'titulo',
        'locador',
        'categoria',
        'camada',
        'status',
        'preco_diaria',
        'valor_caucao',
        'aprovado_para_uso',
        'is_destacado',
        'avaliacao_media',
        'total_locacoes',
        'created_at',
    )
    list_filter = (
        'camada',
        'status',
        'aprovado_para_uso',
        'is_destacado',
        'categoria',
    )
    search_fields = (
        'titulo',
        'descricao',
        'locador__username',
        'locador__first_name',
        'locador__last_name',
    )
    raw_id_fields = ('locador',)
    readonly_fields = (
        'avaliacao_media',
        'total_avaliacoes',
        'total_locacoes',
        'created_at',
        'updated_at',
    )
    inlines = [FotoItemInline]

    fieldsets = (
        (
            'Informações Básicas',
            {
                'fields': (
                    'locador',
                    'categoria',
                    'titulo',
                    'descricao',
                    'camada',
                    'status',
                ),
            },
        ),
        (
            'Preços',
            {
                'fields': ('preco_diaria', 'valor_caucao'),
            },
        ),
        (
            'Localização',
            {
                'fields': ('localizacao', 'endereco_texto'),
            },
        ),
        (
            'Controle Regulatório (Camada PRO)',
            {
                'fields': (
                    'requer_licenca',
                    'documento_licenca',
                    'aprovado_para_uso',
                ),
                'classes': ('collapse',),
            },
        ),
        (
            'Destaque / Impulsionamento',
            {
                'fields': ('is_destacado', 'destaque_expira_em'),
                'classes': ('collapse',),
            },
        ),
        (
            'Métricas (somente leitura)',
            {
                'fields': (
                    'avaliacao_media',
                    'total_avaliacoes',
                    'total_locacoes',
                    'created_at',
                    'updated_at',
                ),
            },
        ),
    )

    actions = ['aprovar_para_uso', 'revogar_aprovacao', 'destacar_item']

    @admin.action(description='✅ Aprovar item(ns) para uso no mapa')
    def aprovar_para_uso(self, request, queryset):
        """
        Aprova itens PRO pendentes para exibição no mapa.

        Conforme gemini.md §4.2: aprovação obrigatória manual.
        """
        atualizado = queryset.filter(
            aprovado_para_uso=False,
        ).update(aprovado_para_uso=True)
        self.message_user(
            request,
            f'{atualizado} item(ns) aprovado(s) para uso.',
        )

    @admin.action(description='❌ Revogar aprovação de item(ns)')
    def revogar_aprovacao(self, request, queryset):
        """Revoga a aprovação de itens, removendo-os do mapa."""
        atualizado = queryset.update(aprovado_para_uso=False)
        self.message_user(
            request,
            f'{atualizado} item(ns) teve(tiveram) a aprovação revogada.',
        )

    @admin.action(description='⭐ Destacar item(ns)')
    def destacar_item(self, request, queryset):
        """Marca itens como destacados (impulsionados)."""
        atualizado = queryset.update(is_destacado=True)
        self.message_user(
            request,
            f'{atualizado} item(ns) destacado(s).',
        )


@admin.register(FotoItem)
class FotoItemAdmin(admin.ModelAdmin):
    """Admin para o modelo FotoItem."""

    list_display = ('item', 'is_capa', 'ordem', 'created_at')
    list_filter = ('is_capa',)
    search_fields = ('item__titulo',)
    raw_id_fields = ('item',)


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    """Admin para o modelo Avaliacao."""

    list_display = (
        'item',
        'avaliador',
        'nota',
        'created_at',
    )
    list_filter = ('nota',)
    search_fields = (
        'item__titulo',
        'avaliador__username',
        'avaliador__first_name',
        'comentario',
    )
    raw_id_fields = ('item', 'avaliador', 'locacao')
    readonly_fields = ('created_at',)
