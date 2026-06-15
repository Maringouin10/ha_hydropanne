"""L'intégration Hydro-Panne — assistant de panne électrique pour Hydro-Québec."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import HydroPanneCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

type HydroPanneConfigEntry = ConfigEntry[HydroPanneCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: HydroPanneConfigEntry
) -> bool:
    """Configure Hydro-Panne à partir d'une entrée de configuration."""
    coordinator = HydroPanneCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: HydroPanneConfigEntry
) -> bool:
    """Décharge une entrée de configuration."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(
    hass: HomeAssistant, entry: HydroPanneConfigEntry
) -> None:
    """Recharge l'intégration lorsque les options changent."""
    await hass.config_entries.async_reload(entry.entry_id)
