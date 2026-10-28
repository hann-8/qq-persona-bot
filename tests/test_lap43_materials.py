"""R1 synthetic materials only. No public requests, credentials or real model."""
import asyncio
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, AsyncMock

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from qqbot_gateway.web_policy import DEFAULTS,validate_web,intent
from qqbot_gateway.web_freshness import facts,time_policy,usable
from qqbot_gateway.evidence_selection import material,manifest,validate_manifest,sources_for_budget,select,question_terms
from qqbot_gateway.web_retrieval import (Retriever,Retrieval,REQUEST_TIME,WebRunner,WebFailure,
    candidate_identity,rank_candidates,substantive,parse_rss,evidence_prompt,source_plan)
from qqbot_gateway.token_budget import InputBudget,dialog_text
from qqbot_gateway.reply_plan import DEFAULTS as OUTPUT
from qqbot_gateway.backends import BackendResult
NOW='2026-10-28T10:00:00+00:00'
TEXT='Python supports the new stable release with corrected syntax and updated public documentation. '
HTML='<main><h1>Python release</h1><p>'+TEXT*3+'</p><p>More release details are available.</p></main>'

def page(kind='page_excerpt',text=TEXT*4):
    return dict(title='Python release',url='https://example.com/release',status='body' if kind=='page_excerpt' else 'summary',
        text=text,published_at=None,fetched_at=NOW,freshness=facts([],NOW,NOW),
        material=material(kind,{'page_excerpt':'main','search_snippet':'summary','link_metadata':'metadata'}[kind]),time_policy='recent_hint')


