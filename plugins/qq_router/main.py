import json
import asyncio
from dataclasses import replace
import logging
import math
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
from qqbot_gateway.config_files import load_consumer
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
        settings=load_consumer(self.root)
        from qqbot_gateway.qq_transport import resolve_transport
        from qqbot_gateway.config_files import canonical,sha
        transport=resolve_transport(settings)
        self.transport_provider=transport['provider']
        self.transport_health_ttl=transport['snowluma']['health_ttl_seconds']
        self.transport_config_digest=sha(canonical(settings))
        self.transport_instance_id=os.environ.get('QQBOT_INSTANCE_ID','')
        from qqbot_gateway.vision import require_production
        require_production(settings,root=self.root)
        self.vision=settings['vision']
        from qqbot_gateway.members import suspend_unverified,MemberClient
        from qqbot_gateway.vision import context_token
        self.members=suspend_unverified(settings);settings['members']=self.members
        self.member_client=MemberClient(f"http://127.0.0.1:{settings['onebot']['port']}/context/members",context_token(self.root)) if self.members['enabled'] else None
        self.bot=settings['bot']['qq'];self.groups=set(settings['access']['allowed_groups']);self.admins=set(settings['access']['admin_users'])
        self.blocked=set(settings['access']['blocked_users'])
        from qqbot_gateway.group_memory import MemoryStore
        self.memory=MemoryStore(self.root,self.bot,self.groups,self.blocked,self.admins,settings['memory'])
        self.output=settings['output']
        self.web=settings['web']
        self.bilibili=settings['bilibili']
        self.participation=settings['participation']
        from qqbot_gateway.meme_catalog import MemeCatalog
        self.memes=MemeCatalog(self.root,settings['memes'])
        self.persona=compose_persona((self.root/'config/persona.md').read_text(encoding='utf-8'),self.output,self.web,self.participation,settings['memes'],settings.get('vision'),settings.get('members'),settings['memory'],settings.get('bilibili'))
        self.persona_id=session_version(self.persona+('\n'+self.memes.fingerprint() if self.memes.cfg['enabled'] else ''),settings)
        chat=settings.get('chat',{})
        self.budget=InputBudget.from_settings(settings,validate_model_settings(settings))
        self.coordinator=SessionCoordinator(chat.get('user_cooldown_seconds',5),chat.get('session_queue_limit',2),chat.get('session_queue_timeout_seconds',600))
        self.tasks=TaskStore(self.root/'state/tasks.sqlite')
        self.delivery=ReplyDelivery(self.tasks,self.output,self.delivery_allowed,catalog=self.memes,members=self.member_client)
        self.attention_effective=self.participation['mode']=='free' and self.participation['attention']['enabled']
        from qqbot_gateway.attention import Attention
        self.group_turns=(Attention if self.attention_effective or self.vision['enabled'] or self.members['enabled'] or self.memory.cfg['enabled'] or self.bilibili['enabled'] else Participation)(self.participation,digest(self.persona_id+uuid.uuid4().hex),settings['llm']['queue_limit'],chat.get('session_queue_timeout_seconds',600))
        self.group_turns.bot=self.bot
        self.connection_id=None
        self.connection_watcher=None
        self.silence_mirror=None

    def gate_metadata(self):
        try:
            data=json.loads((self.root/'state/gate-connection.json').read_text(encoding='utf-8'))
            process=psutil.Process(data['pid'])
            if abs(process.create_time()-data['created'])>=.01 or not 0<=time.time()-data['updated']<=45:return None
            if getattr(self,'transport_provider','napcat')=='snowluma':
                if (data.get('provider')!='snowluma' or data.get('channel_ready') is not True or
                    not self.transport_instance_id or data.get('instance_id')!=self.transport_instance_id or
                    data.get('config_digest')!=self.transport_config_digest or
                    data.get('good') is not True or type(data.get('online_at')) not in (int,float) or
                    not 0<=time.time()-data['online_at']<45):return None
            if self.silence_enabled():
                from qqbot_gateway.group_silence import group_ref
                mirror=data.get('silence')
                if (not isinstance(mirror,dict) or type(mirror.get('v')) is not int or mirror['v']!=1 or
                    mirror.get('enabled') is not True or not isinstance(mirror.get('boot_id'),str) or
                    not re.fullmatch('[a-f0-9]{32}',mirror['boot_id']) or not isinstance(mirror.get('groups'),dict) or
                    set(mirror['groups'])!={group_ref(self.bot,g) for g in self.groups}):return None
                for state in mirror['groups'].values():
                    if (not isinstance(state,dict) or set(state)!={'mode','generation'} or state['mode'] not in ('normal','muted') or
                        type(state['generation']) is not int or state['generation']<0):return None
            return data if data['connected'] and data['online'] is True else None
        except (OSError,ValueError,TypeError,KeyError,psutil.Error):return None

    def connection(self):
        data=self.gate_metadata()
        return data['id'] if data else None

    def silence_enabled(self):return self.participation.get('silence',{}).get('enabled',True)

    def transport_allowed(self,event):
        if getattr(self,'transport_provider','napcat')!='snowluma':return True
        connection=self.connection()
        raw=getattr(event.message_obj,'raw_message',None)
        original=event.get_extra('qq_transport_connection')
        if original is None and isinstance(raw,dict):original=raw.get('qqbot_connection')
        return bool(connection and original==connection)

    def silence_allowed(self,event):
        if not self.transport_allowed(event):return False
        if not self.silence_enabled():return True
        from qqbot_gateway.group_silence import decode_ticket,group_ref
        try:
            d,_,_=decode_ticket(event.get_extra('qq_output_ticket'))
            data=self.gate_metadata();mirror=data['silence']
            state=mirror['groups'][group_ref(self.bot,str(event.get_group_id()))]
            return (mirror['v']==1 and mirror['enabled'] is True and d['boot_id']==mirror['boot_id'] and
                d['connection_id']==data['id'] and d['bot']==self.bot and d['group']==str(event.get_group_id()) and
                d['sender']==str(event.get_sender_id()) and d['message_id']==str(event.message_obj.message_id) and
                type(state['generation']) is int and d['generation']==state['generation'] and state['mode']=='normal' and
                d['expires_ms']>=int(time.monotonic()*1000))
        except (ValueError,TypeError,KeyError):return False

    def observe_gate(self):
        data=self.gate_metadata();current=data['id'] if data else None
        mirror=data.get('silence') if data else None
        if current!=self.connection_id:
            self.group_turns.invalidate();self.connection_id=current
        elif self.silence_enabled() and mirror!=self.silence_mirror:
            from qqbot_gateway.group_silence import group_ref
            for group in self.groups:
                ref=group_ref(self.bot,group)
                old=self.silence_mirror;new=mirror
                if not old or not new or old.get('boot_id')!=new.get('boot_id') or old.get('groups',{}).get(ref)!=new.get('groups',{}).get(ref):
                    self.group_turns.reset(group)
        self.silence_mirror=mirror

    async def watch_connection(self):
        # RAM invalidation only; never cancels submitted HTTP or runner/SSH work.
        while True:
            self.observe_gate()
            await asyncio.sleep(.1)

    @filter.on_llm_request()
    async def before_provider(self,event,request):
        QQBotProvider._output_gate.set(dict(valid=lambda:self.silence_allowed(event),submitted=False))
        if not self.silence_allowed(event):event.should_call_llm(False);event.stop_event()

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
        if self.participation['mode']=='free' or self.silence_enabled() or self.transport_provider=='snowluma':self.connection_watcher=asyncio.create_task(self.watch_connection())
        manager=self.context.persona_manager
        try:await manager.get_persona(self.persona_id)
        except ValueError:
            await manager.create_persona(self.persona_id,self.persona,tools=[],skills=[])
        else:
            await manager.update_persona(self.persona_id,system_prompt=self.persona,tools=[],skills=[])
        (self.root/'state/router-ready.json').write_text(json.dumps({'pid':os.getpid(),'created':psutil.Process().create_time(),'time':time.time(),'persona_id':self.persona_id,'instance_id':os.environ.get('QQBOT_INSTANCE_ID'),'config_digest':os.environ.get('QQBOT_CONFIG_DIGEST')}),encoding='utf-8')
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
                plan=verify_metadata(getattr(raw,'qqbot_group_plan',None),request,raw.id,text,self.output,event.get_extra('qq_v2_source'))
                event.set_extra('qq_group_response',raw.id)
                event.set_extra('qq_group_metadata',raw.qqbot_group_plan)
                event.set_extra('qq_delivery_plan',plan)
                self.stage_memory(event,raw.qqbot_group_plan)
                response.result_chain=MessageChain()
                response.reasoning_content=None
                if request['kind']=='member_turn':
                    # Preserve the old personal UMO/history contract: image refs,
                    # caps and source JSON must never enter saved history.
                    users=[m for m in run_context.messages if m.role=='user']
                    if users:users[-1].content=[TextPart(text=event.get_extra('qq_delivery_question'))]
                    if run_context.messages and run_context.messages[-1].role=='assistant':
                        run_context.messages[-1].content=[TextPart(text=text)]
                else:
                    for message in run_context.messages:message._no_save=True
                if plan:
                    key=event.get_extra('qq_delivery_key')
                    if request['kind']=='member_turn':
                        expected=[m.model_dump() for m in run_context.messages if m.role!='system' and not m._no_save]
                        self.tasks.prepare_delivery(key,event.unified_msg_origin,event.get_extra('qq_delivery_cid'),raw.id,plan,event.get_extra('qq_delivery_before'),expected)
                    else:
                        self.tasks.prepare_group_delivery(key,str(event.get_group_id()),request['epoch'],
                            raw.id,plan,request.get('source_digest',request.get('snapshot_digest')),event.get_extra('qq_snapshot_range'))
                    row=self.tasks.delivery(key)
                    if row['response_id']!=raw.id or row['content_sha256']!=digest(plan.canonical_text) or tuple(json.loads(row['bubbles']))!=plan.bubbles:
                        raise ValueError('Group response changed during hook reentry')
            except Exception:
                event.set_extra('qq_group_invalid',True)
                event.set_extra('qq_delivery_plan',None)
                response.result_chain=MessageChain()
                for message in run_context.messages:message._no_save=True
            # AstrBot skips result decoration for an empty chain. Keep a verified
            # text carrier so the normal hook can perform ledger/ACK delivery.
            # Silent/invalid results have no carrier and must finish here.
            plan=event.get_extra('qq_delivery_plan')
            if plan:response.result_chain=MessageChain().message(plan.canonical_text)
            else:await self.deliver_reply(event)
            return
        if response.role!='assistant':
            event.set_extra('qq_router_success',False)
            return
        raw=response.raw_completion
        if (raw is None or raw.model!='workbuddy-local' or
                not raw.id.startswith('chatcmpl-') or len(raw.choices)!=1):
            if (getattr(self,'output',{}).get('delivery_mode')=='adaptive' or event.get_extra('qq_media_turn') or event.get_extra('needs_guarded_delivery')) and event.get_extra('qq_delivery_key'):
                response.result_chain=MessageChain()
                if run_context.messages and run_context.messages[-1].role=='assistant':run_context.messages[-1]._no_save=True
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
            if (getattr(self,'output',{}).get('delivery_mode')=='adaptive' or event.get_extra('qq_media_turn') or event.get_extra('needs_guarded_delivery')) and event.get_extra('qq_delivery_key'):
                response.result_chain=MessageChain()
                if run_context.messages and run_context.messages[-1].role=='assistant':run_context.messages[-1]._no_save=True
                event.clear_result();event.stop_event()
            return
        response.result_chain=MessageChain().message(text)
        response.reasoning_content=None
        if run_context.messages and run_context.messages[-1].role=='assistant':
            run_context.messages[-1].content=[TextPart(text=text)]
        event.set_extra('qq_router_success',True)
        if (getattr(self,'output',{}).get('delivery_mode')=='adaptive' or event.get_extra('qq_media_turn') or event.get_extra('needs_guarded_delivery')) and event.get_extra('qq_delivery_key'):
            # Persist before the framework can either save history or dispatch a result.
            try:
                key=event.get_extra('qq_delivery_key')
                plan=trusted_plan(getattr(raw,'qqbot_reply_plan',None),text,raw.id,self.output)
                if event.get_extra('qq_media_turn') and plan.fallback_reason=='metadata_missing_or_mismatch':raise ValueError('Missing media identity')
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
                if (event.get_extra('qq_media_turn') or event.get_extra('needs_guarded_delivery')) and run_context.messages and run_context.messages[-1].role=='assistant':
                    run_context.messages[-1]._no_save=True
                    run_context.messages[-1].content=[]
                event.clear_result();event.stop_event()
                LOG.error('QQ_DELIVERY_PREPARE_FAILED')

    def delivery_allowed(self,event):
        group_request=event.get_extra('qq_group_request')
        group_ok=(not group_request or (group_request['epoch']==self.group_turns.group_epoch(str(event.get_group_id())) and
            not self.tasks.group_blocked(str(event.get_group_id())) and
            event.get_extra('qq_connection')==self.connection() and
            (group_request['must_reply'] or (time.monotonic()-event.get_extra('qq_group_created')<=self.participation['max_ambient_age_seconds'] and (group_request.get('addressing')=='focused_candidate' or self.group_turns.may_speak(str(event.get_group_id())))))))
        return (self.silence_allowed(event) and group_ok and not stopping(self.root) and str(event.get_self_id())==self.bot and
                str(event.get_group_id()) in self.groups and str(event.get_sender_id()) not in self.blocked and
                str(event.get_sender_id())!=self.bot and event.get_extra('qq_delivery_version')==self.persona_id and
                event.get_extra('qq_delivery_identity')==(str(event.get_self_id()),str(event.get_group_id()),str(event.get_sender_id())))

    def memory_allowed(self,event):
        request=event.get_extra('qq_group_request')
        return (self.silence_allowed(event) and request and request.get('version')==2 and not stopping(self.root) and str(event.get_self_id())==self.bot and
            str(event.get_group_id()) in self.groups and str(event.get_sender_id()) not in self.blocked and
            request['epoch']==self.group_turns.group_epoch(str(event.get_group_id())) and
            event.get_extra('qq_connection')==self.connection() and event.get_extra('qq_delivery_version')==self.persona_id and
            event.get_extra('qq_delivery_identity')==(self.bot,str(event.get_group_id()),str(event.get_sender_id())))

    def prepare_memory(self,event,source,identities,events,request_key):
        context=self.memory.prepare(str(event.get_group_id()),request_key,source,identities,events)
        event.set_extra('qq_memory_context',context)

    def stage_memory(self,event,metadata):
        if not getattr(self,'memory',None) or not self.memory_allowed(event) or event.get_extra('qq_memory_staged'):return
        event.set_extra('qq_memory_staged',True)
        from copy import deepcopy
        from qqbot_gateway.turn_v2 import close_refs
        effective=deepcopy(event.get_extra('qq_v2_source'));manifest=metadata['manifest']
        effective['messages']=[r for r in effective['messages'] if r['seq'] in manifest['seqs']]
        close_refs(effective);effective['memory']=manifest.get('memory');effective['member_candidates']=manifest.get('member_candidates',[])
        self.memory.stage(event.get_extra('qq_memory_context'),metadata.get('memory_proposals',[]),effective)

    def close_memory(self,event):
        context=event.get_extra('qq_memory_context')
        if context:
            acks=self.tasks.parts(event.get_extra('qq_delivery_key')) if self.memory_allowed(event) and not event.get_extra('qq_group_invalid') else ()
            self.memory.close(context,acks)

    @filter.on_decorating_result()
    async def deliver_reply(self,event:AstrMessageEvent):
        guard=event.get_extra('qq_send_guard')
        if event.get_extra('qq_group_request'):
            event.clear_result()
            if event.get_extra('qq_delivery_handled'):return
            request=event.get_extra('qq_group_request');plan=event.get_extra('qq_delivery_plan');key=event.get_extra('qq_delivery_key')
            if plan:
                try:verify_metadata(event.get_extra('qq_group_metadata'),request,event.get_extra('qq_group_response'),plan.canonical_text,self.output,event.get_extra('qq_v2_source'))
                except Exception:plan=None;event.set_extra('qq_group_invalid',True)
            if plan and self.delivery_allowed(event):
                if request['version']==2:event.set_extra('qq_v2_delivery_started',time.monotonic())
                with guard.grant():await self.delivery.send(event,key,plan)
                await self.failed_image_notice(event,key,plan)
            else:
                event.set_extra('qq_delivery_handled',True)
                if request['must_reply'] and not getattr(self,'members',{}).get('enabled') and (event.get_extra('qq_group_invalid') or not event.get_extra('qq_group_metadata')):
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
        if (getattr(self,'output',{}).get('delivery_mode')!='adaptive' and not event.get_extra('qq_media_turn') and not event.get_extra('needs_guarded_delivery')) or not event.get_extra('qq_delivery_key'):
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
        await self.failed_image_notice(event,key,plan)

    async def failed_image_notice(self,event,key,plan):
        request=event.get_extra('qq_group_request')
        if (len(plan.parts)==1 and plan.parts[0].type=='image' and
            (not request or request['must_reply']) and self.tasks.parts(key)[0][1]=='failed' and
            not event.get_extra('qq_image_notice')):
            event.set_extra('qq_image_notice',True)
            await self.local_notice(event,'这张表情暂时发不了。')

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_group(self,event:AstrMessageEvent):
        if (stopping(self.root) or event.is_private_chat() or str(event.get_self_id())!=self.bot or str(event.get_group_id()) not in self.groups or
            str(event.get_sender_id()) in self.blocked or str(event.get_sender_id())==self.bot):
            event.should_call_llm(False);event.stop_event();return
        self.observe_gate()
        raw=getattr(event.message_obj,'raw_message',None)
        snow=getattr(self,'transport_provider','napcat')=='snowluma'
        if snow:event.set_extra('qq_transport_connection',raw.get('qqbot_connection') if isinstance(raw,dict) else None)
        # The same signed event ticket also fences Snow epochs when muting is off.
        event.set_extra('qq_silence_enabled',self.silence_enabled() or snow)
        event.set_extra('qq_output_ticket',raw.get('qqbot_output_ticket') if isinstance(raw,dict) else None)
        event.set_extra('needs_guarded_delivery',self.silence_enabled() or snow)
        if not self.silence_allowed(event):
            event.should_call_llm(False);event.stop_event();return
        event.set_extra('qq_send_guard',EventSendGuard(event))
        # Framework otherwise adds SendMessageToUserTool even for explicit requests.
        # Copy metadata on this event only; never mutate the adapter's shared object.
        event.platform_meta=replace(event.platform_meta,support_proactive_message=False)
        event.set_extra('qq_delivery_version',self.persona_id)
        event.set_extra('qq_delivery_identity',(str(event.get_self_id()),str(event.get_group_id()),str(event.get_sender_id())))
        if self.attention_effective or (self.vision['enabled'] or self.members['enabled'] or self.memory.cfg['enabled'] or self.bilibili['enabled']) and self.participation['mode']=='free':
            async for item in self.on_attention_group(event):yield item
        elif self.participation['mode']=='free':
            async for item in self.on_free_group(event):yield item
        else:
            async for item in self.on_mentions(event):yield item

    async def on_mentions(self,event):
        if stopping(self.root) or not self.transport_allowed(event):
            event.should_call_llm(False);event.stop_event();return
        if (str(event.get_self_id())!=self.bot or str(event.get_group_id()) not in self.groups or
                str(event.get_sender_id())==self.bot or str(event.get_sender_id()) in self.blocked):
            event.should_call_llm(False);event.stop_event();return
        components=event.get_messages()
        raw=getattr(event.message_obj,'raw_message',None)
        image=raw.get('qqbot_image') if isinstance(raw,dict) and self.vision['enabled'] else None
        media=raw.get('qqbot_media',False) if isinstance(raw,dict) else False
        if not any(isinstance(c,At) and str(c.qq)==self.bot for c in components):
            event.should_call_llm(False);event.stop_event();return
        event.should_call_llm(True)
        trace=uuid.uuid4().hex[:10];event.set_extra('qq_router_trace',trace)
        key=self.bot+':'+str(event.get_group_id())+':'+str(event.message_obj.message_id)
        if not self.tasks.accept(key,trace):return
        try:lease=await self.coordinator.acquire(event.unified_msg_origin,lambda:self.silence_allowed(event))
        except SessionError as error:
            self.tasks.set(key,'failed')
            if error.code=='INVALIDATED':event.should_call_llm(False);event.stop_event()
            if error.notify:
                texts={'COOLDOWN':'上一条还在处理，等几秒再叫我吧。','SESSION_QUEUE_FULL':'你这边还有问题排着队，稍后再试。','SESSION_QUEUE_TIMEOUT':'这条问题排队超时了，请重新提问。'}
                yield event.plain_result(texts[error.code])
            return
        try:
            if stopping(self.root) or not self.silence_allowed(event):
                event.should_call_llm(False);event.stop_event();self.tasks.set(key,'failed');return
            self.tasks.set(key,'running')
            if any(not isinstance(c,(At,AtAll,Plain,Reply)) for c in components) or media and not image:
                self.tasks.set(key,'failed');yield event.plain_result('目前只接通文字聊天，图片、音频和视频还没接入。');return
            prompt=''.join(c.text for c in components if isinstance(c,Plain)).strip()
            if image:prompt=raw.get('qqbot_text','').strip() or '[当前消息含图片]'
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
            if event.get_extra('needs_guarded_delivery') or self.output['delivery_mode']=='adaptive' or self.memes.cfg['enabled'] or self.vision['enabled'] or self.members['enabled'] or self.memory.cfg['enabled'] or self.bilibili['enabled']:
                event.set_extra('qq_delivery_key',key)
                event.set_extra('qq_delivery_cid',cid)
                event.set_extra('qq_delivery_before',history)
                event.set_extra('qq_delivery_version',self.persona_id)
                event.set_extra('qq_delivery_identity',(str(event.get_self_id()),str(event.get_group_id()),str(event.get_sender_id())))
            if self.memes.cfg['enabled']:event.set_extra('qq_media_turn',True)
            session_id='qqbot-media' if event.get_extra('qq_media_turn') else None
            if self.vision['enabled'] or self.members['enabled'] or self.memory.cfg['enabled'] or self.bilibili['enabled']:
                from qqbot_gateway.vision import member_source,attach_image
                from qqbot_gateway.turn_v2 import sha
                from qqbot_gateway.attention import canonical
                trace=uuid.uuid4().hex;event.set_extra('qq_router_trace',trace)
                source=member_source(prompt,self.participation['attention']['aliases'])
                ref=source['messages'][0]['member_ref']
                self.prepare_memory(event,source,{ref:str(event.get_sender_id())},
                    {1:(str(event.get_sender_id()),str(event.message_obj.message_id),time.time())},digest(key))
                if image:attach_image(source,image)
                from qqbot_gateway.web_policy import intent
                if intent(prompt,self.web).kind!='none':source['web_anchor']=prompt
                request=dict(version=2,kind='member_turn',mode='mentions',request_key=digest(key),epoch=self.group_turns.group_epoch(str(event.get_group_id())),
                    config_version=digest(self.persona_id),source_digest=sha(source),addressing='mention',must_reply=True,target_seq=1,resource_caps=[image['cap']] if image else [])
                member_cap=raw.get('qqbot_member_cap') if isinstance(raw,dict) and self.members['enabled'] else None
                if member_cap:request['resource_caps'].append(member_cap)
                from qqbot_gateway.turn_v2 import fit
                history=self.budget.select_history(self.persona,canonical(source),history)
                await manager.update_conversation(umo,cid,history=history)
                conv.history=json.dumps(history,ensure_ascii=False);event.set_extra('qq_delivery_before',history)
                source=json.loads(fit(source,request,self.persona,self.budget,history=history))
                request['source_digest']=sha(source)
                event.set_extra('qq_group_request',request);event.set_extra('qq_v2_source',source)
                event.set_extra('qq_connection',self.connection());event.set_extra('qq_group_created',time.monotonic())
                event.set_extra('qq_delivery_question',prompt);event.set_extra('qq_snapshot_range',[1,1])
                event.set_extra('qq_media_turn',True)
                session_id='qqbot-v2:'+canonical(dict(request=request,trace=trace))
                prompt=canonical(source)
                # No framework attachment conversion/download, including quote expansion.
                event.message_obj.message=[c for c in components if isinstance(c,Plain)]
                event.message_obj.raw_message=None
            event.set_extra('qq_meme_question',prompt)
            LOG.warning('QQ_TASK_RUNNING trace=%s',trace)
            try:
                if not self.silence_allowed(event):event.should_call_llm(False);event.stop_event();return
                yield event.request_llm(prompt=prompt,conversation=conv,tool_set=None,session_id=session_id)
            finally:
                if self.output['delivery_mode']=='adaptive' or event.get_extra('qq_media_turn') or event.get_extra('needs_guarded_delivery'):
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
        finally:
            self.close_memory(event)
            lease.release()

    async def on_attention_group(self,event):
        if not self.transport_allowed(event):event.should_call_llm(False);event.stop_event();return
        from qqbot_gateway.attention import DIRECT,canonical
        from qqbot_gateway.turn_v2 import sha,fit
        event.should_call_llm(False)
        components=event.get_messages();group=str(event.get_group_id());sender=str(event.get_sender_id())
        connection=self.connection()
        if connection!=self.connection_id:
            self.group_turns.invalidate();self.connection_id=connection
        raw=getattr(event.message_obj,'raw_message',None)
        get=raw.get if hasattr(raw,'get') else lambda k,d=None:d
        image=get('qqbot_image') if self.vision['enabled'] else None
        member_cap=get('qqbot_member_cap') if self.members['enabled'] else None
        if connection is None or get('qqbot_connection',connection)!=connection:event.stop_event();return
        trace=uuid.uuid4().hex;key=self.bot+':'+group+':'+str(event.message_obj.message_id)
        if not self.tasks.accept(key,trace):event.stop_event();return
        event.set_extra('qq_router_trace',trace);event.set_extra('qq_connection',connection)
        created=time.monotonic();event.set_extra('qq_group_created',created)
        LOG.info('ATTENTION trace=%s stage=received config=%s',trace,self.persona_id)
        prompt=''.join(c.text for c in components if isinstance(c,Plain)).strip()
        if image:prompt=get('qqbot_text','').strip()
        ats=get('qqbot_at_ids') or [str(c.qq) for c in components if isinstance(c,At)]
        if any(isinstance(c,At) and str(c.qq)==self.bot for c in components) and self.bot not in ats:ats=[self.bot]+ats
        reference=get('qqbot_reference') or next((str(c.id) for c in components if isinstance(c,Reply)),None)
        event.message_obj.message=[c for c in components if isinstance(c,Plain)]
        event.message_obj.raw_message=None
        mention=self.bot in ats
        if mention and prompt=='重置本群上下文':
            if sender in self.admins:self.group_turns.reset(group);await self.local_notice(event,'本群当前上下文已重置。')
            else:await self.local_notice(event,'当前只允许管理员重置本群上下文。')
            self.tasks.set(key,'completed');event.stop_event();return
        row,addressing,required=self.group_turns.observe(group,sender,str(event.message_obj.message_id),
            getattr(event.message_obj.sender,'nickname',''),prompt or '[非文本未解析]',ats,reference)
        row['memory_received_at']=time.time()
        if not self.attention_effective:
            addressing='mention' if mention else 'ambient';required={row['seq']}
        has_text=bool(prompt.replace('[非文本未解析]','').strip())
        if not has_text and not image or len(prompt)>self.participation['message_max_chars']:
            LOG.info('ATTENTION trace=%s stage=filtered reason=unsupported_or_oversized_text',trace)
            if mention:await self.local_notice(event,MESSAGES['INPUT_TOO_LONG'] if has_text else '我在，目前只接通文字聊天。')
            self.tasks.set(key,'failed');event.stop_event();return
        epoch=self.group_turns.group_epoch(group);direct=addressing in DIRECT;ticket=None;lease=None
        LOG.info('ATTENTION trace=%s stage=attention_reason addressing=%s',trace,addressing)
        def valid():
            return (self.silence_allowed(event) and not stopping(self.root) and self.connection()==connection and self.group_turns.group_epoch(group)==epoch and
                group in self.groups and sender not in self.blocked and
                (direct or time.monotonic()-created<=min(90,self.participation['max_ambient_age_seconds'])))
        try:
            ticket=self.group_turns.freeze(group,addressing,row,required,trace)
            ticket.memory_event=(sender,str(event.message_obj.message_id),row['memory_received_at'])
            # Keep the cap with the frozen target, outside model material. Ambient
            # merging must replace both together, never reuse the carrier image.
            ticket.image=dict(image) if image else None
            ticket.member_cap=member_cap
            if member_cap:ticket.size+=len(member_cap)
            if image:
                ticket.size+=len(canonical(image).encode('utf-8'))
                if ticket.size>32768:raise SessionError('SESSION_QUEUE_FULL')
            if addressing=='ambient':
                pending=next((t for t in self.group_turns.pending if t.group==group and t.addressing=='ambient' and not t.cancelled),None)
                if pending:
                    # The original owner will dispatch the merged newest ambient target.
                    if sum(t.size for t in self.group_turns.pending)-pending.size+ticket.size<=262144:
                        pending.source=ticket.source;pending.required=ticket.required;pending.size=ticket.size
                        pending.identities=ticket.identities
                        pending.image=ticket.image
                        pending.member_cap=ticket.member_cap
                        pending.received=ticket.received
                        pending.memory_event=ticket.memory_event
                        LOG.info('ATTENTION trace=%s stage=merged owner_trace=%s',trace,pending.trace)
                    return
                if not await self.group_turns.batch(group,valid):return
            lease=await self.group_turns.dispatch(ticket,valid)
            if not valid() or self.tasks.group_blocked(group):return
            if addressing=='ambient':self.group_turns.window(group).evaluations.append(time.monotonic())
            source=self.group_turns.rebuild(ticket)
            image=ticket.image
            # One concrete allowed anchor, never a serialized window/history.
            target=next(r for r in source['messages'] if r['seq']==source['target_seq'])
            state=self.group_turns.state(group)
            eligible=[target] if direct else [r for r in source['messages'] if r['seq'] in source['eligible_seq'] and r['seq']>state.web_evaluated_seq]
            from qqbot_gateway.web_policy import intent
            if direct or self.participation['allow_ambient_web']:
                source['web_anchor']=next((r['text'] for r in reversed(eligible) if intent(r['text'],self.web).kind!='none'),None)
            source['meme_question']=target['text']
            rows={r['seq']:r for r in self.group_turns.window(group).rows}
            now=time.time();mono=time.monotonic()
            events={seq:(r['sender'],r['mid'],r.get('memory_received_at',now-(mono-r['at']))) for seq,r in rows.items() if r['sender']!='bot'}
            # Frozen target can outlive the ordinary RAM window.
            if target['seq'] not in events:events[target['seq']]=ticket.memory_event
            self.prepare_memory(event,source,ticket.identities,events,digest(key))
            if image:
                from qqbot_gateway.vision import attach_image
                attach_image(source,image)
            if eligible:state.web_evaluated_seq=max(state.web_evaluated_seq,max(r['seq'] for r in eligible))
            request=dict(version=2,kind='group_turn',mode='free',request_key=digest(key),epoch=epoch,
                config_version=digest(self.persona_id),source_digest=sha(source),addressing=addressing,must_reply=direct,
                target_seq=target['seq'],resource_caps=[image['cap']] if image else [])
            from qqbot_gateway.turn_budget import candidate_instruction
            suffix=candidate_instruction([]) if self.memes.cfg['enabled'] else ''
            body=fit(source,request,self.persona,self.budget,suffix)
            source=json.loads(body);request['source_digest']=sha(source)
            if ticket.member_cap:request['resource_caps'].append(ticket.member_cap)
            ticket.source=source
            event.set_extra('qq_v2_source',source);event.set_extra('qq_group_request',request)
            event.set_extra('qq_delivery_key',key);event.set_extra('qq_meme_question',source['meme_question'] or '')
            event.set_extra('qq_snapshot_range',[source['messages'][0]['seq'],source['messages'][-1]['seq']])
            self.tasks.set(key,'running');event.should_call_llm(True)
            if not self.silence_allowed(event):event.should_call_llm(False);event.stop_event();return
            yield event.request_llm(prompt=body,contexts=[],system_prompt=self.persona,conversation=None,tool_set=None,
                session_id='qqbot-v2:'+canonical(dict(request=request,trace=trace)))
            if direct and not event.get_extra('qq_delivery_handled'):await self.local_notice(event,'这条没处理好，请稍后再试。')
        except (SessionError,GatewayError) as error:
            LOG.info('ATTENTION trace=%s stage=filtered reason=%s',trace,error.code)
            if direct and getattr(error,'notify',True):await self.local_notice(event,'这条排队已满、超时或超过输入限制，请稍后再问。')
        except asyncio.CancelledError:
            LOG.info('ATTENTION trace=%s stage=filtered reason=cancelled',trace)
            raise
        except Exception:
            LOG.error('ATTENTION trace=%s stage=filtered reason=framework_error',trace)
            raise
        finally:
            try:
                delivery=self.tasks.delivery(key)
                if delivery:
                    self.tasks.finish_group(key)
                    metadata=event.get_extra('qq_group_metadata');plan=event.get_extra('qq_delivery_plan')
                    if (lease and plan and metadata and metadata['decision']=='speak' and not plan.fallback_reason and
                        self.group_turns.group_epoch(group)==epoch):
                        # Reverify identity even on abnormal framework exit before ACK attribution.
                        verify_metadata(metadata,event.get_extra('qq_group_request'),event.get_extra('qq_group_response'),
                            plan.canonical_text,self.output,event.get_extra('qq_v2_source'))
                        confirmed=[(plan.parts[i].payload_ref,mid) for i,state,mid in self.tasks.parts(key)
                            if state=='sent' and mid and plan.parts[i].type=='text']
                        ticket.source=event.get_extra('qq_v2_source')
                        self.group_turns.acknowledge(ticket,confirmed,metadata['response_to_seq'])
                        if confirmed and not direct:self.group_turns.window(group).spoken.append(time.monotonic())
                    ack_start=event.get_extra('qq_v2_delivery_started')
                    LOG.info('ATTENTION trace=%s stage=delivery status=%s ack_ms=%s',trace,delivery['state'],
                        int((time.monotonic()-ack_start)*1000) if ack_start is not None else 0)
                else:self.tasks.set(key,'failed' if direct else 'completed')
            finally:
                self.close_memory(event)
                event.clear_result();event.should_call_llm(False);event.stop_event()
                if ticket:self.group_turns.finish(ticket)

    async def on_free_group(self,event):
        if not self.transport_allowed(event):event.should_call_llm(False);event.stop_event();return
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
            return (self.silence_allowed(event) and not stopping(self.root) and self.connection()==connection and self.group_turns.group_epoch(group)==epoch and
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
            from qqbot_gateway.turn_budget import fit_snapshot,candidate_instruction
            suffix=candidate_instruction([]) if self.memes.cfg['enabled'] else ''
            try:
                body=fit_snapshot(dict(must_reply=mention,target_seq=target_seq if mention else None,
                    web_anchor=anchor,messages=snapshot),self.persona,self.budget,suffix)
            except GatewayError as error:
                if mention:await self.local_notice(event,MESSAGES[error.code])
                return
            snapshot=json.loads(body)['messages']
            request=dict(version=1,kind='group_turn',trigger='mention' if mention else 'ambient',must_reply=mention,
                         epoch=epoch,snapshot_digest=digest(body),request_key=digest(key))
            event.set_extra('qq_group_request',request);event.set_extra('qq_delivery_key',key)
            event.set_extra('qq_meme_question',next((r['text'] for r in json.loads(body)['messages'] if r['seq']==json.loads(body).get('target_seq')),''))
            event.set_extra('qq_snapshot_range',[snapshot[0]['seq'],snapshot[-1]['seq']])
            event.should_call_llm(True);self.tasks.set(key,'running')
            if not self.silence_allowed(event):event.should_call_llm(False);event.stop_event();return
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
