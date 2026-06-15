"""Client API pour le jeu de données ouvert des pannes d'Hydro-Québec."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL, API_MAX_RECORDS, API_PAGE_LIMIT, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class HydroPanneApiError(Exception):
    """Levée lorsque l'API de données ouvertes d'Hydro-Québec est injoignable."""


class HydroPanneApiClient:
    """Client asynchrone léger sur l'endpoint records d'OpenDataSoft Explore v2.1."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialise le client avec la session aiohttp partagée de Home Assistant."""
        self._session = session

    async def async_get_outages(
        self, latitude: float, longitude: float, radius_m: int
    ) -> list[dict[str, Any]]:
        """Retourne les pannes dont la zone est à moins de ``radius_m`` du point.

        On filtre côté serveur d'abord sur le polygone (``geo_shape``) puis, en
        repli, sur le point central (``geo_point_2d``) si l'API refuse la requête.
        """
        last_error: Exception | None = None
        for geo_field in ("geo_shape", "geo_point_2d"):
            # WKT : POINT(longitude latitude) — l'axe x est la longitude.
            where = (
                f"within_distance({geo_field}, "
                f"geom'POINT({longitude} {latitude})', {radius_m}m)"
            )
            try:
                return await self._fetch_all(where)
            except aiohttp.ClientResponseError as err:
                last_error = err
                if err.status in (400, 404):
                    _LOGGER.debug(
                        "Filtre géo sur « %s » refusé (%s), tentative de repli",
                        geo_field,
                        err.status,
                    )
                    continue
                raise HydroPanneApiError(str(err)) from err
            except (aiohttp.ClientError, TimeoutError) as err:
                raise HydroPanneApiError(str(err)) from err
        raise HydroPanneApiError(
            f"Aucun filtre géographique accepté par l'API: {last_error}"
        )

    async def _fetch_all(self, where: str) -> list[dict[str, Any]]:
        """Récupère toutes les pages correspondant à la clause ``where``."""
        results: list[dict[str, Any]] = []
        offset = 0
        timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
        while offset < API_MAX_RECORDS:
            params = {
                "where": where,
                "limit": API_PAGE_LIMIT,
                "offset": offset,
            }
            async with self._session.get(
                API_BASE_URL, params=params, timeout=timeout
            ) as resp:
                resp.raise_for_status()
                payload = await resp.json()

            batch = payload.get("results") or []
            results.extend(batch)
            total = payload.get("total_count", len(results))
            offset += API_PAGE_LIMIT
            if len(batch) < API_PAGE_LIMIT or offset >= total:
                break
        return results
