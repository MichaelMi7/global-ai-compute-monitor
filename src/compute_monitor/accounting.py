"""Conservative selections, with publication cutoffs and overlap guards."""
from datetime import date
from .model import normalize

def latest_snapshot(data,cutoff,maximum_age_days=90):
    cutoff=date.fromisoformat(cutoff) if isinstance(cutoff,str) else cutoff
    sources={s['source_id']:s for s in data['sources']}
    candidates={}
    for row in data['observations']:
        source=sources[row['source_id']]
        if row['evidence_class']!='disclosed' or date.fromisoformat(row['as_of'])>cutoff: continue
        if not source.get('published_on') or date.fromisoformat(source['published_on'])>cutoff: continue
        # A later page update means the current text cannot substantiate an earlier backtest.
        if source.get('updated_on') and date.fromisoformat(source['updated_on'])>cutoff: continue
        key=row.get('series_id',row['provider']+'_'+row['scope'])
        prior=candidates.get(key)
        if prior is None or (row['as_of'],row['revision'])>(prior['as_of'],prior['revision']): candidates[key]=row
    return [dict(r,**normalize(r),stale=(cutoff-date.fromisoformat(r['as_of'])).days>maximum_age_days) for r in candidates.values()]

def compatible_sum(rows,relationships):
    """Only explicit non-overlapping provider period totals with matching accounting."""
    if not rows: raise ValueError('No observations selected')
    if len({r['observation_id'] for r in rows})!=len(rows): raise ValueError('Duplicate observation')
    first=rows[0]
    for r in rows:
        if r.get('ledger')!='provider' or r['evidence_class']!='disclosed': raise ValueError('Only disclosed provider records')
        if r['unit']!='tokens_in_period' or not r.get('period_start') or not r.get('period_end'): raise ValueError('Explicit period totals required')
        if r['qualifier']=='approximately': raise ValueError('Approximate reports cannot establish a floor')
        fields=('period_start','period_end','accounting_basis','workload','geography','token_direction')
        if any(r.get(k)!=first.get(k) for k in fields): raise ValueError('Incompatible scope, period or accounting')
        if 'unspecified' in r.get('accounting_basis','unspecified'): raise ValueError('Known token accounting required')
    disjoint={frozenset((x['left_id'],x['right_id'])) for x in relationships if x['relation']=='disjoint'}
    conflicts={frozenset((x['left_id'],x['right_id'])) for x in relationships if x['relation'] in ('contained_in','possible_overlap','scope_break')}
    for i,a in enumerate(rows):
        for b in rows[i+1:]:
            pair=frozenset((a['observation_id'],b['observation_id']))
            if pair in conflicts or pair not in disjoint: raise ValueError('Unresolved overlap; no certified disjointness')
    return dict(tokens_per_day=sum(normalize(r)['tokens_per_day'] for r in rows),qualifier='over' if any(r['qualifier']=='over' for r in rows) else 'equal',classification='selected_compatible_subset_not_global')
