# ContextEngine — Architettura v1

Direzione approvata; implementazione limitata allo step 0. Questa copia cloud è
ricostruita dal piano letto nella sessione Windows: non è una copia byte per byte
dei file Windows, che non erano accessibili dal cloud. Le decisioni conservate sono
elencate qui; risultati e variazioni osservate si trovano in progress.md.

## Obiettivo e confini

Fornire a un agente il contesto necessario per implementare un task, riducendo
letture, token e costo senza perdere evidenze indispensabili. Due skill collegate:
workflow (TaskSpec, coding, verifica) e context-retrieval (invocazione del package).
Il retrieval resta in Python con API tipizzate e CLI JSON; nessun nostro server MCP
o plugin è richiesto. MCP è il protocollo interno supportato per Serena.

L'engine legge il repository e scrive configurazione/cache proprie. Non sviluppare
parser, resolver o language server proprietari. SCIP, Joern, vector database,
generazione automatica estesa dei domini e watcher continuo restano fuori dalla v1.

## Provider e tre livelli

| Livello | Provider | Regole |
| --- | --- | --- |
| Domini | Catalogo compatibile Backstage Domain/subdomainOf + NetworkX | Pochi domini configurati; glob/alias sono un'estensione nostra; più domini per file; parent aciclici; relazioni trasversali anche cicliche |
| File/moduli | pydeps per Python; dependency-cruiser per JS/TS nello step 2 | Conservare moduli, percorsi solo se risolti, esterni/import non risolti espliciti; nessun call graph dedotto |
| Simboli/riferimenti | Serena tramite MCP stdio e LSP | Query su richiesta; overview/firme prima dei corpi; capability discovery; riferimenti non equivalgono a chiamate |

Ricerca globale con ripgrep anche fuori dai domini selezionati. SQLite conserva
snapshot, sessioni, frontier, cache e trace. La baseline deterministica precede Jev.

## Dati e contratti

TaskSpec: obiettivo, criteri di accettazione, vincoli, anchor. Domain: ID, descrizione,
parent, alias, glob, provenienza. File: repo, percorso relativo, linguaggio, hash,
domini. Symbol: localizzatore del provider, nome qualificato, file, intervallo,
snapshot. Edge: tipo, origine, destinazione, provider, qualità, snapshot. Evidence:
fonte, posizione, hash, acquisizione. RetrievalSession: task, snapshot, frontier,
visite, decisioni, budget, trace. Decision: true/false/null, probabilità se presente,
evidenze, motivo. Relazioni: subdomain_of, belongs_to, imports, defines, references.

Le righe sono coordinate dello snapshot, non ID persistenti. Lo step 0 verifica
se il provider espone ID o solo localizzatori; nessun ID stabile globale è presunto.

API del prodotto, da implementare nello step 1:

```python
index_repo(repo_path, *, mode='auto') -> IndexReport
retrieve_task_context(repo_path, task, *, budget) -> ContextBundle
find_context(retrieval_id, need, *, budget) -> ContextDelta
refresh_index(repo_path, *, changed_paths=None) -> IndexReport
explain_retrieval(retrieval_id) -> RetrievalTrace
```

CLI: index, retrieve, find, refresh, explain, doctor. Input file/stdin, JSON stdout,
diagnostica stderr. retrieval_id opaco nello store del repo aperto; ID sconosciuto
o di altro repo genera errore, senza scansione del filesystem.

Bundle/Delta includono schema_version, snapshot, frammenti verificabili, relazioni,
test/config, irrisolti, stop_reason e metriche. Delta: aggiunte, aggiornamenti,
invalidazioni, senza ripetere tutto. status=complete|partial e quality=normal|degraded
sono dimensioni separate. Complete riguarda la richiesta, non tutto il repository.

Per gli spike il contratto ProbeResult separa ok, blocked, error, unsupported.
ok con data=[] rappresenta un risultato vuoto; un errore richiede error e non data.
Non è ancora il modello pubblico del retrieval. DependencySnapshot normalizza solo
percorsi realmente riportati e presenti. Noul restituisce probability_yes, model,
usage e request_id se forniti; dati assenti restano null, non stimati.

## Retrieval e Jev

Snapshot aggiornato -> candidati da anchor/testo/catalogo -> ranking/classificazione
-> frontier ed espansione limitata -> overview/firme -> evidenze/corpi mirati -> pack.
Deduplicare visite e intervalli; arrestare per bisogno soddisfatto, frontier esaurita,
nessuna nuova evidenza o budget. Gli errori operativi restano separati da null.

