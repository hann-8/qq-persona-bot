"""Fixed zero-model public batch. No local config/CA/proxy/DNS/credentials read.

Three static pages per explicit mode, three original query categories (system),
seven domain classifications. Each HTTP item <=5s/1MiB/2 redirects, no retries.
Only domain/status/counts/metrics are saved; page/query result text stays in RAM.
"""
import asyncio
from datetime import datetime,timezone
import json
from pathlib import Path
import socket
import sys
import time
from urllib.parse import urlencode,urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from qqbot_gateway.public_http import PublicHTTP,PublicResolver,Audit,WebFailure,public_ip
from qqbot_gateway.web_retrieval import Retriever,parse_rss
from qqbot_gateway.web_policy import DEFAULTS,SEARCH_QUALITY_PASSED

ROOT=Path(__file__).resolve().parents[1]
PAGES=('https://www.runoob.com/python3/python3-tutorial.html',
       'https://docs.python.org/zh-cn/3/tutorial/introduction.html',
       'https://docs.python.org/3/library/asyncio.html')
DOMAINS=('cn.bing.com','docs.python.org','www.bilibili.com','api.bilibili.com','gchat.qpic.cn','aisubtitle.hdslb.com','www.runoob.com')


def error_status(error):
    from qqbot_gateway.public_network import failure_status
    return failure_status(error)


async def main():
    rows=[];dns=[]
    for host in DOMAINS:
        try:
            addresses=await asyncio.wait_for(asyncio.get_running_loop().getaddrinfo(host,443,type=socket.SOCK_STREAM),3)
            addresses={r[4][0] for r in addresses};good=0
            for ip in addresses:
                try:public_ip(ip);good+=1
                except (WebFailure,ValueError):pass
            dns.append(dict(domain=host,addresses=len(addresses),public=good,nonpublic=len(addresses)-good))
        except (OSError,TimeoutError):dns.append(dict(domain=host,status='dns_failed'))
    for mode in ('system','cloudflare_doh'):
        for index,url in enumerate(PAGES):
            cfg=DEFAULTS|dict(enabled=True,timeout_seconds=5,public_network=dict(resolver=mode,ca_bundle_file=None))
            audit=Audit();http=PublicHTTP(cfg,audit);row=dict(kind='page',sample=index+1,domain=urlsplit(url).hostname,resolver=mode)
            started=time.monotonic()
            try:
                async with asyncio.timeout(5):
                    text,final,mime=await http.get(url)
                    reader=Retriever(cfg)
                    result=await reader.extract(text,final,mime)
                    row.update(status='body_received_quality_review_required',body_bytes=len(result['text'].encode()),mime=mime)
                    if reader.extractor:row['worker']=reader.extractor.last_metrics;reader.extractor.temporary.cleanup()
            except Exception as error:row.update(error_status(error))
            row.update(audit=vars(audit),elapsed_seconds=round(time.monotonic()-started,3));rows.append(row)
    for category,query in (('fact','中国长江长度是多少'),('dated_news','2026年10月21日 新闻'),('documentation','site:docs.ollama.com api chat')):
        audit=Audit(search_calls=1);http=PublicHTTP(DEFAULTS|dict(timeout_seconds=5),audit)
        row=dict(kind='search',category=category,domain='cn.bing.com',resolver='system')
        try:
            async with asyncio.timeout(5):
                text,_,_=await http.get('https://cn.bing.com/search?'+urlencode(dict(q=query,format='rss')),rss=True)
                items=parse_rss(text,query,DEFAULTS)
                row.update(status='candidates_only_quality_not_passed',candidate_count=len(items))
        except Exception as error:row.update(error_status(error))
        row['audit']=vars(audit);rows.append(row)
    result=dict(timestamp=datetime.now(timezone.utc).isoformat(),network_state='network_unverified',
                limits=dict(page_attempts=6,search_attempts=3,max_http_hops=27,max_seconds_per_item=5,
                            max_response_bytes=1048576,doh_bytes=32768,doh_seconds=3),
                system_dns=dns,items=rows,search_quality_passed=SEARCH_QUALITY_PASSED,
                real_model_calls=0,real_qq_outputs=0,machine_config_changes=0)
    path=ROOT/'reports/lap-18-B-public-probe.json'
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


async def diagnose_doh():
    path=ROOT/'reports/lap-18-B-public-probe.json';result=json.loads(path.read_text(encoding='utf-8'))
    audit=Audit();started=time.monotonic()
    try:
        async with asyncio.timeout(5):await PublicHTTP(DEFAULTS|dict(public_network={'resolver':'cloudflare_doh'}),audit).get(PAGES[2])
        status=dict(status='received')
    except Exception as error:status=error_status(error)
    result['nested_doh_diagnostic']=dict(domain='docs.python.org',resolver='cloudflare_doh',audit=vars(audit),
        elapsed_seconds=round(time.monotonic()-started,3),**status)
    result['limits']['additional_doh_diagnostic_attempts']=1
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result['nested_doh_diagnostic']))


if __name__=='__main__':asyncio.run(diagnose_doh() if sys.argv[1:]==['--diagnose-doh'] else main())
