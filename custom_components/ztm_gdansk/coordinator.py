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
    API_STOPS_GDANSK,
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
            data = await response.json(content_type=None)
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

        _LOGGER.info("Fetching names for %d stops: %s", len(missing_stops), missing_stops)
        
        # Try Gdańsk-specific endpoint first, then fallback to full stops list
        endpoints = [
            (API_STOPS_GDANSK, "stopsingdansk.json"),
            (API_STOPS, "stops.json"),
        ]
        
        for url, name in endpoints:
            still_missing = [s for s in missing_stops if str(s) not in self._stop_names_cache]
            if not still_missing:
                break
                
            _LOGGER.debug("Trying endpoint %s for %d stops", name, len(still_missing))
            await self._fetch_stops_from_url(url, still_missing)
        
        # Add fallback for any still missing
        still_missing = [s for s in missing_stops if str(s) not in self._stop_names_cache]
        if still_missing:
            _LOGGER.warning("Stops not found in any API: %s", still_missing)
            self._add_fallback_names(still_missing)

    async def _fetch_stops_from_url(self, url: str, missing_stops: list[int]) -> int:
        """Fetch stop names from a specific URL. Returns count of found stops."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    _LOGGER.debug("API %s response status: %s", url.split('/')[-1], response.status)
                    response.raise_for_status()
                    data = await response.json(content_type=None)

            _LOGGER.debug("API response keys: %s", list(data.keys())[:5])

            # Find the latest date key (format: "YYYY-MM-DD" or similar)
            date_keys = [k for k in data.keys() if k not in ("lastUpdate", "stops")]
            if date_keys:
                dates = sorted(date_keys, reverse=True)
                stops_data = data[dates[0]].get("stops", [])
                _LOGGER.debug("Using date key: %s, found %d stops", dates[0], len(stops_data))
            elif "stops" in data:
                # Direct stops array
                stops_data = data["stops"]
                _LOGGER.debug("Using direct 'stops' key, found %d stops", len(stops_data))
            else:
                _LOGGER.warning("Unknown API structure. Keys: %s", list(data.keys()))
                return 0

            if not stops_data:
                _LOGGER.warning("Empty stops data from API")
                return 0

            # Log first stop structure for debugging
            if stops_data:
                _LOGGER.debug("Sample stop keys: %s", list(stops_data[0].keys()))
                _LOGGER.debug("Sample stop data: %s", {k: stops_data[0].get(k) for k in ['stopId', 'stopDesc', 'stopName', 'subName']})

            # Build lookup and cache missing stops
            found_count = 0
            missing_stops_set = set(missing_stops)
            
            for stop in stops_data:
                stop_id_raw = stop.get("stopId")
                if stop_id_raw is None:
                    continue
                    
                stop_id = int(stop_id_raw)
                
                if stop_id in missing_stops_set and str(stop_id) not in self._stop_names_cache:
                    # Try different name fields - stopDesc is from TRISTAR, stopName from schedule system
                    name = (
                        stop.get("stopDesc") or 
                        stop.get("stopName") or 
                        stop.get("stopShortName") or 
                        stop.get("name") or
                        ""
                    )
                    
                    if not name:
                        _LOGGER.debug("Stop %s has no name fields", stop_id)
                        continue
                    
                    sub_name = stop.get("subName", "") or stop.get("platform", "")
                    # subName is often the platform number like "01", "02"
                    if sub_name:
                        sub_name = str(sub_name).zfill(2) if str(sub_name).isdigit() else sub_name
                    
                    full_name = f"{name} {sub_name}".strip() if sub_name else name
                    
                    self._stop_names_cache[str(stop_id)] = {
                        "name": full_name,
                        "short_name": name,
                        "platform": sub_name,
                        "zone": stop.get("zoneName", "") or stop.get("zone", ""),
                        "lat": stop.get("stopLat"),
                        "lon": stop.get("stopLon"),
                        "type": "TRAM" if stop.get("type") == 2 else "BUS",
                    }
                    found_count += 1
                    _LOGGER.debug("Cached stop %s: %s", stop_id, full_name)

            _LOGGER.info(
                "Fetched %d/%d stop names from %s. Cache size: %d", 
                found_count, len(missing_stops), url.split('/')[-1], len(self._stop_names_cache)
            )
            return found_count

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error from %s: %s", url.split('/')[-1], err)
            return 0
        except Exception as err:
            _LOGGER.error("Error fetching from %s: %s", url.split('/')[-1], err, exc_info=True)
            return 0

    def _add_fallback_names(self, stop_ids: list[int]) -> None:
        """Add fallback names for stops that couldn't be fetched."""
        for stop_id in stop_ids:
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
