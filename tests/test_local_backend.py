import asyncio
from copy import deepcopy
import hashlib
import base64
import json
import os
import shutil
import subprocess
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch, MagicMock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'),str(ROOT)]
from qqbot_gateway.backends import BackendResult, resolve_backend, create_runner, numeric_usage
from qqbot_gateway.config import normalize_settings, read_settings, save_settings
from qqbot_gateway.errors import GatewayError
from qqbot_gateway.ollama_ssh_runner import OllamaSSHRunner, clear_unknown
from qqbot_gateway.ssh_transport import SSHTransport, secrets_path, load_access, initialize_access
from qqbot_gateway.token_budget import InputBudget
from qqbot_gateway.persona import session_version
from qqbot_gateway.model_gateway import ModelQueue, application
from scripts.configure_bot import execute, menu

DIGEST = 'a'*64


def snapshot():
    data = yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
    data['bot']['qq']='222';data['access'].update(allowed_groups=['111'],admin_users=['333'])
    return normalize_settings(data)


class ProfileTests(unittest.TestCase):
    def test_backend_menu_and_local_edit_keeps_cli_parameters(self):
        from test_configure_menu import RecordedConsole
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'config').mkdir();path=root/'config/settings.local.yaml'
            data=snapshot();data['llm']['profiles']['ollama_ssh']['expected_digest']=DIGEST
            path.write_text(yaml.safe_dump(data),encoding='utf-8')
            cli=deepcopy(resolve_backend(data))
            # local profile num_predict=1500 -> activate local -> return to CLI
            ui=RecordedConsole(['5','5','4','1500','','2','','1','','0','0'])
            menu(path,ui)
            result=read_settings(path)[0]
            self.assertEqual(resolve_backend(result),cli)
            self.assertEqual(resolve_backend(result,'ollama_ssh')['num_predict'],1500)
            self.assertIn('后端与连接',ui.text);self.assertIn('不自动切换',ui.text)
            original=path.read_bytes()
            with patch('qqbot_gateway.ollama_ssh_runner.OllamaSSHRunner.preflight',side_effect=GatewayError('SSH_UNAVAILABLE')) as check:
                ui=RecordedConsole(['5','4','','0','0']);menu(path,ui)
                check.assert_called_once_with(require_digest=False)
                self.assertIn('家庭SSH连接不可用',ui.text)
                self.assertEqual(path.read_bytes(),original)

    def test_management_python_chinese_space_path_and_external_cwd(self):
        with tempfile.TemporaryDirectory(prefix='机器人 LAP17 ') as temp:
            root=Path(temp);(root/'config').mkdir();(root/'scripts').mkdir();(root/'.venv/Scripts').mkdir(parents=True)
            self.assertFalse((ROOT/'配置机器人.cmd').exists())
            for filename in ('configure_bot.py','console_ui.py'):shutil.copy2(ROOT/'scripts'/filename,root/'scripts'/filename)
            shutil.copytree(ROOT/'src',root/'src',ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copy2(sys.executable,root/'.venv/Scripts/python.exe')
            shutil.copy2(ROOT/'.venv/pyvenv.cfg',root/'.venv/pyvenv.cfg')
            data=snapshot();data['llm']['profiles']['ollama_ssh']['expected_digest']=DIGEST
            path=root/'config/settings.local.yaml';path.write_text(yaml.safe_dump(data),encoding='utf-8')
            env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'.venv/Lib/site-packages');env['PYTHONUTF8']='1'
            for backend in ('ollama_ssh','codebuddy_cli'):
                command=[sys.executable,str(root/'scripts/configure_bot.py'),'backend','set',backend]
                result=subprocess.run(command,cwd=ROOT.parent,env=env,capture_output=True,timeout=10)
                self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
                self.assertEqual(read_settings(path)[0]['llm']['backend'],backend)

    def test_v1_v2_exact_values_extensions_and_conflict(self):
        for version in (1,2):
            data=snapshot();data['schema_version']=version
            cli=data['llm'].pop('profiles')['codebuddy_cli']
            data['chat'].update(cli.pop('input_budget'));data['llm'].update(cli)
            data['llm'].update(model='custom-model',run_timeout_seconds=91)
            data['chat'].update(context_input_limit_tokens=24001,context_overhead_reserve_tokens=1234,output_reserve_tokens=3210,history_turns=13)
            data['extension']={'keep':17};data['llm']['future']={'x':1}
            result=normalize_settings(data);cfg=resolve_backend(result)
            self.assertEqual(cfg['model'],'custom-model');self.assertEqual(cfg['run_timeout_seconds'],91)
            self.assertEqual(cfg['input_budget'],dict(context_input_limit_tokens=24001,context_overhead_reserve_tokens=1234,output_reserve_tokens=3210))
            self.assertEqual(result['chat']['history_turns'],13);self.assertEqual(result['extension'],{'keep':17})
            self.assertEqual(result['llm']['future'],{'x':1});self.assertNotIn('model',result['llm'])
            self.assertIsNone(result['llm']['profiles']['ollama_ssh']['expected_digest'])
            data['llm']['profiles']={'codebuddy_cli':{'model':'different'}}
            with self.assertRaises(ValueError):normalize_settings(data)

    def test_profile_switch_roundtrip_and_inactive_edits_version(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'config').mkdir();path=root/'config/settings.local.yaml'
            data=snapshot();data['llm']['profiles']['ollama_ssh']['expected_digest']=DIGEST
            path.write_text(yaml.safe_dump(data),encoding='utf-8')
            original=path.read_bytes();cli=deepcopy(resolve_backend(data));version=session_version('角色',data)
            execute(path,'context','set','24000');execute(path,'effort','set','high')
            execute(path,'backend','set','ollama_ssh');local=read_settings(path)[0]
            self.assertEqual(resolve_backend(local)['input_budget']['context_input_limit_tokens'],12288)
            self.assertNotEqual(version,session_version('角色',local))
            local['llm']['profiles']['codebuddy_cli']['model']='other'
            self.assertEqual(session_version('角色',read_settings(path)[0]),session_version('角色',local))
            execute(path,'context','set','12000');execute(path,'backend','set','codebuddy_cli')
            saved=read_settings(path)[0];self.assertEqual(resolve_backend(saved)['input_budget']['context_input_limit_tokens'],24000)
            self.assertEqual(resolve_backend(saved)['reasoning_effort'],'high')
            self.assertEqual(resolve_backend(saved,'ollama_ssh')['input_budget']['context_input_limit_tokens'],12000)
            self.assertTrue(any(p.read_bytes()==original for p in (root/'state/config-backups').glob('*')))

    def test_invalid_profile_relationships_and_types(self):
        for key,value in [('num_ctx',True),('num_ctx',65536),('num_predict',4097),('think',True),('temperature',float('nan')),('top_p',0),('expected_digest','bad'),('access_file','../secrets/x'),('access_file','secrets/../../x'),('keep_alive_seconds',-1),('model','qwen:latest'),('model','x:cloud')]:
            data=snapshot();data['llm']['profiles']['ollama_ssh'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):normalize_settings(data)
        data=snapshot();data['llm']['backend']='ollama_ssh'
        with self.assertRaises(ValueError):normalize_settings(data)
        data['llm']['profiles']['ollama_ssh']['expected_digest']=DIGEST
        data['llm']['profiles']['ollama_ssh']['run_timeout_seconds']=126
        with self.assertRaises(ValueError):normalize_settings(data)
        data['llm']['profiles']['ollama_ssh']['run_timeout_seconds']=120
        data['llm']['profiles']['ollama_ssh']['num_predict']=4096
        with self.assertRaises(ValueError):normalize_settings(data)
        data=snapshot();data['llm']['model']='shadow'
        with self.assertRaises(ValueError):normalize_settings(data)

    def test_cli_factory_never_reads_home_credentials(self):
        data=snapshot()
        with patch('qqbot_gateway.ssh_transport.load_access',side_effect=AssertionError('must not read')):
            runner=create_runner(ROOT,data,InputBudget.from_settings(data))
            self.assertEqual(runner.backend,'codebuddy_cli')

    def test_usage_only_allowlisted_nonnegative_integers(self):
        self.assertEqual(numeric_usage({'eval_count':3,'prompt_eval_count':True,'credits':999,'total_cost_usd':0,'secret':'hidden'}),{'eval_count':3})

    def test_native_budget_counts_exact_full_request_and_no_secret_fields(self):
        from qqbot_gateway.ollama_ssh_runner import native_payload
        data=snapshot();data['llm']['backend']='ollama_ssh'
        cfg=resolve_backend(data);budget=InputBudget.from_settings(data)
        prompt='[{"role":"user","content":"中文\\n🙂"}]'
        wire=json.dumps(native_payload(cfg,'SYS',prompt),ensure_ascii=False,allow_nan=False).encode('utf-8')
        self.assertEqual(budget.usage('SYS',prompt),len(wire)+budget.overhead)
        self.assertNotIn(b'access_file',wire);self.assertNotIn(b'expected_digest',wire)


