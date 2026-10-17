import json
import asyncio
from dataclasses import replace
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
from qqbot_gateway.persona import compose_persona, session_version
from qqbot_gateway.lifecycle import stopping
from qqbot_gateway.reply_plan import trusted_plan, digest
from qqbot_gateway.reply_delivery import ReplyDelivery, cancellable
from qqbot_gateway.event_guard import EventSendGuard
from qqbot_gateway.participation import Participation
from qqbot_gateway.group_protocol import verify_metadata
from .provider import QQBotProvider  # registers the project adapter before provider loading

LOG=logging.getLogger(__name__)


@register('qq_router','local','严格入口后的单一文本路由','0.1.0')
class QQRouter(Star):
    def __init__(self,context:Context):
        super().__init__(context)
        self.root=Path(os.environ['QQBOT_ROOT']).resolve()
        settings=load_settings(self.root/'config/settings.local.yaml')
        self.bot=settings['bot']['qq'];self.groups=set(settings['access']['allowed_groups']);self.admins=set(settings['access']['admin_users'])
        self.blocked=set(settings['access']['blocked_users'])
        self.output=settings['output']
        self.web=settings['web']
        self.participation=settings['participation']
        self.persona=compose_persona((self.root/'config/persona.md').read_text(encoding='utf-8'),self.output,self.web,self.participation)
        self.persona_id=session_version(self.persona,settings)
        chat=settings.get('chat',{})
        self.budget=InputBudget.from_settings(settings,validate_model_settings(settings))
        self.coordinator=SessionCoordinator(chat.get('user_cooldown_seconds',5),chat.get('session_queue_limit',2),chat.get('session_queue_timeout_seconds',600))
        self.tasks=TaskStore(self.root/'state/tasks.sqlite')
        self.delivery=ReplyDelivery(self.tasks,self.output,self.delivery_allowed)
        self.group_turns=Participation(self.participation,digest(self.persona_id+uuid.uuid4().hex),settings['llm']['queue_limit'],chat.get('session_queue_timeout_seconds',600))
        self.connection_id=None
        self.connection_watcher=None

    def connection(self):
        try:
            data=json.loads((self.root/'state/gate-connection.json').read_text(encoding='utf-8'))
            process=psutil.Process(data['pid'])
            if abs(process.create_time()-data['created'])>=.01 or time.time()-data['updated']>45:return None
            return data['id'] if data['connected'] and data['online'] is True else None
        except (OSError,ValueError,KeyError,psutil.Error):return None

    async def watch_connection(self):
        # Metadata invalidation only. This task never searches, generates or sends.
        while True:
            current=self.connection()
            if current!=self.connection_id:
                self.group_turns.invalidate();self.connection_id=current
            await asyncio.sleep(.1)

    async def local_notice(self,event,text):
        guard=event.get_extra('qq_send_guard')
        if not text or not self.delivery_allowed(event) or (event.get_extra('qq_connection') and event.get_extra('qq_connection')!=self.connection()):return
        try:
            async with self.delivery.queue.hold(str(event.get_group_id()),lambda:self.delivery_allowed(event)):
                with guard.grant():
                    await cancellable(event.send(event.plain_result(text)),lambda:self.delivery_allowed(event),3)
        except Exception:pass

    async def initialize(self):
        await self.tasks.recover_deliveries(self.context.conversation_manager)
        if self.participation['mode']=='free':self.connection_watcher=asyncio.create_task(self.watch_connection())
        manager=self.context.persona_manager
        try:await manager.get_persona(self.persona_id)
        except ValueError:
            await manager.create_persona(self.persona_id,self.persona,tools=[],skills=[])
        else:
            await manager.update_persona(self.persona_id,system_prompt=self.persona,tools=[],skills=[])
        (self.root/'state/router-ready.json').write_text(json.dumps({'pid':os.getpid(),'created':psutil.Process().create_time(),'time':time.time(),'persona_id':self.persona_id,'instance_id':os.environ.get('QQBOT_INSTANCE_ID')}),encoding='utf-8')
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
        if event.get_extra('qq_group_request'):
            event.clear_result()
            try:
                raw=response.raw_completion
                if raw.model!='workbuddy-local' or not raw.id.startswith('chatcmpl-') or len(raw.choices)!=1:raise ValueError()
                text=raw.choices[0].message.content
                request=event.get_extra('qq_group_request')
                plan=verify_metadata(getattr(raw,'qqbot_group_plan',None),request,raw.id,text,self.output)
                event.set_extra('qq_group_response',raw.id)
                event.set_extra('qq_group_metadata',raw.qqbot_group_plan)
                event.set_extra('qq_delivery_plan',plan)
                response.result_chain=MessageChain()
                response.reasoning_content=None
                for message in run_context.messages:message._no_save=True
                if plan:
                    key=event.get_extra('qq_delivery_key')
                    self.tasks.prepare_group_delivery(key,str(event.get_group_id()),request['epoch'],
                        raw.id,plan,request['snapshot_digest'],event.get_extra('qq_snapshot_range'))
                    row=self.tasks.delivery(key)
                    if row['response_id']!=raw.id or row['content_sha256']!=digest(plan.canonical_text) or tuple(json.loads(row['bubbles']))!=plan.bubbles:
                        raise ValueError('Group response changed during hook reentry')
            except Exception:
                event.set_extra('qq_group_invalid',True)
                event.set_extra('qq_delivery_plan',None)
                response.result_chain=MessageChain()
                for message in run_context.messages:message._no_save=True
            return
        if response.role!='assistant':
            event.set_extra('qq_router_success',False)
            return
        raw=response.raw_completion
        if (raw is None or raw.model!='workbuddy-local' or
                not raw.id.startswith('chatcmpl-') or len(raw.choices)!=1):
            if getattr(self,'output',{}).get('delivery_mode')=='adaptive' and event.get_extra('qq_delivery_key'):
                event.clear_result();event.stop_event()
            return
        if getattr(raw,'qqbot_web_expired',False) is True:
            # Authenticated gateway deadline marker: never save/send its internal body.
            event.set_extra('qq_web_expired',True)
            event.set_extra('qq_router_success',False)
            response.result_chain=MessageChain()
            response.reasoning_content=None
            if run_context.messages and run_context.messages[-1].role=='assistant':
                run_context.messages[-1]._no_save=True
                run_context.messages[-1].content=[]
            event.clear_result();event.stop_event();return
        text=raw.choices[0].message.content
        if not isinstance(text,str) or not text.strip() or response.role!='assistant':
            if getattr(self,'output',{}).get('delivery_mode')=='adaptive' and event.get_extra('qq_delivery_key'):
                event.clear_result();event.stop_event()
            return
        response.result_chain=MessageChain().message(text)
        response.reasoning_content=None
        if run_context.messages and run_context.messages[-1].role=='assistant':
            run_context.messages[-1].content=[TextPart(text=text)]
        event.set_extra('qq_router_success',True)
        if getattr(self,'output',{}).get('delivery_mode')=='adaptive' and event.get_extra('qq_delivery_key'):
            # Persist before the framework can either save history or dispatch a result.
            try:
                key=event.get_extra('qq_delivery_key')
                plan=trusted_plan(getattr(raw,'qqbot_reply_plan',None),text,raw.id,self.output)
                expected=[m.model_dump() for m in run_context.messages if m.role!='system' and not m._no_save]
                self.tasks.prepare_delivery(key,event.unified_msg_origin,event.get_extra('qq_delivery_cid'),
                    raw.id,plan,event.get_extra('qq_delivery_before'),expected)
                row=self.tasks.delivery(key)
                if (row['response_id']!=raw.id or row['content_sha256']!=digest(plan.canonical_text) or
                        tuple(json.loads(row['bubbles']))!=plan.bubbles):
                    raise ValueError('Response changed during hook reentry')
                event.set_extra('qq_delivery_plan',plan)
            except Exception:
                # Framework swallows hook exceptions; explicitly stop unsafe save/dispatch.
                event.set_extra('qq_router_success',False)
                event.clear_result();event.stop_event()
                LOG.error('QQ_DELIVERY_PREPARE_FAILED')

    def delivery_allowed(self,event):
        group_request=event.get_extra('qq_group_request')
        group_ok=(not group_request or (group_request['epoch']==self.group_turns.group_epoch(str(event.get_group_id())) and
            not self.tasks.group_blocked(str(event.get_group_id())) and
            event.get_extra('qq_connection')==self.connection() and
            (group_request['must_reply'] or (time.monotonic()-event.get_extra('qq_group_created')<=self.participation['max_ambient_age_seconds'] and self.group_turns.may_speak(str(event.get_group_id()))))))
        return (group_ok and not stopping(self.root) and str(event.get_self_id())==self.bot and
                str(event.get_group_id()) in self.groups and str(event.get_sender_id()) not in self.blocked and
                str(event.get_sender_id())!=self.bot and event.get_extra('qq_delivery_version')==self.persona_id and
                event.get_extra('qq_delivery_identity')==(str(event.get_self_id()),str(event.get_group_id()),str(event.get_sender_id())))

    @filter.on_decorating_result()
    async def deliver_reply(self,event:AstrMessageEvent):
        guard=event.get_extra('qq_send_guard')
        if event.get_extra('qq_group_request'):
            event.clear_result()
            if event.get_extra('qq_delivery_handled'):return
            request=event.get_extra('qq_group_request');plan=event.get_extra('qq_delivery_plan');key=event.get_extra('qq_delivery_key')
            if plan:
                try:verify_metadata(event.get_extra('qq_group_metadata'),request,event.get_extra('qq_group_response'),plan.canonical_text,self.output)
                except Exception:plan=None;event.set_extra('qq_group_invalid',True)
            if plan and self.delivery_allowed(event):
                with guard.grant():await self.delivery.send(event,key,plan)
            else:
                event.set_extra('qq_delivery_handled',True)
                if request['must_reply'] and (event.get_extra('qq_group_invalid') or not event.get_extra('qq_group_metadata')):
                    await self.local_notice(event,'这条没接住，请再说一次。')
            event.clear_result();return
        if guard and not event.get_extra('qq_delivery_key'):
            result=event.get_result()
            event.clear_result()
            if result and not event.get_extra('qq_local_handled'):
                event.set_extra('qq_local_handled',True)
                await self.local_notice(event,''.join(c.text for c in result.chain if isinstance(c,Plain)))
            return
        if event.get_extra('qq_web_expired'):
            event.clear_result();event.stop_event();return
        if getattr(self,'output',{}).get('delivery_mode')!='adaptive' or not event.get_extra('qq_delivery_key'):
            return
        # Always take over this model event, even if the hook/SDK failed to prepare a plan.
        event.clear_result()
        key=event.get_extra('qq_delivery_key')
        plan=event.get_extra('qq_delivery_plan')
        if plan is None:
            if event.get_extra('qq_delivery_handled'):return
            event.set_extra('qq_delivery_handled',True)
            self.tasks.set(key,'failed')
            if self.delivery_allowed(event):
                # No model result is trusted here. Local error remains one short message.
                if guard:await self.local_notice(event,'这条没有生成可发送的回答，请稍后再试。')
                else:
                    try:await cancellable(event.send(event.plain_result('这条没有生成可发送的回答，请稍后再试。')),lambda:self.delivery_allowed(event),3)
                    except Exception:pass
            return
        if guard:
            with guard.grant():await self.delivery.send(event,key,plan)
        else:await self.delivery.send(event,key,plan)

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_group(self,event:AstrMessageEvent):
        if (stopping(self.root) or event.is_private_chat() or str(event.get_self_id())!=self.bot or str(event.get_group_id()) not in self.groups or
            str(event.get_sender_id()) in self.blocked or str(event.get_sender_id())==self.bot):
            event.should_call_llm(False);event.stop_event();return
        event.set_extra('qq_send_guard',EventSendGuard(event))
        # Framework otherwise adds SendMessageToUserTool even for explicit requests.
        # Copy metadata on this event only; never mutate the adapter's shared object.
        event.platform_meta=replace(event.platform_meta,support_proactive_message=False)
        event.set_extra('qq_delivery_version',self.persona_id)
        event.set_extra('qq_delivery_identity',(str(event.get_self_id()),str(event.get_group_id()),str(event.get_sender_id())))
        if self.participation['mode']=='free':
            async for item in self.on_free_group(event):yield item
        else:
            async for item in self.on_mentions(event):yield item

    async def on_mentions(self,event):
        if stopping(self.root):
            event.should_call_llm(False);event.stop_event();return
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
            if stopping(self.root):
                self.tasks.set(key,'failed');return
            self.tasks.set(key,'running')
            if any(not isinstance(c,(At,AtAll,Plain,Reply)) for c in components):
                self.tasks.set(key,'failed');yield event.plain_result('目前只接通文字聊天，图片、音频和视频还没接入。');return
            prompt=''.join(c.text for c in components if isinstance(c,Plain)).strip()
            if not prompt:
                self.tasks.set(key,'failed');yield event.plain_result('我在~ 带上想问的文字再叫我吧。');return
            if re.search(r'https?://\S+',prompt,re.I) and not self.web['enabled']:
                self.tasks.set(key,'failed');yield event.plain_result('网页读取尚未开启，视频正文还没接入。贴段文字，我先帮你捋捋。');return
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
            if self.tasks.quarantined(umo,cid):
                self.tasks.set(key,'failed')
                yield event.plain_result('这个会话的发送历史需要本机核对，暂时不能继续。');return
            history=json.loads(conv.history or '[]')
            history=self.budget.select_history(self.persona,prompt,history)
            await manager.update_conversation(umo,cid,history=history)
            conv.history=json.dumps(history,ensure_ascii=False)
            if self.output['delivery_mode']=='adaptive':
                event.set_extra('qq_delivery_key',key)
                event.set_extra('qq_delivery_cid',cid)
                event.set_extra('qq_delivery_before',history)
                event.set_extra('qq_delivery_version',self.persona_id)
                event.set_extra('qq_delivery_identity',(str(event.get_self_id()),str(event.get_group_id()),str(event.get_sender_id())))
            LOG.warning('QQ_TASK_RUNNING trace=%s',trace)
            try:
                yield event.request_llm(prompt=prompt,conversation=conv,tool_set=None)
            finally:
                if self.output['delivery_mode']=='adaptive':
                    row=self.tasks.delivery(key)
                    if row:
                        await self.tasks.repair_delivery(key,manager)
                        status=self.tasks.db.execute('SELECT status FROM tasks WHERE message_key=?',(key,)).fetchone()[0]
                    else:
                        status='failed';self.tasks.set(key,status)
                elif event.get_extra('qq_web_expired'):
                    status='failed';self.tasks.set(key,status)
                else:
                    sent=bool(getattr(event,'_has_send_oper',False))
                    success=event.get_extra('qq_router_success')
                    status='completed' if success and sent else ('failed' if not success and sent else 'send_unknown')
                    self.tasks.set(key,status)
                LOG.warning('QQ_TASK_FINAL trace=%s status=%s',trace,status)
        except Exception:
            self.tasks.set(key,'failed')
            LOG.error('QQ_ROUTER_ERROR trace=%s',trace)
            if not event.get_extra('qq_delivery_key') and not getattr(event,'_has_send_oper',False):yield event.plain_result('这条没处理好，请稍后再试。（追踪'+trace+'）')
        finally:lease.release()

    async def on_free_group(self,event):
        event.should_call_llm(False)
        components=event.get_messages()
        mention=any(isinstance(c,At) and str(c.qq)==self.bot for c in components)
        group=str(event.get_group_id());sender=str(event.get_sender_id())
        # Observe only current gate connection. Losing it invalidates every RAM snapshot.
        connection=self.connection()
        if connection!=self.connection_id:
            self.group_turns.invalidate();self.connection_id=connection
        raw=getattr(event.message_obj,'raw_message',None)
        get=raw.get if hasattr(raw,'get') else lambda k,d=None:d
        if connection is None or get('qqbot_connection',connection)!=connection:
            event.stop_event();return
        trace=uuid.uuid4().hex[:10]
        key=self.bot+':'+group+':'+str(event.message_obj.message_id)
        if not self.tasks.accept(key,trace):event.stop_event();return
        event.set_extra('qq_router_trace',trace)
        prompt=''.join(c.text for c in components if isinstance(c,Plain)).strip()
        media=get('qqbot_media',False) or any(not isinstance(c,(Plain,At,AtAll,Reply)) for c in components)
        reference=get('qqbot_reference') or next((str(c.id) for c in components if isinstance(c,Reply)),None)
        # Remove all attachment/Reply components before AstrBot can expand/download them.
        event.message_obj.message=[c for c in components if isinstance(c,(Plain,At,AtAll))]
        event.message_obj.raw_message=None
        event.set_extra('qq_connection',connection)
        created=time.monotonic();event.set_extra('qq_group_created',created)
        if mention:self.group_turns.preempt(group)
        if mention and prompt=='重置本群上下文':
            if sender in self.admins:
                self.group_turns.reset(group)
                await self.local_notice(event,'本群当前上下文已重置。')
            else:await self.local_notice(event,'当前只允许管理员重置本群上下文。')
            self.tasks.set(key,'completed');event.stop_event();return
        if mention and (not prompt or media and not prompt.replace('[非文本未解析]','').strip()):
            await self.local_notice(event,'我在，目前只接通文字聊天，图片、音频和视频还没接入。')
            self.tasks.set(key,'completed');event.stop_event();return
        if mention and len(prompt)>self.participation['message_max_chars']:
            await self.local_notice(event,MESSAGES['INPUT_TOO_LONG']);self.tasks.set(key,'failed');event.stop_event();return
        name=getattr(event.message_obj.sender,'nickname','')
        self.group_turns.append(group,sender,str(event.message_obj.message_id),name,prompt or '[非文本未解析]',reference)
        epoch=self.group_turns.group_epoch(group)
        target_seq=self.group_turns.window(group).seq
        def valid():
            return (not stopping(self.root) and self.connection()==connection and self.group_turns.group_epoch(group)==epoch and
                group in self.groups and sender not in self.blocked and (mention or time.monotonic()-created<=self.participation['max_ambient_age_seconds']))
        lease=None
        try:
            if self.tasks.group_blocked(group):
                if mention:await self.local_notice(event,'本群发送结果需要本机核对，暂时不能继续。')
                return
            if not mention:
                if not prompt.replace('[非文本未解析]','').strip():return
                if not await self.group_turns.batch(group,valid):return
            try:lease=await self.group_turns.acquire(group,mention,valid)
            except SessionError as error:
                if mention and error.notify:await self.local_notice(event,'这条排队已满或超时，请稍后再问。')
                return
            if not valid():return
            if self.tasks.group_blocked(group):
                if mention:await self.local_notice(event,'本群发送结果需要本机核对，暂时不能继续。')
                return
            if not mention:
                self.group_turns.window(group).evaluations.append(time.monotonic())
            snapshot=self.group_turns.snapshot(group)
            if mention and not any(r['seq']==target_seq for r in snapshot):
                await self.local_notice(event,'这条问题已超过当前上下文窗口，请再问一次。');return
            from qqbot_gateway.web_policy import intent
            w=self.group_turns.window(group)
            eligible=[r for r in snapshot if r['speaker']!='bot' and
                      (r['seq']==target_seq if mention else r['seq']>w.evaluated_seq)]
            anchor=None
            if mention or self.participation['allow_ambient_web']:
                anchor=next((r['text'] for r in reversed(eligible) if '[非文本未解析]' not in r['text'] and intent(r['text'],self.web).kind!='none'),None)
            w.evaluated_seq=w.seq
            # Cut oldest rows against the selected backend's real envelope budget.
            while snapshot:
                body=json.dumps(dict(must_reply=mention,target_seq=target_seq if mention else None,web_anchor=anchor,messages=snapshot),ensure_ascii=False,separators=(',',':'))
                try:self.budget.select_history(self.persona,body,[]);break
                except GatewayError:
                    if len(snapshot)==1:
                        if mention:await self.local_notice(event,MESSAGES['INPUT_TOO_LONG'])
                        return
                    remove=next((i for i,r in enumerate(snapshot) if not mention or r['seq']!=target_seq),None)
                    if remove is None:return
                    snapshot.pop(remove)
                    if anchor and not any(r['text']==anchor for r in snapshot):anchor=None
            if not snapshot:return
            request=dict(version=1,kind='group_turn',trigger='mention' if mention else 'ambient',must_reply=mention,
                         epoch=epoch,snapshot_digest=digest(body),request_key=digest(key))
            event.set_extra('qq_group_request',request);event.set_extra('qq_delivery_key',key)
            event.set_extra('qq_snapshot_range',[snapshot[0]['seq'],snapshot[-1]['seq']])
            event.should_call_llm(True);self.tasks.set(key,'running')
            yield event.request_llm(prompt=body,contexts=[],system_prompt=self.persona,conversation=None,tool_set=None,
                                    session_id='qqbot-group:'+json.dumps(request,separators=(',',':')))
            if mention and not event.get_extra('qq_delivery_handled'):
                # Framework failures may bypass decoration. Their direct sends were denied.
                await self.local_notice(event,'这条没处理好，请稍后再试。')
        finally:
            row=self.tasks.delivery(key)
            if row:
                self.tasks.finish_group(key)
                if self.group_turns.group_epoch(group)==epoch:
                    bubbles=json.loads(row['bubbles']);confirmed=[]
                    for index,state,mid in self.tasks.parts(key):
                        if state!='sent':break
                        confirmed.append(bubbles[index])
                        self.group_turns.confirm(group,bubbles[index],mid)
                    if confirmed and not mention:self.group_turns.window(group).spoken.append(time.monotonic())
            else:self.tasks.set(key,'failed' if mention else 'completed')
            event.clear_result();event.should_call_llm(False);event.stop_event()
            if lease:lease.release()

    async def terminate(self):
        if self.connection_watcher:
            self.connection_watcher.cancel();await asyncio.gather(self.connection_watcher,return_exceptions=True)
        self.group_turns.invalidate()
        self.tasks.close()
        ready=self.root/'state/router-ready.json'
        if ready.exists() and json.loads(ready.read_text(encoding='utf-8')).get('pid')==os.getpid():ready.unlink()
