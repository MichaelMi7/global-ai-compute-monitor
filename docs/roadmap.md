# Research roadmap and completion status

Release 0.2 delivers the end-to-end tooling requested after Phase 1. An evolving global
research dataset cannot eliminate unknown private activity; open questions are tracked
in `data/research_gaps.json` rather than represented by fabricated values.

| Workstream | Delivered | Evidence still needed |
|---|---|---|
| Primary demand | OpenAI, Google, Microsoft, Fireworks, national China and OpenRouter ledger; dates, qualifiers, periods and source updates | Fresher totals and broader private/on-device coverage; absolute Anthropic and Meta totals |
| Accounting | Separate ledgers/series, containment graph, publication cutoff, explicit disjointness requirement | Reviewed cross-provider/deployment and national-perimeter overlap |
| Workload equivalents | Validated input/output FLOP conversion tool | Population-weighted model mix, context, cache and matched measured coefficients |
| Supply | Versioned power/chip/use/commitment evidence and estimate intervals | Inference allocation, commissioning, availability, workload-matched throughput |
| Economics | Revenue/price response and cost/break-even scenarios with exports | Identified elasticity, realized prices, complete costs and independent backtests |
| Tightness | Matching-scope guard and hypothetical comparisons | Comparable dated demand and available supply per geography/workload |
| Reproducibility | Offline DuckDB, tests, deterministic CSV/hash manifests, portable HTML, CI/container checks | Wider version/platform testing and historical archive agreements |
| Monitoring | Weekly public source availability/content-hash reports; manual review gate | Permitted durable source archives and broader source discovery |

Cloud hosting is optional. Streamlit Community Cloud configuration and a container
recipe are provided; this release runs locally and can be downloaded as offline HTML.
