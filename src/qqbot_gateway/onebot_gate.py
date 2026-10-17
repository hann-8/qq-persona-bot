import argparse
import asyncio
import json
import logging
from pathlib import Path
import random
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


def metadata_error_code(error):
    # Fixed categories only: never log paths or arbitrary OS exception text.
    return {5:'ACCESS_DENIED',32:'SHARING_VIOLATION',33:'LOCK_VIOLATION'}.get(getattr(error,'winerror',None),'IO_ERROR')


def admitted_message(event, config):
    if not isinstance(event, dict):
        return False
    if (event.get('post_type') != 'message' or event.get('message_type') != 'group' or
            qq_id(event.get('self_id')) != config.bot_qq or
            not qq_id(event.get('user_id')) or qq_id(event.get('user_id')) == config.bot_qq or
            qq_id(event.get('user_id')) in config.blocked_users or
            qq_id(event.get('group_id')) not in config.allowed_groups):
        return False
    message = event.get('message')
    return isinstance(message, list) and bool(message) and all(isinstance(s,dict) and isinstance(s.get('type'),str) and isinstance(s.get('data'),dict) for s in message) and (config.participation_mode=='free' or any(
        isinstance(segment, dict) and segment.get('type') == 'at' and
        isinstance(segment.get('data'), dict) and
        qq_id(segment['data'].get('qq')) == config.bot_qq
        for segment in message
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
    if action in ('get_group_info', 'get_group_member_info', 'get_group_member_list', 'send_group_msg'):
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
        self.store = DedupStore(config.database)
        self.active = None
        self.failures = 0
        self.root = root
        self.connected = False
        self.ever_connected = False
        self.last_heartbeat = None
        self.online = None
        self.online_at = None
        self.health_pending = {}
        self.admin_pending={}
        self.admin_busy=False
        from .meme_import import admin_token
        self.admin_token=admin_token(root) if root else None
        if self.admin_token in (config.inbound_token,config.upstream_token):raise ValueError('Independent admin token required')
        self.connection_id=secrets.token_hex(32)

    def publish_connection(self):
        if self.root:
            path=self.root/'state/gate-connection.json'
            temp=path.with_suffix('.tmp')
            try:
                path.parent.mkdir(parents=True,exist_ok=True)
                temp.write_text(json.dumps(dict(id=self.connection_id,connected=self.connected,online=self.online,
                    pid=os.getpid(),created=psutil.Process().create_time(),updated=time.time())),encoding='utf-8')
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
        online = self.online if self.connected and self.online_at and time.time()-self.online_at < 45 else None
        channel = ('connected' if online is True else 'disconnected' if online is False else 'unknown') if self.connected else (
            'disconnected' if self.ever_connected else 'waiting_login')
        return {'alive': True, 'connected': self.connected, 'self_id_verified': self.connected,
                'last_heartbeat': self.last_heartbeat, 'online': online, 'channel_state': channel,
                'stopping': bool(self.root and stopping(self.root))}

    def observe_online(self, data):
        previous=self.online
        self.online = data.get('online') if isinstance(data, dict) and type(data.get('online')) is bool else None
        self.online_at = time.time()
        if self.online is not True and previous is True:self.connection_id=secrets.token_hex(32)
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
            await asyncio.sleep(15)

    async def handle(self, request):
        if (len(request.headers.getall('Authorization', [])) != 1 or
                not secrets.compare_digest(request.headers.get('Authorization', ''), 'Bearer ' + self.config.inbound_token)):
            raise web.HTTPUnauthorized(text='AUTH_FAILED')
        if (len(request.headers.getall('X-Self-ID', [])) != 1 or
                request.headers.get('X-Self-ID') != self.config.bot_qq):
            raise web.HTTPForbidden(text='SELF_ID_MISMATCH')
        role = request.headers.get('X-Client-Role', 'Universal')
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
                    self.ever_connected = True
                    LOG.info('CHANNEL_CONNECTED_SELF_ID_VERIFIED')
                    pending = set()
                    tasks = [asyncio.create_task(self._incoming(downstream, upstream, pending)),
                             asyncio.create_task(self._outgoing(upstream, downstream, pending)),
                             asyncio.create_task(self._status_loop(downstream))]
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
            self.connected = False
            self.online = None
            self.online_at = None
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
                event = json.loads(frame.data)
            except ValueError:
                LOG.info('DROP_INVALID_JSON')
                continue
            if not isinstance(event, dict):
                continue
            if admitted_message(event, self.config):
                if self.root and stopping(self.root):continue
                if self.store.reserve(event):
                    if self.config.participation_mode=='free':
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
                        event=dict(event,message=safe,raw_message='',qqbot_reference=reference,qqbot_media=media,
                                   qqbot_connection=self.connection_id)
                        await upstream.send_json(event)
                    else:await upstream.send_str(frame.data)
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
                    await upstream.send_str(frame.data)

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
            if allowed_action(event, self.config) and key is not None and key not in self.health_pending and key not in self.admin_pending and len(pending) < 128:
                pending.add(key)
                await downstream.send_str(frame.data)
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

        async def cleanup(app):
            if self.active is not None:
                await self.active.close(code=1001, message=b'SHUTDOWN')
            self.store.close()

        app.on_cleanup.append(cleanup)
        return app

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
        if not self.connected or self.online is not True or self.active is None:raise web.HTTPServiceUnavailable(text='BOT_NOT_CONNECTED')
        self.admin_busy=True;echo='gate-memes-'+secrets.token_hex(32);key=echo_key(echo)
        future=asyncio.get_running_loop().create_future();self.admin_pending[key]=future
        try:
            await self.active.send_json(dict(action='fetch_custom_face' if obj['mode']=='basic' else 'fetch_custom_face_detail',params={'count':obj['count']},echo=echo))
            result=await asyncio.wait_for(future,5)
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
    args = parser.parse_args()
    config = load_gate_config(args.config)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    root=Path(args.config).resolve().parent.parent
    web.run_app(OneBotGate(config,root).application(), host=config.host, port=config.port, access_log=None)


if __name__ == '__main__':
    main()
