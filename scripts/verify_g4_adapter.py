"""Offline regression using the installed AstrBot converter; no QQ or model calls."""
import asyncio
from dataclasses import replace
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from qqbot_gateway.config import GateConfig
from qqbot_gateway.onebot_gate import allowed_action


async def verify():
    from aiocqhttp import Event
    from aiocqhttp.exceptions import ActionFailed
    from astrbot.api.message_components import At
    from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_platform_adapter import AiocqhttpAdapter

    with tempfile.TemporaryDirectory() as directory:
        config = GateConfig('222', frozenset({'111'}), frozenset({'333'}),
                            'a'*40, 'b'*40, Path(directory)/'unused.sqlite')
        class LocalActions:
            def __init__(self, deny_fallback=False):
                self.calls=[]
                self.deny_fallback=deny_fallback

            async def call_action(self, action, **params):
                self.calls.append(action)
                if not allowed_action({'action':action,'params':params}, config) or (
                        self.deny_fallback and action == 'get_stranger_info'):
                    raise ActionFailed({'status':'failed','retcode':1403})
                if action == 'get_group_member_info':return {'card':''}
                if action == 'get_stranger_info':return {'nickname':'offline bot'}
                raise AssertionError('Unexpected action')

        event = Event({'post_type':'message','message_type':'group','sub_type':'normal',
            'self_id':222,'user_id':333,'group_id':111,'message_id':1,'time':1,
            'sender':{'user_id':333,'nickname':'offline user'},
            'message':[{'type':'at','data':{'qq':'222'}},
                       {'type':'text','data':{'text':'offline regression'}}]})
        adapter = object.__new__(AiocqhttpAdapter)
        # Reproduce the exact previous failure: rejected nickname fallback loses At.
        adapter.bot = LocalActions(deny_fallback=True)
        broken = await adapter._convert_handle_message_event(event)
        assert not any(isinstance(c,At) for c in broken.message)
        # The scoped allowlist now preserves the real At segment.
        adapter.bot = LocalActions()
        fixed = await adapter._convert_handle_message_event(event)
        assert any(isinstance(c,At) and str(c.qq)=='222' for c in fixed.message)
        assert adapter.bot.calls == ['get_group_member_info','get_stranger_info']
        assert not allowed_action({'action':'get_stranger_info','params':{'user_id':333}},config)
        print('PASS: prior At loss reproduced; scoped bot lookup preserves At; other user denied; no network/model requests.')


if __name__ == '__main__':asyncio.run(verify())
