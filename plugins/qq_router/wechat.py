"""Akasha transport binding for the existing router business methods.

No QQ identity/ticket is manufactured. The qq_* event extras are internal
business protocol fields; input authorization is based on the platform binding.
"""
import asyncio
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import time
import uuid
import psutil

from qqbot_gateway.attention import Attention
from qqbot_gateway.event_guard import EventSendGuard
from qqbot_gateway.reply_delivery import ReplyDelivery

CONFIG=Path('E:/CodexWS/WeChatbot/config/local/akasha.json')
POLICY='''\n当前来源是微信 Akasha 独立平台。昵称与文本@只是显示/唤醒材料，不是QQ身份或原生@。
仅回复当前微信会话，不转发到QQ。不能发送原生@、语音、视频或任意文件；表情只使用登记素材，GIF仅首帧。
真实成员资料只取本轮来源。不要声称已送达服务器，发送仅本地报告。\n'''

def stable_id(account,kind,value):
    return str(int.from_bytes(hashlib.sha256(json.dumps([account,kind,str(value)],ensure_ascii=False).encode()).digest()[:6],'big') or 1)

class AliasedAttention:
    """Explicit shared_context pairs use the same RAM Attention service."""
    def __init__(self,base,rooms,actors,bot):
        object.__setattr__(self,'base',base);object.__setattr__(self,'rooms',rooms)
        object.__setattr__(self,'actors',actors);object.__setattr__(self,'bot',bot)
    def __getattr__(self,name):
        value=getattr(self.base,name)
        if name in ('window','state','group_epoch','reset','preempt','batch','source','freeze'):
            return lambda group,*args,**kw:value(self.rooms.get(group,group),*args,**kw)
        return value
    def observe(self,group,sender,mid,name,text,ats=(),reply=None):
        mapped=self.actors.get((group,sender),'wechat:'+sender)
        return self.base.observe(self.rooms.get(group,group),mapped,'wechat:'+mid,name,text,
            [self.base.bot if q==self.bot else 'wechat:'+q for q in ats], 'wechat:'+reply if reply else None)
    def invalidate(self):
        for room in self.rooms.values():self.base.reset(room)

