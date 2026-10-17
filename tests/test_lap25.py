import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest

from aiohttp import web,ClientSession

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from qqbot_gateway.contracts import normalize_request
from qqbot_gateway.errors import GatewayError,MESSAGES
from qqbot_gateway.group_protocol import group_plan,verify_metadata,SILENT
from qqbot_gateway.media_protocol import media_plan
from qqbot_gateway.model_gateway import application,ModelQueue
from qqbot_gateway.reply_plan import DEFAULTS,digest,ReplyPlan
from qqbot_gateway.task_store import TaskStore
from qqbot_gateway.token_budget import InputBudget,dialog_text
from qqbot_gateway.turn_budget import fit_snapshot,candidate_instruction


def snapshot(mention=True,count=8,size=200):
    return dict(must_reply=mention,target_seq=count if mention else None,web_anchor='old'*size,
        messages=[dict(seq=i,speaker='u1',name='synthetic',text=('old' if i==1 else 'x')*size,reply=None) for i in range(1,count+1)])


def payload(s,system='system'):
    body=json.dumps(s,ensure_ascii=False,separators=(',',':'))
    request=dict(version=1,kind='group_turn',trigger='mention' if s['must_reply'] else 'ambient',
        must_reply=s['must_reply'],epoch='e'*64,snapshot_digest=digest(body),request_key='a'*64)
    return dict(model='workbuddy-local',messages=[dict(role='system',content=system),dict(role='user',content=body)],qqbot_request=request)


def envelope(**changes):
    return dict(qqbot_group_reply=1,decision='speak',kind='chat',bubbles=['合成答复'],meme_id=None)|changes


class OutputRecoveryTests(unittest.TestCase):
    def test_whole_fence_optional_fields_and_string_bubbles(self):
        for mode in ('single','adaptive'):
            for obj in (envelope(),{k:v for k,v in envelope().items() if k!='meme_id'},
                        envelope(bubbles='合成答复',reason='inert'),dict(bubbles=['合成答复'])):
                for raw in (json.dumps(obj), '```json\n'+json.dumps(obj)+'\n```'):
                    decision,plan=media_plan(raw,DEFAULTS|{'delivery_mode':mode},'hi',None,[],group=True)
                    self.assertEqual(decision,'speak');self.assertEqual(plan.canonical_text,'合成答复')
                    self.assertEqual([p.type for p in plan.parts],['text'])

    def test_plain_text_only_mention_and_no_second_generation(self):
        for parse in (group_plan,lambda raw,cfg,q,must:media_plan(raw,cfg,q,None,[],group=True,must_reply=must)):
            self.assertEqual(parse('嗯？咋啦',DEFAULTS,'hi',True)[1].canonical_text,'嗯？咋啦')
            self.assertEqual(parse('嗯？咋啦',DEFAULTS,'hi',False),('error',None))
        self.assertEqual(media_plan('普通文字',DEFAULTS,'hi',None,[])[1].canonical_text,'普通文字')
        for raw in ('666','"嗯"'):
            self.assertEqual(group_plan(raw,DEFAULTS,'hi',True)[1].canonical_text,raw)

    def test_bad_image_and_silent_with_text_preserve_mention_text(self):
        for mid in (False,12,{},'file:///private','unknown'):
            _,plan=media_plan(json.dumps(envelope(meme_id=mid)),DEFAULTS,'hi',None,[],group=True)
            self.assertEqual(plan.canonical_text,'合成答复');self.assertEqual(len(plan.parts),1)
            _,plain=group_plan(json.dumps(envelope(meme_id=mid)),DEFAULTS,'hi',True)
            self.assertEqual(plain.canonical_text,'合成答复');self.assertEqual(len(plain.parts),1)
        self.assertEqual(group_plan(json.dumps(envelope(decision='silent')),DEFAULTS,'',True)[0],'speak')
        self.assertEqual(group_plan(json.dumps(envelope(decision='silent',bubbles=[])),DEFAULTS,'',False),('silent',None))

    def test_no_envelope_tool_or_broken_json_leaks(self):
        for raw in ('{"qqbot_group_reply":1', '{"bubbles":["x"],"bubbles":["y"]}',
                    json.dumps(envelope()|{'tool_calls':[]}),json.dumps(envelope(bubbles=['<tool_call>x</tool_call>'])),
                    json.dumps(envelope(bubbles=['&lt;tool_call&gt;x&lt;/tool_call&gt;'])),
                    '{"url":"file:///private"}',json.dumps(envelope(qqbot_group_reply=True)),
                    'QQBOT_INTERNAL_SILENT','```json\n{"broken"\n```'):
            decision,plan=media_plan(raw,DEFAULTS,'hi',None,[],group=True)
            self.assertEqual(decision,'error',raw);self.assertEqual(plan.fallback_reason,'media_protocol_error')
            self.assertNotIn('{',plan.canonical_text)
        self.assertEqual(group_plan(json.dumps({'bubbles':['text']}),DEFAULTS,'',False),('error',None))


