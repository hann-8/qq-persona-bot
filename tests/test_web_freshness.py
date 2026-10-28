"""Date evidence, worker schema, bounded search and final metadata/source integrity."""
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from qqbot_gateway.web_policy import DEFAULTS,intent,validate_web
from qqbot_gateway.web_freshness import assess,page_dates,validate
from qqbot_gateway.web_retrieval import Retriever,source_plan
from qqbot_gateway.web_extractor import WebExtractor
from qqbot_gateway.evidence_selection import sources_for_budget,manifest,validate_manifest

NOW=datetime(2026,10,28,14,0,tzinfo=timezone.utc)


def html(date='',extra=''):
    return '<html><head><title>Python release news</title>'+date+'</head><body><main><h1>Python release news</h1>'+extra+'<p>'+('Python release announcement with documented changes and fixes. '*12)+'</p></main></body></html>'


class Dates(unittest.TestCase):
    def test_meta_json_ld_main_time_and_conflicts(self):
        from lxml import html as parser
        for markup,expected in [('<meta property="article:published_time" content="2026-10-28T12:00:00Z">','meta'),
            ('<script type="application/ld+json">{"@type":"NewsArticle","datePublished":"2026-10-28"}</script>','json_ld')]:
            tree=parser.fromstring(html(markup));self.assertEqual(page_dates(tree,tree.xpath('//main')[0])['date_source'],expected)
        tree=parser.fromstring(html('', '<time datetime="2026-10-28">日期</time>'))
        self.assertEqual(page_dates(tree,tree.xpath('//main')[0])['date_source'],'main_time')
        tree=parser.fromstring(html('<meta property="article:published_time" content="2026-10-28"><meta name="date" content="2026-10-27">'))
        self.assertTrue(page_dates(tree)['date_conflict'])

    def test_missing_future_stale_precision_and_modified_not_event(self):
        base=dict(fetched_at=NOW.isoformat(),date_source='meta')
        for value,question,status in [(None,'今天新闻','unknown'),('2026-10-29','最新消息','invalid'),('2026-09-01','最新消息','stale'),
            ('2026-10-28','过去24小时新闻','unknown'),('2026-10-28T12:00:00Z','今天新闻','fresh')]:
            row=assess(base|dict(published_at=value),question,NOW);self.assertEqual(row['freshness_status'],status);validate(row)
        self.assertEqual(assess(base|dict(published_at='2026-09-01',modified_at='2026-10-28'),'最新消息',NOW)['freshness_status'],'stale')

    def test_intent_privacy_and_explicit_disabled(self):
        cfg=validate_web(dict(enabled=True,search_enabled=True))
        for text in ('查查Python最新消息','今天Python有什么新动态','最近Python更新公告','查一下Python 2026-10-28 新闻'):
            self.assertEqual(intent(text,cfg).kind,'search')
        for text in ('你现在怎么样','我最近很累','不要联网查查Python最新消息'):
            self.assertEqual(intent(text,cfg).kind,'none')
        self.assertEqual(intent('查查Python最新消息',cfg|dict(search_enabled=False)).kind,'search_disabled')
        self.assertEqual(intent('查查QQ号12345678的消息',cfg).kind,'sensitive')
        self.assertEqual(intent('查一下那个',cfg).kind,'clarify')
        self.assertFalse(DEFAULTS['search_enabled'])


class WorkerAndRetrieval(unittest.IsolatedAsyncioTestCase):
    async def test_owned_worker_schema_and_bounded_search(self):
        date=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        calls=[]
        class HTTP:
            def __init__(self,cfg,audit):pass
            async def get(self,url,**kwargs):
                calls.append(url)
                if kwargs.get('rss'):
                    items=''.join('<item><title>Python release news</title><link>https://www.python.org/news/'+str(i)+'</link></item>' for i in range(5))
                    return '<rss><channel>'+items+'</channel></rss>',url,'application/rss+xml'
                return html('<meta property="article:published_time" content="'+date+'">'),url,'text/html'
        with tempfile.TemporaryDirectory() as folder:
            cfg=validate_web(dict(enabled=True,search_enabled=True))
            retriever=Retriever(cfg,http_factory=HTTP,root=folder)
            result=await retriever.retrieve('Python最新消息')
            self.assertIsNone(result.notice);self.assertEqual(len(calls),3);self.assertEqual(len(result.sources),2)
            rows=sources_for_budget(result.sources,6000,4000,'excerpt','Python最新消息')
            proof=manifest(rows);validate_manifest(proof,dict(web_anchor='Python最新消息'))
            self.assertEqual(proof[0]['freshness']['freshness_status'],'fresh')
            with self.assertRaises(ValueError):validate_manifest([proof[0]|dict(freshness=proof[0]['freshness']|dict(date_source='model'))],dict(web_anchor='Python最新消息'))
            output=dict(max_reply_chars=1800)
            plan=source_plan('本次材料记载了版本更新。',rows,output,'Python最新消息')
            self.assertIn('北京时间',plan.canonical_text)
            for row in rows:self.assertIn(row['url'],plan.canonical_text)
            self.assertEqual(retriever.last_audit['search_calls'],1)
    async def test_no_date_no_model_material(self):
        class HTTP:
            def __init__(self,cfg,audit):pass
            async def get(self,url,**kwargs):
                if kwargs.get('rss'):return '<rss><channel><item><title>Python news</title><link>https://www.python.org/news/1</link></item></channel></rss>',url,'application/rss+xml'
                return html(),url,'text/html'
        with tempfile.TemporaryDirectory() as folder:
            result=await Retriever(dict(enabled=True,search_enabled=True),http_factory=HTTP,root=folder).retrieve('Python最新消息')
            self.assertFalse(result.sources);self.assertIn('无法核实',result.notice)


if __name__=='__main__':unittest.main()