class WeChatRoute:
    def route(self,event):return self

    def connection(self):
        try:
            value=json.loads(self.status_path.read_text(encoding='utf-8'))
            process=psutil.Process(value['pid'])
            if 'project_entry.py' not in ' '.join(process.cmdline()):return None
            return value['boot'] if value.get('astrbot_ws') else None
        except (OSError,ValueError,KeyError,psutil.Error):return None

    def transport_allowed(self,event):
        ext=event.get_extra('akasha_source')
        if not isinstance(ext,dict) or event.get_platform_id()!='akasha-wechat':return False
        return (ext.get('account')==self.cfg['bridge']['bot_wxid'] and
                ext.get('session') in self.sessions and ext.get('boot')==self.connection() and
                str(event.get_self_id())==self.bot and str(event.get_group_id()) in self.groups and
                ext.get('sender') not in self.cfg['bridge']['blacklist'])

    def silence_allowed(self,event):
        if not self.transport_allowed(event):return False
        try:
            state=json.loads(self.status_path.read_text(encoding='utf-8'));ext=event.get_extra('akasha_source');sid=ext['session']
            return not state['paused'].get(sid) and ext['generation']==state['generations'].get(sid,0)
        except (OSError,KeyError,ValueError):return False

    def silence_enabled(self):return False
    def observe_gate(self):pass

    async def local_notice(self,event,text):
        if text and self.silence_allowed(event):
            guard=event.get_extra('qq_send_guard')
            with guard.grant():
                try:await asyncio.wait_for(event.send(event.plain_result(text)),30)
                except Exception:pass

    async def accept(self,event):
        event.should_call_llm(False)
        raw=event.message_obj.raw_message
        ext=raw.get('akasha') if isinstance(raw,dict) else None
        event.set_extra('akasha_source',ext);event.set_extra('akasha_route',self)
        if not self.silence_allowed(event):event.stop_event();return
        sid=ext['session'];generation=ext['generation']
        previous=self.generations.get(sid)
        if previous is not None and previous!=generation:self.group_turns.reset(str(event.get_group_id()))
        self.generations[sid]=generation
        if str(event.get_sender_id())==self.bot:event.stop_event();return
        event.platform_meta=replace(event.platform_meta,support_proactive_message=False)
        event.set_extra('qq_send_guard',EventSendGuard(event))
        event.set_extra('qq_silence_enabled',False)
        event.set_extra('qq_delivery_version',self.persona_id)
        event.set_extra('qq_delivery_identity',(self.bot,str(event.get_group_id()),str(event.get_sender_id())))
        rows=ext['rows'];row=rows[-1];text=row.get('content','')
        # Text wake is never represented as a native OneBot At component.
        wake=ext.get('wake')=='text-derived'
        if wake:
            for name in self.cfg['bridge']['nicknames']:text=text.replace('@'+name,'').replace('＠'+name,'')
        from qqbot_gateway.attention import called
        command=text.strip()
        if ext.get('sender_trusted') and ext['sender']==self.cfg['bridge'].get('owner_wxid'):
            actions={'暂停发言':'pause','恢复发言':'resume','重置本群上下文':'reset','重置会话':'reset','/重置':'reset'}
            if command in actions:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post('http://127.0.0.1:18766/control',json=dict(action=actions[command],session=ext['session'])) as r:await r.read()
                self.group_turns.reset(str(event.get_group_id()));event.stop_event();return
        # Preserve all batch members in the shared Attention RAM window.
        for r in rows[:-1]:
            uid=stable_id(self.cfg['bridge']['bot_wxid'],'user',r['sender_id'])
            self.group_turns.observe(str(event.get_group_id()),uid,str(r['rawid']),r.get('sourceName',''),r.get('content',''))
        raw['qqbot_connection']=ext['boot']
        raw['qqbot_input']=dict(text=text,media_types=[])
        raw['qqbot_at_ids']=[self.bot] if wake else []
        raw['qqbot_reference']=row.get('reply_id')
        if ext.get('members'):
            cap=uuid.uuid4().hex+uuid.uuid4().hex
            folder=self.status_path.parent/'member-caps';folder.mkdir(exist_ok=True)
            (folder/(cap+'.json')).write_text(json.dumps(dict(members=ext['members'],sender=ext['sender'],expires=time.time()+60)),encoding='utf-8')
            raw['qqbot_member_cap']=cap
        if row.get('media_path'):
            # An opaque one-use local cap, resolved by the existing gateway normalizer.
            cap=uuid.uuid4().hex+uuid.uuid4().hex;ref='i_'+uuid.uuid4().hex
            media=self.status_path.parent/'media-caps';media.mkdir(exist_ok=True)
            (media/(cap+'.json')).write_text(json.dumps(dict(path=row['media_path'],image_ref=ref,expires=time.time()+60)),encoding='utf-8')
            raw['qqbot_image']=dict(image_ref=ref,cap=cap)
            raw['qqbot_text']=text if text not in ('[图片]','[表情]','[动画表情]') else ''
        elif ext.get('media_error'):
            if wake or called(text,self.participation['attention']['aliases']):await self.local_notice(event,'这张当前消息的图片暂时无法读取，请发送一张新图片。')
            event.stop_event();return
        elif any(mark in text for mark in ('[语音]','[视频]','[文件]')):
            if wake or called(text,self.participation['attention']['aliases']):await self.local_notice(event,'目前支持文字和当前图片，暂不支持语音、视频或文件。')
            event.stop_event();return
        async for item in self.on_attention_group(event):yield item

