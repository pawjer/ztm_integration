# 🚌 ZTM Gdańsk - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2023.1+-blue.svg)](https://www.home-assistant.io/)

Custom integration dla Home Assistant wyświetlająca odjazdy z przystanków ZTM Gdańsk w czasie rzeczywistym.

## ✨ Funkcje

- 🚌 **Odjazdy w czasie rzeczywistym** - dane GPS z pojazdów
- 🖥️ **Konfiguracja przez UI** - bez edycji YAML
- 📍 **Automatyczne nazwy przystanków** - pobierane z API ZTM
- ⚙️ **Konfigurowalne parametry** - interwał odświeżania, liczba odjazdów
- 💾 **Lazy loading** - nazwy cachowane w pamięci
- 📊 **Panel zbiorczy** - wszystkie przystanki w jednym sensorze
- 🔧 **Usługi** - ręczne odświeżanie danych

## 📦 Instalacja

### HACS (zalecane)

1. Otwórz HACS → **Integracje**
2. Kliknij `⋮` → **Repozytoria niestandardowe**
3. Dodaj URL: `https://github.com/pawjer/ztm_integration`
4. Kategoria: **Integracja**
5. Zainstaluj **ZTM Gdańsk**
6. Zrestartuj Home Assistant

### Ręcznie

1. Pobierz i rozpakuj archiwum
2. Skopiuj folder `custom_components/ztm_gdansk/` do `/config/custom_components/`
3. Zrestartuj Home Assistant

## ⚙️ Konfiguracja

### Przez interfejs (zalecane)

1. **Ustawienia** → **Urządzenia i usługi** → **Dodaj integrację**
2. Szukaj: **ZTM Gdańsk**
3. Wypełnij formularz:

| Pole | Opis | Wartości |
|------|------|----------|
| **Numery przystanków** | ID przystanków (przecinki/spacje) | np. `14562, 14563, 2161` |
| **Interwał odświeżania** | Częstotliwość pobierania danych | 10-300 sekund (domyślnie: 30) |
| **Maksymalna liczba odjazdów** | Ile odjazdów na przystanek | 1-20 (domyślnie: 5) |

### Przez YAML (opcjonalnie)

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

### Zmiana ustawień

1. **Ustawienia** → **Urządzenia i usługi** → **ZTM Gdańsk**
2. Kliknij **Konfiguruj**
3. Wybierz opcję:
   - **General** - numery przystanków, interwał odświeżania, liczba odjazdów
   - **Icons** - dostosuj ikony właściwości pojazdów (♿ 🚴 🔽 ❄️ 🔌 ⬇️)
   - **Departure Format** - dostosuj format wyświetlania odjazdów
4. Integracja automatycznie się przeładuje

### Personalizacja ikon

Możesz dostosować ikony wyświetlane dla właściwości pojazdów:

1. **Ustawienia** → **Urządzenia i usługi** → **ZTM Gdańsk** → **Konfiguruj**
2. Wybierz **Icons**
3. Zmień dowolną ikonę (można użyć emoji, symboli lub tekstu):
   - **Wheelchair** (♿) - dostępność dla wózków
   - **Bike** (🚴) - wieszaki na rowery
   - **Low Floor** (🔽) - pojazd niskopodłogowy
   - **Air Conditioning** (❄️) - klimatyzacja
   - **USB** (🔌) - porty USB
   - **Kneeling** (⬇️) - mechanizm przyklęku
4. Ikony pojawią się w polu `vehicle_properties_icons` każdego odjazdu

### Personalizacja formatu odjazdów

Możesz dostosować format wyświetlania informacji o odjazdach:

1. **Ustawienia** → **Urządzenia i usługi** → **ZTM Gdańsk** → **Konfiguruj**
2. Wybierz **Departure Format**
3. Wprowadź własny szablon używając placeholderów:

