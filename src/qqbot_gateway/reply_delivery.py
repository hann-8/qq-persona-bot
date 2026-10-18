"""Bounded, per-group delivery through the original event and connection only."""
import asyncio
from contextlib import asynccontextmanager
import random
import re
import time


class DeliveryStopped(Exception):
    pass


async def cancellable(awaitable, allowed, timeout):
    task=asyncio.ensure_future(awaitable)
    deadline=time.monotonic()+timeout
    try:
        while not task.done():
            if not allowed():raise DeliveryStopped('stopped_or_invalidated')
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError()
            await asyncio.wait((task,),timeout=min(.1,remaining))
        if not allowed():raise DeliveryStopped('stopped_or_invalidated')
        return await task
    finally:
        if not task.done():task.cancel()
        await asyncio.gather(task,return_exceptions=True)


class GroupDeliveryQueue:
    def __init__(self, limit=2, timeout=10):
        self.limit=limit;self.timeout=timeout;self.groups={}

    @asynccontextmanager
    async def hold(self,group,allowed):
        state=self.groups.setdefault(group,dict(lock=asyncio.Lock(),count=0))
        if state['count']>=self.limit+1:raise DeliveryStopped('delivery_queue_full')
        state['count']+=1
        acquired=False
        try:
            # Track acquisition inside the task so cancellation at grant cannot leak the lock.
            async def acquire():
                nonlocal acquired
                await state['lock'].acquire();acquired=True
            await cancellable(acquire(),allowed,self.timeout)
            yield
        finally:
            if acquired:state['lock'].release()
            state['count']-=1
            if not state['count']:self.groups.pop(group,None)


class EventReceiptProxy:
    """One event's bot reference is wrapped; shared CQHttp instance is untouched."""
    def __init__(self,bot,group,image_uri=None,image_digest=None,mention_permission=None,expected_text=None):
        self.original=bot;self.group=str(group);self.calls=0;self.message_id=None
        self.image_uri=image_uri;self.image_digest=image_digest
        self.mention_permission=mention_permission;self.expected_text=expected_text;self.mention_applied=None

    def __getattr__(self,name):
        return getattr(self.original,name)

    async def send_group_msg(self,**kwargs):
        self.calls+=1
        if self.calls!=1 or str(kwargs.get('group_id'))!=self.group:
            raise DeliveryStopped('unexpected_send_route')
        if self.image_uri:
            import base64,hashlib
            segments=kwargs.get('message')
            if not isinstance(segments,list) or len(segments)!=1 or segments[0].get('type')!='image':raise DeliveryStopped('image_conversion_mismatch')
            file=segments[0].get('data',{}).get('file','')
            if not file.startswith('base64://'):raise DeliveryStopped('image_conversion_mismatch')
            try:data=base64.b64decode(file[9:],validate=True)
            except ValueError:raise DeliveryStopped('image_conversion_mismatch') from None
            if hashlib.sha256(data).hexdigest()!=self.image_digest:raise DeliveryStopped('image_conversion_mismatch')
            kwargs=dict(kwargs,message=[{'type':'image','data':{'file':self.image_uri}}])
        if self.mention_permission:
            if kwargs.get('message')!=[{'type':'text','data':{'text':self.expected_text}}]:raise DeliveryStopped('mention_conversion_mismatch')
            kwargs=dict(kwargs,qqbot_mention_permission=self.mention_permission)
        result=await self.original.send_group_msg(**kwargs)
        if isinstance(result,dict):
            if type(result.get('qqbot_mention_applied')) is bool:self.mention_applied=result['qqbot_mention_applied']
            mid=result.get('message_id')
            if type(mid) is int and mid!=0:
                self.message_id=str(mid)
            elif isinstance(mid,str) and len(mid)<=32 and re.fullmatch(r'-?[0-9]+',mid) and int(mid)!=0:
                self.message_id=str(int(mid))
        return result