class FakeNative:
    def __init__(self,mode='ok'):
        self.mode=mode;self.calls=[];self.closed=False;self.started=threading.Event()
    def close(self):self.closed=True
    def request(self,method,path,payload=None,*,deadline,before_send=None):
        self.calls.append((method,path,payload))
        if path=='/api/version':return {'version':'synthetic'}
        if path=='/api/tags':return {'models':[] if self.mode=='missing' else [{'name':'qwen3.5:9b-q4_K_M','digest':'b'*64 if self.mode=='digest' else DIGEST}]}
        if path=='/api/show':return {'capabilities':['completion','thinking'],'thinking':{'values':[True] if self.mode=='no-think-false' else [False,True]},'model_info':{'qwen35.context_length':262144}}
        if path=='/api/ps':return {'models':[]}
        if before_send:before_send()
        self.started.set()
        if self.mode in ('timeout','cancel'):
            while not self.closed:time.sleep(.002)
            raise OSError('synthetic closed channel')
        if self.mode=='disconnect':raise OSError('synthetic lost response')
        result={'model':'qwen3.5:9b-q4_K_M','done':True,'done_reason':'stop','message':{'role':'assistant','content':'你好🙂'},'prompt_eval_count':12,'eval_count':3}
        if self.mode=='incomplete':result['done']=False
        if self.mode=='wrong-model':result['model']='other'
        if self.mode=='thinking':result['message']['thinking']='hidden reasoning'
        if self.mode=='tool':result['message']['tool_calls']=[{'function':{'name':'exec'}}]
        if self.mode=='markup':result['message']['content']='<tool_call>Read</tool_call>'
        if self.mode=='large':result['message']['content']='a'*(512*1024+1)
        return result


class NativeRunnerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.cfg=resolve_backend(snapshot(),'ollama_ssh');self.cfg['expected_digest']=DIGEST
    async def asyncTearDown(self):self.temp.cleanup()
    def runner(self,mode='ok'):
        self.fake=FakeNative(mode)
        return OllamaSSHRunner(self.root,self.cfg,InputBudget(),transport_factory=lambda *a:self.fake)

    async def test_metadata_zero_generation_and_parameter_evidence(self):
        runner=self.runner();result=await runner.preflight()
        self.assertEqual(result['state'],'metadata_ready');self.assertFalse(result['real_generation_verified'])
        self.assertEqual([x[1] for x in self.fake.calls],['/api/version','/api/tags','/api/show','/api/ps'])
        self.assertEqual(runner.attempts,0);self.assertTrue(self.fake.closed)
        for mode,code in [('missing','OLLAMA_MODEL_MISMATCH'),('digest','OLLAMA_DIGEST_MISMATCH'),('no-think-false','OLLAMA_PARAMETERS_UNSUPPORTED')]:
            with self.subTest(mode=mode),self.assertRaises(GatewayError) as error:await self.runner(mode).preflight()
            self.assertEqual(error.exception.code,code)

    async def test_unconfigured_digest_read_only_inspection_and_startup_gate(self):
        from aiohttp.test_utils import TestServer
        self.cfg['expected_digest']=None
        runner=self.runner()
        result=await runner.preflight(require_digest=False)
        self.assertEqual(result['digest'],DIGEST);self.assertFalse(result['digest_confirmed'])
        runner=self.runner();queue=ModelQueue(runner);server=TestServer(application(queue,'a'*40))
        try:
            with self.assertRaises(GatewayError) as error:await server.start_server()
            self.assertEqual(error.exception.code,'OLLAMA_DIGEST_MISMATCH')
            self.assertIsNone(queue.worker);self.assertEqual(runner.attempts,0)
        finally:await server.close()

    async def test_single_post_complete_wire_and_usage(self):
        runner=self.runner();result=await runner.run('SYS','[{"role":"user","content":"问"}]','test')
        self.assertEqual(result.text,'你好🙂');self.assertEqual(result.usage['eval_count'],3)
        calls=[c for c in self.fake.calls if c[1]=='/api/chat'];self.assertEqual(len(calls),1)
        payload=calls[0][2];self.assertIs(payload['think'],False);self.assertIs(payload['stream'],False)
        self.assertEqual(payload['messages'],[{'role':'system','content':'SYS'},{'role':'user','content':'问'}])
        self.assertEqual(payload['options']['num_ctx'],16384);self.assertEqual(payload['options']['num_predict'],1024)
        self.assertNotIn('tools',payload);self.assertNotIn('format',payload);self.assertFalse(runner.marker.exists())

    async def test_tag_failure_has_no_generation_no_unknown_marker(self):
        for mode in ('missing','digest'):
            runner=self.runner(mode)
            with self.assertRaises(GatewayError):await runner.run('SYS','[]','test')
            self.assertFalse(runner.marker.exists());self.assertEqual(runner.attempts,0)

    async def test_terminal_content_failures_do_not_repeat_or_keep_uncertainty(self):
        for mode in ('wrong-model','thinking','tool','markup','large'):
            runner=self.runner(mode)
            with self.subTest(mode=mode),self.assertRaises(GatewayError):await runner.run('SYS','[]','test')
            self.assertEqual(runner.attempts,1);self.assertFalse(runner.marker.exists())

    async def test_unknown_persists_blocks_next_and_restart_until_explicit_clear(self):
        for mode in ('disconnect','incomplete'):
            runner=self.runner(mode)
            with self.assertRaises(GatewayError) as error:await runner.run('SYS','[]','test')
            self.assertEqual(error.exception.code,'REMOTE_RESULT_UNKNOWN')
            restarted=self.runner()
            with self.assertRaises(GatewayError):await restarted.run('SYS','[]','test2')
            self.assertEqual(restarted.attempts,0)
            with self.assertRaises(ValueError):clear_unknown(self.root,'yes')
            clear_unknown(self.root,'REMOTE_CHECKED_STOPPED')

    async def test_timeout_and_cancel_close_transport_before_next_job(self):
        for mode in ('timeout','cancel'):
            runner=self.runner(mode);runner.profile['run_timeout_seconds']=.05
            task=asyncio.create_task(runner.run('SYS','[]','test'))
            if mode=='cancel':
                while not self.fake.started.is_set():await asyncio.sleep(.002)
                task.cancel()
            with self.assertRaises(GatewayError) as error:await task
            self.assertEqual(error.exception.code,'REMOTE_RESULT_UNKNOWN');self.assertTrue(self.fake.closed)
            clear_unknown(self.root,'REMOTE_CHECKED_STOPPED')

    async def test_queue_cancel_unknown_blocks_already_queued_next(self):
        runner=self.runner('cancel');queue=ModelQueue(runner);await queue.start()
        first=asyncio.create_task(queue.submit('SYS','[]','one'))
        while not self.fake.started.is_set():await asyncio.sleep(.002)
        second=asyncio.create_task(queue.submit('SYS','[]','two'));await asyncio.sleep(.01)
        first.cancel();await asyncio.gather(first,return_exceptions=True)
        with self.assertRaises(GatewayError) as error:await second
        self.assertEqual(error.exception.code,'REMOTE_RESULT_UNKNOWN');self.assertEqual(runner.attempts,1)
        await queue.close()

    async def test_health_separates_metadata_and_generation_counts(self):
        from aiohttp.test_utils import TestClient,TestServer
        runner=self.runner();queue=ModelQueue(runner)
        async with TestClient(TestServer(application(queue,'a'*40))) as client:
            health=await (await client.get('/health')).json()
            self.assertEqual(health['metadata']['state'],'metadata_ready');self.assertEqual(health['cli_attempts'],0)
            self.assertEqual(health['backend_attempts'],0);self.assertFalse(health['real_inference_verified'])


