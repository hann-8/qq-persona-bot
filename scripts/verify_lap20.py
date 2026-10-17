"""Installed SDK/runner/framework synthetic group flow; zero real model/QQ/SSH."""
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
os.environ['ASTRBOT_DISABLE_METRICS']='1'


async def verify(root,backend,mode,full_lifecycle=False,lap24=False,lap25=False):
    import yaml
    from aiohttp import web
    from astrbot.api.platform import AstrBotMessage,MessageMember,MessageType,PlatformMetadata
    from astrbot.api.message_components import Plain,At,Reply
    from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
    from astrbot.core.astr_main_agent import collect_initial_request,build_main_agent,MainAgentBuildConfig
    from astrbot.core.agent.message import Message
    from astrbot.core.agent.runners.base import AgentState
    from astrbot.core.agent.runners.tool_loop_agent_runner import ToolLoopAgentRunner
    from astrbot.core.pipeline.process_stage.method.agent_sub_stages.internal import InternalAgentSubStage
    from astrbot.core.pipeline.result_decorate.stage import ResultDecorateStage
    from astrbot.core.pipeline.respond.stage import RespondStage
    from astrbot.core.config.default import DEFAULT_CONFIG
    import astrbot.core.pipeline.result_decorate.stage as decorate_module
    from plugins.qq_router.main import QQRouter
    from plugins.qq_router.provider import QQBotProvider
    from scripts.verify_lap17 import Harness
    from qqbot_gateway.model_gateway import application,ModelQueue
    from qqbot_gateway.task_store import TaskStore
    from qqbot_gateway.web_retrieval import WebRunner,Retriever
    from qqbot_gateway.token_budget import InputBudget
    from qqbot_gateway.group_protocol import SILENT

    class Manager:
        def __getattr__(self,name):raise AssertionError('Personal history accessed: '+name)
    class Bot:
        def __init__(self,ack='ok'):self.sent=[];self.ack=ack
        async def send_group_msg(self,**kwargs):
            self.sent.append(kwargs)
            if self.ack=='error':raise ConnectionError('synthetic')
            if self.ack=='timeout':await asyncio.sleep(1)
            if self.ack=='missing':return {}
            return {'message_id':len(self.sent)}
    settings=yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
    settings['bot']['qq']='222';settings['access'].update(allowed_groups=['111','444'],admin_users=['333'],blocked_users=['999'])
    settings['llm']['backend']=backend
    settings['participation'].update(mode='free',debounce_seconds=.5,max_batch_wait_seconds=2)
    settings['output'].update(delivery_mode=mode,bubble_delay_min_ms=0,bubble_delay_max_ms=0)
    if backend=='ollama_ssh':settings['llm']['profiles'][backend]['expected_digest']='a'*64
    (root/'config').mkdir();(root/'state').mkdir()
    (root/'config/settings.local.yaml').write_text(yaml.safe_dump(settings),encoding='utf-8')
    (root/'config/persona.md').write_text('合成人设',encoding='utf-8')
    connection='a'*64
    def connect(value=connection,online=True):
        import psutil,time
        (root/'state/gate-connection.json').write_text(json.dumps(dict(id=value,connected=True,online=online,pid=os.getpid(),created=psutil.Process().create_time(),updated=time.time())),encoding='utf-8')
    connect()
    os.environ['QQBOT_INSTANCE_ID']='lap20-synthetic'
    with patch.dict(os.environ,{'QQBOT_ROOT':str(root)}):router=QQRouter(SimpleNamespace(conversation_manager=Manager()))
    router.delivery.timeout=.03
    harness=Harness(root,backend)
    wrapped=WebRunner(harness,Retriever(settings['web']),InputBudget(),settings['output'])
    queue=ModelQueue(wrapped);token=secrets.token_urlsafe(32)
    server=web.AppRunner(application(queue,token,output=settings['output']),access_log=None)
    await server.setup();site=web.TCPSite(server,'127.0.0.1',0);await site.start()
    port=site._server.sockets[0].getsockname()[1]
    provider=QQBotProvider(dict(id='lap20',type='qqbot_openai',api_base=f'http://127.0.0.1:{port}/v1',key=[token],
        model='workbuddy-local',modalities=['text'],custom_extra_body={},timeout=10),{})
    config=copy.deepcopy(DEFAULT_CONFIG);config['t2i']=False;config['content_safety']['also_use_in_response']=False
    config['provider_settings'].update(prompt_prefix='{{prompt}}',identifier=False,group_name_display=False,datetime_system_prompt=False,web_search=False)
    config['kb_names']=[];config['provider_ltm_settings']['group_message_history_enable']=False
    config['provider_tts_settings']['enable']=False;config['provider_settings']['display_reasoning_text']=False
    # Intentionally hostile old quote settings: event capability must still enforce direct text.
    config['platform_settings'].update(reply_prefix='',reply_with_mention=True,reply_with_quote=True,forward_threshold=100000)
    config['platform_settings']['segmented_reply']['enable']=False
    async def no_tts(*args):return None
    ctx=SimpleNamespace(astrbot_config=config,plugin_manager=SimpleNamespace(context=SimpleNamespace(get_using_tts_provider_async=no_tts)))
    decorate=ResultDecorateStage();respond=RespondStage();await decorate.initialize(ctx);await respond.initialize(ctx)
    stage=InternalAgentSubStage();stage.conv_manager=Manager()
    serial=0
    def event(mention=False,sender='333',group='111',text='合成文字',ack='ok',mid=None):
        nonlocal serial
        serial+=1;msg=AstrBotMessage();msg.self_id='222';msg.type=MessageType.GROUP_MESSAGE
        msg.group_id=group;msg.sender=MessageMember(sender,'合成显示名');msg.message_id=mid or str(serial)
        msg.message=([At(qq='222')] if mention else [])+[Plain(text=text)];msg.message_str=text;msg.session_id=group
        msg.raw_message=dict(qqbot_connection=connection)
        return AiocqhttpMessageEvent(text,msg,PlatformMetadata(name='aiocqhttp',description='offline',id='qqbot'),group,Bot(ack))

    async def finish(gen):
        try:await anext(gen)
        except StopAsyncIteration:pass

    async def complete(e,req,text):
        harness.text=text
        # Actual runner request method forwards session_id through project provider to SDK.
        e.set_extra('provider_request',req)
        from astrbot.api.star import Context
        plugin_context=Context.__new__(Context)
        plugin_context.conversation_manager=Manager();plugin_context.get_config=lambda **kwargs:config
        plugin_context.kb_manager=None;plugin_context._db=None
        from unittest.mock import AsyncMock
        import astrbot.core.tools.knowledge_base_tools as kb_module
        with patch.object(kb_module.sp,'session_get',AsyncMock(return_value={})),patch.object(kb_module.sp,'get_async',AsyncMock(return_value={})):
            built=await build_main_agent(event=e,plugin_context=plugin_context,provider=provider,
                config=MainAgentBuildConfig(tool_call_timeout=5,streaming_response=False,add_cron_tools=False,llm_safety_mode=False,
                    provider_settings=config['provider_settings'],request_max_retries=1))
        assert built.provider_request.conversation is None and built.provider_request.contexts==[]
        assert built.provider_request.prompt==req.prompt and built.provider_request.extra_user_content_parts==[]
        assert built.provider_request.func_tool is None or built.provider_request.func_tool.empty()
        runner=built.agent_runner;messages=runner.run_context.messages
        handler=SimpleNamespace(handler_module_path='lap20',handler_name='deliver_reply',handler=router.deliver_reply)
        from astrbot.core.star.star_handler import EventType
        def handlers(kind,**kwargs):return [handler] if kind==EventType.OnDecoratingResultEvent else []
        with patch.object(decorate_module.star_handlers_registry,'get_handlers_by_event_type',side_effect=handlers),patch.dict(decorate_module.star_map,{'lap20':SimpleNamespace(name='lap20')}):
            if full_lifecycle:
                from astrbot.core.astr_agent_run_util import run_agent
                async def done(context,response):
                    await router.preserve_gateway_text(e,context,response)
                with patch.object(runner.agent_hooks,'on_agent_done',side_effect=done):
                    async for _ in run_agent(runner,max_step=1,show_tool_use=False):
                        async for _ in decorate.process(e):pass
                        await respond.process(e)
                await stage._save_to_history(e,req,runner.get_final_llm_resp(),messages,None)
            else:
                responses=[r async for r in runner._iter_llm_responses()]
                assert len(responses)==1
                await router.preserve_gateway_text(e,runner.run_context,responses[0])
                await stage._save_to_history(e,req,responses[0],messages,None)
                e.set_result(e.plain_result(responses[0].completion_text))
                async for _ in decorate.process(e):pass
                await respond.process(e)

    silent=json.dumps(dict(qqbot_group_reply=1,decision='silent',kind='chat',bubbles=[],meme_id=None))
    speak=json.dumps(dict(qqbot_group_reply=1,decision='speak',kind='chat',bubbles=['合成回复'],meme_id=None),ensure_ascii=False)

    report=[]
    try:
        if lap25:
            for case,raw in [('fenced','```json\n'+speak+'\n```'),('plain','普通合成答复'),
                             ('optional',json.dumps(dict(bubbles='普通合成答复',reason='inert'))),
                             ('gateway_budget',speak),('final_system_trim',speak)]:
                router.group_turns.reset('111')
                if case=='final_system_trim':
                    for n in range(30):router.group_turns.append('111','old',str(n),'old','x'*350)
                e=event(True);gen=router.on_group(e);req=await anext(gen)
                if case=='gateway_budget':req.system_prompt+='S'*20000
                if case=='final_system_trim':req.system_prompt+='S'*7500
                before=harness.attempts;await complete(e,req,raw);await finish(gen)
                assert len(e.bot.sent)==1,(case,e.bot.sent)
                assert harness.attempts==before+int(case!='gateway_budget'),case
                if case=='gateway_budget':
                    from qqbot_gateway.errors import MESSAGES
                    assert MESSAGES['INPUT_TOO_LONG'] in str(e.bot.sent)
                    assert router.tasks.delivery(e.get_extra('qq_delivery_key'))['reason']=='gateway_input_too_long'
                else:assert ('合成回复' if case in ('fenced','final_system_trim') else '普通合成答复') in str(e.bot.sent)
                report.append(dict(case='lap25_'+case,generations=harness.attempts-before,sends=1))
        if full_lifecycle:
            if lap24:
                for kind,number in [('chat',1),('chat',2),('chat',3),('answer',3)]:
                    router.group_turns.reset('111')
                    e=event(True);gen=router.on_group(e);req=await anext(gen)
                    raw=json.dumps(dict(qqbot_group_reply=1,decision='speak',kind=kind,
                        bubbles=['合成正文'+str(i) for i in range(number)],meme_id=None),ensure_ascii=False)
                    before=harness.attempts
                    await complete(e,req,raw);await finish(gen)
                    expected=number if kind=='chat' and mode=='adaptive' else 1
                    assert len(e.bot.sent)==expected,(kind,number,e.bot.sent)
                    key=e.get_extra('qq_delivery_key')
                    assert all(state=='sent' for _,state,_ in router.tasks.parts(key))
                    count=len(e.bot.sent);await router.deliver_reply(e);assert len(e.bot.sent)==count
                    assert harness.attempts==before+1
                    report.append(dict(case='lap24_'+kind+str(number),sends=count,generations=1,ack=True))
            for mention in (False,True):
                for case,text in (('speak',speak),('silent',silent),('bad','{"broken"')):
                    router.group_turns.reset('111')
                    e=event(mention);gen=router.on_group(e);req=await anext(gen)
                    before=harness.attempts
                    await complete(e,req,text)
                    await finish(gen)
                    count=len(e.bot.sent)
                    assert count==int(mention or case=='speak'),(case,mention,count)
                    if case=='speak':
                        assert '合成回复' in str(e.bot.sent),(case,mention,'canonical reply missing')
                    elif mention:
                        assert '没接住' in str(e.bot.sent),(case,mention,'protocol fallback missing')
                    assert harness.attempts==before+1
                    assert e.get_extra('qq_delivery_handled'),(case,mention,'delivery hook skipped')
                    report.append(dict(case='full_lifecycle_'+case,mention=mention,generations=1,sends=count))
        for mention in (False,True):
            for case in ('speak','silent','bad','tamper','missing','error','timeout','stop','disconnect','framework_error','late','blocked'):
                router.group_turns.reset('111')
                # Prior unknown ACK evidence remains; new messages stay admissible.
                bot_ack=case if case in ('missing','error','timeout') else 'ok'
                e=event(mention,ack=bot_ack,sender='999' if case=='blocked' else '333')
                gen=router.on_group(e);attempts=harness.attempts
                try:req=await anext(gen)
                except StopAsyncIteration:
                    assert case=='blocked';assert harness.attempts==attempts and not e.bot.sent
                    report.append(dict(case=case,mention=mention,generations=0,sends=0));continue
                assert req.conversation is None and req.contexts==[] and req.func_tool is None
                e.set_extra('provider_request',req)
                resolved,_=await collect_initial_request(e,SimpleNamespace(conversation_manager=Manager()),SimpleNamespace())
                assert resolved.conversation is None
                if case=='framework_error':
                    await e.send(e.plain_result('framework raw exception'));assert not e.bot.sent
                    await finish(gen)
                    assert len(e.bot.sent)==int(mention)
                    report.append(dict(case=case,mention=mention,generations=0,sends=len(e.bot.sent)));continue
                harness.text=('{"broken"' if case=='bad' else json.dumps(dict(qqbot_group_reply=1,
                    decision='silent' if case=='silent' else 'speak',kind='chat',bubbles=[] if case=='silent' else ['第一条','第二条'],meme_id=None),ensure_ascii=False))
                response=await provider.text_chat(prompt=req.prompt,system_prompt=req.system_prompt,contexts=req.contexts,
                    session_id=req.session_id,func_tool=None,request_max_retries=1)
                assert harness.attempts==attempts+1
                assert isinstance(response.raw_completion.qqbot_group_plan,dict)
                if case=='tamper':response.raw_completion.qqbot_group_plan['request']['epoch']='b'*64
                run=SimpleNamespace(messages=[Message(role='user',content=req.prompt)])
                class Hooks:
                    async def on_agent_done(self,context,result):await router.preserve_gateway_text(e,context,result)
                runner=ToolLoopAgentRunner.__new__(ToolLoopAgentRunner);runner._state=AgentState.RUNNING
                runner.stats=SimpleNamespace(end_time=None);runner.run_context=run;runner.agent_hooks=Hooks();runner._pending_follow_ups=[]
                # Recheck invalidation at completion as well as result decoration.
                if case=='stop':(root/'state/stop-request.json').write_text('{"instance_id":"lap20-synthetic"}',encoding='utf-8')
                if case=='disconnect':connect('b'*64)
                if case=='late':e.set_extra('qq_group_created',e.get_extra('qq_group_created')-181)
                await runner._complete_with_assistant_response(response)
                await stage._save_to_history(e,req,response,run.messages,None)
                sent_before=len(e.bot.sent)
                await e.send(e.plain_result(SILENT));assert len(e.bot.sent)==sent_before
                e.set_result(e.plain_result(response.completion_text))
                handler=SimpleNamespace(handler_module_path='lap20',handler_name='deliver_reply',handler=router.deliver_reply)
                with patch.object(decorate_module.star_handlers_registry,'get_handlers_by_event_type',return_value=[handler]),patch.dict(decorate_module.star_map,{'lap20':SimpleNamespace(name='lap20')}):
                    async for _ in decorate.process(e):pass
                await respond.process(e);count=len(e.bot.sent)
                await router.deliver_reply(e);assert len(e.bot.sent)==count
                await finish(gen)
                for sent in e.bot.sent:
                    assert all(p['type']=='text' for p in sent['message']),sent
                    assert SILENT not in str(sent) and 'qqbot_group_reply' not in str(sent)
                should_speak=case in ('speak','missing','error','timeout') or mention and case in ('silent','bad','tamper','late')
                assert bool(e.bot.sent)==should_speak,(case,mention,e.bot.sent)
                key=e.get_extra('qq_delivery_key');row=router.tasks.delivery(key)
                if row:
                    confirmed=sum(state=='sent' for _,state,_ in router.tasks.parts(key))
                    bot_rows=[r for r in router.group_turns.snapshot('111') if r['speaker']=='bot']
                    assert len(bot_rows)==confirmed,(case,confirmed,bot_rows)
                    assert req.prompt not in str(row)
                    if case in ('missing','error','timeout'):assert not router.tasks.group_blocked('111')
                report.append(dict(case=case,mention=mention,generations=harness.attempts-attempts,sends=count))
                (root/'state/stop-request.json').unlink(missing_ok=True);connect()
        router.group_turns.reset('111')
        # Two speakers are batched once. Snapshot stays immutable as later events arrive.
        e1=event(text='batch one');g1=router.on_group(e1);first=asyncio.create_task(anext(g1));await asyncio.sleep(.05)
        e2=event(sender='334',text='batch two');g2=router.on_group(e2)
        try:await anext(g2)
        except StopAsyncIteration:pass
        req=await first;body=json.loads(req.prompt)
        assert [r['text'] for r in body['messages']]==['batch one','batch two']
        assert len({r['speaker'] for r in body['messages']})==2
        duplicate=event(sender='334',mid=e2.message_obj.message_id,text='batch two')
        assert not [x async for x in router.on_group(duplicate)]
        assert len(router.group_turns.snapshot('111'))==2
        await complete(e1,req,silent);await finish(g1)
        before=harness.attempts;await asyncio.sleep(.1);assert harness.attempts==before
        # A pending ambient gets cancelled; a running ambient finishes once and is suppressed.
        router.group_turns.reset('111')
        e1=event(text='active');g1=router.on_group(e1);req=await anext(g1)
        frozen=req.prompt
        e2=event(sender='334',text='next ambient');g2=router.on_group(e2);pending=asyncio.create_task(anext(g2));await asyncio.sleep(.55)
        e3=event(True,sender='335',text='must reply one');g3=router.on_group(e3);priority=asyncio.create_task(anext(g3));await asyncio.sleep(.03)
        assert req.prompt==frozen and 'next ambient' not in frozen
        await complete(e1,req,speak);assert not e1.bot.sent;await finish(g1)
        mention_req=await priority
        try:await pending
        except StopAsyncIteration:pass
        assert not e2.bot.sent and not e2.get_extra('qq_group_request')
        # Evaluation and speech limits never suppress either distinct @ ticket.
        w=router.group_turns.window('111');import time
        w.spoken.extend([time.monotonic()]*20);w.evaluations.extend([time.monotonic()]*60)
        e4=event(True,sender='336',text='must reply two');g4=router.on_group(e4);another=asyncio.create_task(anext(g4));await asyncio.sleep(.03)
        await complete(e3,mention_req,speak);await finish(g3)
        second_req=await another
        assert json.loads(mention_req.session_id[len('qqbot-group:'):])['request_key']!=json.loads(second_req.session_id[len('qqbot-group:'):])['request_key']
        await complete(e4,second_req,speak);await finish(g4)
        assert len(e3.bot.sent)==len(e4.bot.sent)==1
        # Only current batch row can be a search anchor, never the previous topic.
        router.group_turns.reset('111');router.web['enabled']=True
        old=event(True,text='查一下月球半径');oldgen=router.on_group(old);oldreq=await anext(oldgen)
        assert json.loads(oldreq.prompt)['web_anchor']=='查一下月球半径'
        await complete(old,oldreq,speak);await finish(oldgen)
        w=router.group_turns.window('111');w.evaluations.clear()
        fresh=event(text='新的普通闲聊');freshgen=router.on_group(fresh);freshreq=await anext(freshgen)
        assert json.loads(freshreq.prompt)['web_anchor'] is None
        await complete(fresh,freshreq,silent);await finish(freshgen)
        report.append(dict(case='multiuser_batch_dedup_snapshot_priority_distinct_mentions_anchor',passed=True))
        before=harness.attempts
        for variant in ('private','unauthorized','self','blocked','media'):
            admission=event(sender='222' if variant=='self' else '999' if variant=='blocked' else '333',group='999' if variant=='unauthorized' else '111',text='[非文本未解析]' if variant=='media' else '不应生成')
            if variant=='private':admission.message_obj.type=MessageType.FRIEND_MESSAGE
            if variant=='media':admission.message_obj.raw_message['qqbot_media']=True
            assert not [r async for r in router.on_group(admission)]
            assert not admission.bot.sent and harness.attempts==before
        # Embedded Reply bodies are ignored and cannot reach framework quote expansion.
        router.group_turns.reset('111')
        quoted=event(True,text='引用问题')
        quoted.message_obj.message.insert(0,Reply(id='absent',chain=[Plain(text='BLOCKED EMBEDDED BODY')]))
        quotedgen=router.on_group(quoted);quotedreq=await anext(quotedgen)
        assert 'BLOCKED EMBEDDED BODY' not in quotedreq.prompt and not any(isinstance(c,Reply) for c in quoted.get_messages())
        assert '引用未解析' in quotedreq.prompt
        await complete(quoted,quotedreq,speak);await finish(quotedgen)
        report.append(dict(case='scope_media_and_embedded_quote',passed=True))
        # A waiting new mention continues after a preceding unknown ACK, without replay.
        router.group_turns.reset('111')
        uncertain=event(True,ack='missing');uncertaingen=router.on_group(uncertain);uncertainreq=await anext(uncertaingen)
        queued=event(True,sender='334');queuedgen=router.on_group(queued);queuedtask=asyncio.create_task(anext(queuedgen));await asyncio.sleep(.03)
        await complete(uncertain,uncertainreq,speak);await finish(uncertaingen)
        attempts=harness.attempts
        queuedreq=await queuedtask
        await complete(queued,queuedreq,speak);await finish(queuedgen)
        assert harness.attempts==attempts+1 and len(queued.bot.sent)==1 and queued.get_extra('qq_group_request')
        assert not router.tasks.group_blocked('111')
        report.append(dict(case='waiting_mention_continues_after_unknown_ack',passed=True))
        # Reopen unknown intent: discard RAM target without touching personal manager or resending.
        from qqbot_gateway.reply_plan import ReplyPlan
        key='crash';router.tasks.accept(key,'t');router.tasks.prepare_group_delivery(key,'444','e','r',ReplyPlan('answer',('bot','bot2'),'bot\nbot2'),'d',[1,2]);router.tasks.begin_part(key,0)
        router.tasks.close();router.tasks=TaskStore(root/'state/tasks.sqlite')
        await router.tasks.recover_deliveries(Manager())
        assert not router.tasks.group_blocked('444') and router.tasks.delivery(key)['repair']=='ram_discarded'
        return dict(backend=backend,mode=mode,real_model_requests=0,real_qq_messages=0,real_ssh=0,cases=report,
            original_event=True,no_personal_conversation=True,recovery=True,usage=queue.group_usage)
    finally:
        router.tasks.close();await provider.client.close();await server.cleanup()


def main():
    results=[];previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap20-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    root=Path(directory)/(backend+'-'+mode);root.mkdir()
                    results.append(asyncio.run(verify(root,backend,mode)))
                    print('PASS',backend,mode,len(results[-1]['cases']))
        finally:os.chdir(previous)
    (ROOT/'reports/lap-20-framework-offline.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

if __name__=='__main__':main()
