"""Outils géométriques sans dépendance : distance et lecture de coordonnées.

Le flux temps réel d'Hydro-Québec ne fournit qu'un point (centre) par panne,
et non un polygone de zone touchée. On détermine donc si une panne concerne le
domicile en comparant la distance orthodromique (« haversine ») entre le point
de la panne et le domicile au rayon de recherche configuré. On évite ainsi
toute dépendance lourde comme shapely.
"""

from __future__ import annotations

import json
import math
from typing import Any

_EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance en mètres entre deux points (latitudes/longitudes en degrés)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * _EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


def parse_coordinates(raw: Any) -> tuple[float, float] | None:
    """Lit le champ coordonnées de l'API v3_0, au format ``"[lon, lat]"``.

    Retourne ``(latitude, longitude)`` ou ``None`` si la valeur est illisible.
    Attention : l'API place la **longitude en premier** (convention GeoJSON).
    """
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            return None
    if not isinstance(raw, (list, tuple)) or len(raw) < 2:
        return None
    try:
        lon = float(raw[0])
        lat = float(raw[1])
    except (ValueError, TypeError):
        return None
    return lat, lon
