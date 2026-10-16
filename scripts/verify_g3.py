"""Explicit local AstrBot-provider verification; never sends a QQ message."""
import argparse
import asyncio
import json
from pathlib import Path
import secrets
import sys
import uuid

from aiohttp import web

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from qqbot_gateway.errors import GatewayError
from qqbot_gateway.model_gateway import application, ModelQueue
from qqbot_gateway.workbuddy_cli_runner import CLIRunner


async def verify():
    from astrbot.core.provider.sources.openai_source import ProviderOpenAIOfficial
    cli=CLIRunner(ROOT,'deepseek-v4.1-flash')
    queue=ModelQueue(cli)
    token=secrets.token_urlsafe(32)
    server=web.AppRunner(application(queue,token),access_log=None,handler_cancellation=True)
    await server.setup();site=web.TCPSite(server,'127.0.0.1',0);await site.start()
    port=site._server.sockets[0].getsockname()[1]
    provider=ProviderOpenAIOfficial({'id':'g3-local-test','type':'openai_chat_completion','provider':'openai',
        'api_base':f'http://127.0.0.1:{port}/v1','key':[token],'model':'workbuddy-local',
        'modalities':['text'],'custom_extra_body':{},'timeout':180},{})
    report={'real_request':False,'failure_attempts':{}}
    try:
        word='G3_'+uuid.uuid4().hex[:10]
        response=await provider.text_chat(prompt='回忆历史口令，只输出口令本身。',
            contexts=[{'role':'user','content':'历史口令是'+word},{'role':'assistant','content':'记住了'}],
            system_prompt='这是本机验证。严格按用户要求只输出历史口令，无需解释。',func_tool=None,request_max_retries=1)
        report.update(real_request=True,answer_exact=response.completion_text==word,
                      cli_attempts=cli.attempts,contract=queue.last_shape,protocol=cli.last_protocol)
        if not report['answer_exact'] or cli.attempts!=1:raise RuntimeError('Real provider contract failed')
        class Failing:
            def __init__(self,code):self.code=code;self.attempts=0
            async def run(self,*args):self.attempts+=1;raise GatewayError(self.code)
        for code in ('RATE_LIMITED','MODEL_TIMEOUT','PROTOCOL_ERROR'):
            runner=Failing(code);queue.runner=runner
            failed=False
            try:await provider.text_chat(prompt='synthetic failure',func_tool=None,request_max_retries=1)
            except Exception:failed=True
            report['failure_attempts'][code]={'failed':failed,'attempts':runner.attempts}
            if not failed or runner.attempts!=1:raise RuntimeError('Unexpected provider retries')
    finally:
        await provider.client.close();await server.cleanup()
        (ROOT/'reports/g3-2026-10-16.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'real_answer_exact':report['answer_exact'],'real_cli_attempts':cli.attempts,'failure_attempts':report['failure_attempts']},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--real',action='store_true',required=True);parser.parse_args()
    asyncio.run(verify())
