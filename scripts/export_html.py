"""Export a mobile-friendly HTML snapshot; no network dependencies or JavaScript."""
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape
import hashlib
import json
from pathlib import Path
from compute_monitor.model import ROOT, normalize


def export():
    observations_path = ROOT / 'data/observations.json'
    sources_path = ROOT / 'data/sources.json'
    sources = {s['source_id']: s for s in json.loads(sources_path.read_text(encoding='utf-8'))}
    revisions = {}
    for row in json.loads(observations_path.read_text(encoding='utf-8')):
        if row['observation_id'] not in revisions or row['revision'] > revisions[row['observation_id']]['revision']:
            revisions[row['observation_id']] = row
    rows = sorted((r for r in revisions.values() if r['evidence_class'] == 'disclosed'), key=lambda r: r['as_of'])
    colors = {'Google': '#6ee7b7', 'Microsoft': '#93c5fd', 'Fireworks': '#f9a8d4'}
    bars, cards = [], []
    infrastructure = json.loads((ROOT / 'data/infrastructure.json').read_text(encoding='utf-8'))
    supply_cards = []
    for record in infrastructure:
        source = sources[record['source_id']]
        interval = f"Source-reported 90% interval: {record['uncertainty_lower']:,.0f} to {record['uncertainty_upper']:,.0f}." if record['uncertainty_lower'] is not None else 'Statistical uncertainty: not disclosed.'
        supply_cards.append(f'''<article class="evidence"><div class="eyebrow">{escape(record['entity'])} · {record['as_of']}</div><h3>{record['reported_value']:,.2f} {escape(record['unit'].replace('_',' '))}</h3><p>{escape(record['qualifier'])} · {escape(record['evidence_class'])} · {escape(record['status'].replace('_',' '))}</p><p>{escape(record['metric'].replace('_',' '))}. {escape(record['workload'].replace('_',' '))}.</p><p>{escape(interval)}</p><p>{escape(record['notes'])}</p><a href="{escape(source['url'],quote=True)}">{escape(source['title'])}</a></article>''')
    ceiling = max(normalize(r)['tokens_per_day'] / 1e12 for r in rows) * 1.12
    for r in rows:
        norm, source = normalize(r), sources[r['source_id']]
        value = norm['tokens_per_day'] / 1e12
        sign = '&gt;' if r['qualifier'] == 'over' else ('~' if r['qualifier'] == 'approximately' else '')
        period = f"{r['period_start']} to {r['period_end']}" if r['period_start'] else 'Exact averaging window unspecified'
        frequency = r['reporting_frequency'].replace('_', ' ')
        color = colors.get(r['provider'], '#ddd')
        label = f"{escape(r['provider'])} <span>{r['as_of']}</span>"
        bars.append(f'''<div class="bar-row"><div class="bar-label">{label}<strong>{sign}{value:.2f} T/day</strong></div>
        <div class="track"><div class="bar" style="width:{value/ceiling*100:.3f}%;background:{color}"></div></div>
        <small>{escape(frequency)}</small></div>''')
        if r['unit'] == 'tokens_per_month':
            original = f"{sign}{r['reported_value']/1e12:,.0f} trillion tokens/month"
            sensitivity = f"Calendar-denominator threshold sensitivity: {norm['calendar_sensitivity_lower']/1e12:.2f} to {norm['calendar_sensitivity_upper']/1e12:.2f} T/day (31 vs 28 days). This is not a confidence interval or an upper bound."
        elif r['unit'] == 'tokens_in_period':
            original = f"{sign}{r['reported_value']/1e12:,.0f} trillion tokens in period"
            sensitivity = f"Normalized over {norm['normalization_days']:.0f} inclusive calendar days."
        else:
            label = {'tokens_per_minute':'minute','tokens_per_week':'week','tokens_per_day':'day'}[r['unit']]
            original = f"{sign}{r['reported_value']/1e12:,.3f} trillion tokens/{label}"
            sensitivity = norm['normalization_basis'] + '. Daily-equivalent run rate; not a measured daily count.'
        cards.append(f'''<article class="evidence"><div class="eyebrow" style="color:{color}">{escape(r['provider'])} · {r['as_of']}</div>
        <h3>{original}</h3><p class="rate">{sign}{value:.2f} <span>trillion raw tokens/day, normalized</span></p>
        <dl><dt>Period</dt><dd>{escape(period)}</dd><dt>Scope</dt><dd>{escape(r['scope'].replace('_',' '))}</dd>
        <dt>Deployment</dt><dd>{escape(r['deployment'].replace('_',' '))}</dd>
        <dt>Published</dt><dd>{source['published_on']}</dd><dt>Source checked</dt><dd>{source['retrieved_on']}</dd></dl>
        <p>{escape(sensitivity)}</p><p>{escape(r['notes'])}</p>
        <details><summary>Source and accounting details</summary><p><a href="{escape(source['url'],quote=True)}">{escape(source['title'])}</a></p>
        <p>Company disclosure; unaudited. Original publication date is the date displayed on the source page. Geography: global, unspecified. Model and input/output token split: unknown. Statistical uncertainty bounds: unknown.</p>
        <p>Observation: {escape(r['observation_id'])}, revision {r['revision']}. Not eligible for aggregation.</p></details></article>''')
    digest = hashlib.sha256(observations_path.read_bytes()).hexdigest()
    html = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark"><title>Global AI Compute Monitor — offline snapshot</title>
    <style>*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#e5edf8;font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:900px;margin:auto;padding:28px 18px 56px}h1{font-size:clamp(30px,7vw,48px);line-height:1.1;letter-spacing:-1.4px;margin:12px 0 20px}h2{font-size:23px;margin:30px 0 12px}h3{font-size:22px;margin:8px 0}p{margin:12px 0;color:#c4d0e2}.eyebrow{text-transform:uppercase;letter-spacing:1.4px;font-size:12px;font-weight:700;color:#6ee7b7}.notice{border-left:3px solid #fbbf24;padding:14px 16px;background:#27231c;border-radius:6px;color:#f9e4b3}.stats{display:flex;gap:12px;flex-wrap:wrap;margin:22px 0}.stat{background:#162135;border:1px solid #29364b;border-radius:14px;padding:16px;flex:1;min-width:125px}.stat strong{font-size:26px;display:block}.stat span,small{font-size:13px;color:#a6b5cc}.panel,.evidence{background:#121d30;border:1px solid #29364b;border-radius:16px;padding:20px;margin:14px 0}.bar-row{margin:22px 0}.bar-label{display:flex;justify-content:space-between;gap:10px;font-size:14px}.bar-label span{display:block;font-size:12px;color:#a6b5cc}.bar-label strong{white-space:nowrap}.track{background:#253249;height:12px;border-radius:6px;margin:7px 0}.bar{height:100%;border-radius:6px}.rate{font-size:25px;font-weight:700;color:#fff}.rate span{display:block;font-size:13px;color:#a6b5cc;font-weight:400}dl{display:grid;grid-template-columns:95px 1fr;gap:7px;font-size:14px}dt{color:#a6b5cc}dd{margin:0;overflow-wrap:anywhere}summary{cursor:pointer;padding:10px 0;color:#93c5fd}a{color:#93c5fd;overflow-wrap:anywhere}footer{margin-top:35px;font-size:12px;color:#94a3b8;overflow-wrap:anywhere}li{margin:10px 0}code{font-size:12px} @media(min-width:700px){.evidence-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.evidence{margin:0}.bar-label span{display:inline;margin-left:10px}}</style></head><body><main>
    <div class="eyebrow">Independent infrastructure research · Release 0.2</div><h1>Global AI<br>Compute Monitor</h1>
    <p>A portable view of selected public AI token disclosures. This file works offline without Python, a server or external chart libraries.</p>
    <div class="notice"><strong>Historical evidence sample.</strong> These are selected disclosures from 2024–2026, not a current global total. Scopes and periods differ. Do not add the figures together.</div>
    <div class="stats"><div class="stat"><strong>6</strong><span>Reporting entities</span></div><div class="stat"><strong>11</strong><span>Demand disclosures</span></div><div class="stat"><strong>Unknown</strong><span>Global total</span></div></div>
    <h2>Disclosed throughput</h2><div class="panel"><p>Separate observations, ordered by date. Bar length shows normalized trillion raw tokens/day. &gt; preserves the original “over” qualifier.</p>''' + ''.join(bars) + '''<p><small>Dates are period midpoints for Microsoft and publication anchors for run rates with unknown windows. No interpolation or extrapolation. Raw tokens are not compute equivalents; this chart is not a like-for-like provider ranking.</small></p></div>
    <h2>Evidence ledger</h2><div class="evidence-grid">''' + ''.join(cards) + '''</div><h2>Infrastructure ledger</h2><p>Stocks, additions, access announcements and plans are separate concepts. Different units are not additive. Epoch AI estimates are attributed to Josh You / Epoch AI (CC BY); they include R&amp;D and inference.</p><div class="evidence-grid">''' + ''.join(supply_cards) + '''</div><h2>What remains unknown</h2><div class="panel"><ul><li>Economic demand, willingness to pay and unmet workloads are not measured by realized processing.</li><li>Input/output split, model mix, caching and modality accounting are unknown; compute-equivalent demand is not estimated.</li><li>Microsoft’s March figure is contained in its quarterly figure. Cross-provider overlap remains unresolved.</li><li>Installed GPU stock does not establish effective available inference capacity. Training, private deployments and tightness remain unquantified.</li></ul><p>Source re-verification does not make an old observation current. No statistical confidence intervals are available.</p></div>
    <footer>Snapshot generated ''' + datetime.now(ZoneInfo('Australia/Sydney')).date().isoformat() + '''. Source verification dates: 2026-11-03 and 2026-11-04. No automatic measurement updates.<br>Observation ledger SHA-256: <code>''' + digest + '''</code><br><a href="https://github.com/MichaelMi7/global-ai-compute-monitor">Project and full methodology on GitHub</a></footer></main></body></html>'''
    path = ROOT / 'exports/global-ai-compute-monitor.html'
    path.parent.mkdir(exist_ok=True)
    path.write_text(html,encoding='utf-8')
    print(f'{path} ({path.stat().st_size:,} bytes)')
    return path

if __name__ == '__main__':
    export()
