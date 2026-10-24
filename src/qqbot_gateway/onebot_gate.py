import argparse
import asyncio
import json
import logging
from pathlib import Path
import random
import re
import secrets
import sqlite3
import time
import os
import psutil

import aiohttp
from aiohttp import web

from .config import GateConfig, load_gate_config, qq_id
from .lifecycle import stopping

LOG = logging.getLogger(__name__)
MAX_FRAME = 1024 * 1024


class ChannelNotReady(ValueError):
    """Known rejection before the socket write; transport errors remain unknown."""


def metadata_error_code(error):
    # Fixed categories only: never log paths or arbitrary OS exception text.
    return {5:'ACCESS_DENIED',32:'SHARING_VIOLATION',33:'LOCK_VIOLATION'}.get(getattr(error,'winerror',None),'IO_ERROR')


def controllable_message(event, config):
    if not isinstance(event, dict):
        return False
    if (event.get('post_type') != 'message' or event.get('message_type') != 'group' or
            qq_id(event.get('self_id')) != config.bot_qq or
            not qq_id(event.get('user_id')) or qq_id(event.get('user_id')) == config.bot_qq or
            qq_id(event.get('user_id')) in config.blocked_users or
            qq_id(event.get('group_id')) not in config.allowed_groups):
        return False
    message = event.get('message')
    return isinstance(message, list) and bool(message) and all(isinstance(s,dict) and isinstance(s.get('type'),str) and isinstance(s.get('data'),dict) for s in message)


def admitted_message(event, config):
    return controllable_message(event,config) and (config.participation_mode=='free' or any(
        isinstance(segment, dict) and segment.get('type') == 'at' and
        isinstance(segment.get('data'), dict) and
        qq_id(segment['data'].get('qq')) == config.bot_qq
        for segment in event['message']
    ))


def allowed_action(event, config):
    if not isinstance(event, dict) or not isinstance(event.get('params', {}), dict):
        return False
    action, params = event.get('action'), event.get('params', {})
    # AstrBot resolves an empty group card through this lookup before preserving At.
    # Only the configured bot's public nickname is needed; arbitrary users stay denied.
    if action == 'get_stranger_info':
        return qq_id(params.get('user_id')) == config.bot_qq
    if action in ('get_login_info', 'get_version_info', 'get_status', 'get_group_list'):
        return True
    if action=='get_group_member_info':
        return qq_id(params.get('group_id')) in config.allowed_groups and qq_id(params.get('user_id'))==config.bot_qq
    if action=='get_group_member_list':return False
    if action in ('get_group_info', 'send_group_msg'):
        return qq_id(params.get('group_id')) in config.allowed_groups and (action!='send_group_msg' or allowed_segments(params.get('message'),config))
    if action == 'send_msg':
        return params.get('message_type') == 'group' and qq_id(params.get('group_id')) in config.allowed_groups and allowed_segments(params.get('message'),config)
    return False


def allowed_segments(message,config):
    if not isinstance(message,list) or not message or len(message)>1:return False
    for part in message:
        if not isinstance(part,dict) or set(part)!={'type','data'} or not isinstance(part['data'],dict):return False
        data=part['data']
        if part['type']=='text':
            if set(data)!={'text'} or not isinstance(data['text'],str) or '[CQ:' in data['text']:return False
        elif part['type']=='image':
            if not config.media_catalog or set(data)!={'file'} or not isinstance(data.get('file'),str):return False
            try:
                # Exact library URI + hash validation; remote/base64/other local paths denied.
                valid=False
                from .meme_catalog import controlled_path,inspect_image
                for row in config.media_catalog.rows:
                    try:
                        path,_=config.media_catalog.resolve(row['id'])
                        for candidate in (path,controlled_path(config.media_catalog.root,'state/meme-delivery/'+row['file'])):
                            if candidate.as_uri()==data['file'] and candidate.stat().st_size<=config.media_catalog.cfg['max_file_bytes'] and inspect_image(candidate.read_bytes())['sha256']==row['sha256']:valid=True
                    except (OSError,ValueError):continue
                if not valid:return False
            except (OSError,ValueError):return False
        else:return False
    return True


def echo_key(value):
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'))
    return encoded if len(encoded) <= 1024 else None


