"""LAP-06 actual AstrBot/provider/run_agent and native-runner fixture integration.
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
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
os.environ['ASTRBOT_DISABLE_METRICS']='1'


async def verify(root,backend,mode,participation="free",attention=True,memes=True,web_enabled=True,memory_enabled=True,body_reader=False):
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
    from qqbot_gateway.onebot_gate import OneBotGate
    from qqbot_gateway.config import GateConfig
    from aiohttp import WSMsgType
    from qqbot_gateway.model_gateway import application,ModelQueue
    from qqbot_gateway.task_store import TaskStore
    from qqbot_gateway.web_retrieval import WebRunner,Retriever,Retrieval
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
            return {'message_id':10000+serial*10+len(self.sent)}
    settings=yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
    settings['participation']['silence']={'enabled':True}  # legacy-disabled regression
    settings['bot']['qq']='222';settings['access'].update(allowed_groups=['111','444'],admin_users=['333'],blocked_users=['999'])
    settings['llm']['backend']=backend
    settings['vision']=dict(enabled=False,input_reserve_tokens=4096)
    settings['bilibili']={'enabled':True}
    settings['memory']=dict(enabled=memory_enabled,learning_enabled=False)
    settings['chat']['user_cooldown_seconds']=0
    settings['participation'].update(mode=participation,debounce_seconds=.5,max_batch_wait_seconds=2)
    settings['participation']['attention']['enabled']=attention
    settings['memes']['enabled']=memes
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
        import psutil,time
        (root/'state/gate-connection.json').write_text(json.dumps(dict(id=value,connected=True,online=online,pid=os.getpid(),created=psutil.Process().create_time(),updated=time.time())),encoding='utf-8')
    connect()
    os.environ['QQBOT_INSTANCE_ID']='lap20-synthetic'
    with patch.dict(os.environ,{'QQBOT_ROOT':str(root)}),patch('qqbot_gateway.vision.context_token',return_value='c'*64):
        router=QQRouter(SimpleNamespace(conversation_manager=manager))
    router.delivery.timeout=.03
    if memory_enabled:
        info=router.memory.manage('111','inspect')
        router.memory.manage('111','add',user='333',kind='preference',slot='likes',fact='合成茶',expected=info['digest'])
    harness=Harness(root,backend)
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
    from tests.test_bilibili import HTTP,BVID,OTHER,subtitle_body
    HTTP.calls=[];HTTP.delay=0;HTTP.cancelled=0;HTTP.need=False;HTTP.code=0;HTTP.body=subtitle_body()
    reader=Retriever(settings['web'],bilibili=settings['bilibili'],http_factory=HTTP,root=root)
    budget=InputBudget(native_profile=harness.runner.profile) if backend=='ollama_ssh' else InputBudget()
    wrapped=WebRunner(harness,reader,budget,settings['output'])
    queue=ModelQueue(wrapped);token=secrets.token_urlsafe(32)
    wrapped.memes=router.memes
    gate=OneBotGate(GateConfig('222',frozenset({'111','444'}),frozenset({'333'}),'a'*40,'b'*40,root/'state/gate.db',participation_mode=participation,vision_enabled=False,blocked_users=frozenset({'999'}),attention_enabled=attention,silence_enabled=True),root)
    gate.context_token='c'*64;gate.connected=True;gate.online=True;gate.connection_id=connection;gate.publish_connection()
    private_server=web.AppRunner(gate.application(),access_log=None);await private_server.setup()
    private_site=web.TCPSite(private_server,'127.0.0.1',0);await private_site.start()
    v2=dict(mode=participation,config_version=__import__('qqbot_gateway.reply_plan',fromlist=['digest']).digest(router.persona_id),aliases=router.participation['attention']['aliases'],memory_enabled=memory_enabled)
    server=web.AppRunner(application(queue,token,budget=budget,output=settings['output'],memes=router.memes,v2=v2),access_log=None)
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
        from astrbot.core.pipeline.context_utils import call_event_hook
        from astrbot.core.star.star_handler import EventType
        before_handler=SimpleNamespace(handler_module_path='lap06',handler_name='before_provider',handler=router.before_provider)
        with patch.object(decorate_module.star_handlers_registry,'get_handlers_by_event_type',return_value=[before_handler]),patch.dict(decorate_module.star_map,{'lap06':SimpleNamespace(name='lap06')}):
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

    report=[]
    async def admitted(text,mention=True,sender='333',ack='ok'):
        e=event(mention,sender=sender,text=text,ack=ack)
        raw=dict(post_type='message',message_type='group',self_id=222,user_id=int(sender),group_id=111,
                 message_id=e.message_obj.message_id,sender={'user_id':int(sender),'nickname':'合成'},
                 message=([dict(type='at',data={'qq':'222'})] if mention else [])+[dict(type='text',data={'text':text})],raw_message='')
        class Upstream:
            def __init__(self):self.rows=[]
            async def send_json(self,row):self.rows.append(row)
            async def send_str(self,row):self.rows.append(json.loads(row))
        upstream=Upstream()
        async def frames():yield SimpleNamespace(type=WSMsgType.TEXT,data=json.dumps(raw))
        await gate._incoming(frames(),upstream,set())
        if not upstream.rows:return None
        e.message_obj.raw_message=upstream.rows[0]
        return e

    def output(body='正文事实：实验先降温再加压。'):return json.dumps(dict(qqbot_turn_reply=2,decision='speak',kind='answer',bubbles=[body],
        meme_id=None,response_to_seq=None,mention=None,memory_proposals=[]),ensure_ascii=False)

    async def turn(text,case,mention=True,generations=1,evidence=True,ack='ok',reset=True):
        if reset:router.group_turns.reset('111')
        e=await admitted(text,mention=mention,ack=ack);assert e is not None,case
        generator=router.on_group(e);req=await anext(generator)
        before=harness.attempts;before_http=len(HTTP.calls)
        await complete(e,req,output('普通文字回应，不总结视频。' if case=='free_bare_no_fetch' else '正文事实：实验先降温再加压。'));await finish(generator)
        assert harness.attempts==before+generations,(case,harness.attempts,before,e.bot.sent)
        metadata=e.get_extra('qq_group_metadata')
        assert metadata and not e.get_extra('qq_group_invalid'),(case,metadata)
        sources=metadata['manifest'].get('web',[])
        assert bool(sources)==evidence,(case,sources)
        if evidence:
            assert sources[0]['coverage'] in ('full','excerpt')
            native=json.loads(harness.script.with_suffix('.input').read_text(encoding='utf-8')) if backend=='codebuddy_cli' else native_inputs[-1]
            raw=json.dumps(native,ensure_ascii=False)
            assert '先降温再加压' in raw and '正文优先于标题' in raw and 'auth_key' not in raw and 'SESSDATA' not in raw
            assert '来源：' in str(e.bot.sent) and '字幕' in str(e.bot.sent)
        if case=='cached_material_independent_generation':assert len(HTTP.calls)==before_http
        if not evidence and case=='free_bare_no_fetch':assert len(HTTP.calls)==before_http
        assert len(e.bot.sent)<=1,(case,e.bot.sent)
        if ack=='missing':
            assert router.tasks.delivery(e.get_extra('qq_delivery_key'))['state']=='unknown'
            assert len(e.bot.sent)==1
        if participation=='mentions':
            histories=str([c.history for c in manager.items.values()])
            assert 'auth_key' not in histories and 'time_ranges' not in histories and 'subtitle_url' not in histories
        report.append(dict(case=case,generations=generations,sends=len(e.bot.sent),evidence=evidence,http_calls=len(HTTP.calls)-before_http))

    try:
        await turn(BVID,'mention_bare_once')
        await turn('概括 '+BVID+' 的实验步骤','cached_material_independent_generation',reset=False)
        await turn('总结 https://b23.tv/abc','short_p2_once')
        if participation=='free':
            await turn('总结 '+BVID,'free_explicit_once',mention=False)
            await turn(BVID,'free_bare_no_fetch',mention=False,evidence=False)
        HTTP.need=True
        await turn('总结 '+BVID,'login_notice_zero',generations=0,evidence=False)
        HTTP.need=False
        await turn('总结 '+BVID+' '+OTHER,'multiple_zero',generations=0,evidence=False)
        HTTP.body=subtitle_body(True)
        await turn('总结 '+BVID,'excerpt_once')
        await turn('完整总结 '+BVID,'complete_budget_zero',generations=0,evidence=False)
        HTTP.body=subtitle_body()
        await turn(BVID,'unknown_ack_no_resend',ack='missing')
        n=len(HTTP.calls);before=harness.attempts
        assert await admitted('总结 '+BVID,sender='999') is None
        assert await admitted('肥鱼闭嘴',mention=False) is None
        assert await admitted('总结 '+BVID,mention=False) is None
        assert len(HTTP.calls)==n and harness.attempts==before
        report.append(dict(case='blacklist_and_silence_no_framework_or_fetch',generations=0,sends=0))
        await turn(BVID,'real_mention_restores_silence')
        return dict(backend=backend,mode=mode,participation=participation,cases=report,real_run_agent=True,actual_provider=True,
                    actual_runner=True,original_event_ACK=True,gate=True,memory=memory_enabled,memes=True,bilibili_only_v2=(mode=='single'),real_model_calls=0,real_qq_calls=0)
    finally:
        router.tasks.close();gate.store.close();await provider.client.close();await server.cleanup();await private_server.cleanup()


async def main():
    import time
    previous=Path.cwd();rows=[];started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='lap06-framework-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    for participation in ('mentions','free'):
                        root=Path(directory)/(backend+mode+participation);root.mkdir()
                        rows.append(await verify(root,backend,mode,participation,attention=(mode=='adaptive'),memory_enabled=(mode=='adaptive')))
        finally:os.chdir(previous)
    value=dict(passed=True,combinations=len(rows),cases=sum(len(r['cases']) for r in rows),elapsed_seconds=round(time.monotonic()-started,3),
               real_model_calls=0,real_qq_outputs=0,real_bot_operations=0,rows=rows)
    (ROOT/'reports/lap-06-framework-offline.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('LAP06_FRAMEWORK',value['combinations'],value['cases'],value['elapsed_seconds'])


if __name__=='__main__':asyncio.run(main())
