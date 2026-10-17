"""First LAP-20 capability gate: installed framework only, no QQ/model."""
import asyncio
import os
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
os.environ['ASTRBOT_DISABLE_METRICS']='1'


async def verify():
    from astrbot.api.platform import AstrBotMessage,MessageMember,MessageType,PlatformMetadata
    from astrbot.api.message_components import Plain
    from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
    from astrbot.core.pipeline.process_stage.method.agent_sub_stages.internal import InternalAgentSubStage
    from astrbot.core.astr_main_agent import collect_initial_request
    from qqbot_gateway.event_guard import EventSendGuard
    from qqbot_gateway.reply_delivery import ReplyDelivery
    from qqbot_gateway.reply_plan import ReplyPlan,DEFAULTS
    from qqbot_gateway.task_store import TaskStore
    import tempfile
    class Bot:
        sent=[]
        async def send_group_msg(self,**kwargs):self.sent.append(kwargs);return {'message_id':len(self.sent)}
    class Manager:
        def __getattr__(self,name):raise AssertionError('Personal conversation accessed: '+name)
    msg=AstrBotMessage();msg.self_id='222';msg.type=MessageType.GROUP_MESSAGE
    msg.group_id='111';msg.sender=MessageMember('333','synthetic');msg.message_id='1'
    msg.message=[Plain(text='synthetic')];msg.message_str='synthetic';msg.session_id='111'
    bot=Bot();event=AiocqhttpMessageEvent('synthetic',msg,PlatformMetadata(name='aiocqhttp',description='offline',id='qqbot'),'111',bot)
    guard=EventSendGuard(event)
    req=event.request_llm(prompt='synthetic snapshot',contexts=[],system_prompt='policy',conversation=None,tool_set=None)
    event.set_extra('provider_request',req)
    resolved,_=await collect_initial_request(event,SimpleNamespace(conversation_manager=Manager()),SimpleNamespace())
    assert resolved.conversation is None and resolved.contexts==[]
    stage=InternalAgentSubStage();stage.conv_manager=Manager()
    await stage._save_to_history(event,req,None,[],None)
    await event.send(event.plain_result('INTERNAL_SILENT'))
    await event.send(event.plain_result('framework exception'))
    assert not bot.sent
    with tempfile.TemporaryDirectory() as directory:
        store=TaskStore(Path(directory)/'tasks.sqlite');store.accept('k','t')
        plan=ReplyPlan('answer',('ACK text',),'ACK text')
        store.prepare_delivery('k','umo','cid','r',plan,[],[{'role':'user','content':'synthetic'},{'role':'assistant','content':plan.canonical_text}])
        delivery=ReplyDelivery(store,DEFAULTS,lambda e:True)
        with guard.grant():await delivery.send(event,'k',plan)
        assert len(bot.sent)==1 and store.parts('k')[0][1]=='sent'
        await event.send(event.plain_result('late exception'));assert len(bot.sent)==1
        store.close()
    print('PASS installed collect_initial_request/no conversation/save skipped; silent/exception denied; granted original-event ACK; late send denied')

if __name__=='__main__':asyncio.run(verify())
