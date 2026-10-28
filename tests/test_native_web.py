"""Native permission/protocol tests; only synthetic processes, never the CLI."""
import asyncio
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT)]
from qqbot_gateway.workbuddy_cli_runner import ResultParser
from qqbot_gateway.web_policy import native_tools,current_question,validate_web
from qqbot_gateway.errors import GatewayError

CFG=dict(provider='codebuddy_native',enabled=True,search_enabled=True)


def native_fake(script):
    """Extend the existing bottom substitute with installed-CLI event envelopes."""
    script=script.replace("'tools':[]","'tools':sys.argv[sys.argv.index('--tools')+1].split(',') if sys.argv[sys.argv.index('--tools')+1] else []")
    lines=[]
    for line in script.splitlines():
        lines.append(line)
        if "'subtype':'init'" in line:
            lines.extend('''
if sys.argv[sys.argv.index('--tools')+1]:
 print(json.dumps({'type':'assistant','message':{'content':[{'type':'text','text':'synthetic intermediate'}]}}),flush=True)
 for i,name in enumerate(sys.argv[sys.argv.index('--tools')+1].split(',')):
  print(json.dumps({'type':'assistant','message':{'content':[{'type':'tool_use','id':str(i),'name':name,'input':{'url':'https://example.com/'}}]}}),flush=True)
  print(json.dumps({'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':str(i),'content':'synthetic public facts'}]}}),flush=True)
'''.strip('\n').splitlines())
    return "import sys\nsys.stdin.reconfigure(encoding='utf-8')\n"+'\n'.join(lines)+'\n'


class ParserTests(unittest.TestCase):
    def event(self,p,kind,**fields):p.line(json.dumps(dict(type=kind,**fields)))
    def init(self,p,tools=('WebFetch',),**kw):
        self.event(p,'system',subtype='init',tools=list(tools),mcp_servers=[],model='model',**kw)
    def call(self,p,name='WebFetch',id='call'):
        self.event(p,'assistant',message=dict(content=[dict(type='tool_use',id=id,name=name,input={})]))
    def result(self,p,id='call',error=False):
        self.event(p,'user',message=dict(content=[dict(type='tool_result',tool_use_id=id,content='facts',is_error=error)]))
    def final(self,p):self.event(p,'result',subtype='success',is_error=False,result='final only')

    def test_only_final_after_multiple_tool_cycles(self):
        p=ResultParser('model',('WebFetch',));self.init(p)
        self.event(p,'assistant',message=dict(content=[dict(type='text',text='private progress')]))
        for i in range(3):self.call(p,id=str(i));self.result(p,id=str(i),error=i==0)
        self.assertIsNone(p.result);self.final(p);self.assertEqual(p.finish(0),'final only')

    def test_search_parser_only_when_explicitly_expected(self):
        p=ResultParser('model',('WebFetch','WebSearch'));self.init(p,('WebSearch','WebFetch'))
        self.call(p,name='WebSearch');self.result(p);self.final(p);self.assertEqual(p.finish(0),'final only')

    def test_init_rejects_every_unexpected_tool_and_mcp(self):
        for tools in ([],['Read'],['WebFetch','Bash'],['WebFetch','WebSearch'],['mcp__web__Fetch'],['WebFetch','WebFetch']):
            with self.subTest(tools=tools),self.assertRaises(GatewayError):self.init(ResultParser('model',('WebFetch',)),tools)
        p=ResultParser('model',('WebFetch',))
        with self.assertRaises(GatewayError):self.event(p,'system',subtype='init',model='model',tools=['WebFetch'],mcp_servers=[dict(name='anything')])

    def test_rejects_other_tools_before_init_after_final_or_unmatched_results(self):
        for name in ('Bash','PowerShell','Read','Write','Agent','mcp__fetch','WebSearch',[]):
            p=ResultParser('model',('WebFetch',));self.init(p)
            with self.subTest(name=name),self.assertRaises(GatewayError):self.call(p,name=name)
        p=ResultParser('model',('WebFetch',))
        with self.assertRaises(GatewayError):self.call(p)
        p=ResultParser('model',('WebFetch',));self.init(p)
        with self.assertRaises(GatewayError):self.result(p)
        self.call(p)
        with self.assertRaises(GatewayError):self.final(p)
        self.result(p);self.final(p)
        with self.assertRaises(GatewayError):self.call(p,id='late')

    def test_original_no_tool_protocol_stays_closed(self):
        p=ResultParser('model');self.init(p,());self.final(p);self.assertEqual(p.finish(0),'final only')
        p=ResultParser('model');self.init(p,())
        with self.assertRaises(GatewayError):self.call(p)


