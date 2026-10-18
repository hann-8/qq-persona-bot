"""ATT-01..12: synthetic identities only, no external services or private inputs."""
import asyncio
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1])]
from qqbot_gateway.attention import Attention,called,canonical
from qqbot_gateway.participation import validate_participation
from qqbot_gateway.turn_v2 import validate_header,validate_source,fit,sha,plan,metadata,verify,manifest
from qqbot_gateway.errors import GatewayError
from qqbot_gateway.reply_plan import DEFAULTS as OUTPUT
from qqbot_gateway.token_budget import InputBudget
from qqbot_gateway.session_queue import SessionError

def setup(limit=5):
    now=[100.]
    a=Attention(validate_participation({'mode':'free','attention':{'enabled':True}}),'e'*64,limit=limit,clock=lambda:now[0]);a.bot='222'
    return a,now

def ticket(a,text='肥鱼，看看',sender='333',ats=(),reply=None,group='111'):
    row,kind,required=a.observe(group,sender,str(a.window(group).seq+100),sender,text,ats,reply)
    return a.freeze(group,kind,row,required,'t')

def request(t):
    return dict(version=2,kind='group_turn',request_key='a'*64,epoch=t.epoch,config_version='b'*64,
        source_digest=sha(t.source),mode='free',addressing=t.addressing,must_reply=t.addressing in ('mention','direct_name','reply_bot','focused_followup'),
        target_seq=t.source['target_seq'],resource_caps=[])

def reply(**kwargs):
    return canonical(dict(qqbot_turn_reply=2,decision='speak',kind='chat',bubbles=['合成正文'],meme_id=None,
        response_to_seq=None,mention=None,memory_proposals=[])|kwargs)

