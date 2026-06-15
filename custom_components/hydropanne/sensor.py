"""Capteurs pour Hydro-Panne (rétablissement estimé, clients touchés, etc.)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HydroPanneConfigEntry
from .coordinator import HydroPanneData
from .entity import HydroPanneEntity


@dataclass(frozen=True, kw_only=True)
class HydroPanneSensorEntityDescription(SensorEntityDescription):
    """Description d'un capteur Hydro-Panne avec sa fonction de valeur."""

    value_fn: Callable[[HydroPanneData], datetime | int | str | None]


SENSORS: tuple[HydroPanneSensorEntityDescription, ...] = (
    HydroPanneSensorEntityDescription(
        key="estimated_restoration",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.estimated_restoration,
    ),
    HydroPanneSensorEntityDescription(
        key="outage_start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.outage_start,
    ),
    HydroPanneSensorEntityDescription(
        key="affected_customers",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="clients",
        icon="mdi:account-group",
        value_fn=lambda data: data.affected_customers,
    ),
    HydroPanneSensorEntityDescription(
        key="nearby_outages",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-alert",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: len(data.nearby),
    ),
    HydroPanneSensorEntityDescription(
        key="cause",
        icon="mdi:help-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.cause,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HydroPanneConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure les capteurs."""
    coordinator = entry.runtime_data
    async_add_entities(
        HydroPanneSensor(coordinator, description) for description in SENSORS
    )


class HydroPanneSensor(HydroPanneEntity, SensorEntity):
    """Capteur générique piloté par une :class:`HydroPanneSensorEntityDescription`."""

    entity_description: HydroPanneSensorEntityDescription

    def __init__(
        self, coordinator, description: HydroPanneSensorEntityDescription
    ) -> None:
        """Initialise le capteur."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> datetime | int | str | None:
        """Valeur courante calculée à partir des données du coordinateur."""
        return self.entity_description.value_fn(self.coordinator.data)
