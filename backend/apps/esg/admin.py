"""Admin do módulo ESG do Aloogaí."""

from django.contrib import admin

from .models import FatorESGCategoria, HistoricoESG, SeloESG, UsuarioSelo


@admin.register(FatorESGCategoria)
class FatorESGCategoriaAdmin(admin.ModelAdmin):
    """Admin para fatores de CO₂ por categoria."""

    list_display = [
        'categoria',
        'co2_fabricacao_kg',
        'fator_reuso',
        'reducao_frete_kg',
        'co2_estimado_por_dia',
    ]
    list_editable = ['co2_fabricacao_kg', 'fator_reuso', 'reducao_frete_kg']
    search_fields = ['categoria__nome']

    def co2_estimado_por_dia(self, obj):
        """Mostra o CO₂ economizado estimado por dia de locação."""
        valor = (obj.co2_fabricacao_kg * obj.fator_reuso) + obj.reducao_frete_kg
        return f'{valor:.2f} kg'
    co2_estimado_por_dia.short_description = 'CO₂/dia estimado'


@admin.register(HistoricoESG)
class HistoricoESGAdmin(admin.ModelAdmin):
    """Admin para histórico de cálculos ESG."""

    list_display = [
        'usuario',
        'locacao',
        'co2_economizado',
        'score_anterior',
        'score_novo',
        'created_at',
    ]
    list_filter = ['created_at']
    search_fields = [
        'usuario__first_name',
        'usuario__last_name',
        'usuario__email',
    ]
    readonly_fields = [
        'usuario',
        'locacao',
        'co2_economizado',
        'score_anterior',
        'score_novo',
        'created_at',
    ]
    raw_id_fields = ['usuario', 'locacao']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SeloESG)
class SeloESGAdmin(admin.ModelAdmin):
    """Admin para selos ecológicos."""

    list_display = [
        'nome',
        'icone',
        'requisito_locacoes',
        'requisito_score',
        'total_usuarios',
    ]
    search_fields = ['nome']

    def total_usuarios(self, obj):
        """Total de usuários com este selo."""
        return obj.usuarios.count()
    total_usuarios.short_description = 'Usuários'


@admin.register(UsuarioSelo)
class UsuarioSeloAdmin(admin.ModelAdmin):
    """Admin para selos desbloqueados por usuários."""

    list_display = ['usuario', 'selo', 'desbloqueado_em']
    list_filter = ['selo', 'desbloqueado_em']
    search_fields = [
        'usuario__first_name',
        'usuario__last_name',
    ]
    raw_id_fields = ['usuario', 'selo']