class WireTests(unittest.TestCase):
    def test_trusted_identity_scope_and_per_ticket_random_refs(self):
        a,_=setup();one=ticket(a);two=ticket(a);other=ticket(a,group='444')
        refs=[t.source['messages'][0]['member_ref'] for t in (one,two,other)]
        self.assertEqual(len(set(refs)),3)
        self.assertEqual([t.identities[ref] for t,ref in zip((one,two,other),refs)],['333']*3)
        for change in ({'unknown':True},{'enabled':1},{'aliases':['']},{'aliases':['x']*2},{'focus_ttl_seconds':True},{'max_intervening_messages':1}):
            with self.subTest(change=change),self.assertRaises(ValueError):validate_participation({'attention':change})

    def test_ATT01_header_source_closed_types_digest(self):
        a,_=setup();t=ticket(a);r=request(t)
        self.assertEqual(validate_header(r),r);self.assertEqual(validate_source(canonical(t.source),r),t.source)
        for delta in ({'extra':1},{'version':True},{'target_seq':True},{'resource_caps':['forged']},{'must_reply':False},{'source_digest':'x'}):
            with self.subTest(delta=delta),self.assertRaises(GatewayError):validate_header(r|delta)
        for field,value in [('memory',{}),('member_candidates',[{}]),('images',[{}]),('target_seq',True),('web_anchor','unseen')]:
            obj=copy.deepcopy(t.source);obj[field]=value
            with self.subTest(field=field),self.assertRaises(GatewayError):validate_source(canonical(obj),r|{'source_digest':sha(obj)})
        with self.assertRaises(GatewayError):validate_source(canonical(t.source)[:-1]+',"focus":null}',r)

    def test_ATT02_aux_invalid_preserves_text_and_fixed_target(self):
        a,_=setup();t=ticket(a);r=request(t)
        decision,p,response=plan(reply(response_to_seq=999,mention={'member_ref':'123'},memory_proposals=[{'op':'danger'}]),OUTPUT,'',r,t.source)
        self.assertEqual((decision,p.canonical_text,response),('speak','合成正文',t.source['target_seq']))
        value=metadata(r,'r','speak',p,t.source,response)
        self.assertEqual(verify(value,r,'r',p.canonical_text,OUTPUT,t.source),p)
        for key,val in [('effective_digest','a'*64),('request',r|{'epoch':'c'*64}),('response_to_seq',999)]:
            bad=copy.deepcopy(value);bad[key]=val;bad['plan_hash']=sha({k:v for k,v in bad.items() if k!='plan_hash'})
            with self.assertRaises(ValueError):verify(bad,r,'r',p.canonical_text,OUTPUT,t.source)

    def test_ATT03_bad_core_never_salvages_aux(self):
        a,_=setup();t=ticket(a);r=request(t)
        for raw in (reply()[:-1]+',"decision":"speak"}',reply(qqbot_turn_reply=True),reply(bubbles=['<tool_call>x</tool_call>']),reply(extra='x')):
            decision,p,response=plan(raw,OUTPUT,'',r,t.source)
            self.assertIsNone(response);self.assertIsNotNone(p);self.assertIsNotNone(p.fallback_reason)

    def test_ATT04_frozen_target_and_dependencies_survive_trim(self):
        small,_=setup();small.cfg['context_max_bytes']=4096
        large=ticket(small,'肥鱼，请看'+'长'*1990)
        self.assertEqual(small.rebuild(large)['target_seq'],large.source['target_seq'])
        self.assertTrue(small.rebuild(large)['messages'])
        a,_=setup();first=ticket(a);a.acknowledge(first,[('说说细节','800')],first.source['target_seq'])
        follow=ticket(a,'你能解释吗');frozen=copy.deepcopy(follow.source)
        for n in range(100):ticket(a,'后到文字'+str(n),sender='444')
        rebuilt=a.rebuild(follow)
        self.assertEqual(rebuilt['focus'],frozen['focus'])
        for row in frozen['messages']:self.assertIn(row,rebuilt['messages'])
        self.assertEqual(follow.addressing,'focused_followup')
        a,_=setup();base=ticket(a)
        a.acknowledge(base,[('已确认文字','799')],base.source['target_seq'])
        mentioned=ticket(a,'继续',ats=['222'],reply='799')
        self.assertEqual(mentioned.addressing,'mention')
        self.assertTrue(any(r['member_ref']=='bot' and r['text']=='已确认文字' for r in mentioned.source['messages']))
        validate_source(canonical(mentioned.source),request(mentioned))
        a.acknowledge(base,[('鲸'*3000,str(n+800)) for n in range(3)],base.source['target_seq'])
        with self.assertRaises(SessionError):ticket(a,'你能解释吗'+'鱼'*1990)

    def test_ATT05_call_focus_interruption_reply_and_expiry(self):
        a,now=setup();t=ticket(a,'肥鱼');self.assertEqual(t.addressing,'direct_name')
        for text in ['肥鱼很可爱','他说肥鱼，来','“肥鱼”','```肥鱼```','http://x/肥鱼','DSHing']:
            self.assertFalse(called(text,a.cfg['attention']['aliases']),text)
        a.acknowledge(t,[('具体要什么','800')],t.source['target_seq'])
        self.assertEqual(ticket(a,'你能讲吗').addressing,'focused_followup')
        self.assertEqual(ticket(a,'再具体一点').addressing,'focused_candidate')
        now[0]+=61;self.assertEqual(ticket(a,'你能讲吗').addressing,'ambient')
        self.assertEqual(ticket(a,'说明一下',reply='800').addressing,'reply_bot')
        self.assertEqual(ticket(a,'肥鱼，说明',ats=['444']).addressing,'ambient')
        self.assertEqual(ticket(a,'肥鱼，说明',reply='unknown').addressing,'ambient')
        a.acknowledge(t,[('继续','801')],t.source['target_seq'])
        ticket(a,'插话',sender='444');self.assertEqual(ticket(a,'你能讲吗').addressing,'ambient')
        a.invalidate();self.assertEqual(ticket(a,'说明',reply='800').addressing,'ambient')

    def test_ATT08_ack_target_not_carrier_and_text_only(self):
        a,_=setup();t=ticket(a,'随便聊聊',sender='333');other=ticket(a,'给个例子',sender='444')
        t.source=a.rebuild(t)
        a.acknowledge(t,[('合成答复','800')],other.source['target_seq'])
        self.assertEqual(a.state('111').focus['sender'],'444')
        self.assertEqual(ticket(a,'你怎么看',sender='333').addressing,'ambient')
        a.state('111').focus=None;a.acknowledge(t,[],other.source['target_seq']);self.assertIsNone(a.state('111').focus)
        a.acknowledge(t,[('答复','801')],None);self.assertIsNone(a.state('111').focus)

    def test_ATT09_final_fit_closes_refs_and_protects_dependencies(self):
        a,_=setup()
        for i in range(15):ticket(a,'旧材料'*90,sender=str(i))
        t=ticket(a);source=a.rebuild(t);r=request(t)|{'source_digest':sha(source)}
        original=len(source['messages'])
        source['messages'][-1]['reply_seq']=source['messages'][0]['seq'];r['source_digest']=sha(source)
        budget=InputBudget(limit=3000,overhead=0,output=0)
        body=fit(source,r,'policy',budget);effective=json.loads(body)
        self.assertLess(len(effective['messages']),original);self.assertIn(t.source['target_seq'],manifest(effective)['seqs'])
        self.assertEqual(effective['messages'][-1]['reply_seq'],'unresolved')
        p=plan(reply(),OUTPUT,'',r,effective)[1];m=metadata(r,'r','speak',p,effective,r['target_seq'])
        verify(m,r,'r',p.canonical_text,OUTPUT,source)
        with self.assertRaises(GatewayError):fit(source,r,'x'*4000,budget)

    def test_ATT10_single_anchors_and_future_empty(self):
        a,_=setup();t=ticket(a);r=request(t)
        for key in ('web_anchor','meme_question'):
            source=copy.deepcopy(t.source);source[key]=source['messages'][0]['text']
            validate_source(canonical(source),r|{'source_digest':sha(source)})
            source[key]=canonical(source)
            with self.assertRaises(GatewayError):validate_source(canonical(source),r|{'source_digest':sha(source)})

    def test_ATT11_off_defaults_and_persona_version(self):
        from qqbot_gateway.persona import compose_persona,session_version
        import yaml
        from qqbot_gateway.config import normalize_settings
        settings=yaml.safe_load((Path(__file__).resolve().parents[1]/'config/settings.example.yaml').read_text(encoding='utf-8'))
        settings['bot']['qq']='222';settings['access'].update(allowed_groups=['111'],admin_users=['333'])
        settings=normalize_settings(settings)
        for mode in ('mentions','free'):
            settings['participation']['mode']=mode
            old=copy.deepcopy(settings);old['participation'].pop('attention')
            args=lambda s:compose_persona('角色',s['output'],s['web'],s['participation'],s['memes'])
            self.assertEqual(args(old),args(settings));self.assertEqual(session_version(args(old),old),session_version(args(settings),settings))
        settings['participation']['mode']='mentions';settings['participation']['attention']['enabled']=True
        self.assertNotIn('关注协议v2',args(settings))

    def test_ATT12_export_only_owned_keys_and_double_digest(self):
        import yaml,hashlib
        from qqbot_gateway.config import export_legacy_config,activate_legacy_config
        settings=yaml.safe_load((Path(__file__).resolve().parents[1]/'config/settings.example.yaml').read_text(encoding='utf-8'))
        settings['bot']['qq']='222';settings['access'].update(allowed_groups=['111'],admin_users=['333']);settings['extension']={'keep':17}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir();p=root/'config/settings.local.yaml';p.write_text(yaml.safe_dump(settings),encoding='utf-8')
            before=p.read_bytes();value=export_legacy_config(p)
            self.assertEqual(p.read_bytes(),before);self.assertFalse(value['activated'])
            legacy=Path(value['review']).read_bytes();obj=yaml.safe_load(legacy)
            self.assertNotIn('attention',obj['participation']);self.assertEqual(obj['extension'],{'keep':17})
            self.assertEqual(value['legacy_digest'],hashlib.sha256(legacy).hexdigest());self.assertEqual(Path(value['backup']).read_bytes(),before)
            with patch('qqbot_gateway.config.require_stopped',side_effect=ValueError('running')):
                with self.assertRaises(ValueError):export_legacy_config(p)
            for source_sha,copy_sha in [('0'*64,value['legacy_digest']),(value['source_digest'],'0'*64)]:
                with self.assertRaises(ValueError):activate_legacy_config(p,value['review'],source_sha,copy_sha,'已核对')
            with self.assertRaises(ValueError):activate_legacy_config(p,value['review'],value['source_digest'],value['legacy_digest'],'')
            activate_legacy_config(p,value['review'],value['source_digest'],value['legacy_digest'],'已核对')
            self.assertEqual(p.read_bytes(),legacy)

