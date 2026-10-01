# ContextEngine — Risultati dello step 0

Data: 2026-10-01. Stato **parziale**, esclusivamente per la prova live Jev mancante.
I numeri seguenti sono misure sulla piccola fixture, non benchmark della futura v1.

## Riproduzione

Seguire README.md. Provider/script in `spikes/`, fixture in `tests/fixtures/python_repo/`.
`evidence/step0/main/` conserva la prova nel primo ambiente; `clean/` la ripetizione
dopo installazione nuova da lock transitivo con hash. Gli assessment richiedono tutti
i percorsi locali normali, negativi, edit/delete e shutdown, senza sostituire Jev.

## pydeps

Comando effettivo: `python -m pydeps <package o maintenance.py> --show-deps
--no-output --noshow --nodot --no-config --include-missing --max-bacon 2`.
Il cwd e PYTHONPATH sono la fixture. Si analizza l'ambiente Python installato,
inclusa PyYAML esterna. Non viene eseguita l'applicazione.

Il JSON è un oggetto indicizzato da nome modulo; ogni elemento può contenere path,
imports, imported_by, name, bacon. La normalizzazione unisce entrambe le direzioni
deduplicando archi imports; solo path esistenti dentro la fixture diventano file
locali. Path esterni esistenti conservano resolution=external senza inventare un file
locale. Path assente/non valido resta unresolved. Nessun resolver proprietario.

13 nodi/20 archi sul package, 6/8 sul file non mappato. Sono verificati api.session ->
auth.tokens, api.session -> storage.users, auth.tokens -> storage.users. YAML è un
esterno risolto; contextengine_missing_fixture_provider è unresolved. Il provider
riporta anche importlib.import_module senza percorso: non va classificato come un
nuovo file o call target. Il nome passato a load_plugin può essere qualsiasi stringa
runtime e non è recuperabile da questo grafo.

L'analisi ha hop massimi 2 ed esclude la stdlib per default: non dichiara copertura
esaustiva di tutti gli import. Il file non mappato è analizzato separatamente. Target
inesistente: exit 1 con errore esplicito. No Graphviz, SVG o processi grafici.

## Serena/Jedi

Protocollo: MCP stdio tramite SDK ufficiale; nessuna importazione di classi interne
Serena per eseguire le query. Release 1.7.0 e language server python_jedi, configurato
nella copia temporanea della fixture. Tool schema scoperto e conservato in JSON.
Dashboard, GUI e memorie disabilitati. SERENA_HOME diretto a un path temporaneo.

| Misura | Ambiente principale | Installazione pulita |
| --- | ---: | ---: |
| Startup fino a initialize/list_tools | 3313,1 ms | 5445,0 ms |
| Prima overview | 669,5 ms | 1634,5 ms |
| Overview riusata | 107,3 ms | 95,0 ms |
| Riferimenti | 2201,5 ms | 2206,8 ms |
| pydeps package | 1867,3 ms | 2222,2 ms |

Due osservazioni singole con server/home nuovi, cache OS/rete non controllate:
non bastano a stimare una distribuzione o decidere un daemon. Per ora avvio pigro e
riuso intra-processo sono la strategia minima, senza servizio persistente.

Overview può includere simboli importati (User, sha256). find_symbol(include_body)
restituisce oggetti con name_path, kind, relative_path, body_location e body se
disponibile. Le righe osservate sono 0-based, estremo finale inclusivo.
Il localizzatore (file, name_path) resta invariato mentre un commento aggiunto sposta
la funzione da righe 5–7 a 6–8 e l'edit del body viene visto nella query successiva.
Non è un ID globale; invalidare la cache su hash/snapshot.

find_declaration su un'occorrerenza in api/session.py risolve auth/tokens.py.
Input reale: relative_path, regex con un gruppo per l'occorrenza, include_body;
contenitore opzionale. find_referencing_symbols restituisce gruppi file/kind con
snippet di riferimento: coperti api/session.py, tokens.py, maintenance.py e test.
Queste relazioni non dimostrano chiamate né copertura semantica esaustiva.

Query senza match restituisce []; file inesistente produce testo di errore anche
quando il flag MCP isError è false. Il wrapper li distingue. Dopo la cancellazione
di tokens.py, l'overview fallisce e la vecchia definizione non compare nella ricerca;
rimangono import alias negli altri tre file, che sono candidati, non definizioni.

Tre processi figli sono tracciati nei run finali con il PID compatibile col mount
/proc; dopo chiusura client stdio nessun PID rimane. Il precedente tentativo di
misura con os.getpid()/psutil era incompatibile col namespace e non è usato come
evidenza. Windows, processi lunghi, overload e rinomine non sono verificati.

## Jev / TypeSafe SDK

SDK 0.7.2 reale installato. Noul/NoulAnswer/SystemOneResponse verificano una richiesta
tipizzata e una risposta sintetica tramite httpx2.MockTransport. La normalizzazione
conserva probabilità yes, modello, usage e request_id opzionali; valida [0,1] finito.
Uso/costo assente rimane null. Timeout e HTTP 401 producono errori SDK distinti;
retry=0 è verificato con una sola chiamata al trasporto simulato.

**Nessuna inferenza Jev live è stata eseguita.** Non è configurata TYPESAFE_API_KEY.
Il comando live esplicito si arresta con credentials_missing prima di inviare la
richiesta. Il modello effettivo, probabilità live, token reali, costo e latenza
restano non misurati. Non sono state cercate credenziali in altri file o assunto
valido un vecchio tunnel. Il mock è prova dell'interfaccia SDK, non del provider.

## Test e prontezza

10 test di contratto passati in entrambi gli ambienti. I test includono due casi
della fixture eseguiti in sottoprocesso. 23 controlli sulle evidenze reali passano
in entrambi i report: step0_status=partial, jev_live_verified=false.

Sono utilizzabili per lo step 1: runtime/lock, fixture/etichette, distinzione
errori-vuoti, mapping pydeps e localizzatori/hash, discovery/lifecycle Serena.
Il motore pubblico, ranking, persistenza, CLI prodotto e skill non esistono ancora.
Lo step 1 non è stato avviato.
