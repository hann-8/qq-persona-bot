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
        from astrbot.api.message_components import Plain
        if any(not isinstance(c,Plain) for c in chain.chain):
            raise ValueError('Only direct text is authorized')
        await self.original(chain)

    @contextmanager
    def grant(self):
        token=self.capability.set(True)
        try:yield
        finally:self.capability.reset(token)
