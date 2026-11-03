"""Synthetic values below are testing fixtures only, never production evidence."""
from datetime import date
import json
import math
import pytest
from compute_monitor.model import ROOT, build_database, normalize, effective_capacity, compute_equivalent

@pytest.fixture
def synthetic_row():
    return dict(reported_value=310,unit="tokens_in_period",period_start="2024-01-01",period_end="2024-01-31")

def test_calendar_days(synthetic_row):
    assert normalize(synthetic_row)["tokens_per_day"] == 10

def test_leap_february(synthetic_row):
    synthetic_row.update(period_start="2024-02-01",period_end="2024-02-29",reported_value=290)
    assert normalize(synthetic_row)["tokens_per_day"] == 10

def test_month_sensitivity(synthetic_row):
    synthetic_row.update(unit="tokens_per_month",reported_value=310)
    out=normalize(synthetic_row)
    assert out["calendar_sensitivity_lower"] == 10
    assert out["calendar_sensitivity_upper"] == pytest.approx(310/28)
    assert out["measurement_upper"] is None

@pytest.mark.parametrize("unit",["dollars","gpu_hours"])
def test_reject_unknown_units(synthetic_row,unit):
    synthetic_row["unit"]=unit
    with pytest.raises(ValueError): normalize(synthetic_row)

def test_missing_period(synthetic_row):
    synthetic_row["period_start"]=None
    with pytest.raises(ValueError): normalize(synthetic_row)

def test_capacity_fixture():
    assert effective_capacity(10,.5,.8,.5,100)==pytest.approx(17280000)

@pytest.mark.parametrize("vals",[(1,1.1,1,1,1),(1,1,1,-.1,1),(math.nan,1,1,1,1)])
def test_capacity_rejects_invalid(vals):
    with pytest.raises(ValueError): effective_capacity(*vals)

def test_compute_equivalent_requires_split():
    with pytest.raises(ValueError): compute_equivalent(None,100,1,4,1)
    assert compute_equivalent(10,20,1,4,2)==45

def test_offline_ingestion_and_accounting():
    con=build_database()
    assert con.execute("SELECT count(*) FROM daily_demand").fetchone()[0]==11
    assert con.execute("SELECT count(DISTINCT provider) FROM daily_demand").fetchone()[0]==6
    assert con.execute("SELECT count(*) FROM observations WHERE aggregation_eligible").fetchone()[0]==0
    assert con.execute("SELECT count(input_tokens)+count(output_tokens) FROM observations").fetchone()[0]==0
    assert con.execute("SELECT qualifier FROM daily_demand WHERE observation_id='google_2025_07'").fetchone()[0]=='over'
    assert con.execute("SELECT tokens_per_day FROM daily_demand WHERE observation_id='microsoft_2025_03'").fetchone()[0]==pytest.approx(50e12/31)
    for row in json.loads((ROOT/'data/observations.json').read_text()):
        sql=con.execute("SELECT tokens_per_day FROM daily_demand WHERE observation_id=?",[row['observation_id']]).fetchone()[0]
        assert sql==pytest.approx(normalize(row)['tokens_per_day'])
    con.close()

def test_rebuild_reproducibility(tmp_path):
    path=tmp_path/'fixture.duckdb'
    con=build_database(path)
    a=con.execute("SELECT * FROM metadata ORDER BY key").fetchall()
    con.close()
    con=build_database(path)
    assert con.execute("SELECT * FROM metadata ORDER BY key").fetchall()==a
    con.close()

def test_version_selection(tmp_path):
    sources=json.loads((ROOT/'data/sources.json').read_text())
    rows=json.loads((ROOT/'data/observations.json').read_text())
    revision=dict(rows[0],revision=2,reported_value=123)
    rows.append(revision) # SYNTHETIC revision, tmp_path only
    (tmp_path/'sources.json').write_text(json.dumps(sources))
    (tmp_path/'observations.json').write_text(json.dumps(rows))
    con=build_database(data_dir=tmp_path)
    assert con.execute("SELECT reported_value FROM latest_observations WHERE observation_id=?",[revision['observation_id']]).fetchone()[0]==123
    assert con.execute("SELECT count(*) FROM observations").fetchone()[0]==12
    con.close()

def test_reject_unreviewed_aggregation(tmp_path):
    rows=json.loads((ROOT/'data/observations.json').read_text())
    rows[0]['aggregation_eligible']=True
    (tmp_path/'sources.json').write_bytes((ROOT/'data/sources.json').read_bytes())
    (tmp_path/'observations.json').write_text(json.dumps(rows))
    with pytest.raises(ValueError,match='aggregation'): build_database(data_dir=tmp_path)

@pytest.mark.parametrize("value",[-1,math.nan,math.inf])
def test_invalid_reported_values(synthetic_row,value):
    synthetic_row['reported_value']=value
    with pytest.raises(ValueError): normalize(synthetic_row)

def test_estimates_excluded_from_disclosed_view(tmp_path):
    rows=json.loads((ROOT/'data/observations.json').read_text())
    rows[0]['evidence_class']='estimated' # SYNTHETIC reclassification, tmp_path only
    (tmp_path/'sources.json').write_bytes((ROOT/'data/sources.json').read_bytes())
    (tmp_path/'observations.json').write_text(json.dumps(rows))
    con=build_database(data_dir=tmp_path)
    assert con.execute("SELECT count(*) FROM daily_demand").fetchone()[0]==10
    assert con.execute("SELECT count(*) FROM observations WHERE evidence_class='estimated'").fetchone()[0]==1
    con.close()
