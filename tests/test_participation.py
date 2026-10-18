import asyncio
import json
from pathlib import Path
import sys
import tempfile
from dataclasses import replace
import unittest
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1])]
from qqbot_gateway.participation import Participation,DEFAULTS,validate_participation
from qqbot_gateway.group_protocol import group_plan,validate_request,metadata,verify_metadata,SILENT
from qqbot_gateway.reply_plan import DEFAULTS as OUTPUT,digest,ReplyPlan
from qqbot_gateway.errors import GatewayError
from qqbot_gateway.contracts import normalize_request
from qqbot_gateway.task_store import TaskStore
from qqbot_gateway.onebot_gate import admitted_message,OneBotGate
from qqbot_gateway.config import GateConfig,normalize_settings
from qqbot_gateway.session_queue import SessionError


def request(body='body',mention=False):
    return dict(version=1,kind='group_turn',trigger='mention' if mention else 'ambient',must_reply=mention,
                epoch='e'*64,snapshot_digest=digest(body),request_key='f'*64)


def reply(decision='speak',**kwargs):
    return json.dumps(dict(qqbot_group_reply=1,decision=decision,kind='chat',bubbles=[] if decision=='silent' else ['甲','乙'],meme_id=None)|kwargs,ensure_ascii=False)


class ProtocolTests(unittest.TestCase):
    def test_defaults_and_rejected_ranges_types(self):
        self.assertEqual({k:v for k,v in validate_participation({}).items() if k!='attention'},DEFAULTS)
        self.assertIs(validate_participation({})['attention']['enabled'],False)
        for value in ({'mode':'auto'},{'context_messages':True},{'context_messages':201},{'debounce_seconds':0},
                      {'max_batch_wait_seconds':2,'debounce_seconds':3},{'allow_ambient_web':'true'},{'probability':.3}):
            with self.subTest(value=value),self.assertRaises(ValueError):validate_participation(value)

    def test_schema_missing_defaults_and_quote_false(self):
        import yaml
        cfg=yaml.safe_load((Path(__file__).resolve().parents[1]/'config/settings.example.yaml').read_text(encoding='utf-8'))
        cfg['bot']['qq']='222';cfg['access'].update(allowed_groups=['111'],admin_users=['333'])
        cfg.pop('participation');normalized=normalize_settings(cfg)
        self.assertEqual(normalized['participation']['mode'],'mentions');self.assertIs(normalized['output']['quote_reply'],False)
        cfg['output']['quote_reply']=True
        with self.assertRaises(ValueError):normalize_settings(cfg)

    def test_single_and_adaptive_group_protocol(self):
        for mode,count in (('single',1),('adaptive',2)):
            decision,plan=group_plan(reply(),OUTPUT|{'delivery_mode':mode},'',False)
            self.assertEqual(decision,'speak');self.assertEqual(len(plan.bubbles),count)
            self.assertEqual(plan.canonical_text,'甲\n乙')

    def test_silent_and_must_reply_fallback(self):
        self.assertEqual(group_plan(reply('silent'),OUTPUT,'',False),('silent',None))
        decision,plan=group_plan(reply('silent'),OUTPUT,'',True)
        self.assertEqual(decision,'error');self.assertIn('没接住',plan.canonical_text)

    def test_invalid_output_never_leaks_envelope(self):
        for raw in ('', '{}',reply(bubbles=[]),reply(bubbles=['']),reply(kind='tool'),
                    reply(qqbot_group_reply=True),reply()[:-1]+',"decision":"speak"}',reply(bubbles=['<tool_call>bad</tool_call>'])):
            with self.subTest(raw=raw):
                self.assertEqual(group_plan(raw,OUTPUT,'',False),('error',None))
                decision,plan=group_plan(raw,OUTPUT,'',True)
                self.assertEqual(decision,'error');self.assertNotIn('qqbot_',plan.canonical_text)

    def test_strict_request_digest_and_no_personal_dialog(self):
        body=json.dumps(dict(must_reply=False,target_seq=None,web_anchor=None,messages=[dict(seq=1,speaker='u1',name='n',text='body',reply=None)]))
        req=request(body);self.assertEqual(validate_request(req),req)
        payload=dict(model='workbuddy-local',messages=[dict(role='user',content=body)],qqbot_request=req)
        normalize_request(payload)
        for change in ({'extra':1},{'must_reply':True},{'epoch':'x'},{'version':True},{'trigger':'timer'}):
            with self.assertRaises(GatewayError):validate_request(req|change)
        with self.assertRaises(GatewayError):normalize_request(payload|{'messages':[dict(role='user',content='spoof')]})
        with self.assertRaises(GatewayError):normalize_request(payload|{'messages':[dict(role='user',content='old'),dict(role='assistant',content='old'),dict(role='user',content=body)]})

    def test_metadata_bound_to_request_response_text(self):
        req=request();plan=group_plan(reply(),OUTPUT,'',False)[1];value=metadata(req,'r', 'speak',plan)
        self.assertEqual(verify_metadata(value,req,'r',plan.canonical_text,OUTPUT),plan)
        for wrong in (value|{'response_id':'wrong'},value|{'decision':'silent'},value|{'request':req|{'epoch':'d'*64}}):
            with self.assertRaises(ValueError):verify_metadata(wrong,req,'r',plan.canonical_text,OUTPUT)
        with self.assertRaises(ValueError):verify_metadata(value,req,'r','changed',OUTPUT)
        self.assertIsNone(verify_metadata(metadata(req,'s','silent',None),req,'s',SILENT,OUTPUT))


