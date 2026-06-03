"""
Configuração WSGI do projeto Aloogaí.

Ponto de entrada para servidores WSGI compatíveis (Gunicorn, etc.).
Para deploy com WebSocket (chat), use ASGI (config/asgi.py) em vez deste.

Para mais informações, consulte:
https://docs.djangoproject.com/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_wsgi_application()
