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
3. Dodaj URL: `https://github.com/twoj-github/ha-ztm-gdansk`
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
3. Zmień parametry
4. Integracja automatycznie się przeładuje

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
departures:
  - route: "158"
    headsign: "Wrzeszcz PKP"
    minutes: 3
    delay: 1.5
    is_realtime: true
    estimated_time: "2024-01-15T14:35:00Z"
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
    departures_count: 5
    departures:
      - route: "158"
        headsign: "Wrzeszcz PKP"
        minutes: 3
        delay: 1.5
        realtime: true
        time: "15:35"
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
  ### 📍 {{ stop.stop_name | default('Przystanek ' ~ stop.stop_id) }}
  {% if stop.departures and stop.departures | length > 0 %}
  {% for dep in stop.departures %}
  {{ '🟢' if dep.realtime else '⚪' }} **{{ dep.route }}** {{ dep.headsign[:20] }} | **{{ dep.time }}** ({{ dep.minutes }} min){% if dep.delay and dep.delay > 1 %} 🔴+{{ dep.delay | int }}{% endif %}

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

**Problemy?** Otwórz [issue na GitHub](https://github.com/twoj-github/ha-ztm-gdansk/issues)
