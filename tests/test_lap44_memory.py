"""LAP-44 synthetic persistence, full-wire, quota and transactional receipt checks."""
import asyncio
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from qqbot_gateway.group_memory import MemoryStore,validate_config,valid_memory,auxiliary,receipt_plan,chars
from qqbot_gateway.turn_v2 import fit,plan,metadata,verify,sha
from qqbot_gateway.vision import member_source
from qqbot_gateway.reply_plan import DEFAULTS as OUTPUT,ReplyPlan,PreparedPart,digest
from qqbot_gateway.token_budget import InputBudget
from qqbot_gateway.errors import GatewayError

CFG=dict(enabled=True,learning_enabled=True)
class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.store=MemoryStore(self.root,'10000',['20000','30000'],cfg=CFG)
        self.seq=0
    def tearDown(self):self.tmp.cleanup()
    def turn(self,store=None,group='20000'):
        self.seq+=1;source=member_source('合成称呼', ['鱼鱼']);who=source['messages'][0]['member_ref']
        store=store or self.store
        ctx=store.prepare(group,f'{self.seq:064x}',source,{who:'40000'}, {})
        self.assertIsNotNone(ctx);return ctx,source
    def save(self,ctx,source,updates,**kw):return self.store.stage(ctx,dict(updates=updates,receipt=True,reason='valid')|kw,source)
    def test_blocks_names_duplicates_full_wire_and_isolation(self):
        ctx,s=self.turn();self.assertEqual(s['memory']['actors'][next(iter(s['memory']['actors']))],'40000')
        updates={'members':{'40000':[' 茶 ','茶','以前甜饮，最近清茶。'],'50000':['茶']},'group':['周六联机']}
        self.assertEqual(self.save(ctx,s,updates)['result'],'saved')
        ctx,s=self.turn();self.assertEqual(s['memory']['members']['40000']['memory'],['茶','以前甜饮，最近清茶。'])
        self.assertEqual(s['memory']['members']['50000']['memory'],['茶'])
        self.assertNotIn('_meta',s['memory']);self.assertNotIn('generation',s['memory'])
        head=dict(must_reply=True,target_seq=1,addressing='mention')
        self.assertEqual(json.loads(fit(s,head,'policy',InputBudget(limit=524288)))['memory'],s['memory'])
        self.save(ctx,s,{'members':{'40000':[]}})
        _,s=self.turn();self.assertEqual(s['memory']['members']['40000']['memory'],[])
        self.assertEqual(s['memory']['group'],['周六联机'])
        _,other=self.turn(group='30000');self.assertEqual(other['memory']['members'],{})
        self.store.known_names['50000']='同名';self.store.known_names['40000']='同名'
        _,s=self.turn();self.assertEqual(len(s['memory']['members']),2)
        self.store.known_names['50000']='改名';_,s=self.turn();self.assertEqual(s['memory']['members']['50000']['name'],'改名')
    def test_conflict_protocol_capacity_and_atomic_failure(self):
        ctx,s=self.turn();other,t=self.turn()
        result=self.save(ctx,s,{'group':['新认识']})
        self.assertEqual(self.save(ctx,s,{'group':['重复请求']}),result)
        self.assertEqual(self.save(other,t,{'group':['并发']})['reason'],'conflict')
        for update in ({'new_1':'旧接口'},{'members':{'40000':None}},{'group':{'0':'下标'}}):
            ctx,s=self.turn();self.assertEqual(self.save(ctx,s,update)['reason'],'protocol')
        ctx,s=self.turn();before=self.store.path('20000').read_bytes()
        self.assertEqual(self.save(ctx,s,{'group':['长'*50001]})['reason'],'capacity');self.assertEqual(before,self.store.path('20000').read_bytes())
        ctx,s=self.turn()
        with patch('qqbot_gateway.group_memory.os.replace',side_effect=OSError('synthetic')):
            self.assertEqual(self.save(ctx,s,{'group':['失败']})['result'],'failed')
        self.assertEqual(before,self.store.path('20000').read_bytes())
    def test_legacy_association_and_deleted_text_never_revives(self):
        path=self.store.path('20000');path.parent.mkdir(parents=True)
        known=self.store.actor('20000','40000');unknown=self.store.actor('20000','50000')
        old=dict(schema_version=2,namespace_hmac=self.store.namespace('20000'),generation='a'*32,revision=4,last_request_key=None,
            records={'a'*32:'u_'+known+' 旧事实','b'*32:'u_'+unknown+' 待关联事实','c'*32:'本群 约定'})
        path.write_text(json.dumps(old),encoding='utf-8')
        ctx,s=self.turn();self.assertEqual(s['memory']['members']['40000']['memory'],['旧事实'])
        self.assertEqual(len(s['memory']['unassigned']),1)
        self.save(ctx,s,{'unassigned':[]});self.store.associate('20000',['50000'])
        _,s=self.turn();self.assertNotIn('50000',s['memory']['members'])
        self.assertEqual(s['memory']['group'],['本群 约定'])
        self.store.identity_links[('30000','wx-user')]='40000'
        self.assertEqual(self.store.identity('30000','wx-user'),'40000')
        self.assertEqual(self.store.identity('30000','wx-other'),'wechat:wx-other')
        self.store.wechat_groups.add('30000');self.assertEqual(self.store.identity('30000','12345'),'wechat:12345')
    def test_wire_manifest_and_silent_success_preserves_parts(self):
        ctx,s=self.turn();req=dict(must_reply=True,target_seq=1,addressing='mention')
        raw=dict(qqbot_turn_reply=2,decision='speak',kind='chat',bubbles=['好。'],meme_id=None,response_to_seq=1,mention=None,memory_updates={'members':{'40000':['小青']}},memory_receipt=True)
        aux={};decision,p,response=plan(json.dumps(raw),OUTPUT,'合成',req,s,memory_out=aux)
        meta=metadata(req,'r1',decision,p,s,response,memory_proposals=aux)
        self.assertEqual(meta['manifest']['fact_refs'],[])
        self.assertEqual(verify(meta,req,'r1',p.canonical_text,OUTPUT,s,self.store.cfg),p)
        saved=self.store.stage(ctx,aux,s)
        self.assertIs(receipt_plan(p,saved,True,OUTPUT),p)
        image=PreparedPart('image','b'*64,'m_'+'b'*64,'合成表情')
        p=replace(p,prepared_parts=(*p.parts,image))
        for result in ('saved','unchanged'):self.assertIs(receipt_plan(p,dict(result=result),True,OUTPUT),p)
        self.assertIs(receipt_plan(p,dict(result='failed'),False,OUTPUT),p)
        final=receipt_plan(p,dict(result='failed'),True,OUTPUT)
        self.assertEqual(final.parts[:2],p.parts);self.assertEqual(len(final.parts),3)

class WebMemoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_native_web_keeps_human_updates_prepared_and_no_tools(self):
        from qqbot_gateway.backends import BackendResult
        from qqbot_gateway.web_retrieval import WebRunner
        from types import SimpleNamespace
        from qqbot_gateway.reply_plan import DEFAULTS
        source=member_source('合成问题',['鱼鱼']);source['memory']=dict(group=[],members={},unassigned=[],actors={})
        request=dict(must_reply=True,target_seq=source['target_seq'],addressing='mention')
        raw=dict(qqbot_turn_reply=2,decision='speak',kind='chat',bubbles=['公开消息'],meme_id=None,response_to_seq=1,mention=None,memory_updates={'group':['本群人类的新称呼']},memory_receipt=True)
        for calls in (0,1):
            class Runner:
                async def run(self,*args):return BackendResult(json.dumps(raw),parameters={'native_web':dict(calls=calls,result_bytes=100,sha256='b'*64,urls=['https://example.com/news'])})
            w=WebRunner(Runner(),SimpleNamespace(),InputBudget(),DEFAULTS)
            result=await w.run_native_v2('policy','prompt','trace',request,source,'合成问题')
            if calls:self.assertEqual(result.memory_aux['updates'],raw['memory_updates']);self.assertIsNotNone(result.prepared_plan)
            else:self.assertEqual(json.loads(result.text)['memory_updates'],raw['memory_updates'])

class GatewayMemoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_http_normal_and_prepared_plan_keep_full_memory_and_aux(self):
        from aiohttp.test_utils import TestClient,TestServer
        from qqbot_gateway.model_gateway import application,ModelQueue
        from qqbot_gateway.backends import BackendResult
        from qqbot_gateway.attention import canonical
        source=member_source('合成目标',['鱼鱼']);source['memory']=dict(group=['中'*60000],members={},unassigned=[],actors={})
        req=dict(version=2,kind='group_turn',request_key='a'*64,epoch='b'*64,config_version='c'*64,source_digest=sha(source),mode='free',addressing='mention',must_reply=True,target_seq=1,resource_caps=[])
        aux=dict(receipt=True,updates={'group':['本群合成称呼']},reason='valid')
        raw=dict(qqbot_turn_reply=2,decision='speak',kind='answer',bubbles=['合成答复'],meme_id=None,response_to_seq=1,mention=None,memory_updates=aux['updates'],memory_receipt=True)
        for prepared in (False,True):
            class Runner:
                attempts=0
                async def run(self,system,prompt,trace):
                    self.attempts+=1;self.snapshot=json.loads(json.loads(prompt)[-1]['content'])
                    return BackendResult('合成答复',prepared_plan=ReplyPlan('answer',('合成答复',),'合成答复'),memory_aux=aux) if prepared else BackendResult(json.dumps(raw))
            runner=Runner();cfg=validate_config(CFG|dict(max_chars_per_group=100000))
            app=application(ModelQueue(runner),'t'*32,budget=InputBudget(limit=786432),v2=dict(mode='free',config_version='c'*64,aliases=['鱼鱼'],memory_enabled=True,learning_enabled=True,memory_config=cfg))
            async with TestClient(TestServer(app)) as client:
                response=await client.post('/v1/chat/completions',json=dict(model='workbuddy-local',stream=False,messages=[dict(role='user',content=canonical(source))],qqbot_request=req),headers={'Authorization':'Bearer '+'t'*32,'X-QQBot-Trace':'d'*32})
                self.assertEqual(response.status,200,await response.text());body=await response.json()
                self.assertEqual(runner.snapshot['memory'],source['memory']);self.assertEqual(body['qqbot_group_plan']['memory_aux'],aux)
                verify(body['qqbot_group_plan'],req,body['id'],body['choices'][0]['message']['content'],OUTPUT,source,cfg)
                self.assertEqual(runner.attempts,1)

class AstrBotMemoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_hook_saves_before_ledger_and_reentry_preserves_final_hash(self):
        import os,time
        if not os.environ.get('QQBOT_TEST_ASTRBOT_SITE'):self.skipTest('AstrBot runtime required')
        import test_transport_router as fixture
        from types import SimpleNamespace
        from qqbot_gateway.task_store import TaskStore
        fixture.RouterTests.setUpClass();f=fixture.RouterTests('test_actual_js_gate_astrbot_parser_time_sender_image_and_no_reply_fetch')
        await f.asyncSetUp();tasks=None
        try:
            self.assertTrue(f.ready());r=f.router;r.output=OUTPUT;r.members=dict(enabled=False)
            r.memory=MemoryStore(f.root,'222',['111'],cfg=CFG)
            tasks=r.tasks=TaskStore(f.root/'tasks.sqlite3');key='synthetic-delivery';tasks.accept(key,key)
            row=(await f.inbound(sender={'user_id':'333'},time=1700000000))[0];e=await f.framework_event(row)
            source=member_source('记住合成称呼',['鱼鱼']);ref=source['messages'][0]['member_ref']
            ctx=r.memory.prepare('111','a'*64,source,{ref:'333'}, {})
            req=dict(version=2,kind='group_turn',request_key='a'*64,epoch='fixture-epoch',source_digest=sha(source),must_reply=True,target_seq=1,addressing='mention')
            for k,v in dict(qq_router_trace='trace',qq_group_request=req,qq_v2_source=source,qq_memory_context=ctx,qq_connection=r.connection(),qq_delivery_key=key,qq_snapshot_range=[1,1]).items():e.set_extra(k,v)
            p=ReplyPlan('answer',('好。',),'好。');aux=dict(receipt=True,updates={'group':['合成称呼']},reason='valid')
            meta=metadata(req,'chatcmpl-synthetic','speak',p,source,1,memory_proposals=aux)
            raw=SimpleNamespace(model='workbuddy-local',id='chatcmpl-synthetic',choices=[SimpleNamespace(message=SimpleNamespace(content=p.canonical_text))],qqbot_group_plan=meta)
            response=SimpleNamespace(raw_completion=raw);run=SimpleNamespace(messages=[])
            for _ in range(2):await r.preserve_gateway_text(e,run,response)
            self.assertFalse(e.get_extra('qq_group_invalid'))
            final=e.get_extra('qq_delivery_plan');self.assertEqual(final.canonical_text,'好。')
            self.assertEqual(tasks.delivery(key)['content_sha256'],digest(final.canonical_text))
            tasks.begin_part(key,0);tasks.part_result(key,0,'sent','synthetic-ack')
            self.assertEqual(tasks.parts(key),[(0,'sent','synthetic-ack')])
            self.assertEqual(len(r.memory._load('111')['group']),1);self.assertEqual(r.memory._load('111')['_meta']['revision'],1)
            verify(e.get_extra('qq_group_metadata'),req,raw.id,final.canonical_text,OUTPUT,source,r.memory.cfg)
        finally:
            if tasks:tasks.db.close()
            await f.asyncTearDown();fixture.RouterTests.tearDownClass()
