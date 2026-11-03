# Release 0.2 validation — 2026-11-04 (Australia/Sydney)

- Windows / Python 3.14.3: **43 tests passed**, no failures (8.78 seconds).
- Streamlit AppTest: initial render, empty selection, positive capacity and complete
  matched-scope scenario interaction passed; four dashboard tabs present.
- Browser inspection: running dashboard shows release 0.2, six reporting entities,
  eleven selected disclosures and a latest selected publication of 2026-10-28.
- Offline DuckDB v2 rebuild: 11 demand observations and 14 infrastructure records.
- Accounting tests cover minute/week/month/calendar conversion, leap years, qualifier
  preservation, scope separation, containment cycle rejection, duplicate revisions,
  publication/update cutoff, staleness and rejection of unresolved aggregation.
- Scenario tests cover finite inputs, token split, reversed/mismatched periods,
  planned capacity rejection, revenue bands, elasticity, idle cost and break-even.
- Release tests verify deterministic manifests, real CSV parsing and expected rows.
- Portable HTML checks: 25 evidence cards, mobile viewport, no JavaScript or external
  resources; minute and week original-unit labels preserved. Phone OS-specific file
  viewers have not been tested.
- Dependency check: no broken requirements; package installed as version 0.2.0.
- Monitoring tests: curated HTTPS/port allowlist, content changes, unchanged sources,
  HTTP failures and script noise filtering; measurements are never promoted.

Initial direct-network source check: 10 fingerprints captured, 5 unavailable. These
HTTP failures do not override manual browsing verification. Baselines store normalized
text hashes only; source publication/navigation edits can produce review alerts.

- openai_api_2026: HTTPError: HTTP Error 403: Forbidden
- google_q3_2026: HTTPError: HTTP Error 403: Forbidden
- openai_compute_2026: HTTPError: HTTP Error 403: Forbidden
- anthropic_spacex_2026: URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1081)>
- anthropic_aws_2026: URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1081)>


The CI workflow additionally rebuilds exports, builds the Linux container and checks
that the container loads the evidence. Remote results are recorded below after push.
Docker is not installed on the laptop; container verification relies on remote CI.
No paid cloud deployment or comprehensive real-world fleet/tightness validation has
been performed. Unavailable worldwide telemetry remains an explicit research gap.

Historical Phase 1 validation is preserved in Git (20 passing tests and successful
Linux run 41550663936); it is superseded by this release record.


## Remote release verification

Linux / Python 3.14 CI passed at exact implementation commit
3b2c8980a0b69e71f092c41107b3659087537e67:
https://github.com/MichaelMi7/global-ai-compute-monitor/actions/runs/41721718628

The run passed all 43 tests, offline database rebuild, export regeneration, byte-for-byte
CSV/manifest comparison, Linux Docker image build and in-container evidence-load check.
The tested implementation commit is the v0.2.0 release target. Subsequent completion
notes do not change the tested implementation. Cloud hosting itself is not activated.
