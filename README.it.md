# Cronotermostato Multizona - Integrazione Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/evlas/Cronotermostato?color=blue&style=flat-square)](https://github.com/evlas/Cronotermostato/releases)
[![Hassfest](https://github.com/evlas/Cronotermostato/actions/workflows/hassfest.yml/badge.svg)](https://github.com/evlas/Cronotermostato/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/evlas/Cronotermostato/actions/workflows/hacs.yml/badge.svg)](https://github.com/evlas/Cronotermostato/actions/workflows/hacs.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)

🌐 *[English version](README.md) | Versione in italiano*

**Cronotermostato Multizona** è un'integrazione personalizzata (*Custom Integration*) per **Home Assistant**, progettata come evoluzione avanzata del package YAML originale di gestione fasce orarie e preset per impianti di climatizzazione e riscaldamento HVAC.

Elimina la necessità di mantenere decine di automazioni e helper YAML complessi, offrendo una configurazione pulita direttamente dall'interfaccia grafica di Home Assistant con supporto completo per **zone termiche multiple e indipendenti**.

---

## 📋 Sintesi dell'Evoluzione dal Package YAML

| Caratteristica | Vecchio Package YAML (`cronotermostato.yaml`) | Nuova Integrazione Multizona |
|---|---|---|
| **Gestione Zone** | Rigida (solo Piano Terra `pt` e Seminterrato `psi`) | **Dinamica e illimitata**: configurazione via UI (*Config Flow*) |
| **Entità Clima** | Hardcoded (`climate.salotto`, `group.climapt`, ecc.) | **Selezionabili da menu a tendina** per ogni zona |
| **Automazioni nel Registro** | **40 automazioni individuali** (2.180 righe) | **0 automazioni**: motore schedulatore interno in Python |
| **Allineamento all'avvio** | Mancante (attendeva il prossimo orario) | **Automatico**: calcola e applica la fascia attiva all'avvio |
| **Selettori Orario** | `input_datetime` generici | Piattaforma nativa **`time`** di Home Assistant |
| **Selettori Modalità** | `input_select` manuali | Piattaforma nativa **`select`** con preset standard |
| **Diagnostica e Stato** | Nessuna indicazione in tempo reale | **Sensori dedicati**: *Fascia Attiva*, *Prossima Fascia*, *Stato* |
| **Multilingua** | Solo testo fisso in italiano | **Localizzazione completa (IT ed EN)** con `translation_key` |

---

## ⚙️ Logica di Funzionamento

Per ciascuna zona termica creata (es. *Piano Terra*, *Zona Notte*, *Taverna*):
1. **Configurazione Guidata**:
   - Assegnazione dei termostati principali (`climate.*`).
   - Assegnazione facoltativa di termostati secondari / zona notte.
   - Collegamento facoltativo allo switch stagionale (*Estate / Inverno*).
   - Numero di fasce orarie giornaliere desiderate (da 1 a 10, predefinito: 5).
2. **Ciclo Stagionale & Zona Notte**:
   - **Inverno**: il preset programmato viene inviato a **tutti** i termostati della zona (principali + secondari).
   - **Estate**: se lo switch *Zona Secondaria/Notte Partecipa in Estate* è disabilitato, i termostati secondari non vengono attivati per evitare raffrescamenti indesiderati.
3. **Preset Supportati**:
   - `NONE` (fascia disattivata/saltata)
   - `comfort`
   - `standby`
   - `economy`
   - `building_protection`
   - `eco`
   - `boost`

---

## 🧩 Entità Create per ogni Zona

| Piattaforma | Translation Key | Icona | Descrizione |
|---|---|---|---|
| **`switch`** | `crono_master` | `mdi:calendar-clock` | Switch master per abilitare/disabilitare il cronotermostato |
| **`switch`** | `auto` | `mdi:thermostat-auto` | Switch termoregolazione automatica |
| **`switch`** | `secondary_summer` | `mdi:bed` | *(Opzionale)* Inclusione zona secondaria/notte in estate |
| **`time`** | `slot_time_1` .. `slot_time_N` | `mdi:clock-outline` | Orario di avvio per ciascuna fascia programmata |
| **`select`** | `slot_preset_1` .. `slot_preset_N` | `mdi:tune-vertical` | Preset / modalità assegnata a ciascuna fascia |
| **`sensor`** | `active_slot` | `mdi:clock-check-outline` | Fascia oraria attualmente in esecuzione |
| **`sensor`** | `next_slot` | `mdi:clock-fast` | Prossima fascia programmata e relativo orario |
| **`sensor`** | `zone_status` | `mdi:information-outline` | Stato diagnostico (`active`, `crono_disabled`, `auto_disabled`) |
| **`button`** | `apply_now` | `mdi:play-circle-outline` | Pulsante per forzare l'applicazione della fascia corrente |

---

## 📦 Installazione

### Metodo 1: Tramite HACS (Consigliato)
1. Assicurati che **HACS** sia installato nel tuo Home Assistant.
2. Vai su **HACS** ➡️ **Integrazioni** ➡️ menu con i tre puntini in alto a destra ➡️ **Repository personalizzati**.
3. Inserisci l'URL del repository:
   ```text
   https://github.com/evlas/Cronotermostato
   ```
4. Seleziona come categoria **Integrazione** e clicca su **Aggiungi**.
5. Cerca **Cronotermostato Multizona**, clicca su **Scarica** e riavvia Home Assistant.

### Metodo 2: Installazione Manuale
1. Scarica l'archivio `cronotermostato.zip` dalle [Releases](https://github.com/evlas/Cronotermostato/releases) o clona il repository.
2. Copia la cartella `custom_components/cronotermostato/` all'interno della cartella `custom_components/` della tua installazione di Home Assistant:
   ```text
   /config/custom_components/cronotermostato/
   ```
3. Riavvia Home Assistant.

---

## 🛠️ Configurazione di una Zona

1. In Home Assistant, vai su **Impostazioni** ➡️ **Dispositivi e Servizi**.
2. Clicca su **Aggiungi Integrazione** in basso a destra.
3. Cerca **Cronotermostato Multizona**.
4. Compila i campi guidati:
   - **Nome della Zona**: es. `Piano Terra`.
   - **Termostati Principali**: seleziona le entità `climate.*` della zona.
   - **Termostati Secondari (opzionale)**: es. termostati delle camere da letto.
   - **Switch Estate/Inverno (opzionale)**: es. `switch.inverno_estate`.
   - **Inverti logica switch stagione**: lascia disattivato se `ON = Inverno` e `OFF = Estate`.
   - **Numero di Fasce Orarie**: es. `5`.
5. Clicca su **Invia**: il dispositivo con tutte le sue entità verrà generato automaticamente!

> [!TIP]
> Puoi modificare i termostati o le impostazioni in qualsiasi momento cliccando su **Configura** nella scheda dell'integrazione, senza perdere le fasce orarie impostate.

---

## 📱 Esempio di Dashboard Lovelace

Nella cartella del repository trovi il file [`lovelace_example.yaml`](lovelace_example.yaml) pronto all'uso:

```yaml
type: entities
title: 🌡️ Cronotermostato Piano Terra
entities:
  - entity: switch.cronotermostato_piano_terra_abilitazione_cronotermostato
  - entity: switch.cronotermostato_piano_terra_termoregolazione_automatica
  - entity: sensor.cronotermostato_piano_terra_fascia_attiva
  - entity: sensor.cronotermostato_piano_terra_prossima_fascia
  - entity: button.cronotermostato_piano_terra_applica_fascia_corrente
  - type: divider
  - entity: time.cronotermostato_piano_terra_orario_fascia_1
  - entity: select.cronotermostato_piano_terra_modalita_fascia_1
  - entity: time.cronotermostato_piano_terra_orario_fascia_2
  - entity: select.cronotermostato_piano_terra_modalita_fascia_2
  - entity: time.cronotermostato_piano_terra_orario_fascia_3
  - entity: select.cronotermostato_piano_terra_modalita_fascia_3
```

---

## ⚡ Servizi Personalizzati

L'integrazione espone due servizi utilizzabili in script o automazioni esterne:

### 1. `cronotermostato.apply_now`
Forza l'applicazione immediata della fascia oraria attualmente attiva per la zona specificata.
```yaml
action: cronotermostato.apply_now
data:
  zone_id: "Piano Terra"
```

### 2. `cronotermostato.set_slot`
Modifica programmaticamente l'orario e/o il preset di una specifica fascia.
```yaml
action: cronotermostato.set_slot
data:
  zone_id: "Piano Terra"
  slot_number: 1
  time: "06:30:00"
  preset: "comfort"
```

---

## 📄 Licenza
Rilasciato sotto licenza open-source **GPL-3.0**.  
Autore: **Vito Ammirata** ([@evlas](https://github.com/evlas)).
