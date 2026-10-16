import json
import logging
import os
from pathlib import Path
import re
import time
import uuid

import psutil
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import At, AtAll, Plain, Reply
from astrbot.core.agent.message import TextPart
from astrbot.core.message.message_event_result import MessageChain

from qqbot_gateway.session_queue import SessionCoordinator, SessionError
from qqbot_gateway.task_store import TaskStore
from qqbot_gateway.config import load_settings
from qqbot_gateway.token_budget import InputBudget, validate_model_settings
from qqbot_gateway.errors import GatewayError, MESSAGES
from qqbot_gateway.persona import compose_persona, persona_version

LOG=logging.getLogger(__name__)


@register('qq_router','local','严格入口后的单一文本路由','0.1.0')
class QQRouter(Star):
    def __init__(self,context:Context):
        super().__init__(context)
        self.root=Path(os.environ['QQBOT_ROOT']).resolve()
        settings=load_settings(self.root/'config/settings.local.yaml')
        self.bot=settings['bot']['qq'];self.groups=set(settings['access']['allowed_groups']);self.admins=set(settings['access']['admin_users'])
        self.blocked=set(settings['access']['blocked_users'])
        self.persona=compose_persona((self.root/'config/persona.md').read_text(encoding='utf-8'))
        self.persona_id=persona_version(self.persona)
        chat=settings.get('chat',{})
        self.budget=InputBudget.from_settings(settings,validate_model_settings(settings))
        self.coordinator=SessionCoordinator(chat.get('user_cooldown_seconds',5),chat.get('session_queue_limit',2),chat.get('session_queue_timeout_seconds',600))
        self.tasks=TaskStore(self.root/'state/tasks.sqlite')

    async def initialize(self):
        manager=self.context.persona_manager
        try:await manager.get_persona(self.persona_id)
        except ValueError:
            await manager.create_persona(self.persona_id,self.persona,tools=[],skills=[])
        else:
            await manager.update_persona(self.persona_id,system_prompt=self.persona,tools=[],skills=[])
        (self.root/'state/router-ready.json').write_text(json.dumps({'pid':os.getpid(),'created':psutil.Process().create_time(),'time':time.time(),'persona_id':self.persona_id}),encoding='utf-8')
        LOG.warning('QQ_ROUTER_READY persona_version=%s',self.persona_id)

    @filter.on_llm_response()
    async def model_response(self,event:AstrMessageEvent,response):
        if event.get_extra('qq_router_trace'):
            event.set_extra('qq_router_success',bool(response.completion_text))

    @filter.on_agent_done()
    async def preserve_gateway_text(self,event:AstrMessageEvent,run_context,response):
        # The OpenAI adapter strips whitespace, <think> tags and JSON wrappers.
        # Our gateway has already returned final plain text; restore that exact
        # value in both the outgoing chain and runner history, without parsing.
        if not event.get_extra('qq_router_trace') or response is None:
            return
        raw=response.raw_completion
        if (raw is None or raw.model!='workbuddy-local' or
                not raw.id.startswith('chatcmpl-') or len(raw.choices)!=1):
            return
        text=raw.choices[0].message.content
        if not isinstance(text,str) or not text.strip() or response.role!='assistant':
            return
        response.result_chain=MessageChain().message(text)
        response.reasoning_content=None
        if run_context.messages and run_context.messages[-1].role=='assistant':
            run_context.messages[-1].content=[TextPart(text=text)]
        event.set_extra('qq_router_success',True)

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_group(self,event:AstrMessageEvent):
        if (str(event.get_self_id())!=self.bot or str(event.get_group_id()) not in self.groups or
                str(event.get_sender_id())==self.bot or str(event.get_sender_id()) in self.blocked):
            event.should_call_llm(False);event.stop_event();return
        components=event.get_messages()
        if not any(isinstance(c,At) and str(c.qq)==self.bot for c in components):
            event.should_call_llm(False);event.stop_event();return
        event.should_call_llm(True)
        trace=uuid.uuid4().hex[:10];event.set_extra('qq_router_trace',trace)
        key=self.bot+':'+str(event.get_group_id())+':'+str(event.message_obj.message_id)
        if not self.tasks.accept(key,trace):return
        try:lease=await self.coordinator.acquire(event.unified_msg_origin)
        except SessionError as error:
            self.tasks.set(key,'failed')
            if error.notify:
                texts={'COOLDOWN':'上一条还在处理，等几秒再叫我吧。','SESSION_QUEUE_FULL':'你这边还有问题排着队，稍后再试。','SESSION_QUEUE_TIMEOUT':'这条问题排队超时了，请重新提问。'}
                yield event.plain_result(texts[error.code])
            return
        try:
            self.tasks.set(key,'running')
            if any(not isinstance(c,(At,AtAll,Plain,Reply)) for c in components):
                self.tasks.set(key,'failed');yield event.plain_result('目前只接通文字聊天，图片、音频和视频还没接入。');return
            prompt=''.join(c.text for c in components if isinstance(c,Plain)).strip()
            if not prompt:
                self.tasks.set(key,'failed');yield event.plain_result('我在~ 带上想问的文字再叫我吧。');return
            if re.search(r'https?://\S+',prompt,re.I):
                self.tasks.set(key,'failed');yield event.plain_result('我目前只接通文字聊天，B站和网页正文还没接入。贴段文字，我先帮你捋捋。');return
            try:self.budget.select_history(self.persona,prompt,[])
            except GatewayError:
                self.tasks.set(key,'failed');yield event.plain_result(MESSAGES['INPUT_TOO_LONG']);return
            manager=self.context.conversation_manager
            umo=event.unified_msg_origin
            cid=await manager.get_curr_conversation_id(umo)
            conv=await manager.get_conversation(umo,cid) if cid else None
            if prompt in ('重置会话','/重置'):
                if str(event.get_sender_id()) not in self.admins:
                    self.tasks.set(key,'failed');yield event.plain_result('当前只允许管理员重置本人会话。');return
                await manager.new_conversation(umo,persona_id=self.persona_id)
                self.tasks.set(key,'completed');yield event.plain_result('你在这个群里的当前会话已重置，重新聊吧。');return
            if conv is None or conv.persona_id!=self.persona_id:
                cid=await manager.new_conversation(umo,persona_id=self.persona_id)
                conv=await manager.get_conversation(umo,cid)
            history=json.loads(conv.history or '[]')
            history=self.budget.select_history(self.persona,prompt,history)
            await manager.update_conversation(umo,cid,history=history)
            conv.history=json.dumps(history,ensure_ascii=False)
            LOG.warning('QQ_TASK_RUNNING trace=%s',trace)
            try:
                yield event.request_llm(prompt=prompt,conversation=conv,tool_set=None)
            finally:
                sent=bool(getattr(event,'_has_send_oper',False))
                success=event.get_extra('qq_router_success')
                status='completed' if success and sent else ('failed' if not success and sent else 'send_unknown')
                self.tasks.set(key,status)
                LOG.warning('QQ_TASK_FINAL trace=%s status=%s',trace,status)
        except Exception:
            self.tasks.set(key,'failed')
            LOG.error('QQ_ROUTER_ERROR trace=%s',trace)
            if not getattr(event,'_has_send_oper',False):yield event.plain_result('这条没处理好，请稍后再试。（追踪'+trace+'）')
        finally:lease.release()

    async def terminate(self):
        self.tasks.close()
        ready=self.root/'state/router-ready.json'
        if ready.exists() and json.loads(ready.read_text(encoding='utf-8')).get('pid')==os.getpid():ready.unlink()
