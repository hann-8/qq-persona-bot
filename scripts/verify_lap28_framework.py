"""LAP-28 actual AstrBot/provider/run_agent and native-runner fixture integration.
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


async def verify(root,backend,mode,participation="free",attention=True,memes=False,web_enabled=False):
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
    from qqbot_gateway.vision import MaterialClient
    from qqbot_gateway.onebot_gate import OneBotGate
    from qqbot_gateway.config import GateConfig
    import io
    from PIL import Image
    from aiohttp import WSMsgType
    raw_image=io.BytesIO();Image.new('RGB',(20,10),'red').save(raw_image,format='PNG')
    fetched=[]
    async def fetch(url):fetched.append(url);return raw_image.getvalue()
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
    settings['bot']['qq']='222';settings['access'].update(allowed_groups=['111','444'],admin_users=['333'],blocked_users=['999'])
    settings['llm']['backend']=backend
    settings['vision']=dict(enabled=True,input_reserve_tokens=4096)
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
    with patch.dict(os.environ,{'QQBOT_ROOT':str(root)}),patch('qqbot_gateway.vision.require_production',return_value=True):
        router=QQRouter(SimpleNamespace(conversation_manager=manager))
    router.delivery.timeout=.03
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
    class OfflineReader(Retriever):
        def __init__(self):super().__init__(settings['web']);self.questions=[]
        async def retrieve(self,q):
            self.questions.append(q)
            assert q=='肥鱼，请看 https://example.com/'
            if not web_enabled:return Retrieval('disabled',notice='网页读取尚未开启。')
            return Retrieval('read',[dict(url='https://example.com/',title='合成公开页',text='public synthetic material '*50,status='body')])
    reader=OfflineReader()
    wrapped=WebRunner(harness,reader,InputBudget(),settings['output'])
    queue=ModelQueue(wrapped);token=secrets.token_urlsafe(32)
    wrapped.memes=router.memes
    gate=OneBotGate(GateConfig('222',frozenset({'111','444'}),frozenset({'333'}),'a'*40,'b'*40,root/'state/gate.db',participation_mode=participation,vision_enabled=True,blocked_users=frozenset({'999'}),attention_enabled=attention))
    gate.context_token='c'*64;gate.connected=True;gate.online=True;gate.connection_id=connection
    gate.materials.fetch=fetch
    private_server=web.AppRunner(gate.application(),access_log=None);await private_server.setup()
    private_site=web.TCPSite(private_server,'127.0.0.1',0);await private_site.start()
    private_port=private_site._server.sockets[0].getsockname()[1]
    client=MaterialClient(f'http://127.0.0.1:{private_port}/context/vision/resolve','c'*64,4096)
    v2=dict(mode=participation,config_version=__import__('qqbot_gateway.reply_plan',fromlist=['digest']).digest(router.persona_id),aliases=router.participation['attention']['aliases'])
    server=web.AppRunner(application(queue,token,output=settings['output'],memes=router.memes,v2=v2,materials=client),access_log=None)
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
    async def image_event(text='合成问题',mention=True,first='https://gchat.qpic.cn/synthetic',ack='ok',reuse=None):
        e=event(mention,text=text,ack=ack)
        source=dict(post_type='message',message_type='group',self_id=222,user_id=333,group_id=111,
            message_id=e.message_obj.message_id,sender={'user_id':333,'nickname':'合成显示名'},
            message=([dict(type='at',data={'qq':'222'})] if mention else [])+[dict(type='text',data={'text':text}),
                     dict(type='image',data=dict(url=first,filePath='C:/private/never-read')),
                     dict(type='image',data=dict(url='https://multimedia.nt.qq.com.cn/never-second'))],raw_message='private raw')
        class Upstream:
            def __init__(self):self.rows=[]
            async def send_json(self,row):self.rows.append(row)
            async def send_str(self,row):self.rows.append(json.loads(row))
        upstream=Upstream()
        async def frames():yield SimpleNamespace(type=WSMsgType.TEXT,data=json.dumps(source))
        await gate._incoming(frames(),upstream,set())
        if not upstream.rows:return e
        raw=upstream.rows[0]
        assert 'gchat.qpic' not in json.dumps(raw) and 'filePath' not in json.dumps(raw)
        if reuse:raw['qqbot_image']=reuse
        e.message_obj.raw_message=raw
        e.message_obj.message=[At(qq=x['data']['qq']) if x['type']=='at' else Plain(text=x['data']['text']) for x in raw['message']]
        e.message_str=''.join(c.text for c in e.message_obj.message if isinstance(c,Plain))
        return e

    def output():return json.dumps(dict(qqbot_turn_reply=2,decision='speak',kind='answer',bubbles=['合成图片答复'],
        meme_id=None,response_to_seq=1,mention=None,memory_proposals=[]),ensure_ascii=False)

    async def turn(e,case,generations=1):
        generator=router.on_group(e);req=await anext(generator)
        header=e.get_extra('qq_group_request');source=json.loads(req.prompt)
        assert header['version']==2 and len(header['resource_caps'])==1 and len(source['images'])==1
        assert header['resource_caps'][0] not in req.prompt and 'gchat.qpic' not in req.prompt
        assert not req.image_urls and not req.extra_user_content_parts
        before=harness.attempts
        await complete(e,req,output());await finish(generator)
        assert harness.attempts==before+generations,(case,harness.attempts,before,e.get_extra('qq_group_invalid'),e.bot.sent)
        assert e.get_extra('qq_group_metadata') and not e.get_extra('qq_group_invalid'),(case,e.get_extra('qq_group_metadata'))
        assert len(e.bot.sent)==(1 if header['must_reply'] or generations else 0),(case,e.bot.sent)
        assert all(x['message'][0]['type']=='text' for x in e.bot.sent)
        assert router.group_turns.current is None if participation=='free' else True
        if generations:
            native=json.loads(harness.script.with_suffix('.input').read_text(encoding='utf-8')) if backend=='codebuddy_cli' else native_inputs[-1]
            if backend=='codebuddy_cli':
                content=native['message']['content'];assert [x['type'] for x in content]==['text','image']
                encoded=content[1]['source']['data'];text=content[0]['text']
            else:
                assert len(native['messages'][-1]['images'])==1 and 'tools' not in native
                encoded=native['messages'][-1]['images'][0];text=native['messages'][-1]['content']
            import base64,hashlib
            descriptor=e.get_extra('qq_group_metadata')['manifest']['images'][0]
            assert hashlib.sha256(base64.b64decode(encoded)).hexdigest()==descriptor['sha256']
            assert header['resource_caps'][0] not in json.dumps(native) and 'gchat.qpic' not in text and 'never-second' not in text
            assert len(json.dumps(native).encode())<=2*1024*1024
        report.append(dict(case=case,generations=generations,sends=len(e.bot.sent)))
        return header

    try:
        e=await image_event(text='肥鱼，请看 https://example.com/' if web_enabled else '合成问题')
        original=copy.deepcopy(e.message_obj.raw_message['qqbot_image'])
        await turn(e,'current_first_image_native_once')
        assert fetched==['https://gchat.qpic.cn/synthetic']
        if web_enabled:assert reader.questions==['肥鱼，请看 https://example.com/']
        if participation=='mentions':
            histories=[json.loads(c.history) for c in manager.items.values()]
            assert any(h and h[-1]['role']=='assistant' and '合成图片答复' in str(h[-1]['content']) for h in histories),histories
            assert 'resource_caps' not in str(histories) and 'image_ref' not in str(histories) and 'qqbot_turn_reply' not in str(histories)
        else:assert manager.calls==0
        plain=event(True,text='合成纯文字续问')
        generator=router.on_group(plain);req=await anext(generator)
        assert plain.get_extra('qq_group_request')['version']==2
        assert plain.get_extra('qq_group_request')['resource_caps']==[] and json.loads(req.prompt)['images']==[]
        before=harness.attempts
        await complete(plain,req,output());await finish(generator)
        assert harness.attempts==before+1 and len(plain.bot.sent)==1
        if backend=='ollama_ssh':assert all('images' not in m for m in native_inputs[-1]['messages'])
        else:assert '"type":"image"' not in harness.script.with_suffix('.input').read_text(encoding='utf-8')
        report.append(dict(case='vision_effective_text_only_v2_no_image',generations=1,sends=1))
        e=await image_event(reuse=original)
        await turn(e,'replay_local_notice_no_generation',0)
        assert len(fetched)==1
        client.reserve=100000
        e=await image_event()
        await turn(e,'text_visual_reserve_rejected_before_native',0)
        assert len(fetched)==2
        client.reserve=4096
        if participation=='free':
            router.group_turns.reset('111')
            e=await image_event(mention=False,reuse=original)
            await turn(e,'ambient_unavailable_silent_no_generation',0)
            router.group_turns.reset('111')
            held=event(True,text='持有dispatcher');held_gen=router.on_group(held);held_req=await anext(held_gen)
            carrier=await image_event(mention=False,text='普通图片甲',first='https://gchat.qpic.cn/carrier')
            pending_gen=router.on_group(carrier);waiting=asyncio.create_task(anext(pending_gen))
            for _ in range(100):
                if router.group_turns.pending:break
                await asyncio.sleep(.01)
            assert router.group_turns.pending
            newest=await image_event(mention=False,text='普通图片乙',first='https://gchat.qpic.cn/newest')
            newest_image=copy.deepcopy(newest.message_obj.raw_message['qqbot_image'])
            merged_gen=router.on_group(newest)
            try:await anext(merged_gen)
            except StopAsyncIteration:pass
            else:raise AssertionError('Ambient image did not merge')
            assert router.group_turns.pending[0].image==newest_image
            await complete(held,held_req,output());await finish(held_gen)
            merged_req=await asyncio.wait_for(waiting,2)
            assert carrier.get_extra('qq_group_request')['resource_caps']==[newest_image['cap']]
            before=harness.attempts
            await complete(carrier,merged_req,output());await finish(pending_gen)
            assert harness.attempts==before+1 and fetched[-1]=='https://gchat.qpic.cn/newest'
            assert 'https://gchat.qpic.cn/carrier' not in fetched
            report.append(dict(case='ambient_merge_target_and_cap_together',generations=2,sends=len(held.bot.sent)+len(carrier.bot.sent)))
        return dict(backend=backend,mode=mode,participation=participation,attention=attention,web=web_enabled,
            cases=report,real_model_calls=0,real_qq_calls=0,real_run_agent=True,actual_runner=True,
            private_gate_http=True,actual_provider=True,original_event_ACK=True,production_eligible=False)
    finally:
        router.tasks.close();await provider.client.close();await server.cleanup();await private_server.cleanup()
