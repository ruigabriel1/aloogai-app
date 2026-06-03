"""
Configurações base do Django para o projeto Aloogaí.

Marketplace P2P/B2B de locação por proximidade.
Estas configurações são compartilhadas entre todos os ambientes (dev, prod).
Configurações específicas de ambiente ficam em dev.py e prod.py.

Para mais informações sobre configurações do Django, consulte:
https://docs.djangoproject.com/5.1/ref/settings/
"""

import os
from datetime import timedelta
from pathlib import Path

import environ

# ==============================================================================
# Caminhos do Projeto
# ==============================================================================

# backend/config/settings/base.py → backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ==============================================================================
# Variáveis de Ambiente
# ==============================================================================

env = environ.Env(
    # Valores padrão seguros para variáveis booleanas
    DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, []),
    CORS_ALLOW_ALL_ORIGINS=(bool, False),
)

# Carrega o arquivo .env se existir (não obrigatório em produção)
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

# ==============================================================================
# Segurança
# ==============================================================================

SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env("DEBUG")

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

# ==============================================================================
# Aplicações Instaladas
# ==============================================================================

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_gis",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "django_fsm",
    "django_extensions",
    "storages",
    "channels",
]

LOCAL_APPS = [
    "apps.users",
    "apps.catalog",
    "apps.rentals",
    "apps.payments",
    "apps.chat",
    "apps.esg",
    "apps.notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ==============================================================================
# Middleware
# ==============================================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

# ==============================================================================
# URLs & ASGI/WSGI
# ==============================================================================

ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"
WSGI_APPLICATION = "config.wsgi.application"

# ==============================================================================
# Templates
# ==============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ==============================================================================
# Banco de Dados — PostgreSQL + PostGIS
# ==============================================================================
# SRID 4326 (WGS84) é obrigatório para todos os campos geoespaciais.
# Usar geography=True nos PointFields + ST_DWithin com índice GiST.

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": env("POSTGRES_DB", default="aloogai_db"),
        "USER": env("POSTGRES_USER", default="aloogai"),
        "PASSWORD": env("POSTGRES_PASSWORD", default=""),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        "CONN_MAX_AGE": env.int("POSTGRES_CONN_MAX_AGE", default=60),
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================================================================
# Modelo de Usuário Customizado
# ==============================================================================

AUTH_USER_MODEL = "users.Usuario"

# ==============================================================================
# Validação de Senhas
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ==============================================================================
# Internacionalização — pt-BR
# ==============================================================================
# App 100% em pt-BR conforme gemini.md. i18n-ready para o futuro.

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = [BASE_DIR / "locale"]

# ==============================================================================
# Arquivos Estáticos (CSS, JavaScript, Imagens)
# ==============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# ==============================================================================
# Arquivos de Mídia (uploads de usuários)
# ==============================================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==============================================================================
# Django REST Framework
# ==============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework_gis.renderers.GeoJSONRenderer",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
    "DATE_FORMAT": "%Y-%m-%d",
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
}

# ==============================================================================
# SimpleJWT — Tokens de Acesso e Refresh
# ==============================================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_TYPE_CLAIM": "token_type",
}

# ==============================================================================
# CORS — Cross-Origin Resource Sharing
# ==============================================================================

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=False)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# ==============================================================================
# Django Channels — WebSocket (Chat em Tempo Real)
# ==============================================================================

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379/0")],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}

# ==============================================================================
# Celery — Fila de Tarefas Assíncronas
# ==============================================================================

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env(
    "CELERY_RESULT_BACKEND", default="redis://localhost:6379/2"
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutos
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutos (aviso antes do hard limit)
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# ==============================================================================
# Redis — Cache
# ==============================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/3"),
        "OPTIONS": {
            "db": 3,
        },
    },
}

# ==============================================================================
# Armazenamento de Arquivos (S3 / GCS)
# ==============================================================================
# Configuração desativada no dev (usa filesystem local).
# Ativada em prod.py com django-storages + boto3.

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="aloogai-media")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="sa-east-1")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = True
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}

# ==============================================================================
# Stripe Connect — Pagamentos e Split
# ==============================================================================

STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")

# ==============================================================================
# Regras de Negócio — Aloogaí (Invariantes do gemini.md)
# ==============================================================================
# Taxa de Serviço (Locatário): 10% sobre valor da diária
# Taxa de Sucesso (Locador): 15% sobre valor recebido (retido no split)

ALOOGAI_TAXA_SERVICO_LOCATARIO = env.float(
    "ALOOGAI_TAXA_SERVICO_LOCATARIO", default=0.10
)
ALOOGAI_TAXA_SUCESSO_LOCADOR = env.float(
    "ALOOGAI_TAXA_SUCESSO_LOCADOR", default=0.15
)

# ==============================================================================
# Logging
# ==============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {module}.{funcName}:{lineno} — {message}",
            "style": "{",
        },
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
AUTHENTICATION_BACKENDS = ['apps.users.backends.EmailBackend', 'django.contrib.auth.backends.ModelBackend']
