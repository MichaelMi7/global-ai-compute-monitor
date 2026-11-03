# DuckDB data model, schema v1

`sql/schema.sql` is executable. JSON is the version-controlled source of truth.

| Object | Purpose |
|---|---|
| sources | Stable source ID, URL, title, displayed publication date/status, retrieval date, source type, factual summary |
| observations | Revisioned original numeric evidence, source FK, provider/model, geography and its basis, workload/deployment/scope, token split, frequency, period boundaries/status, as-of chart anchor, qualifier, evidence class, uncertainty, overlap/aggregation controls, notes |
| metadata | Schema/model version and SHA-256 hashes of committed input bytes |
| latest_observations | Highest revision per observation ID |
| daily_demand | Joined provenance and normalized tokens/day; denominator sensitivity and derived classification |

Input/output fields and model are nullable; absence is not zero. Uncertainty bounds
are in original observation units and are null when no interval was disclosed.
Derived calendar sensitivities use tokens/day and do not replace uncertainty bounds.
Qualifiers (`equal`, `over`, `approximately`) apply to the numeric report and derived
rate. Geography basis is stored independently from provider identity.

Future migrations should add independently sourced capacity stock/availability,
benchmark workload definitions, price/revenue observations, model FLOP coefficients,
overlap relationships, assumption versions and scenario-result tables. Those concepts
are intentionally not populated with guessed Phase 1 values. Persist scenarios with
provenance before presenting investment or tightness conclusions.
