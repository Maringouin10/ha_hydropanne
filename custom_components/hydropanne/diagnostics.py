"""Diagnostics pour Hydro-Panne (les coordonnées précises sont tronquées)."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import HydroPanneConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: HydroPanneConfigEntry
) -> dict[str, Any]:
    """Retourne des informations de diagnostic pour une entrée de configuration."""
    coordinator = entry.runtime_data
    data = coordinator.data

    def _dump(outage: Any) -> dict[str, Any]:
        return {
            "customers": outage.customers,
            "cause": outage.cause,
            "start": outage.start.isoformat() if outage.start else None,
            "estimated_restoration": (
                outage.estimated_restoration.isoformat()
                if outage.estimated_restoration
                else None
            ),
            "status": outage.status,
            "municipality": outage.municipality,
            "region": outage.region,
            "planned": outage.planned,
            "affects_home": outage.affects_home,
        }

    return {
        "config": {
            # Coordonnées arrondies pour préserver la vie privée.
            "latitude": round(coordinator.latitude, 2),
            "longitude": round(coordinator.longitude, 2),
            "radius": coordinator.radius,
        },
        "is_outage": data.is_outage,
        "affected_customers": data.affected_customers,
        "nearby_customers": data.nearby_customers,
        "estimated_restoration": (
            data.estimated_restoration.isoformat()
            if data.estimated_restoration
            else None
        ),
        "affected": [_dump(o) for o in data.affected],
        "nearby_count": len(data.nearby),
    }
