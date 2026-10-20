"""MEMB-01—04; synthetic identities, observations and transports only."""
import asyncio
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from qqbot_gateway.members import Members,DEFAULTS,validate_config,require_production,suspend_unverified,MemberClient
from qqbot_gateway.vision import member_source
from qqbot_gateway.turn_v2 import sha,plan,metadata,verify,validate_header,validate_source,fit
from qqbot_gateway.attention import canonical
from qqbot_gateway.reply_plan import DEFAULTS as OUTPUT,digest,trusted_plan,ReplyPlan
from qqbot_gateway.config import GateConfig
from qqbot_gateway.onebot_gate import OneBotGate,allowed_action

CFG=DEFAULTS|dict(enabled=True,mentions_enabled=True)


class Fixture:
    def __init__(self,count=3,age=0,observe=True):
        self.now=100.;self.count=count;self.age=age;self.calls=[];self.connection='c'*64;self.blocked={'999'}
        self.rows=[dict(group_id=111,user_id=uid,card=name,nickname=name) for uid,name in ((333,'自造甲'),(444,'自造乙'),(222,'自造bot'))]
        self.service=Members(CFG,lambda:self.now,(lambda data:dict(count=self.count,age=self.age,source='synthetic-observation')) if observe else None)
        self.active=True

    def allowed(self,identity):return self.active and identity[0]=='222' and identity[1]=='111' and identity[2] not in self.blocked|{'222'}

    async def rpc(self,action,params):
        self.calls.append((action,params))
        if action=='get_group_info':return dict(group_id=111,member_count=self.count,received_at=self.now,observed_at=self.now)
        return copy.deepcopy(self.rows)

    def request(self,text='请叫自造乙',sender=333,**event_fields):
        event=dict(self_id=222,group_id=111,user_id=sender,message_id=len(self.service.caps)+1,message=[dict(type='text',data=dict(text=text))])|event_fields
        cap=self.service.issue(event,self.connection)
        source=member_source(text,['鱼片'])
        header=dict(version=2,kind='group_turn',mode='free',request_key='a'*64,epoch='e'*64,config_version='b'*64,
            source_digest=sha(source),addressing='mention',must_reply=True,target_seq=1,resource_caps=[cap])
        body=dict(purpose='members.resolve',cap=cap,source=source,**{k:header[k] for k in ('request_key','target_seq','source_digest','epoch')})
        return source,header,body

    async def resolve(self,text='请叫自造乙',**kwargs):
        source,header,body=self.request(text,**kwargs)
        self.service.bind(body,self.connection,self.allowed)
        result=await self.service.resolve(body,self.connection,self.allowed,self.rpc)
        return source,header,body,result


def output(ref=None,index=0,bubbles=None,**extra):
    return canonical(dict(qqbot_turn_reply=2,decision='speak',kind='chat',bubbles=bubbles or ['一起聊吧'],meme_id=None,
        response_to_seq=1,mention=None if ref is None else dict(member_ref=ref,bubble_index=index),memory_proposals=[])|extra)


async def prepared(f):
    source,header,body,result=await f.resolve()
    effective=copy.deepcopy(source);effective['member_candidates']=result['candidates']
    ref=result['candidates'][-1]['member_ref']
    decision,reply,response=plan(output(ref),OUTPUT,'请叫自造乙',header,effective)
    meta=metadata(header,'r',decision,reply,effective,response,result['receipt'])
    return source,header,result,reply,meta


