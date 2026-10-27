# Cronotermostato Multizona per Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)
[![Author](https://img.shields.io/badge/Author-Vito%20Ammirata%20(@evlas)-orange.svg)](https://github.com/evlas)

**Cronotermostato Multizona** è un'integrazione personalizzata (*Custom Integration*) per **Home Assistant**, nata come evoluzione avanzata del package YAML originale di gestione fasce orarie e preset per termostati HVAC.

Elimina la necessità di mantenere decine di automazioni e helper YAML complessi, offrendo una configurazione pulita direttamente dall'interfaccia grafica di Home Assistant con supporto completo per **zone termiche multiple e indipendenti**.

---

## 🚀 Punti di Forza rispetto al vecchio Package YAML

| Caratteristica | Vecchio Package YAML | Nuova Integrazione Multizona |
|---|---|---|
| **Zone Termiche** | Rigide (solo Piano Terra e Seminterrato) | **Illimitate e configurabili da UI** (*Config Flow*) |
| **Entità Clima** | Hardcoded nel file (`climate.salotto`, ecc.) | **Selezionabili liberamente dal menu a tendina** |
| **Automazioni nel Registro** | **40 automazioni individuali** (2.180 righe) | **0 automazioni**: motore gestito internamente in Python |
| **Allineamento all'avvio** | Mancante (attendeva il prossimo orario) | **Automatico**: calcola e applica la fascia attiva all'avvio |
| **Selettori Orario** | `input_datetime` generici | Piattaforma nativa **`time`** di Home Assistant |
| **Selettori Modalità** | `input_select` manuali | Piattaforma nativa **`select`** integrata nel dispositivo |
| **Diagnostica e Stato** | Nessuna indicazione in tempo reale | **Sensori dedicati**: *Fascia Attiva*, *Prossima Fascia*, *Stato* |
| **Pulsante di Forzatura** | Non presente | **Pulsante nativo**: applica immediatamente la fascia attiva |

---

## ⚙️ Logica di Funzionamento

Per ciascuna zona creata (es. *Piano Terra*, *Zona Notte*, *Taverna*):
1. **Configurazione Flessibile**:
   - Assegnazione dei termostati principali (`climate.*`).
   - Assegnazione facoltativa di termostati secondari / zona notte.
   - Collegamento facoltativo allo switch stagionale (*Estate / Inverno*).
   - Numero di fasce orarie giornaliere desiderate (da 1 a 10, predefinito: 5).
2. **Ciclo Stagionale & Zona Notte**:
   - **Inverno**: il preset programmato viene applicato a **tutti** i termostati (principali + secondari).
   - **Estate**: se lo switch *Zona Notte Partecipa in Estate* è disabilitato, i termostati secondari non vengono attivati per evitare raffrescamenti indesiderati.
3. **Preset Supportati**:
   - `NONE` (fascia disattivata/saltata)
   - `comfort`
   - `standby`
   - `economy`
   - `building_protection`
   - `eco`
   - `boost`

---

## 📦 Installazione

### Metodo 1: Manuale
1. Copia la cartella `custom_components/cronotermostato/` all'interno della cartella `custom_components/` del tuo Home Assistant:
   ```text
   /config/custom_components/cronotermostato/
   ```
2. Riavvia Home Assistant.

### Metodo 2: Tramite HACS
1. Apri HACS in Home Assistant.
2. Vai su **Integrazioni** ➡️ menu in alto a destra ➡️ **Repository personalizzati**.
3. Inserisci l'URL del repository e seleziona la categoria **Integrazione**.
4. Clicca su **Scarica** e riavvia Home Assistant.

---

## 🛠️ Configurazione di una Zona

1. In Home Assistant, vai su **Impostazioni** ➡️ **Dispositivi e Servizi**.
2. Clicca su **Aggiungi Integrazione** in basso a destra.
3. Cerca **Cronotermostato Multizona**.
4. Compila i campi guidati:
   - **Nome della Zona**: es. `Piano Terra`.
   - **Termostati Principali**: seleziona i climate desiderati (es. `climate.salotto`, `climate.cucina`).
   - **Termostati Secondari (opzionale)**: es. `climate.camera`.
   - **Switch Estate/Inverno (opzionale)**: es. `switch.inverno_estate`.
   - **Numero di Fasce Orarie**: es. `5`.
5. Clicca su **Invia**: il dispositivo con tutte le sue entità verrà creato istantaneamente!

> [!TIP]
> Puoi modificare i termostati o le impostazioni in qualsiasi momento cliccando su **Configura** nella scheda dell'integrazione, senza perdere le fasce orarie impostate.

---

## 📱 Esempio di Dashboard Lovelace

Nella cartella del progetto trovi il file [`lovelace_example.yaml`](lovelace_example.yaml) pronto da incollare nella tua dashboard:

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

## ⚡ Servizi Disponibili

L'integrazione registra due servizi utilizzabili in script o automazioni:

### 1. `cronotermostato.apply_now`
Forza l'applicazione della fascia attualmente in corso.
```yaml
action: cronotermostato.apply_now
data:
  zone_id: "Piano Terra"
```

### 2. `cronotermostato.set_slot`
Modifica l'orario o il preset di una specifica fascia oraria.
```yaml
action: cronotermostato.set_slot
data:
  zone_id: "Piano Terra"
  slot_number: 1
  time: "06:45:00"
  preset: "comfort"
```

---

## 📄 Licenza
Progetto rilasciato con licenza open source GPL-3.0.
Autore: **Vito Ammirata** ([@evlas](https://github.com/evlas)).
