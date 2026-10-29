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
    def test_first_write_reset_restart_group_isolation(self):
        ctx,source=self.turn();marker=next(iter(source['memory']['actors'].values()))
        self.assertEqual(source['memory']['records'],{})
        self.assertEqual(self.save(ctx,source,{'new_1':marker+' 爱手机摄影，也在学健康饮食。'})['result'],'saved')
        self.store.close(ctx);self.store.live.clear()
        restarted=MemoryStore(self.root,'10000',['20000','30000'],cfg=CFG)
        _,again=self.turn(restarted);self.assertEqual(next(iter(again['memory']['actors'].values())),marker)
        self.assertIn('手机摄影',next(iter(again['memory']['records'].values())))
        _,other=self.turn(restarted,'30000');self.assertEqual(other['memory']['records'],{})
    def test_full_unicode_and_expandable_configuration(self):
        for limit,file,total,budget in ((50000,1048576,8388608,524288),(100000,2097152,33554432,786432)):
            self.store.cfg=validate_config(CFG|dict(max_chars_per_group=limit,max_group_file_bytes=file,max_total_bytes=total))
            ctx,source=self.turn();updates={k:None for k in source['memory']['records']};updates['new_1']=('中🙂\\\"'*((limit+3)//4))[:limit]
            self.assertEqual(self.save(ctx,source,updates)['result'],'saved')
            ctx,source=self.turn();self.assertEqual(chars(source['memory']['records']),limit)
            valid_memory(source['memory'],cfg=self.store.cfg)
            source['memory']['actors']['p_'+'b'*16]='u_'+'c'*64 # absent actor is not a filter
            head=dict(must_reply=True,target_seq=source['target_seq'],addressing='mention')
            body=json.loads(fit(source,head,'policy',InputBudget(limit=budget)))
            self.assertEqual(body['memory'],source['memory'])
            with self.assertRaises(GatewayError):fit(source,head,'policy',InputBudget(limit=10000))
            ctx,source=self.turn();before=self.store.path('20000').read_bytes()
            self.assertEqual(self.save(ctx,source,{'new_1':'多'})['reason'],'capacity');self.assertEqual(before,self.store.path('20000').read_bytes())
    def test_atomic_merge_delete_and_no_semantic_gate(self):
        ctx,s=self.turn();self.save(ctx,s,{f'new_{i}':'自由概括含手机健康与猜测背景 '+str(i) for i in range(1,12)})
        ctx,s=self.turn();ids=list(s['memory']['records']);updates={k:None for k in ids[1:]};updates[ids[0]]='合并经历，可能是玩笑。'+'长'*300
        self.assertEqual(self.save(ctx,s,updates)['result'],'saved');_,s=self.turn();self.assertEqual(len(s['memory']['records']),1)
    def test_conflict_reentry_protocol_storage_and_noop(self):
        ctx,s=self.turn();other,t=self.turn();r=self.save(ctx,s,{'new_1':'新认识'})
        self.assertEqual(self.save(ctx,s,{'new_1':'不能重复'}) ,r)
        self.assertEqual(self.save(other,t,{'new_1':'并发'})['reason'],'conflict')
        for update,reason in (({},'no_action'),({'new_1':None},'protocol'),({'unknown':'x'},'protocol')):
            ctx,s=self.turn();before=self.store.path('20000').read_bytes()
            got=self.save(ctx,s,update);self.assertIn(got['reason'],(reason,'valid'));self.assertEqual(before,self.store.path('20000').read_bytes())
        ctx,s=self.turn();before=self.store.path('20000').read_bytes()
        with patch('qqbot_gateway.group_memory.os.replace',side_effect=OSError('synthetic')):
            self.assertEqual(self.save(ctx,s,{'new_1':'保存失败'})['result'],'failed')
        self.assertEqual(before,self.store.path('20000').read_bytes())
        self.assertEqual(auxiliary({'memory_updates':[]},s)['reason'],'protocol')
        self.assertEqual(auxiliary({},s)['reason'],'no_action')
    def test_schema1_migration_preserves_all_and_corrupt_file(self):
        path=self.store.path('20000');path.parent.mkdir(parents=True)
        old=dict(schema_version=1,namespace_hmac=self.store.namespace('20000'),records=[dict(id='a'*32,scope='member',subject_key='b'*64,fact='旧事实',status='candidate')],pending=[],purge=None)
        path.write_text(json.dumps(old),encoding='utf-8')
        doc=self.store._load('20000');self.assertEqual(doc['schema_version'],2);self.assertIn('尚未确认',doc['records']['a'*32]);self.assertTrue(path.with_name('schema1.before.json').exists())
        path.write_text('{"schema_version":2,"schema_version":1}',encoding='utf-8');before=path.read_bytes()
        with self.assertRaises(ValueError):self.store._load('20000')
        self.assertEqual(path.read_bytes(),before)
    def test_wire_aux_manifest_and_receipt_hash(self):
        ctx,s=self.turn();req=dict(must_reply=True,target_seq=s['target_seq'],addressing='mention');raw=dict(qqbot_turn_reply=2,decision='speak',kind='chat',bubbles=['好，以后叫你小青。'],meme_id=None,response_to_seq=1,mention=None,memory_updates={'new_1':'合成称呼小青'},memory_receipt=True)
        aux={};decision,p,response=plan(json.dumps(raw,ensure_ascii=False),OUTPUT,'合成',req,s,memory_out=aux)
        meta=metadata(req,'r1',decision,p,s,response,memory_proposals=aux)
        self.assertEqual(verify(meta,req,'r1',p.canonical_text,OUTPUT,s,self.store.cfg),p)
        saved=self.store.stage(ctx,aux,s);final=receipt_plan(p,saved,aux['receipt'],OUTPUT)
        self.assertIn('已保存到本群长期记忆',final.canonical_text)
        meta['plan']=final.metadata('r1');meta['plan_hash']=sha({k:v for k,v in meta.items() if k!='plan_hash'})
        self.assertEqual(verify(meta,req,'r1',final.canonical_text,OUTPUT,s,self.store.cfg),final)
        self.assertEqual(digest(final.canonical_text),meta['plan']['content_sha256'])
        broken=deepcopy(meta);broken['manifest'].pop('memory');broken['plan_hash']=sha({k:v for k,v in broken.items() if k!='plan_hash'})
        with self.assertRaises(ValueError):verify(broken,req,'r1',final.canonical_text,OUTPUT,s)
    def test_typed_meme_mention_receipt_preserves_parts(self):
        from qqbot_gateway.reply_plan import trusted_plan
        text=PreparedPart('text',digest('好'),'好','好','p_'+'a'*16);image=PreparedPart('image','b'*64,'m_'+'b'*64,'合成表情')
        p=ReplyPlan('chat',('好','合成表情'),'好\n合成表情',prepared_parts=(text,image))
        for result in ('saved','unchanged','failed'):
            final=receipt_plan(p,dict(result=result),True,OUTPUT)
            trusted=trusted_plan(final.metadata('r'),'\n'.join(final.bubbles),'r',OUTPUT)
            self.assertEqual(trusted.parts[-1],image);self.assertEqual(trusted.parts[0].mention_ref,text.mention_ref)
        self.assertIsNone(receipt_plan(None,dict(result='saved'),True,OUTPUT))

class WebMemoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_native_web_keeps_human_updates_prepared_and_no_tools(self):
        from qqbot_gateway.backends import BackendResult
        from qqbot_gateway.web_retrieval import WebRunner
        from types import SimpleNamespace
        from qqbot_gateway.reply_plan import DEFAULTS
        source=member_source('合成问题',['鱼鱼']);source['memory']=dict(generation='a'*32,base_revision=0,records={},actors={})
        request=dict(must_reply=True,target_seq=source['target_seq'],addressing='mention')
        raw=dict(qqbot_turn_reply=2,decision='speak',kind='chat',bubbles=['公开消息'],meme_id=None,response_to_seq=1,mention=None,memory_updates={'new_1':'本群人类的新称呼'},memory_receipt=True)
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
        source=member_source('合成目标',['鱼鱼']);source['memory']=dict(generation='a'*32,base_revision=0,records={'c'*32:'中'*60000},actors={})
        req=dict(version=2,kind='group_turn',request_key='a'*64,epoch='b'*64,config_version='c'*64,source_digest=sha(source),mode='free',addressing='mention',must_reply=True,target_seq=1,resource_caps=[])
        aux=dict(receipt=True,updates={'new_1':'本群合成称呼'},reason='valid')
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
            p=ReplyPlan('answer',('好。',),'好。');aux=dict(receipt=True,updates={'new_1':'合成称呼'},reason='valid')
            meta=metadata(req,'chatcmpl-synthetic','speak',p,source,1,memory_proposals=aux)
            raw=SimpleNamespace(model='workbuddy-local',id='chatcmpl-synthetic',choices=[SimpleNamespace(message=SimpleNamespace(content=p.canonical_text))],qqbot_group_plan=meta)
            response=SimpleNamespace(raw_completion=raw);run=SimpleNamespace(messages=[])
            for _ in range(2):await r.preserve_gateway_text(e,run,response)
            self.assertFalse(e.get_extra('qq_group_invalid'))
            final=e.get_extra('qq_delivery_plan');self.assertIn('已保存',final.canonical_text)
            self.assertEqual(tasks.delivery(key)['content_sha256'],digest(final.canonical_text))
            tasks.begin_part(key,0);tasks.part_result(key,0,'sent','synthetic-ack')
            self.assertEqual(tasks.parts(key),[(0,'sent','synthetic-ack')])
            self.assertEqual(len(r.memory._load('111')['records']),1);self.assertEqual(r.memory._load('111')['revision'],1)
            verify(e.get_extra('qq_group_metadata'),req,raw.id,final.canonical_text,OUTPUT,source,r.memory.cfg)
        finally:
            if tasks:tasks.db.close()
            await f.asyncTearDown();fixture.RouterTests.tearDownClass()
