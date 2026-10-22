import asyncio
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from qqbot_gateway.bilibili_policy import DEFAULTS,validate,locator,current_locators
from qqbot_gateway.bilibili_subtitles import Subtitles,choose_track,normalize,select_source,credentials
from qqbot_gateway.public_http import PublicHTTP,Audit,WebFailure,bilibili_url
from qqbot_gateway.web_policy import DEFAULTS as WEB
from qqbot_gateway.web_retrieval import Retriever,Retrieval,WebRunner,CURRENT_TEXT,evidence_prompt,source_plan
from qqbot_gateway.evidence_selection import sources_for_budget,manifest,validate_manifest,encoded
from qqbot_gateway.token_budget import InputBudget,dialog_text
from qqbot_gateway.reply_plan import DEFAULTS as OUTPUT
BVID='BV1234567890'
OTHER='BVabcdefghij'
CDN='https://aisubtitle.hdslb.com/bfs/ai_subtitle/test.json?auth_key=synthetic'


def subtitle_body(long=False):
    return {'body':[{'from':i*10,'to':i*10+9,'content':('事实第%d段：实验先降温再加压；验证码只是字幕词语。'%i)*(8 if long else 1)} for i in range(60 if long else 6)]}


class HTTP:
    calls=[];delay=0;cancelled=0;body=subtitle_body();need=False;code=0
    def __init__(self,cfg,audit):self.cfg=cfg;self.audit=audit
    async def get(self,url,**kwargs):
        type(self).calls.append((url,kwargs));self.audit.http_calls+=1
        try:
            if self.delay:await asyncio.sleep(self.delay)
            if kwargs['purpose']=='bilibili_short':return '',f'https://www.bilibili.com/video/{BVID}?p=2','redirect'
            if '/view?' in url:
                bv=OTHER if OTHER in url else BVID
                obj={'code':self.code,'data':{'bvid':bv,'aid':123,'title':'标题声称升温，正文实际降温','pages':[
                    {'page':1,'cid':11,'part':'第一P','duration':600},{'page':2,'cid':22,'part':'第二P','duration':600}]}}
            elif '/wbi/v2?' in url:obj={'code':0,'data':{'need_login_subtitle':self.need,'subtitle':{'subtitles':[
                {'lan':'ai-zh','subtitle_url':CDN},{'lan':'zh-CN','subtitle_url':CDN},{'lan':'en','subtitle_url':CDN}]}}}
            else:obj=copy.deepcopy(self.body)
            return json.dumps(obj,ensure_ascii=False),url,'application/json'
        except asyncio.CancelledError:type(self).cancelled+=1;raise


