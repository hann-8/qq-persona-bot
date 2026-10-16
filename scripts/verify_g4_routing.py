"""Offline router integration with installed AstrBot events and session builder.

Uses an in-memory conversation-manager double; no model or QQ network calls.
"""
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]


async def verify():
    from astrbot.core.db.po import Conversation
    from astrbot.api.message_components import At,Plain
    from astrbot.api.platform import AstrBotMessage,MessageMember,MessageType,PlatformMetadata
    from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
    from astrbot.core.pipeline.waking_check.stage import build_unique_session_id
    from astrbot.core.provider.entities import ProviderRequest
    from plugins.qq_router.main import QQRouter

    class Conversations:
        def __init__(self):self.current={};self.items={}
        async def get_curr_conversation_id(self,umo):return self.current.get(umo)
        async def get_conversation(self,umo,cid):return self.items[(umo,cid)]
        async def new_conversation(self,umo,persona_id):
            cid=str(len(self.items)+1);self.current[umo]=cid
            self.items[(umo,cid)]=Conversation('qqbot',umo,cid,history='[]',persona_id=persona_id)
            return cid
        async def update_conversation(self,umo,cid,history):self.items[(umo,cid)].history=json.dumps(history)

    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory);(root/'config').mkdir()
        (root/'config/settings.local.yaml').write_text('bot:\n  qq: "222"\naccess:\n  allowed_groups: ["111", "444"]\n  admin_users: ["333"]\nchat:\n  user_cooldown_seconds: 0\n',encoding='utf-8')
        (root/'config/persona.md').write_text('offline persona',encoding='utf-8')
        previous=os.environ.get('QQBOT_ROOT');os.environ['QQBOT_ROOT']=directory
        manager=Conversations()
        router=QQRouter(SimpleNamespace(conversation_manager=manager))
        if previous is None:os.environ.pop('QQBOT_ROOT')
        else:os.environ['QQBOT_ROOT']=previous

        def event(user,group,mid,text,mention=True):
            msg=AstrBotMessage();msg.self_id='222';msg.type=MessageType.GROUP_MESSAGE
            msg.group_id=group;msg.sender=MessageMember(user,'offline user')
            msg.message_id=str(mid);msg.message=([At(qq='222')] if mention else [])+[Plain(text=text)]
            msg.message_str=text;msg.session_id=group
            e=AiocqhttpMessageEvent(text,msg,PlatformMetadata(name='aiocqhttp',description='offline',id='qqbot'),group,None)
            e.session_id=build_unique_session_id(e)
            return e

        async def request(e):
            generator=router.on_group(e)
            result=await anext(generator)
            assert isinstance(result,ProviderRequest), 'Router did not yield a provider request'
            e.set_extra('qq_router_success',True);e._has_send_oper=True
            try:await anext(generator)
            except StopAsyncIteration:pass
            else:raise AssertionError('Duplicate router output')
            return result

        try:
            first=event('333','111',1,'remember A')
            a=await request(first)
            a.conversation.history=json.dumps([{'role':'user','content':'remember A'},
                                                {'role':'assistant','content':'A-secret'}])
            same=await request(event('333','111',2,'recall'))
            other_user=await request(event('555','111',3,'recall'))
            other_group=await request(event('333','444',4,'recall'))
            assert 'A-secret' in same.conversation.history
            assert other_user.conversation.history=='[]' and other_group.conversation.history=='[]'
            assert len(manager.items)==3
            no_at=router.on_group(event('333','111',5,'ordinary',mention=False))
            try:await anext(no_at)
            except StopAsyncIteration:pass
            else:raise AssertionError('Non-At reached the model')
            print('PASS: actual AstrBot session keys + router retain same-user history, isolate other user/group, reject no-At; no network/model calls.')
        finally:router.tasks.close()


if __name__=='__main__':asyncio.run(verify())
