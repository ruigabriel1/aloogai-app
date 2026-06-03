"""
Configuração do Celery — Projeto Aloogaí.

Inicializa o app Celery com autodiscovery de tarefas
em todos os Django apps registrados.

Para mais informações, consulte:
https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html
"""

import os

from celery import Celery

# Define o módulo de settings padrão do Django para o Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("aloogai")

# Carrega configurações do Django com prefixo CELERY_
# para evitar conflito com outras variáveis de ambiente.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscovery de tarefas em todos os apps registrados
# Procura por arquivos tasks.py em cada app.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarefa de debug — imprime informações da requisição."""
    print(f"Requisição: {self.request!r}")