class PolicyTests(unittest.TestCase):
    def test_defaults_and_configuration(self):
        self.assertFalse(validate({},WEB)['enabled'])
        for cfg in ({'enabled':True},{'trigger':'auto'},{'auth_mode':'browser'},{'max_duration_seconds':1201},{'max_evidence_bytes':6001},{'cache_ttl_seconds':True},{'Cookie':'x'}):
            with self.subTest(cfg=cfg),self.assertRaises(ValueError):validate(cfg,WEB)
        self.assertTrue(validate({'enabled':True},WEB|{'enabled':True})['enabled'])

    def test_current_explicit_and_links(self):
        for text in (BVID,'av123',f'https://www.bilibili.com/video/{BVID}?p=2&share_source=x',f'm.bilibili.com/video/{BVID}?p=2','b23.tv/abc'):
            self.assertIsNone(current_locators(text))
            self.assertTrue(current_locators(text,True))
            self.assertTrue(current_locators('总结 '+text))
        self.assertIsNone(current_locators('不要联网 总结 '+BVID,True))
        self.assertIsNone(current_locators('123456'))
        self.assertEqual(locator(f'bilibili.com/video/{BVID}?p=2&session=discarded'),(BVID,2))
        for url in (f'https://www.bilibili.com/video/{BVID}?p=0',f'https://www.bilibili.com/video/{BVID}?p=1&p=2',
                    'https://b23.tv@127.0.0.1/a','https://b23.tv/a#x','https://bilibili.com/bangumi/x'):
            with self.subTest(url=url),self.assertRaises(WebFailure):locator(url)
        with self.assertRaises(WebFailure):current_locators('总结 '+BVID+' https://example.com')

    def test_purpose_endpoints(self):
        for url,purpose in [('https://api.bilibili.com/x/player/wbi/v2?bvid='+BVID+'&cid=22','bilibili_api'),(CDN,'subtitle'),('https://b23.tv/abc','bilibili_short')]:
            self.assertEqual(bilibili_url(url,purpose),url)
        for url,purpose in [('http://aisubtitle.hdslb.com/bfs/subtitle/x','subtitle'),('https://evil.hdslb.com/bfs/subtitle/x','subtitle'),
                            ('https://i0.hdslb.com/a.json','subtitle'),('https://i1.hdslb.com/bfs/subtitle/../x','subtitle'),
                            ('https://api.bilibili.com/x/player/wbi/playurl?bvid='+BVID,'bilibili_api'),
                            ('https://api.bilibili.com/x/web-interface/view?bvid='+BVID+'&token=x','bilibili_api'),
                            ('https://api.bilibili.com.evil.com/x/web-interface/view?aid=1','bilibili_api'),
                            ('https://b23.tv/a?x=y','bilibili_short')]:
            with self.subTest(url=url),self.assertRaises(WebFailure):bilibili_url(url,purpose)

    def test_single_track_language_priority(self):
        tracks=[{'lan':'ai-zh','subtitle_url':CDN},{'lan':'en','subtitle_url':CDN},{'lan':'zh-CN','subtitle_url':'//i0.hdslb.com/bfs/subtitle/manual.json'}]
        info={'code':0,'data':{'subtitle':{'subtitles':tracks}}}
        self.assertEqual(choose_track(info,'zh')[1:],('zh-CN',False))
        self.assertEqual(choose_track(info,'en')[1:],('en',False))
        tracks.pop();self.assertTrue(choose_track(info,'zh')[2])
        tracks.pop(0);self.assertEqual(choose_track(info,'zh')[1],'en')
        info['data']['need_login_subtitle']=True
        with self.assertRaises(WebFailure):choose_track(info,'zh')

    def test_normalize_and_invalid_times(self):
        obj={'body':[{'from':2,'to':3,'content':'第二句'*15},{'from':0,'to':1,'content':'第一句'*15},{'from':.5,'to':2,'content':'第一句'*15}]}
        rows=normalize(obj,600);self.assertEqual(len(rows),2);self.assertEqual(rows[0][:2],(0,2))
        for a,b in [(float('nan'),1),(0,float('inf')),(-1,2),(3,2),(0,601),(True,3)]:
            with self.subTest(a=a,b=b),self.assertRaises(WebFailure):normalize({'body':[{'from':a,'to':b,'content':'x'*100}]},600)

    def test_none_never_reads_secret(self):
        with patch('qqbot_gateway.config_files.plain_path',side_effect=AssertionError('secret read')):
            self.assertEqual(credentials(DEFAULTS,None),(None,'none'))


class MaterialTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        HTTP.calls=[];HTTP.delay=0;HTTP.cancelled=0;HTTP.body=subtitle_body();HTTP.need=False;HTTP.code=0
        self.cfg=DEFAULTS|{'enabled':True};self.web=WEB|{'enabled':True}
        self.service=Subtitles(self.cfg,self.web,http_factory=HTTP)
    async def test_p2_short_and_cache_scope(self):
        source=await self.service.get((('https://b23.tv/abc',None),),'group-a')
        self.assertEqual((source['page'],source['cid']),(2,22));self.assertIn('?p=2',source['url'])
        self.assertEqual(len(HTTP.calls),4);self.assertIn('cid=22',HTTP.calls[-2][0])
        await self.service.get(((BVID,2),),'group-a');self.assertEqual(len(HTTP.calls),4)
        await self.service.get(((BVID,2),),'group-b');self.assertEqual(len(HTTP.calls),7)
        await self.service.get(((BVID,1),),'group-a');self.assertEqual(len(HTTP.calls),10)
        self.assertTrue(all('credential' not in kw for _,kw in HTTP.calls))
    async def test_short_hop_and_total_http_bound(self):
        from urllib.parse import urlsplit
        class Chain(HTTP):
            calls=[]
            async def get(inner,url,**kw):
                if kw['purpose']=='bilibili_short':
                    inner.audit.http_calls+=1;type(inner).calls.append((url,kw))
                    return '',('https://b23.tv/second' if url.endswith('/first') else 'https://www.bilibili.com/video/'+BVID),'redirect'
                return await super().get(url,**kw)
        svc=Subtitles(self.cfg,self.web,http_factory=Chain)
        await svc.get((('https://b23.tv/first',None),),'g')
        self.assertEqual(len(Chain.calls),5)
        Chain.calls=[]
        with self.assertRaises(WebFailure):await svc.get((('https://b23.tv/first',None),('https://b23.tv/third',None)),'other')
        self.assertLessEqual(len(Chain.calls),6)
        self.assertFalse(any(kw['purpose']=='subtitle' for _,kw in Chain.calls))

    async def test_equivalent_and_multiple(self):
        await self.service.get(((BVID,1),('av123',1)),'g');self.assertEqual(len(HTTP.calls),3)
        for values in [((BVID,1),(BVID,2)),((BVID,1),(OTHER,1))]:
            HTTP.calls=[]
            with self.assertRaises(WebFailure):await self.service.get(values,'g2')
            self.assertFalse(any(kw['purpose']=='subtitle' for _,kw in HTTP.calls))
    async def test_auth_isolation_and_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'secrets').mkdir();path=root/'secrets/bilibili-session.local.json'
            path.write_text(json.dumps({'SESSDATA':'synthetic-one'}))
            svc=Subtitles(self.cfg|{'auth_mode':'sessdata'},self.web,root=root,http_factory=HTTP)
            await svc.get((('https://b23.tv/abc',None),),'g')
            for _,kw in HTTP.calls:self.assertEqual(kw.get('credential'), 'synthetic-one' if kw['purpose']=='bilibili_api' else None)
            n=len(HTTP.calls);path.write_text(json.dumps({'SESSDATA':'synthetic-two'}));await svc.get(((BVID,2),),'g')
            self.assertEqual(len(HTTP.calls),n+3)
            raw=json.dumps(list(svc.cache.values()),default=str)
            self.assertNotIn('synthetic-one',raw);self.assertNotIn('synthetic-two',raw)
    async def test_failures_and_no_title_fallback(self):
        for need,code in [(True,0),(False,-404),(False,-101),(False,-403)]:
            HTTP.need=need;HTTP.code=code;HTTP.calls=[]
            with self.assertRaises(WebFailure):await self.service.get(((BVID,1),),'g')
            self.assertFalse(any(kw['purpose']=='subtitle' for _,kw in HTTP.calls));self.assertFalse(self.service.cache)
    async def test_duration_page_and_line_limit(self):
        svc=Subtitles(self.cfg|{'max_duration_seconds':60},self.web,http_factory=HTTP)
        with self.assertRaises(WebFailure):await svc.get(((BVID,1),),'g')
        self.assertEqual(len(HTTP.calls),1)
        with self.assertRaises(WebFailure):await self.service.get(((BVID,3),),'g')
        HTTP.body={'body':[{}]*10001}
        with self.assertRaises(WebFailure):await self.service.get(((BVID,1),),'g')
    async def test_singleflight_cancel_one_and_last(self):
        HTTP.delay=.03
        a=asyncio.create_task(self.service.get(((BVID,1),),'g'));b=asyncio.create_task(self.service.get(((BVID,1),),'g'))
        await asyncio.sleep(.01);a.cancel()
        with self.assertRaises(asyncio.CancelledError):await a
        self.assertEqual((await b)['cid'],11);self.assertEqual(len(HTTP.calls),3);self.assertFalse(self.service.flights)
        c=asyncio.create_task(self.service.get(((BVID,1),),'other'));await asyncio.sleep(.01);c.cancel()
        with self.assertRaises(asyncio.CancelledError):await c
        self.assertGreater(HTTP.cancelled,0);self.assertFalse(self.service.flights)
    async def test_ttl_lru_and_disabled_cache(self):
        for i in range(34):await self.service.get(((BVID,1),),str(i))
        self.assertEqual(len(self.service.cache),32);self.assertLessEqual(sum(v[1] for v in self.service.cache.values()),4*1024*1024)
        key=next(iter(self.service.cache));expiry,size,known,source=self.service.cache[key];self.service.cache[key]=(0,size,known,source)
        await self.service.get(((BVID,1),),'new');self.assertNotIn(key,self.service.cache)
        svc=Subtitles(self.cfg|{'cache_ttl_seconds':0},self.web,http_factory=HTTP);await svc.get(((BVID,1),),'g');self.assertFalse(svc.cache)
    async def test_six_time_zones_and_final_budget(self):
        HTTP.body=subtitle_body(True);source=await self.service.get(((BVID,1),),'g')
        rows=sources_for_budget([source],6000,6000,'excerpt','总结')
        row=rows[0];self.assertEqual(row['coverage'],'excerpt');self.assertGreaterEqual(len(row['ranges']),4)
        self.assertGreaterEqual(row['selected_bytes'],1200);self.assertLessEqual(len(encoded({'partial':False,'sources':rows})),6000)
        self.assertEqual(row['time_ranges'][0][0],0);self.assertEqual(row['time_ranges'][-1][1],599)
        self.assertLess(row['time_coverage'],1);self.assertTrue(row['time_gaps'])
        validate_manifest(manifest(rows),{'web_anchor':'总结 '+BVID})
        for a,b in row['ranges']:self.assertIn(source['_full_text'][a:b],row['text'])
        with self.assertRaises(WebFailure):sources_for_budget([source],6000,6000,'excerpt','完整总结')
        with self.assertRaises(WebFailure):sources_for_budget([source],6000,6000,'reject','总结')
        prompt=dialog_text([{'role':'user','content':'总结 '+BVID}])
        enriched,selected=evidence_prompt('policy',prompt,Retrieval('subtitle',[source]),InputBudget(),self.web)
        self.assertTrue(selected);self.assertIn('正文优先于标题',enriched)
        plan=source_plan('实验先降温。',selected,OUTPUT,'总结');self.assertIn('字幕节选',plan.canonical_text);self.assertNotIn('auth_key',plan.canonical_text)
        with self.assertRaises(WebFailure):source_plan('https://evil.example/x',selected,OUTPUT,'总结')
    async def test_final_budget_shrink_manifest_and_oversized_cache(self):
        HTTP.body=subtitle_body(True);source=await self.service.get(((BVID,1),),'g')
        prompt=dialog_text([{'role':'user','content':'旧问题'*1000},{'role':'assistant','content':'旧回答'},{'role':'user','content':'总结 '+BVID}])
        for limit in (2800,5000,8000):
            budget=InputBudget(limit=limit,overhead=10)
            result,rows=evidence_prompt('fixed policy',prompt,Retrieval('subtitle',[source]),budget,self.web)
            if rows:
                self.assertLessEqual(budget.usage('fixed policy',result),limit)
                self.assertEqual(rows[0]['coverage'],'excerpt');validate_manifest(manifest(rows),{'web_anchor':BVID})
            else:self.assertIsNone(result)
        rows=sources_for_budget([source],6000,6000,'excerpt','总结')
        bad=manifest(rows);bad[0]['subtitle']['time_coverage']=1
        with self.assertRaises(ValueError):validate_manifest(bad,{'web_anchor':BVID})
        svc=Subtitles(self.cfg,self.web,http_factory=HTTP)
        HTTP.body={'body':[{'from':i*.05,'to':i*.05+.04,'content':'合成大字幕'*30} for i in range(1500)]}
        await svc.get(((BVID,1),),'g');self.assertFalse(svc.cache)

    async def test_queue_stop_deadline_and_unknown_no_retry(self):
        from qqbot_gateway.model_gateway import ModelQueue
        from qqbot_gateway.errors import GatewayError
        from unittest.mock import AsyncMock
        HTTP.delay=.2
        r=Retriever(self.web|{'timeout_seconds':.01},bilibili=self.cfg,http_factory=HTTP)
        runner=type('Runner',(),{'run':AsyncMock()})()
        wrapper=WebRunner(runner,r,InputBudget(),OUTPUT)
        result=await wrapper.run('policy',dialog_text([{'role':'user','content':BVID}]),'deadline')
        self.assertFalse(result.generation_performed);runner.run.assert_not_called();self.assertFalse(r.bilibili.flights)
        r.cfg['timeout_seconds']=15;r.bilibili.web['timeout_seconds']=15
        queue=ModelQueue(wrapper);await queue.start()
        task=asyncio.create_task(queue.submit('policy',dialog_text([{'role':'user','content':BVID}]),'cancel'))
        await asyncio.sleep(.02);task.cancel();await asyncio.gather(task,return_exceptions=True);await queue.close()
        self.assertFalse(r.bilibili.flights);runner.run.assert_not_called()
        HTTP.delay=0
        runner.run=AsyncMock(side_effect=GatewayError('REMOTE_RESULT_UNKNOWN'))
        with self.assertRaises(GatewayError) as error:await wrapper.run('policy',dialog_text([{'role':'user','content':BVID}]),'unknown')
        self.assertEqual(error.exception.code,'REMOTE_RESULT_UNKNOWN');self.assertEqual(runner.run.await_count,1)

    async def test_older_eligible_video_never_fetched_for_current_target(self):
        from unittest.mock import AsyncMock
        from qqbot_gateway.backends import BackendResult
        r=Retriever(self.web,bilibili=self.cfg,http_factory=HTTP)
        runner=type('Runner',(),{'run':AsyncMock(return_value=BackendResult('ordinary text'))})()
        wrapper=WebRunner(runner,r,InputBudget(),OUTPUT)
        source={'web_anchor':'总结 '+BVID,'target_seq':2,'eligible_seq':[1,2],
                'messages':[{'seq':1,'text':'总结 '+BVID},{'seq':2,'text':'当前只聊新的文字'}]}
        result=await wrapper.run_v2('policy',dialog_text([{'role':'user','content':json.dumps(source)}]),'new',{'must_reply':False,'target_seq':2,'addressing':'ambient','epoch':'g'})
        self.assertEqual(result.text,'ordinary text');runner.run.assert_awaited_once();self.assertFalse(HTTP.calls)

    async def test_explicit_retriever_and_no_fetch_bare(self):
        r=Retriever(self.web,bilibili=self.cfg,http_factory=HTTP)
        self.assertEqual((await r.retrieve(BVID)).kind,'none');self.assertFalse(HTTP.calls)
        result=await r.retrieve('总结 '+BVID);self.assertEqual(result.kind,'subtitle');self.assertTrue(result.sources)
        token=CURRENT_TEXT.set((True,'g'))
        try:self.assertEqual((await r.retrieve(BVID)).kind,'subtitle')
        finally:CURRENT_TEXT.reset(token)
        r=Retriever(self.web,http_factory=HTTP);self.assertIsNotNone((await r.retrieve('总结 '+BVID)).notice)


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_fixed_purposes_cookies_redirects_mime_compression_and_budget(self):
        import aiohttp
        import gzip
        class Content:
            def __init__(self,body):self.body=body
            async def iter_chunked(self,n):
                for i in range(0,len(self.body),n):yield self.body[i:i+n]
        class Response:
            charset='utf-8';content_length=None
            def __init__(self,body=b'{}',status=200,headers=None):
                self.status=status;self.headers=headers or {'Content-Type':'application/json'};self.content=Content(body);self.url=CDN
            async def __aenter__(self):return self
            async def __aexit__(self,*a):pass
        calls=[];responses=[]
        class Session:
            def __init__(self,**kw):
                self.connector=kw['connector']
                assert kw['trust_env'] is False and kw['auto_decompress'] is False and isinstance(kw['cookie_jar'],aiohttp.DummyCookieJar)
                assert self.connector._ssl.check_hostname and self.connector._ssl.verify_mode
            async def __aenter__(self):return self
            async def __aexit__(self,*a):await self.connector.close()
            def get(self,url,**kw):
                assert self._retry_connection is False and kw['allow_redirects'] is False
                calls.append((url,kw));return responses.pop(0)
        api='https://api.bilibili.com/x/web-interface/view?bvid='+BVID
        async def fetch(url,purpose,response,credential=None,audit=None):
            responses[:]=[response]
            with patch('qqbot_gateway.public_http.aiohttp.ClientSession',Session):
                return await PublicHTTP(WEB|{'max_response_bytes':65536},audit or Audit()).get(url,purpose=purpose,credential=credential)
        await fetch(api,'bilibili_api',Response(),credential='synthetic-cookie')
        self.assertEqual(calls[-1][1]['headers'],{'Cookie':'SESSDATA=synthetic-cookie'})
        await fetch(CDN,'subtitle',Response('验证码是正常字幕'.encode()))
        self.assertEqual(calls[-1][1]['headers'],{})
        for target in ('http://127.0.0.1/x','https://169.254.169.254/','https://evil.example/x','https://bilibili.com/live/1'):
            n=len(calls)
            with self.subTest(target=target),self.assertRaises(WebFailure):
                await fetch('https://b23.tv/abc','bilibili_short',Response(status=302,headers={'Location':target}))
            self.assertEqual(len(calls),n+1)
        for purpose,url,resp in [
            ('bilibili_api',api,Response(status=302,headers={'Location':api})),
            ('subtitle',CDN,Response(status=302,headers={'Location':'https://example.com/x'})),
            ('subtitle',CDN,Response(b'<html>login</html>',headers={'Content-Type':'text/html'})),
            ('subtitle',CDN,Response(b'x'*65537)),
            ('subtitle',CDN,Response(gzip.compress(b'x'*100000),headers={'Content-Type':'application/json','Content-Encoding':'gzip'})),
            ('subtitle',CDN,Response(b'broken',headers={'Content-Type':'application/json','Content-Encoding':'gzip'})),
            ('subtitle',CDN,Response(status=403)),('subtitle',CDN,Response(status=412)),('subtitle',CDN,Response(status=429))]:
            with self.subTest(purpose=purpose),self.assertRaises(WebFailure):await fetch(url,purpose,resp)
        for purpose,url in [('subtitle',CDN),('bilibili_short','https://b23.tv/abc'),('page','https://example.com')]:
            n=len(calls)
            with self.assertRaises(WebFailure):await fetch(url,purpose,Response(),credential='synthetic-cookie')
            self.assertEqual(n,len(calls))
        audit=Audit(http_calls=6);n=len(calls)
        with self.assertRaises(WebFailure):await fetch(CDN,'subtitle',Response(),audit=audit)
        self.assertEqual(len(calls),n)


if __name__=='__main__':unittest.main()