class ReplyDelivery:
    def __init__(self,store,output,allowed,timeout=3,catalog=None,members=None):
        self.store=store;self.output=output;self.allowed=allowed;self.timeout=timeout
        self.queue=GroupDeliveryQueue()
        self.members=members
        self.catalog=catalog;self.image_times={};self.same_times={}

    async def send(self,event,key,plan):
        # Mark before awaiting: duplicate hook invocations cannot dispatch again.
        if event.get_extra('qq_delivery_handled'):return
        event.set_extra('qq_delivery_handled',True)
        event.clear_result()
        reason=None
        try:
            async with self.queue.hold(str(event.get_group_id()),lambda:self.allowed(event)):
                for index,part in enumerate(plan.parts):
                    if index:
                        delay=random.uniform(self.output['bubble_delay_min_ms'],self.output['bubble_delay_max_ms'])/1000
                        await cancellable(asyncio.sleep(delay),lambda:self.allowed(event),6)
                    if not self.allowed(event):raise DeliveryStopped('stopped_or_invalidated')
                    uri=None;permission=None
                    if part.mention_ref:
                        if self.members is None:raise DeliveryStopped('mention_service_missing')
                        metadata=event.get_extra('qq_group_metadata')
                        if not metadata or not metadata.get('member_receipt'):raise DeliveryStopped('mention_receipt_missing')
                        permission=await cancellable(self.members.permit(metadata['member_receipt'],metadata,index),lambda:self.allowed(event),3)
                    if part.type=='image':
                        try:
                            if self.catalog is None:raise ValueError()
                            group=str(event.get_group_id());now=time.monotonic()
                            from .media_protocol import explicit_meme
                            bypass=explicit_meme(event.get_extra('qq_meme_question') or '')
                            if not bypass and (now-self.image_times.get(group,float('-inf'))<self.catalog.cfg['cooldown_seconds'] or now-self.same_times.get((group,part.payload_ref),float('-inf'))<self.catalog.cfg['same_meme_cooldown_seconds']):raise ValueError()
                            path,row=self.catalog.resolve(part.payload_ref)
                            if row['sha256']!=part.digest or part.semantic_label!='[bot发了表情：'+row['name']+']':raise ValueError()
                            from .meme_catalog import controlled_path,inspect_image
                            data=path.read_bytes()
                            if inspect_image(data,self.catalog.cfg['max_file_bytes'])['sha256']!=part.digest:raise ValueError()
                            frozen=controlled_path(self.catalog.root,'state/meme-delivery/'+row['file'])
                            frozen.parent.mkdir(parents=True,exist_ok=True)
                            if not frozen.exists():
                                with frozen.open('xb') as f:f.write(data)
                            if frozen.read_bytes()!=data:raise ValueError()
                            uri=frozen.as_uri()
                        except (ValueError,OSError):
                            self.store.fail_prepared_part(key,index)
                            continue
                    if not self.store.begin_part(key,index):raise DeliveryStopped('part_already_attempted')
                    original=event.bot
                    proxy=EventReceiptProxy(original,event.get_group_id(),uri,part.digest if uri else None,permission,part.payload_ref if permission else None)
                    event.bot=proxy
                    try:
                        if uri:
                            from astrbot.api.message_components import Image
                            from astrbot.core.message.message_event_result import MessageChain
                            chain=MessageChain([Image.fromFileSystem(str(frozen))])
                        else:chain=event.plain_result(part.payload_ref)
                        guard=event.get_extra('qq_send_guard')
                        if uri and guard:
                            with guard.grant(image_uri=chain.chain[0].file):
                                await cancellable(event.send(chain),lambda:self.allowed(event),self.timeout)
                        elif permission and guard:
                            with guard.grant(mention_text=part.payload_ref):
                                await cancellable(event.send(chain),lambda:self.allowed(event),self.timeout)
                        else:await cancellable(event.send(chain),lambda:self.allowed(event),self.timeout)
                        state=self.store.part_result(key,index,'sent' if proxy.calls==1 and proxy.message_id else 'unknown',proxy.message_id)
                        if part.mention_ref:
                            self.store.mention_result(key,index,proxy.mention_applied if state=='sent' else None)
                        if uri and state=='sent':
                            self.image_times[group]=time.monotonic();self.same_times[(group,part.payload_ref)]=time.monotonic()
                    except BaseException:
                        # A correlated ACK already captured is evidence even if stop/cancel
                        # arrives while the framework finishes its local send bookkeeping.
                        self.store.part_result(key,index,'sent' if proxy.calls==1 and proxy.message_id else 'unknown',proxy.message_id)
                        if part.mention_ref:self.store.mention_result(key,index,proxy.mention_applied if proxy.message_id else None)
                        raise
                    finally:event.bot=original
                    if state!='sent':raise DeliveryStopped('ack_unknown_or_duplicate')
        except asyncio.CancelledError:
            reason='cancelled'
            raise
        except DeliveryStopped as error:
            reason=str(error)
        except TimeoutError:
            reason='ack_or_queue_timeout'
        except Exception:
            # Do not expose arbitrary transport exceptions or send a second error message.
            reason='transport_or_local_unknown'
        finally:
            self.store.finish_delivery(key,reason)
            event.clear_result()
