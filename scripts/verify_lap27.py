"""Independent LAP-27 verifier. Actual framework and two runners, fake transport.

Only this task's reports are written. No old verifier main, model/QQ or credentials.
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


async def verify(root,backend,mode,memes=False,web_enabled=True):
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
    settings['participation'].update(mode='free',debounce_seconds=.5,max_batch_wait_seconds=2)
    settings['participation']['attention']['enabled']=True
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
    with patch.dict(os.environ,{'QQBOT_ROOT':str(root)}):router=QQRouter(SimpleNamespace(conversation_manager=Manager()))
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
    v2=dict(mode='free',config_version=__import__('qqbot_gateway.reply_plan',fromlist=['digest']).digest(router.persona_id),aliases=router.participation['attention']['aliases'])
    server=web.AppRunner(application(queue,token,output=settings['output'],memes=router.memes,v2=v2),access_log=None)
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
        msg.raw_message=dict(qqbot_connection=connection,qqbot_at_ids=['222'] if mention else [])
        return AiocqhttpMessageEvent(text,msg,PlatformMetadata(name='aiocqhttp',description='offline',id='qqbot'),group,Bot(ack))

    async def finish(gen):
        try:await anext(gen)
        except StopAsyncIteration:pass

    async def complete(e,req,text,tamper=None):
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

    def output(decision='speak',response=None,**kwargs):
        return json.dumps(dict(qqbot_turn_reply=2,decision=decision,kind='chat',
            bubbles=[] if decision=='silent' else ['合成正文'],meme_id=None,
            response_to_seq=response,mention=None,memory_proposals=[])|kwargs,ensure_ascii=False)

    report=[]
    async def turn(e,expected,raw=None,tamper=None):
        gen=router.on_group(e);req=await anext(gen)
        header=e.get_extra('qq_group_request')
        assert header['addressing']==expected,(expected,header)
        assert header['version']==2 and 'qqbot_turn_reply' in req.system_prompt
        source=json.loads(req.prompt)
        # No raw QQ/group/mid identities or attachments in structured model source.
        import re
        assert source['images']==[] and all(re.fullmatch(r'bot|p_[a-f0-9]{16}',r['member_ref']) for r in source['messages'])
        assert all(set(r)=={'seq','member_ref','name','text','reply_seq','at_refs','age_ms','images'} for r in source['messages'])
        before=harness.attempts
        await complete(e,req,raw or output(response=source['target_seq']),tamper)
        await finish(gen)
        assert harness.attempts==before+1
        if not tamper:assert e.get_extra('qq_group_response')=='chatcmpl-'+e.get_extra('qq_router_trace')
        native=json.loads(harness.script.with_suffix('.input').read_text(encoding='utf-8')) if backend=='codebuddy_cli' else native_inputs[-1]['messages'][1:]
        assert native[-1]['role']=='user' and 'target_seq' in native[-1]['content']
        assert router.group_turns.current is None and not router.group_turns.pending
        report.append(dict(case=expected,generations=1,sends=len(e.bot.sent),original_ack=True))
        return source,header

    try:
        before=harness.attempts
        for mention in (False,True):
            e=event(mention,text='[非文本未解析]');e.message_obj.raw_message['qqbot_media']=True
            gen=router.on_group(e)
            try:await anext(gen)
            except StopAsyncIteration:pass
            else:raise AssertionError('unsupported media generated')
        assert before==harness.attempts
        report.append(dict(case='unsupported_media_zero_generation',generations=0,sends=1))
        # Real @, reliable name, second-person followup, omitted subject, ending.
        e=event(True);await turn(e,'mention');assert len(e.bot.sent)==1
        assert router.group_turns.state('111').focus['sender']=='333'
        e=event(text='你能解释一下吗');await turn(e,'focused_followup')
        e=event(text='再加一个例子');await turn(e,'focused_candidate')
        e=event(text='好，明白了');await turn(e,'focused_candidate',output('silent'))
        assert not e.bot.sent
        e=event(text='肥鱼');await turn(e,'direct_name')
        router.group_turns.reset('111')
        e=event(text='肥鱼，请看 https://example.com/')
        if web_enabled:
            await turn(e,'direct_name',output(kind='answer'))
            assert '来源：' in str(e.bot.sent)
            report[-1]['case']='direct_web_anchor_native_once'
        else:
            gen=router.on_group(e);req=await anext(gen);before=harness.attempts
            await complete(e,req,output());await finish(gen)
            assert harness.attempts==before and len(e.bot.sent)==1 and router.group_turns.state('111').focus is None
            report.append(dict(case='web_disabled_zero_generation',generations=0,sends=1))
        assert reader.questions==['肥鱼，请看 https://example.com/']
        if memes:
            router.group_turns.reset('111');e=event(True,text='给我发个开心的表情')
            await turn(e,'mention',output(bubbles=[],meme_id=meme_id))
            assert e.bot.sent and router.group_turns.state('111').focus is None
            assert 'image' in str(e.bot.sent)
            report[-1]['case']='controlled_image_only_ACK_no_focus'
            e=event(True);await turn(e,'mention')
        # Reply ID comes only from a real successful original-event text ACK.
        if not router.group_turns.state('111').ack:
            e=event(True);await turn(e,'mention')
        mid=router.group_turns.state('111').ack[-1]['mid']
        e=event(sender='555',text='补充说明一下');e.message_obj.raw_message['qqbot_reference']=mid
        await turn(e,'reply_bot');assert router.group_turns.state('111').focus['sender']=='555'
        # Ambient chooses another eligible sender, never the carrying event's sender.
        router.group_turns.reset('111')
        e=event(True,sender='555');src,_=await turn(e,'mention')
        chosen=src['target_seq'];e=event(sender='333',text='大家接着说')
        await turn(e,'ambient',output(response=chosen))
        # Another human intervened: no personal focus can be inferred.
        assert router.group_turns.state('111').focus is None or router.group_turns.state('111').focus['sender']!='333'
        # Unresolved reply / @other never upgrades a name or "you" to direct.
        router.group_turns.reset('111')
        e=event(text='肥鱼，解释一下');e.message_obj.raw_message['qqbot_at_ids']=['555']
        await turn(e,'ambient',output('silent'));assert not e.bot.sent
        e=event(text='肥鱼，解释一下');e.message_obj.raw_message['qqbot_reference']='unknown'
        await turn(e,'ambient',output('silent'))
        # Bad aux drops aux, preserves validated text; no future side effects.
        e=event(True);await turn(e,'mention',output(response=999,mention={'member_ref':'forged'},memory_proposals=[{'op':'danger'}]))
        assert len(e.bot.sent)==1 and router.group_turns.state('111').focus['sender']=='333'
        # Effective source trimmed by actual framework-added system, metadata verifies.
        router.group_turns.reset('111')
        for n in range(24):router.group_turns.observe('111','old',str(n),'old','旧材料'*80)
        e=event(True);gen=router.on_group(e);req=await anext(gen);req.system_prompt+='S'*5000
        before=harness.attempts;await complete(e,req,output());await finish(gen)
        assert harness.attempts==before+1 and len(e.bot.sent)==1
        meta=e.get_extra('qq_group_metadata');assert meta and not e.get_extra('qq_group_invalid')
        assert e.get_extra('qq_group_request')['target_seq'] in meta['manifest']['seqs']
        report.append(dict(case='effective_subset_framework_system',generations=1,sends=1))
        # Corrupt authenticated result identity fails closed; no focus from local notice.
        router.group_turns.reset('111')
        def corrupt(raw):raw.qqbot_group_plan['effective_digest']='f'*64
        e=event(True);await turn(e,'mention',tamper=corrupt)
        assert e.get_extra('qq_group_invalid') and router.group_turns.state('111').focus is None
        # Unknown, failed or image-only ACK cannot create a focus, and is not retried.
        for ack in ('missing','error','timeout'):
            router.group_turns.reset('111');e=event(True,ack=ack);await turn(e,'mention')
            assert router.group_turns.state('111').focus is None
        # Partial delivery uses only confirmed text parts with a verified fixed object.
        if mode=='adaptive':
            router.group_turns.reset('111');e=event(True)
            original=e.bot.send_group_msg
            async def partial(**kwargs):
                if e.bot.sent:raise ConnectionError('synthetic partial')
                return await original(**kwargs)
            e.bot.send_group_msg=partial
            await turn(e,'mention',output(bubbles=['第一段','第二段']))
            focus=router.group_turns.state('111').focus
            assert focus and len(focus['rows'])==1 and focus['sender']=='333'
        # Blacklist/private/foreign bot are rejected before window/provider generation.
        before=harness.attempts
        for e in (event(True,sender='999'),event(True,group='777')):
            gen=router.on_group(e)
            try:await anext(gen)
            except StopAsyncIteration:pass
            else:raise AssertionError('unauthorized event')
        assert before==harness.attempts
        # Two direct messages queued behind an active turn stay independent and FIFO;
        # frozen target survives over 60 optional rows while the first event holds ACK lease.
        router.group_turns.reset('111');first=event(True);g1=router.on_group(first);r1=await anext(g1)
        a=event(text='肥鱼，问题甲');ga=router.on_group(a);ta=asyncio.create_task(anext(ga));await asyncio.sleep(.03)
        b=event(True,text='问题乙');gb=router.on_group(b);tb=asyncio.create_task(anext(gb));await asyncio.sleep(.03)
        for n in range(80):router.group_turns.observe('111','noise',str(n),'noise','可选材料')
        assert not ta.done() and not tb.done()
        await complete(first,r1,output());assert not tb.done();await finish(g1)
        rb=await asyncio.wait_for(tb,2);assert not ta.done()
        source=json.loads(rb.prompt);assert next(r['text'] for r in source['messages'] if r['seq']==source['target_seq'])=='问题乙'
        await complete(b,rb,output());await finish(gb)
        ra=await asyncio.wait_for(ta,2)
        source=json.loads(ra.prompt);assert next(r['text'] for r in source['messages'] if r['seq']==source['target_seq'])=='肥鱼，问题甲'
        await complete(a,ra,output());await finish(ga)
        assert len(first.bot.sent)==len(a.bot.sent)==len(b.bot.sent)==1
        report.append(dict(case='priority_frozen_target_original_ACK_lease',generations=3,sends=3))
        # Pending ambient merge owns one ticket; response object follows merged
        # source instead of the original event sender. No direct is merged.
        router.group_turns.reset('111');first=event(True);g1=router.on_group(first);r1=await anext(g1)
        ambient=event(text='普通话题甲');ga=router.on_group(ambient);ta=asyncio.create_task(anext(ga))
        for _ in range(100):
            if router.group_turns.pending:break
            await asyncio.sleep(.01)
        assert len(router.group_turns.pending)==1
        latest=event(sender='555',text='普通话题乙');gl=router.on_group(latest)
        try:await anext(gl)
        except StopAsyncIteration:pass
        else:raise AssertionError('ambient did not merge')
        assert len(router.group_turns.pending)==1
        await complete(first,r1,output());await finish(g1)
        ra=await asyncio.wait_for(ta,2);source=json.loads(ra.prompt)
        assert next(r['text'] for r in source['messages'] if r['seq']==source['target_seq'])=='普通话题乙'
        await complete(ambient,ra,output(response=source['target_seq']));await finish(ga)
        assert router.group_turns.state('111').focus['sender']=='555' and not router.group_turns.frozen
        report.append(dict(case='ambient_merge_object_not_carrier',generations=2,sends=2))
        # Business error follows same bound metadata path; zero extra generation.
        router.group_turns.reset('111');queue.state='QUOTA_EXHAUSTED';e=event(True);gen=router.on_group(e);req=await anext(gen)
        before=harness.attempts;await complete(e,req,output());await finish(gen)
        assert harness.attempts==before and len(e.bot.sent)==1 and router.group_turns.current is None
        assert router.group_turns.state('111').focus is None
        report.append(dict(case='bound_business_error',generations=0,sends=1))
        return dict(backend=backend,mode=mode,memes=memes,web=web_enabled,cases=report,real_model_calls=0,real_qq_calls=0,
            real_run_agent=True,actual_runner=True,original_event_ACK=True)
    finally:
        router.tasks.close();await provider.client.close();await server.cleanup()


def main():
    import subprocess
    import unittest
    if sys.argv[1:]!=['--frameworks-only']:
        sys.path.insert(0,str(ROOT/'tests'))
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        result=unittest.TextTestRunner(verbosity=1).run(suite)
        if not result.wasSuccessful():return 1
        python=ROOT/'runtime/astrbot-tool/astrbot/Scripts/python.exe'
        subprocess.run([str(python),'-X','utf8',str(Path(__file__).resolve()),'--frameworks-only'],cwd=ROOT/'runtime/astrbot',check=True)
        path=ROOT/'reports/lap-27-offline.json'
        path.write_text(json.dumps(dict(unit_tests=result.testsRun,framework_report='lap-27-framework-offline.json',
            real_model_calls=0,real_qq_calls=0,real_bot_operations=0),indent=2)+'\n',encoding='utf-8',newline='\n')
        return 0
    results=[];previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap27-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    for memes in (False,True):
                        for web_enabled in (False,True):
                            root=Path(directory)/(backend+'-'+mode+'-'+str(memes)+'-'+str(web_enabled));root.mkdir()
                            value=asyncio.run(verify(root,backend,mode,memes,web_enabled));results.append(value)
                            print('PASS v2',backend,mode,'memes',memes,'web',web_enabled,len(value['cases']),flush=True)
            # Invoke existing read-only verification functions, never old report mains.
            from scripts.verify_lap20 import verify as v1
            from scripts.verify_lap21 import verify as media
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    root=Path(directory)/(backend+'-'+mode+'-v1');root.mkdir()
                    results.append(asyncio.run(v1(root,backend,mode,full_lifecycle=True,lap24=True,lap25=True)))
                    for participation in ('mentions','free'):
                        root=Path(directory)/(backend+'-'+mode+'-'+participation);root.mkdir()
                        results.append(asyncio.run(media(root,backend,mode,participation,full_lifecycle=True,lap24=True,lap25=True)))
        finally:os.chdir(previous)
    (ROOT/'reports/lap-27-framework-offline.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS LAP-27 offline framework; no real model/QQ/bot operations',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
