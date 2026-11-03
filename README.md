# Global AI Compute Monitor

Independent, reproducible research on AI inference throughput and eventual effective
compute supply. Phase 1 provides an offline public evidence ledger, DuckDB model and
Streamlit dashboard. Five historical disclosures cover Google, Microsoft and Fireworks.
This is a historical research seed, not a current global demand estimate.

## Quick start (PowerShell, from this repository)

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m compute_monitor.model --database data/monitor.duckdb
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Open http://127.0.0.1:8501 . No API key or paid service is required. Stop with Ctrl+C.
Exact dependency versions are locked from the Windows Python 3.14 environment; CI also
checks Linux Python 3.14. For other supported Python versions, install `-e '.[test]'`
using the bounded declarations in pyproject.toml and validate separately. Run from this
checkout: SQL and evidence are repository assets, not packaged wheel resources.

## What works

- Offline, transactional DuckDB rebuild with source URLs, dates, revisions and input hashes.
- Original disclosures separate from arithmetic daily normalization and hypothetical scenarios.
- Interactive historical points, provider filters, scope/coverage, uncertainty and freshness tables.
- CSV export and an explicitly hypothetical capacity calculator.
- Tests for calendar accounting, missing inputs, revision selection, repeatable ingestion,
  prohibited aggregation, scenario arithmetic and Streamlit rendering/interactions.

The dashboard rebuilds a small in-memory database on each run; the CLI writes a local
DuckDB artifact. Never point the CLI at a database containing unrelated tables with the
same names. Production JSON is public evidence; test fixtures stay inside tests/tmp dirs.

## Research and development

Read [methodology](docs/methodology.md), [source review](docs/sources.md),
[data dictionary](docs/data-model.md), [validation](docs/validation.md), and
[Phase 2 roadmap](docs/roadmap.md). No current global sum, demand/capacity ratio or
investment recommendation is justified by this sample. Unknowns remain null.

To add evidence, verify a primary source, add provenance and a versioned observation,
retain reporting qualifiers and period ambiguity, run tests, and commit the ledger.
Never put secrets or employer material in this repository. Local `.env`, credentials,
Streamlit secrets, databases and the virtual environment are ignored. Report factual
corrections through GitHub issues. Code is MIT licensed; underlying third-party source
material remains subject to its own rights and is linked rather than redistributed.

## Portable phone preview

`exports/global-ai-compute-monitor.html` is a single mobile-friendly offline snapshot.
Transfer the actual file to a phone and open it in a browser that permits local HTML.
Some phone attachment previews restrict HTML; use a browser or HTML viewer if needed.
It contains its own styles and charts, with no JavaScript, remote libraries or server.
Source links require internet; the charts and evidence do not. This snapshot does not
update automatically. Rebuild it with:

```powershell
.\.venv\Scripts\python.exe scripts/export_html.py
```