class MemberTests(unittest.IsolatedAsyncioTestCase):
    async def test_MEMB01_49_50_51_unknown_bool_zero_negative(self):
        for count in (49,50,51,None,True,0,-1,'3'):
            f=Fixture(count)
            if count==49:f.rows=[dict(group_id=111,user_id=1000+i,card='自造'+str(i),nickname='') for i in range(49)]
            _,_,_,result=await f.resolve()
            lists=sum(a=='get_group_member_list' for a,_ in f.calls)
            self.assertEqual(lists,1 if count==49 else 0)
            if count!=49:self.assertEqual(result,dict(candidates=[],receipt=None))

    async def test_MEMB01_received_at_and_cached_observed_field_do_not_prove_freshness(self):
        f=Fixture(observe=False)
        for _ in range(2):
            result=(await f.resolve())[-1];self.assertFalse(result['candidates'])
        self.assertTrue(all(a=='get_group_info' for a,_ in f.calls))

    async def test_MEMB02_age_reduces_ttl_and_count_expires_before_roster(self):
        f=Fixture(age=55);await f.resolve()
        self.assertEqual(f.service.counts['111']['expires'],105)
        self.assertEqual(f.service.rosters['111']['expires'],400)
        f.now=104;await f.resolve();self.assertEqual(len(f.calls),2)
        f.now=105;f.age=None;await f.resolve()
        self.assertEqual(sum(a=='get_group_member_list' for a,_ in f.calls),1)
        self.assertNotIn('111',f.service.rosters)

    async def test_MEMB02_count_refresh_can_reuse_unexpired_roster(self):
        f=Fixture();await f.resolve();f.now+=60;await f.resolve()
        self.assertEqual([a for a,_ in f.calls],['get_group_info','get_group_member_list','get_group_info'])
        f.now+=300;await f.resolve();self.assertEqual(sum(a=='get_group_member_list' for a,_ in f.calls),2)
        f=Fixture();await f.resolve();f.now+=60;f.count=4
        f.rows.append(dict(group_id=111,user_id=555,card='新夹具',nickname=''))
        await f.resolve();self.assertEqual(sum(a=='get_group_member_list' for a,_ in f.calls),2)

    async def test_MEMB02_stale_unknown_nan_and_infinite_age_zero_list(self):
        for age in (None,True,-1,60,100,float('inf'),float('nan')):
            f=Fixture(age=age);await f.resolve()
            self.assertEqual(len(f.calls),1)

    async def test_MEMB02_list_mismatch_duplicates_wrong_group_bad_ids_discard(self):
        for change in ('large','mismatch','duplicate','group','id','boolean','name'):
            f=Fixture()
            if change=='large':f.rows*=17
            elif change=='mismatch':f.rows.pop()
            elif change=='duplicate':f.rows[1]['user_id']=333
            elif change=='group':f.rows[1]['group_id']=555
            elif change=='id':f.rows[1]['user_id']='all'
            elif change=='boolean':f.rows[1]['user_id']=True
            else:f.rows[1]['card']=True
            result=(await f.resolve())[-1]
            self.assertEqual(result['candidates'],[]);self.assertNotIn('111',f.service.rosters)

    async def test_MEMB02_count_expires_during_list(self):
        f=Fixture();original=f.rpc
        async def rpc(action,params):
            data=await original(action,params)
            if action=='get_group_member_list':f.now+=61
            return data
        f.rpc=rpc;result=(await f.resolve())[-1]
        self.assertFalse(result['candidates'])
        f=Fixture();original=f.rpc
        async def changed(action,params):
            data=await original(action,params)
            if action=='get_group_member_list':f.service.invalidate('111')
            return data
        f.rpc=changed;self.assertFalse((await f.resolve())[-1]['candidates'])

    async def test_candidates_only_current_named_and_unique_no_raw_ids(self):
        f=Fixture();_,_,_,result=await f.resolve()
        self.assertEqual([c['name'] for c in result['candidates']],['自造甲','自造乙'])
        self.assertNotIn('444',canonical(result));self.assertNotIn('entries',canonical(result))
        f=Fixture();f.rows[1]['card']='自造甲'
        result=(await f.resolve())[-1];self.assertEqual(result['candidates'],[])

    async def test_candidate_ambiguity_including_blocked_and_bot(self):
        for uid in (999,222):
            f=Fixture();f.rows[1].update(user_id=uid,card='自造甲',nickname='自造甲')
            if uid==222:f.rows[-1]['user_id']=555
            self.assertFalse((await f.resolve())[-1]['candidates'])

    async def test_candidate_reference_and_eight_byte_limits(self):
        f=Fixture(12);f.rows=[dict(group_id=111,user_id=333+i,card='名字'+str(i),nickname='') for i in range(12)]
        first=dict(self_id=222,group_id=111,user_id=334,message_id='ref',message=[dict(type='text',data={'text':'前文'})])
        f.service.issue(first,f.connection)
        text=' '.join(r['card'] for r in f.rows)
        message=[dict(type='reply',data={'id':'ref'}),dict(type='text',data={'text':text})]
        result=(await f.resolve(text,message=message))[-1]
        self.assertEqual(len(result['candidates']),8);self.assertLessEqual(len(canonical(result['candidates']).encode()),768)
        self.assertEqual(result['candidates'][1]['name'],'名字1')

    async def test_cap_wrong_purpose_digest_target_connection_replay_and_no_rpc(self):
        for mutation in ({'purpose':'vision.resolve'},{'source_digest':'f'*64},{'target_seq':2},{'epoch':True}):
            f=Fixture();_,_,body=f.request();body.update(mutation)
            with self.assertRaises(ValueError):f.service.bind(body,f.connection,f.allowed)
            self.assertTrue(f.service.caps[body['cap']]['used']);self.assertEqual(f.calls,[])
        f=Fixture();_,_,body=f.request()
        with self.assertRaises(ValueError):f.service.bind(body,'other',f.allowed)
        f=Fixture();_,_,body,result=await f.resolve()
        with self.assertRaises(ValueError):await f.service.resolve(body,f.connection,f.allowed,f.rpc)
        self.assertEqual(len(f.calls),2)

    async def test_cap_single_use_after_rpc_failure_cancel_and_concurrent_busy(self):
        f=Fixture();_,_,body=f.request();f.service.bind(body,f.connection,f.allowed)
        async def bad(*args):raise ConnectionError()
        with self.assertRaises(ConnectionError):await f.service.resolve(body,f.connection,f.allowed,bad)
        with self.assertRaises(ValueError):await f.service.resolve(body,f.connection,f.allowed,f.rpc)
        self.assertFalse(f.service.busy)
        f=Fixture();_,_,body=f.request();f.service.bind(body,f.connection,f.allowed)
        async def cancel(*args):raise asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):await f.service.resolve(body,f.connection,f.allowed,cancel)
        self.assertFalse(f.service.busy);self.assertTrue(f.service.caps[body['cap']]['used'])

    async def test_generation_clear_and_membership_notice_invalidate(self):
        f=Fixture();_,_,_,reply,meta=await prepared(f)
        receipt=meta['member_receipt'];f.service.invalidate('111')
        permit=f.service.permit(dict(purpose='mention.send',receipt=receipt,metadata=meta,part_index=0),f.connection,f.allowed)
        _,applied=f.service.consume(permit,'111',[dict(type='text',data={'text':reply.canonical_text})],f.connection,f.allowed)
        self.assertFalse(applied)
        f.service.clear();self.assertFalse(f.service.receipts)

    async def test_MEMB03_v3_permission_consumption_exact_part_and_no_replay(self):
        f=Fixture();source,header,result,reply,meta=await prepared(f)
        self.assertEqual(meta['plan']['version'],3)
        self.assertEqual(verify(meta,header,'r',reply.canonical_text,OUTPUT,source),reply)
        request=dict(purpose='mention.send',receipt=result['receipt'],metadata=meta,part_index=0)
        permit=f.service.permit(request,f.connection,f.allowed)
        with self.assertRaises(ValueError):f.service.permit(request,f.connection,f.allowed)
        message=[dict(type='text',data={'text':reply.canonical_text})]
        segments,applied=f.service.consume(permit,'111',message,f.connection,f.allowed)
        self.assertTrue(applied);self.assertEqual(segments,[dict(type='at',data={'qq':'444'})]+message)
        with self.assertRaises(ValueError):f.service.consume(permit,'111',message,f.connection,f.allowed)

    async def test_MEMB03_generation_expiry_blocked_offline_connection_strips_same_attempt(self):
        for mutation in ('roster','version','block'):
            f=Fixture();_,_,result,reply,meta=await prepared(f)
            permit=f.service.permit(dict(purpose='mention.send',receipt=result['receipt'],metadata=meta,part_index=0),f.connection,f.allowed)
            if mutation=='roster':f.service.rosters.clear()
            elif mutation=='version':f.service.rosters['111']['version']='new-roster'
            elif mutation=='block':f.blocked.add('444')
            message=[dict(type='text',data={'text':reply.canonical_text})]
            segments,applied=f.service.consume(permit,'111',message,f.connection,f.allowed)
            self.assertFalse(applied);self.assertEqual(segments,message);self.assertEqual(len(f.calls),2)
        for mutation in ('offline','connection','sender_block','group'):
            f=Fixture();_,_,result,reply,meta=await prepared(f)
            permit=f.service.permit(dict(purpose='mention.send',receipt=result['receipt'],metadata=meta,part_index=0),f.connection,f.allowed)
            if mutation=='offline':f.active=False
            elif mutation=='connection':f.connection='d'*64
            elif mutation=='sender_block':f.blocked.add('333')
            with self.assertRaises(ValueError):
                f.service.consume(permit,'555' if mutation=='group' else '111',[dict(type='text',data={'text':reply.canonical_text})],f.connection,f.allowed)
            self.assertEqual(len(f.calls),2)
        f=Fixture();_,_,result,reply,meta=await prepared(f);f.now+=61
        permit=f.service.permit(dict(purpose='mention.send',receipt=result['receipt'],metadata=meta,part_index=0),f.connection,f.allowed)
        message=[dict(type='text',data={'text':reply.canonical_text})]
        self.assertEqual(f.service.consume(permit,'111',message,f.connection,f.allowed),(message,False))

    async def test_permission_tamper_wrong_group_part_hash_and_manifest(self):
        for mutation in ('plan_hash','candidate','group','text','part'):
            f=Fixture();_,_,result,reply,meta=await prepared(f)
            req=dict(purpose='mention.send',receipt=result['receipt'],metadata=meta,part_index=0)
            if mutation=='plan_hash':meta['plan_hash']='f'*64
            elif mutation=='candidate':meta['manifest']['member_candidates'][-1]['name']='伪造';meta['plan_hash']=sha({k:v for k,v in meta.items() if k!='plan_hash'})
            elif mutation=='part':req['part_index']=1
            if mutation in ('plan_hash','candidate','part'):
                with self.assertRaises(ValueError):f.service.permit(req,f.connection,f.allowed)
            else:
                permit=f.service.permit(req,f.connection,f.allowed)
                with self.assertRaises(ValueError):f.service.consume(permit,'555' if mutation=='group' else '111',[dict(type='text',data={'text':'改动' if mutation=='text' else reply.canonical_text})],f.connection,f.allowed)

    async def test_aux_bad_all_bot_raw_qq_cq_outside_manifest_leave_text(self):
        f=Fixture();source,header,_,result=await f.resolve();source['member_candidates']=result['candidates']
        for ref in ('all','bot','444','[CQ:at,qq=444]','p_'+'f'*16):
            _,reply,_=plan(output(ref),OUTPUT,'',header,source)
            self.assertFalse(any(p.mention_ref for p in reply.parts));self.assertEqual(reply.canonical_text,'一起聊吧')
        for index in (True,-1,1,'0'):
            _,reply,_=plan(output(result['candidates'][0]['member_ref'],index),OUTPUT,'',header,source)
            self.assertFalse(any(p.mention_ref for p in reply.parts))

    async def test_single_merge_adaptive_mapping_and_truncated_dependency(self):
        f=Fixture();source,header,_,result=await f.resolve();source['member_candidates']=result['candidates'];ref=result['candidates'][0]['member_ref']
        for mode,count in (('single',1),('adaptive',2)):
            _,reply,_=plan(output(ref,1,['第一句','第二句']),OUTPUT|dict(delivery_mode=mode),'',header,source)
            self.assertEqual(len(reply.parts),count);self.assertEqual(reply.parts[-1].mention_ref,ref)
        _,reply,_=plan(output(ref,0,['字'*1300]),OUTPUT,'',header,source)
        self.assertFalse(any(p.mention_ref for p in reply.parts))

    async def test_final_budget_trims_candidates_and_invalidates_ref(self):
        from qqbot_gateway.token_budget import InputBudget,dialog_text
        f=Fixture();source,header,_,result=await f.resolve();effective=copy.deepcopy(source);effective['member_candidates']=result['candidates']
        budget=InputBudget();base=budget.usage('政策',dialog_text([dict(role='user',content=canonical(source))]))
        from dataclasses import replace
        trimmed=json.loads(fit(effective,header,'政策',replace(budget,limit=base+1)))
        self.assertFalse(trimmed['member_candidates'])
        _,reply,_=plan(output(result['candidates'][0]['member_ref']),OUTPUT,'',header,trimmed)
        self.assertFalse(any(p.mention_ref for p in reply.parts))