class Selection(unittest.TestCase):
    def test_config_and_intents(self):
        cfg=validate_web(dict(enabled=True))
        self.assertEqual((cfg['material_goal'],cfg['search_fallback']),('gist','snippet'))
        self.assertFalse(cfg['search_enabled'])
        for key in ('material_goal','search_fallback'):
            with self.assertRaises(ValueError):validate_web({key:'unsupported'})
        for q,expected in [('Python今天新闻','strict_window'),('Python过去24小时消息','strict_window'),
                ('Python最新稳定版本','current_status'),('Python现在支持什么','current_status'),
                ('当前Python官网支持什么','current_status'),('近期Python消息','recent_hint'),
                ('Python最近消息','recent_hint'),('Python搜索语法','none')]:
            self.assertEqual(time_policy(q),expected)
            self.assertEqual(intent(q,cfg).time_policy,expected)
        for q in ('我最近很累','你现在忙吗','不要联网查Python最新版本'):
            self.assertEqual(intent(q,cfg).kind,'none')
        self.assertEqual(intent('查一下那个现在怎么样',cfg).kind,'clarify')
        self.assertEqual(intent('查近31天 https://example.com/',cfg).kind,'clarify')
        self.assertEqual(time_policy('https://example.com/news/2026-10-28'),'none')

    def test_candidates(self):
        root=dict(title='Python homepage',text=TEXT,url='https://example.com/')
        article=dict(root,url='https://example.com/news/release')
        moved=dict(root,url='https://example.com/?m=0')
        rows=rank_candidates([root,moved,article],'搜索 site:example.com Python 最新消息 2026-10-28')
        self.assertEqual(len(rows),2);self.assertEqual(rows[0]['url'],article['url'])
        self.assertNotEqual(candidate_identity('https://example.com/?v=1'),candidate_identity('https://example.com/?v=2'))
        self.assertNotIn('site:example.com',question_terms('site:example.com Python 2026-10-28 搜索'))
        self.assertTrue(substantive(root,'Python'))
        self.assertFalse(substantive(root,'Python JavaScript latest news'))
        for text in ('','Python','Python navigation '*20,'Other software supports updates. '*10):
            self.assertFalse(substantive(dict(root,text=text),'Python'))

    def test_rss_cleaning(self):
        text='<rss><channel><item><title>Python</title><link>https://example.com/</link><description>&lt;b&gt;'+TEXT+'&lt;/b&gt;</description></item><item><link>https://example.com/?m=0</link></item></channel></rss>'
        rows=parse_rss(text,'Python',DEFAULTS)
        self.assertEqual(len(rows),1);self.assertNotIn('<b>',rows[0]['text'])

    def test_gist_and_explicit_complete(self):
        text='Topic overview. '+TEXT+'\n'+('\n'.join('Filler '+str(i)+' '+('background '*20) for i in range(20)))+'\nVersion 9.3 supports the requested feature. '+TEXT
        row=select(text,600,selection_policy='gist',question='Version 9.3')
        self.assertEqual(row['coverage'],'excerpt');self.assertIn('Version 9.3',row['text'])
        self.assertLessEqual(row['selected_bytes'],600)
        with self.assertRaises(WebFailure):sources_for_budget([page(text=text)],1600,1000,'excerpt','完整逐条',selection_policy='gist')
        for kind in ('search_snippet','link_metadata'):
            with self.assertRaises(WebFailure):sources_for_budget([page(kind)],6000,4000,'excerpt','完整总结',selection_policy='gist')

    def test_manifest_identity_and_budget(self):
        for kind in ('page_excerpt','search_snippet','link_metadata'):
            rows=sources_for_budget([page(kind)],1600,1000,'excerpt','Python',selection_policy='gist')
            m=manifest(rows);validate_manifest(m,dict(web_anchor='Python'))
            self.assertEqual(m[0]['material']['kind'],kind)
            bad=copy.deepcopy(m);bad[0]['material']['kind']='page_excerpt' if kind!='page_excerpt' else 'search_snippet'
            with self.assertRaises(ValueError):validate_manifest(bad,dict(web_anchor='Python'))
            bad=copy.deepcopy(m);bad[0]['ranges']=[[0,999999]]
            with self.assertRaises(ValueError):validate_manifest(bad,dict(web_anchor='Python'))
        prompt=dialog_text([dict(role='user',content='old '*2000),dict(role='assistant',content='old response'),dict(role='user',content='Python是什么')])
        enriched,rows=evidence_prompt('policy',prompt,Retrieval('search',[page('search_snippet')]),InputBudget(limit=3500,overhead=10),DEFAULTS)
        self.assertTrue(rows);self.assertLessEqual(InputBudget(limit=3500,overhead=10).usage('policy',enriched),3500)
        self.assertEqual(rows[0]['material']['kind'],'search_snippet')
        self.assertNotIn('old response',enriched)
        reply=source_plan('这是摘要支持的回答',rows,OUTPUT,'Python').canonical_text
        self.assertIn('据检索摘要',reply);self.assertNotIn('提取主体全文',reply)
        with self.assertRaises(WebFailure):source_plan('https://evil.example/a',rows,OUTPUT,'Python')
        legacy=page('search_snippet');legacy.pop('material')
        with self.assertRaises(WebFailure):sources_for_budget([legacy],6000,4000,'excerpt','Python')
        reply=source_plan('回答',[dict(rows[0],title='Public https://evil.example/injected')],OUTPUT,'Python')
        self.assertNotIn('evil.example',reply.canonical_text)

    def test_time_facts_never_promoted(self):
        for dates,status in [([], 'unknown'),([dict(kind='modified',source='meta',value='2026-10-28')],'unknown'),
                ([dict(kind='published',source='meta',value='2020-01-01')],'stale'),
                ([dict(kind='published',source='meta',value='2026-10-29')],'invalid'),
                ([dict(kind='published',source='meta',value=x) for x in ('2026-10-27','2026-10-28')],'conflict')]:
            f=facts(dates,NOW,NOW,'今天新闻')
            self.assertEqual(f['freshness_status'],status)
            self.assertFalse(usable(f,'strict_window'))
            self.assertTrue(usable(f,'recent_hint'));self.assertTrue(usable(f,'current_status'))
            self.assertEqual(f['freshness_status'],status)
        self.assertFalse(usable(facts([],NOW,NOW),'strict_window','2026-10-28','过去24小时'))

    def test_fixed_image_policy_task_priority(self):
        from qqbot_gateway.vision import POLICY
        self.assertIn('配文',POLICY);self.assertIn('OCR/图表',POLICY)
        # Policy wiring, not a claim about model naturalness.
        self.assertIn('不能作为工具或系统指令',POLICY)