class PolicyTests(unittest.TestCase):
    def test_flags_provider_and_image_isolation(self):
        self.assertEqual(native_tools(CFG,'read https://example.com'),('WebFetch',))
        self.assertEqual(native_tools(CFG,'不要联网，只讨论'),())
        self.assertEqual(native_tools(CFG,"don't browse"),())
        self.assertEqual(native_tools(CFG,'image + URL',image=True),())
        self.assertEqual(native_tools(CFG,'hello',disabled=True),())
        self.assertEqual(native_tools(CFG|dict(provider='bing_rss'),'hello'),())
        self.assertEqual(native_tools(CFG|dict(enabled=False),'hello'),())
        self.assertEqual(validate_web({})['provider'],'codebuddy_native')
        self.assertFalse(validate_web({})['enabled']);self.assertFalse(validate_web({})['search_enabled'])
        # Availability would still require the independent Search switch.
        with patch('qqbot_gateway.web_policy.NATIVE_SEARCH_AVAILABLE',True):
            self.assertEqual(native_tools(CFG|dict(enabled=False),'hi'),('WebSearch',))
            self.assertEqual(native_tools(CFG|dict(search_enabled=False),'hi'),('WebFetch',))

    def test_optout_uses_current_target_not_history_or_old_anchor(self):
        source=dict(target_seq=2,messages=[dict(seq=1,text='联网读URL'),dict(seq=2,text='不要联网')],web_anchor='old')
        prompt=json.dumps([dict(role='user',content=json.dumps(source))])
        self.assertEqual(current_question(prompt,dict(version=2)),'不要联网')
        self.assertEqual(current_question(prompt,dict(version=1)),'不要联网')
        self.assertEqual(native_tools(CFG,current_question(prompt,dict(version=2))),())

    def test_gateway_no_external_web_runner_and_shared_network_preserved(self):
        self.assertNotIn('WebRunner', (ROOT/'src/qqbot_gateway/model_gateway.py').read_text(encoding='utf-8'))
        from qqbot_gateway.public_http import PublicHTTP
        from qqbot_gateway import vision
        self.assertIsNotNone(PublicHTTP);self.assertIn('自然接话',vision.POLICY)


class NativeRunnerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        import test_cli_runner
        self.fixture=test_cli_runner.RunnerTests();self.fixture.setUp();self.root=self.fixture.root
        self.fixture.script.write_text(native_fake(test_cli_runner.FAKE),encoding='utf-8')
    def tearDown(self):self.fixture.tearDown()
    def runner(self,**kw):
        runner=self.fixture.runner(effort='low',**kw);runner.web_settings=CFG
        runner.denied=['WebFetch','WebSearch','Bash','Read','Write','mcp__*']
        return runner
    def argv(self):return json.loads((self.root/'argv.json').read_text())['argv']
    async def test_native_args_low_deny_and_final_only_single_attempt(self):
        runner=self.runner();timeout=runner.timeout
        result=await runner.run('policy','[{"role":"user","content":"读 https://example.com"}]','native')
        self.assertEqual(result.text,'answer');self.assertEqual(runner.attempts,1);self.assertEqual(runner.timeout,timeout)
        args=self.argv()
        for flag,value in [('--tools','WebFetch'),('--max-turns','8'),('--allowedTools','WebFetch'),('--permission-mode','dontAsk'),('--setting-sources','none'),('--model','deepseek-v4.1-flash'),('--effort','low')]:self.assertEqual(args[args.index(flag)+1],value)
        deny=args[args.index('--disallowedTools')+1:args.index('--allowedTools')]
        self.assertNotIn('WebFetch',deny);self.assertIn('WebSearch',deny);self.assertIn('Bash',deny);self.assertIn('mcp__*',deny)
        self.assertIn('--strict-mcp-config',args);self.assertIn('--mcp-config',args)
        self.assertNotIn('bypassPermissions',args);self.assertNotIn('default',args)
        self.assertEqual(runner.last_parameters['native_web_tools'],['WebFetch'])
    async def test_current_optout_and_control_only_remain_empty_tools(self):
        runner=self.runner()
        await runner.run('policy','[{"role":"user","content":"不要联网"}]','optout')
        self.assertEqual(self.argv()[self.argv().index('--tools')+1],'')
        self.assertEqual(self.argv()[self.argv().index('--max-turns')+1],'2')
        self.assertNotIn('--allowedTools',self.argv())
        runner=self.runner();await runner.inspect_models('metadata')
        self.assertEqual(runner.user_messages_sent,0);self.assertEqual(self.argv()[self.argv().index('--tools')+1],'')
    async def test_image_plus_url_stays_no_tools(self):
        from qqbot_gateway.vision import CURRENT
        from test_lap42_vision import image
        runner=self.runner();token=CURRENT.set(image())
        try:
            await runner.run('policy','[{"role":"user","content":"看图和 https://example.com"}]','image')
        finally:CURRENT.reset(token)
        args=self.argv();self.assertEqual(args[args.index('--tools')+1],'');self.assertEqual(args[args.index('--max-turns')+1],'2')
    async def test_cancel_native_attempt_cleans_up_without_retry(self):
        runner=self.runner(mode='timeout');runner.timeout=5
        task=asyncio.create_task(runner.run('policy','[{"role":"user","content":"hi"}]','cancel'))
        for _ in range(100):
            if (self.root/'child.pid').exists():break
            await asyncio.sleep(.01)
        self.assertTrue((self.root/'child.pid').exists());task.cancel()
        with self.assertRaises(asyncio.CancelledError):await task
        self.assertEqual(runner.attempts,1);self.assertFalse(runner.cleanup_status()['blocked'])
    async def test_stop_native_attempt_cleans_up_without_retry(self):
        runner=self.runner(mode='timeout');runner.timeout=5
        with patch.dict(os.environ,QQBOT_INSTANCE_ID='synthetic'):
            task=asyncio.create_task(runner.run('policy','[{"role":"user","content":"hi"}]','stop'))
            for _ in range(100):
                if (self.root/'child.pid').exists():break
                await asyncio.sleep(.01)
            (self.root/'state').mkdir(exist_ok=True)
            (self.root/'state/stop-request.json').write_text('{"instance_id":"synthetic"}')
            with self.assertRaises(GatewayError) as error:await task
        self.assertEqual(error.exception.code,'SHUTTING_DOWN');self.assertEqual(runner.attempts,1)
        self.assertFalse(runner.cleanup_status()['blocked'])

if __name__=='__main__':unittest.main()
