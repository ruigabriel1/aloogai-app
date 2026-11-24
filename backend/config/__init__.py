# Pacote de configuração do projeto Aloogaí.
# Carrega o app Celery junto com o Django (celery está em requirements/base.txt).
from config.celery import app as celery_app

__all__ = ("celery_app",)
