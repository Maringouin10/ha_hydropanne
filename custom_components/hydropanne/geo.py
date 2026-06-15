"""Outils géométriques sans dépendance (test point-dans-polygone).

Les données d'Hydro-Québec exposent la zone touchée par chaque panne sous forme
d'un polygone GeoJSON (champ ``geo_shape``). Pour savoir si le domicile de
l'utilisateur est touché, on vérifie si son point (longitude, latitude) se
trouve à l'intérieur de ce polygone à l'aide de l'algorithme du lancer de rayon
(« ray casting »). On évite ainsi toute dépendance lourde comme shapely.
"""

from __future__ import annotations

from typing import Any


def _point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    """Test du lancer de rayon pour un anneau unique (coordonnées GeoJSON [lon, lat])."""
    n = len(ring)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        denom = (yj - yi) or 1e-16
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / denom + xi
        ):
            inside = not inside
        j = i
    return inside


def _point_in_polygon_coords(lon: float, lat: float, polygon: list) -> bool:
    """``polygon`` = [anneau_extérieur, trou1, trou2, ...]."""
    if not polygon:
        return False
    if not _point_in_ring(lon, lat, polygon[0]):
        return False
    # Un point situé dans un « trou » du polygone n'est pas à l'intérieur.
    return not any(_point_in_ring(lon, lat, hole) for hole in polygon[1:])


def point_in_geometry(
    lon: float, lat: float, geometry: dict[str, Any] | None
) -> bool:
    """Vraie si (lon, lat) est dans une géométrie GeoJSON Polygon/MultiPolygon."""
    if not geometry:
        return False
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if not coords:
        return False
    if geom_type == "Polygon":
        return _point_in_polygon_coords(lon, lat, coords)
    if geom_type == "MultiPolygon":
        return any(_point_in_polygon_coords(lon, lat, poly) for poly in coords)
    return False


def extract_geometry(geo_shape: Any) -> dict[str, Any] | None:
    """Normalise un ``geo_shape`` OpenDataSoft (Feature ou géométrie) en géométrie."""
    if not isinstance(geo_shape, dict):
        return None
    if geo_shape.get("type") == "Feature":
        geom = geo_shape.get("geometry")
        return geom if isinstance(geom, dict) else None
    if isinstance(geo_shape.get("geometry"), dict):
        return geo_shape["geometry"]
    if geo_shape.get("type") in ("Polygon", "MultiPolygon"):
        return geo_shape
    return None
