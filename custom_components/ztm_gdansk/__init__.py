"""ZTM Gdańsk integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_ICON_AIR_CONDITIONING,
    CONF_ICON_BIKE,
    CONF_ICON_KNEELING,
    CONF_ICON_LOW_FLOOR,
    CONF_ICON_USB,
    CONF_ICON_WHEELCHAIR,
    CONF_MAX_DEPARTURES,
    CONF_SCAN_INTERVAL,
    CONF_STOPS,
    DEFAULT_MAX_DEPARTURES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import ZTMCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

# Schema for YAML configuration (still supported)
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_STOPS): vol.All(
                    cv.ensure_list, [cv.positive_int]
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.positive_int,
                vol.Optional(
                    CONF_MAX_DEPARTURES, default=DEFAULT_MAX_DEPARTURES
                ): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up ZTM Gdańsk from YAML configuration."""
    hass.data.setdefault(DOMAIN, {})
    
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    stop_ids = conf[CONF_STOPS]
    scan_interval = conf.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    max_departures = conf.get(CONF_MAX_DEPARTURES, DEFAULT_MAX_DEPARTURES)

    _LOGGER.info(
        "Setting up ZTM Gdańsk (YAML) with %d stops, interval: %ds, max: %d",
        len(stop_ids),
        scan_interval,
        max_departures,
    )

    # Create coordinator
    coordinator = ZTMCoordinator(hass, stop_ids, scan_interval, max_departures)
    
    # Store coordinator
    hass.data[DOMAIN]["coordinator"] = coordinator
    hass.data[DOMAIN]["stop_ids"] = stop_ids
    hass.data[DOMAIN]["max_departures"] = max_departures

    # Initial data fetch
    await coordinator.async_config_entry_first_refresh()

    # Register services
    await _async_setup_services(hass)

    # Setup platforms
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform(
            Platform.SENSOR, DOMAIN, {}, config
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ZTM Gdańsk from a config entry (UI)."""
    hass.data.setdefault(DOMAIN, {})

    # Get config from entry data or options (options take precedence)
    stop_ids = entry.options.get(CONF_STOPS, entry.data.get(CONF_STOPS, []))
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    max_departures = entry.options.get(
        CONF_MAX_DEPARTURES,
        entry.data.get(CONF_MAX_DEPARTURES, DEFAULT_MAX_DEPARTURES)
    )

    # Get custom icons from options (if configured)
    custom_icons = None
    if any(key in entry.options for key in [
        CONF_ICON_WHEELCHAIR, CONF_ICON_BIKE, CONF_ICON_LOW_FLOOR,
        CONF_ICON_AIR_CONDITIONING, CONF_ICON_USB, CONF_ICON_KNEELING
    ]):
        custom_icons = {
            "wheelchair": entry.options.get(CONF_ICON_WHEELCHAIR),
            "bike": entry.options.get(CONF_ICON_BIKE),
            "low_floor": entry.options.get(CONF_ICON_LOW_FLOOR),
            "air_conditioning": entry.options.get(CONF_ICON_AIR_CONDITIONING),
            "usb": entry.options.get(CONF_ICON_USB),
            "kneeling": entry.options.get(CONF_ICON_KNEELING),
        }

    _LOGGER.info(
        "Setting up ZTM Gdańsk (UI) with %d stops, interval: %ds, max: %d",
        len(stop_ids),
        scan_interval,
        max_departures,
    )

    # Create coordinator
    coordinator = ZTMCoordinator(hass, stop_ids, scan_interval, max_departures, custom_icons)
    await coordinator.async_config_entry_first_refresh()

    # Store data
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "stop_ids": stop_ids,
        "max_departures": max_departures,
    }

    # Register services (once)
    if not hass.services.has_service(DOMAIN, "refresh_stop_names"):
        await _async_setup_services(hass)

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    _LOGGER.info("Reloading ZTM Gdańsk due to options change")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def _async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for ZTM Gdańsk."""

    async def refresh_stop_names(call: ServiceCall) -> None:
        """Refresh stop names cache."""
        _LOGGER.info("Refreshing stop names cache")
        
        # Find all coordinators
        for key, value in hass.data[DOMAIN].items():
            if isinstance(value, dict) and "coordinator" in value:
                coordinator = value["coordinator"]
                await coordinator.async_refresh_stop_names()
                await coordinator.async_request_refresh()
            elif key == "coordinator":
                await value.async_refresh_stop_names()
                await value.async_request_refresh()

    async def force_update(call: ServiceCall) -> None:
        """Force update of all data."""
        _LOGGER.info("Forcing data update")
        
        for key, value in hass.data[DOMAIN].items():
            if isinstance(value, dict) and "coordinator" in value:
                await value["coordinator"].async_request_refresh()
            elif key == "coordinator":
                await value.async_request_refresh()

    hass.services.async_register(
        DOMAIN, "refresh_stop_names", refresh_stop_names
    )
    hass.services.async_register(
        DOMAIN, "force_update", force_update
    )