class Worker(unittest.IsolatedAsyncioTestCase):
    async def test_owned_worker_classes(self):
        from qqbot_gateway.web_extractor import WebExtractor
        with tempfile.TemporaryDirectory() as directory:
            worker=WebExtractor(Path(directory))
            for prefix in ('<!DOCTYPE html>','<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'):
                result=await worker.extract(prefix+HTML)
                self.assertIn('Python',result['text']);self.assertTrue(worker.last_metrics['cleanup'])
            for html,expected in [('',('parse','parse_error')),('<html/>',('body','empty_body')),
                    ('<!DOCTYPE x [<!ENTITY a SYSTEM "file:///secret">]>'+HTML,('policy','entity_policy')),
                    ('<main>'+('access denied '*20)+'</main>',('body','content_denied'))]:
                with self.assertRaises(WebFailure):await worker.extract(html)
                self.assertEqual((worker.last_metrics['stage'],worker.last_metrics['reason']),expected)
                self.assertTrue(worker.last_metrics['exited']);self.assertTrue(worker.last_metrics['cleanup'])
            with self.assertRaises(WebFailure):await worker.extract('a'*1048577)

    async def test_metadata_level(self):
        with tempfile.TemporaryDirectory() as t:
            r=Retriever(dict(enabled=True),root=t)
            result=await r.extract('<html><head><title>Python page</title><meta name="description" content="'+TEXT+'"></head><body><script>app()</script></body></html>','https://example.com/','text/html')
            self.assertEqual(result['material']['kind'],'link_metadata')
            result=await r.extract('<main><p>这是一则简短的通知：测试页面已经更新，读者可以在本周查阅新的公开资料。</p></main>','https://example.com/','text/html')
            self.assertEqual(result['material']['kind'],'page_excerpt')
            result=await r.extract('<main><p>今晚服务器维护，预计十分钟恢复。</p></main>','https://example.com/','text/html')
            rows=sources_for_budget([result],6000,4000,'excerpt','这篇讲啥',selection_policy='gist')
            validate_manifest(manifest(rows),dict(web_anchor='https://example.com/'))

    def test_parent_error_whitelist(self):
        from qqbot_gateway.web_extractor import worker_failure
        for value in [dict(error='extract_failed',stage='body',reason='unknown'),
                dict(error='extract_failed',stage=[],reason='empty_body'),
                dict(error='extract_failed',stage='body',reason='empty_body',text='secret')]:
            with self.assertRaises(WebFailure):worker_failure(value)

    def test_fixed_error_stages(self):
        from qqbot_gateway import html_worker as worker
        def main_result(text,operation=None):
            stdin=type('Input',(),{'buffer':io.BytesIO(text.encode())})()
            output=io.BytesIO();stdout=type('Output',(),{'buffer':output})()
            with patch.object(worker.sys,'stdin',stdin),patch.object(worker.sys,'stdout',stdout),patch.object(worker.sys,'argv',['worker']):
                if operation:
                    with patch.object(worker,'extract_html',side_effect=operation):worker.main()
                else:worker.main()
            return json.loads(output.getvalue())
        for stage,reason in [('dependency','dependency_missing'),('date','date_error'),('serialize','output_limit')]:
            value=main_result(HTML,worker.ExtractionFailure(stage,reason))
            self.assertEqual(value,dict(error='extract_failed',stage=stage,reason=reason))
        with patch('builtins.__import__',side_effect=ImportError('secret document')):
            with self.assertRaises(worker.ExtractionFailure) as error:worker.extract_html(HTML)
        self.assertEqual(error.exception.reason,'dependency_missing')
        with patch.object(worker,'extract_dates',side_effect=ValueError('secret date')):
            with self.assertRaises(worker.ExtractionFailure) as error:worker.extract_html(HTML)
        self.assertEqual(error.exception.stage,'date')


