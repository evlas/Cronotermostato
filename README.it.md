# Cronotermostato Multizona - Integrazione Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/evlas/Cronotermostato?color=blue&style=flat-square)](https://github.com/evlas/Cronotermostato/releases)
[![Hassfest](https://github.com/evlas/Cronotermostato/actions/workflows/hassfest.yml/badge.svg)](https://github.com/evlas/Cronotermostato/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/evlas/Cronotermostato/actions/workflows/hacs.yml/badge.svg)](https://github.com/evlas/Cronotermostato/actions/workflows/hacs.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)

🌐 *[English version](README.md) | Versione in italiano*

**Cronotermostato Multizona** è un'integrazione personalizzata (*Custom Integration*) per **Home Assistant**, progettata come evoluzione completa del package YAML originale e delle automazioni correlate per la gestione del clima, delle fasce orarie e delle **Scene KNX**.

Elimina completamente la necessità di mantenere decine di automazioni ed entità ausiliarie (*input_datetime*, *input_select*, *input_boolean*), integrando nativamente:
1. **Programmazione oraria multizona** a fasce giornaliere configurabili.
2. **Integrazione diretta con Scene KNX** (In Casa, Uscita, Notte, Vacanza) senza automazioni esterne.
3. **Gestione Clima OFF e Protezione Edificio** (*Building Protection / Antigelo*).
4. **Allineamento automatico all'avvio** e cambio stagione intelligente.

---

## 📋 Sintesi dell'Evoluzione dal Package YAML e Automazioni

| Caratteristica | Configurazione Precedente (Package + Automazioni) | Nuova Integrazione Multizona |
|---|---|---|
| **Gestione Zone** | Rigida (solo Piano Terra `pt` e Seminterrato `psi`) | **Dinamica e illimitata**: configurazione via UI (*Config Flow*) |
| **Entità Clima** | Hardcoded (`climate.salotto`, `group.climapt`, ecc.) | **Selezionabili da menu a tendina** per ogni zona |
| **Automazioni eliminate** | **56 automazioni in totale** (40 nel package + 8 scene KNX + 8 auto/manual) | **0 automazioni esterne**: motore a stati integrato in Python |
| **Gestione Scene KNX** | 8 automazioni separate sensibili allo stato di `crono` | **Ascolto e cambio preset nativo**: gestito direttamente dal coordinator |
| **Spegnimento Clima** | Automazioni con forzatura di `building_protection` | **Modalità OFF nativa**: invio automatico del preset di sicurezza |
| **Allineamento all'avvio** | Mancante (attendeva il prossimo orario) | **Automatico**: calcola e applica la fascia attiva all'avvio di HA |
| **Selettori Orario** | `input_datetime` generici | Piattaforma nativa **`time`** di Home Assistant |
| **Selettori Modalità** | `input_select` manuali | Piattaforma nativa **`select`** con preset e modalità operativa |
| **Diagnostica e Stato** | Nessuna indicazione in tempo reale | **Sensori dedicati**: *Fascia Attiva*, *Prossima Fascia*, *Stato Zona* |
| **Multilingua** | Solo testo fisso in italiano | **Localizzazione completa (IT ed EN)** con `translation_key` |

---

## 🕹️ Modalità Operative di Zona (`select.zone_mode`)

Ciascuna zona dispone di un selettore di modalità operativa che coordina il comportamento dei termostati:

- **`cronotermostato` (Programmazione Oraria)**:
  - Il motore schedulatore applica automaticamente i preset definiti nelle fasce orarie della giornata.
  - All'attivazione calcola immediatamente la fascia oraria corrente e la applica ai termostati.
- **`scene_knx` (Controllo da Scene KNX)**:
  - Sospende la programmazione oraria e si mette in ascolto dei sensori KNX configurati.
  - Applica immediatamente il preset corrispondente alla scena KNX rilevata.
- **`manuale` (Controllo Libero)**:
  - Sospende ogni schedulazione e l'ascolto delle scene KNX, lasciando l'utente libero di impostare i termostati manualmente o da app/tastierino.
- **`off` (Zona Spenta / Protezione Edificio)**:
  - Invia immediatamente il preset di sicurezza (`building_protection` o personalizzato) a tutti i termostati della zona e disattiva ogni schedulazione.

> **Retrocompatibilità**: gli switch `crono_master` e `auto` sono bidirezionalmente sincronizzati con la modalità operativa, consentendo di riutilizzare le card Lovelace esistenti senza modifiche.

---

## 🏛️ Integrazione Nativa Scene KNX

Nelle opzioni della zona è possibile associare i sensori KNX dedicati (oppure un sensore unificato DPT 17.001 / 18.001):

| Sensore Scena KNX | Valore Rilevato | Preset Applicato | Significato |
|---|---|---|---|
| `knx_scene_in_casa` | `3` | `comfort` | Persone presenti nell'abitazione |
| `knx_scene_uscita` | `2` | `away` | Abitazione vuota temporaneamente |
| `knx_scene_notte` | `4` | `economy` | Modalità notturna |
| `knx_scene_vacanza` | `5` | `building_protection` | Assenza prolungata / protezione antigelo |

---

## 🧩 Entità Create per ogni Zona

| Piattaforma | Translation Key | Icona | Descrizione |
|---|---|---|---|
| **`select`** | `zone_mode` | `mdi:thermostat-cog` | Modalità operativa globale (`cronotermostato`, `scene_knx`, `manuale`, `off`) |
| **`switch`** | `crono_master` | `mdi:calendar-clock` | Switch master per abilitare/disabilitare la programmazione oraria |
| **`switch`** | `auto` | `mdi:thermostat-auto` | Switch termoregolazione automatica (se spento porta in OFF) |
| **`switch`** | `secondary_summer` | `mdi:bed` | *(Opzionale)* Consente alla zona secondaria/notte di partecipare al raffrescamento estivo |
| **`time`** | `slot_time_X` | `mdi:clock-outline` | Orario di inizio della fascia oraria *X* (da 1 a N) |
| **`select`** | `slot_preset_X` | `mdi:tune-vertical` | Preset associato alla fascia oraria *X* |
| **`sensor`** | `active_slot` | `mdi:clock-check-outline` | Fascia attualmente attiva con orario e preset |
| **`sensor`** | `next_slot` | `mdi:clock-fast` | Prossima fascia programmata |
| **`sensor`** | `zone_status` | `mdi:information-outline` | Modalità corrente e diagnostica di zona |
| **`button`** | `apply_now` | `mdi:play-circle-outline` | Forza il ricalcolo e l'applicazione immediata della fascia corrente |

---

## 🛠️ Servizi Disponibili

### `cronotermostato.set_zone_mode`
Imposta la modalità operativa globale della zona:
```yaml
service: cronotermostato.set_zone_mode
data:
  zone_id: "Piano Terra"
  mode: "cronotermostato"  # oppure scene_knx, manuale, off
```

### `cronotermostato.apply_now`
Forza l'applicazione della fascia oraria attualmente attiva:
```yaml
service: cronotermostato.apply_now
data:
  zone_id: "Piano Terra"
```

### `cronotermostato.set_slot`
Modifica orario e preset di una fascia specifica:
```yaml
service: cronotermostato.set_slot
data:
  zone_id: "Piano Terra"
  slot_number: 1
  time: "06:30:00"
  preset: "comfort"
```

---

## 📦 Installazione tramite HACS

1. Assicurati che **HACS** sia installato nel tuo Home Assistant.
2. Apri **HACS** > **Integrazioni** > Menu tre puntini in alto a destra > **Repository personalizzati**.
3. Incolla l'URL del repository: `https://github.com/evlas/Cronotermostato`
4. Categoria: **Integrazione**.
5. Fai clic su **Aggiungi** e poi installa **Cronotermostato Multizona**.
6. Riavvia Home Assistant.
7. Vai su **Impostazioni** > **Dispositivi e Servizi** > **Aggiungi Integrazione** e cerca **Cronotermostato Multizona**.

---

## 🧹 Pulizia della Vecchia Configurazione

Per la procedura dettagliata di rimozione del vecchio package YAML e delle automazioni ridondanti, consulta il documento dedicato:
👉 [Guida Pulizia Configurazione](GUIDA_PULIZIA_CONFIGURAZIONE.md)

---

## 📄 Licenza

Rilasciato sotto licenza [GNU General Public License v3.0](LICENSE).
