"""Synthetic loopback provider -> real runner/history/decorate/send, no QQ/model."""
import asyncio
import copy
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]


async def verify(synthetic=None, backend='codebuddy_cli', report_path=None):
    from aiohttp import web
    from astrbot.core.agent.message import Message
    from astrbot.core.agent.runners.base import AgentState
    from astrbot.core.agent.runners.tool_loop_agent_runner import ToolLoopAgentRunner
    from astrbot.core.config.default import DEFAULT_CONFIG
    from astrbot.core.db.po import Conversation
    from astrbot.core.pipeline.process_stage.method.agent_sub_stages.internal import InternalAgentSubStage
    from astrbot.core.pipeline.result_decorate.stage import ResultDecorateStage
    from astrbot.core.pipeline.respond.stage import RespondStage
    import astrbot.core.pipeline.result_decorate.stage as decorate_module
    from astrbot.core.provider.entities import ProviderRequest
    from astrbot.core.provider.sources.openai_source import ProviderOpenAIOfficial
    from astrbot.api.platform import AstrBotMessage, MessageMember, MessageType, PlatformMetadata
    from astrbot.api.message_components import At, Plain
    from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
    from qqbot_gateway.chat_text import prepare_reply
    from qqbot_gateway.model_gateway import application, ModelQueue
    from plugins.qq_router.main import QQRouter

    class Synthetic:
        attempts = 0
        text = ''
        async def run(self, *args):
            self.attempts += 1
            return self.text

    class History:
        saved = None
        async def update_conversation(self, umo, cid, history, **kwargs):
            self.saved = history

    class Bot:
        def __init__(self): self.sent = []
        async def send_group_msg(self, **kwargs):
            self.sent.append(kwargs)
            return {'message_id': len(self.sent)}  # Simulated ACK only.

    router = QQRouter.__new__(QQRouter)
    synthetic = synthetic or Synthetic()
    queue = ModelQueue(synthetic)
    token = secrets.token_urlsafe(32)
    server = web.AppRunner(application(queue, token, max_reply_chars=200), access_log=None)
    await server.setup()
    site = web.TCPSite(server, '127.0.0.1', 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    provider = ProviderOpenAIOfficial({'id': 'lap11-offline', 'type': 'openai_chat_completion',
        'api_base': f'http://127.0.0.1:{port}/v1', 'key': [token], 'model': 'workbuddy-local',
        'modalities': ['text'], 'custom_extra_body': {}, 'timeout': 10}, {})
    report = {'real_model_requests': 0, 'real_qq_messages': 0, 'cases': []}
    try:
        config = copy.deepcopy(DEFAULT_CONFIG)
        config['t2i'] = False
        config['content_safety']['also_use_in_response'] = False
        config['provider_tts_settings']['enable'] = False
        config['provider_settings']['display_reasoning_text'] = False
        config['platform_settings'].update(reply_prefix='', reply_with_mention=False,
                                           reply_with_quote=True, forward_threshold=100000)
        config['platform_settings']['segmented_reply']['enable'] = False
        async def no_tts(*args): return None
        ctx = SimpleNamespace(astrbot_config=config, plugin_manager=SimpleNamespace(
            context=SimpleNamespace(get_using_tts_provider_async=no_tts)))
        decorate = ResultDecorateStage()
        respond = RespondStage()
        await decorate.initialize(ctx)
        await respond.initialize(ctx)
        samples = {
            'mixed': '# 标题\n\n**重点**\n\n| a | b |\n|---|---|\n| x | y |\n\n[文档](https://example.com)',
            'literal_code': '```\n    **literal**\n        a * b\n```',
            'literal_think': '```\n<think>literal code</think>\n```',
            'literal_json': '```\n[{"type":"text","text":"literal JSON"}]\n```',
            'truncated': '鱼' * 110 + '。' + '鲸' * 200,
        }
        for index, (name, source) in enumerate(samples.items(), 1):
            synthetic.text = source
            expected, _ = prepare_reply(source, 200)
            response = await provider.text_chat(prompt='synthetic input', func_tool=None, request_max_retries=1)
            msg = AstrBotMessage()
            msg.self_id = '222'; msg.type = MessageType.GROUP_MESSAGE
            msg.group_id = '111'; msg.sender = MessageMember('333', 'offline user')
            msg.message_id = str(index); msg.message = [At(qq='222'), Plain(text='test')]
            msg.message_str = 'test'; msg.session_id = '111'
            bot = Bot()
            event = AiocqhttpMessageEvent('test', msg,
                PlatformMetadata(name='aiocqhttp', description='offline', id='qqbot'), '111', bot)
            event.set_extra('qq_router_trace', 'offline')
            run_context = SimpleNamespace(messages=[Message(role='system', content='policy'),
                                                    Message(role='user', content='test')])

            class Hooks:
                async def on_agent_done(self, context, result):
                    await router.model_response(event, result)
                    await router.preserve_gateway_text(event, context, result)

            runner = ToolLoopAgentRunner.__new__(ToolLoopAgentRunner)
            runner._state = AgentState.RUNNING
            runner.stats = SimpleNamespace(end_time=None)
            runner.run_context = run_context; runner.agent_hooks = Hooks()
            runner._pending_follow_ups = []
            await runner._complete_with_assistant_response(response)
            assert response.completion_text == expected
            history = History()
            stage = InternalAgentSubStage()
            stage.conv_manager = history
            conv = Conversation('qqbot', event.unified_msg_origin, 'offline', history='[]', persona_id='offline')
            req = ProviderRequest(prompt='test', conversation=conv)
            await stage._save_to_history(event, req, response, run_context.messages, None)
            saved = history.saved[-1]['content']
            if isinstance(saved, list): saved = ''.join(p['text'] for p in saved if p['type'] == 'text')
            event.set_result(event.plain_result(response.completion_text))
            handler=SimpleNamespace(handler_module_path='lap17-single',handler_name='deliver_reply',handler=router.deliver_reply)
            with patch.object(decorate_module.star_handlers_registry,'get_handlers_by_event_type',return_value=[handler]),patch.dict(decorate_module.star_map,{'lap17-single':SimpleNamespace(name='lap17-single')}):
                async for _ in decorate.process(event): pass
            await respond.process(event)
            assert len(bot.sent) == 1
            wire = bot.sent[0]['message']
            sent = ''.join(p['data']['text'] for p in wire if p['type'] == 'text')
            assert saved == sent == expected
            assert not any(p['type'] == 'at' for p in wire)
            report['cases'].append({'name': name, 'saved_equals_sent_equals_gateway': True,
                                    'send_count': len(bot.sent), 'ack': 'simulated'})
        assert synthetic.attempts == len(samples)
        report['synthetic_attempts'] = synthetic.attempts
        print('PASS: 5 loopback cases, real AstrBot provider/runner/history/decorate/OneBot sender; exact text, 1 simulated send each.')
    finally:
        await provider.client.close()
        await server.cleanup()
    (report_path or ROOT / 'reports/lap-11-offline-2026-10-16.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    # Framework imports create data files; keep all such side effects in a scratch cwd.
    previous = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap11-') as directory:
        os.chdir(directory)
        try: asyncio.run(verify())
        finally: os.chdir(previous)
