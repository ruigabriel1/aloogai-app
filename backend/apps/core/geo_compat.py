"""
Módulo de compatibilidade para campos geoespaciais.

Com `settings.USE_SQLITE = True` (padrão só no dev local), usa campos de texto no lugar
dos campos do PostGIS. Em qualquer outro caso, usa o PostGIS de verdade e um erro de
GDAL/GEOS aparece na hora, em vez de cair em silêncio para o modo texto.

O PointField daqui se descreve igual nos dois modos (mesmo caminho e mesmos kwargs no
`deconstruct`), então um único conjunto de migrações serve para SQLite e PostGIS.
"""

from django.conf import settings

USE_SQLITE = getattr(settings, "USE_SQLITE", False)

if not USE_SQLITE:
    from django.contrib.gis.db import models as gis_models
    from django.contrib.gis.geos import Point  # noqa: F401
    from django.contrib.gis.measure import D  # noqa: F401

    HAS_GIS = True

    class PointField(gis_models.PointField):
        """PointField do PostGIS, com caminho estável para as migrações."""

else:
    from django.db import models

    HAS_GIS = False

    class PointField(models.CharField):
        """
        Fallback para PointField sem GIS.
        Armazena o ponto como texto WKT: 'POINT (lng lat)'.
        """

        def __init__(self, *args, geography=False, spatial_index=True, srid=4326, **kwargs):
            self._geo = {"geography": geography, "spatial_index": spatial_index, "srid": srid}
            self._injetados = [k for k in ("max_length", "blank", "default") if k not in kwargs]
            kwargs.setdefault("max_length", 100)
            kwargs.setdefault("blank", True)
            kwargs.setdefault("default", "")
            super().__init__(*args, **kwargs)

        def deconstruct(self):
            """Descreve-se como o PointField do GIS descreveria (ver GeometryField.deconstruct)."""
            name, path, args, kwargs = super().deconstruct()
            for chave in self._injetados:
                kwargs.pop(chave, None)
            if self._geo["geography"]:
                kwargs["geography"] = True
            if self._geo["srid"] != 4326:
                kwargs["srid"] = self._geo["srid"]
            if not self._geo["spatial_index"]:
                kwargs["spatial_index"] = False
            return name, path, args, kwargs

    class Point:
        """Fallback para Point (x = longitude, y = latitude)."""

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


def coordenadas(valor) -> tuple[float | None, float | None]:
    """
    Devolve (latitude, longitude) de um ponto, com ou sem GIS.

    Aceita um Point do GEOS ou o texto WKT do modo SQLite ("POINT (lng lat)" ou
    "SRID=4326;POINT(lng lat)").
    """
    import re

    if not valor:
        return None, None
    if hasattr(valor, "x") and hasattr(valor, "y"):
        return float(valor.y), float(valor.x)
    numeros = re.findall(r"-?\d+(?:\.\d+)?", str(valor).split(";")[-1])
    if len(numeros) < 2:
        return None, None
    lng, lat = float(numeros[0]), float(numeros[1])
    return lat, lng


def distancia_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distância em km entre dois pontos (fórmula de haversine)."""
    from math import asin, cos, radians, sin, sqrt

    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 6371.0 * 2 * asin(sqrt(a))
