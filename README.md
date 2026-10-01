# ContextEngine — Step 0

Provider validation for a Python context retrieval engine. This deliverable includes
the fixture, reproducible experiments, normalized contracts and measured evidence.
It does not implement the retrieval engine or the two planned skills yet.

**Status: partial.** Serena and pydeps are verified on Linux/Python 3.12.14.
The TypeSafe SDK is installed and its typed responses/error behavior are tested;
live Jev is still unverified because credentials are not configured.

## Reproduce

```bash
uv venv --python 3.12.14 .venv
uv pip install --python .venv/bin/python --require-hashes -r spikes/requirements.lock
.venv/bin/python -m unittest discover -s tests -p 'test_contracts.py' -v
.venv/bin/python -m spikes.run all
.venv/bin/python -m spikes.check_report spikes/output/all-report.json
```

Windows uses `.venv\Scripts\python.exe`; Windows provider compatibility has not
been verified. The lock records the Linux resolution. No Graphviz is required for
these JSON-only pydeps probes. Serena's stdio process owns a Jedi language server
and operates on a temporary copy of the fixture. Global Serena data is redirected
to that copy's temporary directory.

The default run sends no Jev request. To make **one** live request with an already
authorized environment configuration, use:

```bash
# Set TYPESAFE_API_KEY through your existing secret configuration.
# TYPESAFE_BASE_URL and TYPESAFE_DEFAULT_MODEL are optional SDK settings.
.venv/bin/python -m spikes.run jev --live-jev
```

No credential file is read automatically. Custom endpoints must implement the
TypeSafe API; the SDK's key validation still applies. A credential-free Kev endpoint
has not been tested in this step and is not silently treated as authenticated Jev.
Retries are disabled and the live request timeout is ten seconds. No secrets, endpoint
URLs or service exception bodies are written to reports.

Exit codes: 0 means all requested checks passed; 1 means an unexpected error/check
failure; 2 means a requested provider remains blocked/unsupported. Expected negative
probes (invalid target/missing file/deleted file) remain visible as errors in JSON.
Thus the all-provider run correctly exits 2 when Jev credentials are missing.

## Contents and continuity

- `tests/fixtures/python_repo/`: two configured domains, package imports, refresh
  token symbols, references/tests, unmapped file, real external dependency, unresolved
  import and dynamic import.
- `spikes/`: real provider probes, normalizers, evidence assessment and pinned lock.
- `evidence/step0/`: retained raw/normalized outputs, environment and assessments.
- `docs/`: architecture, roadmap, progress and detailed observed limits.

The original Windows workspace was disconnected before a verified delivery. This
cloud project reconstructs the planning documents from the contents already read
in the conversation. It does not claim to modify or copy the inaccessible Windows
workspace. Resume future work by extracting the whole project archive, reading the
three documents and continuing the existing files. Do not automatically start step 1.
