"""Per-event fail-closed capability. Never patch an AstrBot class or shared bot."""
from contextlib import contextmanager
from contextvars import ContextVar


class EventSendGuard:
    def __init__(self,event):
        self.event=event;self.capability=ContextVar('qqbot_event_send',default=False);self.original=event.send
        event.send=self.send

    async def send(self,chain):
        if not self.capability.get():
            self.event.clear_result()
            return
        # All project output is direct text, including local notices.
        from astrbot.api.message_components import Plain,Image
        if any(not isinstance(c,Plain) and not (isinstance(c,Image) and self.capability.get()==getattr(c,'file',None)) for c in chain.chain):
            raise ValueError('Only prepared direct output is authorized')
        await self.original(chain)

    @contextmanager
    def grant(self,image_uri=None):
        token=self.capability.set(image_uri or True)
        try:yield
        finally:self.capability.reset(token)
