"""
Configurações de Desenvolvimento do Django — Projeto Aloogaí.

Estende as configurações base com opções otimizadas para
desenvolvimento local: DEBUG=True, CORS aberto, e-mail no console, etc.
"""

import os

from config.settings.base import *  # noqa: F401, F403
from config.settings.base import BASE_DIR, INSTALLED_APPS, REST_FRAMEWORK

# ==============================================================================
# Geral
# ==============================================================================

DEBUG = True

ALLOWED_HOSTS = ["*"]

# ==============================================================================
# Banco de Dados — SQLite para validação local
# ==============================================================================
# Usar SQLite quando PostgreSQL/PostGIS não estiver disponível.
# Para usar PostGIS, defina USE_SQLITE=False e configure o PostgreSQL.

USE_SQLITE = os.environ.get("USE_SQLITE", "True").lower() in ("true", "1")

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    # Remover apps que dependem de GIS/GDAL quando usando SQLite
    GIS_APPS = {"django.contrib.gis", "rest_framework_gis"}
    INSTALLED_APPS = [
        app for app in INSTALLED_APPS
        if app not in GIS_APPS
    ]
    # Remover GeoJSON renderer do DRF quando GIS não está disponível
    REST_FRAMEWORK = {
        **REST_FRAMEWORK,
        "DEFAULT_RENDERER_CLASSES": (
            "rest_framework.renderers.JSONRenderer",
        ),
    }

# ==============================================================================
# CORS — Liberar todas as origens em desenvolvimento
# ==============================================================================

CORS_ALLOW_ALL_ORIGINS = True

# ==============================================================================
# E-mail — Console (para desenvolvimento)
# ==============================================================================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ==============================================================================
# Cache — Em memória para desenvolvimento
# ==============================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "aloogai-dev-cache",
    },
}

# ==============================================================================
# Channels — Em memória para desenvolvimento
# ==============================================================================

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# ==============================================================================
# Logging — Mais verboso em desenvolvimento
# ==============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} — {message}",
            "style": "{",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# ==============================================================================
# Frontend URL (para callbacks Stripe em dev)
# ==============================================================================

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8081")

# ==============================================================================
# Chat — Chave de criptografia para mensagens em repouso (AES-256 / Fernet)
# ==============================================================================
# Chave FIXA para desenvolvimento. Em produção, deve ser gerada e armazenada
# em variável de ambiente. Gere uma nova com:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

CHAT_ENCRYPTION_KEY = os.environ.get(
    "CHAT_ENCRYPTION_KEY",
    "Jds10_5pBwQLBmgS6I3kvfJ6mxyMoIXyDPpe694euQE=",  # DEV ONLY
)
