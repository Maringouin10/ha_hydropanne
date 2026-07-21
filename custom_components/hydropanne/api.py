"""Client API pour le flux temps réel « Info-pannes » d'Hydro-Québec."""

from __future__ import annotations

import logging
import re
from typing import Any

import aiohttp

from .const import API_HEADERS, API_TIMEOUT, API_VERSION_URL, markers_url

_LOGGER = logging.getLogger(__name__)

# Le numéro de version est un horodatage compact, p. ex. « 20260721153004 ».
_VERSION_RE = re.compile(r"\d{6,}")


class HydroPanneApiError(Exception):
    """Levée lorsque l'API temps réel d'Hydro-Québec est injoignable."""


class HydroPanneApiClient:
    """Client asynchrone du flux Info-pannes v3_0.

    Le flux fonctionne en deux temps : ``bisversion.json`` donne le numéro de
    version courant, puis ``bismarkers<version>.json`` liste toutes les pannes
    de la province sous forme de tableaux positionnels.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialise le client avec la session aiohttp partagée de Home Assistant."""
        self._session = session

    async def async_get_all_outages(self) -> list[list[Any]]:
        """Retourne la liste brute des pannes de toute la province.

        Le filtrage géographique se fait ensuite côté client : ce flux ne
        propose aucun filtre côté serveur.
        """
        try:
            version = await self._fetch_version()
            try:
                return await self._fetch_markers(version)
            except aiohttp.ClientResponseError as err:
                # La version a pu changer entre les deux appels : on réessaie
                # une fois avec un numéro de version rafraîchi.
                if err.status == 404:
                    _LOGGER.debug("Marqueurs %s introuvables (404), nouvel essai", version)
                    version = await self._fetch_version()
                    return await self._fetch_markers(version)
                raise
        except aiohttp.ClientResponseError as err:
            _LOGGER.error(
                "L'API Info-pannes d'Hydro-Québec a répondu HTTP %s (%s)",
                err.status,
                err.message,
            )
            raise HydroPanneApiError(f"HTTP {err.status}: {err.message}") from err
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.error("Échec de communication avec l'API d'Hydro-Québec : %s", err)
            raise HydroPanneApiError(str(err)) from err

    async def _fetch_version(self) -> str:
        """Récupère le numéro de version courant du flux."""
        timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
        async with self._session.get(
            API_VERSION_URL, headers=API_HEADERS, timeout=timeout
        ) as resp:
            resp.raise_for_status()
            text = await resp.text()
        match = _VERSION_RE.search(text)
        if not match:
            raise HydroPanneApiError(
                f"Numéro de version introuvable dans la réponse : {text[:100]!r}"
            )
        return match.group(0)

    async def _fetch_markers(self, version: str) -> list[list[Any]]:
        """Récupère la liste des pannes pour un numéro de version donné."""
        timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
        async with self._session.get(
            markers_url(version), headers=API_HEADERS, timeout=timeout
        ) as resp:
            resp.raise_for_status()
            # Le serveur ne renvoie pas toujours un en-tête JSON strict.
            payload = await resp.json(content_type=None)
        if not isinstance(payload, dict):
            return []
        pannes = payload.get("pannes")
        return pannes if isinstance(pannes, list) else []