class DispatchTests(unittest.IsolatedAsyncioTestCase):
    async def test_ATT05_gate_trusted_at_relations_no_name_or_attachment_RPC(self):
        import aiohttp
        from types import SimpleNamespace
        from qqbot_gateway.config import GateConfig
        from qqbot_gateway.onebot_gate import OneBotGate
        with tempfile.TemporaryDirectory() as directory:
            cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,Path(directory)/'gate.db',
                blocked_users=frozenset({'999'}),participation_mode='free',attention_enabled=True)
            gate=OneBotGate(cfg)
            base=dict(post_type='message',message_type='group',self_id=222,group_id=111,user_id=333,message_id=1,
                qqbot_at_ids=['spoof'],qqbot_reference='spoof',message=[dict(type='text',data=dict(text='肥鱼，你能解释吗')),
                    dict(type='at',data=dict(qq='444')),dict(type='at',data=dict(qq='all')),
                    dict(type='reply',data=dict(id='unknown',text='untrusted embedded')),
                    dict(type='image',data=dict(url='https://invalid.example/never-fetch'))])
            async def frames():
                for value in (base|{'user_id':999},base,base):yield SimpleNamespace(type=aiohttp.WSMsgType.TEXT,data=json.dumps(value))
            class Upstream:
                def __init__(self):self.values=[]
                async def send_json(self,value):self.values.append(value)
            upstream=Upstream()
            try:
                await gate._incoming(frames(),upstream,set());self.assertEqual(len(upstream.values),1)
                value=upstream.values[0];self.assertEqual(value['qqbot_at_ids'],['444','other_member'])
                self.assertEqual(value['qqbot_reference'],'unknown');self.assertNotIn('never-fetch',str(value));self.assertNotIn('untrusted embedded',str(value))
                self.assertFalse(any(s['type']=='at' for s in value['message']))
            finally:gate.store.close()

    async def test_ATT01_HTTP_negotiation_config_mode_and_duplicate_top_keys(self):
        from aiohttp.test_utils import TestClient,TestServer
        from qqbot_gateway.model_gateway import application,ModelQueue
        class Runner:
            attempts=0
            async def run(self,*args):self.attempts+=1;return reply()
        a,_=setup();t=ticket(a);r=request(t);runner=Runner()
        app=application(ModelQueue(runner),'t'*32,v2=dict(mode='free',config_version=r['config_version'],aliases=t.source['self']['names']))
        async with TestClient(TestServer(app)) as client:
            payload=dict(model='workbuddy-local',stream=False,messages=[dict(role='user',content=canonical(t.source))],qqbot_request=r)
            headers={'Authorization':'Bearer '+'t'*32,'X-QQBot-Trace':'c'*32}
            response=await client.post('/v1/chat/completions',json=payload,headers=headers)
            self.assertEqual(response.status,200);obj=await response.json();self.assertEqual(obj['id'],'chatcmpl-'+'c'*32)
            verify(obj['qqbot_group_plan'],r,obj['id'],obj['choices'][0]['message']['content'],OUTPUT,t.source)
            self.assertEqual(runner.attempts,1)
            for change in ({'config_version':'d'*64},{'mode':'mentions','kind':'member_turn'}):
                response=await client.post('/v1/chat/completions',json=payload|{'qqbot_request':r|change},headers=headers)
                self.assertEqual(response.status,422)
            response=await client.post('/v1/chat/completions',data=canonical(payload)[:-1]+',"stream":false}',headers=headers)
            self.assertEqual(response.status,422);self.assertEqual(runner.attempts,1)
        async with TestClient(TestServer(application(ModelQueue(runner),'t'*32))) as client:
            response=await client.post('/v1/chat/completions',json=payload,headers=headers)
            self.assertEqual(response.status,422);self.assertEqual(runner.attempts,1)

    async def test_ATT10_v2_web_one_anchor_same_generation_no_history_upload(self):
        from qqbot_gateway.web_retrieval import WebRunner,Retrieval
        from qqbot_gateway.web_policy import DEFAULTS as WEB
        from qqbot_gateway.token_budget import dialog_text
        class Reader:
            cfg=WEB|{'enabled':True};last_audit={}
            def __init__(self):self.questions=[]
            async def retrieve(self,q):
                self.questions.append(q)
                return Retrieval('read',[dict(url='https://example.com/',title='公开材料',text='public evidence '*50,status='body')])
        class Runner:
            attempts=0
            async def run(self,system,prompt,request_id):self.attempts+=1;self.prompt=prompt;return reply(kind='answer')
        a,_=setup();ticket(a,'不会外发的群窗口');t=ticket(a,'肥鱼，请看https://example.com/');source=a.rebuild(t)
        source['web_anchor']=source['messages'][-1]['text'];r=request(t)|{'source_digest':sha(source)}
        reader=Reader();runner=Runner();wrapped=WebRunner(runner,reader,InputBudget(),OUTPUT)
        result=await wrapped.run_group('policy',dialog_text([dict(role='user',content=canonical(source))]),'r',r)
        self.assertEqual(reader.questions,[source['web_anchor']]);self.assertEqual(runner.attempts,1)
        self.assertIn('来源：',result.text);self.assertEqual(result.response_to_seq,source['target_seq'])
        self.assertIn('public evidence',runner.prompt)

    async def test_ATT06_candidate_rolling_across_focus_versions_and_silent(self):
        a,now=setup()
        for i in range(5):
            base=ticket(a);a.acknowledge(base,[('问句',str(i+800))],base.source['target_seq'])
            t=ticket(a,'好的');self.assertEqual(t.addressing,'focused_candidate')
            if i<4:
                lease=await a.dispatch(t,lambda:True);a.finish(lease)
                self.assertEqual(plan(reply(decision='silent',bubbles=[]),OUTPUT,'',request(t),t.source),('silent',None,None))
            else:
                with self.assertRaises(SessionError):await a.dispatch(t,lambda:True)
        now[0]+=60;t=ticket(a,'肥鱼');a.acknowledge(t,[('问句','900')],t.source['target_seq'])
        t=ticket(a,'好的');await a.dispatch(t,lambda:True);a.finish(t)

    async def test_ATT07_priority_reserve_FIFO_Q0_and_single_activity(self):
        a,_=setup();active=ticket(a);await a.dispatch(active,lambda:True)
        tasks=[];tickets=[]
        try:
            for text,ats in [('普通',()),('肥鱼，A',()),('肥鱼，B',()),('真@A',('222',)),('真@B',('222',))]:
                t=ticket(a,text,ats=ats);tickets.append(t);tasks.append(asyncio.create_task(a.dispatch(t,lambda:True)));await asyncio.sleep(.02)
            self.assertEqual(len(a.pending),5)
            with self.assertRaises(SessionError):await a.dispatch(ticket(a,'肥鱼，满了'),lambda:True)
            self.assertFalse(any(task.done() for task in tasks))
            a.finish(active)
            for index in (3,4,1,2,0):
                self.assertIs(await asyncio.wait_for(tasks[index],1),tickets[index]);a.finish(tickets[index]);a.finish(tickets[index])
            self.assertIsNone(a.current);self.assertFalse(a.pending)
        finally:
            for task in tasks:task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
        a,_=setup(0);first=ticket(a);await a.dispatch(first,lambda:True)
        with self.assertRaises(SessionError):await a.dispatch(ticket(a,ats=['222']),lambda:True)
        a.finish(first);await a.dispatch(ticket(a,'随便'),lambda:True)

    async def test_ATT04_direct_queue_past_focus_TTL_and_candidate_age_timeout_cancel(self):
        a,now=setup();base=ticket(a);a.acknowledge(base,[('问题','800')],base.source['target_seq'])
        active=ticket(a);await a.dispatch(active,lambda:True)
        direct=ticket(a,'你能解释吗');candidate=ticket(a,'再详细一点')
        d=asyncio.create_task(a.dispatch(direct,lambda:True));c=asyncio.create_task(a.dispatch(candidate,lambda:True));await asyncio.sleep(.02)
        now[0]+=91;a.finish(active);self.assertIs(await d,direct);a.finish(direct)
        with self.assertRaises(SessionError):await c
        active=ticket(a);await a.dispatch(active,lambda:True)
        waiting=asyncio.create_task(a.dispatch(ticket(a,ats=['222']),lambda:True));await asyncio.sleep(.02)
        waiting.cancel()
        with self.assertRaises(asyncio.CancelledError):await waiting
        self.assertFalse(a.pending);a.finish(active)

    async def test_ATT07_frozen_bytes_group_limit_timeout_and_invalidate(self):
        a,now=setup();active=ticket(a);await a.dispatch(active,lambda:True)
        a.cfg['attention']['direct_queue_limit']=1
        first=ticket(a);task=asyncio.create_task(a.dispatch(first,lambda:True));await asyncio.sleep(.02)
        with self.assertRaises(SessionError):await a.dispatch(ticket(a),lambda:True)
        now[0]+=601
        with self.assertRaises(SessionError):await task
        a.finish(active);a.finish(first)
        active=ticket(a);await a.dispatch(active,lambda:True)
        first=ticket(a,ats=['222']);first.size=262145
        with self.assertRaises(SessionError):await a.dispatch(first,lambda:True)
        first=ticket(a,ats=['222']);task=asyncio.create_task(a.dispatch(first,lambda:True));await asyncio.sleep(.02)
        a.invalidate()
        with self.assertRaises(SessionError):await task
        a.finish(active);self.assertIsNone(a.current)

if __name__=='__main__':unittest.main()
