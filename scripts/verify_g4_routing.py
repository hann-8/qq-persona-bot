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
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]


async def verify():
    from astrbot.core.db.po import Conversation
    from astrbot.api.message_components import At,Plain,Reply
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
        settings=yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
        settings['bot']['qq']='222'
        settings['access'].update(allowed_groups=['111','444'],admin_users=['333'])
        settings['chat']['user_cooldown_seconds']=0
        (root/'config/settings.local.yaml').write_text(yaml.safe_dump(settings),encoding='utf-8')
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
            for text in ('大肥鱼', '鱼鱼在吗', '冷场了，出来说话'):
                silent=event('333','111',50,text,mention=False)
                assert [item async for item in router.on_group(silent)]==[]
                assert not silent.get_extra('qq_router_trace')
            quoted=event('333','111',51,'引用旧消息',mention=False)
            quoted.message_obj.message.insert(0,Reply(id='old',chain=[At(qq='222')]))
            assert [item async for item in router.on_group(quoted)]==[]
            assert not quoted.get_extra('qq_router_trace')
            # Direct plugin delivery must stop before trace/task/coordinator/history, including admins.
            router.blocked={'333','555'}
            before_conversations=len(manager.items)
            from unittest.mock import patch
            with patch.object(router.tasks,'accept',side_effect=AssertionError('Blocked task accepted')), \
                 patch.object(router.coordinator,'acquire',side_effect=AssertionError('Blocked cooldown/queue reached')):
                for user in ('333','555'):
                    for mention in (True,False):
                        rejected=event(user,'111',6,'blocked',mention=mention)
                        assert [item async for item in router.on_group(rejected)]==[]
                        assert not rejected.get_extra('qq_router_trace')
                        assert rejected.is_stopped()
                cross_group=event('333','999',7,'unauthorized admin')
                assert [item async for item in router.on_group(cross_group)]==[]
                assert cross_group.is_stopped()
            assert len(manager.items)==before_conversations
            router.blocked=set()
            restored=await request(event('333','111',8,'recall after unblock'))
            assert 'A-secret' in restored.conversation.history
            from qqbot_gateway.token_budget import InputBudget
            router.budget=InputBudget(limit=1024,overhead=32,history_turns=1)
            single=await request(event('333','111',9,'only current'))
            assert single.conversation.history=='[]'
            too_long=event('333','111',10,'🙂'*1000)
            rejected=[item async for item in router.on_group(too_long)]
            assert len(rejected)==1 and not isinstance(rejected[0],ProviderRequest)
            # A larger configured budget must not retain the old 24k/8k character ceiling.
            router.budget=InputBudget(limit=100000,overhead=32,history_turns=64)
            large=await request(event('333','111',11,'x'*25000))
            assert len(large.prompt)==25000
            from qqbot_gateway.persona import compose_persona,persona_version
            old_cid=manager.current[first.unified_msg_origin]
            old_count=len(manager.items)
            router.persona=compose_persona('new offline character')
            router.persona_id=persona_version(router.persona)
            migrated=await request(event('333','111',12,'new persona'))
            assert migrated.conversation.cid!=old_cid and migrated.conversation.history=='[]'
            assert len(manager.items)==old_count+1
            assert (first.unified_msg_origin,old_cid) in manager.items
            print('PASS: actual AstrBot session keys + router retain same-user history, isolate other user/group, reject no-At; no network/model calls.')
            print('PASS: direct blocked admin/user, no-At and unauthorized admin stop before trace/tasks/cooldown/history; unblocking retains history.')
            print('PASS: configured history=1, over-budget emoji rejection before provider, and >24k input under a larger budget.')
            print('PASS: name/cold-chat/quoted-At stay silent; persona version creates a new conversation without deleting old history.')
        finally:router.tasks.close()


if __name__=='__main__':asyncio.run(verify())
