"""Capteur binaire « Panne d'électricité » pour Hydro-Panne."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HydroPanneConfigEntry
from .entity import HydroPanneEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HydroPanneConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure le capteur binaire de panne."""
    async_add_entities([HydroPannePowerOutageBinarySensor(entry.runtime_data)])


class HydroPannePowerOutageBinarySensor(HydroPanneEntity, BinarySensorEntity):
    """Indique s'il y a actuellement une panne au domicile."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator) -> None:
        """Initialise le capteur binaire."""
        super().__init__(coordinator, "power_outage")

    @property
    def is_on(self) -> bool:
        """Vrai lorsqu'au moins une panne touche le domicile."""
        return self.coordinator.data.is_outage

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Détails sur la (les) panne(s) en cours au domicile."""
        data = self.coordinator.data
        attrs: dict[str, object] = {
            "affected_outages": len(data.affected),
            "nearby_outages": len(data.nearby),
            "affected_customers": data.affected_customers,
            "cause": data.cause,
            "planned": data.planned,
        }
        if data.estimated_restoration is not None:
            attrs["estimated_restoration"] = data.estimated_restoration.isoformat()
        if data.outage_start is not None:
            attrs["outage_start"] = data.outage_start.isoformat()
        return attrs