class WindowTests(unittest.TestCase):
    def setUp(self):
        self.now=0;self.p=Participation(DEFAULTS,'epoch',clock=lambda:self.now)

    def test_window_bounds_aliases_ttl_and_untrusted_reference(self):
        for i in range(100):self.p.append('g','user'+str(i),str(i),'name\x00','x'*2000,reply='blocked-message')
        w=self.p.window('g');self.assertLessEqual(len(w.rows),60);self.assertLessEqual(len(json.dumps(list(w.rows),ensure_ascii=False).encode()),32768)
        self.assertLessEqual(len(w.aliases),len(w.rows))
        rows=self.p.snapshot('g');self.assertNotIn('\x00',str(rows));self.assertEqual(rows[-1]['reply'],'引用未解析')
        self.assertNotIn('sender',rows[-1]);self.assertNotIn('mid',rows[-1])
        self.now=901;self.assertEqual(self.p.snapshot('g'),[])

    def test_known_reference_group_isolation_and_immutable_snapshot(self):
        self.p.append('a','u','1','n','one');snapshot=self.p.snapshot('a')
        self.p.append('a','v','2','n','two','1');self.assertEqual(self.p.snapshot('a')[-1]['reply'],1)
        self.p.append('b','v','3','n','three','1');self.assertEqual(self.p.snapshot('b')[-1]['reply'],'引用未解析')
        self.assertEqual(len(snapshot),1);self.assertEqual(snapshot[0]['text'],'one')

    def test_reset_only_one_group_and_disconnect_epoch(self):
        self.p.append('a','u','1','n','one');self.p.append('b','u','2','n','two')
        a=self.p.group_epoch('a');b=self.p.group_epoch('b');self.p.reset('a')
        self.assertNotEqual(a,self.p.group_epoch('a'));self.assertEqual(b,self.p.group_epoch('b'))
        self.p.invalidate();self.assertEqual(self.p.snapshot('b'),[]);self.assertNotEqual(b,self.p.group_epoch('b'))

    def test_cooldown_frequency_only_ambient(self):
        w=self.p.window('g');self.assertTrue(self.p.may_speak('g'));w.spoken.append(0)
        self.assertFalse(self.p.may_speak('g'));self.now=16;self.assertTrue(self.p.may_speak('g'))
        w.spoken.extend([15,16,17]);self.assertFalse(self.p.may_speak('g'));self.now=78;self.assertTrue(self.p.may_speak('g'))


