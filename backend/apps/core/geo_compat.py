"""
Módulo de compatibilidade para campos geoespaciais.

Quando GDAL/PostGIS não está disponível (desenvolvimento local com SQLite),
faz fallback para campos normais do Django. Em produção com PostGIS,
usa os campos geoespaciais reais.
"""

import os

USE_SQLITE = os.environ.get("USE_SQLITE", "True").lower() in ("true", "1")

try:
    if USE_SQLITE:
        raise ImportError("Forçando fallback SQLite")

    from django.contrib.gis.db import models as gis_models
    from django.contrib.gis.geos import Point
    from django.contrib.gis.measure import D

    HAS_GIS = True

    # Exportar PointField real
    PointField = gis_models.PointField

except (ImportError, Exception):
    from django.db import models

    HAS_GIS = False

    class PointField(models.CharField):
        """
        Fallback para PointField quando GIS não está disponível.
        Armazena coordenadas como string 'lat,lng'.
        """

        def __init__(self, *args, **kwargs):
            kwargs.pop("geography", None)
            kwargs.pop("spatial_index", None)
            kwargs.pop("srid", None)
            kwargs.setdefault("max_length", 100)
            kwargs.setdefault("blank", True)
            kwargs.setdefault("default", "")
            super().__init__(*args, **kwargs)

    class Point:
        """Fallback para Point."""

        def __init__(self, x=0, y=0, srid=4326):
            self.x = x
            self.y = y
            self.srid = srid

        def __str__(self):
            return f"POINT ({self.x} {self.y})"

    class D:
        """Fallback para Distance."""

        def __init__(self, **kwargs):
            self.km = kwargs.get("km", 0)
            self.m = kwargs.get("m", 0)
