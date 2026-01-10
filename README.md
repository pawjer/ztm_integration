# 🚌 ZTM Gdańsk - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Custom integration dla Home Assistant wyświetlająca odjazdy z przystanków ZTM Gdańsk w czasie rzeczywistym.

## ✨ Funkcje

- 🚌 Odjazdy w czasie rzeczywistym (GPS)
- 📍 Automatyczne pobieranie nazw przystanków
- 💾 Lazy loading - nazwy cachowane lokalnie
- ⏱️ Konfigurowalne interwały odświeżania
- 📊 Panel zbiorczy wszystkich przystanków
- 🔧 Usługi do odświeżania danych

## 📦 Instalacja

### HACS (zalecane)

1. Otwórz HACS
2. Kliknij `...` → `Custom repositories`
3. Dodaj URL: `https://github.com/twoj-github/ha-ztm-gdansk`
4. Kategoria: `Integration`
5. Zainstaluj "ZTM Gdańsk"
6. Zrestartuj Home Assistant

### Ręcznie

1. Skopiuj folder `custom_components/ztm_gdansk` do `/config/custom_components/`
2. Zrestartuj Home Assistant

## ⚙️ Konfiguracja

Dodaj do `configuration.yaml`:

```yaml
ztm_gdansk:
  stops:
    - 14562
    - 14563
    - 2161
    - 2162
    - 9989
    - 1645
    - 1644
  scan_interval: 30  # opcjonalne, domyślnie 30 sekund
```

### Jak znaleźć ID przystanku?

1. Wejdź na https://mapa.ztm.gda.pl
2. Kliknij na przystanek
3. ID jest widoczne w adresie URL lub szczegółach

## 📊 Encje

Dla każdego przystanku tworzone są:

| Encja | Opis |
|-------|------|
| `sensor.ztm_stop_XXXXX` | Liczba nadchodzących odjazdów |
| `sensor.ztm_next_XXXXX` | Minuty do następnego odjazdu |
| `sensor.ztm_panel` | Agregat wszystkich przystanków |

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
  - route: "258"
    headsign: "Stogi"
    minutes: 8
    delay: 0
    is_realtime: true
```

## 🎨 Przykładowa karta Lovelace

```yaml
type: markdown
content: >
  {% set panel = state_attr('sensor.ztm_panel', 'stops') %}
  {% for stop in panel %}
  ### 📍 {{ stop.stop_name }}
  {% for dep in stop.departures %}
  {{ '🟢' if dep.realtime else '⚪' }} **{{ dep.route }}** {{ dep.headsign[:20] }} | {{ dep.minutes }} min
  {% endfor %}

  {% endfor %}
```

## 🔧 Usługi

### `ztm_gdansk.refresh_stop_names`
Wyczyść cache i pobierz ponownie nazwy przystanków.

```yaml
service: ztm_gdansk.refresh_stop_names
```

### `ztm_gdansk.force_update`
Wymuś natychmiastowe pobranie danych.

```yaml
service: ztm_gdansk.force_update
```

## 🏗️ Architektura

```
                    ┌─────────────────────┐
                    │   configuration.yaml │
                    │   stops: [14562...]  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   ZTMCoordinator    │
                    │  (DataUpdateCoord)  │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
┌─────────▼─────────┐ ┌────────▼────────┐ ┌────────▼────────┐
│  departures API   │ │   stops API     │ │   Local Cache   │
│ (co 30 sekund)    │ │ (lazy loading)  │ │ (nazwy w pamięci)│
└───────────────────┘ └─────────────────┘ └─────────────────┘
```

## 📝 Changelog

### 1.0.0
- Pierwsza wersja
- Sensory przystanków i odjazdów
- Lazy loading nazw przystanków
- Usługi refresh i force_update

## 📜 Licencja

MIT

Dane ZTM Gdańsk: [Creative Commons Attribution](https://ckan.multimediagdansk.pl)
