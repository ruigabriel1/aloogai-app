"""
Configuração do admin para o app de Locações.

Inclui admin customizado para Locação com inline da timeline,
filtros por status e campos financeiros somente-leitura.
"""
from django.contrib import admin

from apps.rentals.models import Locacao, TimelineLocacao


class TimelineLocacaoInline(admin.TabularInline):
    """Inline da timeline dentro do admin de Locação."""

    model = TimelineLocacao
    extra = 0
    readonly_fields = [
        "id",
        "status_anterior",
        "status_novo",
        "observacao",
        "created_at",
    ]
    ordering = ["-created_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        """Timeline é gerada automaticamente — não permite adição manual."""
        return False


@admin.register(Locacao)
class LocacaoAdmin(admin.ModelAdmin):
    """Admin customizado para o modelo Locação."""

    list_display = [
        "id_curto",
        "item",
        "locatario",
        "status",
        "data_inicio",
        "data_fim",
        "total_locatario",
        "created_at",
    ]
    list_filter = [
        "status",
        "data_inicio",
        "created_at",
    ]
    search_fields = [
        "id",
        "item__titulo",
        "locatario__email",
        "payment_intent_id",
        "caucao_auth_id",
    ]
    readonly_fields = [
        "id",
        "valor_diarias",
        "valor_taxa_servico",
        "valor_taxa_sucesso",
        "total_locatario",
        "valor_caucao",
        "payment_intent_id",
        "caucao_auth_id",
        "co2_evitado",
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        (
            "Informações Gerais",
            {
                "fields": (
                    "id",
                    "item",
                    "locatario",
                    "status",
                    "data_inicio",
                    "data_fim",
                ),
            },
        ),
        (
            "Valores Financeiros",
            {
                "fields": (
                    "valor_diarias",
                    "valor_caucao",
                    "valor_taxa_servico",
                    "valor_taxa_sucesso",
                    "total_locatario",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Stripe",
            {
                "fields": (
                    "payment_intent_id",
                    "caucao_auth_id",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "ESG",
            {
                "fields": ("co2_evitado",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    inlines = [TimelineLocacaoInline]
    list_per_page = 25
    date_hierarchy = "created_at"

    @admin.display(description="ID")
    def id_curto(self, obj: Locacao) -> str:
        """Exibe apenas os primeiros 8 caracteres do UUID."""
        return str(obj.id)[:8]


@admin.register(TimelineLocacao)
class TimelineLocacaoAdmin(admin.ModelAdmin):
    """Admin para visualização direta de eventos da timeline."""

    list_display = [
        "locacao_id_curto",
        "status_anterior",
        "status_novo",
        "observacao_curta",
        "created_at",
    ]
    list_filter = ["status_novo", "created_at"]
    search_fields = ["locacao__id", "observacao"]
    readonly_fields = [
        "id",
        "locacao",
        "status_anterior",
        "status_novo",
        "observacao",
        "created_at",
    ]
    list_per_page = 50

    @admin.display(description="Locação")
    def locacao_id_curto(self, obj: TimelineLocacao) -> str:
        """Exibe apenas os primeiros 8 caracteres do UUID da locação."""
        return str(obj.locacao_id)[:8]

    @admin.display(description="Observação")
    def observacao_curta(self, obj: TimelineLocacao) -> str:
        """Trunca a observação para exibição na listagem."""
        if len(obj.observacao) > 60:
            return f"{obj.observacao[:60]}…"
        return obj.observacao
