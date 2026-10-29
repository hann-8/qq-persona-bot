import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from qqbot_gateway.workbuddy_cli_runner import CLIRunner
from qqbot_gateway.token_budget import InputBudget
from qqbot_gateway.errors import GatewayError


FAKE = r'''
import json,os,sys,time,subprocess
from pathlib import Path
base=Path(__file__).parent
mode=(base/'mode').read_text()
(base/'argv.json').write_text(json.dumps({'argv':sys.argv[1:], 'memory':os.environ.get('CODEBUDDY_DISABLE_AUTO_MEMORY')}))
def send(value):print(json.dumps(value),flush=True)
if '--input-format' in sys.argv:
 request=json.loads(sys.stdin.readline())
 (base/'control.json').write_text(json.dumps(request))
 if mode=='timeout':
  child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])
  (base/'child.pid').write_text(str(child.pid));time.sleep(60)
 models=[{'id':'deepseek-v4.1-flash','maxInputTokens':1000000,'reasoning':{'supportedEfforts':['low','high','max']}}]
 if mode=='changed-capability':models[0]['reasoning']['supportedEfforts']=['low']
 response={'type':'control_response','response':{'subtype':'success',
   'request_id':request['request_id'],'response':{'rawModels':models}}}
 if mode=='wrong-id':response['response']['request_id']='wrong'
 if mode=='control-error':response['response']['subtype']='error'
 if mode=='config-errors':response['response']['response']['errors']={'model':'bad'}
 send(response)
 if mode=='duplicate-control':send(response)
 user=sys.stdin.readline()
 if user:(base/'user.json').write_text(user)
 if not user:sys.exit(0)
else:
 user=sys.stdin.read();(base/'user.json').write_text(user)
send({'type':'system','subtype':'init','model':'deepseek-v4.1-flash','tools':[],'mcp_servers':[]})
if mode=='missing-final':sys.exit(0)
if mode=='backend-error':
 send({'type':'result','is_error':True,'errors':['PRIVATE_SENTINEL https://example.com/private']});sys.exit(0)
result={'type':'result','subtype':'success','is_error':False,'result':'answer'}
send(result)
if mode=='duplicate-final':send(result)
'''


class RunnerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.script=self.root/'fake.py';self.script.write_text(FAKE,encoding='utf-8')

    def tearDown(self):self.temp.cleanup()

    async def test_backend_failure_keeps_only_safe_metadata_after_cleanup(self):
        runner=self.runner('backend-error')
        with self.assertRaises(GatewayError) as raised:
            await runner.run('SYS','Synthetic question','trace')
        self.assertEqual(raised.exception.code,'BACKEND_UNAVAILABLE')
        raw=(self.root/'state/cli-last-failure.json').read_text(encoding='utf-8')
        summary=json.loads(raw)
        self.assertEqual(summary['code'],'BACKEND_UNAVAILABLE')
        self.assertTrue(summary['initialized'])
        self.assertEqual(summary['tool_calls'],0)
        self.assertNotIn('PRIVATE_SENTINEL',raw)
        self.assertNotIn('https://',raw)
        self.assertEqual(list((self.root/'runtime/requests').iterdir()),[])

    def test_failure_summary_never_copies_raw_guard_errors(self):
        from qqbot_gateway.workbuddy_cli_runner import failure_summary,ResultParser
        summary=failure_summary('raw private trace','unknown',ResultParser(),
            dict(reason='https://example.com/private',guard_reason='PRIVATE_SENTINEL',hook_error='secret'))
        self.assertEqual(summary['reason'],'suppressed')
        self.assertEqual(summary['guard_reason'],'suppressed')
        self.assertNotIn('PRIVATE_SENTINEL',json.dumps(summary))

    def runner(self,mode='success',effort='high',budget=None):
        (self.root/'mode').write_text(mode)
        runner=object.__new__(CLIRunner)
        for key,value in {'root':self.root,'node':Path(sys.executable),'entry':self.script,
                          'model':'deepseek-v4.1-flash','timeout':2,'cleanup_seconds':2,
                          'reasoning_effort':effort,'budget':budget or InputBudget(),'denied':['Read','Write'],
                          'attempts':0,'control_attempts':0,'user_messages_sent':0,'last_protocol':[],
                          'last_parameters':{},'control_timeout':1}.items():setattr(runner,key,value)
        return runner

    async def test_explicit_effort_single_user_after_control_and_isolation(self):
        runner=self.runner()
        self.assertEqual((await runner.run('SYS','[{"role":"user","content":"hi"}]','test')).text,'answer')
        self.assertEqual((runner.attempts,runner.control_attempts,runner.user_messages_sent),(1,1,1))
        argv=json.loads((self.root/'argv.json').read_text())
        self.assertEqual(argv['memory'],'1')
        self.assertIn('--effort',argv['argv']);self.assertIn('high',argv['argv'])
        index=argv['argv'].index('--settings')
        self.assertIs(json.loads(argv['argv'][index+1])['autoCompactEnabled'],False)
        self.assertIs(json.loads(argv['argv'][index+1])['alwaysThinkingEnabled'],False)
        user=json.loads((self.root/'user.json').read_text())
        self.assertEqual(user['type'],'user');self.assertEqual(user['message']['role'],'user')
        self.assertEqual(list((self.root/'runtime/requests').iterdir()),[])

    async def test_auto_keeps_verified_text_path_without_effort_override(self):
        runner=self.runner(effort='auto')
        await runner.run('SYS','question','test')
        argv=json.loads((self.root/'argv.json').read_text())['argv']
        self.assertNotIn('--effort',argv);self.assertNotIn('--input-format',argv)
        self.assertEqual(runner.control_attempts,0);self.assertEqual(runner.user_messages_sent,1)

    async def test_pre_user_control_failures_never_infer(self):
        for mode in ('wrong-id','control-error','config-errors','changed-capability'):
            runner=self.runner(mode)
            with self.subTest(mode=mode),self.assertRaises(GatewayError):await runner.run('SYS','question','test')
            self.assertEqual((runner.attempts,runner.user_messages_sent),(1,0))
            self.assertFalse((self.root/'user.json').exists())

    async def test_control_timeout_cleans_owned_child_before_user(self):
        import psutil
        runner=self.runner('timeout');runner.control_timeout=.5
        with self.assertRaises(GatewayError):await runner.run('SYS','question','test')
        self.assertEqual(runner.user_messages_sent,0)
        pid=int((self.root/'child.pid').read_text())
        self.assertFalse(psutil.pid_exists(pid))

    async def test_duplicate_or_missing_terminal_and_duplicate_control_fail(self):
        for mode in ('duplicate-final','missing-final','duplicate-control'):
            runner=self.runner(mode)
            with self.subTest(mode=mode),self.assertRaises(GatewayError):await runner.run('SYS','question','test')
            self.assertEqual(runner.attempts,1)

    async def test_over_budget_zero_cli_attempts(self):
        runner=self.runner(budget=InputBudget(limit=100,overhead=32))
        with self.assertRaises(GatewayError):await runner.run('SYS','🙂'*100,'test')
        self.assertEqual((runner.attempts,runner.user_messages_sent),(0,0))
        self.assertFalse((self.root/'argv.json').exists())


if __name__=='__main__':unittest.main()
