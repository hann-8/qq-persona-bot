"""LAP-43 targeted actual AstrBot/provider/run_agent and memory integration.
Scaffolding follows LAP-27; all inputs/credentials/transports are synthetic.
"""
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
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
os.environ['ASTRBOT_DISABLE_METRICS']='1'


async def verify(root,backend,mode,participation="free",attention=False,memes=False,web_enabled=False,memory=False,members=False,material_kind=None):
    full_lifecycle=True
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
    from astrbot.core.db.po import Conversation
    class Conversations:
        def __init__(self):self.current={};self.items={};self.calls=0
        async def get_curr_conversation_id(self,umo):self.calls+=1;return self.current.get(umo)
        async def get_conversation(self,umo,cid):return self.items[(umo,cid)]
        async def new_conversation(self,umo,persona_id):
            cid=str(len(self.items)+1);self.current[umo]=cid
            self.items[(umo,cid)]=Conversation('qqbot',umo,cid,history='[]',persona_id=persona_id)
            return cid
        async def update_conversation(self,umo,cid,history,**kwargs):self.items[(umo,cid)].history=json.dumps(history,ensure_ascii=False)
    manager=Conversations()
    from qqbot_gateway.members import MemberClient,DEFAULTS as MEMBER_DEFAULTS
    from qqbot_gateway.onebot_gate import OneBotGate
    from qqbot_gateway.config import GateConfig
    from aiohttp import WSMsgType
    import time
    from qqbot_gateway.model_gateway import application,ModelQueue
    from qqbot_gateway.task_store import TaskStore
    from qqbot_gateway.token_budget import InputBudget
    from qqbot_gateway.group_protocol import SILENT

    class Manager:
        def __getattr__(self,name):raise AssertionError('Personal history accessed: '+name)
    class Bot:
        def __init__(self,ack='ok'):self.sent=[];self.ack=ack
        async def send_group_msg(self,**kwargs):
            class Capture:
                def __init__(self):self.rows=[]
                async def send_json(self,value):self.rows.append(value)
                async def send_str(self,value):self.rows.append(json.loads(value))
            async def frames(value):yield SimpleNamespace(type=WSMsgType.TEXT,data=json.dumps(value))
            echo='send-'+secrets.token_hex(8);pending=set();down=Capture();up=Capture()
            class Duplex:
                def __aiter__(self):return frames(dict(action='send_group_msg',params=kwargs,echo=echo))
                async def send_json(self,value):await up.send_json(value)
            await gate._outgoing(Duplex(),down,pending)
            if not down.rows:
                from aiocqhttp.exceptions import ActionFailed
                raise ActionFailed(up.rows[-1])
            assert len(down.rows)==1,up.rows
            wire=down.rows[0];self.sent.append(wire['params'])
            assert 'qqbot_mention_permission' not in json.dumps(wire)
            if self.ack=='error':raise ConnectionError('synthetic')
            if self.ack=='timeout':await asyncio.sleep(1)
            data={} if self.ack=='missing' else {'message_id':10000+serial*10+len(self.sent)}
            # An untrusted adapter claim is always replaced by the gate.
            data['qqbot_mention_applied']=True
            await gate._incoming(frames(dict(status='ok',retcode=0,data=data,echo=echo)),up,pending)
            assert len(up.rows)==1 and not pending
            return up.rows[0]['data']
    settings=yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
    settings['participation']['silence']={'enabled':True}  # legacy-disabled regression
    settings['bot']['qq']='222';settings['access'].update(allowed_groups=['111','444'],admin_users=['333'],blocked_users=['999'])
    settings['llm']['backend']=backend
    settings['vision']=dict(enabled=False,input_reserve_tokens=4096)
    settings['members']=dict(MEMBER_DEFAULTS,enabled=members,mentions_enabled=members)
    settings['memory']=dict(enabled=memory,learning_enabled=memory)
    settings['chat']['user_cooldown_seconds']=0
    settings['participation'].update(mode=participation,debounce_seconds=.5,max_batch_wait_seconds=2)
    settings['participation']['attention']['enabled']=attention
    settings['memes'].update(enabled=memes,cooldown_seconds=0,same_meme_cooldown_seconds=0)
    settings['web']['enabled']=web_enabled
    settings['output'].update(delivery_mode=mode,bubble_delay_min_ms=0,bubble_delay_max_ms=0)
    if backend=='ollama_ssh':settings['llm']['profiles'][backend]['expected_digest']='a'*64
    (root/'config').mkdir();(root/'state').mkdir()
    (root/'config/settings.local.yaml').write_text(yaml.safe_dump(settings),encoding='utf-8')
    (root/'config/persona.md').write_text('合成人设',encoding='utf-8')
    meme_id=None
    if memes:
        import io
        from PIL import Image
        from qqbot_gateway.meme_catalog import MemeCatalog
        catalog=MemeCatalog(root,settings['memes']);image=io.BytesIO();Image.new('RGB',(3,3),'red').save(image,format='PNG')
        row=catalog.add(image.getvalue());row.update(name='自造红块',tags=['开心'],enabled=True);catalog.save();meme_id=row['id']
    connection='a'*64
    def connect(value=connection,online=True):
        gate.connection_id=value;gate.online=online;gate.publish_connection()
    os.environ['QQBOT_INSTANCE_ID']='lap20-synthetic'
    with patch.dict(os.environ,{'QQBOT_ROOT':str(root)}),patch('qqbot_gateway.members.suspend_unverified',side_effect=lambda settings:settings['members']),patch('qqbot_gateway.vision.context_token',return_value='c'*64):
        router=QQRouter(SimpleNamespace(conversation_manager=manager))
    router.delivery.timeout=.5
    if backend=='codebuddy_cli':
        # Construct the existing bottom substitute without validating the installed
        # CLI artifact: no real CLI is executed or substituted into evidence.
        from test_cli_runner import RunnerTests
        fixture=RunnerTests();fixture.root=root;fixture.script=root/'synthetic_cli.py'
        synthetic=fixture.runner(effort='auto')
        synthetic.denied=json.loads((ROOT/'config/cli-tools-denied.json').read_text(encoding='utf-8'))
        with patch('scripts.verify_lap17.CLIRunner',return_value=synthetic):harness=Harness(root,backend)
    else:harness=Harness(root,backend)
    native_inputs=[]
    if backend=='codebuddy_cli':
        fake=harness.script.read_text(encoding='utf-8').replace('sys.stdin.read()',"Path(__file__).with_suffix('.input').write_text(sys.stdin.buffer.read().decode('utf-8'),encoding='utf-8')")
        harness.script.write_text(fake,encoding='utf-8')
    else:
        original_factory=harness.runner.factory
        class CaptureNative(original_factory):
            def request(self,method,path,payload=None,**kwargs):
                if path=='/api/chat':native_inputs.append(copy.deepcopy(payload))
                return super().request(method,path,payload,**kwargs)
        harness.runner.factory=CaptureNative
    # Same runner as production: no external retriever or material wrapper.
    if backend=='codebuddy_cli':
        harness.runner.web_settings=dict(provider='codebuddy_native',enabled=web_enabled,search_enabled=False)
        from test_native_web import native_fake
        harness.script.write_text(native_fake(harness.script.read_text(encoding='utf-8')),encoding='utf-8')
    wrapped=harness.runner
    queue=ModelQueue(wrapped);token=secrets.token_urlsafe(32)
    wrapped.memes=router.memes
    gate=OneBotGate(GateConfig('222',frozenset({'111','444'}),frozenset({'333'}),'a'*40,'b'*40,root/'state/gate.db',participation_mode=participation,members_enabled=members,members_config=settings['members'],media_catalog=router.memes if memes else None,blocked_users=frozenset({'999'}),attention_enabled=attention,silence_enabled=True),root)
    gate.context_token='c'*64;gate.connected=True;gate.online=True;gate.connection_id=connection
    connect()
    async def forbidden_rpc(action,params):
        if action=='get_group_info':return dict(group_id=int(params['group_id']),member_count=2)
        return [dict(group_id=int(params['group_id']),user_id=333,nickname='自造成员'),dict(group_id=int(params['group_id']),user_id=555,nickname='另一成员')]
    gate.member_rpc=forbidden_rpc
    gate.members.observe=lambda data:dict(count=2,age=0,source='synthetic')
    private_server=web.AppRunner(gate.application(),access_log=None);await private_server.setup()
    private_site=web.TCPSite(private_server,'127.0.0.1',0);await private_site.start()
    private_port=private_site._server.sockets[0].getsockname()[1]
    client=MemberClient(f'http://127.0.0.1:{private_port}/context/members','c'*64) if members else None
    router.member_client=client;router.delivery.members=client
    v2=dict(mode=participation,config_version=__import__('qqbot_gateway.reply_plan',fromlist=['digest']).digest(router.persona_id),aliases=router.participation['attention']['aliases'],mentions_enabled=members,memory_enabled=memory,learning_enabled=memory)
    server=web.AppRunner(application(queue,token,output=settings['output'],memes=router.memes,v2=v2,members=client),access_log=None)
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
    stage=InternalAgentSubStage();stage.conv_manager=manager
    serial=0
    def event(mention=False,sender='333',group='111',text='合成文字',ack='ok',mid=None):
        nonlocal serial
        serial+=1;msg=AstrBotMessage();msg.self_id='222';msg.type=MessageType.GROUP_MESSAGE
        msg.group_id=group;msg.sender=MessageMember(sender,'合成显示名');msg.message_id=mid or str(serial)
        msg.message=([At(qq='222')] if mention else [])+[Plain(text=text)];msg.message_str=text;msg.session_id=group
        msg.raw_message=dict(qqbot_connection=connection,qqbot_at_ids=['222'] if mention else [])
        e=AiocqhttpMessageEvent(text,msg,PlatformMetadata(name='aiocqhttp',description='offline',id='qqbot'),group,Bot(ack))
        from astrbot.core.pipeline.waking_check.stage import build_unique_session_id
        e.session_id=build_unique_session_id(e)
        return e

    async def finish(gen):
        try:await anext(gen)
        except StopAsyncIteration:pass

    async def complete(e,req,text,tamper=None):
        harness.text=text
        # Actual AstrBot event-hook dispatcher binds the per-task pre-HTTP guard.
        from astrbot.core.pipeline.context_utils import call_event_hook
        from astrbot.core.star.star_handler import EventType
        before_handler=SimpleNamespace(handler_module_path='lap43',handler_name='before_provider',handler=router.before_provider)
        with patch.object(decorate_module.star_handlers_registry,'get_handlers_by_event_type',return_value=[before_handler]),patch.dict(decorate_module.star_map,{'lap43':SimpleNamespace(name='lap43')}):
            await call_event_hook(e,EventType.OnLLMRequestEvent,req)
        # Actual runner request method forwards session_id through project provider to SDK.
        e.set_extra('provider_request',req)
        from astrbot.api.star import Context
        plugin_context=Context.__new__(Context)
        plugin_context.conversation_manager=manager;plugin_context.get_config=lambda **kwargs:config
        plugin_context.kb_manager=None;plugin_context._db=None
        from unittest.mock import AsyncMock
        plugin_context.persona_manager=SimpleNamespace(resolve_selected_persona=AsyncMock(return_value=(router.persona_id,{'prompt':router.persona,'tools':[],'skills':[]},None,False)))
        plugin_context.get_llm_tool_manager=lambda:SimpleNamespace(func_list=[])
        plugin_context.subagent_orchestrator=None
        import astrbot.core.tools.knowledge_base_tools as kb_module
        with patch.object(kb_module.sp,'session_get',AsyncMock(return_value={})),patch.object(kb_module.sp,'get_async',AsyncMock(return_value={})):
            built=await build_main_agent(event=e,plugin_context=plugin_context,provider=provider,
                config=MainAgentBuildConfig(tool_call_timeout=5,streaming_response=False,add_cron_tools=False,llm_safety_mode=False,
                    provider_settings=config['provider_settings'],request_max_retries=1))
        if participation=='free':assert built.provider_request.conversation is None and built.provider_request.contexts==[]
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
                    if tamper:tamper(response.raw_completion)
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

    from test_group_silence import frames as input_frames,Capture
    report=[]
    async def inbound(text='普通问题',mention=True,sender='333',group='111',ack='ok'):
        e=event(mention,sender,group,text,ack)
        raw=dict(post_type='message',message_type='group',self_id='222',user_id=sender,group_id=group,
                 message_id=e.message_obj.message_id,message=([dict(type='at',data={'qq':'222'})] if mention else [])+[dict(type='text',data={'text':text})])
        up=Capture();await gate._incoming(input_frames(raw),up,set())
        if not up.rows:return None
        e.message_obj.raw_message=up.rows[-1]
        return e
    async def control():
        assert await inbound('肥鱼先别参与讨论了',False) is None
        assert not gate.silence.normal('111')
        router.observe_gate()
    async def wake():
        assert await inbound('恢复发言',True,sender='333') is None
        e=await inbound('新问题',True,sender='555');assert e is not None
        router.observe_gate();return e
    def response(req,text='合成答复',image=False,mention_ref=None):
        if req.session_id is None:return json.dumps(dict(qqbot_reply=1,kind='chat',bubbles=text if isinstance(text,list) else [text]),ensure_ascii=False) if mode=='adaptive' else text
        if req.session_id=='qqbot-media':return json.dumps(dict(qqbot_media_reply=1,kind='chat',bubbles=[] if image else text if isinstance(text,list) else [text],meme_id=meme_id if image else None))
        source=json.loads(req.prompt)
        if 'target_seq' in source and ('version' not in source or source.get('version')!=2):pass
        if req.session_id.startswith('qqbot-group:'):
            return json.dumps(dict(qqbot_group_reply=1,decision='speak',kind='chat',bubbles=[] if image else text if isinstance(text,list) else [text],meme_id=meme_id if image else None))
        obj=dict(qqbot_turn_reply=2,decision='speak',kind='chat',bubbles=[] if image else text if isinstance(text,list) else [text],meme_id=meme_id if image else None,
                 response_to_seq=source['target_seq'],mention=dict(bubble_index=0,member_ref=mention_ref) if mention_ref else None)
        if memory:obj['memory_proposals']=[]
        return json.dumps(obj,ensure_ascii=False)
    async def start(e):
        gen=router.on_group(e);req=await anext(gen);return gen,req
    async def execute(e,text='合成答复'):
        gen,req=await start(e);before=harness.attempts
        await complete(e,req,response(req,text));await finish(gen)
        assert harness.attempts==before+1
        return req
    try:
        generation=gate.silence.states['111']['generation']
        assert await inbound('暂停发言',True,sender='555') is None
        assert gate.silence.normal('111') and gate.silence.states['111']['generation']==generation
        await control()
        for sender in ('333','555'):
            assert await inbound('普通问题',True,sender=sender) is None
            assert await inbound('',True,sender=sender) is None
        assert await inbound('恢复发言',True,sender='555') is None
        assert not gate.silence.normal('111')
        await wake()
        report.append(dict(case='owner_only_explicit_resume_muted_mentions',sends=0))
        for question in ('鱼鱼查查最新消息','鱼鱼这个怎么看？','我想问鱼鱼一个问题','帮我看看这个，鱼鱼'):
            question=question.replace('鱼鱼',router.participation['attention']['aliases'][0])
            e=await inbound(question,False);gen,req=await start(e)
            assert e.get_extra('qq_group_request')['must_reply'] is True
            await complete(e,req,response(req));await finish(gen)
            assert len(e.bot.sent)==1
        report.append(dict(case='direct_name_grammar_one_generation',sends=4))
        before=harness.attempts
        for text,kind in (('',None),('caption','video'),('caption','audio'),('caption','file'),('caption','forward')):
            e=await inbound(text)
            if kind:e.message_obj.raw_message.update(qqbot_media_kinds=[kind],qqbot_media=True)
            async for _ in router.on_group(e):raise AssertionError('local input reached provider')
            assert len(e.bot.sent)==1
        assert harness.attempts==before
        e=await inbound('',ack='missing')
        async for _ in router.on_group(e):raise AssertionError('empty mention generated')
        assert e.get_extra('qq_local_delivery_state')=='unknown' and harness.attempts==before
        report.append(dict(case='empty_at_unsupported_caption_zero_generation',sends=5,missing_ACK='unknown'))
        old_mode=router.participation['mode'];old_attention=router.attention_effective
        try:
            for test_mode,test_attention in (('mentions',False),('free',False),('free',True)):
                router.participation['mode']=test_mode;router.attention_effective=test_attention
                before_epoch=router.group_turns.group_epoch('111');before_calls=manager.calls;before=harness.attempts
                e=await inbound('重置本群上下文',sender='555')
                async for _ in router.on_group(e):raise AssertionError('denied reset generated')
                assert router.group_turns.group_epoch('111')==before_epoch and manager.calls==before_calls
                e=await inbound('重置本群上下文')
                async for _ in router.on_group(e):raise AssertionError('owner reset generated')
                assert router.group_turns.group_epoch('111')!=before_epoch and harness.attempts==before
        finally:router.participation['mode']=old_mode;router.attention_effective=old_attention
        report.append(dict(case='shared_reset_owner_only_three_mode_entries',sends=6))
        e=await inbound('直接问题');gen,req=await start(e);before=harness.attempts
        silent=json.dumps(dict(qqbot_turn_reply=2,decision='silent',kind='chat',bubbles=[],meme_id=None,response_to_seq=None,mention=None,memory_proposals=[]))
        await complete(e,req,silent);await finish(gen)
        assert harness.attempts==before+1 and len(e.bot.sent)<=1
        report.append(dict(case='direct_silent_protocol_failure_no_second_generation',sends=len(e.bot.sent)))
        # Basic event/model/ACK.
        e=await inbound();req=await execute(e)
        assert len(e.bot.sent)==1
        assert 'qqbot_output_ticket' not in json.dumps(e.bot.sent)
        if participation=='mentions' and not (memory or members or memes):assert req.session_id is None
        report.append(dict(case='normal_original_event_ACK',sends=1))
        # Same @ + silence is consumed before framework/model, and non-@ wakes fail.
        before=harness.attempts
        assert await inbound('请先不要说话',True) is None
        for text in ['肥鱼可以说了','@222','[CQ:at,qq=222]']:
            assert await inbound(text,False) is None
        assert await inbound('醒',True,sender='999') is None
        assert harness.attempts==before
        e=await wake();await execute(e);assert len(e.bot.sent)==1
        report.append(dict(case='same_at_stop_blacklist_other_member_wake',sends=1))
        # Result completed after mute->wake cannot use the fresh generation.
        e=await inbound();gen,req=await start(e)
        original_run=wrapped.run
        async def late_result(*args,**kwargs):
            result=await original_run(*args,**kwargs)
            await control();await wake()
            return result
        wrapped.run=late_result
        await complete(e,req,response(req));await finish(gen)
        wrapped.run=original_run
        assert not e.bot.sent
        key=e.get_extra('qq_delivery_key')
        if key:
            assert router.tasks.delivery(key)['state']=='failed'
            assert all(state=='failed' for _,state,_ in router.tasks.parts(key))
        if participation=='mentions':
            cid=await manager.get_curr_conversation_id(e.unified_msg_origin)
            history=json.loads((await manager.get_conversation(e.unified_msg_origin,cid)).history)
            assert not history or history[-1]['role']!='assistant'
        report.append(dict(case='old_result_after_wake_no_assistant_history',sends=0))
        # All local notices use immutable event ticket (includes reset/error/empty@).
        e=await inbound();gen=router.on_group(e)
        # Reuse valid event context without a model for the notice check.
        router.observe_gate()
        e.set_extra('qq_silence_enabled',True);e.set_extra('qq_output_ticket',e.message_obj.raw_message['qqbot_output_ticket'])
        from qqbot_gateway.event_guard import EventSendGuard
        e.set_extra('qq_send_guard',EventSendGuard(e));e.set_extra('qq_delivery_version',router.persona_id)
        e.set_extra('qq_delivery_identity',('222','111','333'))
        await router.local_notice(e,'合成本地提示');assert len(e.bot.sent)==1
        await control();await wake()
        await router.local_notice(e,'旧本地提示');assert len(e.bot.sent)==1
        report.append(dict(case='local_notice_ticket_old_rejected',sends=1))
        for category in ['空@','输入超限','冷却','排队满','排队超时','管理员限制','上下文重置','历史隔离','协议错误','生成失败','图片失败']:
            e=await inbound()
            e.set_extra('qq_silence_enabled',True);e.set_extra('qq_output_ticket',e.message_obj.raw_message['qqbot_output_ticket'])
            e.set_extra('qq_send_guard',EventSendGuard(e));e.set_extra('qq_delivery_version',router.persona_id)
            e.set_extra('qq_delivery_identity',('222','111','333'))
            await router.local_notice(e,'合成提示：'+category);assert len(e.bot.sent)==1
            await control();await wake();await router.local_notice(e,'合成旧提示：'+category)
            assert len(e.bot.sent)==1
        report.append(dict(case='all_local_notice_families_immutable_ticket',sends=11))
        # Explicit gate refusal between router allow-check and gate send is known failed.
        e=await inbound();gen,req=await start(e)
        original=e.bot.send_group_msg
        async def reject_before_gate(**kw):
            await control();await wake()
            return await original(**kw)
        e.bot.send_group_msg=reject_before_gate
        await complete(e,req,response(req));await finish(gen)
        assert not e.bot.sent
        key=e.get_extra('qq_delivery_key');assert router.tasks.delivery(key)['state']=='failed'
        assert not router.tasks.group_blocked('111')
        report.append(dict(case='gate_refusal_known_not_sent_no_unknown_lock',sends=0))
        # Already submitted ACK must finish after silence and retain sent fact.
        e=await inbound();gen,req=await start(e);original=e.bot.send_group_msg
        async def delayed_ack(**kw):
            result=await original(**kw)
            await control();await asyncio.sleep(.005)
            return result
        e.bot.send_group_msg=delayed_ack
        await complete(e,req,response(req));await finish(gen)
        assert len(e.bot.sent)==1
        assert router.tasks.delivery(e.get_extra('qq_delivery_key'))['state']=='sent'
        await wake()
        report.append(dict(case='submitted_delayed_ACK_retained',sends=1))
        # Multi-part sends stop after the already ACKed first bubble; no fake tail.
        if mode=='adaptive':
            e=await inbound();gen,req=await start(e);original=e.bot.send_group_msg
            async def stop_between_bubbles(**kw):
                result=await original(**kw)
                await control();await wake()
                return result
            e.bot.send_group_msg=stop_between_bubbles
            await complete(e,req,response(req,['第一条','第二条']));await finish(gen)
            assert len(e.bot.sent)==1
            assert router.tasks.delivery(e.get_extra('qq_delivery_key'))['state']=='partial'
            report.append(dict(case='bubble_interval_stop_wake_partial',sends=1))
        e=await inbound('搜索合成最新消息');gen,req=await start(e)
        await complete(e,req,response(req,'合成公开资料'));await finish(gen)
        assert len(e.bot.sent)==1 and '合成公开资料' in str(e.bot.sent)
        assert 'synthetic intermediate' not in str(e.bot.sent) and 'tool_use' not in str(e.bot.sent)
        metadata=e.get_extra('qq_group_metadata')
        assert not (metadata['manifest'].get('web',[]) if 'manifest' in metadata else metadata.get('web',[]))
        report.append(dict(case='native_final_only_original_event_ACK',sends=1))
        if memes:
            e=await inbound('发个开心表情');gen,req=await start(e)
            await complete(e,req,response(req,image=True));await finish(gen)
            assert len(e.bot.sent)==1 and e.bot.sent[0]['message'][0]['type']=='image'
            report.append(dict(case='image_only_original_ACK_ticket',sends=1))
            e=await inbound('发个开心表情');gen,req=await start(e)
            original_run=wrapped.run
            async def old_image(*args,**kw):
                result=await original_run(*args,**kw);await control();await wake();return result
            wrapped.run=old_image
            await complete(e,req,response(req,image=True));await finish(gen);wrapped.run=original_run
            assert not e.bot.sent
            report.append(dict(case='old_image_after_wake_rejected',sends=0))
            # File failure keeps the existing short local image notice, also ticketed.
            e=await inbound('发个开心表情');gen,req=await start(e);resolve=router.memes.resolve
            def fail_resolve(*args):raise ValueError('synthetic')
            def damage(raw):router.memes.resolve=fail_resolve
            await complete(e,req,response(req,image=True),damage);await finish(gen);router.memes.resolve=resolve
            assert len(e.bot.sent)==1 and e.bot.sent[0]['message'][0]['type']=='text'
            report.append(dict(case='failed_image_local_notice_ticket',sends=1))
        if members:
            original_run=wrapped.run
            async def select_member(system,prompt,request_id,**kwargs):
                effective=json.loads(json.loads(prompt)[-1]['content'])
                candidates=effective['member_candidates'];assert candidates
                harness.text=harness.text.replace('$candidate',candidates[0]['member_ref'])
                return await original_run(system,prompt,request_id,**kwargs)
            wrapped.run=select_member
            e=await inbound();gen,req=await start(e)
            await complete(e,req,response(req,mention_ref='$candidate'));await finish(gen)
            assert e.bot.sent[0]['message'][0]['type']=='at'
            report.append(dict(case='typed_at_same_chain_ticket_and_permission',sends=1))
            # Stop while preparing the per-part permission: final gate still refuses.
            e=await inbound();gen,req=await start(e);permit=client.permit
            async def stop_permit(*args,**kw):
                result=await permit(*args,**kw);await control();await wake();return result
            client.permit=stop_permit
            await complete(e,req,response(req,mention_ref='$candidate'));await finish(gen)
            client.permit=permit;wrapped.run=original_run
            assert not e.bot.sent
            assert router.tasks.delivery(e.get_extra('qq_delivery_key'))['state']=='failed'
            report.append(dict(case='typed_at_permission_race_no_send',sends=0))
        # Router-local waiting cancels before any provider submission; owners survive.
        e=await inbound();before=harness.attempts
        local_owner=None
        if participation=='mentions':local_owner=await router.coordinator.acquire(e.unified_msg_origin)
        elif hasattr(router.group_turns,'current'):router.group_turns.current=object()
        else:router.group_turns.active=True
        gen=router.on_group(e);waiting=asyncio.create_task(anext(gen));await asyncio.sleep(.03)
        assert not waiting.done()
        await control();await wake()
        try:await asyncio.wait_for(waiting,1);raise AssertionError('invalidated local queue yielded')
        except StopAsyncIteration:pass
        if local_owner:local_owner.release()
        elif hasattr(router.group_turns,'current'):router.group_turns.current=None
        else:router.group_turns.active=False
        assert harness.attempts==before and not e.bot.sent
        if participation=='mentions':assert e.is_stopped()
        report.append(dict(case='router_local_wait_no_provider_no_global_cancel',sends=0))
        if participation=='free':
            e=await inbound('合成闲聊',False);gen=router.on_group(e);waiting=asyncio.create_task(anext(gen))
            await asyncio.sleep(.03);await control();await wake()
            try:await asyncio.wait_for(waiting,1);raise AssertionError('invalidated batch yielded')
            except StopAsyncIteration:pass
            assert not e.bot.sent and harness.attempts==before
            report.append(dict(case='ambient_batch_discard_no_backlog',sends=0))
        # A request yielded by router but not yet submitted to provider is blocked.
        e=await inbound();gen,req=await start(e);before=harness.attempts
        await control();await wake();await complete(e,req,response(req));await finish(gen)
        assert harness.attempts==before and not e.bot.sent
        report.append(dict(case='pre_HTTP_invalidated_no_generation',sends=0))
        # Exercise actual decorating/respond chain for local input/error/reset notices.
        for question in ['', 'https://example.com/' if participation=='mentions' else '合成'*2100, '重置会话' if participation=='mentions' else '重置本群上下文']:
            e=await inbound(question);gen=router.on_group(e)
            try:
                item=await anext(gen)
                if hasattr(item,'chain'):
                    e.set_result(item)
                    handler=SimpleNamespace(handler_module_path='lap43',handler_name='deliver_reply',handler=router.deliver_reply)
                    from astrbot.core.star.star_handler import EventType
                    with patch.object(decorate_module.star_handlers_registry,'get_handlers_by_event_type',side_effect=lambda kind,**kw:[handler] if kind==EventType.OnDecoratingResultEvent else []),patch.dict(decorate_module.star_map,{'lap43':SimpleNamespace(name='lap43')}):
                        async for _ in decorate.process(e):pass
                        await respond.process(e)
                    await finish(gen)
                else:
                    # Free reset wording is handled by existing exact command below;
                    # this synthetic normal request is closed without submitting.
                    await gen.aclose()
            except StopAsyncIteration:pass
            assert all('qqbot_output_ticket' not in json.dumps(row) for row in e.bot.sent)
            report.append(dict(case='local_input_notice_'+str(len(question)),sends=len(e.bot.sent)))
        # Actual provider HTTP can sit inside ModelQueue. Silence must not cancel it.
        entered=asyncio.Event();release=asyncio.Event();original_wrapped=wrapped.run
        async def hold_worker(system,prompt,request_id,*args,**kw):
            if request_id=='lap43-queue-holder':
                from qqbot_gateway.backends import BackendResult
                entered.set();await release.wait();return BackendResult('合成占位',generation_performed=False)
            return await original_wrapped(system,prompt,request_id,*args,**kw)
        wrapped.run=hold_worker
        blocker=asyncio.create_task(queue.submit('', '[]', 'lap43-queue-holder'))
        await asyncio.wait_for(entered.wait(),2)
        e=await inbound();gen,req=await start(e);before=harness.attempts
        submitted=asyncio.create_task(complete(e,req,response(req)))
        deadline=time.monotonic()+3
        while queue.queue.qsize()==0 and time.monotonic()<deadline:await asyncio.sleep(.01)
        assert queue.queue.qsize()==1
        queued_job=queue.queue._queue[0]
        await control();await wake();await asyncio.sleep(.02)
        assert not submitted.done() and not queued_job.cancelled.is_set() and not queued_job.future.cancelled()
        release.set();await blocker;await submitted;await finish(gen);wrapped.run=original_wrapped
        assert harness.attempts==before+1 and not e.bot.sent
        assert queue.state not in ('REMOTE_RESULT_UNKNOWN','CLEANUP_FAILED')
        report.append(dict(case='submitted_HTTP_internal_queue_natural_completion',sends=0))
        for blocked_state in ('REMOTE_RESULT_UNKNOWN','CLEANUP_FAILED'):
            previous=queue.state;queue.state=blocked_state
            await control();await wake()
            assert queue.state==blocked_state
            queue.state=previous
        report.append(dict(case='wake_never_clears_real_blocking_state',sends=0))
        # Unknown remains unknown across wake; never retry or clear persistent guards.
        e=await inbound(ack='missing');gen,req=await start(e)
        await complete(e,req,response(req));await finish(gen)
        assert router.tasks.delivery(e.get_extra('qq_delivery_key'))['state']=='unknown'
        await control();await wake()
        assert router.tasks.delivery(e.get_extra('qq_delivery_key'))['state']=='unknown'
        report.append(dict(case='true_ACK_unknown_preserved',sends=1))
        # Other group remains usable even with A muted/unknown.
        await control();e=await inbound(group='444');await execute(e);assert len(e.bot.sent)==1
        await wake()
        report.append(dict(case='other_group_isolated',sends=1))
        # Missing mirror is fail closed for every branch; no speculative default.
        e=await inbound();(root/'state/gate-connection.json').unlink()
        gen=router.on_group(e)
        try:await anext(gen);raise AssertionError('missing mirror admitted')
        except StopAsyncIteration:pass
        connect()
        report.append(dict(case='missing_mirror_closed',sends=0))
        for malformed in [[],dict(v=1,boot_id=gate.silence.boot_id,enabled=True,groups={})]:
            e=await inbound();data=json.loads((root/'state/gate-connection.json').read_text());data['silence']=malformed
            (root/'state/gate-connection.json').write_text(json.dumps(data),encoding='utf-8')
            gen=router.on_group(e)
            try:await anext(gen);raise AssertionError('malformed mirror admitted')
            except StopAsyncIteration:pass
            assert not e.bot.sent;connect()
        e=await inbound();assert router.connection()==connection
        report.append(dict(case='malformed_mirror_closed_then_recovers',sends=0))
        return dict(backend=backend,mode=mode,participation=participation,attention=attention,memory=memory,memes=memes,members=members,
                    cases=report,material_kind=material_kind,real_model_calls=0,real_qq_calls=0,real_run_agent=True,actual_runner=True,original_event_ACK=True)
    finally:
        router.tasks.close();gate.store.close();await provider.client.close();await server.cleanup();await private_server.cleanup()
