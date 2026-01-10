"""Sensor platform for ZTM Gdańsk."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DELAY,
    ATTR_DEPARTURES,
    ATTR_HEADSIGN,
    ATTR_IS_REALTIME,
    ATTR_NEXT_DEPARTURE,
    ATTR_PLATFORM,
    ATTR_ROUTE,
    ATTR_STOP_ID,
    ATTR_STOP_NAME,
    ATTR_ZONE,
    DOMAIN,
)
from .coordinator import ZTMCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up ZTM Gdańsk sensors from YAML."""
    if DOMAIN not in hass.data:
        return

    coordinator = hass.data[DOMAIN].get("coordinator")
    stop_ids = hass.data[DOMAIN].get("stop_ids", [])

    if not coordinator or not stop_ids:
        _LOGGER.error("Coordinator or stop_ids not found")
        return

    entities = []
    
    for stop_id in stop_ids:
        entities.append(ZTMStopSensor(coordinator, stop_id))
        entities.append(ZTMNextDepartureSensor(coordinator, stop_id))

    # Add panel sensor (aggregate)
    entities.append(ZTMPanelSensor(coordinator, stop_ids))

    async_add_entities(entities)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ZTM Gdańsk sensors from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    stop_ids = data["stop_ids"]

    entities = []
    
    for stop_id in stop_ids:
        entities.append(ZTMStopSensor(coordinator, stop_id))
        entities.append(ZTMNextDepartureSensor(coordinator, stop_id))

    entities.append(ZTMPanelSensor(coordinator, stop_ids))

    async_add_entities(entities)


class ZTMStopSensor(CoordinatorEntity[ZTMCoordinator], SensorEntity):
    """Sensor representing a ZTM stop with departures."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZTMCoordinator, stop_id: int) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._stop_id = stop_id
        self._attr_unique_id = f"ztm_stop_{stop_id}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.coordinator.get_stop_name(self._stop_id)

    @property
    def native_value(self) -> int:
        """Return the number of upcoming departures."""
        return len(self.coordinator.get_departures(self._stop_id))

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "odjazdów"

    @property
    def icon(self) -> str:
        """Return the icon."""
        stop_info = self.coordinator.get_stop_info(self._stop_id)
        stop_type = stop_info.get("type", "BUS")
        return "mdi:tram" if stop_type == "TRAM" else "mdi:bus"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        departures = self.coordinator.get_departures(self._stop_id)
        stop_info = self.coordinator.get_stop_info(self._stop_id)
        
        # Format departures for attributes
        formatted_departures = []
        max_deps = self.coordinator.max_departures
        for dep in departures[:max_deps]:
            est_time = dep.get("estimatedTime", "")
            try:
                est_dt = datetime.fromisoformat(est_time.replace("Z", "+00:00"))
                minutes = int((est_dt - datetime.now(est_dt.tzinfo)).total_seconds() / 60)
            except (ValueError, TypeError):
                minutes = -1

            formatted_departures.append({
                "route": dep.get("routeShortName", "?"),
                "headsign": dep.get("headsign", "?"),
                "minutes": minutes,
                "delay": round(dep.get("delayInSeconds", 0) / 60, 1),
                "is_realtime": dep.get("status") == "REALTIME",
                "estimated_time": est_time,
                "theoretical_time": dep.get("theoreticalTime", ""),
            })

        return {
            ATTR_STOP_ID: self._stop_id,
            ATTR_STOP_NAME: stop_info.get("name", f"Przystanek {self._stop_id}"),
            ATTR_PLATFORM: stop_info.get("platform", ""),
            ATTR_ZONE: stop_info.get("zone", ""),
            ATTR_DEPARTURES: formatted_departures,
            "departures_raw": departures,
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._stop_id))},
            name=self.coordinator.get_stop_name(self._stop_id),
            manufacturer="ZTM Gdańsk",
            model="Przystanek",
        )


class ZTMNextDepartureSensor(CoordinatorEntity[ZTMCoordinator], SensorEntity):
    """Sensor showing next departure from a stop."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "min"

    def __init__(self, coordinator: ZTMCoordinator, stop_id: int) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._stop_id = stop_id
        self._attr_unique_id = f"ztm_next_{stop_id}"

    @property
    def name(self) -> str:
        """Return the name."""
        stop_name = self.coordinator.get_stop_name(self._stop_id)
        return f"{stop_name} - następny"

    @property
    def native_value(self) -> int | None:
        """Return minutes to next departure."""
        departures = self.coordinator.get_departures(self._stop_id)
        if not departures:
            return None

        try:
            est_time = departures[0].get("estimatedTime", "")
            est_dt = datetime.fromisoformat(est_time.replace("Z", "+00:00"))
            minutes = int((est_dt - datetime.now(est_dt.tzinfo)).total_seconds() / 60)
            return max(0, minutes)
        except (ValueError, TypeError, IndexError):
            return None

    @property
    def icon(self) -> str:
        """Return icon."""
        return "mdi:clock-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        departures = self.coordinator.get_departures(self._stop_id)
        if not departures:
            return {}

        dep = departures[0]
        delay_seconds = dep.get("delayInSeconds", 0)
        
        return {
            ATTR_ROUTE: dep.get("routeShortName", "?"),
            ATTR_HEADSIGN: dep.get("headsign", "?"),
            ATTR_DELAY: round(delay_seconds / 60, 1),
            ATTR_IS_REALTIME: dep.get("status") == "REALTIME",
            "estimated_time": dep.get("estimatedTime", ""),
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._stop_id))},
        )


class ZTMPanelSensor(CoordinatorEntity[ZTMCoordinator], SensorEntity):
    """Aggregate sensor for all stops."""

    _attr_has_entity_name = True
    _attr_name = "ZTM Panel"
    _attr_unique_id = "ztm_panel"
    _attr_icon = "mdi:bus-clock"

    def __init__(self, coordinator: ZTMCoordinator, stop_ids: list[int]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._stop_ids = stop_ids

    @property
    def native_value(self) -> str:
        """Return last update time."""
        if self.coordinator.data:
            return self.coordinator.data.get("last_update", "")[:19]
        return "Brak danych"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all stops data for Lovelace."""
        stops_data = []
        total_departures = 0

        for stop_id in self._stop_ids:
            departures = self.coordinator.get_departures(stop_id)
            stop_name = self.coordinator.get_stop_name(stop_id)
            total_departures += len(departures)

            # Format departures
            formatted = []
            max_deps = self.coordinator.max_departures
            for dep in departures[:max_deps]:
                try:
                    est_time = dep.get("estimatedTime", "")
                    est_dt = datetime.fromisoformat(est_time.replace("Z", "+00:00"))
                    minutes = int((est_dt - datetime.now(est_dt.tzinfo)).total_seconds() / 60)
                except (ValueError, TypeError):
                    minutes = -1

                formatted.append({
                    "route": dep.get("routeShortName", "?"),
                    "headsign": dep.get("headsign", "?"),
                    "minutes": minutes,
                    "delay": round(dep.get("delayInSeconds", 0) / 60, 1),
                    "realtime": dep.get("status") == "REALTIME",
                })

            stops_data.append({
                "stop_id": stop_id,
                "stop_name": stop_name,
                "departures_count": len(departures),
                "departures": formatted,
            })

        return {
            "stops": stops_data,
            "total_stops": len(self._stop_ids),
            "total_departures": total_departures,
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, "panel")},
            name="ZTM Gdańsk Panel",
            manufacturer="ZTM Gdańsk",
            model="Panel odjazdów",
        )
