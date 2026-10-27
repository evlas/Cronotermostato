# Guida alla Pulizia della Vecchia Configurazione Clima

Questa guida è un documento operativo passo-passo per il tuo uso personale, finalizzato a ripulire in totale sicurezza la configurazione di Home Assistant dopo l'installazione della nuova integrazione **Cronotermostato Multizona**.

Con questa transizione vengono eliminate **56 automazioni ridondanti** e oltre **45 helper YAML**, alleggerendo sensibilmente il database, l'avvio e il carico dell'event loop di Home Assistant.

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
  - `climate.camera_pt`
- **Termostati Secondari / Notte (opzionale)**:
  - `climate.camera_pt` (se vuoi escluderla dal raffrescamento estivo)
- **Switch Estate/Inverno**: `switch.inverno_estate` (lascia `Inverti logica` disabilitato: ON=Inverno)
- **Numero Fasce**: `5`
- **Sensori Scene KNX**:
  - *In Casa (3)*: `sensor.sceneknxincasa`
  - *Uscita (2)*: `sensor.sceneknxuscita`
  - *Notte (4)*: `sensor.sceneknxnotte`
  - *Vacanza (5)*: `sensor.sceneknxvacanza`
- **Preset Spento/OFF**: `building_protection`

### 🔹 Zona 2: Piano Seminterrato
- **Nome della Zona**: `Piano Seminterrato`
- **Termostati Principali (`climate.*`)**:
  - `climate.taverna`
  - `climate.bagno_psi`
  - `climate.disimpegno_psi`
  - `climate.lavanderia`
  - `climate.camera_ospiti`
  - `climate.studio`
- **Switch Estate/Inverno**: `switch.inverno_estate`
- **Numero Fasce**: `5`
- **Sensori Scene KNX**: gli stessi sensori KNX usati per il PT.
- **Preset Spento/OFF**: `building_protection`

---

## 🗑️ FASE 2: Eliminazione Automazioni da `automations.yaml`

Apri il file `/config/automations.yaml` (oppure vai in **Impostazioni** > **Automazioni e Scene** dall'interfaccia web) ed elimina le seguenti **16 automazioni**:

### 1. Le 8 Automazioni Scene Clima KNX
Queste automazioni inviavano i preset a `group.climapt` e `group.climapsi` quando `crono` era spento. Ora sono gestite nativamente dall'integrazione in modalità **Scene KNX**:

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

> ⚠️ **ATTENZIONE - Automazioni da MANTENERE**:
> NON cancellare le automazioni di reset KNX:
> - `'1695758294486'` (**Scena Vacanza RST**)
> - `'1695758317122'` (**Scena Uscita RST**)
> - `'1695758350025'` (**Scena In Casa RST**)
> - `'1695758381070'` (**Scena Notte RST**)
> 
> Queste servono al bus KNX per resettare lo stato dei pulsanti/scene dopo 3 secondi e non interferiscono con il clima.
> Mantieni anche **Prese Scena ON** e **Prese Scena OFF**.

---

## 📦 FASE 3: Rimozione del Package `cronotermostato.yaml`

1. Apri la cartella dei packages (solitamente `/config/packages/` o inclusa in `configuration.yaml`).
2. Rimuovi o rinomina il file:
   ```bash
   # Esempio rinomina di backup prima della cancellazione definitiva:
   mv /config/packages/cronotermostato.yaml /config/packages/cronotermostato.yaml.bak
   ```
3. Se in `configuration.yaml` avevi una riga dedicata come:
   ```yaml
   # cronotermostato: !include packages/cronotermostato.yaml
   ```
   commentala o rimuovila.
4. Ricarica la configurazione YAML o riavvia Home Assistant.

Tutti i seguenti vecchi helper spariranno automaticamente:
- `input_datetime.time_fascia_1_inverno_pt` ... fino a `fascia_5_estate_psi` (20 helper)
- `input_select.modalita_fascia_1_inverno_pt` ... fino a `fascia_5_estate_psi` (20 helper)
- `input_boolean.crono_pt`, `input_boolean.crono_psi`
- `input_boolean.termoregolazioneautopt`, `input_boolean.termoregolazioneautopsi`
- `input_boolean.termoregolazionemanualept`, `input_boolean.termoregolazionemanualepsi`
- `input_boolean.zonanotteinvernopt`

---

## 📱 FASE 4: Aggiornamento della Dashboard Lovelace

Nelle tue card della plancia:

1. **Nuova Entità Consigliata**:
   Aggiungi il selettore unico di modalità:
   - `select.cronotermostato_piano_terra_modalita_operativa`
   - `select.cronotermostato_piano_seminterrato_modalita_operativa`
   Questo menu a tendina ti permette di scegliere con un solo tocco tra:
   - 🕒 `Cronotermostato (Programmazione oraria)`
   - 🏛️ `Scene KNX`
   - ✋ `Manuale`
   - ❄️ `Spento (Protezione antigelo)`

2. **Selettori Orario e Preset delle Fasce**:
   Sostituisci i vecchi `input_datetime` e `input_select` con le nuove entità native:
   - `time.cronotermostato_piano_terra_orario_fascia_1` ... `5`
   - `select.cronotermostato_piano_terra_modalita_fascia_1` ... `5`

3. **Per consultare una card completa pronta all'uso**:
   Vedi il file [`lovelace_example.yaml`](lovelace_example.yaml).

---

## ✅ FASE 5: Checklist di Collaudo

Effettua questa rapida sequenza di verifiche per accertarti che tutto risponda correttamente:

1. [ ] **Test Modalità Cronotermostato**:
   - Imposta la modalità su `Cronotermostato`.
   - Verifica che il sensore `sensor.cronotermostato_piano_terra_fascia_attiva` riporti lo slot corrente.
   - Premi il pulsante `button.cronotermostato_piano_terra_applica_fascia_corrente`: verifica nel logbook dei termostati che il preset corretto sia stato inviato.
2. [ ] **Test Scene KNX da Tastiera/Pulsantiera**:
   - Imposta la modalità su `Scene KNX` (oppure spegni lo switch `crono`).
   - Attiva la scena "In Casa": verifica che i termostati vadano in `comfort`.
   - Attiva la scena "Uscita": verifica che i termostati vadano in `away`.
   - Attiva la scena "Notte": verifica che vadano in `economy`.
   - Attiva la scena "Vacanza": verifica che vadano in `building_protection`.
3. [ ] **Test Spegnimento (OFF)**:
   - Imposta la modalità su `Spento (Protezione antigelo)` (oppure spegni lo switch `termoregolazione_automatica`).
   - Verifica che tutti i termostati della zona ricevano immediatamente `building_protection`.
4. [ ] **Verifica Registro di Sistema**:
   - Vai in **Impostazioni** > **Sistema** > **Registro**.
   - Assicurati che non vi siano avvisi o errori relativi a entità mancanti dei vecchi package.
