# Multi-Zone Chrono-thermostat - Home Assistant Integration

[![Status: Work in Progress](https://img.shields.io/badge/Status-Work%20in%20Progress-orange.svg)]()
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/evlas/Cronotermostato?color=blue&style=flat-square)](https://github.com/evlas/Cronotermostato/releases)
[![Hassfest](https://github.com/evlas/Cronotermostato/actions/workflows/hassfest.yml/badge.svg)](https://github.com/evlas/Cronotermostato/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/evlas/Cronotermostato/actions/workflows/hacs.yml/badge.svg)](https://github.com/evlas/Cronotermostato/actions/workflows/hacs.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)

🌐 *English version | [Versione in italiano](README.it.md)*

> [!WARNING]
> ### 🚧 Work in Progress
> This integration is currently under active development, real-world testing, and ongoing optimization. Features, entities, and services may evolve across revisions.

**Multi-Zone Chrono-thermostat** (*Cronotermostato Multizona*) is an advanced custom integration for **Home Assistant**, designed to evolve legacy YAML packages and automations into an elegant, reliable, and multi-zone climate controller with native **Scene / Presence** support.

It completely eliminates the need to maintain dozens of complex automations and auxiliary YAML entities (*input_datetime*, *input_select*, *input_boolean*).

---

## 📋 Evolution Highlights

| Feature | Legacy Setup (Package + Automations) | New Custom Integration |
|---|---|---|
| **Zones** | Hardcoded (only Ground Floor `pt` & Basement `psi`) | **Unlimited & Dynamic**: Config Flow UI |
| **Climate Entities** | Hardcoded groups/entities | **Dropdown selectors** per zone |
| **Automations removed** | **56 total automations** (40 package + 8 scenes + 8 auto/manual) | **0 external automations**: built-in async state machine |
| **Scene & Presence Integration** | 8 automations conditioned on `crono == off` | **Native event listener**: automatic preset sync |
| **Climate Off / Antifreeze** | External automations forcing building protection | **Native Off Mode**: automated fallback preset |
| **Startup Alignment** | Missing (waited for next scheduled trigger) | **Instant automatic alignment** on HA restart |
| **Time Pickers** | Generic `input_datetime` helpers | Native Home Assistant **`time`** platform |
| **Mode Pickers** | Manual `input_select` helpers | Native Home Assistant **`select`** platform |
| **Localization** | Italian only | **Full IT and EN support** via `translation_key` |

---

## 🕹️ Operating Modes (`select.zone_mode`)

Each zone provides a unified operating mode selector:
- **`cronotermostato` (Scheduled Chrono-thermostat)**: Evaluates active time slots and applies scheduled presets.
- **`scene` (Scene / Presence Control)**: Halts the time schedule and listens directly to the configured scene/presence sensor (e.g. `sensor.last_scene`).
- **`manuale` (Manual)**: Suspends all automation, leaving thermostats open for local/manual control.
- **`off` (Building Protection)**: Sends safety preset (`building_protection` or custom) to all thermostats in the zone.

---

## 🏛️ Native Scene & Presence Sensor Integration

The integration natively supports any unified scene or presence sensor (e.g., `sensor.ultima_scena`), uncoupling your climate setup from vendor-specific protocols (KNX, Zigbee, Z-Wave or helper templates).

Sensor states are mapped case-insensitively to standard HVAC presets:

| Detected State (e.g. `sensor.last_scene`) | Applied Preset | Meaning |
|---|---|---|
| `In Casa`, `in_casa`, `Home`, `Comfort` | **`comfort`** | Occupants at home |
| `Uscita`, `uscita`, `Away`, `Eco`, `Standby` | **`standby`** | Leaving home temporarily |
| `Notte`, `notte`, `Night`, `Sleep`, `Economy` | **`economy`** | Sleeping / Night mode |
| `Vacanza`, `vacanza`, `Holiday`, `Protezione` | **`building_protection`** | Prolonged absence / Freeze protection |

---

## ⚙️ Configuration via UI

Setting up and modifying zones is done entirely through the Home Assistant UI (*Config Flow* and *Options Flow*):

1. Go to **Settings** > **Devices & Services** > **Add Integration**.
2. Search for **Cronotermostato Multizona**.
3. Configure your zone parameters:
   - **Zone Name**: e.g., `Ground Floor`, `Basement`, `Night Zone`.
   - **Main Thermostats (`climate.*`)**: select the thermostats controlled by this zone.
   - **Secondary / Night Thermostats (`climate.*`)**: *(Optional)* bedroom thermostats that can be excluded from summer cooling via the dedicated switch.
   - **Summer/Winter Switch**: *(Optional)* season switch entity (with invert logic toggle).
   - **Daily Time Slots**: number of daily slots (1 to 10, default: `5`).
   - **Scene / Presence Sensor**: *(Optional)* unified scene state sensor (e.g. `sensor.ultima_scena`).
   - **Off Mode Preset**: preset applied when zone is OFF (default: `building_protection`).
   - **Startup Alignment**: auto-sync active slot on Home Assistant reboot.

---

## 🛠️ Custom Services

- **`cronotermostato.set_zone_mode`**: Change operating mode (`cronotermostato`, `scene`, `manuale`, `off`).
- **`cronotermostato.apply_now`**: Force immediate evaluation and application of the current time slot.
- **`cronotermostato.set_slot`**: Programmatically modify start time and preset for any slot.

---

## 📦 Installation via HACS

1. In Home Assistant, open **HACS** > **Integrations**.
2. Click the three dots (top right) > **Custom repositories**.
3. Add `https://github.com/evlas/Cronotermostato` as **Integration**.
4. Install and restart Home Assistant.
5. Go to **Settings** > **Devices & Services** > **Add Integration** and search for **Cronotermostato Multizona**.

---

## 🧹 Legacy Configuration Cleanup Guide

For step-by-step instructions on decommissioning the legacy package and automations, see:
👉 [Cleanup Guide (Italian)](GUIDA_PULIZIA_CONFIGURAZIONE.md)

---

## 📄 License

Released under [GNU General Public License v3.0](LICENSE).
