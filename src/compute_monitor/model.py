"""Offline, transactional evidence database and explicit raw-token normalization."""
from __future__ import annotations
import argparse
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[2]
DATA_FILES = ('sources','observations','infrastructure','relationships','research_gaps')
MODEL_VERSION = '0.2.0'

def normalize(row):
    value, unit = row['reported_value'], row['unit']
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0:
        raise ValueError('Reported values must be finite and nonnegative')
    if unit == 'tokens_per_day':
        divisor, basis = 1., 'reported daily run rate; averaging window may be unknown'
    elif unit == 'tokens_per_minute':
        divisor, basis = 1/1440, 'minute run rate times 1440; not a measured day total'
    elif unit == 'tokens_per_week':
        divisor, basis = 7., 'weekly run rate divided by 7; actual week may be unspecified'
    elif unit == 'tokens_per_month':
        divisor, basis = 365.25/12, 'standard month; actual month unspecified'
    elif unit == 'tokens_in_period':
        if not row.get('period_start') or not row.get('period_end'):
            raise ValueError('Period total requires explicit boundaries')
        divisor = (date.fromisoformat(row['period_end'])-date.fromisoformat(row['period_start'])).days+1
        if divisor <= 0: raise ValueError('Invalid reporting period')
        basis = 'inclusive calendar-day average'
    else:
        raise ValueError(f'Unsupported unit: {unit}')
    daily=value/divisor
    if not math.isfinite(daily): raise ValueError('Normalization overflow')
    return dict(tokens_per_day=daily,normalization_days=divisor,normalization_basis=basis,
        calendar_sensitivity_lower=value/31 if unit=='tokens_per_month' else daily,
        calendar_sensitivity_upper=value/28 if unit=='tokens_per_month' else daily,
        measurement_upper=None,derived_class='normalized_'+('estimate' if row.get('evidence_class')=='estimated' else 'disclosure'))

def effective_capacity(installed,inference_fraction,available_fraction,utilization,tok_per_second):
    vals=[installed,inference_fraction,available_fraction,utilization,tok_per_second]
    if not all(isinstance(x,(int,float)) and math.isfinite(x) and x>=0 for x in vals):
        raise ValueError('Scenario inputs must be finite and nonnegative')
    if any(x>1 for x in vals[1:4]): raise ValueError('Fractions must be in [0,1]')
    result=math.prod(vals)*86400
    if not math.isfinite(result): raise ValueError('Capacity overflow')
    return result

def compute_equivalent(input_tokens,output_tokens,input_flops,output_flops,reference_flops):
    vals=[input_tokens,output_tokens,input_flops,output_flops,reference_flops]
    if any(x is None or not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 for x in vals) or reference_flops==0:
        raise ValueError('Known nonnegative split and costs, positive reference required')
    result=(input_tokens*input_flops+output_tokens*output_flops)/reference_flops
    if not math.isfinite(result): raise ValueError('Compute conversion overflow')
    return result

def read_ledger(data_dir=None):
    folder=Path(data_dir or ROOT/'data')
    result={}
    for name in DATA_FILES:
        path=folder/(name+'.json')
        if name in ('sources','observations') and not path.exists(): raise ValueError(f'Missing {name}')
        result[name]=json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else []
    validate_ledger(result)
    return result

def validate_ledger(data):
    sources=data['sources']; ids={s['source_id'] for s in sources}
    if len(ids)!=len(sources): raise ValueError('Duplicate source IDs')
    from urllib.parse import urlparse
    for s in sources:
        if urlparse(s['url']).scheme!='https': raise ValueError('Sources require HTTPS')
        retrieved=date.fromisoformat(s['retrieved_on'])
        if s.get('published_on') and date.fromisoformat(s['published_on'])>retrieved:
            raise ValueError('Publication after verification')
    for table,key in [('observations','observation_id'),('infrastructure','capacity_id')]:
        seen=set()
        for r in data[table]:
            identity=(r[key],r['revision'])
            if identity in seen: raise ValueError('Duplicate observation revision')
            seen.add(identity)
            if r['source_id'] not in ids: raise ValueError('Unknown source')
            if not isinstance(r['revision'],int) or r['revision']<1: raise ValueError('Invalid revision')
            if r['evidence_class'] not in ('disclosed','estimated'): raise ValueError('Invalid evidence class')
            value=r['reported_value']
            if not isinstance(value,(int,float)) or not math.isfinite(value) or value<0: raise ValueError('Invalid magnitude')
            date.fromisoformat(r['as_of'])
            lo,hi=r.get('uncertainty_lower'),r.get('uncertainty_upper')
            for bound in (lo,hi):
                if bound is not None and (not math.isfinite(bound) or bound<0): raise ValueError('Invalid uncertainty')
            if lo is not None and hi is not None and not lo<=value<=hi: raise ValueError('Invalid interval')
            if bool(r.get('period_start')) != bool(r.get('period_end')): raise ValueError('Incomplete reporting period')
            if r.get('period_start') and r['period_start']>r['period_end']: raise ValueError('Reversed period')
            if table=='observations':
                normalize(r)
                if r['aggregation_eligible']: raise ValueError('No unreviewed global aggregation is permitted')
                if r['qualifier'] not in ('equal','over','approximately'): raise ValueError('Unknown qualifier')
            elif r['unit'] not in ('GW','MW','H100_equivalent','physical_accelerators'):
                raise ValueError('Unsupported infrastructure unit')
    obs_ids={r['observation_id'] for r in data['observations']}
    graph={}
    for rel in data['relationships']:
        if rel['left_id'] not in obs_ids or rel['right_id'] not in obs_ids: raise ValueError('Unknown relationship endpoint')
        if rel['source_id'] not in ids: raise ValueError('Unknown relationship source')
        if rel['left_id']==rel['right_id']: raise ValueError('Self relationship')
        if rel['relation'] not in ('contained_in','possible_overlap','scope_break','disjoint'): raise ValueError('Unknown relation')
        if rel['relation']=='contained_in': graph.setdefault(rel['left_id'],[]).append(rel['right_id'])
    def visit(node,path):
        if node in path: raise ValueError('Containment cycle')
        for parent in graph.get(node,[]): visit(parent,path|{node})
    for node in graph: visit(node,set())

