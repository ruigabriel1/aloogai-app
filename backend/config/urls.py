"""
Configuração de URLs do projeto Aloogaí.

Roteamento principal da API versionada (/api/v1/) e Django Admin.
Todas as rotas de apps são incluídas sob o namespace 'api/v1/'.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# ==============================================================================
# URLs da API v1
# ==============================================================================

api_v1_patterns = [
    # --- Autenticação JWT ---
    path(
        "auth/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "auth/token/verify/",
        TokenVerifyView.as_view(),
        name="token_verify",
    ),
    # --- Apps ---
    path("users/", include("apps.users.urls", namespace="users")),
    path("catalog/", include("apps.catalog.urls", namespace="catalog")),
    path("rentals/", include("apps.rentals.urls", namespace="rentals")),
    path("payments/", include("apps.payments.urls", namespace="payments")),
    path("chat/", include("apps.chat.urls", namespace="chat")),
    path("esg/", include("apps.esg.urls", namespace="esg")),
    path(
        "notifications/",
        include("apps.notifications.urls", namespace="notifications"),
    ),
]

# ==============================================================================
# URLs Raiz
# ==============================================================================

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),
    # API v1
    path("api/v1/", include((api_v1_patterns, "api"), namespace="api-v1")),
    # Stripe Webhook (fora do namespace versionado — URL fixa)
    path(
        "webhooks/stripe/",
        __import__("apps.payments.views", fromlist=["StripeWebhookView"]).StripeWebhookView.as_view(),
        name="stripe-webhook",
    ),
]

# ==============================================================================
# Servir arquivos de mídia em desenvolvimento
# ==============================================================================

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug Toolbar
    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# ==============================================================================
# Personalização do Django Admin
# ==============================================================================

admin.site.site_header = "Aloogaí — Painel Administrativo"
admin.site.site_title = "Aloogaí Admin"
admin.site.index_title = "Gerenciamento do Marketplace"
