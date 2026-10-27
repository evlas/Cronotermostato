# Multi-Zone Chrono-thermostat - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/evlas/Cronotermostato?color=blue&style=flat-square)](https://github.com/evlas/Cronotermostato/releases)
[![Hassfest](https://github.com/evlas/Cronotermostato/actions/workflows/hassfest.yml/badge.svg)](https://github.com/evlas/Cronotermostato/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/evlas/Cronotermostato/actions/workflows/hacs.yml/badge.svg)](https://github.com/evlas/Cronotermostato/actions/workflows/hacs.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)

🌐 *English version | [Versione in italiano](README.it.md)*

**Multi-Zone Chrono-thermostat** (*Cronotermostato Multizona*) is an advanced custom integration for **Home Assistant**, designed to evolve legacy YAML packages and automations into an elegant, reliable, and multi-zone climate controller with native **KNX Scenes** support.

It completely eliminates the need to maintain dozens of complex automations and auxiliary YAML entities (*input_datetime*, *input_select*, *input_boolean*).

---

## 📋 Evolution Highlights

| Feature | Legacy Setup (Package + Automations) | New Custom Integration |
|---|---|---|
| **Zones** | Hardcoded (only Ground Floor `pt` & Basement `psi`) | **Unlimited & Dynamic**: Config Flow UI |
| **Climate Entities** | Hardcoded groups/entities | **Dropdown selectors** per zone |
| **Automations removed** | **56 total automations** (40 package + 8 KNX scenes + 8 auto/manual) | **0 external automations**: built-in async state machine |
| **KNX Scene Integration** | 8 automations conditioned on `crono == off` | **Native event listener**: automatic preset sync |
| **Climate Off / Antifreeze** | External automations forcing building protection | **Native Off Mode**: automated fallback preset |
| **Startup Alignment** | Missing (waited for next scheduled trigger) | **Instant automatic alignment** on HA restart |
| **Time Pickers** | Generic `input_datetime` helpers | Native Home Assistant **`time`** platform |
| **Mode Pickers** | Manual `input_select` helpers | Native Home Assistant **`select`** platform |
| **Localization** | Italian only | **Full IT and EN support** via `translation_key` |

---

## 🕹️ Operating Modes (`select.zone_mode`)

Each zone provides a unified operating mode selector:
- **`cronotermostato` (Scheduled Chrono-thermostat)**: Evaluates active time slots and applies scheduled presets.
- **`scene_knx` (KNX Scene Control)**: Halts the time schedule and listens directly to KNX scene sensors.
- **`manuale` (Manual)**: Suspends all automation, leaving thermostats open for local/manual control.
- **`off` (Building Protection)**: Sends safety preset (`building_protection` or custom) to all thermostats in the zone.

---

## 🏛️ Direct KNX Scene Mapping

| KNX Scene Sensor | Value | Applied Preset | Description |
|---|---|---|---|
| `knx_scene_in_casa` | `3` | `comfort` | Occupants at home |
| `knx_scene_uscita` | `2` | `away` | Leaving home temporarily |
| `knx_scene_notte` | `4` | `economy` | Night time |
| `knx_scene_vacanza` | `5` | `building_protection` | Long absence / freeze protection |

---

## 🛠️ Custom Services

- **`cronotermostato.set_zone_mode`**: Change operating mode (`cronotermostato`, `scene_knx`, `manuale`, `off`).
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
