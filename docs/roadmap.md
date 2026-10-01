# ContextEngine — Roadmap operativa

Ricostruzione cloud del piano letto nella sessione precedente. Numerazione 0–5.
Alla richiesta «implementa step N», leggere architecture.md, progress.md e questo
documento, riusare il codice esistente e implementare soltanto la fase richiesta.

## Regole comuni

Verificare prerequisiti e stato reale, preservare modifiche e riferimenti dell'utente.
Non riscrivere una fase precedente né introdurre provider sostitutivi senza evidenze.
Usare interfacce pubbliche documentate e versioni effettivamente provate. Se cambiano
confini/API, aggiornare contratti, consumatori, test e architettura nella consegna.
Una prova live non eseguita non è sostituita da mock o test saltati. In assenza di
credenziali completare il lavoro indipendente, registrando esattamente la parte aperta.
Credenziali e contenuti sensibili non entrano in fixture, codice o registro.

Ogni sessione aggiorna progress.md con comandi/esiti, versioni, evidenze, limiti e
passaggio di consegne. Dichiarare completato soltanto se i criteri sono soddisfatti.
Una fase parziale si riprende con lo stesso comando. Commit/push/pubblicazione non
sono requisiti automatici. Non avviare lo step successivo senza incarico.

## Step 0 — Provider e contratti

Fixture Python: pochi domini, import tra moduli, simboli/riferimenti, test, file non
mappato, import non risolto/dinamico. Serena: startup/shutdown, overview, simboli,
definizioni/riferimenti disponibili, edit salvato, cancellazione, freddo/caldo e
stabilità localizzatori. pydeps: JSON reale, mapping modulo/file, esterni, irrisolti,
limiti ed esecuzione riproducibile. Jev: SDK corrente, richiesta tipizzata minima,
probabilità/usage, timeout/errori, accesso già configurato. Contratti normalizzati,
versioni/runtime e lifecycle verificati. Non costruire ancora l'engine o TypeScript.

Completamento: tre prove reali eseguite e documentate, oppure sostituzione motivata
con alternativa verificata. Senza accesso live Jev resta parziale. Risultati vuoti
distinti dagli errori. Fixture/script nel progetto; aggiornare architettura e registro.

Prompt: implementa queste consegne, usando i provider reali sulla fixture. Fissa
versioni compatibili osservate, conserva output normalizzati e comandi, aggiorna
progress.md. Non dichiarare live il mock Jev. Non avviare lo step 1.

## Step 1 — Baseline deterministica

Prerequisiti: ambiente Python e contratti dello step 0; Jev live può restare aperto.
Package installabile, modelli e CLI JSON; domini/NetworkX, ripgrep anche globale,
ranking spiegabile, SQLite, snapshot/sessioni/cache. Implementare index, retrieve,
find, refresh, explain, doctor. Bundle/Delta con provenienza, status/quality, budget,
stop_reason e invalidazioni. Prima baseline sulla fixture e un piccolo repo Python.

Criteri: installazione nuova esegue index/retrieve/find; anchor e file non mappati
recuperabili; edit/cancellazioni invalidano snippet; ID sconosciuti espliciti;
determinismo, budget e deduplicazione verificati. Non integrare ancora Jev o adapter
completi dello step 2. Aggiornare registro e fermarsi.

## Step 2 — Dipendenze e simboli

Prerequisito: step 1 verificato. Adapter pydeps e Serena riusando gli spike; capability
detection, errori/fallback visibili, espansione limitata, overview/firme, riferimenti
su richiesta e test pertinenti. Invalidazione query/lifecycle misurato. Poi fixture
JS/TS e dependency-cruiser con alias/workspace/config effettivi e versione fissata.

Criteri: percorso Python dominio -> file -> simbolo -> riferimento verificabile;
JS/TS stesso modello; esterni/irrisolti espliciti; provider assente non bloccante e
qualità degradata dichiarata. Non dedurre chiamate dagli import. Contract test e
misure rispetto alla baseline. Non avviare lo step 3.

## Step 3 — Jev e frontier iterativa

Prerequisiti: step 2 e accesso Jev live. Judizi Noul indipendenti per candidato,
true/false/null per task, frontier persistita, reopening e nuove evidenze per incerti.
Cache versionata, timeout/errori separati, fallback deterministico, budget cumulativi
e costi riportati. Confronto baseline/Jev e con/senza domini sugli stessi task.

Criteri: cicli, riapertura false, null con nuove evidenze, servizio assente, budget,
più domini e file non mappati; token totali, costo, latenza, falso pruning e regressioni
misurati. Soglie restano configurabili da calibrare. Non presumere vantaggi Jev;
conservare baseline selezionabile. Non avviare lo step 4.

## Step 4 — Due skill e coding

Prerequisito: step 3. workflow/SKILL.md e context-retrieval/SKILL.md collegate,
wrapper sottile, installazione/discovery verificata. Ciclo retrieve -> coding ->
refresh -> find -> verifica mantenendo retrieval_id e gestendo snapshot/Delta.
Due task in copie fixture, uno locale e uno trasversale con approfondimento necessario.

Criteri: agente esegue workflow senza orchestrare manualmente ogni attraversamento;
modifiche visibili e frammenti obsoleti invalidati; comandi realmente eseguibili;
misure token/costo approfondimenti. Non duplicare algoritmo nelle skill. Non step 5.

## Step 5 — Robustezza, benchmark e packaging

Prerequisito: step 4. Refresh su edit/aggiunte/cancellazioni/rinomine/branch/config/
manifest/versioni, query concorrenti, transazioni e shutdown senza orfani. Benchmark
>=30 task Python/JS/TS/misti, taratura separata, tre modalità e con/senza domini.
Packaging, dipendenze fissate, doctor e installazione pulita riproducibile.

Criteri: prove funzionali/freshness passano, risultati confrontati con target senza
abbassarli. Riportare variabilità/limiti e distinguere valutazione completata da v1
pronta. Non pubblicare né avviare nuove fasi implicitamente.
