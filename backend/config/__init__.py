# Pacote de configuração do projeto Aloogaí.
# Importa o app Celery para garantir que seja carregado junto com o Django.
try:
    from config.celery import app as celery_app

    __all__ = ("celery_app",)
except ImportError:
    # Celery não instalado — pular importação (dev sem Redis)
    __all__ = ()
