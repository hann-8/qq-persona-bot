"""Synthetic bounded JSON/selection/cache resource observation, zero network/model."""
import asyncio
import json
from pathlib import Path
import sys
import time
import tracemalloc
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
from test_bilibili import HTTP,BVID,CDN,subtitle_body
from qqbot_gateway.bilibili_subtitles import Subtitles,normalize,parsed,encoded
from qqbot_gateway.bilibili_policy import DEFAULTS
from qqbot_gateway.web_policy import DEFAULTS as WEB
from qqbot_gateway.evidence_selection import sources_for_budget
import psutil
async def main():
    process=psutil.Process();baseline=process.memory_info().rss;tracemalloc.start();started=time.perf_counter()
    body={'body':[{'from':i*.1,'to':i*.1+.09,'content':'Synthetic fact %05d'%i} for i in range(10000)]}
    payload=encoded(body);assert len(payload)<=1048576
    rows=normalize(parsed(payload),1000);parse_seconds=time.perf_counter()-started
    HTTP.calls=[];HTTP.delay=0;HTTP.need=False;HTTP.code=0;HTTP.body=subtitle_body(True)
    svc=Subtitles(DEFAULTS|{'enabled':True},WEB|{'enabled':True},http_factory=HTTP)
    source=await svc.get(((BVID,1),),'synthetic-group');start_select=time.perf_counter()
    selected=sources_for_budget([source],6000,6000,'excerpt','总结');selection_seconds=time.perf_counter()-start_select
    before=len(HTTP.calls);again=await svc.get(((BVID,1),),'synthetic-group')
    assert len(HTTP.calls)==before and source==again
    current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    value=dict(passed=True,fixture_rows=len(rows),fixture_json_bytes=len(payload),parse_normalize_seconds=round(parse_seconds,6),
               selection_seconds=round(selection_seconds,6),evidence_bytes=len(encoded({'partial':False,'sources':selected})),
               cache_entries=len(svc.cache),cache_accounted_bytes=sum(v[1] for v in svc.cache.values()),cache_payload_is_bytes=all(isinstance(v[3],bytes) for v in svc.cache.values()),
               tracemalloc_peak_bytes=peak,rss_baseline_bytes=baseline,rss_after_bytes=process.memory_info().rss,
               new_runtime_dependencies=0,idle_workers=0,real_network_requests=0,real_model_calls=0,real_qq_outputs=0)
    (ROOT/'reports/lap-06-resources.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(value,ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