class DedupStore:
    def __init__(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS seen (bot TEXT, grp TEXT, msg TEXT, ts REAL, PRIMARY KEY(bot,grp,msg))')
        self.db.execute('CREATE INDEX IF NOT EXISTS seen_ts ON seen(ts)')

    def reserve(self, event):
        value = event.get('message_id')
        if isinstance(value, bool) or not isinstance(value, (str, int)) or not str(value) or len(str(value)) > 128:
            return False
        with self.db:
            self.db.execute('DELETE FROM seen WHERE ts < ?', (time.time() - 86400,))
            cursor = self.db.execute('INSERT OR IGNORE INTO seen VALUES (?,?,?,?)',
                                     (str(event['self_id']), str(event['group_id']), str(value), time.time()))
        return cursor.rowcount == 1

    def close(self):
        self.db.close()


class OneBotGate:
    def __init__(self, config: GateConfig, root=None):
        self.config = config
        self.config_message_limit=getattr(config,'message_max_chars',2000)
        self.store = DedupStore(config.database)
        self.active = None
        self.failures = 0
        self.root = root
        self.connected = False
        self.ever_connected = False
        self.last_heartbeat = None
        self.online = None
        self.online_at = None
        self.good = None
        self.transport_health = None
        self.transport_monitor_task = None
        self.transport_supervisor = None
        self.transport_recovery_closed = False
        self.transport_pending = set()
        self.send_observations={}
        self.send_counts=dict(acked=0,failed=0,unknown=0,latency_ms=None)
        self._transport_ready = False
        self.health_pending = {}
        self.admin_pending={}
        self.admin_busy=False
        from .meme_import import admin_token
        self.admin_token=admin_token(root) if root else None
        if self.admin_token in (config.inbound_token,config.upstream_token):raise ValueError('Independent admin token required')
        self.connection_id=secrets.token_hex(32)
        from .group_silence import GroupSilence
        self.silence=GroupSilence(config.bot_qq,config.allowed_groups,config.blocked_users,config.silence_enabled,
                                  config.session_queue_timeout_seconds+210)
        from .vision import Materials,context_token,fetch_image
        from functools import partial
        self.materials=Materials(fetch=partial(fetch_image,network=config.public_network,root=root))
        from .members import Members
        self.members=Members(config.members_config or {'enabled':config.members_enabled})
        self.mention_pending={}
        self.context_token=context_token(root) if root and (config.vision_enabled or config.members_enabled) else None
        if self.context_token and self.context_token in (config.inbound_token,config.upstream_token,self.admin_token):
            raise ValueError('Independent context token required')

    def snow(self):return self.config.transport_provider == 'snowluma'

    def send_metrics(self,*,disconnect=False):
        now=time.monotonic()
        for key,at in list(self.send_observations.items()):
            if disconnect or not 0<=now-at<=15:
                self.send_observations.pop(key,None)
                self.send_counts['unknown']=min(9007199254740991,self.send_counts['unknown']+1)
        return dict(self.send_counts)

    def _observe_send_ack(self,key,event):
        self.send_metrics()
        at=self.send_observations.pop(key,None)
        if at is None:return
        mid=event.get('data',{}).get('message_id') if isinstance(event.get('data'),dict) else None
        valid=(type(mid) is int and mid!=0) or (isinstance(mid,str) and re.fullmatch('-?[0-9]{1,32}',mid) and int(mid)!=0)
        state='acked' if event['status']=='ok' and event['retcode']==0 and valid else 'failed' if event['status']=='failed' else 'unknown'
        self.send_counts[state]=min(9007199254740991,self.send_counts[state]+1)
        if state=='acked':self.send_counts['latency_ms']=max(0,min(15000,int((time.monotonic()-at)*1000)))

    async def revoke_transport_epoch(self):
        self.send_metrics(disconnect=True)
        self.transport_recovery_closed=True;self.channel_ready()
        self.connection_id=secrets.token_hex(32)
        self.connected=False;self.online=None;self.good=None;self.online_at=None
        self.materials.clear();self.members.clear();self.mention_pending.clear()
        if self.transport_health:self.transport_health.invalidate()
        if self.active is not None:await self.active.close(code=1001,message=b'TRANSPORT_RECOVERY')
        self.publish_connection()

    def bind_transport_health(self, verifier):
        # Only a managed in-process owner may bind; no HTTP self-attestation route.
        from .transport_health import HealthVerifier
        if (not isinstance(verifier, HealthVerifier) or not self.snow() or
            verifier.binding.instance_id != self.config.transport_instance_id or
            verifier.binding.config_digest != self.config.transport_config_digest or
            verifier.binding.listener_port != self.config.transport_control_port or
            verifier.ttl != self.config.transport_health_ttl):raise ValueError('HEALTH_BINDING_INVALID')
        if self.transport_health:self.transport_health.invalidate()
        self.channel_ready()
        self.transport_health = verifier
        self.publish_connection()

    def accept_transport_health(self, content):
        # A late fresh proof cannot hide a gap and revive the old event epoch.
        self.channel_ready()
        accepted = bool(self.transport_health and self.transport_health.accept(content))
        self.channel_ready();self.publish_connection()
        return accepted

    def channel_ready(self, *, publish=True):
        base = bool(self.connected and self.online is True and not (self.root and stopping(self.root)))
        if not self.snow():return base
        ready = bool(base and not self.transport_recovery_closed and self.good is True and self.online_at is not None and
                     0 <= time.time()-self.online_at < self.config.transport_health_ttl and self.transport_health and self.transport_health.ready())
        previous = self._transport_ready
        self._transport_ready = ready
        if previous and not ready:
            self.connection_id=secrets.token_hex(32)
            self.materials.clear();self.members.clear();self.mention_pending.clear()
        if previous != ready and publish:self.publish_connection()
        return ready

    async def _transport_expiry_loop(self):
        # TTL expiry revokes capabilities without needing another WS frame.
        while True:
            self.channel_ready()
            delay=self.config.transport_health_poll
            if self._transport_ready:
                delay=min(delay,max(.001,self.transport_health.expires-self.transport_health.clock()),
                          max(.001,self.config.transport_health_ttl-(time.time()-self.online_at)))
            await asyncio.sleep(delay)

    async def _send_current(self, downstream, event, connection):
        # Recheck inside the scheduled coroutine, after wait_for's scheduling gap.
        if self.snow() and (not self.channel_ready() or self.connection_id != connection):
            raise ChannelNotReady('CHANNEL_NOT_READY')
        await downstream.send_json(event)

    def publish_connection(self):
        if self.root:
            path=self.root/'state/gate-connection.json'
            temp=path.with_suffix('.tmp')
            try:
                ready=self.channel_ready(publish=False)
                transport=(dict(provider='snowluma',channel_ready=ready,
                    instance_id=self.config.transport_instance_id,config_digest=self.config.transport_config_digest,
                    health=self.transport_health.mirror() if self.transport_health else dict(ready=False,expires_mono=0.,sequence=0))
                    if self.snow() else {})
                path.parent.mkdir(parents=True,exist_ok=True)
                temp.write_text(json.dumps(dict(id=self.connection_id,connected=self.connected,online=self.online,
                    pid=os.getpid(),created=psutil.Process().create_time(),updated=time.time(),silence=self.silence.mirror(),**transport)),encoding='utf-8')
                # Windows readers can briefly deny replacement. Bound the retry
                # to 20 ms; a permanent failure still closes the channel.
                for attempt in range(3):
                    try:
                        temp.replace(path)
                        break
                    except PermissionError as error:
                        if getattr(error,'winerror',None) not in (5,32,33) or attempt==2:raise
                        time.sleep(.01)
            except OSError as error:
                LOG.warning('CHANNEL_METADATA_WRITE_FAILED code=%s',metadata_error_code(error))
                raise
            finally:
                try:temp.unlink(missing_ok=True)
                except OSError:pass

    def status(self):
        ready=self.channel_ready()
        online = self.online if self.connected and self.online_at and time.time()-self.online_at < 45 else None
        channel = ('connected' if online is True else 'disconnected' if online is False else 'unknown') if self.connected else (
            'disconnected' if self.ever_connected else 'waiting_login')
        if self.snow() and self.connected and not ready:channel='unknown'
        return {'alive': True, 'connected': self.connected, 'self_id_verified': self.connected,
                'last_heartbeat': self.last_heartbeat, 'online': online, 'channel_state': channel,
                'stopping': bool(self.root and stopping(self.root)),
                'silence_enabled':self.silence.enabled,'muted_groups':sum(s['mode']=='muted' for s in self.silence.states.values()),
                **(dict(channel_ready=ready,good=self.good,
                    transport_recovery=self.transport_supervisor.status() if self.transport_supervisor else dict(enabled=False,phase='observe',operator_required=False),
                    transport_monitor=dict(running=bool(self.transport_monitor_task and not self.transport_monitor_task.done())),
                    transport_health=self.transport_health.safe_status() if self.transport_health else
                    dict(trusted=False,ready=False,sequence=0,armed=False)) if self.snow() else {})}

    def observe_online(self, data):
        if self.snow():self.channel_ready()
        previous=self.online
        self.online = data.get('online') if isinstance(data, dict) and type(data.get('online')) is bool else None
        self.good = data.get('good') if isinstance(data, dict) and type(data.get('good')) is bool else None
        self.online_at = time.time()
        if self.online is not True and previous is True:self.connection_id=secrets.token_hex(32)
        if self.online is not True:self.materials.clear();self.members.clear();self.mention_pending.clear()
        self.channel_ready()
        self.publish_connection()

    async def _status_loop(self, downstream):
        # Independent bounded echo space, never mixed with framework pending actions.
        while True:
            echo = 'gate-health-' + secrets.token_hex(16)
            future = asyncio.get_running_loop().create_future()
            self.health_pending[echo_key(echo)] = future
            try:
                await downstream.send_json({'action':'get_status','params':{},'echo':echo})
                try:await asyncio.wait_for(future, timeout=3)
                except TimeoutError:self.observe_online(None)
            finally:
                self.health_pending.pop(echo_key(echo), None)
            await asyncio.sleep(self.config.transport_health_poll if self.snow() else 15)

    async def handle(self, request):
        if (len(request.headers.getall('Authorization', [])) != 1 or
                not secrets.compare_digest(request.headers.get('Authorization', ''), 'Bearer ' + self.config.inbound_token)):
            raise web.HTTPUnauthorized(text='AUTH_FAILED')
        if (len(request.headers.getall('X-Self-ID', [])) != 1 or
                request.headers.get('X-Self-ID') != self.config.bot_qq):
            raise web.HTTPForbidden(text='SELF_ID_MISMATCH')
        role = request.headers.get('X-Client-Role', 'Universal')
        if self.snow() and (len(request.headers.getall('X-Client-Role', [])) != 1 or role.lower() != 'universal'):
            raise web.HTTPForbidden(text='INVALID_ROLE')
        if role.lower() not in ('universal', 'api', 'event'):
            raise web.HTTPForbidden(text='INVALID_ROLE')
        if self.active is not None:
            raise web.HTTPConflict(text='BOT_ALREADY_CONNECTED')
        downstream = web.WebSocketResponse(max_msg_size=MAX_FRAME)
        self.active = downstream
        try:
            await downstream.prepare(request)
            if self.failures:
                await asyncio.sleep(min(30, 2 ** min(self.failures - 1, 5) * random.uniform(.8, 1.2)))
            headers = {'Authorization': 'Bearer ' + self.config.upstream_token,
                       'X-Self-ID': self.config.bot_qq, 'X-Client-Role': role}
            async with aiohttp.ClientSession(trust_env=False, timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.ws_connect(self.config.upstream, headers=headers, max_msg_size=MAX_FRAME,
                                              timeout=aiohttp.ClientWSTimeout(ws_close=2),
                                              receive_timeout=None) as upstream:
                    self.failures = 0
                    self.connected = True
                    self.connection_id=secrets.token_hex(32);self.publish_connection()
                    self.materials.clear();self.members.clear();self.mention_pending.clear()
                    self.ever_connected = True
                    LOG.info('CHANNEL_CONNECTED_SELF_ID_VERIFIED')
                    pending = self.transport_pending if self.snow() else set()
                    tasks = [asyncio.create_task(self._incoming(downstream, upstream, pending)),
                             asyncio.create_task(self._outgoing(upstream, downstream, pending)),
                             asyncio.create_task(self._status_loop(downstream))]
                    if self.snow():tasks.append(asyncio.create_task(self._transport_expiry_loop()))
                    try:
                        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                        for task in done:
                            task.result()
                    finally:
                        for task in tasks:
                            task.cancel()
                        await asyncio.gather(*tasks, return_exceptions=True)
        except (aiohttp.ClientError, OSError, asyncio.TimeoutError, ValueError, TypeError):
            self.failures += 1
            LOG.warning('UPSTREAM_OR_PROTOCOL_FAILURE')
        finally:
            # Release ownership before fallible file I/O, including when the
            # metadata error itself is why the channel is closing.
            self.active = None
            if self.snow():self.send_metrics(disconnect=True)
            self.connected = False
            self.materials.clear();self.members.clear();self.mention_pending.clear()
            self.online = None
            self.online_at = None
            self.good = None
            if self.transport_health:self.transport_health.invalidate()
            self.channel_ready()
            self.health_pending.clear()
            for future in self.admin_pending.values():
                if not future.done():future.set_exception(ConnectionError('disconnected'))
            self.admin_pending.clear()
            try:self.publish_connection()
            except OSError:
                pass  # Already logged safely; must not skip socket cleanup.
            LOG.info('CHANNEL_DISCONNECTED')
            if downstream.prepared:
                await downstream.close(code=1011, message=b'CHANNEL_CLOSED')
        return downstream

    async def _incoming(self, downstream, upstream, pending):
        async for frame in downstream:
            if frame.type != aiohttp.WSMsgType.TEXT:
                if frame.type == aiohttp.WSMsgType.BINARY:
                    await downstream.close(code=1003, message=b'TEXT_JSON_REQUIRED')
                break
            try:
                if self.snow():
                    from .transport_health import strict_json
                    event = strict_json(frame.data, MAX_FRAME)
                else:event = json.loads(frame.data)
            except (ValueError,UnicodeError,RecursionError):
                LOG.info('DROP_INVALID_JSON')
                continue
            if not isinstance(event, dict):
                continue
            if controllable_message(event,self.config) and (self.config.silence_enabled or admitted_message(event,self.config)):
                if self.snow() and not self.channel_ready():continue
                if self.root and stopping(self.root):continue
                if self.store.reserve(event):
                    output_ticket=None
                    if self.config.silence_enabled:
                        from .group_silence import silence_request,real_at
                        group=str(event['group_id'])
                        async with self.silence.locks[group]:
                            if self.snow() and not self.channel_ready():continue
                            mention=real_at(event,self.config.bot_qq)
                            text=''.join(p['data'].get('text','') for p in event['message'] if p['type']=='text' and isinstance(p['data'].get('text'),str))
                            stop=silence_request(text,self.config.silence_aliases,mention,self.config_message_limit)
                            changed=self.silence.control(group,stop,mention)
                            if changed:
                                for cap,row in list(self.materials.entries.items()):
                                    if row['identity'][1]==group:self.materials.expire(cap)
                                self.members.invalidate(group)
                                for ledger in (self.members.caps,self.members.receipts,self.members.permits):
                                    for token,row in list(ledger.items()):
                                        if row['identity'][1]==group:ledger.pop(token,None)
                                for key in list(self.members.events):
                                    if key[1]==group:self.members.events.pop(key,None)
                                self.publish_connection()
                            if stop or not self.silence.normal(group):continue
                            if not admitted_message(event,self.config):continue
                            output_ticket=self.silence.issue(event,self.connection_id)
                    if self.snow() and not output_ticket:output_ticket=self.silence.issue(event,self.connection_id)
                    if self.config.ingress_diagnostics:
                        from .vision_ingress import inspect_event,encode
                        LOG.info(encode(inspect_event(event)))
                    if (not self.snow() and not self.config.silence_enabled and self.config.participation_mode=='mentions' and not self.config.vision_enabled and not self.config.members_enabled and
                        all(s['type'] in ('text','at') for s in event['message']) and
                        not any(k.startswith('qqbot_') for k in event)):
                        # Unchanged legacy text-only frame. Attachments and
                        # embedded replies always take the stripping path below.
                        await upstream.send_str(frame.data)
                        continue
                    # Never let adapter quote expansion fetch or expose embedded bodies.
                    safe=[];reference=None;media=False
                    for segment in event['message']:
                        if not isinstance(segment,dict):continue
                        kind=segment.get('type');data=segment.get('data',{})
                        if not isinstance(data,dict):continue
                        if kind=='text' and isinstance(data.get('text'),str):safe.append({'type':'text','data':{'text':data['text']}})
                        elif kind=='at' and qq_id(data.get('qq'))==self.config.bot_qq:safe.append({'type':'at','data':{'qq':self.config.bot_qq}})
                        elif kind=='reply':reference=str(data.get('id',''))[:128]
                        elif kind!='at':media=True;safe.append({'type':'text','data':{'text':'[非文本未解析]'}})
                    at_ids=[qq_id(s['data'].get('qq')) or 'other_member' for s in event['message'] if s['type']=='at'][:8] if self.config.attention_enabled else []
                    member_cap=self.members.issue(event,self.connection_id) if self.config.members_enabled else None
                    image=self.materials.issue(event,self.connection_id) if self.config.vision_enabled else None
                    image_text=''.join(s['data'].get('text','') for s in event['message'] if s['type']=='text' and isinstance(s['data'].get('text'),str))
                    event={k:v for k,v in event.items() if k in ('post_type','message_type','sub_type','self_id','group_id','user_id','message_id','time','font','sender')}
                    event=dict(event,message=safe,raw_message='',qqbot_reference=reference,qqbot_media=media,
                               qqbot_connection=self.connection_id)
                    if output_ticket:event['qqbot_output_ticket']=output_ticket
                    if member_cap:event['qqbot_member_cap']=member_cap
                    if image:event['qqbot_image']=image;event['qqbot_text']=image_text
                    if self.config.attention_enabled:event['qqbot_at_ids']=at_ids
                    if not self.snow() or self.channel_ready():await upstream.send_json(event)
            elif (event.get('post_type')=='notice' and event.get('notice_type') in ('group_increase','group_decrease') and
                  qq_id(event.get('self_id'))==self.config.bot_qq and qq_id(event.get('group_id')) in self.config.allowed_groups):
                self.members.invalidate(qq_id(event['group_id']))
            elif (event.get('post_type') == 'meta_event' and
                  event.get('meta_event_type') in ('heartbeat', 'lifecycle') and
                  qq_id(event.get('self_id')) == self.config.bot_qq):
                if event.get('meta_event_type') == 'heartbeat':
                    self.last_heartbeat = time.time()
                    self.observe_online(event.get('status'))
                await upstream.send_str(frame.data)
            elif ('post_type' not in event and 'echo' in event and
                  event.get('status') in ('ok', 'failed') and
                  isinstance(event.get('retcode'), int) and not isinstance(event['retcode'], bool)):
                key = echo_key(event['echo'])
                if key in self.admin_pending:
                    future=self.admin_pending[key]
                    if not future.done():future.set_result(event)
                elif key in self.health_pending:
                    future = self.health_pending[key]
                    self.observe_online(event.get('data') if event.get('status')=='ok' and event['retcode']==0 else None)
                    if not future.done():future.set_result(None)
                elif key in pending:
                    pending.remove(key)
                    if self.snow():self._observe_send_ack(key,event)
                    # Strip any transport-supplied claim; only this gate can attest @.
                    applied=self.mention_pending.pop(key,None)
                    if isinstance(event.get('data'),dict):
                        event['data'].pop('qqbot_mention_applied',None)
                        if applied is not None:event['data']['qqbot_mention_applied']=applied
                    await upstream.send_json(event)

    async def _outgoing(self, upstream, downstream, pending):
        async for frame in upstream:
            if frame.type != aiohttp.WSMsgType.TEXT:
                break
            try:
                event = json.loads(frame.data)
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            key = echo_key(event['echo']) if 'echo' in event else None
            authorized=False
            params=event.get('params',{})
            output_ticket=None
            is_send=event.get('action') in ('send_msg','send_group_msg')
            if self.snow() and event.get('action') not in ('get_status','get_version_info','get_login_info') and not self.channel_ready():
                await upstream.send_json(dict(status='failed',retcode=1403,message='CHANNEL_NOT_READY',data=None,echo=event.get('echo')))
                continue
            if is_send and (self.config.silence_enabled or self.snow()):
                from .group_silence import DENIED
                try:
                    output_ticket=params.get('qqbot_output_ticket')
                    self.silence.verify(output_ticket,qq_id(params.get('group_id')),self.connection_id)
                    if not self.channel_ready():raise ValueError()
                except (ValueError,TypeError,AttributeError):
                    await upstream.send_json(dict(status='failed',retcode=1403,message=DENIED,data=None,echo=event.get('echo')))
                    continue
                params={k:v for k,v in params.items() if k!='qqbot_output_ticket'}
                event=dict(event,params=params)
            if isinstance(params,dict) and 'qqbot_mention_permission' in params:
                try:
                    if event.get('action')!='send_group_msg' or set(params)!={'group_id','message','qqbot_mention_permission'}:raise ValueError()
                    message,applied=self.members.consume(params['qqbot_mention_permission'],qq_id(params.get('group_id')),params['message'],self.connection_id,self.member_allowed)
                    if key is None or key in pending or len(pending)>=128:raise ValueError()
                    event=dict(event,params=dict(group_id=params['group_id'],message=message))
                    authorized=True
                except (ValueError,TypeError,KeyError):
                    await upstream.send_json(dict(status='failed',retcode=1403,message='MENTION_PERMISSION_DENIED',data=None,echo=event.get('echo')))
                    continue
            if (authorized or allowed_action(event, self.config)) and key is not None and key not in self.health_pending and key not in self.admin_pending and len(pending) < 128:
                pending.add(key)
                if authorized:self.mention_pending[key]=applied
                elif event.get('action') in ('send_msg','send_group_msg'):self.mention_pending[key]=False
                if is_send and (self.config.silence_enabled or self.snow()):
                    # Same lock as control transition. Linearization is the bounded
                    # socket write, never the later QQ ACK.
                    group=qq_id(params.get('group_id'))
                    async with self.silence.locks[group]:
                        try:
                            self.silence.verify(output_ticket,group,self.connection_id)
                            if self.snow() and not self.channel_ready():raise ValueError()
                        except ValueError:
                            pending.discard(key);self.mention_pending.pop(key,None)
                            await upstream.send_json(dict(status='failed',retcode=1403,message=DENIED,data=None,echo=event.get('echo')))
                            continue
                        try:
                            if self.snow():
                                self.send_metrics()
                                if len(self.send_observations)<128:self.send_observations[key]=time.monotonic()
                            await asyncio.wait_for(self._send_current(downstream,event,self.connection_id),3)
                        except ChannelNotReady:
                            self.send_observations.pop(key,None)
                            pending.discard(key);self.mention_pending.pop(key,None)
                            await upstream.send_json(dict(status='failed',retcode=1403,message=DENIED,data=None,echo=event.get('echo')))
                else:await downstream.send_json(event)
            else:
                await upstream.send_json({'status': 'failed', 'retcode': 1403,
                                          'message': 'SCOPE_DENIED_OR_PENDING_LIMIT',
                                          'data': None, 'echo': event.get('echo')})

    def application(self):
        app = web.Application(client_max_size=MAX_FRAME)
        app.router.add_get('/ws', self.handle)
        async def health(request):return web.json_response(self.status())
        app.router.add_get('/health', health)
        app.router.add_post('/admin/memes/favorites',self.favorites)
        for operation in ('bind','resolve','permit'):
            app.router.add_post('/context/members/'+operation,self.resolve_members)
        app.router.add_post('/context/vision/resolve',self.resolve_vision)
        app.router.add_post('/context/vision/bind',self.resolve_vision)

        monitor=None
        async def start_transport(app):
            nonlocal monitor
            if self.snow():
                from .transport_owner import monitor_from_loaded
                monitor=monitor_from_loaded(self)
                monitor.task=asyncio.create_task(monitor.run())
                self.transport_monitor_task=monitor.task
        app.on_startup.append(start_transport)

        async def cleanup(app):
            if monitor:await monitor.close()
            if self.active is not None:
                await self.active.close(code=1001, message=b'SHUTDOWN')
            self.store.close()
            self.materials.clear();self.members.clear();self.mention_pending.clear()

        app.on_cleanup.append(cleanup)
        return app

    def member_allowed(self,identity):
        bot,group,sender,_=identity
        return (self.config.members_enabled and self.channel_ready() and
            not (self.root and stopping(self.root)) and bot==self.config.bot_qq and
            group in self.config.allowed_groups and (not self.config.silence_enabled or self.silence.normal(group)) and sender not in self.config.blocked_users and sender!=bot)

    async def member_rpc(self,action,params):
        # This private method is never exposed as an action-param HTTP proxy.
        if action not in ('get_group_info','get_group_member_list') or self.active is None or not self.channel_ready():raise ValueError('Fixed member RPC')
        connection=self.connection_id
        echo='gate-members-'+secrets.token_hex(32);key=echo_key(echo)
        future=asyncio.get_running_loop().create_future();self.admin_pending[key]=future
        try:
            await self.active.send_json(dict(action=action,params=params,echo=echo))
            result=await asyncio.wait_for(future,3)
            if not self.channel_ready() or self.snow() and connection!=self.connection_id:raise ValueError('Member RPC unavailable')
            if result.get('status')!='ok' or result.get('retcode')!=0:raise ValueError('Member RPC failed')
            return result.get('data')
        finally:self.admin_pending.pop(key,None)

    async def resolve_members(self,request):
        if (request.remote!='127.0.0.1' or not self.context_token or len(request.headers.getall('Authorization',[]))!=1 or
            not secrets.compare_digest(request.headers.get('Authorization',''),'Bearer '+self.context_token)):
            raise web.HTTPUnauthorized(text='AUTH_FAILED')
        if not self.config.members_enabled or not self.channel_ready():
            raise web.HTTPServiceUnavailable(text='MEMBERS_CAPABILITY_UNVERIFIED')
        connection=self.connection_id
        from .reply_plan import _pairs
        generations={g:s['generation'] for g,s in self.silence.states.items()}
        def current(identity):
            return self.member_allowed(identity) and (not self.config.silence_enabled or
                generations.get(identity[1])==self.silence.states[identity[1]]['generation'])
        try:
            if request.content_length is None or request.content_length>131072:raise ValueError()
            body=json.loads(await request.text(),object_pairs_hook=_pairs)
            if request.path.endswith('/bind'):
                self.members.bind(body,self.connection_id,current);result={'bound':True}
            elif request.path.endswith('/permit'):
                result={'permit':self.members.permit(body,self.connection_id,current)}
            else:
                async with asyncio.timeout(15):
                    result=await self.members.resolve(body,self.connection_id,current,self.member_rpc)
            if self.snow() and (not self.channel_ready() or connection!=self.connection_id):raise ValueError()
            return web.json_response(result)
        except (ValueError,TypeError,KeyError,TimeoutError,ConnectionError):
            raise web.HTTPBadRequest(text='MEMBER_MATERIAL_UNAVAILABLE') from None

    async def resolve_vision(self,request):
        if (request.remote!='127.0.0.1' or not self.context_token or
            len(request.headers.getall('Authorization',[]))!=1 or not secrets.compare_digest(
                request.headers.get('Authorization',''),'Bearer '+self.context_token)):
            raise web.HTTPUnauthorized(text='AUTH_FAILED')
        if not self.config.vision_enabled or not self.channel_ready():
            raise web.HTTPServiceUnavailable(text='MATERIAL_UNAVAILABLE')
        connection=self.connection_id
        from .reply_plan import _pairs
        generations={g:s['generation'] for g,s in self.silence.states.items()}
        try:
            if request.content_length is None or request.content_length>2048:raise ValueError()
            body=json.loads(await request.text(),object_pairs_hook=_pairs)
            def allowed(identity):
                bot,group,sender,_=identity
                return (self.channel_ready() and
                    bot==self.config.bot_qq and group in self.config.allowed_groups and
                    (not self.config.silence_enabled or self.silence.normal(group) and generations.get(group)==self.silence.states[group]['generation']) and sender not in self.config.blocked_users)
            if request.path.endswith('/bind'):
                self.materials.bind(body,self.connection_id,allowed)
                return web.json_response({'bound':True})
            result=await self.materials.resolve(body,self.connection_id,allowed)
            if self.snow() and (not self.channel_ready() or connection!=self.connection_id):raise ValueError()
            return web.json_response(result)
        except (ValueError,TypeError,TimeoutError,aiohttp.ClientError,OSError):
            raise web.HTTPBadRequest(text='MATERIAL_UNAVAILABLE') from None

    async def favorites(self,request):
        if (not self.admin_token or len(request.headers.getall('Authorization',[]))!=1 or
            not secrets.compare_digest(request.headers.get('Authorization',''),'Bearer '+self.admin_token)):
            raise web.HTTPUnauthorized(text='AUTH_FAILED')
        try:
            obj=await request.json()
            if (not isinstance(obj,dict) or set(obj)!={'count','mode'} or type(obj['count']) is not int or
                not 1<=obj['count']<=48 or obj['mode'] not in ('detail','basic')):raise ValueError()
        except (ValueError,TypeError):raise web.HTTPBadRequest(text='INVALID_FIXED_REQUEST') from None
        if self.admin_busy:raise web.HTTPConflict(text='IMPORT_BUSY')
        if not self.channel_ready() or self.active is None:raise web.HTTPServiceUnavailable(text='BOT_NOT_CONNECTED')
        connection=self.connection_id
        self.admin_busy=True;echo='gate-memes-'+secrets.token_hex(32);key=echo_key(echo)
        future=asyncio.get_running_loop().create_future();self.admin_pending[key]=future
        try:
            await self.active.send_json(dict(action='fetch_custom_face' if obj['mode']=='basic' else 'fetch_custom_face_detail',params={'count':obj['count']},echo=echo))
            result=await asyncio.wait_for(future,5)
            if not self.channel_ready() or self.snow() and connection!=self.connection_id:raise ValueError()
            if result.get('status')!='ok' or result.get('retcode')!=0 or not isinstance(result.get('data'),list):raise ValueError()
            # Only URL survives transiently. No arbitrary account metadata reaches client/framework.
            rows=[]
            for row in result['data'][:obj['count']]:
                url=row if isinstance(row,str) else row.get('url') if isinstance(row,dict) else None
                if not isinstance(url,str) or len(url)>2048:raise ValueError()
                rows.append(url)
            return web.json_response(rows)
        except (ValueError,ConnectionError,TimeoutError):raise web.HTTPServiceUnavailable(text='FAVORITES_UNAVAILABLE') from None
        finally:self.admin_pending.pop(key,None);self.admin_busy=False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--root')
    args = parser.parse_args()
    from .config_files import management_root
    root=management_root(args.config,args.root or os.environ.get('QQBOT_ROOT'))
    config = load_gate_config(args.config,root=root)
    if config.transport_provider=='snowluma':
        from .transport_owner import require_runtime
        from .config_files import load_consumer
        require_runtime(root,load_consumer(root,args.config))
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    web.run_app(OneBotGate(config,root).application(), host=config.host, port=config.port, access_log=None)


if __name__ == '__main__':
    from .config_files import ConfigError
    from .transport_owner import TransportBlocked
    import sys
    try:main()
    except (ConfigError,TransportBlocked) as error:
        print(str(error),file=sys.stderr)
        raise SystemExit(1) from None
