# ContextEngine — Stato e passaggio di consegne

Ultimo aggiornamento: 2026-10-01. Questa copia cloud conserva le decisioni del piano
letto nella sessione Windows e registra il lavoro effettivamente verificato qui.
I file originali Windows non sono stati trasferiti né modificati dal cloud.

## Stato corrente

**Step 0 parziale: manca soltanto la prova live Jev.** Fixture, contratti degli spike,
Serena e pydeps sono implementati e verificati. Il TypeSafe SDK è installato; richiesta
tipizzata, risposta, usage e timeout/HTTP error sono verificati su trasporto simulato.
Questi test non dimostrano funzionamento, accuratezza, latenza o costo di Jev live.

| Step | Stato | Evidenze | Prossima azione |
| --- | --- | --- | --- |
| 0 — Provider e contratti | Parziale | Serena/pydeps reali, 10 test, installazione pulita da lock | Una richiesta Jev live con accesso già configurato |
| 1 — Baseline deterministica | Non iniziato | Prerequisiti indipendenti disponibili | Package/CLI/ripgrep/NetworkX/SQLite su incarico esplicito |
| 2 — Dipendenze e simboli | Non iniziato | Spike riusabili, nessun adapter engine | Dopo step 1 |
| 3 — Jev e frontier | Non iniziato | Nessun confronto o classifier engine | Dopo step 2 e prova Jev live |
| 4 — Due skill | Non iniziato | Nessuna skill creata | Dopo step 3 |
| 5 — Robustezza/benchmark | Non iniziato | Nessuna valutazione v1 | Dopo step 4 |

Prontezza v1: non valutata. Nessun engine completo, TypeScript, skill, commit, push
o pubblicazione è stato avviato.

## Ambiente e versioni verificate

Linux x86_64, CPython **3.12.14**. Dipendenze dirette: pydeps **3.0.8**,
serena-agent **1.7.0**, MCP SDK **1.28.1**, jedi-language-server **0.47.0**,
typesafe-sdk **0.7.2**. Jedi **0.20.0**. Lock transitivo con hash in
`spikes/requirements.lock`, input in `spikes/requirements.in`.

Un primo tentativo d'installazione dalla branch main Serena ha risolto la versione
dev 2.0.0: è stata sostituita con la release 1.7.0 prima delle prove consegnate.
L'installazione pulita dal lock contiene soltanto la risoluzione stabile verificata.
Windows e Python 3.13/3.14 non sono stati validati.

## Comandi ed esiti effettivi

| Comando | Esito |
| --- | --- |
| `uv pip compile spikes/requirements.in -o spikes/requirements.lock --generate-hashes` | Lock risolto |
| `uv venv .tools/clean-venv --python 3.12` e installazione `--require-hashes -r spikes/requirements.lock` | Installazione nuova riuscita |
| `.venv/bin/python -m unittest discover -s tests -p 'test_contracts.py' -v` | 10 test passati, inclusi 2 test fixture eseguiti nel sottoprocesso |
| Stesso comando con `.tools/clean-venv/bin/python` | 10 test passati nell'ambiente pulito |
| `.venv/bin/python -m spikes.run all --live-jev` | Exit 2 atteso: provider locali passano, Jev credentials_missing |
| Stessa prova nell'ambiente pulito con `--output spikes/output-clean` | Stesso risultato; shutdown senza figli rimasti |
| `python -m spikes.check_report <all-report.json>` in entrambi gli ambienti | 23 controlli locali true; step0 partial; Jev non verificato |

Rapporti reali/raw/normalizzati e assessment conservati in `evidence/step0/`.
Il run pulito e quello principale sono distinti; nessuna media o stima prestazionale
viene presentata come benchmark. Dettagli e limiti in `docs/step0-results.md`.

## Risultati confermati

- pydeps: 13 nodi/20 archi sul package, 6/8 sul file non mappato. I tre import
  indispensabili sono presenti; YAML esterno è distinto dal modulo mancante senza
  percorso. Target inesistente genera exit 1, non un grafo vuoto. Import dinamici non
  risolti dal provider non vengono inventati. Nessun Graphviz necessario per JSON.
