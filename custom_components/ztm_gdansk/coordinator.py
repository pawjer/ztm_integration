"""DataUpdateCoordinator for ZTM Gdańsk."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_DEPARTURES,
    API_STOPS,
    DOMAIN,
    SCAN_INTERVAL_DEPARTURES,
)

_LOGGER = logging.getLogger(__name__)


class ZTMCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for fetching ZTM departure data."""

    def __init__(
        self,
        hass: HomeAssistant,
        stop_ids: list[int],
        scan_interval: int = 30,
        max_departures: int = 5,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.stop_ids = stop_ids
        self.max_departures = max_departures
        self._stop_names_cache: dict[str, dict[str, Any]] = {}
        self._stop_names_loaded = False

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Lazy load stop names on first run
            if not self._stop_names_loaded:
                await self._load_stop_names()
                self._stop_names_loaded = True

            # Fetch departures for all stops
            departures = await self._fetch_all_departures()
            
            return {
                "departures": departures,
                "stop_names": self._stop_names_cache,
                "last_update": datetime.now().isoformat(),
            }

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    async def _fetch_all_departures(self) -> dict[str, list[dict]]:
        """Fetch departures for all configured stops."""
        departures = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_stop_departures(session, stop_id)
                for stop_id in self.stop_ids
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for stop_id, result in zip(self.stop_ids, results):
                if isinstance(result, Exception):
                    _LOGGER.warning("Failed to fetch departures for stop %s: %s", stop_id, result)
                    departures[str(stop_id)] = []
                else:
                    departures[str(stop_id)] = result

        return departures

    async def _fetch_stop_departures(
        self, session: aiohttp.ClientSession, stop_id: int
    ) -> list[dict]:
        """Fetch departures for a single stop."""
        url = f"{API_DEPARTURES}?stopId={stop_id}"
        
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("departures", [])

    async def _load_stop_names(self) -> None:
        """Load stop names from API (lazy loading with cache)."""
        # Check which stops are missing from cache
        missing_stops = [
            stop_id for stop_id in self.stop_ids
            if str(stop_id) not in self._stop_names_cache
        ]
        
        if not missing_stops:
            _LOGGER.debug("All stop names already cached")
            return

        _LOGGER.info("Fetching names for %d stops", len(missing_stops))
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    API_STOPS, timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            # Find the latest date key
            dates = sorted(data.keys(), reverse=True)
            if not dates:
                _LOGGER.warning("No data in stops API response")
                return

            stops_data = data[dates[0]].get("stops", [])
            
            # Build lookup and cache missing stops
            for stop in stops_data:
                stop_id = str(stop.get("stopId", ""))
                if stop_id and int(stop_id) in missing_stops:
                    name = stop.get("stopDesc", "")
                    sub_name = stop.get("subName", "")
                    
                    self._stop_names_cache[stop_id] = {
                        "name": f"{name} {sub_name}".strip() if sub_name else name,
                        "short_name": name,
                        "platform": sub_name,
                        "zone": stop.get("zoneName", ""),
                        "lat": stop.get("stopLat"),
                        "lon": stop.get("stopLon"),
                        "type": stop.get("type", "BUS"),
                    }

            _LOGGER.info("Cached names for %d stops", len(self._stop_names_cache))

        except Exception as err:
            _LOGGER.error("Failed to load stop names: %s", err)
            # Add fallback names for missing stops
            for stop_id in missing_stops:
                if str(stop_id) not in self._stop_names_cache:
                    self._stop_names_cache[str(stop_id)] = {
                        "name": f"Przystanek {stop_id}",
                        "short_name": f"Przystanek {stop_id}",
                        "platform": "",
                        "zone": "",
                        "is_fallback": True,
                    }

    def get_stop_name(self, stop_id: int | str) -> str:
        """Get cached stop name."""
        stop_data = self._stop_names_cache.get(str(stop_id), {})
        return stop_data.get("name", f"Przystanek {stop_id}")

    def get_stop_info(self, stop_id: int | str) -> dict[str, Any]:
        """Get cached stop info."""
        return self._stop_names_cache.get(str(stop_id), {})

    def get_departures(self, stop_id: int | str) -> list[dict]:
        """Get departures for a stop."""
        if self.data is None:
            return []
        return self.data.get("departures", {}).get(str(stop_id), [])

    async def async_refresh_stop_names(self) -> None:
        """Force refresh of stop names cache."""
        self._stop_names_loaded = False
        self._stop_names_cache.clear()
        await self._load_stop_names()
        self._stop_names_loaded = True