class SSHTests(unittest.TestCase):
    def test_pin_mismatch_before_any_authentication(self):
        access=dict(host='127.0.0.1',port=22,user='synthetic',fingerprint='SHA256:'+'A'*43,password_dpapi='aa')
        fake=MagicMock();fake.is_authenticated.return_value=False;fake.get_remote_server_key.return_value.asbytes.return_value=b'key'
        with patch('socket.create_connection'),patch('paramiko.Transport',return_value=fake),patch('qqbot_gateway.ssh_transport.unprotect_password') as decrypt:
            transport=SSHTransport(ROOT,'unused',access)
            with self.assertRaises(GatewayError) as error:transport.connect(time.monotonic()+5)
            self.assertEqual(error.exception.code,'SSH_HOST_KEY_MISMATCH');fake.auth_password.assert_not_called();decrypt.assert_not_called()
            transport.close()

    def test_pin_verified_once_password_auth_no_agent_or_fallback(self):
        access=dict(host='127.0.0.1',port=22,user='synthetic',fingerprint='SHA256:'+base64.b64encode(hashlib.sha256(b'key').digest()).decode().rstrip('='),password_dpapi='aa')
        fake=MagicMock();fake.is_authenticated.side_effect=[True];fake.get_remote_server_key.return_value.asbytes.return_value=b'key'
        with patch('socket.create_connection'),patch('paramiko.Transport',return_value=fake),patch('qqbot_gateway.ssh_transport.unprotect_password',return_value='synthetic'):
            transport=SSHTransport(ROOT,'unused',access);transport.connect(time.monotonic()+5)
            fake.auth_password.assert_called_once_with('synthetic','synthetic',fallback=False)
            transport.close()

    def http_case(self,raw):
        left,right=socket.socketpair()
        wire=[]
        def server():
            data=b''
            while b'\r\n\r\n' not in data:data+=right.recv(4096)
            wire.append(data);right.sendall(raw);right.close()
        thread=threading.Thread(target=server);thread.start()
        transport=SSHTransport(ROOT,'unused');transport.transport=MagicMock()
        transport.transport.open_channel.return_value=left
        with patch.object(transport,'connect'):
            try:return transport.request('GET','/api/version',deadline=time.monotonic()+2),wire
            finally:
                transport.transport.open_channel.assert_called_once_with('direct-tcpip',('127.0.0.1',11434),('127.0.0.1',0),timeout=unittest.mock.ANY)
                transport.close();thread.join(3)

    def test_actual_http_framing_fixed_target_and_bounded_response(self):
        result,wire=self.http_case(b'HTTP/1.1 200 OK\r\nContent-Length: 15\r\n\r\n{"version":"x"}')
        self.assertEqual(result,{'version':'x'});self.assertIn(b'GET /api/version HTTP/1.1',wire[0])
        result,_=self.http_case(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\nF\r\n{"version":"x"}\r\n0\r\n\r\n')
        self.assertEqual(result,{'version':'x'})
        for raw in (b'HTTP/1.1 302 Found\r\nContent-Length: 0\r\nLocation: http://evil\r\n\r\n',b'HTTP/1.1 200 OK\r\nContent-Length: 99999999\r\n\r\n',b'HTTP/1.1 200 OK\r\nContent-Length: 50\r\n\r\n{}',b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{X'):
            with self.subTest(raw=raw),self.assertRaises(GatewayError):self.http_case(raw)

    def test_secrets_escape_and_plaintext_password_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'secrets').mkdir()
            for path in ('../x','secrets/../../x'):
                with self.assertRaises(ValueError):secrets_path(root,path)
            (root/'secrets/a.json').write_text(json.dumps({'password':'private'}),encoding='utf-8')
            with self.assertRaises(GatewayError):load_access(root,'secrets/a.json')

    def test_explicit_initialization_copies_only_dpapi_and_existing_pin(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'secrets').mkdir();(root/'state').mkdir()
            source='- 主机：127.0.0.1\n- SSH用户：synthetic\n<!-- DPAPI_PASSWORD_BEGIN -->\naa00\n<!-- DPAPI_PASSWORD_END -->'
            (root/'secrets/home-5070-access.local.md').write_text(source,encoding='utf-8')
            (root/'state/home-5070-inventory-2026-10-17.json').write_text(json.dumps({'ssh_server_fingerprint':'SHA256:'+'A'*43}),encoding='utf-8')
            with patch('qqbot_gateway.ssh_transport.unprotect_password',side_effect=AssertionError('no password validation')):
                initialize_access(root,'secrets/runtime.json')
            access=load_access(root,'secrets/runtime.json')
            self.assertEqual(access['password_dpapi'],'aa00');self.assertNotIn('password',access)
            with self.assertRaises(ValueError):initialize_access(root,'secrets/runtime.json')
            self.assertEqual((root/'secrets/home-5070-access.local.md').read_text(encoding='utf-8'),source)


if __name__=='__main__':unittest.main()