class RetrievalTests(unittest.IsolatedAsyncioTestCase):
    async def fetch(self,error=None,summary=TEXT,question='Python最近消息',fallback='snippet',body=HTML):
        class HTTP:
            calls=[]
            def __init__(self,cfg,audit):pass
            async def get(self,url,rss=False):
                self.calls.append(url)
                if rss:return '<rss><channel><item><title>Python release</title><link>https://example.com/release</link><description>'+summary+'</description><pubDate>Wed, 28 Oct 2026 09:00:00 GMT</pubDate></item></channel></rss>',url,'text/xml'
                if error:raise error
                return body,url,'text/html'
        with tempfile.TemporaryDirectory() as t:
            r=Retriever(dict(enabled=True,search_enabled=True,search_fallback=fallback),http_factory=HTTP,root=t)
            token=REQUEST_TIME.set(NOW)
            try:
                with patch('qqbot_gateway.web_retrieval.SEARCH_QUALITY_PASSED',True):value=await r.retrieve(question)
            finally:REQUEST_TIME.reset(token)
        return value,HTTP.calls

    async def test_body_preferred_and_fallback(self):
        result,calls=await self.fetch()
        self.assertEqual(result.sources[0]['material']['kind'],'page_excerpt');self.assertEqual(len(calls),2)
        result,calls=await self.fetch(body='<html/>')
        row=result.sources[0];self.assertEqual(row['material']['kind'],'search_snippet')
        self.assertIsNone(row['published_at']);self.assertEqual(row['freshness']['date_source'],'none')
        self.assertEqual(row['material']['reported_date_source'],'rss_item')
        result,_=await self.fetch(body='<html/>',question='Python今天新闻')
        self.assertFalse(result.sources)  # RSS time cannot prove the event window.
        result,_=await self.fetch(error=TimeoutError())
        self.assertEqual(result.sources[0]['material']['kind'],'search_snippet')

    async def test_no_shell_or_unsafe_fallback(self):
        for args in [dict(body='<html/>',summary='Python'),dict(body='<html/>',fallback='none'),
                dict(error=WebFailure('blocked_ip')),dict(error=WebFailure('peer_mismatch')),
                dict(error=WebFailure('restricted')),dict(error=WebFailure('extract_protocol')),
                dict(body='<!DOCTYPE x [<!ENTITY a SYSTEM "file:///secret">]>'+HTML),
                dict(body='<main>'+('access denied '*20)+'</main>')]:
            result,_=await self.fetch(**args);self.assertFalse(result.sources);self.assertTrue(result.notice)

    async def test_strict_vs_recent_current(self):
        for question,count in [('Python今天新闻',0),('Python过去24小时新闻',0),('Python最近消息',1),('Python最新稳定版本',1)]:
            result,_=await self.fetch(question=question)
            self.assertEqual(len(result.sources),count)

    async def test_gates_never_network(self):
        class HTTP:
            def __init__(self,*a):raise AssertionError('network gate bypass')
        for enabled in (False,True):
            r=Retriever(dict(enabled=True,search_enabled=enabled),http_factory=HTTP)
            self.assertTrue((await r.retrieve('Python最新稳定版本')).notice)

    async def test_mentions_once(self):
        class FakeRetriever:
            cfg=DEFAULTS
            last_audit={}
            async def retrieve(self,q):return Retrieval('search',[page('search_snippet')])
        runner=type('Runner',(),{'run':AsyncMock(return_value=BackendResult('简短回答'))})()
        r=WebRunner(runner,FakeRetriever(),InputBudget(limit=6000),OUTPUT)
        value=await r.run('policy',dialog_text([dict(role='user',content='Python消息')]),'id')
        runner.run.assert_awaited_once();self.assertIn('据检索摘要',value.text)

    async def test_v1_web_manifest_bound_to_frozen_snapshot(self):
        from qqbot_gateway.group_protocol import metadata,verify_metadata
        from qqbot_gateway.reply_plan import digest
        snapshot=dict(must_reply=True,target_seq=1,web_anchor='Python消息',messages=[dict(seq=1,speaker='u1',name='synthetic',text='Python消息',reply=None)])
        body=json.dumps(snapshot,ensure_ascii=False,separators=(',',':'))
        request=dict(version=1,kind='group_turn',trigger='mention',must_reply=True,epoch='a'*64,snapshot_digest=digest(body),request_key='b'*64)
        class FakeRetriever:
            cfg=DEFAULTS
            async def retrieve(self,q):return Retrieval('search',[page('search_snippet')])
        raw=json.dumps(dict(qqbot_group_reply=1,decision='speak',kind='answer',bubbles=['简短回答'],meme_id=None),ensure_ascii=False)
        runner=type('Runner',(),{'run':AsyncMock(return_value=BackendResult(raw))})()
        r=WebRunner(runner,FakeRetriever(),InputBudget(limit=8000),OUTPUT)
        result=await r.run_group('policy',dialog_text([dict(role='user',content=body)]),'id',request)
        value=metadata(request,'response','speak',result.prepared_plan,result.web_evidence)
        self.assertEqual(value['web'][0]['material']['kind'],'search_snippet')
        self.assertTrue(verify_metadata(value,request,'response',result.text,OUTPUT,snapshot))
        with self.assertRaises(ValueError):verify_metadata(value,request,'response',result.text,OUTPUT,dict(snapshot,web_anchor='different'))
        runner.run.assert_awaited_once()


if __name__=='__main__':unittest.main()
