"""Two real local provider calls for memory regression, never sends QQ messages."""
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
from qqbot_gateway.model_gateway import application, ModelQueue
from qqbot_gateway.workbuddy_cli_runner import CLIRunner


def memory_files():
    base=Path.home()/'.codebuddy/projects'
    return {str(p) for p in base.glob('*') if 'qqbot-runtime-requests' in p.name.lower()
            for p in (p/'memory').rglob('*') if p.is_file()}


async def verify():
    from astrbot.core.provider.sources.openai_source import ProviderOpenAIOfficial
    import yaml
    settings=yaml.safe_load((ROOT/'config/settings.local.yaml').read_text(encoding='utf-8-sig'))
    cli=CLIRunner(ROOT,settings['llm']['model'])
    queue=ModelQueue(cli)
    token=secrets.token_urlsafe(32)
    server=web.AppRunner(application(queue,token),access_log=None,handler_cancellation=True)
    await server.setup();site=web.TCPSite(server,'127.0.0.1',0);await site.start()
    port=site._server.sockets[0].getsockname()[1]
    provider=ProviderOpenAIOfficial({'id':'g4-local-memory-test','type':'openai_chat_completion','provider':'openai',
        'api_base':f'http://127.0.0.1:{port}/v1','key':[token],'model':'workbuddy-local',
        'modalities':['text'],'custom_extra_body':{},'timeout':180},{})
    report={'real_requests':0,'passed':False}
    before=memory_files()
    try:
        system=(ROOT/'config/persona.md').read_text(encoding='utf-8')
        word='白饭'+uuid.uuid4().hex[:6]
        prompt='记住口令：'+word
        first=await provider.text_chat(prompt=prompt,system_prompt=system,func_tool=None,request_max_retries=1)
        report['real_requests']+=1
        assert word in first.completion_text, 'Memory acknowledgement did not preserve the supplied word'
        second=await provider.text_chat(prompt='刚才的口令是什么？只回复口令本身。',
            contexts=[{'role':'user','content':prompt},{'role':'assistant','content':first.completion_text}],
            system_prompt=system,func_tool=None,request_max_retries=1)
        report['real_requests']+=1
        report.update(answer_exact=second.completion_text.strip()==word,cli_attempts=cli.attempts,
                      last_contract=queue.last_shape,protocol=cli.last_protocol)
        assert report['answer_exact'] and cli.attempts==2, 'Local memory regression failed'
        assert not memory_files()-before, 'Unexpected CLI memory file creation'
        report.update(passed=True,new_cli_memory_files=0)
    finally:
        report['cli_attempts']=cli.attempts
        report['last_error']=queue.last_error
        await provider.client.close();await server.cleanup()
        (ROOT/'reports/g4-memory-2026-10-16.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('passed','real_requests','cli_attempts','answer_exact','new_cli_memory_files')},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--real',action='store_true',required=True);parser.parse_args()
    asyncio.run(verify())
