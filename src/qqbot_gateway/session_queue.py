import asyncio
from collections import deque
from dataclasses import dataclass, field
import time
from .text_safety import has_tool_markup


class SessionError(Exception):
    def __init__(self,code,notify=True):
        self.code=code;self.notify=notify
        super().__init__(code)


@dataclass
class SessionState:
    busy: bool = False
    waiting: deque = field(default_factory=deque)
    last_accepted: float = float('-inf')
    last_notice: float = float('-inf')


class Lease:
    def __init__(self,coordinator,key,state):
        self.owner=coordinator;self.key=key;self.state=state;self.released=False

    def release(self):
        if self.released:return
        self.released=True
        while self.state.waiting:
            future=self.state.waiting.popleft()
            if not future.done():future.set_result(True);return
        self.state.busy=False


class SessionCoordinator:
    def __init__(self,cooldown=5,limit=2,timeout=600,clock=time.monotonic):
        self.cooldown=cooldown;self.limit=limit;self.timeout=timeout;self.clock=clock;self.states={}

    async def acquire(self,key):
        now=self.clock()
        for stale,state in list(self.states.items()):
            if not state.busy and not state.waiting and now-state.last_accepted>3600:self.states.pop(stale,None)
        state=self.states.setdefault(key,SessionState())
        def reject(code):
            notify=now-state.last_notice>=30
            if notify:state.last_notice=now
            return SessionError(code,notify)
        if now-state.last_accepted<self.cooldown:raise reject('COOLDOWN')
        if state.busy and len(state.waiting)>=self.limit:raise reject('SESSION_QUEUE_FULL')
        state.last_accepted=now
        lease=Lease(self,key,state)
        if not state.busy:state.busy=True;return lease
        future=asyncio.get_running_loop().create_future();state.waiting.append(future)
        try:
            await asyncio.wait_for(asyncio.shield(future),timeout=self.timeout)
            return lease
        except BaseException as error:
            granted=future.done() and not future.cancelled()
            if not granted:
                future.cancel()
                try:state.waiting.remove(future)
                except ValueError:pass
            else:lease.release()
            if isinstance(error,TimeoutError):raise SessionError('SESSION_QUEUE_TIMEOUT') from None
            raise


def trim_history(history,turns=7,char_limit=8000):
    """Keep complete text user/assistant turns, leaving room for the next turn."""
    pairs=[];user=None
    for message in history:
        if not isinstance(message,dict):continue
        role=message.get('role');content=message.get('content')
        if isinstance(content,list):
            if any(not isinstance(part,dict) or part.get('type')!='text' or not isinstance(part.get('text'),str) for part in content):continue
            content=''.join(part['text'] for part in content)
        if not isinstance(content,str):continue
        if role=='user':user={'role':'user','content':content}
        elif role=='assistant' and user is not None:
            if not has_tool_markup(content):
                pairs.append([user,{'role':'assistant','content':content}])
            user=None
    pairs=pairs[-turns:] if turns else []
    while pairs and sum(len(m['content']) for pair in pairs for m in pair)>char_limit:pairs.pop(0)
    return [m for pair in pairs for m in pair]
