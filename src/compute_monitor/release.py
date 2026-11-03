"""Deterministic, no-network release exports and input manifests."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from .model import ROOT,DATA_FILES,MODEL_VERSION,build_database,read_ledger

def release(output_dir=None):
    output=Path(output_dir or ROOT/'exports');output.mkdir(parents=True,exist_ok=True)
    con=build_database(); data=read_ledger()
    tables={'demand-evidence.csv':'SELECT * FROM daily_demand ORDER BY observation_id',
      'infrastructure-evidence.csv':'SELECT i.*,s.url FROM latest_infrastructure i JOIN sources s USING(source_id) ORDER BY capacity_id'}
    for name,query in tables.items():
        with (output/name).open('w',encoding='utf-8',newline='') as f:
            cursor=con.execute(query);writer=csv.writer(f,lineterminator='\n')
            writer.writerow([c[0] for c in cursor.description]);writer.writerows(cursor.fetchall())
    con.close()
    manifest=dict(model_version=MODEL_VERSION,schema_version=2,verification_dates=sorted({s['retrieved_on'] for s in data['sources']}),
       counts={name:len(data[name]) for name in DATA_FILES},
       inputs={name+'.json':hashlib.sha256((ROOT/'data'/(name+'.json')).read_bytes()).hexdigest() for name in DATA_FILES},
       code={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('sql/schema.sql','src/compute_monitor/model.py','src/compute_monitor/accounting.py','src/compute_monitor/scenarios.py')},
       exports={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in tables},
       limitations='Selected public evidence only; no current global sum or matched observed tightness. Estimates and scenarios are not measurements.')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(manifest['counts']))
    return manifest
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir');args=parser.parse_args();release(args.output_dir)
