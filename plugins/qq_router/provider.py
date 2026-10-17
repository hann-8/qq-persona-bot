"""Project provider adapter: request metadata comes from router session_id only."""
import json
from contextvars import ContextVar
from astrbot.core.provider.sources.openai_source import ProviderOpenAIOfficial
from astrbot.core.provider.register import register_provider_adapter
from qqbot_gateway.group_protocol import validate_request


@register_provider_adapter('qqbot_openai','Project authenticated group-turn adapter')
class QQBotProvider(ProviderOpenAIOfficial):
    _group_request=ContextVar('qqbot_provider_request',default=None)

    async def text_chat(self,prompt=None,session_id=None,**kwargs):
        request=None
        if isinstance(session_id,str) and session_id.startswith('qqbot-group:'):
            request=validate_request(json.loads(session_id[len('qqbot-group:'):]))
        token=self._group_request.set(request)
        try:return await super().text_chat(prompt=prompt,session_id=session_id,**kwargs)
        finally:self._group_request.reset(token)

    async def _prepare_chat_payload(self,*args,**kwargs):
        payload,context=await super()._prepare_chat_payload(*args,**kwargs)
        if self._group_request.get() is not None:payload['qqbot_request']=dict(self._group_request.get())
        return payload,context
