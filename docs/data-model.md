# DuckDB data model, schema v2

The JSON ledgers are the version-controlled evidence. `sql/schema.sql` defines the
rebuildable analytical database. Version 2 extends the initial demand-only schema.

| Object | Meaning |
|---|---|
| sources | Source ID, canonical HTTPS URL, title, displayed publication date/status, known update date, manual retrieval/review date, type and short factual summary |
| observations | Original token reports, revision, provider, ledger role, accounting series, model/workload/deployment, geography/basis, period/status, as-of anchor, frequency, input/output split, original magnitude/unit/qualifier, evidence class, uncertainty, overlap and notes |
| infrastructure | Separate versioned stock/flow/access/target reports, entity, original unit, metric/status, evidence class, qualifier, source uncertainty, hardware, geography, workload and unknown inference/availability/utilization fractions |
| relationships | Directed containment, possible overlap, scope break or explicitly evidenced disjointness, plus reason and source |
| research_gaps | Entity-specific search result, checked date, relevant source and unresolved limitation; absence in reviewed pages is not proof of absence everywhere |
| metadata | Schema/model version and hashes of all five evidence ledgers |
| latest_observations / latest_infrastructure | Highest revision for each evidence ID |
| normalized_observations | Daily-equivalent arithmetic joined to provenance; retains evidence class and qualifier |
| daily_demand / normalized_estimates | Disclosed and estimated token evidence are separate views |

Production demand rows currently are disclosures; five infrastructure rows are Epoch
research estimates. Unknown model, input/output, inference fraction, availability and
utilization stay null. H100-equivalent compute use is not physical H100 stock.
Uncertainty bounds use each original row's unit. Only the Epoch rows have source-reported
90% intervals. Demand denominator sensitivities use tokens/day and are not intervals.

The v2 rebuild is a transaction: validate inputs, drop only project-owned named views
and tables, recreate and load. Failure rolls back to the prior database. Use a dedicated
file, never a database containing unrelated tables with the same names. This is a
rebuild migration rather than a destructive in-place edit of a source-of-truth database.
Corrections append revisions; Git preserves earlier dataset releases. Relationship
endpoints refer to stable observation IDs. Validator rejects duplicate revisions,
unknown sources/fields, negative/nonfinite magnitudes, invalid intervals and containment
cycles. No production record is approved for a global sum.

The release manifest also hashes schema and model/accounting/scenario code. CSVs have
stable ordering and deterministic bytes. Source fingerprints separately record only
normalized text hashes; they are not archived original pages or evidence verification.
