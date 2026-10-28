# Cronotermostato Multizona - Integrazione Home Assistant

[![Status: Work in Progress](https://img.shields.io/badge/Status-Work%20in%20Progress-orange.svg)]()
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/evlas/Cronotermostato?color=blue&style=flat-square)](https://github.com/evlas/Cronotermostato/releases)
[![Hassfest](https://github.com/evlas/Cronotermostato/actions/workflows/hassfest.yml/badge.svg)](https://github.com/evlas/Cronotermostato/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/evlas/Cronotermostato/actions/workflows/hacs.yml/badge.svg)](https://github.com/evlas/Cronotermostato/actions/workflows/hacs.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)

🌐 *[English version](README.md) | Versione in italiano*

> [!WARNING]
> ### 🚧 Work in Progress / In fase di sviluppo
> Questa integrazione è attualmente in fase attiva di sviluppo, test e ottimizzazione sul campo. Funzionalità, servizi ed entità potrebbero subire perfezionamenti e modifiche tra le varie versioni.

**Cronotermostato Multizona** è un'integrazione personalizzata (*Custom Integration*) per **Home Assistant**, progettata come evoluzione completa e moderna dei vecchi package YAML e delle automazioni per la gestione del clima, delle fasce orarie e delle **Scene / Presenza**.

Elimina completamente la necessità di mantenere decine di automazioni ed entità ausiliarie (*input_datetime*, *input_select*, *input_boolean*), integrando nativamente:
1. **Programmazione oraria multizona** a fasce giornaliere configurabili da 1 a 10 slot.
2. **Integrazione universale con sensori di Scena e Presenza** (es. `sensor.ultima_scena`) senza automazioni esterne.
3. **Gestione Clima OFF e Protezione Edificio** (*Building Protection / Antigelo*).
4. **Allineamento automatico all'avvio** e cambio stagione intelligente (Inverno/Estate).
5. **Gestione differenziata zone secondarie / notte** (con esclusione selettiva dal raffrescamento estivo).

---

## 📋 Sintesi dell'Evoluzione dal Package YAML e Automazioni

| Caratteristica | Configurazione Precedente (Package + Automazioni) | Nuova Integrazione Multizona |
|---|---|---|
| **Gestione Zone** | Rigida (solo Piano Terra `pt` e Seminterrato `psi`) | **Dinamica e illimitata**: configurazione via UI (*Config Flow*) |
| **Entità Clima** | Hardcoded (`climate.salotto`, `group.climapt`, ecc.) | **Selezionabili da menu a tendina** per ogni zona |
| **Automazioni eliminate** | **56 automazioni in totale** (40 nel package + 8 scene + 8 auto/manual) | **0 automazioni esterne**: motore a stati integrato in Python |
| **Gestione Scene / Presenza** | 8 automazioni separate sensibili allo stato di `crono` | **Ascolto e cambio preset nativo**: gestito direttamente dal coordinator |
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
- **`scene` (Controllo da Scena / Presenza)**:
  - Sospende la programmazione oraria e si mette in ascolto del sensore scena/presenza configurato (es. `sensor.ultima_scena`).
  - Applica immediatamente il preset corrispondente allo stato rilevato.
- **`manuale` (Controllo Libero)**:
  - Sospende ogni schedulazione e l'ascolto delle scene, lasciando l'utente libero di impostare i termostati manualmente o da tastierino/app.
- **`off` (Zona Spenta / Protezione Edificio)**:
  - Invia immediatamente il preset di sicurezza (`building_protection` o personalizzato) a tutti i termostati della zona e disattiva ogni schedulazione.

> **Retrocompatibilità**: gli switch `crono_master` e `auto` sono bidirezionalmente sincronizzati con la modalità operativa, consentendo di riutilizzare le card Lovelace esistenti senza modifiche.

---

## 🏛️ Integrazione Nativa con Sensore Scena / Presenza

L'integrazione supporta nativamente qualsiasi sensore unificato di scena o presenza (ad esempio `sensor.ultima_scena`), slegando completamente la logica da standard hardware specifici (KNX, Zigbee, Z-Wave o helper Home Assistant).

Gli stati del sensore vengono mappati in modo intelligente e case-insensitive sui preset climatici:

| Stato Rilevato (es. `sensor.ultima_scena`) | Preset Applicato | Significato |
|---|---|---|
| `In Casa`, `in_casa`, `Home`, `Comfort` | **`comfort`** | Presenza rilevata / Abitazione occupata |
| `Uscita`, `uscita`, `Away`, `Eco`, `Standby` | **`standby`** | Uscita temporanea / Economia energetica |
| `Notte`, `notte`, `Night`, `Sleep`, `Economy` | **`economy`** | Modalità notturna / Riposo |
| `Vacanza`, `vacanza`, `Holiday`, `Protezione` | **`building_protection`** | Assenza prolungata / Protezione antigelo |

---

## ⚙️ Configurazione via Interfaccia Utente

L'aggiunta e la modifica delle zone avviene interamente tramite l'interfaccia grafica di Home Assistant (*Config Flow* e *Options Flow*):

1. Vai su **Impostazioni** > **Dispositivi e Servizi** > **Aggiungi Integrazione**.
2. Cerca **Cronotermostato Multizona**.
3. Compila i parametri della zona:
   - **Nome della Zona**: es. `Piano Terra`, `Piano Seminterrato`, `Zona Notte`.
   - **Termostati Principali (`climate.*`)**: seleziona le entità termostato da controllare.
   - **Termostati Secondari / Notte (`climate.*`)**: *(Opzionale)* termostati delle camere che possono essere esclusi dal raffrescamento estivo tramite lo switch dedicato.
   - **Switch Estate/Inverno**: *(Opzionale)* seleziona lo switch o input_boolean di cambio stagione (con opzione di inversione logica).
   - **Numero di Fasce Orarie**: scegli quante fasce orarie giornaliere attivare (da 1 a 10, predefinito: `5`).
   - **Sensore Scena / Presenza**: *(Opzionale)* seleziona il sensore di stato scena (es. `sensor.ultima_scena`).
   - **Preset Spento/OFF**: preset inviato ai termostati quando la zona è in OFF (predefinito: `building_protection`).
   - **Allineamento all'avvio**: sincronizza e applica automaticamente la fascia attiva al riavvio di Home Assistant.

Puoi modificare tutti questi parametri in qualunque momento cliccando su **Configura** nella card dell'integrazione.

---

## 🧩 Entità Create per ogni Zona

| Piattaforma | Translation Key | Icona | Descrizione |
|---|---|---|---|
| **`select`** | `zone_mode` | `mdi:thermostat-cog` | Modalità operativa globale (`cronotermostato`, `scene`, `manuale`, `off`) |
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
  mode: "cronotermostato"  # oppure scene, manuale, off
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

## 📄 Licenza

Rilasciato sotto licenza [GNU General Public License v3.0](LICENSE).
