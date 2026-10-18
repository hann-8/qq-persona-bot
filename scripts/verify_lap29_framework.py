"""LAP-29 actual AstrBot/provider/run_agent and members/typed-mention fixture integration.
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


async def verify(root,backend,mode,participation="free",attention=False,memes=False,web_enabled=False,memory_enabled=False):
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
    from qqbot_gateway.web_retrieval import WebRunner,Retriever,Retrieval
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
            await gate._outgoing(frames(dict(action='send_group_msg',params=kwargs,echo=echo)),down,pending)
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
    settings['bot']['qq']='222';settings['access'].update(allowed_groups=['111','444'],admin_users=['333'],blocked_users=['999'])
    settings['llm']['backend']=backend
    settings['vision']=dict(enabled=False,input_reserve_tokens=4096)
    settings['members']=MEMBER_DEFAULTS|dict(enabled=True,mentions_enabled=True)
    settings['memory']=dict(enabled=memory_enabled,learning_enabled=False)
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
        import psutil,time
        (root/'state/gate-connection.json').write_text(json.dumps(dict(id=value,connected=True,online=online,pid=os.getpid(),created=psutil.Process().create_time(),updated=time.time())),encoding='utf-8')
    connect()
    os.environ['QQBOT_INSTANCE_ID']='lap20-synthetic'
    with patch.dict(os.environ,{'QQBOT_ROOT':str(root)}),patch('qqbot_gateway.members.suspend_unverified',side_effect=lambda settings:settings['members']),patch('qqbot_gateway.vision.context_token',return_value='c'*64):
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
    class OfflineReader(Retriever):
        def __init__(self):super().__init__(settings['web']);self.questions=[]
        async def retrieve(self,q):
            self.questions.append(q)
            assert q=='肥鱼，请看 https://example.com/ 并叫自造乙'
            if not web_enabled:return Retrieval('disabled',notice='网页读取尚未开启。')
            return Retrieval('read',[dict(url='https://example.com/',title='合成公开页',text='public synthetic material '*50,status='body')])
    reader=OfflineReader()
    wrapped=WebRunner(harness,reader,InputBudget(),settings['output'])
    queue=ModelQueue(wrapped);token=secrets.token_urlsafe(32)
    wrapped.memes=router.memes
    gate=OneBotGate(GateConfig('222',frozenset({'111','444'}),frozenset({'333'}),'a'*40,'b'*40,root/'state/gate.db',participation_mode=participation,members_enabled=True,members_config=settings['members'],media_catalog=router.memes if memes else None,blocked_users=frozenset({'999'}),attention_enabled=attention))
    gate.context_token='c'*64;gate.connected=True;gate.online=True;gate.connection_id=connection
    observation={'count':3,'age':0,'offset':0}
    gate.members.clock=lambda:time.monotonic()+observation['offset']
    gate.members.observe=lambda data:dict(count=observation['count'],age=observation['age'],source='synthetic-count')
    queries=[]
    async def member_rpc(action,params):
        queries.append(action)
        if action=='get_group_info':return dict(member_count=observation['count'])
        return [dict(group_id=111,user_id=uid,card=name,nickname=name) for uid,name in ((333,'自造甲'),(444,'自造乙'),(222,'自造bot'))]
    gate.member_rpc=member_rpc
    private_server=web.AppRunner(gate.application(),access_log=None);await private_server.setup()
    private_site=web.TCPSite(private_server,'127.0.0.1',0);await private_site.start()
    private_port=private_site._server.sockets[0].getsockname()[1]
    client=MemberClient(f'http://127.0.0.1:{private_port}/context/members','c'*64)
    router.member_client=client;router.delivery.members=client
    v2=dict(mode=participation,config_version=__import__('qqbot_gateway.reply_plan',fromlist=['digest']).digest(router.persona_id),aliases=router.participation['attention']['aliases'],mentions_enabled=True,memory_enabled=memory_enabled)
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
    async def member_event(text='请叫自造乙',ack='ok'):
        e=event(True,text=text,ack=ack)
        raw=dict(post_type='message',message_type='group',self_id=222,user_id=333,group_id=111,
            message_id=e.message_obj.message_id,sender={'user_id':333,'nickname':'自造甲'},
            message=[dict(type='at',data={'qq':'222'}),dict(type='text',data={'text':text})])
        class Capture:
            def __init__(self):self.rows=[]
            async def send_json(self,value):self.rows.append(value)
        async def frames():yield SimpleNamespace(type=WSMsgType.TEXT,data=json.dumps(raw))
        up=Capture();await gate._incoming(frames(),up,set());assert len(up.rows)==1
        e.message_obj.raw_message=up.rows[0]
        assert up.rows[0].get('qqbot_member_cap')
        return e

    expire_during=False;effective_inputs=[]
    native_run=harness.runner.run
    async def run(system,prompt,request_id):
        source=json.JSONDecoder().raw_decode(json.loads(prompt)[-1]['content'])[0]
        effective_inputs.append(copy.deepcopy(source))
        raw=json.loads(harness.text)
        if raw.get('mention',{}):
            if raw['mention']['member_ref']=='$candidate':
                candidates=source['member_candidates']
                raw['mention']=dict(member_ref=candidates[-1]['member_ref'],bubble_index=0) if candidates else None
        harness.text=json.dumps(raw,ensure_ascii=False)
        if expire_during:observation['offset']+=61
        return await native_run(system,prompt,request_id)
    harness.run=run

    async def turn(case,ack='ok',expire=False,bad=False,count=3,age=0,tamper=None,mention=True):
        nonlocal expire_during
        expire_during=expire;observation.update(count=count,age=age)
        gate.members.invalidate('111')
        e=await member_event('肥鱼，请看 https://example.com/ 并叫自造乙' if web_enabled else '请叫自造乙',ack)
        generator=router.on_group(e);req=await anext(generator)
        header=e.get_extra('qq_group_request')
        assert header['version']==2 and len(header['resource_caps'])==1
        assert json.loads(req.prompt)['member_candidates']==[]
        text=json.dumps(dict(qqbot_turn_reply=2,decision='speak',kind='answer' if web_enabled else 'chat',bubbles=['一起聊吧'],
            meme_id=meme_id if memes and not web_enabled else None,response_to_seq=1,
            mention=dict(member_ref='all' if bad else '$candidate',bubble_index=0) if mention else None,memory_proposals=[]),ensure_ascii=False)
        before=harness.attempts;start=len(queries)
        await complete(e,req,text,tamper);await finish(generator)
        assert harness.attempts==before+1,(case,e.get_extra('qq_group_metadata'))
        meta=e.get_extra('qq_group_metadata');assert meta and not e.get_extra('qq_group_invalid'),(case,meta)
        assert len(e.bot.sent)==(2 if memes and not web_enabled else 1),(case,e.bot.sent)
        applied=bool(mention and not bad and not expire and count==3 and age==0)
        self_parts=e.bot.sent[0]['message']
        assert (self_parts[0]['type']=='at')==applied,(case,self_parts,meta)
        assert sum(p['type']=='at' for p in self_parts)<=1
        if applied:assert self_parts[0]['data']['qq']=='444'
        if count in (50,51,None) or age is None:assert 'get_group_member_list' not in queries[start:]
        rows=router.tasks.parts(e.get_extra('qq_delivery_key'))
        if ack=='ok':assert all(s=='sent' for _,s,_ in rows),(case,rows)
        else:assert rows[0][1]=='unknown' and len(e.bot.sent)==1,(case,rows)
        if applied or expire:
            recorded=router.tasks.db.execute('SELECT applied FROM mention_receipt WHERE message_key=?',(e.get_extra('qq_delivery_key'),)).fetchall()
            assert recorded==[(None if ack!='ok' else int(applied),)],(case,recorded)
        assert router.group_turns.current is None if participation=='free' else True
        material=effective_inputs[-1]
        assert len(material['member_candidates'])<=8
        assert header['resource_caps'][0] not in json.dumps(material)
        assert not any('user_id' in json.dumps(c) for c in material['member_candidates'])
        report.append(dict(case=case,generations=1,sends=len(e.bot.sent),mention_applied=applied,part_states=[s for _,s,_ in rows]))
        return e

    try:
        await turn('same_text_chain_gate_ACK')
        await turn('count_expires_during_generation_same_attempt_strip',expire=True)
        await turn('invalid_all_aux_preserves_text',bad=True)
        for count in (50,51,None):await turn('count_'+str(count)+'_zero_list',count=count)
        await turn('unknown_observation_age_zero_list',age=None)
        await turn('ordinary_direct_text_no_automatic_mention',mention=False)
        if not memes and not web_enabled:
            await turn('unknown_ACK_no_retry',ack='missing')
            await turn('transport_error_no_retry',ack='error')
            await turn('new_message_after_unknown')
            e=await member_event();generator=router.on_group(e);req=await anext(generator)
            text=json.dumps(dict(qqbot_turn_reply=2,decision='speak',kind='chat',bubbles=['一起聊吧'],meme_id=None,
                response_to_seq=1,mention=dict(member_ref='$candidate',bubble_index=0),memory_proposals=[]),ensure_ascii=False)
            before=harness.attempts
            await complete(e,req,text,lambda raw:raw.qqbot_group_plan.__setitem__('plan_hash','f'*64));await finish(generator)
            assert harness.attempts==before+1 and not e.bot.sent and e.get_extra('qq_group_invalid')
            report.append(dict(case='tampered_metadata_no_bypass_or_extra_notice',generations=1,sends=0))
        if participation=='mentions':
            histories=[json.loads(c.history) for c in manager.items.values()]
            assert 'resource_caps' not in str(histories) and 'member_candidates' not in str(histories)
            assert 'qqbot_turn_reply' not in str(histories)
        else:assert manager.calls==0
        if memory_enabled:
            assert any(s['memory'] and s['memory']['records'] for s in effective_inputs)
            assert not router.memory.live
        return dict(backend=backend,mode=mode,participation=participation,attention=attention,web=web_enabled,memes=memes,
            memory_enabled=memory_enabled,cases=report,real_model_calls=0,real_qq_calls=0,real_run_agent=True,actual_runner=True,
            private_gate_http=True,actual_provider=True,original_event_ACK=True,production_eligible=False)
    finally:
        router.tasks.close();await provider.client.close();await server.cleanup();await private_server.cleanup()
