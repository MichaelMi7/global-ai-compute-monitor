# Phase 1 validation record

Host: MMI Windows laptop. Validation date: 2026-11-03.
Python 3.14.3; Git 2.26.0.windows.1; isolated `.venv` environment.
DuckDB 1.5.6, Pandas 3.1.0, Plotly 6.9.0, Streamlit 1.66.1,
pytest 9.2.0. Full dependency pins: `requirements-lock.txt`.

- `python -m pytest -q`: **20 passed**, no failures (5.65 seconds).
- Streamlit AppTest executed the application and empty-provider interaction without exceptions.
- `python -m pip check`: no broken requirements found.
- CLI rebuilt `data/monitor.duckdb` from committed evidence, producing five normalized
  disclosures covering three providers.
- Repeatable rebuild and source/input hashes tested; observation revisions tested.
- Calendar day/leap-year arithmetic, monthly denominator sensitivity, unknown units,
  missing periods, nonfinite/negative reports and invalid capacity inputs tested.
- Estimated records excluded from disclosed view; unreviewed aggregation rejected.
- Unknown input/output split rejected by compute-equivalence calculation.
- Local server `http://127.0.0.1:8501/`: HTTP 200.
- Local health `http://127.0.0.1:8501/_stcore/health`: HTTP 200, `ok`.
- `git diff --check`: passed.
- Pattern scan of intended code/data/docs/tests found no credential-shaped strings.
  This is a basic scan, not a guarantee of comprehensive secret detection.

The server binds only to localhost; logs/PID are under ignored `logs/`.
To stop this session's server, inspect `logs/streamlit.pid` and confirm the process
before stopping it. To restart, use the README command.

Dependency lock captured on Windows Python 3.14; Linux CI is configured but its result
must be checked after publication. No browser screenshot or full manual visual review
was performed; dashboard execution was verified with Streamlit AppTest and HTTP checks.
Public source figures were manually checked against the cited primary pages; they
remain unaudited company disclosures. No current global demand/supply claim was tested.

## Remote verification

GitHub Actions on Ubuntu / Python 3.14 completed successfully for implementation
commit d159804 (20 tests passed, dependency installation and database rebuild passed):
https://github.com/MichaelMi7/global-ai-compute-monitor/actions/runs/41550663936

Published repository: https://github.com/MichaelMi7/global-ai-compute-monitor
