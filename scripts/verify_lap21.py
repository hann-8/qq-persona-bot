"""Installed AstrBot/SDK + both real runners with synthetic transports only."""
import asyncio
import copy
import io
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


async def verify(root,backend,mode,participation,full_lifecycle=False,lap24=False,lap25=False):
    import yaml
    from PIL import Image
    from aiohttp import web
    from astrbot.api.platform import AstrBotMessage,MessageMember,MessageType,PlatformMetadata
    from astrbot.api.message_components import Plain,At
    from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
    from astrbot.core.agent.message import Message
    from astrbot.core.pipeline.process_stage.method.agent_sub_stages.internal import InternalAgentSubStage
    from astrbot.core.pipeline.result_decorate.stage import ResultDecorateStage
    from astrbot.core.pipeline.respond.stage import RespondStage
    from astrbot.core.config.default import DEFAULT_CONFIG
    import astrbot.core.pipeline.result_decorate.stage as decorate_module
    from astrbot.core.db.po import Conversation
    from plugins.qq_router.main import QQRouter
    from plugins.qq_router.provider import QQBotProvider
    from qqbot_gateway.meme_catalog import MemeCatalog
    from qqbot_gateway.model_gateway import application,ModelQueue
    from qqbot_gateway.web_retrieval import WebRunner,Retriever
    from qqbot_gateway.token_budget import InputBudget
    from qqbot_gateway.task_store import TaskStore
    from qqbot_gateway.onebot_gate import allowed_action
    from qqbot_gateway.config import GateConfig
    from scripts.verify_lap17 import Harness

    class Manager:
        def __init__(self):self.current={};self.items={}
        async def get_curr_conversation_id(self,umo):return self.current.get(umo)
        async def get_conversation(self,umo,cid):return self.items.get((umo,cid))
        async def new_conversation(self,umo,persona_id):
            cid=str(len(self.items)+1);self.current[umo]=cid
            self.items[(umo,cid)]=Conversation('qqbot',umo,cid,history='[]',persona_id=persona_id);return cid
        async def update_conversation(self,umo,cid,history,**kwargs):self.items[(umo,cid)].history=json.dumps(history,ensure_ascii=False)
    settings=yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
    settings['participation']['silence']={'enabled':False}  # legacy-disabled regression
    settings['bot']['qq']='222';settings['access'].update(allowed_groups=['111'],admin_users=['333'])
    settings['llm']['backend']=backend
    if backend=='ollama_ssh':settings['llm']['profiles'][backend]['expected_digest']='a'*64
    settings['participation'].update(mode=participation,debounce_seconds=.5,max_batch_wait_seconds=2)
    settings['memes'].update(enabled=True,cooldown_seconds=0,same_meme_cooldown_seconds=0)
    settings['chat']['user_cooldown_seconds']=0
    settings['output'].update(delivery_mode=mode,bubble_delay_min_ms=0,bubble_delay_max_ms=0)
    (root/'config').mkdir();(root/'state').mkdir()
    (root/'config/settings.local.yaml').write_text(yaml.safe_dump(settings),encoding='utf-8')
    (root/'config/persona.md').write_text('合成角色',encoding='utf-8')
    c=MemeCatalog(root,settings['memes']);out=io.BytesIO();Image.new('RGB',(3,3),'red').save(out,format='PNG')
    row=c.add(out.getvalue());row.update(name='自造红块',tags=['开心'],enabled=True);c.save();mid=row['id']
    manager=Manager()
    with patch.dict(os.environ,{'QQBOT_ROOT':str(root)}):router=QQRouter(SimpleNamespace(conversation_manager=manager))
    router.connection=lambda:'a'*64;router.delivery.timeout=.03
    harness=Harness(root,backend);wrapped=WebRunner(harness,Retriever(settings['web']),InputBudget(),settings['output']);wrapped.memes=c
    queue=ModelQueue(wrapped);token=secrets.token_urlsafe(32)
    server=web.AppRunner(application(queue,token,output=settings['output'],memes=c),access_log=None)
    await server.setup();site=web.TCPSite(server,'127.0.0.1',0);await site.start();port=site._server.sockets[0].getsockname()[1]
    provider=QQBotProvider(dict(id='lap21',type='qqbot_openai',api_base=f'http://127.0.0.1:{port}/v1',key=[token],model='workbuddy-local',modalities=['text'],custom_extra_body={},timeout=10),{})
    config=copy.deepcopy(DEFAULT_CONFIG);config['t2i']=False;config['content_safety']['also_use_in_response']=False
    config['provider_settings'].update(prompt_prefix='{{prompt}}',identifier=False,group_name_display=False,datetime_system_prompt=False,web_search=False,computer_use_runtime='none')
    config['kb_names']=[]
    config['provider_tts_settings']['enable']=False
    config['platform_settings'].update(reply_prefix='',reply_with_mention=True,reply_with_quote=True,forward_threshold=100000)
    config['platform_settings']['segmented_reply']['enable']=False
    async def no_tts(*args):return None
    ctx=SimpleNamespace(astrbot_config=config,plugin_manager=SimpleNamespace(context=SimpleNamespace(get_using_tts_provider_async=no_tts)))
    decorate=ResultDecorateStage();respond=RespondStage();await decorate.initialize(ctx);await respond.initialize(ctx)
    stage=InternalAgentSubStage();stage.conv_manager=manager
    gatecfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'x'*32,'y'*32,root/'unused.sqlite',media_catalog=c,silence_enabled=False)
    report=[]
    try:
        cases=['text_image','image_only','invalid_id','answer','missing2','duplicate2','error2','timeout2','stop','hash_changed','cooldown','bad','metadata_missing','metadata_mismatch','image_only_missing','web_answer']
        if lap24:cases+=['text1','text2','text3','text2_image','capacity_image']
        if lap25:cases+=['fenced','optional','plain','bad_meme_text','final_system_trim']
        if participation=='free':cases+=['ambient_image_only','silent']
        for case in cases:
            if participation=='free':
                router.group_turns.reset('111')
                if case=='final_system_trim':
                    for n in range(30):router.group_turns.append('111','old',str(n),'old','x'*350)
            class Bot:
                def __init__(self):self.sent=[]
                async def send_group_msg(self,**kwargs):
                    assert allowed_action(dict(action='send_group_msg',params=kwargs),gatecfg),kwargs
                    self.sent.append(kwargs);n=len(self.sent)
                    if n==2:
                        if case=='missing2':return {}
                        if case=='duplicate2':return {'message_id':1}
                        if case=='error2':raise ConnectionError('synthetic')
                        if case=='timeout2':await asyncio.sleep(1)
                    if case=='stop':flag['allowed']=False
                    return {'message_id':n}
            only=case in ('image_only','image_only_missing','ambient_image_only')
            question='发个表情' if only else 'https://example.com/page' if case=='web_answer' else '开心' if case!='answer' else '详细解释'
            original_retriever=wrapped.retriever
            if case=='web_answer':
                from qqbot_gateway.web_retrieval import Retrieval
                class Evidence:
                    cfg=original_retriever.cfg;last_audit={}
                    async def retrieve(self,question):return Retrieval('read',[dict(url='https://example.com/page',title='Synthetic source',text='SYNTHETIC_EVIDENCE '*20,status='read',published=None)])
                wrapped.retriever=Evidence();router.web['enabled']=True
            msg=AstrBotMessage();msg.self_id='222';msg.type=MessageType.GROUP_MESSAGE;msg.group_id='111'
            msg.sender=MessageMember(str(333+len(report)),'synthetic');msg.message_id=str(len(report)+1)
            msg.message=([At(qq='222')] if case not in ('ambient_image_only','silent') else [])+[Plain(text=question)];msg.message_str=question;msg.session_id='111'
            msg.raw_message={'qqbot_connection':'a'*64}
            e=AiocqhttpMessageEvent(question,msg,PlatformMetadata(name='aiocqhttp',description='offline',id='qqbot'),'111',Bot())
            gen=router.on_group(e);req=await anext(gen)
            if case=='final_system_trim':req.system_prompt+='S'*7500
            raw=dict(kind='answer' if case in ('answer','web_answer') else 'chat',bubbles=[] if only or case=='silent' else ['合成文字'],meme_id='invalid' if case=='invalid_id' else None if case=='silent' else mid)
            if case in ('text1','text2','text3','text2_image','capacity_image'):
                n=3 if case in ('text3','capacity_image') else 2 if case in ('text2','text2_image') else 1
                raw.update(bubbles=['合成文字'+str(i) for i in range(n)],meme_id=mid if case in ('text2_image','capacity_image') else None)
            if participation=='free':raw.update(qqbot_group_reply=1,decision='silent' if case=='silent' else 'speak')
            else:raw.update(qqbot_media_reply=1)
            if case in ('fenced','optional','plain','bad_meme_text','final_system_trim'):raw['meme_id']=None
            if case=='optional':raw.pop('meme_id');raw['bubbles']='合成文字';raw['reason']='inert'
            if case=='bad_meme_text':raw['meme_id']={'path':'untrusted'}
            harness.text='{"broken"' if case=='bad' else json.dumps(raw,ensure_ascii=False)
            if case=='fenced':harness.text='```json\n'+harness.text+'\n```'
            if case=='plain':harness.text='合成文字'
            prior=harness.attempts
            path,_=c.resolve(mid);original=path.read_bytes()
            if case in ('hash_changed','image_only_missing'):path.write_bytes(b'changed')
            flag={'allowed':True};old_allowed=router.delivery.allowed
            router.delivery.allowed=lambda ev:flag['allowed'] and old_allowed(ev)
            if case=='cooldown':
                router.delivery.catalog.cfg['cooldown_seconds']=60;router.delivery.image_times['111']=__import__('time').monotonic()
            if case=='text_image' or full_lifecycle:
                from astrbot.core.astr_main_agent import build_main_agent,MainAgentBuildConfig
                from astrbot.api.star import Context
                from unittest.mock import AsyncMock
                from astrbot.core.provider.func_tool_manager import ToolSet
                import astrbot.core.tools.knowledge_base_tools as kb_module
                pc=Context.__new__(Context);pc.conversation_manager=manager;pc.get_config=lambda **kw:config
                pc.kb_manager=None;pc._db=None;pc.subagent_orchestrator=None
                pc.get_llm_tool_manager=lambda:SimpleNamespace(func_list=[])
                pc.persona_manager=SimpleNamespace(resolve_selected_persona=AsyncMock(return_value=(router.persona_id,{'prompt':router.persona,'tools':[],'skills':[]},None,False)))
                e.set_extra('provider_request',req)
                with patch.object(kb_module.sp,'session_get',AsyncMock(return_value={})),patch.object(kb_module.sp,'get_async',AsyncMock(return_value={})):
                    built=await build_main_agent(event=e,plugin_context=pc,provider=provider,config=MainAgentBuildConfig(tool_call_timeout=5,streaming_response=False,add_cron_tools=False,llm_safety_mode=False,provider_settings=config['provider_settings'],request_max_retries=1))
                assert built.provider_request.session_id==req.session_id
                assert built.provider_request.func_tool is None or built.provider_request.func_tool.empty()
                if full_lifecycle:
                    from astrbot.core.astr_agent_run_util import run_agent
                    async def done(context,response):
                        meta_name='qqbot_group_plan' if participation=='free' else 'qqbot_reply_plan'
                        if case=='metadata_missing':setattr(response.raw_completion,meta_name,None)
                        if case=='metadata_mismatch':getattr(response.raw_completion,meta_name)['plan_hash' if participation=='free' else 'content_sha256']='bad'
                        await router.preserve_gateway_text(e,context,response)
                    from astrbot.core.star.star_handler import EventType
                    handler=SimpleNamespace(handler_module_path='lap21',handler_name='deliver_reply',handler=router.deliver_reply)
                    def handlers(kind,**kwargs):return [handler] if kind==EventType.OnDecoratingResultEvent else []
                    with patch.object(built.agent_runner.agent_hooks,'on_agent_done',side_effect=done),patch.object(decorate_module.star_handlers_registry,'get_handlers_by_event_type',side_effect=handlers),patch.dict(decorate_module.star_map,{'lap21':SimpleNamespace(name='lap21')}):
                        async for _ in run_agent(built.agent_runner,max_step=1,show_tool_use=False):
                            async for _ in decorate.process(e):pass
                            await respond.process(e)
                    response=built.agent_runner.get_final_llm_resp()
                else:
                    responses=[r async for r in built.agent_runner._iter_llm_responses()];assert len(responses)==1;response=responses[0]
            else:response=await provider.text_chat(prompt=req.prompt,system_prompt=router.persona,contexts=req.contexts,session_id=req.session_id,func_tool=None,request_max_retries=1)
            assert harness.attempts==prior+1
            meta_name='qqbot_group_plan' if participation=='free' else 'qqbot_reply_plan'
            if not full_lifecycle and case=='metadata_missing':setattr(response.raw_completion,meta_name,None)
            if not full_lifecycle and case=='metadata_mismatch':getattr(response.raw_completion,meta_name)['plan_hash' if participation=='free' else 'content_sha256']='bad'
            prior_messages=[Message.model_validate(m) for m in json.loads(req.conversation.history)] if req.conversation else []
            rc=SimpleNamespace(messages=prior_messages+[Message(role='user',content=req.prompt),Message(role='assistant',content=response.completion_text)])
            if full_lifecycle:rc=built.agent_runner.run_context
            else:await router.preserve_gateway_text(e,rc,response)
            key=e.get_extra('qq_delivery_key')
            if case not in ('silent','metadata_missing','metadata_mismatch'):assert router.tasks.delivery(key),case
            if participation=='mentions':await stage._save_to_history(e,req,response,rc.messages,None)
            if not full_lifecycle:e.set_result(e.plain_result(response.completion_text))
            handler=SimpleNamespace(handler_module_path='lap21',handler_name='deliver_reply',handler=router.deliver_reply)
            if not full_lifecycle:
                with patch.object(decorate_module.star_handlers_registry,'get_handlers_by_event_type',return_value=[handler]),patch.dict(decorate_module.star_map,{'lap21':SimpleNamespace(name='lap21')}):
                    async for _ in decorate.process(e):pass
                await respond.process(e)
            count=len(e.bot.sent)
            # Invalid mentions metadata stops the real pipeline before decoration.
            # Do not invent a decoration call that the framework would never make.
            stopped_metadata=full_lifecycle and participation=='mentions' and case in ('metadata_missing','metadata_mismatch')
            if not stopped_metadata:await router.deliver_reply(e)
            assert len(e.bot.sent)==count,(case,count,len(e.bot.sent))
            try:await anext(gen)
            except StopAsyncIteration:pass
            router.delivery.allowed=old_allowed;router.delivery.catalog.cfg['cooldown_seconds']=0;path.write_bytes(original)
            types=[s['message'][0]['type'] for s in e.bot.sent]
            expected=[] if case=='silent' else ['image'] if case in ('image_only','ambient_image_only') else ['text'] if case in ('invalid_id','answer','stop','hash_changed','cooldown','bad','metadata_missing','metadata_mismatch','image_only_missing','web_answer') else ['text','image']
            if case in ('fenced','optional','plain','bad_meme_text','final_system_trim'):expected=['text']
            if case in ('text1','text2','text3'):expected=['text']*(int(case[-1]) if mode=='adaptive' else 1)
            if case in ('text2_image','capacity_image'):expected=['text']*((3 if case=='capacity_image' else 2) if mode=='adaptive' else 1)+(['image'] if case=='text2_image' or mode=='single' else [])
            if stopped_metadata:expected=[]
            assert types==expected,(case,types,expected)
            if case in ('fenced','optional','plain','bad_meme_text','final_system_trim'):
                assert e.bot.sent[0]['message'][0]['data']['text']=='合成文字',case
            if case=='web_answer':
                assert '来源：Synthetic source https://example.com/page' in e.bot.sent[0]['message'][0]['data']['text']
                assert 'SYNTHETIC_EVIDENCE' not in e.bot.sent[0]['message'][0]['data']['text']
                wrapped.retriever=original_retriever;router.web['enabled']=False
            confirmed=[]
            for i,state,_ in router.tasks.parts(key):
                if state!='sent':break
                confirmed.append(json.loads(router.tasks.delivery(key)['bubbles'])[i])
            if participation=='mentions' and case not in ('metadata_missing','metadata_mismatch'):
                conv=await manager.get_conversation(e.unified_msg_origin,req.conversation.cid);history=json.loads(conv.history)
                assert (history[-1]['content'] if history and history[-1]['role']=='assistant' else '')=='\n'.join(confirmed)
            report.append(dict(case=case,types=types,ack=[s for _,s,_ in router.tasks.parts(key)],generations=1))
        # Crash during an image intent never resends; typed row survives reopen.
        from qqbot_gateway.media_protocol import media_plan
        _,plan=media_plan(json.dumps(dict(qqbot_media_reply=1,kind='chat',bubbles=[],meme_id=mid)),settings['output'],'发个表情',c,c.candidates(''))
        router.tasks.accept('crash','t');router.tasks.prepare_group_delivery('crash','111','epoch','r',plan,'d',[1,2]);router.tasks.begin_part('crash',0)
        router.tasks.close();router.tasks=TaskStore(root/'state/tasks.sqlite');await router.tasks.recover_deliveries(manager)
        assert router.tasks.parts('crash')[0][1]=='unknown' and not router.tasks.group_blocked('111')
        assert router.tasks.db.execute("SELECT part_type FROM prepared_part WHERE message_key='crash'").fetchone()[0]=='image'
        return dict(backend=backend,mode=mode,participation=participation,cases=report,recovery=True,real_model_requests=0,real_qq_messages=0,real_favorites_reads=0)
    finally:
        router.tasks.close();await provider.client.close();await server.cleanup()


def main():
    results=[];previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap21-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    for participation in ('mentions','free'):
                        root=Path(directory)/(backend+'-'+mode+'-'+participation);root.mkdir()
                        results.append(asyncio.run(verify(root,backend,mode,participation)));print('PASS',backend,mode,participation)
        finally:os.chdir(previous)
    (ROOT/'reports/lap-21-framework-offline.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
