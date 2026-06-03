"""Admin do módulo de Notificações do Aloogaí."""

from django.contrib import admin

from .models import Notificacao


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    """Admin para notificações."""

    list_display = [
        'titulo',
        'usuario',
        'tipo',
        'lida',
        'created_at',
    ]
    list_filter = ['tipo', 'lida', 'created_at']
    search_fields = [
        'titulo',
        'mensagem',
        'usuario__first_name',
        'usuario__last_name',
        'usuario__email',
    ]
    readonly_fields = ['created_at']
    raw_id_fields = ['usuario']

    actions = ['marcar_como_lida']

    def marcar_como_lida(self, request, queryset):
        """Ação para marcar notificações selecionadas como lidas."""
        atualizado = queryset.filter(lida=False).update(lida=True)
        self.message_user(
            request, f'{atualizado} notificação(ões) marcada(s) como lida(s).'
        )
    marcar_como_lida.short_description = 'Marcar como lida'
