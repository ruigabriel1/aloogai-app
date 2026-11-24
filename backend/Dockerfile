# Backend do Aloogaí — Django + Channels (ASGI) com PostGIS
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# GDAL/GEOS/PROJ: bibliotecas que o django.contrib.gis exige para falar com o PostGIS
RUN apt-get update \
    && apt-get install -y --no-install-recommends gdal-bin libgeos-c1v5 libproj25 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements/ requirements/
RUN pip install -r requirements/dev.txt -r requirements/prod.txt

COPY . .

EXPOSE 8000

# ASGI: HTTP e WebSocket (chat) no mesmo processo
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
