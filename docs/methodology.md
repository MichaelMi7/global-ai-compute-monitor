# Research methodology v0.1

## Scope and definitions

This is an independent implementation using public prose and company disclosures.
No TokensPerDay code or proprietary data is copied. Phase 1 measures a small sample
of self-reported realized processing, not economic demand or global throughput.
Economic demand includes willingness to pay, price elasticity, substitution, rationing
and unmet workloads. Token counts do not measure those quantities.

Raw tokenization varies by model and modality. Input/prefill and output/decode have
different costs; reasoning, cached tokens, image/audio/video accounting and context
length further change work per token. Unknown input/output splits remain null.
`compute_equivalent` accepts explicit split and workload-specific FLOP costs, divided
by a reference FLOP cost per token. It rejects unknowns; no production compute-equivalent
series is generated from raw aggregate disclosures.

Training is separate from inference. Selected reports appear in inference/product
contexts, but their precise workload accounting is not audited. Workload labels retain
that uncertainty. Fine-tuning, evaluation, reinforcement learning and speculative
execution may be counted differently. These caveats prevent treating the sample as
a mathematically assured inference-only global lower bound.

Installed fleet is a stock. Available capacity depends on workload allocation,
reservations, outage time, interconnect, memory, software and service objectives.
The scenario function multiplies installed accelerators by inference share, availability,
active service duty fraction, benchmark tokens/sec and 86,400. These factors must be
defined without double counting idle time. This is hypothetical throughput for one
workload; it is never an observed token count. No populated supply estimate, tightness
ratio or investment return is asserted. Captive first-party, public-cloud and private-cloud
traffic require separate treatment; mixed reports retain their mixed classification.

## Evidence and normalization

`data/sources.json` records canonical URL, page-displayed original publication date,
retrieval date and a short factual evidence summary. Displayed publication dates are
not independently verified through archives. No full copyrighted pages are redistributed.
`data/observations.json` records original numerical magnitude, qualifier, unit, scope,
frequency, period interpretation, geography, provenance and revision.

Exact period totals divide by inclusive actual calendar days. March 2025 has 31 days;
Microsoft FY2025 Q3 is interpreted as January 1–March 31 (90 days). The March value
is contained in the quarterly value. Midpoints are plotting anchors only. Google monthly
run rates do not identify a completed calendar month: their start/end are null, publication
dates anchor the chart, and daily equivalents divide by 365.25/12. A 28–31 day denominator
sensitivity is displayed separately. It is not a confidence interval. Daily rates retain
the reported rate, with an unknown averaging window.

The `over` qualifier survives normalization: a reported threshold is not an exact
measurement or an upper bound. `equal` means the stated rounded figure, not audited
precision. Statistical interval bounds remain null because none was disclosed.
Calendar sensitivity does not account for reporting error, scope mismatch or missing data.

All production rows are `disclosed`; normalized views are derived arithmetic, not new
observations. Estimates must be tagged `estimated` and kept separate. The only populated
scenario is user-entered, initialized at zero installed fleet and zero throughput. Synthetic
values appear only in tests and are never loaded by the dashboard.

## Accounting controls

No rows are eligible for global aggregation. Cross-provider and partner relationships
have not been reconciled. Provider headquarters do not imply consumption geography;
`global_unspecified` supplies no regional allocation. Two observations from the same
provider may overlap in time; quarterly and monthly disclosures are not additive.
No interpolation, carry-forward, exponential extrapolation or current-day total is shown.
A sample provider count is not a market coverage percentage. Chart changes can reflect
scope/accounting changes as well as actual processing growth.

## Provenance, versioning and freshness

Observation keys are (observation_id, revision). Corrections append revisions in the
committed ledger; the latest view chooses the highest revision. A database rebuild is
transactional and records schema/model versions plus SHA-256 hashes of both input files.
Git commits preserve previous ledgers. Rebuilding replaces curated database tables; use a
dedicated output file, never an unrelated user database. Network access is unnecessary
for rebuilding. Re-verification is manual in Phase 1. Retrieval means checked against
public text on 2026-11-03, not an archived snapshot or automated freshness guarantee.
Publication age, observation age and verification age are distinct. The 90-day stale
flag is a display policy, not a statistically justified cutoff. This historical seed is
not an exhaustive search through November 2026; newer disclosures must be collected.

## TokensPerDay reference review (retrieved 2026-11-03)

Reference URLs: https://tokensperday.com/methodology/ and
https://tokensperday.com/data/ and https://tokensperday.com/ .
Original publication dates are not displayed; the pages show a July 16, 2026 verification
label, which must not be treated as an original publication date or current observation.
The reference separates provider, customer and router ledgers; curates overlaps; converts
reported periods to daily rates; and supplements disclosures with estimates and hardware
checks. Its source set includes company statements, national reports, intermediary
telemetry, research and hardware benchmarks, with different accounting scopes.
This project adopts provenance discipline, while withholding a global sum and aggregate
capacity comparison until compatible scope, period and overlap evidence exists. We do
not import its ledger or accept secondary figures as primary measurements. Country
headquarters and bill-to location cannot establish actual serving or consumption location.

## Remaining limitations

Only three providers and four primary pages are seeded. There is no verified OpenAI,
Anthropic, China national, private fleet, on-device or router series. Unknown model mix,
input/output, caching, multimodal accounting, paid/free split, latency targets and
training allocation preclude compute equivalence and supply-demand comparison. Source
pages can change; content snapshots and redistribution rights need a future archival
policy. Source summaries and hashes of curated inputs are not hashes of original pages.
