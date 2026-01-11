# 🚌 ZTM Gdańsk - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2023.1+-blue.svg)](https://www.home-assistant.io/)

Custom integration for Home Assistant displaying real-time departures from ZTM Gdańsk stops.

[🇵🇱 Polish version / Wersja polska](README.md)

## ✨ Features

- 🚌 **Real-time departures** - GPS data from vehicles
- 🖥️ **UI configuration** - no YAML editing required
- 📍 **Automatic stop names** - fetched from ZTM API
- ⚙️ **Configurable parameters** - scan interval, number of departures
- 💾 **Lazy loading** - names cached in memory
- 📊 **Summary panel** - all stops in one sensor
- 🔧 **Services** - manual data refresh

## 📦 Installation

### HACS (recommended)

1. Open HACS → **Integrations**
2. Click `⋮` → **Custom repositories**
3. Add URL: `https://github.com/pawjer/ztm_integration`
4. Category: **Integration**
5. Install **ZTM Gdańsk**
6. Restart Home Assistant

### Manual

1. Download and extract the archive
2. Copy folder `custom_components/ztm_gdansk/` to `/config/custom_components/`
3. Restart Home Assistant

## ⚙️ Configuration

### Through UI (recommended)

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search: **ZTM Gdańsk**
3. Fill in the form:

| Field | Description | Values |
|-------|-------------|--------|
| **Stop IDs** | Stop IDs (comma/space separated) | e.g. `14562, 14563, 2161` |
| **Scan interval** | Data fetching frequency | 10-300 seconds (default: 30) |
| **Maximum departures** | How many departures per stop | 1-20 (default: 5) |

### Through YAML (optional)

```yaml
# configuration.yaml
ztm_gdansk:
  stops:
    - 14562
    - 14563
    - 2161
    - 2162
  scan_interval: 30
  max_departures: 5
```

### Changing settings

1. **Settings** → **Devices & Services** → **ZTM Gdańsk**
2. Click **Configure**
3. Choose option:
   - **General** - stop IDs, scan interval, number of departures
   - **Icons** - customize vehicle property icons (♿ 🚴 🔽 ❄️ 🔌 ⬇️)
   - **Departure Format** - customize departure display format
4. Integration will reload automatically

### Icon customization

You can customize icons displayed for vehicle properties:

1. **Settings** → **Devices & Services** → **ZTM Gdańsk** → **Configure**
2. Choose **Icons**
3. Change any icon (you can use emoji, symbols or text):
   - **Wheelchair** (♿) - wheelchair accessibility
   - **Bike** (🚴) - bike racks
   - **Low Floor** (🔽) - low-floor vehicle
   - **Air Conditioning** (❄️) - air conditioning
   - **USB** (🔌) - USB charging
   - **Kneeling** (⬇️) - kneeling mechanism
4. Icons will appear in the `vehicle_properties_icons` field of each departure

### Departure format customization

You can customize the departure information display format:

1. **Settings** → **Devices & Services** → **ZTM Gdańsk** → **Configure**
2. Choose **Departure Format**
3. Enter your own template using placeholders:

**Available placeholders:**
- `{route}` - route number (e.g. "158")
- `{headsign}` - destination (e.g. "Wrzeszcz PKP")
- `{time}` - departure time in HH:MM format (e.g. "14:35")
- `{scheduled_time}` - scheduled time HH:MM (e.g. "14:33")
- `{minutes}` - minutes until departure (e.g. 3)
- `{delay}` - delay in minutes (e.g. 1.5)
- `{vehicle_code}` - vehicle number (e.g. 3013)
- `{vehicle_properties_icons}` - vehicle property icons (e.g. "♿ 🚴 ❄️")
- `{realtime}` - whether data is real-time (True/False)

**Example templates:**
- Default: `{route} → {headsign} | {time} ({minutes} min)`
- Compact: `{route} {headsign} {time}`
- Full: `🚌 {route} to {headsign} in {minutes} min {vehicle_properties_icons}`
- With vehicle number: `{route} ({vehicle_code}) → {headsign} | {time}`

