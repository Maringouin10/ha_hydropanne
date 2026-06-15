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
from .geo import extract_geometry, point_in_geometry

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

# Le jeu de données est en français ; on accepte plusieurs noms de champ
# possibles afin d'être robuste aux variations du fournisseur de données.
_CUSTOMER_KEYS = ("nbclients", "nb_clients", "clients", "nombre_clients")
_CAUSE_KEYS = ("cause", "cause_panne", "description")
_START_KEYS = ("debut", "date_debut", "datedebut", "heure_debut", "start")
_END_KEYS = (
    "fin_estimee",
    "fin_prevue",
    "date_fin_prevue",
    "date_retablissement",
    "retablissement_prevu",
    "reparation_prevue",
    "fin",
)
_STATUS_KEYS = ("etat", "statut", "status")
_MUNICIPALITY_KEYS = ("municipalite", "ville", "municipality")
_REGION_KEYS = ("region", "regadmin", "region_administrative")
_TYPE_KEYS = ("type", "type_panne", "categorie", "type_interruption")


def _first(record: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Retourne la première valeur non vide parmi ``keys``."""
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
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
            records = await self._client.async_get_outages(
                self.latitude, self.longitude, self.radius
            )
        except HydroPanneApiError as err:
            raise UpdateFailed(
                f"Erreur de communication avec Hydro-Québec : {err}"
            ) from err
        return self._process(records)

    def _process(self, records: list[dict[str, Any]]) -> HydroPanneData:
        """Transforme les enregistrements bruts en données agrégées."""
        affected: list[Outage] = []
        nearby: list[Outage] = []

        for record in records:
            outage = self._parse(record)
            nearby.append(outage)

            geometry = extract_geometry(record.get("geo_shape"))
            if geometry is not None:
                outage.affects_home = point_in_geometry(
                    self.longitude, self.latitude, geometry
                )
            else:
                # Sans polygone, la panne a quand même été retournée dans le
                # rayon de recherche : on la considère comme touchant le domicile.
                outage.affects_home = True

            if outage.affects_home:
                affected.append(outage)

        data = HydroPanneData(
            is_outage=bool(affected),
            affected=affected,
            nearby=nearby,
            nearby_customers=sum(o.customers or 0 for o in nearby),
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

    def _parse(self, record: dict[str, Any]) -> Outage:
        """Construit une :class:`Outage` à partir d'un enregistrement brut."""
        raw_customers = _first(record, _CUSTOMER_KEYS)
        try:
            customers = int(raw_customers) if raw_customers is not None else None
        except (ValueError, TypeError):
            customers = None

        type_text = " ".join(
            str(record.get(key))
            for key in (*_TYPE_KEYS, *_STATUS_KEYS)
            if record.get(key)
        ).lower()
        planned = "planif" in type_text or "interruption" in type_text

        return Outage(
            customers=customers,
            cause=_first(record, _CAUSE_KEYS),
            start=self._parse_dt(_first(record, _START_KEYS)),
            estimated_restoration=self._parse_dt(_first(record, _END_KEYS)),
            status=_first(record, _STATUS_KEYS),
            municipality=_first(record, _MUNICIPALITY_KEYS),
            region=_first(record, _REGION_KEYS),
            planned=planned,
        )

    @staticmethod
    def _parse_dt(value: Any) -> datetime | None:
        """Analyse une date ISO 8601 ; les dates naïves sont localisées (fuseau HA)."""
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
