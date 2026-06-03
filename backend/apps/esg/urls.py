"""URLs do módulo ESG do Aloogaí."""

from django.urls import path

from . import views

app_name = 'esg'

urlpatterns = [
    # Dashboard ESG do usuário
    path(
        'dashboard/',
        views.DashboardESGView.as_view(),
        name='dashboard',
    ),

    # Lista todos os selos disponíveis
    path(
        'selos/',
        views.SelosListView.as_view(),
        name='selos-list',
    ),

    # Histórico de cálculos ESG do usuário
    path(
        'historico/',
        views.HistoricoESGView.as_view(),
        name='historico',
    ),
]
