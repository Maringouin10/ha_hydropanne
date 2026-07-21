"""Coordinateur de mise à jour des données pour Hydro-Panne."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import HydroPanneApiClient, HydroPanneApiError
from .const import DEFAULT_RADIUS, DEFAULT_SCAN_INTERVAL, DOMAIN
from .geo import haversine_m, parse_coordinates

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

# Format positionnel d'une panne dans le tableau « pannes » de l'API v3_0 :
#   [nb_clients, début, rétablissement, type, "[lon, lat]", statut, …]
_IDX_CUSTOMERS = 0  # nombre de clients touchés
_IDX_START = 1  # début « YYYY-MM-DD HH:MM:SS »
_IDX_END = 2  # rétablissement prévu (peut être vide)
_IDX_TYPE = 3  # « P » = panne (non planifiée), autre = interruption planifiée
_IDX_COORDS = 4  # coordonnées « [lon, lat] »
_IDX_STATUS = 5  # code de statut d'intervention


def _to_int(value: Any) -> int | None:
    """Convertit une valeur en entier, ou ``None`` si impossible/vide."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


@dataclass
class Outage:
    """Représentation normalisée d'une panne."""

    customers: int | None = None
    cause: str | None = None
    start: datetime | None = None
    estimated_restoration: datetime | None = None
    status: str | None = None
    municipality: str | None = None
    region: str | None = None
    planned: bool = False
    affects_home: bool = False
    latitude: float | None = None
    longitude: float | None = None
    distance_m: float | None = None


@dataclass
class HydroPanneData:
    """Résultat agrégé exposé aux entités."""

    is_outage: bool = False
    affected: list[Outage] = field(default_factory=list)
    nearby: list[Outage] = field(default_factory=list)
    estimated_restoration: datetime | None = None
    outage_start: datetime | None = None
    affected_customers: int = 0
    nearby_customers: int = 0
    cause: str | None = None
    planned: bool = False
    last_update: datetime | None = None


class HydroPanneCoordinator(DataUpdateCoordinator[HydroPanneData]):
    """Interroge périodiquement Hydro-Québec et détermine l'état au domicile."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise le coordinateur à partir de l'entrée de configuration."""
        self.entry = entry
        self.latitude: float = entry.data[CONF_LATITUDE]
        self.longitude: float = entry.data[CONF_LONGITUDE]
        self._client = HydroPanneApiClient(async_get_clientsession(hass))
        scan = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan),
        )

    @property
    def radius(self) -> int:
        """Rayon de recherche courant (options puis configuration initiale)."""
        return self.entry.options.get(
            CONF_RADIUS, self.entry.data.get(CONF_RADIUS, DEFAULT_RADIUS)
        )

    async def _async_update_data(self) -> HydroPanneData:
        """Récupère et traite les pannes autour du domicile."""
        try:
            pannes = await self._client.async_get_all_outages()
        except HydroPanneApiError as err:
            raise UpdateFailed(
                f"Erreur de communication avec Hydro-Québec : {err}"
            ) from err
        return self._process(pannes)

    def _process(self, pannes: list[list[Any]]) -> HydroPanneData:
        """Filtre les pannes de la province autour du domicile et agrège."""
        radius = self.radius
        affected: list[Outage] = []

        for panne in pannes:
            outage = self._parse(panne)
            if outage is None or outage.latitude is None:
                continue
            outage.distance_m = haversine_m(
                self.latitude, self.longitude, outage.latitude, outage.longitude
            )
            if outage.distance_m <= radius:
                outage.affects_home = True
                affected.append(outage)

        affected.sort(key=lambda o: o.distance_m or 0.0)

        # Le flux ne fournit qu'un point (centre) par panne, sans polygone :
        # « touche le domicile » et « à proximité » désignent donc le même
        # ensemble, les pannes dont le centre est dans le rayon configuré.
        data = HydroPanneData(
            is_outage=bool(affected),
            affected=affected,
            nearby=affected,
            nearby_customers=sum(o.customers or 0 for o in affected),
            last_update=dt_util.utcnow(),
        )

        if affected:
            data.affected_customers = sum(o.customers or 0 for o in affected)
            ends = [o.estimated_restoration for o in affected if o.estimated_restoration]
            # Le courant n'est rétabli que lorsque la dernière panne l'est.
            data.estimated_restoration = max(ends) if ends else None
            starts = [o.start for o in affected if o.start]
            data.outage_start = min(starts) if starts else None
            data.cause = affected[0].cause
            data.planned = all(o.planned for o in affected)

        return data

    def _parse(self, panne: list[Any]) -> Outage | None:
        """Décode un tableau positionnel « panne » en :class:`Outage`."""
        if not isinstance(panne, list):
            return None

        def at(index: int) -> Any:
            return panne[index] if index < len(panne) else None

        coords = parse_coordinates(at(_IDX_COORDS))
        if coords is None:
            return None
        latitude, longitude = coords

        type_code = str(at(_IDX_TYPE) or "").strip().upper()
        status = str(at(_IDX_STATUS) or "").strip() or None

        return Outage(
            customers=_to_int(at(_IDX_CUSTOMERS)),
            start=self._parse_dt(at(_IDX_START)),
            estimated_restoration=self._parse_dt(at(_IDX_END)),
            status=status,
            # « P » = panne non planifiée ; tout autre code = interruption planifiée.
            planned=type_code not in ("", "P"),
            latitude=latitude,
            longitude=longitude,
        )

    @staticmethod
    def _parse_dt(value: Any) -> datetime | None:
        """Analyse une date « YYYY-MM-DD HH:MM:SS » (naïve, localisée au fuseau HA)."""
        if not value:
            return None
        if isinstance(value, (int, float)):
            return dt_util.utc_from_timestamp(float(value))
        parsed = dt_util.parse_datetime(str(value))
        if parsed is None:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
        return parsed
