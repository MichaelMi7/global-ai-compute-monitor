-- Schema v1. Evidence revisions are append-only in the committed JSON ledger.
CREATE TABLE metadata(key VARCHAR PRIMARY KEY, value VARCHAR NOT NULL);
CREATE TABLE sources(
 source_id VARCHAR PRIMARY KEY, url VARCHAR NOT NULL, title VARCHAR NOT NULL,
 published_on DATE, retrieved_on DATE NOT NULL, source_type VARCHAR NOT NULL,
 publication_date_status VARCHAR NOT NULL, evidence_summary VARCHAR NOT NULL
);
CREATE TABLE observations(
 observation_id VARCHAR NOT NULL, revision INTEGER NOT NULL CHECK(revision > 0),
 source_id VARCHAR NOT NULL REFERENCES sources(source_id),
 provider VARCHAR NOT NULL, model VARCHAR, workload VARCHAR NOT NULL,
 deployment VARCHAR NOT NULL, geography VARCHAR NOT NULL,
 geography_basis VARCHAR NOT NULL, scope VARCHAR NOT NULL,
 period_start DATE, period_end DATE, period_status VARCHAR NOT NULL,
 as_of DATE NOT NULL, reporting_frequency VARCHAR NOT NULL,
 token_direction VARCHAR NOT NULL, input_tokens DOUBLE, output_tokens DOUBLE,
 reported_value DOUBLE NOT NULL CHECK(reported_value >= 0), unit VARCHAR NOT NULL,
 qualifier VARCHAR NOT NULL CHECK(qualifier IN ('equal','over','approximately')),
 evidence_class VARCHAR NOT NULL CHECK(evidence_class IN ('disclosed','estimated')),
 uncertainty_lower DOUBLE, uncertainty_upper DOUBLE, uncertainty_basis VARCHAR NOT NULL,
 overlap_group VARCHAR NOT NULL, aggregation_eligible BOOLEAN NOT NULL,
 notes VARCHAR NOT NULL, PRIMARY KEY(observation_id,revision),
 CHECK(period_start IS NULL OR period_end >= period_start),
 CHECK(uncertainty_upper IS NULL OR uncertainty_upper >= uncertainty_lower)
);
CREATE VIEW latest_observations AS
 SELECT * FROM observations QUALIFY row_number() OVER
 (PARTITION BY observation_id ORDER BY revision DESC)=1;
-- No aggregate global floor: heterogeneous scopes and unresolved overlaps.
