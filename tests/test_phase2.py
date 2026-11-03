"""All constructed numeric inputs and changed records are synthetic test fixtures."""
from copy import deepcopy
import csv
from datetime import date
import json
import pytest
from compute_monitor.model import read_ledger,validate_ledger,normalize
from compute_monitor.accounting import latest_snapshot,compatible_sum
from compute_monitor.scenarios import revenue_implied_tokens,price_response,unit_economics,matched_tightness
from compute_monitor.monitor import check_url,check_sources,text_hash
from compute_monitor.release import release

def test_new_rate_units():
    assert normalize(dict(reported_value=2,unit='tokens_per_minute'))['tokens_per_day']==2880
    assert normalize(dict(reported_value=70,unit='tokens_per_week'))['tokens_per_day']==10

def test_publication_cutoff_and_page_update():
    data=read_ledger()
    snap=latest_snapshot(data,'2026-04-01')
    assert 'openai_api_2026_03' in {r['observation_id'] for r in snap}
    assert 'google_api_2026_10' not in {r['observation_id'] for r in snap}
    snap=latest_snapshot(data,'2026-06-01')
    assert 'openrouter_2026_05' not in {r['observation_id'] for r in snap}

def test_snapshot_preserves_scope_and_staleness():
    snap=latest_snapshot(read_ledger(),'2026-11-04')
    google=[r for r in snap if r['provider']=='Google']
    assert len(google)==2
    assert {r['stale'] for r in google}=={True,False}

def test_demand_sources_are_primary_or_official():
    data=read_ledger();sources={s['source_id']:s for s in data['sources']}
    for r in data['observations']:
        assert sources[r['source_id']]['source_type']!='primary_research_estimate'
    assert sum(r['evidence_class']=='estimated' for r in data['infrastructure'])==5
    assert all(r['inference_fraction'] is None for r in data['infrastructure'])

def test_containment_cycle_rejected():
    data=deepcopy(read_ledger());a=data['relationships'][0]
    data['relationships'].append(dict(a,left_id=a['right_id'],right_id=a['left_id']))
    with pytest.raises(ValueError,match='cycle'):validate_ledger(data)

def test_duplicate_revision_and_bad_uncertainty():
    data=deepcopy(read_ledger());data['observations'].append(data['observations'][0])
    with pytest.raises(ValueError,match='Duplicate'):validate_ledger(data)
    data=deepcopy(read_ledger());data['infrastructure'][0].update(uncertainty_lower=5,uncertainty_upper=6)
    with pytest.raises(ValueError,match='interval'):validate_ledger(data)

def test_overlap_controls():
    data=read_ledger()
    rows=[r for r in data['observations'] if r['provider']=='Microsoft']
    with pytest.raises(ValueError):compatible_sum(rows,data['relationships'])
    # Fixture with complete matched periods and explicit disjointness.
    first=dict(rows[0],observation_id='a',reported_value=31,qualifier='equal',accounting_basis='text_total_uncached')
    second=dict(first,observation_id='b',reported_value=62)
    with pytest.raises(ValueError,match='overlap'):compatible_sum([first,second],[])
    relation=[dict(left_id='a',right_id='b',relation='disjoint')]
    out=compatible_sum([first,second],relation)
    assert out['tokens_per_day']==3
    assert out['classification']=='selected_compatible_subset_not_global'
    second['qualifier']='over'
    assert compatible_sum([first,second],relation)['qualifier']=='over'

@pytest.mark.parametrize('ledger',['router','national'])
def test_no_cross_ledger_floor(ledger):
    row=dict(read_ledger()['observations'][0],ledger=ledger)
    with pytest.raises(ValueError):compatible_sum([row],[])

def test_revenue_estimate_and_elasticity():
    band=revenue_implied_tokens(365.25,1,1,2)
    assert band['lower']==500000 and band['upper']==1000000
    assert price_response(100,2,1,1)==200
    assert price_response(100,2,1,0)==100
    with pytest.raises(ValueError):revenue_implied_tokens(1,1,2,1)

def fixture_economics(**overrides):
    return unit_economics(**dict(dict(installed=1,inference_fraction=1,available_fraction=1,utilization=1,throughput=1,price_per_million=1,capex_per_accelerator=100,life_years=5,idle_kw=.1,active_kw=1,pue=1.2,power_price=.1,other_annual_cost=10),**overrides))