class BudgetTests(unittest.TestCase):
    def test_final_system_and_empty_candidates_retrim_authenticated_snapshot(self):
        original=snapshot(size=300);data=payload(original,'framework-added-system '*20)
        req=dict(data['qqbot_request']);budget=InputBudget(limit=4000,overhead=200)
        system,prompt=normalize_request(data,budget=budget,group_suffix=candidate_instruction([]))
        body=json.loads(json.loads(prompt)[0]['content'])
        self.assertLess(len(body['messages']),len(original['messages']))
        self.assertEqual(body['messages'][-1],original['messages'][-1])
        self.assertIsNone(body['web_anchor']);self.assertEqual(data['qqbot_request'],req)
        budget.check(system+candidate_instruction([]),prompt)
        self.assertEqual(len(original['messages']),8)

    def test_protect_middle_target_and_newest_ambient(self):
        for mention in (True,False):
            s=snapshot(mention,size=100)
            if mention:s['target_seq']=3
            target=3 if mention else 8
            result=json.loads(fit_snapshot(s,'s',InputBudget(limit=650,overhead=100)))
            self.assertEqual([r['seq'] for r in result['messages']],[target])

    def test_target_alone_too_long_and_digest_tampering_rejected(self):
        data=payload(snapshot(count=1,size=1200))
        with self.assertRaises(GatewayError) as e:normalize_request(data,budget=InputBudget(limit=700))
        self.assertEqual(e.exception.code,'INPUT_TOO_LONG')
        data['qqbot_request']['snapshot_digest']='b'*64
        with self.assertRaises(GatewayError) as e:normalize_request(data,budget=InputBudget(limit=700))
        self.assertEqual(e.exception.code,'UNSUPPORTED_REQUEST')

    def test_native_envelope_budget_and_target_web_anchor(self):
        from qqbot_gateway.backends import OLLAMA_DEFAULTS
        s=snapshot(size=300);s['messages'][-1]['text']='https://example.com/current'
        s['web_anchor']=s['messages'][-1]['text']
        budget=InputBudget(limit=2000,overhead=100,native_profile=OLLAMA_DEFAULTS)
        system,prompt=normalize_request(payload(s),budget=budget,group_suffix=candidate_instruction([]))
        budget.check(system+candidate_instruction([]),prompt)
        result=json.loads(json.loads(prompt)[0]['content'])
        self.assertEqual(result['web_anchor'],s['web_anchor']);self.assertEqual(result['messages'][-1]['seq'],8)
        self.assertLess(len(result['messages']),8)


