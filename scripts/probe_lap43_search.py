"""One frozen public batch, default inspect. Never enables production search."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]

async def run(root,manifest,expected):
    from qqbot_gateway.web_policy import DEFAULTS,intent
    from qqbot_gateway.web_retrieval import Retriever,REQUEST_TIME
    from qqbot_gateway.public_network import DEFAULTS as NETWORK
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
    retriever=Retriever(cfg,network=NETWORK,root=directory)
    report=[]
    for row in queries:
        token=REQUEST_TIME.set(datetime.now(timezone.utc).isoformat())
        try:
            result=await retriever._fetch(intent(row['query'],cfg),row['query'])
            report.append(dict(query=row['query'],expectations=row,audit=retriever.last_audit,notice=result.notice,
                sources=[{k:s[k] for k in ('title','url','freshness','body_method')} for s in result.sources]))
        finally:REQUEST_TIME.reset(token)
        (directory/'result.json').write_text(json.dumps(dict(queries=report,real_model_calls=0,qq_calls=0,quality_passed=False,human_review='pending'),ensure_ascii=False,indent=2),encoding='utf-8')
    return dict(batch=str(directory),completed=len(report),quality_passed=False,human_review_required=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='store_true')
    p.add_argument('--manifest',type=Path);p.add_argument('--expected-sha256')
    a=p.parse_args()
    if not a.run:print('inspect: no network; requires three frozen queries, comparison basis and explicit --run');return
    if not a.manifest or not a.expected_sha256:p.error('frozen manifest and SHA required')
    print(json.dumps(asyncio.run(run(ROOT,a.manifest,a.expected_sha256))))
if __name__=='__main__':main()
