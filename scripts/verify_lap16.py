"""Synthetic actual-SDK/runner/history/decorate/event-send checks. No real QQ or LLM."""
import asyncio
import copy
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]


async def verify(synthetic=None, backend='codebuddy_cli', report_path=None):
    os.environ['ASTRBOT_DISABLE_METRICS']='1'
    import yaml
    from aiohttp import web
    from astrbot.core.agent.message import Message
    from astrbot.core.agent.runners.base import AgentState
    from astrbot.core.agent.runners.tool_loop_agent_runner import ToolLoopAgentRunner
    from astrbot.core.config.default import DEFAULT_CONFIG
    from astrbot.core.db.po import Conversation
    from astrbot.core.pipeline.process_stage.method.agent_sub_stages.internal import InternalAgentSubStage
    from astrbot.core.pipeline.result_decorate.stage import ResultDecorateStage
    from astrbot.core.pipeline.respond.stage import RespondStage
    import astrbot.core.pipeline.result_decorate.stage as decorate_module
    from astrbot.core.provider.sources.openai_source import ProviderOpenAIOfficial
    from astrbot.api.platform import AstrBotMessage,MessageMember,MessageType,PlatformMetadata
    from astrbot.api.message_components import At,Plain
    from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
    from astrbot.core.pipeline.waking_check.stage import build_unique_session_id
    from qqbot_gateway.model_gateway import application,ModelQueue
    from qqbot_gateway.reply_plan import DEFAULTS
    from plugins.qq_router.main import QQRouter

    class Synthetic:
        attempts=0
        text=''
        async def run(self,*args):self.attempts+=1;return self.text

    class Conversations:
        def __init__(self):self.current={};self.items={}
        async def get_curr_conversation_id(self,umo):return self.current.get(umo)
        async def get_conversation(self,umo,cid):return self.items.get((umo,cid))
        async def new_conversation(self,umo,persona_id):
            cid=str(len(self.items)+1);self.current[umo]=cid
            self.items[(umo,cid)]=Conversation('qqbot',umo,cid,history='[]',persona_id=persona_id)
            return cid
        async def update_conversation(self,umo,cid,history,**kwargs):
            self.items[(umo,cid)].history=json.dumps(history,ensure_ascii=False)

    class Bot:
        def __init__(self,fail_at=None,mode=None):self.sent=[];self.fail_at=fail_at;self.mode=mode
        async def send_group_msg(self,**kwargs):
            self.sent.append(kwargs);n=len(self.sent)
            if n==self.fail_at:
                if self.mode=='missing':return {}
                if self.mode=='duplicate':return {'message_id':1}
                if self.mode=='timeout':await asyncio.sleep(1)
                raise ConnectionError('synthetic transport failure')
            return {'message_id':n}

    cfg=DEFAULTS | dict(delivery_mode='adaptive',bubble_delay_min_ms=0,bubble_delay_max_ms=0)
    synthetic=synthetic or Synthetic();queue=ModelQueue(synthetic);token=secrets.token_urlsafe(32)
    server=web.AppRunner(application(queue,token,output=cfg),access_log=None)
    await server.setup();site=web.TCPSite(server,'127.0.0.1',0);await site.start()
    port=site._server.sockets[0].getsockname()[1]
    provider=ProviderOpenAIOfficial({'id':'lap16-offline','type':'openai_chat_completion',
        'api_base':f'http://127.0.0.1:{port}/v1','key':[token],'model':'workbuddy-local',
        'modalities':['text'],'custom_extra_body':{},'timeout':10},{})
    report={'real_model_requests':0,'real_qq_messages':0,'cases':[]}
    try:
        with tempfile.TemporaryDirectory(prefix='qqbot-lap16-router-',ignore_cleanup_errors=True) as directory:
            root=Path(directory);(root/'config').mkdir()
            settings=yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
            settings['llm']['backend']=backend
            if backend=='ollama_ssh':settings['llm']['profiles']['ollama_ssh']['expected_digest']='a'*64
            settings['bot']['qq']='222';settings['access'].update(allowed_groups=['111'],admin_users=['333'])
            settings['chat']['user_cooldown_seconds']=0;settings['output']=cfg | {'mode':'plain_chat'}
            (root/'config/settings.local.yaml').write_text(yaml.safe_dump(settings),encoding='utf-8')
            (root/'config/persona.md').write_text((ROOT/'config/persona.md').read_text(encoding='utf-8'),encoding='utf-8')
            manager=Conversations()
            with patch.dict(os.environ,{'QQBOT_ROOT':directory}):
                router=QQRouter(SimpleNamespace(conversation_manager=manager))
            try:
                router.delivery.timeout=.03
                from astrbot.api.message_components import Reply
                report['adaptive_admission']=[]
                for variant in ('no_at','name','quoted_at','self','blocked','unauthorized','private'):
                    msg=AstrBotMessage();msg.self_id='222';msg.type=MessageType.GROUP_MESSAGE
                    msg.group_id='111';msg.sender=MessageMember('333','synthetic admission')
                    msg.message_id='admission-'+variant;msg.message=[At(qq='222'),Plain(text='test')]
                    msg.message_str='test';msg.session_id='111'
                    if variant in ('no_at','name'):msg.message=[Plain(text='鱼鱼')]
                    if variant=='quoted_at':msg.message=[Reply(id='1',chain=[At(qq='222')]),Plain(text='test')]
                    if variant=='self':msg.sender=MessageMember('222','synthetic self')
                    if variant=='blocked':router.blocked.add('333')
                    if variant=='unauthorized':msg.group_id='999'
                    if variant=='private':msg.type=MessageType.FRIEND_MESSAGE;msg.group_id=''
                    event=AiocqhttpMessageEvent('test',msg,PlatformMetadata(name='aiocqhttp',description='offline',id='qqbot'),'111',Bot())
                    event.session_id=build_unique_session_id(event)
                    before=router.tasks.db.execute('SELECT count(*) FROM tasks').fetchone()[0]
                    assert not [item async for item in router.on_group(event)]
                    assert not event.get_extra('qq_router_trace') and not event.bot.sent
                    assert router.tasks.db.execute('SELECT count(*) FROM tasks').fetchone()[0]==before
                    assert not manager.items and not router.coordinator.states and synthetic.attempts==0
                    router.blocked.discard('333')
                    report['adaptive_admission'].append(dict(variant=variant,tasks=0,history=0,model=0,sends=0))
                config=copy.deepcopy(DEFAULT_CONFIG)
                config['t2i']=False;config['content_safety']['also_use_in_response']=False
                config['provider_tts_settings']['enable']=False
                config['provider_settings']['display_reasoning_text']=False
                config['platform_settings'].update(reply_prefix='',reply_with_mention=False,reply_with_quote=True,forward_threshold=100000)
                config['platform_settings']['segmented_reply']['enable']=False
                async def no_tts(*args):return None
                ctx=SimpleNamespace(astrbot_config=config,plugin_manager=SimpleNamespace(context=SimpleNamespace(get_using_tts_provider_async=no_tts)))
                decorate=ResultDecorateStage();respond=RespondStage()
                await decorate.initialize(ctx);await respond.initialize(ctx)
                stage=InternalAgentSubStage();stage.conv_manager=manager
                samples=[('chat1',['a']),('chat2',['a','b']),('chat3',['a','b','c']),
                         ('answer',['first','second']),('overflow',['a','b','c','tail']),
                         ('literal',['```\n**literal**\n    a && b || c\n```']),
                         ('metadata_missing',['a','b']),('metadata_mismatch',['a','b'])]
                for index in (1,2,3):
                    for mode in ('error','missing','timeout'):
                        samples.append((f'{mode}{index}',['a','b','c']))
                samples += [('duplicate2',['a','b','c']),('before_send',['a','b','c']),('stop_delay',['a','b','c'])]
                for order in ('save_first','send_first'):
                    for case,parts in samples:
                        kind='answer' if case in ('answer','literal') else 'chat'
                        synthetic.text=json.dumps(dict(qqbot_reply=1,kind=kind,bubbles=parts),ensure_ascii=False)
                        mode=next((m for m in ('error','missing','timeout','duplicate') if case.startswith(m)),None)
                        fail_at=int(case[-1]) if mode else None
                        bot=Bot(fail_at,mode)
                        msg=AstrBotMessage();msg.self_id='222';msg.type=MessageType.GROUP_MESSAGE
                        msg.group_id='111';msg.sender=MessageMember(str(1000+len(report['cases'])),'synthetic')
                        msg.message_id=str(1000+len(report['cases']));msg.message=[At(qq='222'),Plain(text='test')]
                        msg.message_str='test';msg.session_id='111'
                        event=AiocqhttpMessageEvent('test',msg,PlatformMetadata(name='aiocqhttp',description='offline',id='qqbot'),'111',bot)
                        event.session_id=build_unique_session_id(event)
                        gen=router.on_group(event);req=await anext(gen)
                        before_attempts=synthetic.attempts
                        response=await provider.text_chat(prompt=req.prompt,system_prompt=router.persona,func_tool=None,request_max_retries=1)
                        assert synthetic.attempts==before_attempts+1
                        raw=response.raw_completion
                        assert isinstance(raw.qqbot_reply_plan,dict),'SDK discarded metadata'
                        if case=='metadata_missing':raw.qqbot_reply_plan=None
                        if case=='metadata_mismatch':raw.qqbot_reply_plan['content_sha256']='bad'
                        run_context=SimpleNamespace(messages=[Message(role='system',content=router.persona),Message(role='user',content=req.prompt)])
                        class Hooks:
                            async def on_agent_done(self,context,result):
                                await router.model_response(event,result)
                                await router.preserve_gateway_text(event,context,result)
                        runner=ToolLoopAgentRunner.__new__(ToolLoopAgentRunner)
                        runner._state=AgentState.RUNNING;runner.stats=SimpleNamespace(end_time=None)
                        runner.run_context=run_context;runner.agent_hooks=Hooks();runner._pending_follow_ups=[]
                        await runner._complete_with_assistant_response(response)
                        key=event.get_extra('qq_delivery_key')
                        assert router.tasks.delivery(key)['state']=='prepared'
                        async def save():await stage._save_to_history(event,req,response,run_context.messages,None)
                        if order=='save_first':await save()
                        event.set_result(event.plain_result(response.completion_text))
                        handler=SimpleNamespace(handler_module_path='lap16',handler_name='deliver_reply',handler=router.deliver_reply)
                        flag={'allowed':True}
                        original_allowed=router.delivery.allowed
                        router.delivery.allowed=lambda e:flag['allowed'] and original_allowed(e)
                        stopper=None
                        if case=='stop_delay':
                            router.delivery.output=cfg | dict(bubble_delay_min_ms=200,bubble_delay_max_ms=200)
                            async def stop():
                                while router.tasks.parts(key)[0][1]!='sent':await asyncio.sleep(.001)
                                await asyncio.sleep(.005);flag['allowed']=False
                            stopper=asyncio.create_task(stop())
                        original_send=event.send
                        async def no_send(chain):raise RuntimeError('synthetic before send')
                        if case=='before_send':event.send=no_send
                        with patch.object(decorate_module.star_handlers_registry,'get_handlers_by_event_type',return_value=[handler]),patch.dict(decorate_module.star_map,{'lap16':SimpleNamespace(name='lap16')}):
                            async for _ in decorate.process(event):pass
                        await respond.process(event) # Cleared result must suppress default resend.
                        count=len(bot.sent)
                        await router.deliver_reply(event) # Reentrant hook must not resend.
                        assert len(bot.sent)==count
                        if stopper:await stopper
                        event.send=original_send;router.delivery.allowed=original_allowed;router.delivery.output=cfg
                        if order=='send_first':await save()
                        next_msg=copy.deepcopy(msg);next_msg.message_id=str(int(msg.message_id)+10000)
                        follow=AiocqhttpMessageEvent('test',next_msg,PlatformMetadata(name='aiocqhttp',description='offline',id='qqbot'),'111',Bot())
                        follow.session_id=build_unique_session_id(follow)
                        follow_gen=router.on_group(follow)
                        follow_task=asyncio.create_task(anext(follow_gen))
                        await asyncio.sleep(.001)
                        assert not follow_task.done(),'Session lease released before history repair'
                        try:await anext(gen)
                        except StopAsyncIteration:pass
                        row=router.tasks.delivery(key)
                        assert row['repair']=='repaired',row
                        plan=event.get_extra('qq_delivery_plan')
                        ack_count=fail_at-1 if mode else (0 if case=='before_send' else 1 if case=='stop_delay' else len(plan.bubbles))
                        expect_calls=fail_at if mode else (0 if case=='before_send' else 1 if case=='stop_delay' else len(plan.bubbles))
                        assert count==expect_calls,(case,count,expect_calls)
                        conv=await manager.get_conversation(event.unified_msg_origin,req.conversation.cid)
                        history=json.loads(conv.history)
                        confirmed='\n'.join(plan.bubbles[:ack_count])
                        assert len(history)==(2 if confirmed else 1),(case,history)
                        if confirmed:
                            assert history[-1]['content']==confirmed,(case,history,confirmed)
                        assert row['state']==('sent' if ack_count==len(plan.bubbles) else 'unknown'),(case,row)
                        for i,sent in enumerate(bot.sent):
                            assert not any(p['type']=='at' for p in sent['message'])
                            assert sum(p['type']=='reply' for p in sent['message'])==(1 if i==0 else 0)
                        assert event.bot is bot
                        next_req=await asyncio.wait_for(follow_task,1)
                        next_history=json.loads(next_req.conversation.history)
                        assert len(next_history)==(2 if confirmed else 0)
                        if confirmed:assert next_history[-1]['content']==confirmed
                        await follow_gen.aclose()
                        assert not [item async for item in router.on_group(event)],'Inbound duplicate was accepted'
                        report['cases'].append(dict(case=case,order=order,send_calls=count,confirmed_parts=ack_count,
                            history_equals_confirmed=True,next_request_only_confirmed=True,lease_until_repair=True,default_resend=False,ack='simulated',runner_attempts=1))
                # Exercise the installed aiocqhttp echo/result store too, not only a Bot double.
                from aiocqhttp import CQHttp
                from aiocqhttp.api_impl import WebSocketReverseApi, ResultStore
                from aiohttp import WSMsgType
                from qqbot_gateway.onebot_gate import OneBotGate
                from qqbot_gateway.config import GateConfig
                gate=OneBotGate(GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,root/'state/sdk-gate.sqlite'))
                class Frames:
                    def __init__(self,raw):self.raw=raw
                    def __aiter__(self):return self.iterate()
                    async def iterate(self):yield SimpleNamespace(type=WSMsgType.TEXT,data=self.raw)
                class Receiver:
                    async def send_str(self,raw):
                        ResultStore.add(json.loads(raw))
                from qqbot_gateway.reply_plan import ReplyPlan
                report['ack_sdk_cases']=[]
                for mode in ('ok','fail2','timeout1','unknown_echo1','duplicate1'):
                    callbacks=[];pending=set()
                    class Socket:
                        def __init__(self):self.sent=[]
                        async def send(self,raw):
                            await gate._outgoing(Frames(raw),SimpleNamespace(send_str=self.emit),pending)
                        async def emit(self,raw):
                            payload=json.loads(raw);self.sent.append(payload);n=len(self.sent)
                            assert payload['action']=='send_group_msg'
                            delay=.4 if mode=='timeout1' and n==1 else .001
                            ack={'status':'failed' if mode=='fail2' and n==2 else 'ok',
                                 'retcode':1 if mode=='fail2' and n==2 else 0,
                                 'data':{'message_id':n},'echo':payload['echo']}
                            if mode=='unknown_echo1' and n==1:ack['echo']={'seq':-100}
                            async def reply():
                                await asyncio.sleep(delay);await gate._incoming(Frames(json.dumps(ack)),Receiver(),pending)
                                if mode=='duplicate1' and n==1:
                                    await asyncio.sleep(.01);await gate._incoming(Frames(json.dumps(ack)),Receiver(),pending)
                            callbacks.append(asyncio.create_task(reply()))
                    socket=Socket();bot=CQHttp();bot._api=WebSocketReverseApi({'222':socket},set(),.2)
                    router.delivery.timeout=.25
                    message=copy.deepcopy(msg);message.message_id='sdk-'+mode
                    message.sender=MessageMember('333','synthetic SDK')
                    event=AiocqhttpMessageEvent('test',message,PlatformMetadata(name='aiocqhttp',description='offline',id='qqbot'),'111',bot)
                    event.session_id=build_unique_session_id(event)
                    event.set_extra('qq_delivery_version',router.persona_id)
                    event.set_extra('qq_delivery_identity',('222','111','333'))
                    plan=ReplyPlan('chat',('a','b','c'),'a\nb\nc')
                    cid=await manager.new_conversation(event.unified_msg_origin,router.persona_id)
                    history=[{'role':'user','content':'synthetic'},{'role':'assistant','content':plan.canonical_text}]
                    await manager.update_conversation(event.unified_msg_origin,cid,history)
                    key='sdk-'+mode;router.tasks.accept(key,key)
                    router.tasks.prepare_delivery(key,event.unified_msg_origin,cid,key,plan,[],history)
                    await router.delivery.send(event,key,plan)
                    await asyncio.gather(*callbacks)
                    await router.tasks.repair_delivery(key,manager)
                    expected=3 if mode in ('ok','duplicate1') else 2 if mode=='fail2' else 1
                    confirmed=3 if mode in ('ok','duplicate1') else 1 if mode=='fail2' else 0
                    assert len(socket.sent)==expected,(mode,len(socket.sent))
                    assert sum(state=='sent' for _,state,_ in router.tasks.parts(key))==confirmed
                    assert not ResultStore._futures
                    report['ack_sdk_cases'].append(dict(mode=mode,send_calls=len(socket.sent),confirmed_parts=confirmed,
                                                       late_or_unmatched_ack_ignored=True,original_sdk_connection=True,original_gate=True))
                gate.store.close()
                shared=Bot();turns=[]
                for user,label in [('333','A'),('334','B')]:
                    message=copy.deepcopy(msg);message.message_id='concurrent-'+label
                    message.sender=MessageMember(user,'synthetic concurrency')
                    event=AiocqhttpMessageEvent('test',message,PlatformMetadata(name='aiocqhttp',description='offline',id='qqbot'),'111',shared)
                    event.session_id=build_unique_session_id(event)
                    event.set_extra('qq_delivery_version',router.persona_id)
                    event.set_extra('qq_delivery_identity',('222','111',user))
                    plan=ReplyPlan('chat',(label+'1',label+'2'),label+'1\n'+label+'2')
                    cid=await manager.new_conversation(event.unified_msg_origin,router.persona_id)
                    history=[{'role':'user','content':'synthetic'},{'role':'assistant','content':plan.canonical_text}]
                    await manager.update_conversation(event.unified_msg_origin,cid,history)
                    key='concurrent-'+label;router.tasks.accept(key,key)
                    router.tasks.prepare_delivery(key,event.unified_msg_origin,cid,key,plan,[],history)
                    turns.append((event,key,plan))
                await asyncio.gather(*(router.delivery.send(*turn) for turn in turns))
                texts=[''.join(part['data']['text'] for part in sent['message'] if part['type']=='text') for sent in shared.sent]
                assert texts in (['A1','A2','B1','B2'],['B1','B2','A1','A2']),texts
                for event,key,_ in turns:
                    await router.tasks.repair_delivery(key,manager)
                    assert router.tasks.delivery(key)['state']=='sent'
                report['concurrent_delivery']={'same_group_noninterleaved':True,'event_scoped_bot_restored':all(e.bot is shared for e,_,_ in turns)}
                # A framework model error becomes one local message, never raw SDK error text.
                from astrbot.core.provider.entities import LLMResponse
                error_msg=copy.deepcopy(msg);error_msg.message_id='local-model-error';error_msg.sender=MessageMember('335','synthetic')
                bot=Bot();event=AiocqhttpMessageEvent('test',error_msg,PlatformMetadata(name='aiocqhttp',description='offline',id='qqbot'),'111',bot)
                event.session_id=build_unique_session_id(event)
                gen=router.on_group(event);req=await anext(gen)
                response=LLMResponse(role='err',completion_text='synthetic private SDK error detail')
                await router.preserve_gateway_text(event,SimpleNamespace(messages=[]),response)
                await stage._save_to_history(event,req,response,[],None)
                event.set_result(event.plain_result(response.completion_text))
                await router.deliver_reply(event);await router.deliver_reply(event);await respond.process(event)
                assert len(bot.sent)==1
                text=''.join(part['data']['text'] for part in bot.sent[0]['message'] if part['type']=='text')
                assert 'SDK' not in text and 'qqbot_reply' not in text
                try:await anext(gen)
                except StopAsyncIteration:pass
                assert (await manager.get_conversation(event.unified_msg_origin,req.conversation.cid)).history=='[]'
                report['local_model_error']={'single_local_text':True,'no_assistant_history':True,'raw_error_not_disclosed':True}

                # Startup must repair an interrupted round before publishing the ready marker.
                from qqbot_gateway.task_store import TaskStore
                umo='qqbot:GroupMessage:startup-synthetic'
                cid=await manager.new_conversation(umo,router.persona_id)
                plan=ReplyPlan('chat',('confirmed','unconfirmed'),'confirmed\nunconfirmed')
                history=[{'role':'user','content':'synthetic'},{'role':'assistant','content':plan.canonical_text}]
                await manager.update_conversation(umo,cid,history)
                key='startup';router.tasks.accept(key,key)
                router.tasks.prepare_delivery(key,umo,cid,key,plan,[],history)
                router.tasks.begin_part(key,0);router.tasks.part_result(key,0,'sent','999')
                router.tasks.begin_part(key,1)
                router.tasks.close();router.tasks=TaskStore(root/'state/tasks.sqlite')
                async def persona_noop(*args,**kwargs):pass
                router.context.persona_manager=SimpleNamespace(get_persona=persona_noop,update_persona=persona_noop)
                await router.initialize()
                restored=json.loads((await manager.get_conversation(umo,cid)).history)
                assert restored[-1]['content']=='confirmed'
                assert router.tasks.delivery(key)['repair']=='repaired'
                assert (root/'state/router-ready.json').exists()
                report['startup_recovery']={'confirmed_prefix_only':True,'before_ready':True,'no_send_or_model':True}
                await router.terminate()


            finally:router.tasks.close()
        report['synthetic_attempts']=synthetic.attempts
        assert synthetic.attempts==len(report['cases'])
        print(f"PASS: {len(report['cases'])} actual SDK/runner/history/decorate/event-send cases; 0 real model/QQ.")
    finally:
        await provider.client.close();await server.cleanup()
        from astrbot.core import sp, db_helper
        await sp.close();await db_helper.engine.dispose()
    (report_path or ROOT/'reports/lap-16-offline-2026-10-17.json').write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))


if __name__=='__main__':
    previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap16-framework-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:asyncio.run(verify())
        finally:os.chdir(previous)