4. The formatted text will appear in the `departure_string` field of each departure

## 🔍 How to find stop ID?

1. Go to [mapa.ztm.gda.pl](https://mapa.ztm.gda.pl)
2. Click on a stop
3. ID is visible in the URL or stop details

## 📊 Entities

For each stop, the following entities are automatically created:

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.ztm_stop_XXXXX` | Sensor | Number of upcoming departures |
| `sensor.ztm_next_XXXXX` | Sensor | Minutes to next departure |
| `sensor.ztm_panel` | Sensor | Aggregate of all stops |

### Stop sensor attributes

```yaml
stop_id: 14562
stop_name: "Polsat Plus Arena Gdańsk 01"
platform: "01"
zone: "Gdańsk"
wheelchair_accessible: true  # ♿ Wheelchair accessible
on_demand: false             # 📞 On demand (requires prior notification)
zone_border: false           # 🎫 Ticket zone border
departures:
  - route: "158"
    headsign: "Wrzeszcz PKP"
    minutes: 3
    delay: 1.5
    is_realtime: true
    time: "14:35"             # Departure time (local time)
    scheduled_time: "14:33"   # Scheduled time (local time)
    estimated_time: "2024-01-15T14:35:00Z"
    theoretical_time: "2024-01-15T14:33:00Z"  # Scheduled time
    vehicle_code: 3013        # Vehicle number
    vehicle_wheelchair_accessible: true  # ♿ Vehicle wheelchair accessible (ramp)
    vehicle_bike_capacity: 1  # 🚴 Number of bike spaces (0 = none)
    vehicle_low_floor: true   # Low-floor vehicle
    vehicle_air_conditioning: true  # Air conditioning
    vehicle_usb: true         # USB charging
    vehicle_kneeling_mechanism: true  # Kneeling mechanism
    vehicle_properties_icons: "♿ 🚴 🔽 ❄️ 🔌 ⬇️"  # Vehicle property icons
    departure_string: "158 → Wrzeszcz PKP | 14:35 (3 min)"  # Formatted departure text
    last_update: "2024-01-15T14:32:49Z"  # Last GPS update
  - route: "258"
    headsign: "Stogi Plaża"
    minutes: 8
    delay: 0
    is_realtime: true
```

### Panel sensor attributes

```yaml
icons_legend:
  - icon: ♿
    en: Wheelchair accessibility
    pl: Dostępność dla wózków
  - icon: 🚴
    en: Bike racks
    pl: Wieszaki na rowery
  - icon: 🔽
    en: Low-floor vehicle
    pl: Pojazd niskopodłogowy
  - icon: ❄️
    en: Air conditioning
    pl: Klimatyzacja
  - icon: 🔌
    en: USB charging
    pl: Porty USB
  - icon: ⬇️
    en: Kneeling mechanism
    pl: Mechanizm przyklęku
stops:
  - stop_id: 14562
    stop_name: "Polsat Plus Arena Gdańsk 01"
    stop_type: "BUS"  # BUS or TRAM
    wheelchair_accessible: true
    on_demand: false
    zone_border: false
    departures_count: 5
    departures:
      - route: "158"
        headsign: "Wrzeszcz PKP"
        minutes: 3
        delay: 1.5
        realtime: true
        time: "15:35"              # Departure time (local time)
        scheduled_time: "15:33"    # Scheduled time (local time)
        vehicle_code: 3013         # Vehicle number
        vehicle_wheelchair_accessible: true  # ♿ Vehicle with ramp
        vehicle_bike_capacity: 1   # 🚴 Number of bike spaces
        vehicle_low_floor: true    # Low-floor vehicle
        vehicle_air_conditioning: true  # Air conditioning
        vehicle_usb: true          # USB charging
        vehicle_kneeling_mechanism: true  # Kneeling mechanism
        vehicle_properties_icons: "♿ 🚴 🔽 ❄️ 🔌 ⬇️"  # Vehicle property icons
        departure_string: "158 → Wrzeszcz PKP | 15:35 (3 min)"  # Formatted departure text
        last_update: "2024-01-15T14:32:49Z"
total_stops: 4
total_departures: 20
```

## 🎨 Example Lovelace cards

### Markdown card (compact)

```yaml
type: markdown
title: 🚌 ZTM Gdańsk
content: >
  {% set stops = state_attr('sensor.ztm_panel', 'stops') %}
  {% if stops is none or stops is not iterable %}
  *Loading data...*
  {% else %}
  {% for stop in stops %}
  ### {{ '🚊' if stop.stop_type == 'TRAM' else '🚌' }} {{ stop.stop_name | default('Stop ' ~ stop.stop_id) }}{{ ' ♿' if stop.wheelchair_accessible }}{{ ' 📞' if stop.on_demand }}
  {% if stop.departures and stop.departures | length > 0 %}
  {% for dep in stop.departures %}
  {{ '🟢' if dep.realtime else '⚪' }} **{{ dep.route }}**{% if dep.vehicle_code %} ({{dep.vehicle_code}}){% endif %}{% if dep.vehicle_wheelchair_accessible %} ♿{% endif %}{% if dep.vehicle_bike_capacity > 0 %} 🚴{% endif %} {{ dep.headsign[:20] }} | **{{ dep.time }}** ({{ dep.minutes }} min){% if dep.delay and dep.delay > 1 %} 🔴+{{ dep.delay | int }}{% endif %}

  {% endfor %}
  {% else %}
  *No departures*
  {% endif %}

  {% endfor %}
  {% endif %}
```

### Entities card

```yaml
type: entities
title: 🚌 ZTM Stops
entities:
  - entity: sensor.ztm_stop_14562
  - entity: sensor.ztm_stop_14563
  - entity: sensor.ztm_stop_2161
  - type: divider
  - entity: sensor.ztm_panel
    name: Last update
```

### Card with buttons

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      ## 🚌 ZTM Gdańsk
      {% set stops = state_attr('sensor.ztm_panel', 'stops') | default([]) %}
      {% for stop in stops %}
      ### {{ stop.stop_name }}
      {% for dep in stop.departures %}
      {{ '🟢' if dep.realtime else '⚪' }} **{{ dep.route }}** → {{ dep.headsign }} | {{ dep.minutes }} min
      {% endfor %}
      {% endfor %}
  - type: horizontal-stack
    cards:
      - type: button
        name: Refresh names
        icon: mdi:refresh
        tap_action:
          action: call-service
          service: ztm_gdansk.refresh_stop_names
      - type: button
        name: Update
        icon: mdi:update
        tap_action:
          action: call-service
          service: ztm_gdansk.force_update
```

### Card with icons legend

```yaml
type: markdown
title: 🚌 ZTM Gdańsk
content: >
  {% set stops = state_attr('sensor.ztm_panel', 'stops') %}
  {% set legend = state_attr('sensor.ztm_panel', 'icons_legend') %}
  {% if stops is none or stops is not iterable %}
  *Loading data...*
  {% else %}
  {% for stop in stops %}
  ### {{ '🚊' if stop.stop_type == 'TRAM' else '🚌' }} {{ stop.stop_name }}
  {% if stop.departures and stop.departures | length > 0 %}
  {% for dep in stop.departures %}
  {{ '🟢' if dep.realtime else '⚪' }} **{{ dep.route }}** → {{ dep.headsign }} | **{{ dep.time }}** ({{ dep.minutes }} min) {{ dep.vehicle_properties_icons }}
  {% endfor %}
  {% else %}
  *No departures*
  {% endif %}

  {% endfor %}

  ---
  **Legend:**
  {% for item in legend %}
  {{ item.icon }} - {{ item.en }}
  {% endfor %}
  {% endif %}
```

## 🔧 Services

| Service | Description |
|---------|-------------|
| `ztm_gdansk.refresh_stop_names` | Clear cache and fetch stop names again |
| `ztm_gdansk.refresh_vehicles` | Clear cache and fetch vehicle database again |
| `ztm_gdansk.force_update` | Force immediate fetch of departure data |

### Automation example

```yaml
automation:
  - alias: "Refresh ZTM every 6 hours"
    trigger:
      - platform: time_pattern
        hours: "/6"
    action:
      - service: ztm_gdansk.refresh_stop_names
```

## 🐛 Debugging

If stop names are not being fetched, enable debug logging:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.ztm_gdansk: debug
```

Check logs: **Settings → System → Logs** → search for "ztm_gdansk"

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│     Home Assistant UI           │
│   (Config Flow / Options)       │
└───────────────┬─────────────────┘
                │
┌───────────────▼─────────────────┐
│       ZTMCoordinator            │
│    (DataUpdateCoordinator)      │
│   - Fetches departures every X  │
│   - Caches stop names           │
└───────────────┬─────────────────┘
                │
    ┌───────────┴───────────┐
    │                       │
┌───▼───┐             ┌─────▼─────┐
│ Stops │             │ Departures│
│  API  │             │    API    │
└───────┘             └───────────┘
stopsingdansk.json    /departures
stops.json            ?stopId=XXX
```

## 📡 ZTM Gdańsk API

The integration uses the official API [Open data ZTM in Gdańsk](https://ckan.multimediagdansk.pl/dataset/tristar):

- **Departures**: `https://ckan2.multimediagdansk.pl/departures?stopId={id}`
- **Gdańsk stops**: `stopsingdansk.json`
- **All stops**: `stops.json`

Data provided under [Creative Commons Attribution](https://ckan.multimediagdansk.pl) license.

## 📝 Changelog

### 1.6.4 (2026-01-11)
- 🔄 **API retry logic** - automatic retry on failures (3 attempts with exponential backoff)
- 💾 **Last departures cache** - displays last valid data when API is down
- 🛡️ **Prevent data clearing** - panel never gets cleared on transient API errors
- 📊 **Per-stop cache** - each stop has its own cache, one failure doesn't affect others

### 1.6.3 (2026-01-11)
- ✅ **New field `icons_legend`** in panel sensor - legend for vehicle property icons
- 📖 **Bilingual legend** - each icon with description in Polish and English
- 🎨 **Legend card example** - new Lovelace example displaying the legend

### 1.6.2 (2026-01-11)
- 🐛 **Fixed vehicle database loading** - vehicle properties now display correctly
- ✅ **New service `refresh_vehicles`** - allows forcing vehicle database reload
- 🔧 **Improved cache handling** - vehicle database not marked as loaded if error occurs
- 🌐 **Updated API URL** - added version parameter to avoid redirects

### 1.6.1 (2026-01-11)
- 🌐 **UI translations** - added Polish and English interface translations
- 📝 **Localization** - all configuration and options steps translated
- 🇵🇱 **Polish by default** - interface automatically in system language

### 1.6.0 (2026-01-11)
- ✅ **Configurable departure format** - ability to personalize departure display through UI
- 📝 **New field `departure_string`** - formatted departure text according to user template
- 🎨 **9 available placeholders**:
  - {route}, {headsign}, {time}, {scheduled_time}
  - {minutes}, {delay}, {vehicle_code}
  - {vehicle_properties_icons}, {realtime}
- 🔧 **Template configurable through UI** - in Departure Format menu
- 💡 **Example templates** - in documentation with various formatting styles
- ⚡ **Automatic formatting** - template applied to all departures
- 🛡️ **Safe formatting** - fallback on template errors

### 1.5.0 (2026-01-11)
- ✅ **Configurable icons** - ability to personalize vehicle property icons through UI
- 🎨 **New options flow** - menu with two options: General and Icons
- ⚙️ **6 configurable icons**:
  - Wheelchair (♿) - wheelchair accessibility
  - Bike (🚴) - bike racks
  - Low Floor (🔽) - low-floor vehicle
  - Air Conditioning (❄️) - air conditioning
  - USB (🔌) - USB charging
  - Kneeling (⬇️) - kneeling mechanism
- 🔧 **Custom icon support** - ability to use emoji, symbols or text
- 💾 **Automatic reload** - icon changes visible immediately after saving

### 1.4.0 (2026-01-11)
- ✅ **New field `vehicle_properties_icons`** - string with vehicle property icons (♿ 🚴 🔽 ❄️ 🔌 ⬇️)
- 🏗️ **Code refactoring** - created common model for formatting departures and vehicle properties
- 📦 **New coordinator methods**:
  - `format_departure()` - common departure formatting method for all sensors
  - `format_vehicle_properties()` - common vehicle properties method
  - `get_vehicle_icons()` - icon string generation
- 🎨 **Icon constants** - icons moved to const.py (ICON_WHEELCHAIR, ICON_BIKE, etc.)
- 🔧 **Reduced code duplication** - removed ~150 lines of duplicated code from sensors

### 1.3.3 (2026-01-11)
- ✅ **Added HH:MM time format fields** to sensor.ztm_stop_* and sensor.ztm_next_*:
  - `time` - departure time in local HH:MM format
  - `scheduled_time` - scheduled time in local HH:MM format
- 📊 **Data consistency** - all sensors now have the same time fields

### 1.3.2 (2026-01-11)
- ✅ **New vehicle property fields**:
  - `vehicle_low_floor` - low-floor vehicle
  - `vehicle_air_conditioning` - vehicle air conditioning
  - `vehicle_usb` - USB charging availability
  - `vehicle_kneeling_mechanism` - vehicle kneeling mechanism
- 📊 **All sensors** - new fields available in sensor.ztm_stop_*, sensor.ztm_next_*, and sensor.ztm_panel

### 1.3.1 (2026-01-11)
- ✅ **New field**: `vehicle_bike_capacity` - 🚴 number of bike spaces in vehicle (0-2)
- 🎨 **Improved Lovelace card** - shows 🚴 icon for vehicles with bike racks

### 1.3.0 (2026-01-11)
- ✅ **New departure fields**:
  - `vehicle_code` - vehicle number for tracking specific bus/tram
  - `vehicle_wheelchair_accessible` - ♿ **whether vehicle has wheelchair ramp** (data from ZTM vehicle database)
  - `scheduled_time` - scheduled time in HH:MM format (panel sensor)
  - `theoretical_time` - scheduled time ISO (stop sensor, for automation)
  - `last_update` - GPS last update timestamp
- ✅ **New stop fields**:
  - `wheelchair_accessible` - ♿ stop infrastructure wheelchair accessibility
  - `on_demand` - 📞 on-demand stop (requires prior notification)
  - `zone_border` - 🎫 ticket zone border
- 🚀 **Vehicle database** - integration with official ZTM vehicle database (475 vehicles)
- 🎨 **Improved Lovelace card** - shows vehicle numbers and ♿ markings for accessible vehicles
- 📊 **Data consistency** - all sensors have the same fields

### 1.2.1 (2026-01-11)
- ✅ **New "stop_type" field** in panel sensor - BUS/TRAM distinction for each stop
- ⚡ **Performance optimization** - reduced number of cache calls from 2 to 1 per stop
- 🎨 **Improved Lovelace card** - dynamic 🚌/🚊 icons depending on stop type

### 1.2.0 (2026-01-11)
- ✅ **New "time" field** in panel sensor - departure time in HH:MM format (local time)
- ✅ **Improved stop validation** - now checks stop database instead of current departures
- ✅ **Fixed API errors** - added handling for incorrect Content-Type headers
- ✅ **Fixed NoneType error** - handling null in delayInSeconds field
- ✅ **Fixed options flow** - removed 500 error when editing configuration
- ✅ **Added official ZTM icons** - logo for HACS
- 🎨 **Improved Lovelace cards** - show departure time, delays and loading state

### 1.1.0
- UI configuration (config_flow)
- Options: scan interval, max departures
- Two API endpoints for stop names
- Better error logging

### 1.0.0
- First version
- Stop and departure sensors
- Lazy loading of stop names
- Refresh and force_update services

## 📜 License

MIT

---

**Issues?** Open an [issue on GitHub](https://github.com/pawjer/ztm_integration/issues)
