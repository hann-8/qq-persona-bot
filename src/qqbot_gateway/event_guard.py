"""Per-event fail-closed capability. Never patch an AstrBot class or shared bot."""
from contextlib import contextmanager
from contextvars import ContextVar


class EventSendGuard:
    def __init__(self,event):
        self.mention_text=ContextVar('qqbot_mention_text',default=None)
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
        text=self.mention_text.get()
        if text is not None and (len(chain.chain)!=1 or not isinstance(chain.chain[0],Plain) or chain.chain[0].text!=text):
            raise ValueError('Typed mention text mismatch')
        from .reply_delivery import EventReceiptProxy
        ticket=self.event.get_extra('qq_output_ticket')
        if self.event.get_extra('qq_silence_enabled'):
            if not ticket:raise ValueError('GROUP_MUTED_OR_STALE_OUTPUT')
            original=self.event.bot
            self.event.bot=EventReceiptProxy(original,self.event.get_group_id(),output_ticket=ticket)
            try:await self.original(chain)
            finally:self.event.bot=original
        else:await self.original(chain)

    @contextmanager
    def grant(self,image_uri=None,mention_text=None):
        token=self.capability.set(image_uri or True);mention=self.mention_text.set(mention_text)
        try:yield
        finally:
            self.capability.reset(token);self.mention_text.reset(mention)