class SchedulingTests(unittest.IsolatedAsyncioTestCase):
    async def test_gate_free_sanitizes_before_actual_framework_boundary(self):
        import aiohttp
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as directory:
            cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,Path(directory)/'gate.db',blocked_users=frozenset({'333'}),participation_mode='free')
            gate=OneBotGate(cfg)
            base=dict(post_type='message',message_type='group',self_id=222,group_id=111,user_id=444,message_id=1,
                raw_message='PRIVATE RAW',message=[dict(type='text',data=dict(text='hello')),
                dict(type='reply',data=dict(id='old',text='PRIVATE EMBEDDED')),dict(type='forward',data=dict(content='PRIVATE FORWARD')),
                dict(type='image',data=dict(url='https://private.invalid/image'))])
            async def frames():
                for value in (base|{'user_id':333},base,base):yield SimpleNamespace(type=aiohttp.WSMsgType.TEXT,data=json.dumps(value))
            class Upstream:
                def __init__(self):self.values=[]
                async def send_json(self,value):self.values.append(value)
            upstream=Upstream();await gate._incoming(frames(),upstream,set())
            self.assertEqual(len(upstream.values),1)
            value=upstream.values[0];self.assertNotIn('PRIVATE',str(value));self.assertNotIn('private.invalid',str(value))
            self.assertEqual(value['qqbot_reference'],'old');self.assertEqual(value['qqbot_connection'],gate.connection_id)
            self.assertTrue(value['qqbot_media']);self.assertTrue(all(s['type']=='text' for s in value['message']))
            self.assertEqual(gate.store.db.execute('SELECT count(*) FROM seen').fetchone()[0],1);gate.store.close()

    async def test_group_web_anchor_only_no_snapshot_upload(self):
        from qqbot_gateway.web_retrieval import WebRunner,Retrieval
        from qqbot_gateway.web_policy import DEFAULTS as WEB
        from qqbot_gateway.token_budget import InputBudget,dialog_text
        class Reader:
            cfg=WEB|{'enabled':True};private_ids=();last_audit={}
            def __init__(self):self.questions=[]
            async def retrieve(self,question):
                self.questions.append(question);return Retrieval('search',notice='搜索未通过质量门槛')
        class Runner:
            attempts=0
            async def run(self,*args):self.attempts+=1;return reply('silent')
        reader=Reader();runner=Runner();wrapper=WebRunner(runner,reader,InputBudget(),OUTPUT)
        rows=[dict(speaker='u1',text='私人闲聊不要外发'),dict(speaker='u2',text='搜索月球半径')]
        body=dict(messages=rows,web_anchor='搜索月球半径')
        result=await wrapper.run_group('policy',dialog_text([dict(role='user',content=json.dumps(body))]),'r',request())
        self.assertTrue(result.web_expired);self.assertEqual(reader.questions,['搜索月球半径']);self.assertEqual(runner.attempts,0)
        # The same old question in the RAM snapshot does not trigger another lookup.
        body['web_anchor']=None
        await wrapper.run_group('policy',dialog_text([dict(role='user',content=json.dumps(body))]),'r',request())
        self.assertEqual(reader.questions,['搜索月球半径']);self.assertEqual(runner.attempts,1)
        wrapper.allow_ambient_web=False;body['web_anchor']='搜索月球半径'
        await wrapper.run_group('policy',dialog_text([dict(role='user',content=json.dumps(body))]),'r',request())
        self.assertEqual(reader.questions,['搜索月球半径']);self.assertEqual(runner.attempts,2)

    async def test_group_web_single_generation_and_sources_or_silent(self):
        from qqbot_gateway.web_retrieval import WebRunner,Retrieval
        from qqbot_gateway.web_policy import DEFAULTS as WEB
        from qqbot_gateway.token_budget import InputBudget,dialog_text
        class Reader:
            cfg=WEB|{'enabled':True};private_ids=();last_audit={}
            async def retrieve(self,q):return Retrieval('read',[dict(url='https://example.com/',title='test',text='public evidence '*40,status='body')])
        class Runner:
            attempts=0;text=reply()
            async def run(self,*args):self.attempts+=1;return self.text
        runner=Runner();wrapper=WebRunner(runner,Reader(),InputBudget(),OUTPUT)
        body=dict(messages=[dict(speaker='u1',text='https://example.com/')],web_anchor='https://example.com/')
        prompt=dialog_text([dict(role='user',content=json.dumps(body))])
        result=await wrapper.run_group('policy',prompt,'r',request())
        self.assertEqual(runner.attempts,1);self.assertEqual(result.prepared_plan.kind,'answer');self.assertIn('来源：',result.text)
        runner.text=reply(kind='answer',bubbles=['```\n**literal**\n```'])
        result=await wrapper.run_group('policy',prompt,'r',request())
        self.assertTrue(result.text.startswith('**literal**'))
        runner.text=reply('silent');result=await wrapper.run_group('policy',prompt,'r',request())
        self.assertEqual(runner.attempts,3);self.assertIsNone(result.prepared_plan)
        body['web_anchor']='forged anchor'
        with self.assertRaises(GatewayError):await wrapper.run_group('policy',dialog_text([dict(role='user',content=json.dumps(body))]),'r',request())

    async def test_multiplayer_batch_max_wait_and_no_new_message_no_work(self):
        now=[0.];p=Participation(DEFAULTS,'e',clock=lambda:now[0]);calls=0
        async def advance(delay):now[0]+=delay;await real_sleep(0)
        real_sleep=asyncio.sleep
        with patch('qqbot_gateway.participation.asyncio.sleep',advance):
            async def owner():return await p.batch('g',lambda:True)
            task=asyncio.create_task(owner());await real_sleep(0)
            for _ in range(80):
                if task.done():break
                await p.batch('g',lambda:True);await real_sleep(0)
            self.assertTrue(await task);self.assertLessEqual(now[0],5.1)
        self.assertIsNone(p.window('g').candidate);self.assertEqual(p.tickets,[])

    async def test_mention_preempts_pending_batch(self):
        p=Participation(DEFAULTS,'e');task=asyncio.create_task(p.batch('g',lambda:True));await asyncio.sleep(0)
        lease=await p.acquire('g',True,lambda:True);lease.release()
        self.assertFalse(await task)

    async def test_global_priority_bounded_and_fair_rotation(self):
        p=Participation(DEFAULTS,'e',limit=4,timeout=1)
        active=await p.acquire('a',False,lambda:True)
        a=asyncio.create_task(p.acquire('a',False,lambda:True));b=asyncio.create_task(p.acquire('b',False,lambda:True))
        await asyncio.sleep(.01)
        mention=asyncio.create_task(p.acquire('c',True,lambda:True));await asyncio.sleep(.01)
        self.assertTrue(p.mention_pending());self.assertFalse(p.may_speak('a'))
        active.release();lease=await mention;self.assertFalse(a.done());lease.release()
        # c was last; next waiting ambient is a, then b.
        lease=await a;lease.release();lease=await b;lease.release();self.assertFalse(p.active)

    async def test_each_mention_ticket_no_cooldown_queue_full_timeout_cancel(self):
        p=Participation(DEFAULTS|{'mention_queue_limit':1},'e',limit=2,timeout=.05)
        active=await p.acquire('g',False,lambda:True)
        one=asyncio.create_task(p.acquire('g',True,lambda:True));await asyncio.sleep(.001)
        with self.assertRaises(SessionError):await p.acquire('g',True,lambda:True)
        with self.assertRaises(SessionError):await one
        active.release();self.assertFalse(p.tickets)
        lease=await p.acquire('g',True,lambda:True);lease.release()
        active=await p.acquire('g',False,lambda:True)
        waiting=asyncio.create_task(p.acquire('h',True,lambda:True));await asyncio.sleep(.001);waiting.cancel()
        await asyncio.gather(waiting,return_exceptions=True);active.release();self.assertFalse(p.active or p.tickets)

    async def test_rate_defers_same_candidate_without_new_timer_turn(self):
        now=[0.];cfg=DEFAULTS|{'min_evaluation_interval_seconds':5};p=Participation(cfg,'e',clock=lambda:now[0])
        p.window('g').evaluations.append(0)
        real_sleep=asyncio.sleep
        async def advance(delay):now[0]+=delay;await real_sleep(0)
        with patch('qqbot_gateway.participation.asyncio.sleep',advance):self.assertTrue(await p.batch('g',lambda:True))
        self.assertGreaterEqual(now[0],5);self.assertIsNone(p.window('g').candidate)

    async def test_ram_ledger_recovery_unknown_and_manual_review(self):
        class Manager:
            def __getattr__(self,name):raise AssertionError('Personal history touched')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'tasks.sqlite';store=TaskStore(path);store.accept('k','t')
            store.prepare_group_delivery('k','g','epoch','r',ReplyPlan('answer',('bot',),'bot'),'h',[1,2])
            store.begin_part('k',0);store.close();store=TaskStore(path)
            await store.recover_deliveries(Manager());self.assertFalse(store.group_blocked('g'))
            store.review_group('g');self.assertFalse(store.group_blocked('g'));self.assertEqual(store.delivery('k')['state'],'unknown')
            self.assertFalse(store.begin_part('k',0));store.close()


