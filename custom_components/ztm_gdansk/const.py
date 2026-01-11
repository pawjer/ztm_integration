"""Constants for ZTM Gdańsk integration."""
from datetime import timedelta

DOMAIN = "ztm_gdansk"

# API endpoints
API_DEPARTURES = "https://ckan2.multimediagdansk.pl/departures"
API_STOPS = "https://ckan.multimediagdansk.pl/dataset/c24aa637-3619-4dc2-a171-a23eec8f2172/resource/4c4025f0-01bf-41f7-a39f-d156d201b82b/download/stops.json"
API_STOPS_GDANSK = "https://ckan.multimediagdansk.pl/dataset/c24aa637-3619-4dc2-a171-a23eec8f2172/resource/d3e96eb6-25ad-4d6c-8651-b1eb39155945/download/stopsingdansk.json"
API_VEHICLES = "https://files.cloudgdansk.pl/d/otwarte-dane/ztm/baza-pojazdow.json"

# Update intervals
SCAN_INTERVAL_DEPARTURES = timedelta(seconds=30)
SCAN_INTERVAL_STOPS = timedelta(hours=24)

# Config keys
CONF_STOPS = "stops"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MAX_DEPARTURES = "max_departures"
CONF_ICON_WHEELCHAIR = "icon_wheelchair"
CONF_ICON_BIKE = "icon_bike"
CONF_ICON_LOW_FLOOR = "icon_low_floor"
CONF_ICON_AIR_CONDITIONING = "icon_air_conditioning"
CONF_ICON_USB = "icon_usb"
CONF_ICON_KNEELING = "icon_kneeling"
CONF_DEPARTURE_FORMAT = "departure_format"

# Defaults
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_MAX_DEPARTURES = 5
DEFAULT_DEPARTURE_FORMAT = "{route} → {headsign} | {time} ({minutes} min)"

# Attributes
ATTR_STOP_NAME = "stop_name"
ATTR_STOP_ID = "stop_id"
ATTR_DEPARTURES = "departures"
ATTR_NEXT_DEPARTURE = "next_departure"
ATTR_DELAY = "delay"
ATTR_IS_REALTIME = "is_realtime"
ATTR_HEADSIGN = "headsign"
ATTR_ROUTE = "route"
ATTR_PLATFORM = "platform"
ATTR_ZONE = "zone"

# Vehicle property icons
ICON_WHEELCHAIR = "♿"
ICON_BIKE = "🚴"
ICON_LOW_FLOOR = "🔽"
ICON_AIR_CONDITIONING = "❄️"
ICON_USB = "🔌"
ICON_KNEELING = "⬇️"