def create_route(router):
    if not CONFIG.exists():return None
    cfg=json.loads(CONFIG.read_text(encoding='utf-8'))
    if not cfg['bridge']['bot_wxid'] or not cfg['bridge']['sessions']:return None
    # Reuse the router's actual business methods, provider and task ledger.
    cls=type('AkashaBusiness',(WeChatRoute,type(router)),{})
    obj=object.__new__(cls);obj.__dict__=dict(router.__dict__)
    obj.cfg=cfg;account=cfg['bridge']['bot_wxid'];obj.bot=stable_id(account,'bot',account)
    obj.sessions={s['id']:s for s in cfg['bridge']['sessions']}
    obj.groups={stable_id(account,'group',sid) for sid in obj.sessions}
    if cfg['bridge']['private_enabled']:
        obj.sessions.update({s['id']:s for s in cfg['bridge']['private_sessions']})
        obj.groups.update(stable_id(account,'user',s['id']) for s in cfg['bridge']['private_sessions'])
    obj.status_path=CONFIG.parents[2]/'state/akasha-wechat/bridge-status.json'
    obj.generations={}
    obj.admins={stable_id(account,'user',cfg['bridge']['owner_wxid'])} if cfg['bridge'].get('owner_wxid') else set()
    obj.blocked={stable_id(account,'user',s) for s in cfg['bridge']['blacklist']}
    obj.members=dict(router.members,enabled=True,mentions_enabled=False);obj.member_client=None
    obj.participation=deepcopy(router.participation)
    obj.attention_effective=True
    obj.persona=router.persona+POLICY
    obj.connection_id=obj.connection();obj.connection_watcher=None
    obj.group_turns=Attention(obj.participation,uuid.uuid4().hex,router.group_turns.limit,router.group_turns.timeout)
    obj.group_turns.bot=obj.bot
    obj.delivery=ReplyDelivery(router.tasks,router.output,obj.delivery_allowed,timeout=30,catalog=router.memes)
    # One MemoryStore service and one key/database. Only explicit pairings share.
    rooms={};actors={}
    for sid in obj.sessions:
        gid=stable_id(account,'group' if sid.endswith('@chatroom') else 'user',sid);pair=next((p for p in cfg['pairings'] if p['wechat_session']==sid),None)
        qq=str(pair['qq_session']) if pair else None
        if qq and qq not in router.groups:raise ValueError('Pairing QQ room is not authorized')
        router.memory.groups.add(gid)
        router.memory._namespace_overrides[gid]=router.memory.namespace(qq) if qq else router.memory.hmac('wechat',account,sid)
        if pair:
            for wxid,qqid in pair.get('actor_links',{}).items():
                uid=stable_id(account,'user',wxid)
                router.memory.actor_links[(gid,uid)]=router.memory.actor(qq,str(qqid));actors[(gid,uid)]=str(qqid)
            if pair.get('scope')=='shared_context':rooms[gid]=qq
    if rooms:
        # Share only selected scopes. Non-paired rooms retain their own RAM.
        obj.group_turns=RoutedAttention(obj.group_turns,AliasedAttention(router.group_turns,rooms,actors,obj.bot),set(rooms))
    return obj

class RoutedAttention:
    def __init__(self,local,shared,rooms):self.local=local;self.shared=shared;self.rooms=rooms
    def __getattr__(self,name):
        if name in ('window','state','group_epoch','reset','preempt','batch','source','freeze','observe'):
            return lambda group,*a,**k:getattr(self.shared if group in self.rooms else self.local,name)(group,*a,**k)
        if name in ('rebuild','dispatch','finish','acknowledge'):
            return lambda ticket,*a,**k:getattr(self.shared.base if ticket.group in self.shared.rooms.values() else self.local,name)(ticket,*a,**k)
        return getattr(self.local,name)
    def invalidate(self):self.local.invalidate();self.shared.invalidate()

async def start_management(router):
    from aiohttp import web
    async def memory(request):
        if request.headers.get('Origin') not in (None,'http://127.0.0.1:18766'):raise web.HTTPForbidden()
        value=await request.json();route=getattr(router,'wechat',None)
        if route is None:raise web.HTTPServiceUnavailable()
        sid=value.get('session');action=value.get('action','inspect')
        if action!='inspect' and not sid:raise web.HTTPBadRequest(text='Select one memory session')
        selected=[sid] if sid else list(route.sessions)
        result=[]
        for session in selected:
            if session not in route.sessions:raise web.HTTPForbidden()
            gid=stable_id(route.cfg['bridge']['bot_wxid'],'group' if session.endswith('@chatroom') else 'user',session)
            if action not in ('inspect','export','delete','clear'):raise web.HTTPBadRequest()
            try:result.append(router.memory.manage(gid,action,record_id=value.get('record_id'),expected=value.get('expected')))
            except ValueError:raise web.HTTPConflict(text='Memory changed or unavailable') from None
        return web.json_response(dict(results=result))
    app=web.Application();app.router.add_post('/memory',memory)
    runner=web.AppRunner(app,access_log=None);await runner.setup()
    await web.TCPSite(runner,'127.0.0.1',18767).start();router.wechat_management=runner