- Serena/Jedi: startup, overview fredda/calda, ricerca, riferimenti inclusi file non
  mappato e test, definizione da occorrenza, [] per query senza risultato, errori per
  file inesistente/cancellato, edit osservato immediatamente dalla query successiva.
  Dopo cancellazione la vecchia definizione non compare; restano nomi importati.
- Localizzatore file/name_path invariato dopo inserimento di una riga; coordinate
  0-based e hash cambiano. Nessun ID persistente inventato.
- SDK TypeSafe reale: Noul tipizzato, validazione probabilità, usage, timeout distinto
  da HTTP 401, retry disabilitato. Trasporto simulato esplicitamente dichiarato.
- Lifecycle: tre processi figli tracciati per ogni run finale; zero PID rimasti.

## Decisioni consolidate e registro

Conservate dal piano: due skill collegate, engine Python/CLI JSON; domini configurati
compatibili Backstage/NetworkX; pydeps/dependency-cruiser/Serena, ripgrep/SQLite;
baseline prima di Jev; decisioni true/false/null per task e pruning reversibile;
Python prima di JS/TS. Soglie, budget e obiettivi 95% recall/30% token restano ipotesi.

**D-001 — 2026-10-01: contesto tra sessioni.** I tre documenti viaggiano insieme al
codice; una chat nuova non trasferisce automaticamente file da un altro ambiente.

**D-002 — 2026-10-01: prove reali.** Una fase non è completata con mock/test saltati;
se manca un servizio consegnare il lavoro indipendente e registrare lo stato parziale.

**D-003 — 2026-10-01: continuazione cloud.** Il workspace Windows si è disconnesso
durante la scrittura e non c'è un salvataggio verificato recuperabile. I documenti
cloud sono ricostruiti dai contenuti già letti, esplicitando la provenienza. L'archivio
completo è il nuovo passaggio di consegne; non presumere sincronizzazione con Windows.

**D-004 — 2026-10-01: capacità Serena.** Usare MCP stdio pubblico e capability
discovery. Risultati di ricerca sono candidati e possono essere import alias.
Definition è la capacità find_declaration(file, regex con un gruppo, contenitore
opzionale). Riferimenti raggruppati per file/kind; non call graph. Controllare anche
errori testuali perché isError può essere false. Dettagli in architecture.md.

**D-005 — 2026-10-01: runtime/lifecycle.** Runtime verificato 3.12.14, server pigro
riusato nell'invocazione e chiuso con il client stdio. Nessun daemon persistente.
Il cloud ha namespace PID con /proc dell'host: per verificare i processi usare il
PID di /proc/self, non assumere che os.getpid() coincida col PID nel mount /proc.
La prima misura shutdown basata sull'assunzione sbagliata è superata dalle due
misure finali corrette. Nessun processo Serena/Jedi residuo è stato trovato.

## Registro delle sessioni

2026-10-01 — Pianificazione precedente: architettura e roadmap 0–5 approvate;
implementazione non iniziata; nessuna integrazione live misurata allora.

2026-10-01 — Tentativo Windows: lettura dei documenti e ricerca delle interfacce;
download bloccati dal sandbox e workspace disconnesso prima della verifica di scrittura.
Non è stato dichiarato completato alcun componente.

2026-10-01 — Step 0 nel cloud: fixture, normalizzatori, script, lock con hash,
test e assessment implementati. Provider locali provati in due ambienti; test SDK
offline separati da live. Stato parziale per mancanza credenziale Jev.

## Prossimo lavoro

Per riprendere step 0, estrarre l'archivio e configurare l'accesso Jev già autorizzato
nel runtime; eseguire `python -m spikes.run all --live-jev` e `spikes.check_report`,
conservare modello/usage effettivi e aggiornare il registro. Non cercare credenziali
in file non pertinenti. Nessun endpoint storico è stato assunto ancora valido.

Step 1 può partire con incarico esplicito, usando questi contratti/fixture; il blocco
Jev resta visibile e non è prerequisito per la baseline deterministica. I modelli
del prodotto e la CLI pubblica sono ancora da implementare, non sono gli spike.

Questioni aperte: accuracy/costo/latency Jev, multi-linguaggio/JS alias, scala Serena,
simboli omonimi/overload/rinomine, concurrency/freshness, benchmark e taratura.
