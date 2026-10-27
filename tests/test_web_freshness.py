"""Frozen clock, real owned HTML worker, fake public transport; no network."""
import asyncio
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from qqbot_gateway.web_freshness import *
from qqbot_gateway.web_policy import DEFAULTS,intent,validate_web
NOW='2026-10-27T11:00:00+00:00'
def date(value,kind='published',source='meta'):return dict(kind=kind,source=source,value=value)

class Dates(unittest.TestCase):
    def test_windows(self):
        self.assertEqual(facts([date('2026-10-27')],NOW,NOW,'今天新闻')['freshness_status'],'fresh')
        for value,status in [('2026-10-20','stale'),('2026-10-28','invalid'),('2026-10-32','invalid')]:
            self.assertEqual(facts([date(value)],NOW,NOW,'今天新闻')['freshness_status'],status)
        self.assertEqual(facts([date('2026-10-27T12:00:00+08:00')],NOW,NOW,'过去24小时新闻')['freshness_status'],'fresh')
        self.assertEqual(facts([date('2026-10-27')],NOW,NOW,'过去24小时新闻')['freshness_status'],'unknown')
        self.assertEqual(facts([date('2026-10-26'),date('2026-10-27')],NOW,NOW)['freshness_status'],'conflict')
        self.assertEqual(facts([date('2026-10-27',kind='modified')],NOW,NOW)['freshness_status'],'unknown')
        self.assertEqual(facts([date('2025-10-27')],NOW,NOW,'最新发布版本')['freshness_status'],'version_dated')
        with self.assertRaises(ValueError):window('近31天新闻',NOW)
    def test_intents(self):
        cfg=validate_web(dict(enabled=True))
        self.assertFalse(cfg['search_enabled']);self.assertEqual(cfg['freshness_days'],7)
        for q,kind in [('最新消息','search'),('有什么新动态','search'),('我最近很累','none'),('你现在怎么样','none'),('不要联网查最新消息','none'),('查一下那个','clarify'),('搜索QQ号123456','sensitive'),('搜索2026-10-27官方公告','search')]:
            with self.subTest(q=q):self.assertEqual(intent(q,cfg).kind,kind)
        self.assertEqual(intent('最新消息',dict(cfg,trigger='explicit')).kind,'none')
        for v in (True,0,31):
            with self.assertRaises(ValueError):validate_web(dict(freshness_days=v))
    def test_topic_bound_source_preference(self):
        from qqbot_gateway.web_retrieval import first_party
        self.assertTrue(first_party('Python最新版本',dict(url='https://www.python.org/downloads/',title='Python releases',text='Python')))
        self.assertFalse(first_party('Python最新版本',dict(url='https://github.com/other/project',title='Python',text='Python')))
        self.assertFalse(first_party('Python最新版本',dict(url='https://www.python.org/',title='other',text='other')))
    def test_manifest_suffix(self):
        from qqbot_gateway.evidence_selection import sources_for_budget,manifest,validate_manifest
        from qqbot_gateway.web_retrieval import source_plan
        from qqbot_gateway.reply_plan import DEFAULTS as OUTPUT
        row=dict(url='https://example.com/article',title='Public',status='body',text='public facts '*100,published_at='2026-10-27',freshness=facts([date('2026-10-27')],NOW,NOW))
        selected=sources_for_budget([row],6000,4000,'excerpt','news');m=manifest(selected);validate_manifest(m,dict(web_anchor='news'))
        damaged=copy.deepcopy(m);damaged[0]['freshness']['published_at']='2020-01-01'
        with self.assertRaises(ValueError):validate_manifest(damaged,dict(web_anchor='news'))
        text=source_plan('Public answer',selected,OUTPUT,'news').canonical_text
        self.assertIn('北京时间',text);self.assertIn('2026-10-27',text);self.assertIn(row['url'],text)

class Worker(unittest.IsolatedAsyncioTestCase):
    async def test_real_worker_protocol(self):
        from qqbot_gateway.web_extractor import WebExtractor
        body='<article><h1>Public news</h1><p>'+('public body facts '*30)+'</p><p>'+('details '*30)+'</p><time datetime="2026-10-27">today</time></article>'
        with tempfile.TemporaryDirectory() as t:
            worker=WebExtractor(Path(t))
            for metadata,source in [('<meta property="article:published_time" content="2026-10-27T12:00:00+08:00">','meta'),('<script type="application/ld+json">{"@type":"NewsArticle","datePublished":"2026-10-27"}</script>','jsonld'),('','time')]:
                result=await worker.extract('<html><head>'+metadata+'</head><body>'+body+'</body></html>')
                validate_candidates(result['date_candidates']);self.assertEqual(result['date_candidates'][0]['source'],source)
                self.assertTrue(worker.last_metrics['cleanup']);self.assertTrue(worker.last_metrics['exited'])
    async def test_transport_gates_and_freshness(self):
        from qqbot_gateway.web_retrieval import Retriever,REQUEST_TIME
        class HTTP:
            calls=[]
            def __init__(self,cfg,audit):pass
            async def get(self,url,rss=False):
                self.calls.append((url,rss))
                if rss:return ('<rss><channel>'+''.join('<item><title>public news</title><link>https://example.com/'+str(i)+'</link></item>' for i in range(5))+'</channel></rss>',url,'text/xml')
                value='2026-10-27' if url.endswith('/0') else '2020-01-01'
                return '<meta property="article:published_time" content="'+value+'"><article><h1>public news</h1><p>'+('public news facts '*30)+'</p><p>'+('public details '*30)+'</p></article>',url,'text/html'
        with tempfile.TemporaryDirectory() as t:
            r=Retriever(dict(enabled=True,search_enabled=True),http_factory=HTTP,root=Path(t))
            result=await r.retrieve('最新新闻');self.assertTrue(result.notice);self.assertFalse(HTTP.calls)
            token=REQUEST_TIME.set(NOW)
            try:
                with patch('qqbot_gateway.web_retrieval.SEARCH_QUALITY_PASSED',True):result=await r.retrieve('public最新news新闻')
            finally:REQUEST_TIME.reset(token)
            self.assertEqual(len(HTTP.calls),3);self.assertEqual(len(result.sources),1)
            self.assertEqual(result.sources[0]['freshness']['requested_at'],NOW)
if __name__=='__main__':unittest.main()
