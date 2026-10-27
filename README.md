# Multi-Zone Chrono-Thermostat - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/evlas/Cronotermostato?color=blue&style=flat-square)](https://github.com/evlas/Cronotermostato/releases)
[![Hassfest](https://github.com/evlas/Cronotermostato/actions/workflows/hassfest.yml/badge.svg)](https://github.com/evlas/Cronotermostato/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/evlas/Cronotermostato/actions/workflows/hacs.yml/badge.svg)](https://github.com/evlas/Cronotermostato/actions/workflows/hacs.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)

🌐 *English | [Versione in italiano](README.it.md)*

**Multi-Zone Chrono-Thermostat** (*Cronotermostato Multizona*) is a **Home Assistant** custom integration designed as an advanced evolution of the original YAML package for managing time-slot schedules and presets across heating and cooling HVAC systems.

It completely eliminates the need to maintain dozens of repetitive YAML automations and helper entities, offering a clean, native UI configuration with full support for **multiple independent thermal zones**.

---

## 📋 Evolution from the YAML Package

| Feature | Legacy YAML Package (`cronotermostato.yaml`) | New Multi-Zone Integration |
|---|---|---|
| **Zone Management** | Hardcoded (only Ground Floor `pt` & Basement `psi`) | **Dynamic & unlimited**: configure zones via UI (*Config Flow*) |
| **Climate Entities** | Hardcoded (`climate.salotto`, `group.climapt`, etc.) | **Selectable from dropdown** for each zone |
| **Automations Overhead** | **40 individual automations** (2,180 lines) | **0 automations**: internal lightweight Python scheduling engine |
| **Startup Alignment** | Missing (waited for next scheduled trigger) | **Automatic**: computes and applies active slot on HA startup |
| **Time Pickers** | Generic `input_datetime` helpers | Native Home Assistant **`time`** platform |
| **Mode Selectors** | Generic `input_select` helpers | Native Home Assistant **`select`** platform with standard presets |
| **Diagnostics & State** | None | **Dedicated sensors**: *Active Slot*, *Next Slot*, *Zone Status* |
| **Multi-Language** | Fixed Italian strings only | **Full localization (EN and IT)** via `translation_key` |

---

## ⚙️ Operating Logic

For each configured thermal zone (e.g. *Ground Floor*, *Night Zone*, *Basement*):
1. **Guided Setup**:
   - Assign main climate entities (`climate.*`).
   - Optionally assign secondary/night climate entities.
   - Optionally link a seasonal switch (*Summer / Winter*).
   - Choose the number of daily time slots (1 to 10, default: 5).
2. **Seasonal Cycle & Night Zone**:
   - **Winter**: the scheduled preset mode is applied to **all** climate entities in the zone (main + secondary).
   - **Summer**: if the *Secondary/Night Zone Active in Summer* switch is disabled, secondary thermostats are omitted to avoid unwanted cooling.
3. **Supported Presets**:
   - `NONE` (slot disabled/skipped)
   - `comfort`
   - `standby`
   - `economy`
   - `building_protection`
   - `eco`
   - `boost`

---

## 🧩 Entities Created per Zone

| Platform | Translation Key | Icon | Description |
|---|---|---|---|
| **`switch`** | `crono_master` | `mdi:calendar-clock` | Master enable/disable switch for the chrono-thermostat |
| **`switch`** | `auto` | `mdi:thermostat-auto` | Automatic temperature control enable switch |
| **`switch`** | `secondary_summer` | `mdi:bed` | *(Optional)* Secondary/night zone inclusion in summer |
| **`time`** | `slot_time_1` .. `slot_time_N` | `mdi:clock-outline` | Start time for each configured time slot |
| **`select`** | `slot_preset_1` .. `slot_preset_N` | `mdi:tune-vertical` | Preset mode assigned to each time slot |
| **`sensor`** | `active_slot` | `mdi:clock-check-outline` | Currently active time slot |
| **`sensor`** | `next_slot` | `mdi:clock-fast` | Next scheduled time slot and start time |
| **`sensor`** | `zone_status` | `mdi:information-outline` | Diagnostic status (`active`, `crono_disabled`, `auto_disabled`) |
| **`button`** | `apply_now` | `mdi:play-circle-outline` | Button to force immediate application of the current slot |

---

## 📦 Installation

### Method 1: Via HACS (Recommended)
1. Ensure **HACS** is installed in your Home Assistant.
2. Go to **HACS** ➡️ **Integrations** ➡️ top right three dots ➡️ **Custom repositories**.
3. Add the repository URL:
   ```text
   https://github.com/evlas/Cronotermostato
   ```
4. Select **Integration** as category and click **Add**.
5. Search for **Cronotermostato Multizona**, click **Download**, and restart Home Assistant.

### Method 2: Manual Installation
1. Download `cronotermostato.zip` from [Releases](https://github.com/evlas/Cronotermostato/releases) or clone the repository.
2. Copy the folder `custom_components/cronotermostato/` into your Home Assistant's `custom_components/` directory:
   ```text
   /config/custom_components/cronotermostato/
   ```
3. Restart Home Assistant.

---

## 🛠️ Configuring a Zone

1. In Home Assistant, navigate to **Settings** ➡️ **Devices & Services**.
2. Click **Add Integration** in the bottom right corner.
3. Search for **Cronotermostato Multizona**.
4. Fill in the guided setup fields:
   - **Zone Name**: e.g. `Ground Floor`.
   - **Main Thermostats**: select the zone's `climate.*` entities.
   - **Secondary Thermostats (optional)**: e.g. bedroom thermostats.
   - **Summer/Winter Switch (optional)**: e.g. `switch.inverno_estate`.
   - **Invert season switch logic**: leave disabled if `ON = Winter` and `OFF = Summer`.
   - **Number of Daily Time Slots**: e.g. `5`.
5. Click **Submit**: the device with all its entities is generated instantly!

> [!TIP]
> You can reconfigure entities or settings at any time by clicking **Configure** on the integration card without losing your programmed schedules.

---

## 📱 Lovelace Dashboard Example

The file [`lovelace_example.yaml`](lovelace_example.yaml) is ready to copy into your dashboard:

```yaml
type: entities
title: 🌡️ Ground Floor Chrono-Thermostat
entities:
  - entity: switch.cronotermostato_ground_floor_chrono_thermostat_enable
  - entity: switch.cronotermostato_ground_floor_automatic_temperature_control
  - entity: sensor.cronotermostato_ground_floor_active_slot
  - entity: sensor.cronotermostato_ground_floor_next_slot
  - entity: button.cronotermostato_ground_floor_apply_current_slot
  - type: divider
  - entity: time.cronotermostato_ground_floor_slot_1_time
  - entity: select.cronotermostato_ground_floor_slot_1_mode
  - entity: time.cronotermostato_ground_floor_slot_2_time
  - entity: select.cronotermostato_ground_floor_slot_2_mode
  - entity: time.cronotermostato_ground_floor_slot_3_time
  - entity: select.cronotermostato_ground_floor_slot_3_mode
```

---

## ⚡ Custom Services

The integration exposes two services for use in automations or scripts:

### 1. `cronotermostato.apply_now`
Forces immediate application of the currently active time slot for the specified zone.
```yaml
action: cronotermostato.apply_now
data:
  zone_id: "Ground Floor"
```

### 2. `cronotermostato.set_slot`
Programmatically update the start time and/or preset mode for a specific time slot.
```yaml
action: cronotermostato.set_slot
data:
  zone_id: "Ground Floor"
  slot_number: 1
  time: "06:30:00"
  preset: "comfort"
```

---

## 📄 License
Released under the **GPL-3.0** open-source license.  
Author: **Vito Ammirata** ([@evlas](https://github.com/evlas)).
