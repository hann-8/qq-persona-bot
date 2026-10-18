"""Project provider adapter: request metadata comes from router session_id only."""
import json
import re
from contextvars import ContextVar
from astrbot.core.provider.sources.openai_source import ProviderOpenAIOfficial
from astrbot.core.provider.register import register_provider_adapter
from qqbot_gateway.group_protocol import validate_request


@register_provider_adapter('qqbot_openai','Project authenticated group-turn adapter')
class QQBotProvider(ProviderOpenAIOfficial):
    _group_request=ContextVar('qqbot_provider_request',default=None)
    _group_trace=ContextVar('qqbot_provider_trace',default=None)

    def _create_http_client(self,provider_config):
        client=super()._create_http_client(provider_config)
        async def trace_header(request):
            trace=self._group_trace.get()
            if trace is not None:request.headers['X-QQBot-Trace']=trace
        client.event_hooks.setdefault('request',[]).append(trace_header)
        return client

    async def text_chat(self,prompt=None,session_id=None,**kwargs):
        request=None;trace=None
        if isinstance(session_id,str) and session_id.startswith('qqbot-v2:'):
            from qqbot_gateway.reply_plan import _pairs
            local=json.loads(session_id[len('qqbot-v2:'):],object_pairs_hook=_pairs)
            if (set(local)!={'request','trace'} or not isinstance(local['trace'],str) or
                not re.fullmatch(r'[a-f0-9]{32}',local['trace'])):raise ValueError('Invalid internal trace')
            request=validate_request(local['request']);trace=local['trace']
            if request['version']!=2:raise ValueError('Invalid version')
            if kwargs.get('image_urls') or kwargs.get('extra_user_content_parts'):
                raise ValueError('Private image materials are gateway-only')
        elif isinstance(session_id,str) and session_id.startswith('qqbot-group:'):
            request=validate_request(json.loads(session_id[len('qqbot-group:'):]))
            if request['version']!=1:raise ValueError('v2 requires internal trace')
        if session_id=='qqbot-media':request={'version':1,'kind':'media_turn'}
        token=self._group_request.set(request)
        trace_token=self._group_trace.set(trace)
        try:return await super().text_chat(prompt=prompt,session_id=session_id,**kwargs)
        finally:self._group_request.reset(token);self._group_trace.reset(trace_token)

    async def _prepare_chat_payload(self,*args,**kwargs):
        payload,context=await super()._prepare_chat_payload(*args,**kwargs)
        if self._group_request.get() is not None:payload['qqbot_request']=dict(self._group_request.get())
        return payload,context
