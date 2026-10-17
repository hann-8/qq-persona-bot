"""Only three public queries; no model, QQ, secrets, or bot lifecycle."""
import asyncio
import json
from pathlib import Path
import sys
from urllib.parse import urlencode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from qqbot_gateway.web_retrieval import PublicHTTP, Audit, WebFailure, parse_rss, extract
from qqbot_gateway.web_policy import DEFAULTS


async def main():
    rows=[]
    for query in ('中国长江长度是多少','2026年10月17日 新闻','site:docs.ollama.com api chat'):
        audit=Audit(search_calls=1);http=PublicHTTP(DEFAULTS,audit);row=dict(query=query)
        try:
            async with asyncio.timeout(15):
                text,_,_=await http.get('https://cn.bing.com/search?'+urlencode(dict(q=query,format='rss')),rss=True)
                items=parse_rss(text,query,DEFAULTS)
                row['candidates']=[{k:x[k] for k in ('title','url','reported_date')} for x in items]
                row['readable']=[]
                for item in items[:2]:
                    try:
                        text,url,mime=await http.get(item['url'])
                        page=extract(text,url,mime,DEFAULTS)
                        row['readable'].append({k:page[k] for k in ('title','url','published_at','fetched_at')})
                    except Exception as error:row.setdefault('read_errors',[]).append(type(error).__name__)
        except Exception as error:row['error']=type(error).__name__;row['reason']=str(error) if isinstance(error,WebFailure) else 'transport_or_parse'
        row['audit']=vars(audit);rows.append(row)
    path=Path(__file__).resolve().parents[1]/'reports/lap-18-public-probe.json'
    path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(rows,ensure_ascii=False,indent=2))


if __name__=='__main__':asyncio.run(main())
