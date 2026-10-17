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
    def __init__(self,bot,group):
        self.original=bot;self.group=str(group);self.calls=0;self.message_id=None

    def __getattr__(self,name):
        return getattr(self.original,name)

    async def send_group_msg(self,**kwargs):
        self.calls+=1
        if self.calls!=1 or str(kwargs.get('group_id'))!=self.group:
            raise DeliveryStopped('unexpected_send_route')
        result=await self.original.send_group_msg(**kwargs)
        if isinstance(result,dict):
            mid=result.get('message_id')
            if type(mid) is int and mid!=0:
                self.message_id=str(mid)
            elif isinstance(mid,str) and len(mid)<=32 and re.fullmatch(r'-?[0-9]+',mid) and int(mid)!=0:
                self.message_id=str(int(mid))
        return result


class ReplyDelivery:
    def __init__(self,store,output,allowed,timeout=3):
        self.store=store;self.output=output;self.allowed=allowed;self.timeout=timeout
        self.queue=GroupDeliveryQueue()

    async def send(self,event,key,plan):
        # Mark before awaiting: duplicate hook invocations cannot dispatch again.
        if event.get_extra('qq_delivery_handled'):return
        event.set_extra('qq_delivery_handled',True)
        event.clear_result()
        reason=None
        try:
            async with self.queue.hold(str(event.get_group_id()),lambda:self.allowed(event)):
                for index,text in enumerate(plan.bubbles):
                    if index:
                        delay=random.uniform(self.output['bubble_delay_min_ms'],self.output['bubble_delay_max_ms'])/1000
                        await cancellable(asyncio.sleep(delay),lambda:self.allowed(event),6)
                    if not self.allowed(event):raise DeliveryStopped('stopped_or_invalidated')
                    if not self.store.begin_part(key,index):raise DeliveryStopped('part_already_attempted')
                    original=event.bot
                    proxy=EventReceiptProxy(original,event.get_group_id())
                    event.bot=proxy
                    try:
                        chain=event.plain_result(text)
                        await cancellable(event.send(chain),lambda:self.allowed(event),self.timeout)
                        state=self.store.part_result(key,index,'sent' if proxy.calls==1 and proxy.message_id else 'unknown',proxy.message_id)
                    except BaseException:
                        # A correlated ACK already captured is evidence even if stop/cancel
                        # arrives while the framework finishes its local send bookkeeping.
                        self.store.part_result(key,index,'sent' if proxy.calls==1 and proxy.message_id else 'unknown',proxy.message_id)
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
