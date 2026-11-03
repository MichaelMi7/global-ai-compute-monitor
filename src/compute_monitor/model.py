from __future__ import annotations
import argparse
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[2]

def normalize(row):
    """Derived daily average/run rate; never reclassified as a raw observation."""
    value = row["reported_value"]
    if not math.isfinite(value) or value < 0:
        raise ValueError("Reported values must be finite and nonnegative")
    unit = row["unit"]
    if unit == "tokens_per_day":
        divisor, basis = 1.0, "reported daily rate; averaging window unspecified"
        low = high = value
    elif unit == "tokens_per_month":
        divisor, basis = 365.25 / 12, "standard month (365.25/12); actual month unspecified"
        low, high = value / 31, value / 28
    elif unit == "tokens_in_period":
        if not row["period_start"] or not row["period_end"]:
            raise ValueError("Period total requires explicit boundaries")
        divisor = (date.fromisoformat(row["period_end"]) - date.fromisoformat(row["period_start"])).days + 1
        if divisor <= 0:
            raise ValueError("Invalid reporting period")
        basis = "inclusive calendar-day average"
        low = high = value / divisor
    else:
        raise ValueError(f"Unsupported unit: {unit}")
    return {"tokens_per_day": value / divisor, "normalization_days": divisor,
            "normalization_basis": basis, "calendar_sensitivity_lower": low,
            "calendar_sensitivity_upper": high,
            "measurement_upper": None, "derived_class": "normalized_disclosure"}

def effective_capacity(installed, inference_fraction, available_fraction, utilization, tok_per_second):
    """Hypothetical scenario for a fixed benchmark workload, not observed supply."""
    vals = [installed, inference_fraction, available_fraction, utilization, tok_per_second]
    if not all(math.isfinite(x) and x >= 0 for x in vals):
        raise ValueError("Scenario inputs must be finite and nonnegative")
    if any(x > 1 for x in vals[1:4]):
        raise ValueError("Fractions must be in [0,1]")
    return installed * inference_fraction * available_fraction * utilization * tok_per_second * 86400

def compute_equivalent(input_tokens, output_tokens, input_flops, output_flops, reference_flops):
    """Workload-specific FLOP equivalent; unknown token split must remain unknown."""
    vals = [input_tokens, output_tokens, input_flops, output_flops, reference_flops]
    if any(x is None or not math.isfinite(x) or x < 0 for x in vals) or reference_flops == 0:
        raise ValueError("Known nonnegative split and costs, positive reference required")
    return (input_tokens * input_flops + output_tokens * output_flops) / reference_flops

def build_database(path=":memory:", data_dir=None):
    data_dir = Path(data_dir or ROOT / "data")
    source_bytes = (data_dir / "sources.json").read_bytes()
    obs_bytes = (data_dir / "observations.json").read_bytes()
    sources, observations = json.loads(source_bytes), json.loads(obs_bytes)
    # Validate before opening/replacing any database tables.
    source_ids = {s["source_id"] for s in sources}
    if len(source_ids) != len(sources):
        raise ValueError("Duplicate source IDs")
    for row in observations:
        normalize(row)
        if row["source_id"] not in source_ids:
            raise ValueError("Unknown source")
        if row["aggregation_eligible"]:
            raise ValueError("Phase 1 does not permit unreviewed aggregation")
    con = duckdb.connect(str(path))
    try:
        con.execute("BEGIN")
        # Rebuild is transactional; schema v1 contains only these curated objects.
        con.execute("DROP VIEW IF EXISTS daily_demand; DROP VIEW IF EXISTS latest_observations")
        con.execute("DROP TABLE IF EXISTS observations; DROP TABLE IF EXISTS sources; DROP TABLE IF EXISTS metadata")
        con.execute((ROOT / "sql/schema.sql").read_text())
        for table, rows in [("sources", sources), ("observations", observations)]:
            for row in rows:
                keys = list(row)
                columns = ",".join(keys)
                placeholders = ",".join("?" for _ in keys)
                con.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", [row[k] for k in keys])
        con.executemany("INSERT INTO metadata VALUES (?,?)", [
            ("schema_version", "1"), ("model_version", "0.1.0"),
            ("sources_sha256", hashlib.sha256(source_bytes).hexdigest()),
            ("observations_sha256", hashlib.sha256(obs_bytes).hexdigest())])
        con.execute("""CREATE VIEW daily_demand AS SELECT o.*, s.url, s.published_on, s.retrieved_on,
        CASE unit WHEN 'tokens_per_day' THEN reported_value
          WHEN 'tokens_per_month' THEN reported_value/(365.25/12)
          WHEN 'tokens_in_period' THEN reported_value/(date_diff('day',period_start,period_end)+1)
        END AS tokens_per_day,
        CASE WHEN unit='tokens_per_month' THEN reported_value/31 ELSE tokens_per_day END AS calendar_sensitivity_lower,
        CASE WHEN unit='tokens_per_month' THEN reported_value/28 ELSE tokens_per_day END AS calendar_sensitivity_upper,
        'normalized_disclosure' AS derived_class
        FROM latest_observations o JOIN sources s USING(source_id)
        WHERE o.evidence_class='disclosed'""")
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        con.close()
        raise
    return con

def main():
    parser = argparse.ArgumentParser(description="Rebuild a reproducible curated evidence database")
    parser.add_argument("--database", default="data/monitor.duckdb")
    args = parser.parse_args()
    path = Path(args.database)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = build_database(path)
    print(con.execute("SELECT provider, as_of, tokens_per_day, qualifier FROM daily_demand ORDER BY provider, as_of").fetchdf().to_string(index=False))
    con.close()

if __name__ == "__main__":
    main()
