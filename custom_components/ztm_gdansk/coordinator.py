"""DataUpdateCoordinator for ZTM Gdańsk."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    API_DEPARTURES,
    API_STOPS,
    API_STOPS_GDANSK,
    API_VEHICLES,
    DOMAIN,
    ICON_AIR_CONDITIONING,
    ICON_BIKE,
    ICON_KNEELING,
    ICON_LOW_FLOOR,
    ICON_USB,
    ICON_WHEELCHAIR,
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
        custom_icons: dict[str, str] | None = None,
        departure_format: str | None = None,
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
        self._vehicles_cache: dict[str, dict[str, Any]] = {}
        self._vehicles_loaded = False

        # Store custom icons or use defaults
        self._icons = {
            "wheelchair": (custom_icons or {}).get("wheelchair", ICON_WHEELCHAIR),
            "bike": (custom_icons or {}).get("bike", ICON_BIKE),
            "low_floor": (custom_icons or {}).get("low_floor", ICON_LOW_FLOOR),
            "air_conditioning": (custom_icons or {}).get("air_conditioning", ICON_AIR_CONDITIONING),
            "usb": (custom_icons or {}).get("usb", ICON_USB),
            "kneeling": (custom_icons or {}).get("kneeling", ICON_KNEELING),
        }

        # Store departure format template (import needed for default)
        from .const import DEFAULT_DEPARTURE_FORMAT
        self._departure_format = departure_format or DEFAULT_DEPARTURE_FORMAT

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Lazy load stop names on first run
            if not self._stop_names_loaded:
                await self._load_stop_names()
                self._stop_names_loaded = True

            # Lazy load vehicles database on first run
            if not self._vehicles_loaded:
                success = await self._load_vehicles()
                if success:
                    self._vehicles_loaded = True

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
                        "type": stop.get("type", "BUS"),  # API returns "BUS" or "TRAM" as string
                        "wheelchair_accessible": bool(stop.get("wheelchairBoarding", 0)),
                        "on_demand": bool(stop.get("onDemand", 0)),
                        "zone_border": bool(stop.get("ticketZoneBorder", 0)),
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
                    "type": "BUS",
                    "wheelchair_accessible": False,
                    "on_demand": False,
                    "zone_border": False,
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

    async def async_refresh_vehicles(self) -> None:
        """Force refresh of vehicles cache."""
        self._vehicles_loaded = False
        self._vehicles_cache.clear()
        success = await self._load_vehicles()
        if success:
            self._vehicles_loaded = True

    async def _load_vehicles(self) -> bool:
        """Load vehicle database from API. Returns True on success."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    API_VEHICLES, timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response.raise_for_status()
                    data = await response.json(content_type=None)

            vehicles = data.get("results", [])
            for vehicle in vehicles:
                vehicle_code = str(vehicle.get("vehicleCode", ""))
                if vehicle_code:
                    self._vehicles_cache[vehicle_code] = {
                        "wheelchair_accessible": vehicle.get("wheelchairsRamp", False),
                        "low_floor": "niskopodłogowy" in vehicle.get("floorHeight", "").lower(),
                        "air_conditioning": vehicle.get("airConditioning", False),
                        "usb": vehicle.get("usb", False),
                        "bike_holders": vehicle.get("bikeHolders", 0),
                        "kneeling_mechanism": vehicle.get("kneelingMechanism", False),
                        "brand": vehicle.get("brand", ""),
                        "model": vehicle.get("model", ""),
                    }

            _LOGGER.info("Loaded %d vehicles into cache", len(self._vehicles_cache))
            return True

        except Exception as err:
            _LOGGER.warning("Could not load vehicles database: %s", err)
            return False

    def get_vehicle_info(self, vehicle_code: int | str | None) -> dict[str, Any]:
        """Get cached vehicle info."""
        if vehicle_code is None:
            return {}
        return self._vehicles_cache.get(str(vehicle_code), {})

    def get_vehicle_icons(self, vehicle_info: dict[str, Any]) -> str:
        """Generate icon string for vehicle properties."""
        icons = []

        if vehicle_info.get("wheelchair_accessible"):
            icons.append(self._icons["wheelchair"])
        if vehicle_info.get("bike_holders", 0) > 0:
            icons.append(self._icons["bike"])
        if vehicle_info.get("low_floor"):
            icons.append(self._icons["low_floor"])
        if vehicle_info.get("air_conditioning"):
            icons.append(self._icons["air_conditioning"])
        if vehicle_info.get("usb"):
            icons.append(self._icons["usb"])
        if vehicle_info.get("kneeling_mechanism"):
            icons.append(self._icons["kneeling"])

        return " ".join(icons)

    def format_vehicle_properties(self, vehicle_code: int | str | None) -> dict[str, Any]:
        """Get formatted vehicle properties with all fields."""
        vehicle_info = self.get_vehicle_info(vehicle_code)

        return {
            "vehicle_code": vehicle_code,
            "vehicle_wheelchair_accessible": vehicle_info.get("wheelchair_accessible", False),
            "vehicle_bike_capacity": vehicle_info.get("bike_holders", 0),
            "vehicle_low_floor": vehicle_info.get("low_floor", False),
            "vehicle_air_conditioning": vehicle_info.get("air_conditioning", False),
            "vehicle_usb": vehicle_info.get("usb", False),
            "vehicle_kneeling_mechanism": vehicle_info.get("kneeling_mechanism", False),
            "vehicle_properties_icons": self.get_vehicle_icons(vehicle_info),
        }

    def format_departure(self, dep: dict[str, Any], include_is_realtime: bool = True) -> dict[str, Any]:
        """Format a departure with all fields (time conversion, vehicle properties)."""
        # Calculate minutes until departure
        est_time = dep.get("estimatedTime", "")
        try:
            est_dt = datetime.fromisoformat(est_time.replace("Z", "+00:00"))
            minutes = int((est_dt - datetime.now(est_dt.tzinfo)).total_seconds() / 60)
            # Convert UTC to local time
            local_dt = dt_util.as_local(est_dt)
            time_str = local_dt.strftime("%H:%M")
        except (ValueError, TypeError):
            minutes = -1
            time_str = "?"

        # Parse scheduled time
        scheduled_time_str = None
        try:
            theo_time = dep.get("theoreticalTime", "")
            if theo_time:
                theo_dt = datetime.fromisoformat(theo_time.replace("Z", "+00:00"))
                theo_local = dt_util.as_local(theo_dt)
                scheduled_time_str = theo_local.strftime("%H:%M")
        except (ValueError, TypeError):
            pass

        # Get vehicle properties
        vehicle_code = dep.get("vehicleCode")
        vehicle_props = self.format_vehicle_properties(vehicle_code)

        # Build departure dict
        result = {
            "route": dep.get("routeShortName", "?"),
            "headsign": dep.get("headsign", "?"),
            "minutes": minutes,
            "delay": round((dep.get("delayInSeconds") or 0) / 60, 1),
            "time": time_str,
            "scheduled_time": scheduled_time_str,
            "estimated_time": est_time,
            "theoretical_time": dep.get("theoreticalTime", ""),
            **vehicle_props,
            "last_update": dep.get("timestamp"),
        }

        # Add is_realtime or realtime depending on sensor type
        if include_is_realtime:
            result["is_realtime"] = dep.get("status") == "REALTIME"
        else:
            result["realtime"] = dep.get("status") == "REALTIME"

        # Add formatted departure string
        result["departure_string"] = self.format_departure_string(result)

        return result

    def format_departure_string(self, departure_data: dict[str, Any]) -> str:
        """Format departure data into a custom string using template."""
        try:
            # Prepare data for formatting
            format_data = {
                "route": departure_data.get("route", "?"),
                "headsign": departure_data.get("headsign", "?"),
                "time": departure_data.get("time", "?"),
                "scheduled_time": departure_data.get("scheduled_time") or "?",
                "minutes": departure_data.get("minutes", 0),
                "delay": departure_data.get("delay", 0),
                "vehicle_code": departure_data.get("vehicle_code") or "",
                "vehicle_properties_icons": departure_data.get("vehicle_properties_icons", ""),
                "realtime": departure_data.get("realtime", departure_data.get("is_realtime", False)),
            }

            # Format using template
            return self._departure_format.format(**format_data)
        except (KeyError, ValueError) as err:
            _LOGGER.warning("Error formatting departure string: %s", err)
            # Fallback to simple format
            return f"{format_data['route']} → {format_data['headsign']} | {format_data['time']}"
