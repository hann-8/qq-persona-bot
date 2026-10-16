import argparse
import asyncio
import json
import logging
import random
import secrets
import sqlite3
import time

import aiohttp
from aiohttp import web

from .config import GateConfig, load_gate_config, qq_id

LOG = logging.getLogger(__name__)
MAX_FRAME = 1024 * 1024


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
    return isinstance(message, list) and any(
        isinstance(segment, dict) and segment.get('type') == 'at' and
        isinstance(segment.get('data'), dict) and
        qq_id(segment['data'].get('qq')) == config.bot_qq
        for segment in message
    )


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
        return qq_id(params.get('group_id')) in config.allowed_groups
    if action == 'send_msg':
        return params.get('message_type') == 'group' and qq_id(params.get('group_id')) in config.allowed_groups
    return False


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
    def __init__(self, config: GateConfig):
        self.config = config
        self.store = DedupStore(config.database)
        self.active = None
        self.failures = 0

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
                    LOG.info('CHANNEL_CONNECTED_SELF_ID_VERIFIED')
                    pending = set()
                    tasks = [asyncio.create_task(self._incoming(downstream, upstream, pending)),
                             asyncio.create_task(self._outgoing(upstream, downstream, pending))]
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
            self.active = None
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
                if self.store.reserve(event):
                    await upstream.send_str(frame.data)
            elif (event.get('post_type') == 'meta_event' and
                  event.get('meta_event_type') in ('heartbeat', 'lifecycle') and
                  qq_id(event.get('self_id')) == self.config.bot_qq):
                await upstream.send_str(frame.data)
            elif ('post_type' not in event and 'echo' in event and
                  event.get('status') in ('ok', 'failed') and
                  isinstance(event.get('retcode'), int) and not isinstance(event['retcode'], bool)):
                key = echo_key(event['echo'])
                if key in pending:
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
            if allowed_action(event, self.config) and key is not None and len(pending) < 128:
                pending.add(key)
                await downstream.send_str(frame.data)
            else:
                await upstream.send_json({'status': 'failed', 'retcode': 1403,
                                          'message': 'SCOPE_DENIED_OR_PENDING_LIMIT',
                                          'data': None, 'echo': event.get('echo')})

    def application(self):
        app = web.Application(client_max_size=MAX_FRAME)
        app.router.add_get('/ws', self.handle)

        async def cleanup(app):
            if self.active is not None:
                await self.active.close(code=1001, message=b'SHUTDOWN')
            self.store.close()

        app.on_cleanup.append(cleanup)
        return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    config = load_gate_config(args.config)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    web.run_app(OneBotGate(config).application(), host=config.host, port=config.port, access_log=None)


if __name__ == '__main__':
    main()