class GateFreeTests(unittest.TestCase):
    def test_free_blacklist_first_and_no_history_action(self):
        from qqbot_gateway.onebot_gate import allowed_action
        with tempfile.TemporaryDirectory() as d:
            cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,Path(d)/'db',blocked_users=frozenset({'333'}),participation_mode='free')
            base=dict(post_type='message',message_type='group',self_id=222,group_id=111,user_id=444,message=[dict(type='text',data=dict(text='hello'))])
            self.assertTrue(admitted_message(base,cfg));self.assertFalse(admitted_message(base|{'user_id':333},cfg))
            self.assertFalse(admitted_message(base|{'message':[]},cfg));self.assertFalse(admitted_message(base|{'message':[{}]},cfg))
            for action in ('get_msg','get_group_msg_history','get_forward_msg'):
                self.assertFalse(allowed_action(dict(action=action,params=dict(group_id=111)),cfg))

    def test_connection_generation_changes_on_loss(self):
        with tempfile.TemporaryDirectory() as d:
            cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,Path(d)/'db')
            gate=OneBotGate(cfg,Path(d));gate.connected=True;gate.observe_online({'online':True});old=gate.connection_id
            gate.observe_online(None);self.assertNotEqual(old,gate.connection_id)
            value=json.loads((Path(d)/'state/gate-connection.json').read_text())
            self.assertIsNone(value['online']);self.assertIn('created',value);gate.store.close()

if __name__=='__main__':unittest.main()
