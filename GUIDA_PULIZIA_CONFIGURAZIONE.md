# Guida alla Pulizia della Vecchia Configurazione Clima

Questa guida è un documento operativo passo-passo per il tuo uso personale, finalizzato a ripulire in totale sicurezza la configurazione di Home Assistant dopo l'installazione della nuova integrazione **Cronotermostato Multizona**.

Con questa transizione vengono eliminate **56 automazioni ridondanti** e oltre **45 helper YAML**, alleggerendo sensibilmente il database, l'avvio e il carico dell'event loop di Home Assistant.

---

## 🎯 Chiarimento Fondamentale: SetPoint vs Fasce Orarie

### 1. I SetPoint di Temperatura (°C) ➔ DA MANTENERE
La schermata **SetPoint Piano Terra** e **SetPoint Piano Seminterrato** (antigelo 5°C, economy 16°C, comfort 21°C, anticalore 35°C, ecc.) con il tasto **"Update Setpoint PT / PSI"**:
- **NON era gestita dal package `cronotermostato.yaml`**.
- È gestita dai file `input_numbers/termoregolazione.yaml`, `input_booleans/termoregolazione.yaml` e dalle 2 automazioni:
  - `Gestione SetPoint PT` (ID `'1695756904042'`)
  - `Gestione SetPoint PSI` (ID `'1695756937943'`)
- Queste servono a inviare via bus KNX (`knx.send`) i valori di calibrazione delle temperature fisiche direttamente dentro le memorie dei termostati/sonde KNX.
- 👉 **Quella card Lovelace, quegli `input_number` e quelle 2 automazioni NON VANNO TOCCATI né eliminati!**

### 2. Lo switch "Raffrescamento Zona Notte" ➔ INTEGRATO NATIVAMENTE
- Nella schermata sotto "Condizionamento" c'è lo switch **Raffrescamento Zona Notte**:
  - Nel vecchio package si chiamava `input_boolean.zona_notte_partecipa_estate_pt` (e `_psi`).
  - Quando era disattivato in estate, il cronotermostato escludeva le camere da letto dal raffrescamento inviando il preset solo alla zona giorno.
- **Nella nuova integrazione questo switch è già integrato nativamente**:
  - Viene generato automaticamente come:
    `switch.cronotermostato_<nome_zona>_zona_secondaria_notte_partecipa_in_estate`
  - Basta inserire i termostati della notte (es. `climate.camera_pt`) nel campo **"Termostati Secondari / Notte"** durante la configurazione della zona.
  - Sulla tua card Lovelace potrai sostituire il vecchio `input_boolean` con il nuovo `switch`, chiamandolo comodamente "Raffrescamento Zona Notte".

---

## 📋 Riepilogo di Cosa Viene Rimosso

| Componente Vecchio | Dove si trova | Cosa conteneva | Stato con la Nuova Integrazione |
|---|---|---|---|
| **Package `cronotermostato.yaml`** | cartella `packages/` | 40 automazioni, 20 `input_datetime`, 20 `input_select`, 7 `input_boolean` | **Da eliminare/disabilitare interamente** |
| **8 Automazioni Scene Clima KNX** | `automations.yaml` | Cambio preset su scene 2, 3, 4, 5 condizionato a crono=off | **Da eliminare da `automations.yaml`** |
| **8 Automazioni Termoregolazione Auto/Manuale** | `automations.yaml` | Gestione on/off incrociata tra switch manuale/auto e preset off | **Da eliminare da `automations.yaml`** |

---

## 🚀 FASE 1: Configurazione delle Due Zone nella Nuova Integrazione

Prima di cancellare la vecchia configurazione, installa l'integrazione e crea le due zone termiche via UI:

1. Riavvia Home Assistant dopo aver inserito `custom_components/cronotermostato` (o installato da HACS).
2. Vai su **Impostazioni** > **Dispositivi e Servizi** > **Aggiungi Integrazione** > cerca **Cronotermostato Multizona**.

### 🔹 Zona 1: Piano Terra
- **Nome della Zona**: `Piano Terra`
- **Termostati Principali (`climate.*`)**:
  - `climate.salotto`
  - `climate.cucina`
  - `climate.disimpegno_pt`
  - `climate.bagno_pt`
- **Termostati Secondari / Notte**:
  - `climate.camera_pt` *(questo è il termostato comandato dallo switch Raffrescamento Zona Notte!)*
