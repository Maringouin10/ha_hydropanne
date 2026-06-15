"""Flux de configuration (UI) pour Hydro-Panne."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HydroPanneApiClient, HydroPanneApiError
from .const import (
    DEFAULT_NAME,
    DEFAULT_RADIUS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_RADIUS,
    MAX_SCAN_INTERVAL,
    MIN_RADIUS,
    MIN_SCAN_INTERVAL,
)

_RADIUS_SELECTOR = vol.All(vol.Coerce(int), vol.Range(min=MIN_RADIUS, max=MAX_RADIUS))
_SCAN_SELECTOR = vol.All(
    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
)


class HydroPanneConfigFlow(ConfigFlow, domain=DOMAIN):
    """Gère le flux de configuration de Hydro-Panne."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Première étape : emplacement du domicile et rayon de recherche."""
        errors: dict[str, str] = {}

        if user_input is not None:
            latitude = user_input[CONF_LATITUDE]
            longitude = user_input[CONF_LONGITUDE]
            await self.async_set_unique_id(
                f"{round(latitude, 4)}_{round(longitude, 4)}"
            )
            self._abort_if_unique_id_configured()

            client = HydroPanneApiClient(async_get_clientsession(self.hass))
            try:
                await client.async_get_outages(
                    latitude, longitude, user_input[CONF_RADIUS]
                )
            except HydroPanneApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data={
                        CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME),
                        CONF_LATITUDE: latitude,
                        CONF_LONGITUDE: longitude,
                        CONF_RADIUS: user_input[CONF_RADIUS],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(
                    CONF_LATITUDE, default=self.hass.config.latitude
                ): cv.latitude,
                vol.Required(
                    CONF_LONGITUDE, default=self.hass.config.longitude
                ): cv.longitude,
                vol.Required(CONF_RADIUS, default=DEFAULT_RADIUS): _RADIUS_SELECTOR,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> HydroPanneOptionsFlow:
        """Retourne le flux d'options."""
        return HydroPanneOptionsFlow(config_entry)


class HydroPanneOptionsFlow(OptionsFlow):
    """Gère les options (rayon et fréquence de mise à jour)."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Mémorise l'entrée de configuration."""
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Étape unique des options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self._entry.options
        data = self._entry.data
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_RADIUS,
                    default=options.get(
                        CONF_RADIUS, data.get(CONF_RADIUS, DEFAULT_RADIUS)
                    ),
                ): _RADIUS_SELECTOR,
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): _SCAN_SELECTOR,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