Jev effettua domande Noul indipendenti per candidato, raggruppabili sullo stesso
stato. Python applica soglie e controlla il ciclo. true: esplora; false: sospendi;
null: evidenze insufficienti. Pruning reversibile con anchor, riferimenti o nuove
evidenze. Parent false non esclude discendenti trovati globalmente. Le decisioni
appartengono al task, non al catalogo permanente.

Ipotesi da calibrare: true p>=0.75, false p<=0.15; massimo due rivalutazioni;
8.000 token iniziali, 3.000 per approfondimento, quattro round, due hop. Limiti anche
per tempo, candidati, chiamate e costo cumulativo. Nessuna probabilità inventata nel
ranking deterministico. Anchor necessaria fuori budget produce partial esplicito.

## Lifecycle, storage e freshness

Serena: processo locale avviato pigramente, riusato nell'invocazione, timeout e chiusura
pulita. Nessun daemon persistente finché il costo CLI non lo giustifica. Buffer non
salvati fuori scope. Lo step 0 usa una copia usa e getta della fixture, mai l'originale.

Config in .context-engine/config.yaml e domains.yaml; generato in cache/ ignorata
da Git. Snapshot di contenuti locali, config, provider e commit se presente: HEAD
da solo non basta. Senza Git usare manifest hash. changed_paths è un suggerimento.
Invalidare su edit, aggiunta, cancellazione, rinomina, branch, manifest, alias,
config e versione provider. Ricostruzione completa corretta è accettabile.

Cache Jev: task/bisogno, candidato, hash evidenze, modello, versione domande. Rivalidare
hash prima di consegnare snippet. Non mescolare snapshot concorrenti incompatibili.

## Validazione e fasi

Step 0: fixture e prove provider; 1: baseline deterministica; 2: dipendenze e Serena,
poi JS/TS; 3: Jev/frontier e confronti; 4: due skill e due task completi; 5: robustezza,
packaging e benchmark. Nessuna fase successiva avviata implicitamente.

Benchmark finale >=30 task Python, JS/TS e misti, evidenze indispensabili/utili annotate,
taratura separata da valutazione. Confrontare testo, grafi deterministici, grafi+Jev
e con/senza domini. Misurare recall, precisione, falso pruning, token complessivi,
costo, latenza freddo/caldo, successo con stesso agente e budget comparabili.

Obiettivi non dimostrati: recall >=95%, nessuna regressione materiale nel successo,
riduzione >=30% token complessivi. Valutazione completata non equivale a v1 pronta.

## Fonti ufficiali consultate

- https://github.com/oraios/serena e documentazione collegata
- https://pydeps.readthedocs.io/en/latest/
- https://docs.typesafe.ai/sdk/python/usage
- https://github.com/typesafe-ai/typesafe-sdk-python
- https://backstage.io/docs/features/software-catalog/descriptor-format/
- https://networkx.org/documentation/stable/reference/classes/digraph.html

Versioni, capacità realmente osservate e limiti: progress.md e step0-results.md.

## Correzioni confermate dallo step 0

Serena 1.7.0/Jedi restituisce localizzatori `relative_path` + `name_path`, non un
ID opaco stabile. Sono rimasti uguali dopo un edit che sposta il simbolo di una riga;
range e hash cambiano. Non estendere questa stabilità a rinomine o overload.
`find_symbol` e l'overview includono anche nomi importati: l'adapter deve mantenere
il tipo di acquisizione e distinguere candidati da definizioni confermate.
`find_declaration` accetta un file e regex di occorrenza con un gruppo, opzionalmente
un simbolo contenitore; la futura capability `definition` va esposta con questo
input o con una traduzione esplicitamente verificata, non una firma LSP inventata.
`find_referencing_symbols` restituisce gruppi per file e kind, non una lista piatta.

Serena può restituire un errore operativo come testo "Error executing tool..."
senza `isError=true`: verificare entrambi, senza confondere [] con un errore.
L'edit e la cancellazione salvati sono stati osservati nella sessione riusata.
Le importazioni rimaste dopo cancellazione sono candidati nel file importatore,
non prove che la vecchia definizione sia ancora disponibile.

Runtime verificato Linux CPython 3.12.14. Nessuna compatibilità Windows è dichiarata.
Jev: contratto SDK verificato offline; comportamento del modello, uso e costo live
non misurati. Lo step 0 resta parziale e gli step 3–4 restano bloccati dall'accesso live.