def test_economics_cash_flow_and_break_even():
    out=fixture_economics()
    assert out['annual_tokens']==31557600
    assert out['annual_energy_kwh']==pytest.approx(10519.2)
    assert out['annual_depreciation']==20
    assert out['operating_profit']==pytest.approx(31.5576-1051.92-20-10)
    equilibrium=fixture_economics(price_per_million=out['break_even_price_per_million'])
    assert equilibrium['operating_profit']==pytest.approx(0,abs=1e-8)

def test_idle_costs_and_zero_output():
    out=fixture_economics(utilization=0)
    assert out['annual_energy_kwh']>0
    assert out['break_even_price_per_million'] is None and out['operating_margin'] is None
    with pytest.raises(ValueError):fixture_economics(active_kw=.01)

def test_matched_scope_tightness():
    base=dict(workload_id='fixture-model',geography='US',period_start='2026-01-01',period_end='2026-01-31',token_basis='text_combined',deployment='captive')
    demand=dict(base,tokens_per_day=50,qualifier='equal');capacity=dict(base,tokens_per_day=100,status='scenario_available')
    assert matched_tightness(demand,capacity)['ratio']==.5
    for change in (dict(geography='China'),dict(status='planned'),dict(tokens_per_day=0)):
        with pytest.raises(ValueError):matched_tightness(demand,dict(capacity,**change))
    with pytest.raises(ValueError):matched_tightness(dict(demand,qualifier='over'),capacity)

@pytest.mark.parametrize('url',['http://openai.com','https://localhost/a','https://127.0.0.1/','https://openai.com@evil.example/','https://openai.com:444/a'])
def test_network_allowlist(url):
    with pytest.raises(ValueError):check_url(url)

def test_monitor_changes_without_promoting_observations():
    source=dict(source_id='fixture',url='https://openai.com/test')
    report=check_sources([source],fetcher=lambda url:'<p>one</p>')
    digest=report['results'][0]['text_sha256']
    assert report['results'][0]['status']=='new_fingerprint'
    assert check_sources([source],{'fixture':digest},fetcher=lambda url:'<p>one</p>')['results'][0]['status']=='unchanged'
    assert check_sources([source],{'fixture':digest},fetcher=lambda url:'<p>two</p>')['results'][0]['status']=='changed_review_required'
    assert text_hash('<p>one</p><script>noise</script>')==digest
    def fail(url):raise TimeoutError('fixture')
    assert check_sources([source],fetcher=fail)['results'][0]['status']=='unavailable'

def test_deterministic_release_and_real_csv(tmp_path):
    a=release(tmp_path);b=release(tmp_path)
    assert a==b
    assert json.loads((tmp_path/'manifest.json').read_text())['counts']['observations']==11
    with (tmp_path/'demand-evidence.csv').open(encoding='utf-8',newline='') as f:
        assert len(list(csv.DictReader(f)))==11


def test_bad_scope_period():
    base=dict(workload_id='fixture',geography='US',period_start='2026-02-01',period_end='2026-01-01',token_basis='text',deployment='captive',tokens_per_day=1)
    with pytest.raises(ValueError,match='Reversed'):matched_tightness(dict(base,qualifier='equal'),dict(base,status='scenario_available'))

def test_html_export_has_mobile_layout_and_correct_evidence():
    from html.parser import HTMLParser
    from pathlib import Path
    class Inspect(HTMLParser):
        def __init__(self):super().__init__();self.articles=0;self.external_resources=0;self.scripts=0
        def handle_starttag(self,tag,attrs):
            a=dict(attrs)
            self.articles+=tag=='article'
            self.external_resources+=bool(a.get('src')) or (tag=='link' and a.get('rel')=='stylesheet')
            self.scripts+=tag=='script'
    html=(Path(__file__).resolve().parents[1]/'exports/global-ai-compute-monitor.html').read_text(encoding='utf-8')
    parser=Inspect();parser.feed(html)
    assert parser.articles==25
    assert parser.external_resources==parser.scripts==0
    assert 'name="viewport"' in html
    assert 'trillion tokens/minute' in html and 'trillion tokens/week' in html
