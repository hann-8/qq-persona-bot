"""Explicit zero-inference CLI probe; no initialize/account/auth controls, no user turns."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import hashlib

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from qqbot_gateway.cli_control import ControlExchange, model_metadata
from qqbot_gateway.workbuddy_cli_runner import CLIRunner


async def probe():
    runner = CLIRunner(ROOT, 'deepseek-v4.1-flash')
    lock = json.loads((ROOT/'config/versions.lock.json').read_text(encoding='utf-8'))
    report = {'cli_version':lock['cli']['version'], 'bundle_sha256':lock['cli']['headless_sha256'],
              'user_messages':0, 'inference_requests':0, 'controls':[], 'models':[]}
    parent = ROOT/'runtime/requests'; parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='lap10-probe-', dir=parent) as directory:
        args = [str(runner.node), str(runner.entry), '-p', '--input-format','stream-json',
                '--output-format','stream-json','--model',runner.model,'--tools','',
                '--strict-mcp-config','--mcp-config',str(ROOT/'config/mcp-empty.json'),
                '--permission-mode','dontAsk','--no-session-persistence','--setting-sources','none',
                '--settings',json.dumps({'autoCompactEnabled':False,'contextWindow':200000}),
                '--disallowedTools',*runner.denied]
        env = os.environ.copy()
        for key in list(env):
            if any(term in key.upper() for term in ('API_KEY','AUTH_TOKEN','ACCESS_TOKEN','BASE_URL')): env.pop(key)
        env.update({'CODEBUDDY_DISABLE_AUTO_MEMORY':'1','CODEBUDDY_CODE_DISABLE_AUTO_MEMORY':'1',
                    'CODEBUDDY_MEMORY_ENABLED':'false','CODEBUDDY_TEAM_MEMORY_ENABLED':'false',
                    'CODEBUDDY_MEMORY_EXTRACTION_DISABLED':'1','CODEBUDDY_MEMORY_RELEVANCE_DISABLED':'1'})
        process = await asyncio.create_subprocess_exec(*args,cwd=directory,env=env,
            stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,
            limit=2*1024*1024,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        owned = psutil.Process(process.pid); tracked = {(owned.pid,owned.create_time()):owned}
        async def monitor():
            while True:
                try:
                    for child in owned.children(recursive=True): tracked[(child.pid,child.create_time())]=child
                except psutil.NoSuchProcess: pass
                await asyncio.sleep(.05)
        async def discard():
            while await process.stderr.read(8192): pass
        watcher=asyncio.create_task(monitor()); stderr=asyncio.create_task(discard())
        try:
            async with asyncio.timeout(10):
                for exchange in (ControlExchange('get_available_models'),
                                 ControlExchange('set_config',{'autoCompactEnabled':False,'contextWindow':200000})):
                    process.stdin.write((json.dumps(exchange.request())+'\n').encode()); await process.stdin.drain()
                    while True:
                        line=await process.stdout.readline()
                        if not line: raise RuntimeError('CLI ended before control acknowledgement')
                        event=json.loads(line)
                        if event.get('type')=='control_response':
                            response=exchange.accept(event)
                            if exchange.subtype=='get_available_models': report['models']=model_metadata(response)
                            else: report['acknowledged']=response.get('updated')
                            report['controls'].append(exchange.subtype)
                            break
                        if event.get('type') in ('assistant','result','user'): raise RuntimeError('Unexpected inference event')
            report['control_probe']='passed'
        except Exception as error:
            report['control_probe']='failed'; report['failure_type']=type(error).__name__
        finally:
            process.stdin.close()
            watcher.cancel(); await asyncio.gather(watcher,return_exceptions=True)
            for child in reversed(list(tracked.values())):
                try:
                    if child.is_running():child.kill()
                except psutil.NoSuchProcess:pass
            _,alive=await asyncio.to_thread(psutil.wait_procs,list(tracked.values()),timeout=4)
            await asyncio.wait_for(process.wait(),1)
            stderr.cancel();await asyncio.gather(stderr,return_exceptions=True)
            report['cleanup_confirmed']=not alive
    # No effective session budget was observed: acknowledgement is deliberately not success evidence.
    report['native_window_effective_verified']=False
    (ROOT/'reports/lap-10-control-2026-10-16.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


def source_audit():
    lock=json.loads((ROOT/'config/versions.lock.json').read_text(encoding='utf-8'))
    source=Path(lock['cli']['entry']).parent.parent/'dist/codebuddy-headless.js'
    raw=source.read_bytes();text=raw.decode('utf-8')
    markers={
        'process_local_settings':'async set(eA,el){await this.deferred.promise,this.cliSettings[eA]=el',
        'effort_cli_read':'eA.reasoningEffort=ec',
        'effort_model_read':'normalizeReasoningEffort(ep)??normalizeReasoningEffort(el.reasoning?.defaultEffort)',
        'regular_compact_guard':'if(!eu&&!1===await this.settingsManager.get("autoCompactEnabled"))',
        'forced_emergency':'force:!0,type:eC.EMERGENCY_AUTO',
        'forced_ptl':'force:!0,skipContinue:!1,type:eC.EMERGENCY_AUTO,trigger:"ptl"',
        'native_override_write':'this.sessionManager.setOverrideContextWindow(ec,eA)',
    }
    report={'bundle_sha256':hashlib.sha256(raw).hexdigest(),'cli_version':lock['cli']['version'],
            'scope':'static locked bundle evidence; not an upstream execution trace',
            'character_offsets':{k:text.find(v) for k,v in markers.items()},
            'forced_compact_exclusion_verified':False}
    assert report['bundle_sha256']==lock['cli']['headless_sha256']
    assert all(offset>=0 for offset in report['character_offsets'].values())
    (ROOT/'reports/lap-10-cli-source-2026-10-16.json').write_text(json.dumps(report,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps(report,indent=2))


async def real():
    """One selected effort, one provider request, isolated loopback and synthetic history."""
    import secrets
    import uuid
    from aiohttp import web, ClientSession
    from astrbot.core.provider.sources.openai_source import ProviderOpenAIOfficial
    from qqbot_gateway.model_gateway import application, ModelQueue
    from qqbot_gateway.token_budget import InputBudget
    from qqbot_gateway.config import load_settings
    settings=load_settings(ROOT/'config/settings.local.yaml')
    model=settings['llm']['model']
    # User's current model is preserved; high is known to be supported by this selected model.
    budget=InputBudget(limit=32768,history_turns=12)
    cli=CLIRunner(ROOT,model,reasoning_effort='high',budget=budget)
    queue=ModelQueue(cli);token=secrets.token_urlsafe(32)
    server=web.AppRunner(application(queue,token,budget=budget),access_log=None,handler_cancellation=True)
    await server.setup();site=web.TCPSite(server,'127.0.0.1',0);await site.start()
    port=site._server.sockets[0].getsockname()[1]
    provider=ProviderOpenAIOfficial({'id':'lap10-local-test','type':'openai_chat_completion','provider':'openai',
        'api_base':f'http://127.0.0.1:{port}/v1','key':[token],'model':'workbuddy-local',
        'modalities':['text'],'custom_extra_body':{},'timeout':100},{})
    report={'model':model,'requested_effort':'high','native_window_effective_verified':False,'passed':False}
    word='LAP10_'+uuid.uuid4().hex[:8]
    try:
        # Negative HTTP budget check must not start CLI or consume inference.
        async with ClientSession(trust_env=False) as client:
            async with client.post(f'http://127.0.0.1:{port}/v1/chat/completions',headers={'Authorization':'Bearer '+token},
                json={'model':'workbuddy-local','messages':[{'role':'user','content':'🙂'*20000}]}) as response:
                report['over_budget_status']=response.status
        assert report['over_budget_status']==422 and cli.attempts==0
        response=await provider.text_chat(prompt='回忆历史口令，只输出口令本身。',
            contexts=[{'role':'user','content':'历史口令是'+word},{'role':'assistant','content':'记住了'}],
            system_prompt='本机合成验证，按要求只输出历史口令，不使用工具。',func_tool=None,request_max_retries=1)
        report['answer_exact']=response.completion_text.strip()==word
        report['passed']=report['answer_exact'] and cli.attempts==1 and cli.user_messages_sent==1
    finally:
        report.update(cli_attempts=cli.attempts,user_messages_sent=cli.user_messages_sent,
                      control_attempts=cli.control_attempts,parameters=cli.last_parameters,
                      protocol=cli.last_protocol,last_error=queue.last_error)
        await provider.client.close();await server.cleanup()
        (ROOT/'reports/lap-10-real-2026-10-16.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in report.items() if k!='protocol'},ensure_ascii=False,indent=2))
    if not report['passed']:raise RuntimeError('Selected effort provider validation failed')


if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--zero-inference',action='store_true');group.add_argument('--real',action='store_true')
    group.add_argument('--source-audit',action='store_true');args=parser.parse_args()
    if args.source_audit:source_audit()
    else:asyncio.run(real() if args.real else probe())
