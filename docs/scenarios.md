# Scenario definitions and limits

Every scenario is an explicit user-assumption calculation, separate from the public
measurement ledgers. Zero fleet and throughput defaults avoid presenting an invented
installed base. Other visible slider defaults are assumptions, not observations.

## Effective capacity

C_day = N × inference_share × availability × active_duty × benchmark_tps × 86,400.

Availability and active duty are sequential fractions; do not count the same idle time
twice. Benchmark throughput must match model, precision, context, token split, caching,
quality/latency objectives and serving stack. Physical chips and H100e require distinct
benchmark definitions. Power alone cannot identify this capacity.

## Compute equivalents

Reference tokens = (input_tokens × FLOPs_per_input + output_tokens × FLOPs_per_output)
/ FLOPs_per_reference_token. This is a workload-specific FLOP accounting convention,
not a performance prediction. Memory, bandwidth and service-level constraints can bind
instead. Unknown token split or missing coefficients must not be silently filled.

## Tightness

A point comparison requires equal known workload, geography, reporting window, token
basis and deployment perimeter. Announced or planned capacity is rejected. Demand
reported only as an over-threshold cannot determine point utilization. The dashboard
allows a fully specified hypothetical matched-scope comparison, labeled as such.
No current production ledger pair meets the conditions for an observed global ratio.
A ratio above one means the assumptions cannot all describe completed throughput at
that capacity; it does not measure a queue or unmet demand.

## Revenue and economic demand

Revenue-implied T/day = annual_revenue × token_revenue_share / 365.25 /
(realized_USD_per_million_total_tokens) × 1,000,000. The low-volume endpoint uses the
high price and vice versa. This is a deterministic sensitivity range, not a confidence
interval. List prices, paid/free mix, subscriptions, bundled/cloud services and training
revenue make naive division misleading. Revenue recognition and volume periods must
also match. No company revenue is automatically converted into token evidence.

Counterfactual unconstrained demand Q1 = Q0 × (P1/P0)^(-elasticity). Elasticity is a user
assumption; this ledger does not estimate it. This is neither realized throughput nor
a growth forecast, and it omits quality changes, substitution and rationing.

## Operating economics

Annual processed tokens = C_day × 365.25. Revenue uses an assumed realized blended price.
Allocated fleet = installed × inference_share. Annual system energy = allocated fleet
× [idle_kW + (active_kW-idle_kW) × availability × active_duty] × PUE × 8,766.
This deliberately charges idle power across the allocated fleet, including unavailable
machines; switch-off assumptions would require another model. System power inputs
must consistently include supporting server components before PUE is applied.

Annual depreciation = allocated fleet × all-in capex/accelerator / useful_life_years.
Operating profit = revenue − electricity − other operating cost − depreciation.
Break-even price includes those costs per million processed tokens; it is undefined
when output is zero. Margin is undefined with zero revenue. Utilization sensitivity
rows are hypothetical assumptions, not measured probabilities.

This is pre-tax, unlevered operating analysis. Financing, taxes, model development,
working capital, acquisition costs and residual value are excluded unless explicitly
included in the provided cost assumptions. It is not a valuation, forecast or investment
recommendation. Scenario JSON preserves the inputs, outputs, name and model version.