class LedgerTests(unittest.IsolatedAsyncioTestCase):
    async def test_partial_and_unknown_survive_reopen_without_group_lock(self):
        class Manager:
            def __getattr__(self,name):raise AssertionError('Personal history accessed')
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'tasks.sqlite';store=TaskStore(path)
            for key in ('partial','unknown'):
                store.accept(key,key);store.prepare_group_delivery(key,'group','e','r',ReplyPlan('chat',('a','b'),'a\nb'),'d',[1,2])
                store.begin_part(key,0)
                if key=='partial':store.part_result(key,0,'sent',1)
                store.finish_group(key)
            self.assertEqual(store.delivery('partial')['state'],'partial')
            self.assertEqual(store.delivery('unknown')['state'],'unknown')
            self.assertFalse(store.group_blocked('group'));store.close();store=TaskStore(path)
            await store.recover_deliveries(Manager());self.assertFalse(store.group_blocked('group'))
            self.assertFalse(store.accept('unknown','again'));self.assertFalse(store.begin_part('unknown',0))
            self.assertTrue(store.accept('new','new'));store.close()


class GatewayTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        class Runner:
            attempts=0;error=None
            async def run(self,system,prompt,trace):
                self.attempts+=1;self.system=system;self.prompt=prompt
                if self.error:raise GatewayError(self.error)
                return json.dumps(envelope())
        self.runner=Runner();self.queue=ModelQueue(self.runner)
        class Memes:
            cfg={'enabled':True}
            def candidates(self,q):return [{'id':'m_'+'a'*64,'name':'synthetic'*100}]
        self.budget=InputBudget(limit=3500,overhead=100)
        app=application(self.queue,'t'*40,budget=self.budget,memes=Memes())
        self.server=web.AppRunner(app);await self.server.setup();site=web.TCPSite(self.server,'127.0.0.1',0);await site.start()
        self.url='http://127.0.0.1:'+str(site._server.sockets[0].getsockname()[1])+'/v1/chat/completions'
        self.client=ClientSession();self.headers={'Authorization':'Bearer '+'t'*40}

    async def asyncTearDown(self):
        await self.client.close();await self.server.cleanup()

    async def post(self,data):
        async with self.client.post(self.url,json=data,headers=self.headers) as r:return r.status,await r.json()

    async def test_final_budget_crops_and_fits_candidates_single_generation(self):
        data=payload(snapshot(size=300),'framework-extra '*40)
        status,res=await self.post(data);self.assertEqual(status,200);self.assertEqual(self.runner.attempts,1)
        self.budget.check(self.runner.system,self.runner.prompt)
        rows=json.loads(json.loads(self.runner.prompt)[0]['content'])['messages']
        self.assertLess(len(rows),8);self.assertEqual(rows[-1]['seq'],8)
        plan=verify_metadata(res['qqbot_group_plan'],data['qqbot_request'],res['id'],res['choices'][0]['message']['content'],DEFAULTS)
        self.assertEqual(plan.canonical_text,'合成答复')

    async def test_business_error_preserved_and_ambient_silent_without_retry(self):
        for mention in (True,False):
            self.runner.error='RATE_LIMITED';data=payload(snapshot(mention,count=1,size=10))
            before=self.runner.attempts;status,res=await self.post(data)
            self.assertEqual(status,200);self.assertEqual(self.runner.attempts,before+1)
            self.assertEqual(res['qqbot_gateway_error'],'RATE_LIMITED')
            text=res['choices'][0]['message']['content'];self.assertEqual(text,MESSAGES['RATE_LIMITED'] if mention else SILENT)
            verify_metadata(res['qqbot_group_plan'],data['qqbot_request'],res['id'],text,DEFAULTS)

    async def test_impossible_input_reports_budget_not_metadata_error_zero_generation(self):
        data=payload(snapshot(count=1,size=1300));status,res=await self.post(data)
        self.assertEqual(status,200);self.assertEqual(res['qqbot_gateway_error'],'INPUT_TOO_LONG')
        self.assertEqual(self.runner.attempts,0)
        self.assertEqual(res['choices'][0]['message']['content'],MESSAGES['INPUT_TOO_LONG'])
        data['qqbot_request']['snapshot_digest']='c'*64
        status,res=await self.post(data);self.assertEqual(status,422)
        self.assertEqual(res['error']['code'],'UNSUPPORTED_REQUEST');self.assertEqual(self.runner.attempts,0)