- **Switch Estate/Inverno**: `switch.inverno_estate` (lascia `Inverti logica` disabilitato: ON=Inverno)
- **Numero Fasce**: `5`
- **Sensore Scena / Presenza**: `sensor.ultima_scena` (rileva automaticamente *In Casa*, *Uscita*, *Notte*, *Vacanza*)
- **Preset Spento/OFF**: `building_protection`

### 🔹 Zona 2: Piano Seminterrato
- **Nome della Zona**: `Piano Seminterrato`
- **Termostati Principali (`climate.*`)**:
  - `climate.taverna`
  - `climate.bagno_psi`
  - `climate.disimpegno_psi`
  - `climate.lavanderia`
  - `climate.studio`
- **Termostati Secondari / Notte**:
  - `climate.camera_ospiti`
- **Switch Estate/Inverno**: `switch.inverno_estate`
- **Numero Fasce**: `5`
- **Sensore Scena / Presenza**: `sensor.ultima_scena` (stesso sensore unificato di casa).
- **Preset Spento/OFF**: `building_protection`

---

## 🗑️ FASE 2: Eliminazione Automazioni da `automations.yaml`

Apri il file `/config/automations.yaml` (oppure vai in **Impostazioni** > **Automazioni e Scene** dall'interfaccia web) ed elimina le seguenti **16 automazioni**:

### 1. Le 8 Automazioni Scene Clima KNX
Queste automazioni inviavano i preset a `group.climapt` e `group.climapsi` quando `crono` era spento. Ora sono gestite nativamente dall'integrazione in modalità **Scene / Presenza**:

| ID | Alias | Azione | Note |
|---|---|---|---|
| `'1695758419665'` | **Scena Vacanza PSI** | ❌ ELIMINARE | Risolve anche il bug legacy dove agiva per errore su `group.climapt` |
| `'1695758447900'` | **Scena Uscita PSI** | ❌ ELIMINARE | Risolve il bug legacy dove agiva per errore su `group.climapt` |
| `'1695758475409'` | **Scena In Casa PSI** | ❌ ELIMINARE | Risolve il bug legacy dove agiva per errore su `group.climapt` |
| `'1695758501803'` | **Scena Notte PSI** | ❌ ELIMINARE | Integrato nel coordinator |
| `'1695758525947'` | **Scena Vacanza PT** | ❌ ELIMINARE | Integrato nel coordinator |
| `'1695758548531'` | **Scena Uscita PT** | ❌ ELIMINARE | Integrato nel coordinator |
| `'1695758572333'` | **Scena In Casa PT** | ❌ ELIMINARE | Integrato nel coordinator |
| `'1695758602211'` | **Scena Notte PT** | ❌ ELIMINARE | Integrato nel coordinator |

### 2. Le 8 Automazioni Termoregolazione Auto/Manuale
Queste automazioni gestivano la mutua esclusione tra gli switch e forzavano `building_protection` quando veniva disabilitata la termoregolazione:

| ID | Alias | Azione | Note |
|---|---|---|---|
| `'1695757910508'` | **Termoregolazione Auto PSI On** | ❌ ELIMINARE | Gestito internamente |
| `'1695757952875'` | **Termoregolazione Auto PT On** | ❌ ELIMINARE | Gestito internamente |
| `'1695757981625'` | **Termoregolazione Auto PSI Off** | ❌ ELIMINARE | La modalità OFF ora invia `building_protection` |
| `'1695758005604'` | **Termoregolazione Auto PT Off** | ❌ ELIMINARE | La modalità OFF ora invia `building_protection` |
| `'1695758043121'` | **Termoregolazione Manuale PSI Off** | ❌ ELIMINARE | Non più necessario |
| `'1695758069323'` | **Termoregolazione Manuale PSI On** | ❌ ELIMINARE | Sostituito dalla modalità `manuale` |
| `'1695758094398'` | **Termoregolazione Manuale PT Off** | ❌ ELIMINARE | Non più necessario |
| `'1695758126077'` | **Termoregolazione Manuale PT On** | ❌ ELIMINARE | Sostituito dalla modalità `manuale` |

> ⚠️ **ATTENZIONE - Automazioni e Helper da MANTENERE ASSOLUTAMENTE**:
> 1. **Automazioni SetPoint KNX**:
>    - `'1695756904042'` (**Gestione SetPoint PT**)
>    - `'1695756937943'` (**Gestione SetPoint PSI**)
>    - Tutti gli `input_number` in `input_numbers/termoregolazione.yaml`
>    - Gli `input_boolean.update_setpoint_pt` e `update_setpoint_psi`.
> 2. **Automazioni Reset KNX**:
>    - `'1695758294486'` (**Scena Vacanza RST**)
>    - `'1695758317122'` (**Scena Uscita RST**)
>    - `'1695758350025'` (**Scena In Casa RST**)
>    - `'1695758381070'` (**Scena Notte RST**)
>    - **Prese Scena ON** e **Prese Scena OFF**.

---

## 📦 FASE 3: Rimozione del Package `cronotermostato.yaml`

1. Apri la cartella dei packages (solitamente `/config/packages/` o inclusa in `configuration.yaml`).
2. Rimuovi o rinomina il file:
   ```bash
   mv /config/packages/cronotermostato.yaml /config/packages/cronotermostato.yaml.bak
   ```
3. Se in `configuration.yaml` avevi una riga dedicata come:
   ```yaml
   # cronotermostato: !include packages/cronotermostato.yaml
   ```
   commentala o rimuovila.
4. Ricarica la configurazione YAML o riavvia Home Assistant.

Tutti i seguenti vecchi helper del package spariranno automaticamente:
- `input_datetime.time_fascia_1_inverno_pt` ... fino a `fascia_5_estate_psi` (20 helper)
- `input_select.modalita_fascia_1_inverno_pt` ... fino a `fascia_5_estate_psi` (20 helper)
- `input_boolean.crono_pt`, `input_boolean.crono_psi`
- `input_boolean.termoregolazioneautopt`, `input_boolean.termoregolazioneautopsi`
- `input_boolean.termoregolazionemanualept`, `input_boolean.termoregolazionemanualepsi`
- `input_boolean.zona_notte_partecipa_estate_pt`, `input_boolean.zona_notte_partecipa_estate_psi`

---

## 📱 FASE 4: Aggiornamento della Dashboard Lovelace

Nelle tue card della plancia:

1. **Card SetPoint KNX (quella nella tua foto)**:
   - Lasciala esattamente come è!
   - L'unica modifica che puoi fare è sostituire `input_boolean.zona_notte_partecipa_estate_pt` con il nuovo:
     `switch.cronotermostato_piano_terra_zona_secondaria_notte_partecipa_in_estate`
     (puoi dargli come nome personalizzato nella card: `Raffrescamento Zona Notte`).

2. **Nuova Entità Modalità Operativa**:
   - `select.cronotermostato_piano_terra_modalita_operativa`
   - `select.cronotermostato_piano_seminterrato_modalita_operativa`
   Permette di scegliere con un solo tocco tra:
   - 🕒 `Cronotermostato (Programmazione oraria)`
   - 🏛️ `Scene / Presenza`
   - ✋ `Manuale`
   - ❄️ `Spento (Protezione antigelo)`

3. **Selettori Orario e Preset delle Fasce**:
   Sostituisci i vecchi `input_datetime` e `input_select` con le nuove entità native:
   - `time.cronotermostato_piano_terra_orario_fascia_1` ... `5`
   - `select.cronotermostato_piano_terra_modalita_fascia_1` ... `5`

4. **Card completa d'esempio**:
   Consulta il file [`lovelace_example.yaml`](lovelace_example.yaml).

---

## ✅ FASE 5: Checklist di Collaudo

1. [ ] **Test Modalità Cronotermostato**:
   - Imposta la modalità su `Cronotermostato`.
   - Verifica che `sensor.cronotermostato_piano_terra_fascia_attiva` riporti lo slot corrente.
2. [ ] **Test Scene / Presenza da Tastiera/Pulsantiera**:
   - Imposta la modalità su `Scene / Presenza` (oppure spegni lo switch `crono`).
   - Verifica che modificando lo stato di `sensor.ultima_scena` (In Casa, Uscita, Notte, Vacanza), i termostati assumano istantaneamente i rispettivi preset (`comfort`, `away`, `economy`, `building_protection`).
3. [ ] **Test Switch Raffrescamento Notte**:
   - Con switch disattivato in estate, verifica che i termostati secondari (camere) non ricevano il cambio preset.
4. [ ] **Test Tasto "Update Setpoint PT / PSI"**:
   - Modifica un valore (es. comfort da 21 a 21.5) e premi "Update Setpoint PT": verifica che l'automazione continui a inviare correttamente i telegrammi KNX alle sonde.