def build_database(path=':memory:',data_dir=None):
    folder=Path(data_dir or ROOT/'data'); data=read_ledger(folder)
    con=duckdb.connect(str(path))
    try:
        con.execute('BEGIN')
        for v in ('daily_demand','normalized_estimates','normalized_observations','latest_observations','latest_infrastructure'):
            con.execute(f'DROP VIEW IF EXISTS {v}')
        for table in ('relationships','research_gaps','infrastructure','observations','sources','metadata'):
            con.execute(f'DROP TABLE IF EXISTS {table}')
        con.execute((ROOT/'sql/schema.sql').read_text(encoding='utf-8'))
        tables={'sources':'sources','observations':'observations','infrastructure':'infrastructure','relationships':'relationships','research_gaps':'research_gaps'}
        for name,table in tables.items():
            for original in data[name]:
                row=dict(original)
                if name=='sources': row.setdefault('updated_on',None)
                if name=='observations':
                    row.setdefault('ledger','provider'); row.setdefault('series_id',row['provider']+'_'+row['scope'])
                    row.setdefault('accounting_basis','raw_tokens_split_and_modality_unspecified')
                allowed={column[0] for column in con.execute(f'SELECT * FROM {table} LIMIT 0').description}
                if set(row)-allowed: raise ValueError('Unknown ledger fields')
                columns=','.join(row); placeholders=','.join('?' for _ in row)
                con.execute(f'INSERT INTO {table} ({columns}) VALUES ({placeholders})',list(row.values()))
        metadata=[('schema_version','2'),('model_version',MODEL_VERSION)]
        for name in DATA_FILES:
            p=folder/(name+'.json')
            metadata.append((name+'_sha256',hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else 'absent'))
        con.executemany('INSERT INTO metadata VALUES (?,?)',metadata)
        con.execute("""CREATE VIEW normalized_observations AS SELECT o.*,s.url,s.published_on,s.retrieved_on,s.updated_on,
        CASE unit WHEN 'tokens_per_day' THEN reported_value WHEN 'tokens_per_minute' THEN reported_value*1440
          WHEN 'tokens_per_week' THEN reported_value/7 WHEN 'tokens_per_month' THEN reported_value/(365.25/12)
          WHEN 'tokens_in_period' THEN reported_value/(date_diff('day',period_start,period_end)+1) END AS tokens_per_day,
        CASE WHEN unit='tokens_per_month' THEN reported_value/31 ELSE tokens_per_day END AS calendar_sensitivity_lower,
        CASE WHEN unit='tokens_per_month' THEN reported_value/28 ELSE tokens_per_day END AS calendar_sensitivity_upper,
        CASE evidence_class WHEN 'disclosed' THEN 'normalized_disclosure' ELSE 'normalized_estimate' END AS derived_class
        FROM latest_observations o JOIN sources s USING(source_id);
        CREATE VIEW daily_demand AS SELECT * FROM normalized_observations WHERE evidence_class='disclosed';
        CREATE VIEW normalized_estimates AS SELECT * FROM normalized_observations WHERE evidence_class='estimated';""")
        con.execute('COMMIT')
    except Exception:
        con.execute('ROLLBACK'); con.close(); raise
    return con

def main():
    parser=argparse.ArgumentParser(description='Offline evidence database rebuild')
    parser.add_argument('--database',default='data/monitor.duckdb'); args=parser.parse_args()
    path=Path(args.database); path.parent.mkdir(parents=True,exist_ok=True)
    con=build_database(path)
    print(con.execute('SELECT provider,scope,as_of,tokens_per_day,qualifier FROM daily_demand ORDER BY provider,as_of').fetchdf().to_string(index=False))
    print('Infrastructure rows:',con.execute('SELECT count(*) FROM latest_infrastructure').fetchone()[0]); con.close()
if __name__=='__main__': main()
