# Global AI Compute Monitor

Independent, reproducible public research on AI inference throughput, compute evidence
and infrastructure economics. Release **0.2.0** includes 11 demand observations across
six reporting entities, 14 infrastructure records and 15 source pages. Evidence was
reviewed on November 3–4, 2026. This is selected coverage, not a current global total.

## Run locally (PowerShell)

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m compute_monitor.model --database data/monitor.duckdb
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Open http://127.0.0.1:8501 . No paid service or API credentials are needed. Stop with
Ctrl+C. Dependencies are pinned and tested on Python 3.14; the broader declared Python
range is not fully matrix-tested. Run from a source checkout: data and SQL remain
repository assets rather than wheel resources.

## Dashboard

- **Demand evidence:** historical points by accounting series, provider/national/router
  separation, publication-eligible cutoff, original units, qualifiers and CSV export.
- **Infrastructure:** source-reported use, estimates, power, additions, announced access
  and targets. Physical chips, H100-equivalents and power are never silently combined.
- **Scenario lab:** explicit capacity assumptions, workload FLOP equivalents, matched-scope
  demand/capacity, revenue-implied throughput, price elasticity and operating economics.
  Download inputs and outputs as JSON. No assumed values enter the evidence ledger.
- **Research quality:** source register, freshness, overlap relationships, search outcomes
  and reproducibility hashes. Unknowns remain unknown.

No measured global inference supply or defensible global tightness ratio is asserted.
Economic demand, realized raw tokens, compute equivalents and investment returns are
different quantities. Company reports are unaudited; source wording and unknown scope
are preserved. More public disclosures do not solve missing private telemetry.

## Portable phone preview

Download the HTML asset from the [v0.2.0 release](https://github.com/MichaelMi7/global-ai-compute-monitor/releases/tag/v0.2.0).
Open the downloaded file in a browser or HTML viewer; phone attachment previews may
restrict HTML. `exports/global-ai-compute-monitor.html` is self-contained: no Python,
JavaScript, server or external libraries. Source links require internet; the evidence
and charts work offline. It is a dated snapshot, not an automatically refreshed meter.

```powershell
.\.venv\Scripts\python.exe scripts/export_html.py
.\.venv\Scripts\python.exe -m compute_monitor.release
```

The second command writes CSVs and a deterministic input/code/export hash manifest.

## Public source monitoring

```powershell
.\.venv\Scripts\python.exe -m compute_monitor.monitor
```

The monitor checks only registered HTTPS domains, limits response size and timeouts,
and compares normalized text fingerprints against `data/source_fingerprints.json`.
Changes require human review. Navigation edits can cause false change signals; HTTP
blocks/timeouts are reported as unavailable. It never extracts new measurements,
updates verification dates or bypasses access controls. The weekly GitHub workflow
uploads a review report as an Actions artifact. Scheduled reports do not update the UI
until a researcher reviews and commits new evidence. No email is sent.

## Deployment options

The root `requirements.txt` installs locked dependencies and this package for Streamlit
Community Cloud. Select `main`, `app.py`, Python 3.14. No secrets are required. Cloud
account connection/deployment remains a separate operational action.

A container recipe is included:

```powershell
docker build -t compute-monitor .
docker run --rm -p 127.0.0.1:8501:8501 compute-monitor
```

The app uses a small in-memory DuckDB per run. For durable research data, edit and
version the JSON ledger; do not rely on container/cloud local database persistence.

## Research and contribution

Read [methodology](docs/methodology.md), [source review](docs/sources.md),
[data model](docs/data-model.md), [scenario definitions](docs/scenarios.md),
[validation](docs/validation.md) and [release assessment](docs/phase2-assessment.md).
The [research roadmap](docs/roadmap.md) distinguishes completed tooling from open data
questions. Original Phase 1 execution history remains in Git.

Add primary evidence with dates, scope, units, qualifiers and provenance. Append a
revision for a factual correction; never overwrite a historical revision. Review
relationships and source-page changes, rebuild, test, regenerate exports and commit.
No synthetic fixtures belong in production ledgers. Use a dedicated database file:
CLI rebuild replaces the project's named tables transactionally.

Do not commit secrets, employer material, `.env`, databases or virtual environments.
Code is MIT licensed. Third-party source material keeps its own rights. Epoch AI
estimates are attributed to Josh You / Epoch AI under its stated CC BY terms; they
are labeled estimates and not reclassified as observed physical hardware.
