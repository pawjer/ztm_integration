"""Config flow for ZTM Gdańsk integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import (
    API_DEPARTURES,
    API_STOPS,
    API_STOPS_GDANSK,
    CONF_MAX_DEPARTURES,
    CONF_SCAN_INTERVAL,
    CONF_STOPS,
    DEFAULT_MAX_DEPARTURES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def validate_stops(hass: HomeAssistant, stop_ids: list[int]) -> dict[str, str]:
    """Validate stop IDs by checking against stops database."""
    errors = {}
    valid_stops = []

    # Fetch stops database to validate stop IDs
    stops_db = {}
    async with aiohttp.ClientSession() as session:
        # Try Gdańsk-only stops first (smaller, faster)
        for url in [API_STOPS_GDANSK, API_STOPS]:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        # Find latest date key
                        date_keys = [k for k in data.keys() if k not in ("lastUpdate", "stops")]
                        if date_keys:
                            latest_date = sorted(date_keys, reverse=True)[0]
                            stops_list = data.get(latest_date, [])
                            stops_db = {int(stop.get("stopId", 0)): stop for stop in stops_list if stop.get("stopId")}
                            _LOGGER.debug("Loaded %d stops from database for validation", len(stops_db))
                            break
            except Exception as err:
                _LOGGER.debug("Could not load stops from %s: %s", url.split('/')[-1], err)
                continue

    # If we couldn't load stops database, fall back to API check
    if not stops_db:
        _LOGGER.info("Could not load stops database, validating via departures API")
        async with aiohttp.ClientSession() as session:
            for stop_id in stop_ids:
                try:
                    url = f"{API_DEPARTURES}?stopId={stop_id}"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            data = await resp.json(content_type=None)
                            if "departures" in data:
                                valid_stops.append(stop_id)
                        else:
                            _LOGGER.warning("Stop %s returned status %s", stop_id, resp.status)
                except Exception as err:
                    _LOGGER.error("Error validating stop %s: %s", stop_id, err)
    else:
        # Validate against stops database
        for stop_id in stop_ids:
            if stop_id in stops_db:
                valid_stops.append(stop_id)
                _LOGGER.debug("Stop %s validated: %s", stop_id, stops_db[stop_id].get("stopName", "Unknown"))
            else:
                _LOGGER.warning("Stop %s not found in stops database", stop_id)

    if not valid_stops:
        errors["base"] = "no_valid_stops"
    elif len(valid_stops) < len(stop_ids):
        _LOGGER.warning(
            "Some stops were invalid. Valid: %s, Invalid: %s",
            valid_stops,
            set(stop_ids) - set(valid_stops)
        )

    return errors, valid_stops


def parse_stops_input(stops_input: str) -> list[int]:
    """Parse stops input string to list of integers."""
    stops = []
    # Support comma, space, newline separated
    for part in stops_input.replace(",", " ").replace("\n", " ").split():
        part = part.strip()
        if part.isdigit():
            stops.append(int(part))
    return stops


class ZTMGdanskConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ZTM Gdańsk."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Parse stops input
            stops_str = user_input.get(CONF_STOPS, "")
            stop_ids = parse_stops_input(stops_str)
            
            if not stop_ids:
                errors[CONF_STOPS] = "no_stops"
            else:
                # Validate stops
                validation_errors, valid_stops = await validate_stops(self.hass, stop_ids)
                
                if validation_errors:
                    errors.update(validation_errors)
                elif valid_stops:
                    # Create entry with valid stops
                    return self.async_create_entry(
                        title=f"ZTM Gdańsk ({len(valid_stops)} przystanków)",
                        data={
                            CONF_STOPS: valid_stops,
                            CONF_SCAN_INTERVAL: user_input.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                            ),
                            CONF_MAX_DEPARTURES: user_input.get(
                                CONF_MAX_DEPARTURES, DEFAULT_MAX_DEPARTURES
                            ),
                        },
                    )

        # Show form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STOPS): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                    vol.Optional(
                        CONF_MAX_DEPARTURES, default=DEFAULT_MAX_DEPARTURES
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=20)),
                }
            ),
            errors=errors,
            description_placeholders={
                "example_stops": "14562, 14563, 2161",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ZTMGdanskOptionsFlow:
        """Get the options flow for this handler."""
        return ZTMGdanskOptionsFlow(config_entry)


class ZTMGdanskOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for ZTM Gdańsk."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Parse stops
            stops_str = user_input.get(CONF_STOPS, "")
            stop_ids = parse_stops_input(stops_str)
            
            if not stop_ids:
                errors[CONF_STOPS] = "no_stops"
            else:
                # Validate new stops
                validation_errors, valid_stops = await validate_stops(self.hass, stop_ids)
                
                if validation_errors:
                    errors.update(validation_errors)
                elif valid_stops:
                    # Update entry
                    return self.async_create_entry(
                        title="",
                        data={
                            CONF_STOPS: valid_stops,
                            CONF_SCAN_INTERVAL: user_input.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                            ),
                            CONF_MAX_DEPARTURES: user_input.get(
                                CONF_MAX_DEPARTURES, DEFAULT_MAX_DEPARTURES
                            ),
                        },
                    )

        # Current values
        current_stops = self.config_entry.options.get(
            CONF_STOPS, self.config_entry.data.get(CONF_STOPS, [])
        )
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        current_max = self.config_entry.options.get(
            CONF_MAX_DEPARTURES,
            self.config_entry.data.get(CONF_MAX_DEPARTURES, DEFAULT_MAX_DEPARTURES),
        )

        # Format stops for display
        stops_display = ", ".join(str(s) for s in current_stops)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STOPS, default=stops_display): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=current_interval
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                    vol.Optional(
                        CONF_MAX_DEPARTURES, default=current_max
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=20)),
                }
            ),
            errors=errors,
        )
