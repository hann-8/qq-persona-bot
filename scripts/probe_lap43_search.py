"""One frozen public batch, default inspect. Never enables production search."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import time
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]

async def run(root,manifest,expected):
    from qqbot_gateway.web_policy import DEFAULTS,intent
    from qqbot_gateway.web_retrieval import Retriever,REQUEST_TIME
    from qqbot_gateway.public_network import DEFAULTS as NETWORK, failure_status
    from qqbot_gateway.public_http import PublicHTTP
    from qqbot_gateway.web_freshness import facts
    raw=manifest.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('FROZEN_MANIFEST_CHANGED')
    spec=json.loads(raw)
    if set(spec)!={'queries','network'} or spec['network']!=NETWORK:raise ValueError('DEFAULT_NETWORK_ONLY')
    queries=spec['queries']
    if not isinstance(queries,list) or len(queries)!=3:raise ValueError('EXACTLY_THREE_QUERIES')
    cfg=dict(DEFAULTS,enabled=True,search_enabled=False)
    for row in queries:
        if set(row)!={'query','expected_object','window','comparison_basis'} or any(not isinstance(v,str) or not 1<=len(v)<=240 for v in row.values()):raise ValueError('FREEZE_EXPECTATIONS_REQUIRED')
        if intent(row['query'],cfg).kind!='search':raise ValueError('PUBLIC_QUERY_REQUIRED')
    directory=root/'state/lap43-search'/expected
    directory.mkdir(parents=True,exist_ok=True)
    with (directory/'attempt.json').open('x',encoding='utf-8') as f:json.dump(dict(manifest_sha256=expected,state='reserved'),f)
    events=[]; pages=[]
    class ObservedHTTP(PublicHTTP):
        # Same transport and network rules. Instrument only this batch instance.
        def __init__(self,cfg,audit):
            super().__init__(cfg,audit)
            resolve=self.resolver.resolve
            async def observed_resolve(*args,**kwargs):
                events.append(dict(kind='resolution',resolver=NETWORK['resolver']))
                return await resolve(*args,**kwargs)
            self.resolver.resolve=observed_resolve
        async def get(self,url,**kwargs):
            started=time.monotonic()
            before=(self.audit.http_calls,self.audit.redirect_hops,self.audit.dns_calls)
            event=dict(kind='search' if kwargs.get('rss') else 'page',url=url)
            events.append(event)
            try:
                result=await super().get(url,**kwargs)
                event.update(status='ok',final_url=result[1])
                return result
            except BaseException as error:
                event.update(failure_status(error))
                raise
            finally:
                event.update(elapsed_seconds=round(time.monotonic()-started,3),
                    http_attempts=self.audit.http_calls-before[0],
                    redirect_hops=self.audit.redirect_hops-before[1],
                    doh_attempts=self.audit.dns_calls-before[2])
    class ObservedRetriever(Retriever):
        async def extract(self,text,url,mime):
            source=await super().extract(text,url,mime)
            # Bounded public excerpt/hash before production date/relevance filtering.
            pages.append(dict(url=url,title=source['title'],body_method=source['body_method'],
                body_chars=len(source['text']),body_sha256=hashlib.sha256(source['text'].encode()).hexdigest(),
                excerpt=source['text'][:1200],
                freshness=facts(source.get('_date_candidates',[]),REQUEST_TIME.get(),source['fetched_at'],current_query)))
            return source
    retriever=ObservedRetriever(cfg,network=NETWORK,root=directory,http_factory=ObservedHTTP)
    report=[]
    for row in queries:
        current_query=row['query'];events.clear();pages.clear()
        token=REQUEST_TIME.set(datetime.now(timezone.utc).isoformat())
        try:
            result=await retriever._fetch(intent(row['query'],cfg),row['query'])
            report.append(dict(query=row['query'],expectations=row,audit=retriever.last_audit,notice=result.notice,expired=result.expired,
                transport_events=list(events),extracted_pages=list(pages),
                sources=[{k:s[k] for k in ('title','url','freshness','body_method')} for s in result.sources]))
        finally:REQUEST_TIME.reset(token)
        (directory/'result.json').write_text(json.dumps(dict(manifest_sha256=expected,queries=report,real_model_calls=0,qq_calls=0,quality_passed=False,human_review='pending'),ensure_ascii=False,indent=2),encoding='utf-8')
    (directory/'completed.json').write_text(json.dumps(dict(completed=len(report),quality_passed=False)),encoding='utf-8')
    return dict(batch=str(directory),completed=len(report),quality_passed=False,human_review_required=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='store_true')
    p.add_argument('--manifest',type=Path);p.add_argument('--expected-sha256')
    a=p.parse_args()
    if not a.run:print('inspect: no network; requires three frozen queries, comparison basis and explicit --run');return
    if not a.manifest or not a.expected_sha256:p.error('frozen manifest and SHA required')
    print(json.dumps(asyncio.run(run(ROOT,a.manifest,a.expected_sha256))))
if __name__=='__main__':main()