class ConfigAndRPCTests(unittest.TestCase):
    def test_MEMB04_rpc_scope_always_blocks_list_peer_and_stranger(self):
        with tempfile.TemporaryDirectory() as directory:
            cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,Path(directory)/'db',silence_enabled=False)
            for action,params in [('get_group_member_list',{'group_id':111}),('get_group_member_info',{'group_id':111,'user_id':333}),('get_stranger_info',{'user_id':333})]:
                self.assertFalse(allowed_action(dict(action=action,params=params),cfg))
            self.assertTrue(allowed_action(dict(action='get_group_member_info',params={'group_id':111,'user_id':222}),cfg))
            for segments in ([dict(type='at',data={'qq':'444'})],[dict(type='text',data={'text':'[CQ:at,qq=444]'})]):
                self.assertFalse(allowed_action(dict(action='send_group_msg',params=dict(group_id=111,message=segments)),cfg))

    def test_configuration_proof_refuses_activation_and_suspends_only_members(self):
        self.assertEqual(validate_config({}),DEFAULTS)
        for raw in ({'enabled':1},{'mentions_enabled':True},{'max_prompt_entries':9},{'roster_member_count_lt':51},{'count_ttl_seconds':61},{'status':'production_eligible'}):
            with self.assertRaises(ValueError):validate_config(raw)
        settings=dict(members=CFG,vision={'enabled':False},llm={'backend':'codebuddy_cli'})
        with self.assertRaisesRegex(ValueError,'capability_unverified'):require_production(settings)
        self.assertFalse(suspend_unverified(settings)['enabled']);self.assertTrue(settings['members']['enabled'])

    def test_fixed_client_rejects_arbitrary_url_and_missing_token(self):
        for url in ('https://127.0.0.1:12/context/members','http://localhost:12/context/members','http://127.0.0.1:12/proxy','http://user@127.0.0.1:12/context/members'):
            with self.assertRaises(ValueError):MemberClient(url,'c'*64)

    def test_web_sources_preserve_mention_only_when_text_dependency_survives(self):
        from qqbot_gateway.reply_plan import PreparedPart
        from qqbot_gateway.web_retrieval import source_plan
        ref='p_'+'a'*16;text='合成正文'
        reply=ReplyPlan('answer',(text,),text,prepared_parts=(PreparedPart('text',digest(text),text,text,ref),))
        sources=[dict(url='https://example.com/',title='自造页',status='body')]
        kept=source_plan(reply,sources,OUTPUT,'')
        self.assertEqual(kept.parts[0].mention_ref,ref)
        self.assertEqual(kept.parts[0].digest,digest(kept.canonical_text))
        long='字'*1300
        reply=ReplyPlan('answer',(long,),long,prepared_parts=(PreparedPart('text',digest(long),long,long,ref),))
        self.assertFalse(any(p.mention_ref for p in source_plan(reply,sources,OUTPUT,'').parts))


class BoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_name_substrings_are_not_guessed_as_another_member(self):
        for short,long,text in (('Ann','Anna','xxAnnxx Anna'),('小明','小明同学','请小明同学聊聊')):
            f=Fixture(4)
            f.rows[1].update(card=short,nickname=short)
            f.rows.append(dict(group_id=111,user_id=555,card=long,nickname=long))
            result=(await f.resolve(text))[-1]
            self.assertEqual([c['name'] for c in result['candidates']],['自造甲',long])

    async def test_optional_window_trim_precedes_member_candidate_trim(self):
        from qqbot_gateway.token_budget import InputBudget,dialog_text
        from dataclasses import replace
        f=Fixture();source,header,_,result=await f.resolve()
        source['member_candidates']=result['candidates']
        budget=InputBudget();usage=budget.usage('政策',dialog_text([dict(role='user',content=canonical(source))]))
        source['messages'].append(source['messages'][0]|dict(seq=2,member_ref='p_'+'f'*16,text='可裁旧行'*300))
        source['eligible_seq'].append(2)
        fitted=json.loads(fit(source,header,'政策',replace(budget,limit=usage+1)))
        self.assertEqual([r['seq'] for r in fitted['messages']],[1])
        self.assertEqual(fitted['member_candidates'],result['candidates'])

    async def test_gateway_mentions_switch_and_two_purpose_cap_schema(self):
        from aiohttp.test_utils import TestServer,TestClient
        from qqbot_gateway.model_gateway import application,ModelQueue
        from qqbot_gateway.errors import GatewayError
        f=Fixture();source,header,_=f.request()
        for caps in ([{}],['a'*64,'a'*64],['a'*64,'b'*64,'c'*64]):
            with self.assertRaises(GatewayError):validate_header(header|dict(resource_caps=caps))
        image_source=copy.deepcopy(source)
        from qqbot_gateway.vision import attach_image
        attach_image(image_source,dict(image_ref='i_'+'f'*32,cap='d'*64))
        both=header|dict(resource_caps=['d'*64,header['resource_caps'][0]],source_digest=sha(image_source))
        validate_header(both);validate_source(canonical(image_source),both)
        for enabled in (False,True):
            class Runner:
                calls=0
                async def run(self,system,prompt,request_id):
                    self.calls+=1
                    effective=json.loads(json.loads(prompt)[-1]['content'])
                    return output(effective['member_candidates'][0]['member_ref'])
            class Client:
                async def resolve(self,request,source,deadline):
                    return dict(candidates=[dict(member_ref=source['messages'][0]['member_ref'],name='自造甲')],receipt='f'*64)
            runner=Runner();queue=ModelQueue(runner)
            client=TestClient(TestServer(application(queue,'t'*64,v2=dict(mode='free',config_version='b'*64,aliases=['鱼片'],mentions_enabled=enabled),members=Client())))
            await client.start_server()
            try:
                response=await client.post('/v1/chat/completions',json=dict(model='workbuddy-local',stream=False,
                    messages=[dict(role='user',content=canonical(source))],qqbot_request=header),headers={'Authorization':'Bearer '+'t'*64,'X-QQBot-Trace':'c'*32})
                self.assertEqual(response.status,200)
                body=await response.json();meta=body['qqbot_group_plan']
                reply=verify(meta,header,body['id'],body['choices'][0]['message']['content'],OUTPUT,source)
                self.assertEqual(any(p.mention_ref for p in reply.parts),enabled);self.assertEqual(runner.calls,1)
            finally:await client.close()

    async def test_bad_aux_container_preserves_valid_core_text(self):
        f=Fixture();source,header,_,result=await f.resolve();source['member_candidates']=result['candidates']
        for ref in ([],{},True,1):
            _,reply,_=plan(output(ref),OUTPUT,'',header,source)
            self.assertEqual(reply.canonical_text,'一起聊吧');self.assertFalse(any(p.mention_ref for p in reply.parts))

    async def test_expired_cap_wrong_schema_foreign_source_and_unbound_zero_rpc(self):
        for mutation in ('expires','schema','source','unbound'):
            f=Fixture();source,header,body=f.request()
            if mutation=='expires':f.now+=60
            elif mutation=='schema':body['action']='get_group_member_list'
            elif mutation=='source':
                source['messages'][0]['text']='冒充新消息';body['source_digest']=sha(source)
            with self.assertRaises(ValueError):
                if mutation!='unbound':f.service.bind(body,f.connection,f.allowed)
                else:await f.service.resolve(body,f.connection,f.allowed,f.rpc)
            self.assertEqual(f.calls,[])

    async def test_bound_cap_concurrent_resolve_exactly_once(self):
        f=Fixture();_,_,body=f.request();f.service.bind(body,f.connection,f.allowed)
        entered=asyncio.Event();release=asyncio.Event();original=f.rpc
        async def rpc(action,params):entered.set();await release.wait();return await original(action,params)
        running=asyncio.create_task(f.service.resolve(body,f.connection,f.allowed,rpc));await entered.wait()
        with self.assertRaises(ValueError):await f.service.resolve(body,f.connection,f.allowed,f.rpc)
        release.set();await running;self.assertEqual(len(f.calls),2)

    async def test_HTTP_independent_auth_unknown_actions_and_production_paused(self):
        import aiohttp
        from aiohttp.test_utils import TestServer,TestClient
        with tempfile.TemporaryDirectory() as directory:
            cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,Path(directory)/'db',members_enabled=True,members_config=CFG,silence_enabled=False)
            gate=OneBotGate(cfg);gate.context_token='c'*64;gate.connected=True;gate.online=True
            client=TestClient(TestServer(gate.application()));await client.start_server()
            try:
                for token,status in (('a'*40,401),('b'*40,401),('bad',401),('c'*64,400)):
                    response=await client.post('/context/members/resolve',json={'action':'get_group_member_list','group_id':111},headers={'Authorization':'Bearer '+token})
                    self.assertEqual(response.status,status);await response.read()
                gate.config=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,Path(directory)/'db2',silence_enabled=False)
                response=await client.post('/context/members/resolve',json={},headers={'Authorization':'Bearer '+'c'*64})
                self.assertEqual(response.status,503);await response.read()
                self.assertEqual(gate.members.rosters,{})
            finally:await client.close()

    async def test_gate_only_admitted_events_get_caps_and_notice_invalidates(self):
        from aiohttp import WSMsgType
        with tempfile.TemporaryDirectory() as directory:
            gate=OneBotGate(GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,Path(directory)/'db',participation_mode='free',blocked_users=frozenset({'999'}),members_enabled=True,members_config=CFG,silence_enabled=False))
            rows=[]
            class Up:
                async def send_json(self,value):rows.append(value)
            async def frames(events):
                for e in events:yield SimpleNamespace(type=WSMsgType.TEXT,data=json.dumps(e))
            event=dict(post_type='message',message_type='group',self_id=222,group_id=111,user_id=999,message_id=1,message=[dict(type='text',data={'text':'夹具'})],qqbot_member_cap='forged')
            try:
                await gate._incoming(frames([event,event|dict(user_id=333,group_id=555),event|dict(user_id=333,post_type='request')]),Up(),set())
                self.assertFalse(rows);self.assertFalse(gate.members.caps)
                await gate._incoming(frames([event|dict(user_id=333)]),Up(),set())
                self.assertEqual(len(rows),1);self.assertNotEqual(rows[0]['qqbot_member_cap'],'forged')
                gate.members.counts['111']={};gate.members.rosters['111']={}
                await gate._incoming(frames([dict(post_type='notice',notice_type='group_decrease',self_id=222,group_id=111)]),Up(),set())
                self.assertFalse(gate.members.counts);self.assertFalse(gate.members.rosters)
            finally:gate.store.close()

    async def test_legacy_export_removes_members_and_save_rejects_true(self):
        import yaml
        from qqbot_gateway.config import export_legacy_config,read_settings,save_settings,load_gate_config
        root=Path(__file__).resolve().parents[1]
        settings=yaml.safe_load((root/'config/settings.example.yaml').read_text(encoding='utf-8'))
        settings['bot']['qq']='222';settings['access'].update(allowed_groups=['111'],admin_users=['333'],blocked_users=['999'])
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);(base/'config').mkdir();path=base/'config/settings.local.yaml'
            path.write_text(yaml.safe_dump(settings),encoding='utf-8');settings,d=read_settings(path)
            settings['members']=CFG
            with self.assertRaisesRegex(ValueError,'capability_unverified'):save_settings(path,settings,d)
            exported=export_legacy_config(path)
            self.assertNotIn('members',yaml.safe_load(Path(exported['review']).read_text(encoding='utf-8')))
            # Exercise the actual menu, without a live process or any credentials.
            from scripts.configure_bot import ConfigMenu
            original=path.read_bytes();shown=[]
            ui=SimpleNamespace(page=lambda text:shown.append(text),write=lambda text:shown.append(text),
                choose=lambda choices:'1',read=lambda prompt:'true',pause=lambda:None)
            ConfigMenu(path,ui).members_group()
            self.assertEqual(path.read_bytes(),original);self.assertIn('capability_unverified',' '.join(shown))
            # A valid hand edit keeps normal gate startup available but never
            # activates the member service. Only synthetic transport tokens exist.
            path.write_text(yaml.safe_dump(settings),encoding='utf-8')
            token_path=base/settings['secrets_file'];token_path.parent.mkdir(parents=True,exist_ok=True)
            token_path.write_text(json.dumps(dict(onebot_inbound='a'*40,onebot_upstream='b'*40)),encoding='utf-8')
            cfg=load_gate_config(path)
            self.assertFalse(cfg.members_enabled);self.assertFalse(cfg.members_config['enabled'])


if __name__=='__main__':unittest.main()
