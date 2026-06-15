"""Entité de base partagée par les plateformes Hydro-Panne."""

from __future__ import annotations

from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONFIGURATION_URL, DOMAIN, MANUFACTURER, MODEL
from .coordinator import HydroPanneCoordinator


class HydroPanneEntity(CoordinatorEntity[HydroPanneCoordinator]):
    """Base regroupant toutes les entités sous un même appareil."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: HydroPanneCoordinator, key: str) -> None:
        """Initialise l'entité avec sa clé de traduction et son identifiant unique."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url=CONFIGURATION_URL,
        )