**Dostępne placeholders:**
- `{route}` - numer linii (np. "158")
- `{headsign}` - kierunek (np. "Wrzeszcz PKP")
- `{time}` - czas odjazdu w formacie HH:MM (np. "14:35")
- `{scheduled_time}` - czas rozkładowy HH:MM (np. "14:33")
- `{minutes}` - minuty do odjazdu (np. 3)
- `{delay}` - opóźnienie w minutach (np. 1.5)
- `{vehicle_code}` - numer pojazdu (np. 3013)
- `{vehicle_properties_icons}` - ikony właściwości pojazdu (np. "♿ 🚴 ❄️")
- `{realtime}` - czy dane są w czasie rzeczywistym (True/False)

**Przykładowe szablony:**
- Domyślny: `{route} → {headsign} | {time} ({minutes} min)`
- Kompaktowy: `{route} {headsign} {time}`
- Pełny: `🚌 {route} to {headsign} in {minutes} min {vehicle_properties_icons}`
- Z numerem pojazdu: `{route} ({vehicle_code}) → {headsign} | {time}`

4. Sformatowany tekst pojawi się w polu `departure_string` każdego odjazdu

## 🔍 Jak znaleźć ID przystanku?

1. Wejdź na [mapa.ztm.gda.pl](https://mapa.ztm.gda.pl)
2. Kliknij na przystanek
3. ID jest widoczne w adresie URL lub w szczegółach przystanku

## 📊 Encje

Dla każdego przystanku tworzone są automatycznie:

| Encja | Typ | Opis |
|-------|-----|------|
| `sensor.ztm_stop_XXXXX` | Sensor | Liczba nadchodzących odjazdów |
| `sensor.ztm_next_XXXXX` | Sensor | Minuty do następnego odjazdu |
| `sensor.ztm_panel` | Sensor | Agregat wszystkich przystanków |

### Atrybuty sensora przystanku

```yaml
stop_id: 14562
stop_name: "Polsat Plus Arena Gdańsk 01"
platform: "01"
zone: "Gdańsk"
wheelchair_accessible: true  # ♿ Dostępny dla wózków
on_demand: false             # 📞 Na żądanie (wymaga wcześniejszego zgłoszenia)
zone_border: false           # 🎫 Granica strefy biletowej
departures:
  - route: "158"
    headsign: "Wrzeszcz PKP"
    minutes: 3
    delay: 1.5
    is_realtime: true
    time: "14:35"             # Czas odjazdu (czas lokalny)
    scheduled_time: "14:33"   # Czas rozkładowy (czas lokalny)
    estimated_time: "2024-01-15T14:35:00Z"
    theoretical_time: "2024-01-15T14:33:00Z"  # Czas rozkładowy
    vehicle_code: 3013        # Numer pojazdu
    vehicle_wheelchair_accessible: true  # ♿ Pojazd dostępny dla wózków (rampa)
    vehicle_bike_capacity: 1  # 🚴 Liczba miejsc na rowery (0 = brak)
    vehicle_low_floor: true   # Pojazd niskopodłogowy
    vehicle_air_conditioning: true  # Klimatyzacja
    vehicle_usb: true         # Porty USB
    vehicle_kneeling_mechanism: true  # Mechanizm przyklęku
    vehicle_properties_icons: "♿ 🚴 🔽 ❄️ 🔌 ⬇️"  # Ikony właściwości pojazdu
    departure_string: "158 → Wrzeszcz PKP | 14:35 (3 min)"  # Sformatowany tekst odjazdu
    last_update: "2024-01-15T14:32:49Z"  # Ostatnia aktualizacja GPS
  - route: "258"
    headsign: "Stogi Plaża"
    minutes: 8
    delay: 0
    is_realtime: true
```

### Atrybuty sensora panelu

```yaml
stops:
  - stop_id: 14562
    stop_name: "Polsat Plus Arena Gdańsk 01"
    stop_type: "BUS"  # BUS lub TRAM
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
        time: "15:35"              # Czas odjazdu (czas lokalny)
        scheduled_time: "15:33"    # Czas rozkładowy (czas lokalny)
        vehicle_code: 3013         # Numer pojazdu
        vehicle_wheelchair_accessible: true  # ♿ Pojazd z rampą
        vehicle_bike_capacity: 1   # 🚴 Liczba miejsc na rowery
        vehicle_low_floor: true    # Pojazd niskopodłogowy
        vehicle_air_conditioning: true  # Klimatyzacja
        vehicle_usb: true          # Porty USB
        vehicle_kneeling_mechanism: true  # Mechanizm przyklęku
        vehicle_properties_icons: "♿ 🚴 🔽 ❄️ 🔌 ⬇️"  # Ikony właściwości pojazdu
        departure_string: "158 → Wrzeszcz PKP | 15:35 (3 min)"  # Sformatowany tekst odjazdu
        last_update: "2024-01-15T14:32:49Z"
total_stops: 4
total_departures: 20
```

## 🎨 Przykładowe karty Lovelace

### Karta Markdown (kompaktowa)

```yaml
type: markdown
title: 🚌 ZTM Gdańsk
content: >
  {% set stops = state_attr('sensor.ztm_panel', 'stops') %}
  {% if stops is none or stops is not iterable %}
  *Ładowanie danych...*
  {% else %}
  {% for stop in stops %}
  ### {{ '🚊' if stop.stop_type == 'TRAM' else '🚌' }} {{ stop.stop_name | default('Przystanek ' ~ stop.stop_id) }}{{ ' ♿' if stop.wheelchair_accessible }}{{ ' 📞' if stop.on_demand }}
  {% if stop.departures and stop.departures | length > 0 %}
  {% for dep in stop.departures %}
  {{ '🟢' if dep.realtime else '⚪' }} **{{ dep.route }}**{% if dep.vehicle_code %} ({{dep.vehicle_code}}){% endif %}{% if dep.vehicle_wheelchair_accessible %} ♿{% endif %}{% if dep.vehicle_bike_capacity > 0 %} 🚴{% endif %} {{ dep.headsign[:20] }} | **{{ dep.time }}** ({{ dep.minutes }} min){% if dep.delay and dep.delay > 1 %} 🔴+{{ dep.delay | int }}{% endif %}

  {% endfor %}
  {% else %}
  *Brak odjazdów*
  {% endif %}

  {% endfor %}
  {% endif %}
```

### Karta Entities

```yaml
type: entities
title: 🚌 Przystanki ZTM
entities:
  - entity: sensor.ztm_stop_14562
  - entity: sensor.ztm_stop_14563
  - entity: sensor.ztm_stop_2161
  - type: divider
  - entity: sensor.ztm_panel
    name: Ostatnia aktualizacja
```

### Karta z przyciskami

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
        name: Odśwież nazwy
        icon: mdi:refresh
        tap_action:
          action: call-service
          service: ztm_gdansk.refresh_stop_names
      - type: button
        name: Aktualizuj
        icon: mdi:update
        tap_action:
          action: call-service
          service: ztm_gdansk.force_update
```

## 🔧 Usługi

| Usługa | Opis |
|--------|------|
| `ztm_gdansk.refresh_stop_names` | Wyczyść cache i pobierz ponownie nazwy przystanków |
| `ztm_gdansk.force_update` | Wymuś natychmiastowe pobranie danych o odjazdach |

### Przykład automatyzacji

```yaml
automation:
  - alias: "Odśwież ZTM co 6 godzin"
    trigger:
      - platform: time_pattern
        hours: "/6"
    action:
      - service: ztm_gdansk.refresh_stop_names
```

## 🐛 Debugowanie

Jeśli nazwy przystanków nie są pobierane, włącz debug logging:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.ztm_gdansk: debug
```

Sprawdź logi: **Ustawienia → System → Logi** → szukaj "ztm_gdansk"

## 🏗️ Architektura

```
┌─────────────────────────────────┐
│     Home Assistant UI           │
│   (Config Flow / Options)       │
└───────────────┬─────────────────┘
                │
┌───────────────▼─────────────────┐
│       ZTMCoordinator            │
│    (DataUpdateCoordinator)      │
│   - Pobiera odjazdy co X sek    │
│   - Cache nazw przystanków      │
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

## 📡 API ZTM Gdańsk

Integracja korzysta z oficjalnego API [Otwarte dane ZTM w Gdańsku](https://ckan.multimediagdansk.pl/dataset/tristar):

- **Odjazdy**: `https://ckan2.multimediagdansk.pl/departures?stopId={id}`
- **Przystanki Gdańsk**: `stopsingdansk.json`
- **Wszystkie przystanki**: `stops.json`

Dane udostępniane na licencji [Creative Commons Attribution](https://ckan.multimediagdansk.pl).

## 📝 Changelog

### 1.6.0 (2026-01-11)
- ✅ **Konfigurowalny format odjazdów** - możliwość personalizacji wyświetlania odjazdów przez UI
- 📝 **Nowe pole `departure_string`** - sformatowany tekst odjazdu według szablonu użytkownika
- 🎨 **9 dostępnych placeholderów**:
  - {route}, {headsign}, {time}, {scheduled_time}
  - {minutes}, {delay}, {vehicle_code}
  - {vehicle_properties_icons}, {realtime}
- 🔧 **Szablon konfigurowalny przez UI** - w menu Departure Format
- 💡 **Przykładowe szablony** - w dokumentacji z różnymi stylami formatowania
- ⚡ **Automatyczne formatowanie** - template zastosowany do wszystkich odjazdów
- 🛡️ **Bezpieczne formatowanie** - fallback przy błędach w szablonie

### 1.5.0 (2026-01-11)
- ✅ **Konfigurowalne ikony** - możliwość personalizacji ikon właściwości pojazdów przez UI
- 🎨 **Nowy przepływ opcji** - menu z dwiema opcjami: General i Icons
- ⚙️ **6 konfigurowalnych ikon**:
  - Wheelchair (♿) - dostępność dla wózków
  - Bike (🚴) - wieszaki na rowery
  - Low Floor (🔽) - pojazd niskopodłogowy
  - Air Conditioning (❄️) - klimatyzacja
  - USB (🔌) - porty USB
  - Kneeling (⬇️) - mechanizm przyklęku
- 🔧 **Obsługa niestandardowych ikon** - możliwość użycia emoji, symboli lub tekstu
- 💾 **Automatyczne przeładowanie** - zmiany ikon widoczne natychmiast po zapisaniu

### 1.4.0 (2026-01-11)
- ✅ **Nowe pole `vehicle_properties_icons`** - string z ikonami właściwości pojazdu (♿ 🚴 🔽 ❄️ 🔌 ⬇️)
- 🏗️ **Refaktoryzacja kodu** - utworzono wspólny model formatowania odjazdów i właściwości pojazdów
- 📦 **Nowe metody w koordinatorze**:
  - `format_departure()` - wspólna metoda formatowania odjazdów dla wszystkich sensorów
  - `format_vehicle_properties()` - wspólna metoda właściwości pojazdów
  - `get_vehicle_icons()` - generowanie stringu z ikonami
- 🎨 **Stałe dla ikon** - ikony przeniesione do const.py (ICON_WHEELCHAIR, ICON_BIKE, etc.)
- 🔧 **Zmniejszenie duplikacji kodu** - usunięto ~150 linii zduplikowanego kodu z sensorów

### 1.3.3 (2026-01-11)
- ✅ **Dodano pola czasu w formacie HH:MM** do sensor.ztm_stop_* i sensor.ztm_next_*:
  - `time` - czas odjazdu w formacie lokalnym HH:MM
  - `scheduled_time` - czas rozkładowy w formacie lokalnym HH:MM
- 📊 **Spójność danych** - wszystkie sensory mają teraz te same pola czasowe

### 1.3.2 (2026-01-11)
- ✅ **Nowe pola właściwości pojazdów**:
  - `vehicle_low_floor` - pojazd niskopodłogowy
  - `vehicle_air_conditioning` - klimatyzacja w pojeździe
  - `vehicle_usb` - dostępność portów USB
  - `vehicle_kneeling_mechanism` - mechanizm przyklęku pojazdu
- 📊 **Wszystkie sensory** - nowe pola dostępne w sensor.ztm_stop_*, sensor.ztm_next_*, i sensor.ztm_panel

### 1.3.1 (2026-01-11)
- ✅ **Nowe pole**: `vehicle_bike_capacity` - 🚴 liczba miejsc na rowery w pojeździe (0-2)
- 🎨 **Ulepszona karta Lovelace** - pokazuje ikonę 🚴 dla pojazdów z wieszakami na rowery

### 1.3.0 (2026-01-11)
- ✅ **Nowe pola w odjazdach**:
  - `vehicle_code` - numer pojazdu dla śledzenia konkretnego autobusu/tramwaju
  - `vehicle_wheelchair_accessible` - ♿ **czy pojazd ma rampę dla wózków** (dane z bazy pojazdów ZTM)
  - `scheduled_time` - czas rozkładowy w formacie HH:MM (sensor panelu)
  - `theoretical_time` - czas rozkładowy ISO (sensor przystanku, dla automatyzacji)
  - `last_update` - timestamp ostatniej aktualizacji GPS
- ✅ **Nowe pola w przystankach**:
  - `wheelchair_accessible` - ♿ dostępność infrastruktury przystanku dla wózków
  - `on_demand` - 📞 przystanek na żądanie (wymaga wcześniejszego zgłoszenia)
  - `zone_border` - 🎫 granica strefy biletowej
- 🚀 **Baza pojazdów** - integracja z oficjalną bazą pojazdów ZTM (475 pojazdów)
- 🎨 **Ulepszona karta Lovelace** - pokazuje numery pojazdów i oznaczenia ♿ dla dostępnych pojazdów
- 📊 **Spójność danych** - wszystkie sensory mają te same pola

### 1.2.1 (2026-01-11)
- ✅ **Nowe pole "stop_type"** w sensorze panelu - rozróżnienie BUS/TRAM dla każdego przystanku
- ⚡ **Optymalizacja wydajności** - zmniejszono liczbę wywołań do cache z 2 do 1 na przystanek
- 🎨 **Ulepszona karta Lovelace** - dynamiczne ikony 🚌/🚊 w zależności od typu przystanku

### 1.2.0 (2026-01-11)
- ✅ **Nowe pole "time"** w sensorze panelu - czas odjazdu w formacie HH:MM (czas lokalny)
- ✅ **Poprawiona walidacja przystanków** - teraz sprawdza bazę danych przystanków zamiast bieżących odjazdów
- ✅ **Naprawiono błędy API** - dodano obsługę nieprawidłowych nagłówków Content-Type
- ✅ **Naprawiono błąd NoneType** - obsługa null w polu delayInSeconds
- ✅ **Naprawiono opcje flow** - usunięto błąd 500 przy edycji konfiguracji
- ✅ **Dodano oficjalne ikony ZTM** - logo dla HACS
- 🎨 **Ulepszone karty Lovelace** - pokazują czas odjazdu, opóźnienia i stan ładowania

### 1.1.0
- Konfiguracja przez UI (config_flow)
- Opcje: interwał odświeżania, max odjazdów
- Dwa endpointy API dla nazw przystanków
- Lepsze logowanie błędów

### 1.0.0
- Pierwsza wersja
- Sensory przystanków i odjazdów
- Lazy loading nazw przystanków
- Usługi refresh i force_update

## 📜 Licencja

MIT

---

**Problemy?** Otwórz [issue na GitHub](https://github.com/pawjer/ztm_integration/issues)
