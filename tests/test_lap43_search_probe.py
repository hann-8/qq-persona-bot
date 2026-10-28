"""Batch reservation, transport accounting and unchanged production gate; no network."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from scripts.probe_lap43_search import run
from qqbot_gateway.web_retrieval import Retriever
from qqbot_gateway.web_policy import DEFAULTS,SEARCH_QUALITY_PASSED

class Batch(unittest.IsolatedAsyncioTestCase):
    async def test_budget_audit_and_no_second_attempt(self):
        spec=json.loads((ROOT/'reports/lap-43-stage-b-manifest.json').read_text(encoding='utf-8'))
        async def fake_get(client,url,**kwargs):
            client.audit.http_calls+=1
            if kwargs.get('rss'):
                return ('<rss><channel>'+''.join('<item><title>NASA Python Sudan announcement news</title><link>https://'+host+'/'+str(i)+'</link></item>' for i,host in enumerate(['www.nasa.gov','www.python.org','news.un.org']))+'</channel></rss>',url,'text/xml')
            return ('NASA Python Sudan public announcement news facts '*20,url,'text/plain')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);manifest=root/'frozen.json'
            manifest.write_text(json.dumps(spec),encoding='utf-8')
            sha=hashlib.sha256(manifest.read_bytes()).hexdigest()
            with patch('qqbot_gateway.public_http.PublicHTTP.get',fake_get):
                result=await run(root,manifest,sha)
                with self.assertRaises(FileExistsError):await run(root,manifest,sha)
            report=json.loads((Path(result['batch'])/'result.json').read_text(encoding='utf-8'))
            self.assertEqual(len(report['queries']),3)
            self.assertEqual(sum(q['audit']['search_calls'] for q in report['queries']),3)
            self.assertLessEqual(sum(q['audit']['fetch_calls'] for q in report['queries']),6)
            for q in report['queries']:
                self.assertFalse(q['sources']) # undated bodies must not qualify
                self.assertTrue(q['extracted_pages'])
                self.assertTrue(all(p['freshness']['freshness_status']=='unknown' for p in q['extracted_pages']))
                self.assertEqual(sum(e['http_attempts'] for e in q['transport_events']),q['audit']['http_calls'])
                self.assertTrue(all(e['doh_attempts']==e['redirect_hops']==0 for e in q['transport_events']))
            self.assertFalse(report['quality_passed'])
            self.assertFalse(SEARCH_QUALITY_PASSED)
            with patch('qqbot_gateway.public_http.PublicHTTP.get',side_effect=AssertionError('production bypass')):
                gated=await Retriever(dict(DEFAULTS,enabled=True,search_enabled=True)).retrieve('搜索Python最新版本')
                self.assertTrue(gated.notice)
    async def test_changed_manifest_rejected_before_attempt(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'frozen.json';p.write_text('{}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'FROZEN_MANIFEST_CHANGED'):
                await run(Path(temp),p,'0'*64)
            self.assertFalse((Path(temp)/'state').exists())

if __name__=='__main__':unittest.main()
