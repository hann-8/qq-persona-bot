"""Intake-only WS gate: intentionally has NO upstream, RPC or send route."""
import argparse
import asyncio
import json
import os
import secrets
from pathlib import Path

import aiohttp
from aiohttp import web

from .config import load_gate_config, qq_id
from .group_silence import GroupSilence, real_at, silence_request
from .onebot_gate import MAX_FRAME, admitted_message, controllable_message
from .vision_ingress import encode, observe, validate_record


class IntakeGate:
    def __init__(self, config, group, sender, *, fetch=None, emit=None, instance=None):
        if group not in config.allowed_groups or not qq_id(sender) or sender in config.blocked_users or sender==config.bot_qq:
            raise ValueError('INTAKE_TARGET_DENIED')
        self.config=config;self.group=group;self.sender=sender;self.fetch=fetch
        self.instance=instance
        self.emit=emit or (lambda row:print(encode(row),flush=True))
        self.active=None;self.claimed=False;self.task=None;self.result=None;self.done=asyncio.Event();self.online=False
        self.silence=GroupSilence(config.bot_qq,config.allowed_groups,config.blocked_users,config.silence_enabled)

    async def sample(self, event, connection, generation):
        def allowed(identity):
            return (self.active is connection and not connection.closed and self.silence.normal(self.group) and
                generation==self.silence.states[self.group]['generation'] and
                identity[:3]==(self.config.bot_qq,self.group,self.sender))
        try:self.result=await observe(event,'intake',allowed,fetch=self.fetch,emit=self.emit)
        finally:self.done.set()

    async def handle(self, request):
        if (len(request.headers.getall('Authorization',[]))!=1 or
            not secrets.compare_digest(request.headers.get('Authorization',''),'Bearer '+self.config.inbound_token)):
            raise web.HTTPUnauthorized()
        if len(request.headers.getall('X-Self-ID',[]))!=1 or request.headers.get('X-Self-ID')!=self.config.bot_qq:
            raise web.HTTPForbidden()
        if request.headers.get('X-Client-Role','Universal').lower() not in ('universal','event','api'):
            raise web.HTTPForbidden()
        if self.active is not None or self.claimed:raise web.HTTPConflict()
        ws=web.WebSocketResponse(max_msg_size=MAX_FRAME);self.active=ws
        try:
            await ws.prepare(request)
            async for frame in ws:
                if frame.type!=aiohttp.WSMsgType.TEXT:
                    if frame.type==aiohttp.WSMsgType.BINARY:await ws.close(code=1003,message=b'TEXT_JSON_REQUIRED')
                    break
                try:
                    from .reply_plan import _pairs
                    event=json.loads(frame.data,object_pairs_hook=_pairs)
                except ValueError:continue
                if not isinstance(event,dict):continue
                if event.get('post_type')=='meta_event' and qq_id(event.get('self_id'))==self.config.bot_qq:
                    status=event.get('status',{})
                    if isinstance(status,dict) and type(status.get('online')) is bool:self.online=status['online']
                    continue
                if not controllable_message(event,self.config):continue
                group=str(event['group_id'])
                if self.config.silence_enabled:
                    text=''.join(s['data'].get('text','') for s in event['message'] if s['type']=='text' and isinstance(s['data'].get('text'),str))
                    mention=real_at(event,self.config.bot_qq)
                    stop=silence_request(text,self.config.silence_aliases,mention,self.config.message_max_chars)
                    self.silence.control(group,stop,mention)
                    if stop or not self.silence.normal(group):continue
                if (self.claimed or not admitted_message(event,self.config) or group!=self.group or
                    str(event['user_id'])!=self.sender):continue
                # Match the production admission requirement for a bounded ID.
                mid=event.get('message_id')
                if type(mid) not in (int,str) or not 1<=len(str(mid))<=128:continue
                self.claimed=True;self.online=True
                self.task=asyncio.create_task(self.sample(event,ws,self.silence.states[group]['generation']))
        finally:
            if self.task and not self.task.done():
                self.task.cancel();await asyncio.gather(self.task,return_exceptions=True)
            self.active=None
        return ws

    def application(self):
        app=web.Application(client_max_size=MAX_FRAME)
        app.router.add_get('/ws',self.handle)
        async def health(request):
            import psutil
            return web.json_response(dict(alive=True,intake_only=True,instance_id=self.instance,
                pid=os.getpid(),created=psutil.Process().create_time(),online=self.online,claimed=self.claimed))
        app.router.add_get('/health',health)
        async def close(app):
            if self.task and not self.task.done():self.task.cancel();await asyncio.gather(self.task,return_exceptions=True)
            if self.active is not None:await self.active.close()
        app.on_shutdown.append(close)
        return app


async def serve(config, root, instance, group, sender, timeout):
    from .lifecycle import atomic_json
    gate=IntakeGate(config,group,sender,instance=instance)
    runner=web.AppRunner(gate.application(),access_log=None,shutdown_timeout=2)
    await runner.setup()
    try:
        await web.TCPSite(runner,config.host,config.port).start()
        try:
            await asyncio.wait_for(gate.done.wait(),timeout)
            record=validate_record(gate.result) if gate.result else None
            result=dict(state='observed' if record else 'cancelled',record=record)
        except TimeoutError:
            result=dict(state='timeout' if gate.online else 'login_required',record=None)
        # Only closed evidence, never the event or private cap/hash chain.
        atomic_json(root/'state/vision-evidence'/(instance+'.json'),result)
    finally:await runner.cleanup()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--config',required=True);parser.add_argument('--instance',required=True)
    parser.add_argument('--timeout',type=int,required=True);args=parser.parse_args()
    import re
    if not re.fullmatch('[a-f0-9]{32}',args.instance) or not 1<=args.timeout<=120:parser.error('INTAKE_ARGUMENTS_INVALID')
    # Only manager-created, live, matching owners may run the diagnostic child.
    import psutil
    state=json.loads((args.root/'state/service-mode.json').read_text(encoding='utf-8'))
    owner=state['owner'];process=psutil.Process(owner['pid'])
    if (state.get('mode')!='intake_only' or state.get('instance_id')!=args.instance or
        abs(process.create_time()-owner['created'])>=.01 or not process.is_running() or
        process.pid not in {p.pid for p in psutil.Process().parents()}):raise ValueError('INTAKE_OWNER_INVALID')
    asyncio.run(serve(load_gate_config(args.config,root=args.root),args.root,args.instance,
        os.environ['QQBOT_INTAKE_GROUP'],os.environ['QQBOT_INTAKE_SENDER'],args.timeout))


if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt):
        print('INTAKE_CHILD_STOPPED details_suppressed',flush=True);raise SystemExit(1) from None
