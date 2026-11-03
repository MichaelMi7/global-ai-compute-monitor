"""Check public source availability/change; never extract or promote measurements."""
import argparse
from datetime import datetime,timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.parse import urlparse
from urllib.request import Request,urlopen,build_opener,HTTPRedirectHandler
from .model import ROOT,read_ledger

TRUSTED_HOSTS={'blog.google','www.sec.gov','openai.com','openrouter.ai','www.nda.gov.cn','epoch.ai','www.anthropic.com','engineering.fb.com','www.microsoft.com','fireworks.ai'}
MAX_BYTES=2_000_000

def check_url(url):
    parts=urlparse(url)
    if parts.scheme!='https' or parts.hostname not in TRUSTED_HOSTS or parts.username or parts.password or parts.port not in (None,443):
        raise ValueError('Source URL not in curated HTTPS allowlist')

class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        check_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

class Text(HTMLParser):
    def __init__(self): super().__init__();self.skip=0;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'): self.skip+=1
    def handle_endtag(self,tag):
        if tag in ('script','style'): self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip: self.parts.append(data)

def text_hash(html):
    parser=Text();parser.feed(html)
    normalized=re.sub(r'\s+',' ',' '.join(parser.parts)).strip()
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def fetch(url):
    check_url(url)
    request=Request(url,headers={'User-Agent':'GlobalAIComputeMonitor/0.2 (+https://github.com/MichaelMi7/global-ai-compute-monitor)'})
    with build_opener(SafeRedirect()).open(request,timeout=8) as response:
        check_url(response.url)
        content=response.read(MAX_BYTES+1)
        if len(content)>MAX_BYTES: raise ValueError('Source exceeds size limit')
        return content.decode(response.headers.get_content_charset() or 'utf-8',errors='replace')

def check_sources(sources,baseline=None,fetcher=fetch,delay=0):
    baseline=baseline or {};results=[]
    for source in sources:
        row={'source_id':source['source_id'],'url':source['url']}
        try:
            check_url(source['url']);digest=text_hash(fetcher(source['url']))
            previous=baseline.get(source['source_id'])
            row.update(status='changed_review_required' if previous and previous!=digest else ('unchanged' if previous else 'new_fingerprint'),text_sha256=digest)
        except Exception as error:
            row.update(status='unavailable',error=f'{type(error).__name__}: {error}')
        results.append(row)
        if delay: time.sleep(delay)
    return {'checked_at_utc':datetime.now(timezone.utc).isoformat(),'policy':'Availability/content fingerprints only; no automatic measurement or verification-date updates. Navigation edits may trigger changes.','results':results}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='reports/source-check.json')
    parser.add_argument('--baseline',default='data/source_fingerprints.json');args=parser.parse_args()
    baseline_path=Path(args.baseline)
    baseline=json.loads(baseline_path.read_text()) if baseline_path.exists() else {}
    report=check_sources(read_ledger()['sources'],baseline,delay=.2)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    from collections import Counter
    print(dict(Counter(r['status'] for r in report['results'])))
if __name__=='__main__': main()
