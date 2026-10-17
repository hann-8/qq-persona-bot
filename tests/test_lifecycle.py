import asyncio
from contextlib import ExitStack
from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch, Mock

import psutil
from aiohttp import web, ClientSession

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from qqbot_gateway.lifecycle import atomic_json,stopping
from qqbot_gateway.config import configuration_lock
from qqbot_gateway.model_gateway import ModelQueue,application
from scripts import manage


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='机器人 path ')
        self.root=Path(self.temp.name)
        self.stack=ExitStack()
        self.stack.enter_context(patch.object(manage,'ROOT',self.root))
        self.stack.enter_context(patch.object(manage,'STATE',self.root/'state/managed-processes.json'))
    def tearDown(self):self.stack.close();self.temp.cleanup()

    def test_instance_bound_marker_and_atomic_failure(self):
        path=self.root/'state/stop-request.json'
        atomic_json(path,{'instance_id':'old'})
        self.assertFalse(stopping(self.root,'new'));self.assertTrue(stopping(self.root,'old'))
        original=path.read_bytes()
        with patch('qqbot_gateway.lifecycle.os.replace',side_effect=OSError('write failed')):
            with self.assertRaises(OSError):atomic_json(path,{'instance_id':'new'})
        self.assertEqual(path.read_bytes(),original)
        self.assertEqual(list(path.parent.glob('*.tmp')),[])

    def test_pid_reuse_and_repeated_stop_do_not_kill_unowned_process(self):
        entry={'pid':os.getpid(),'created':psutil.Process().create_time()-100,'component':'model'}
        manage.save([entry]);self.assertIsNone(manage.alive(entry))
        manage.stop_project(grace=0);manage.stop_project(grace=0)
        self.assertEqual(manage.read_state(),[])

    def test_cleanup_failure_preserves_identity(self):
        entry={'pid':123,'created':1.,'component':'gate'}
        fake=Mock();fake.children.return_value=[];fake.terminate.side_effect=psutil.AccessDenied(123)
        fake.kill.side_effect=psutil.AccessDenied(123)
        with patch.object(manage,'alive',return_value=fake),patch.object(manage.psutil,'wait_procs',return_value=([],[fake])):
            with self.assertRaises(RuntimeError):manage.stop([entry])
        self.assertEqual(manage.read_state(),[entry])

    def test_uninspectable_descendants_do_not_lose_parent(self):
        entry={'pid':123,'created':1.,'component':'gate'}
        fake=Mock();fake.children.side_effect=psutil.AccessDenied(123)
        with patch.object(manage,'alive',return_value=fake):
            with self.assertRaises(RuntimeError):manage.stop([entry])
        fake.terminate.assert_not_called()
        self.assertEqual(manage.read_state(),[entry])

    def test_start_failure_cleans_only_newly_created_identities(self):
        napcat=self.root/'napcat'
        (napcat/'versions/9.9.33-52230/resources/app/napcat/config').mkdir(parents=True)
        path=self.root/'runtime/astrbot/data/cmd_config.json';path.parent.mkdir(parents=True)
        atomic_json(path,{'platform_settings':{},'provider_settings':{'proactive_capability':{}}})
        gate=SimpleNamespace(upstream_token='test',allowed_groups={'111'},admin_users={'333'},bot_qq='222')
        created={'pid':123,'created':1.,'component':'astrbot'}
        def captured(entries,*args):entries.append(created)
        with patch.object(manage,'NAPCAT',napcat),patch.object(manage,'load_gate_config',return_value=gate), \
             patch.object(manage,'check_port'),patch.object(manage.socket.socket,'connect_ex',return_value=0), \
             patch.object(manage,'capture',side_effect=captured), \
             patch.object(manage.psutil,'Popen',side_effect=[Mock(),RuntimeError('synthetic start failure')]), \
             patch.object(manage,'stop') as cleanup:
            with self.assertRaisesRegex(RuntimeError,'synthetic'):manage.start_channel()
        cleanup.assert_called_once_with([created])
        self.assertEqual(manage.service_mode()['phase'],'failed')

    def test_stop_preserves_unknown_send_and_never_requeues_interrupted_tasks(self):
        from qqbot_gateway.task_store import TaskStore
        store=TaskStore(self.root/'state/tasks.sqlite')
        for key,status in (('a','running'),('b','send_unknown'),('c','completed')):
            store.accept(key,key);store.set(key,status)
        store.close()
        with patch.object(manage,'read_state',return_value=[{'component':'gate'}]), \
             patch.object(manage,'alive',return_value=True),patch.object(manage,'stop') as cleanup:
            manage.stop_project(grace=.01)
        self.assertEqual(manage.task_counts(),{'unknown':1,'send_unknown':1,'completed':1})
        cleanup.assert_called_once()

    def test_start_stop_share_os_lock(self):
        with configuration_lock(self.root):
            with self.assertRaises(ValueError):manage.start_channel(full=True)
            with self.assertRaises(ValueError):manage.stop_project(grace=0)

    def test_duplicate_start_is_noop_and_partial_does_not_spawn(self):
        with patch.object(manage,'read_state',return_value=[{}]),patch.object(manage,'alive',return_value=True), \
             patch.object(manage,'status_report',return_value={'process_state':'running','mode':'text'}), \
             patch.object(manage,'show_status'),patch.object(manage.subprocess,'run') as child:
            manage.start_channel(full=True);child.assert_not_called()
        with patch.object(manage,'read_state',return_value=[{}]),patch.object(manage,'alive',return_value=True), \
             patch.object(manage,'status_report',return_value={'process_state':'partial','mode':'text'}), \
             patch.object(manage.subprocess,'run') as child:
            with self.assertRaises(RuntimeError):manage.start_channel(full=True)
            child.assert_not_called()

    def test_every_start_attempt_prints_login_url_but_json_status_stays_json(self):
        for full in (False,True):
            for failure in (None,RuntimeError('PARTIAL_RUNNING'),ValueError('invalid config')):
                output=StringIO()
                with patch.object(manage,'_start_channel',side_effect=failure),redirect_stdout(output):
                    if failure:
                        with self.assertRaises(type(failure)):manage.start_channel(full=full)
                    else:manage.start_channel(full=full)
                self.assertIn('NapCat 登录/管理：http://127.0.0.1:6099',output.getvalue())
                self.assertEqual('页面可能暂不可访问' in output.getvalue(),failure is not None)
        output=StringIO()
        with patch.object(manage,'status_report',return_value={'metadata':True}), \
             patch.object(sys,'argv',['manage.py','status','--json']),redirect_stdout(output):
            self.assertEqual(manage.main(),0)
        self.assertEqual(json.loads(output.getvalue()),{'metadata':True})

    def test_port_conflict_does_not_kill_owner(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));sock.listen()
            with self.assertRaisesRegex(RuntimeError,'PORT_CONFLICT.*port='):manage.check_port(sock.getsockname()[1])
            self.assertTrue(manage.port_open(sock.getsockname()[1]))

    def test_status_requires_current_online_and_does_not_probe_model(self):
        entries=[{'component':name} for name in ('astrbot','model','gate','napcat')]
        model={'alive':True,'router_ready':True,'backend_state':'not_probed'}
        channel={'alive':True,'connected':True,'self_id_verified':True,'online':None,'channel_state':'unknown'}
        with patch.object(manage,'read_state',return_value=entries),patch.object(manage,'alive',return_value=True), \
             patch.object(manage,'port_open',return_value=True), \
             patch.object(manage,'fetch_health',side_effect=lambda port:model if port==8765 else channel):
            self.assertFalse(manage.status_report()['can_receive_group_messages'])
            channel.update(online=True,channel_state='connected')
            self.assertTrue(manage.status_report()['can_receive_group_messages'])
            channel['stopping']=True
            self.assertFalse(manage.status_report()['can_receive_group_messages'])

    def test_cleanup_discovers_late_child_and_leaves_external_process(self):
        child_file=self.root/'child.txt'
        code='import subprocess,sys,time; from pathlib import Path; time.sleep(.2); p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(60)"]); Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(60)'
        owned=psutil.Popen([sys.executable,'-c',code,str(child_file)],creationflags=subprocess.CREATE_NO_WINDOW)
        outside=psutil.Popen([sys.executable,'-c','import time; time.sleep(60)'],creationflags=subprocess.CREATE_NO_WINDOW)
        entry={'pid':owned.pid,'created':owned.create_time(),'component':'model'}
        child=None
        try:
            for _ in range(100):
                if child_file.exists():break
                time.sleep(.02)
            self.assertTrue(child_file.exists())
            child=psutil.Process(int(child_file.read_text()))
            child_identity={'pid':child.pid,'created':child.create_time(),'component':'model'}
            manage.stop([entry])
            self.assertIsNone(manage.alive(entry));self.assertIsNone(manage.alive(child_identity))
            self.assertTrue(outside.is_running());self.assertEqual(manage.read_state(),[])
        finally:
            for process in (child,owned,outside):
                if process is not None:
                    try:process.kill()
                    except psutil.NoSuchProcess:pass
                    try:process.wait(timeout=3)
                    except psutil.NoSuchProcess:pass


class StopAdmissionTests(unittest.IsolatedAsyncioTestCase):
    async def test_gateway_stopping_rejects_without_cli(self):
        class Runner:
            attempts=0
            async def run(self,*args):self.attempts+=1;raise AssertionError('must not infer')
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'QQBOT_INSTANCE_ID':'test'}):
            root=Path(directory);atomic_json(root/'state/stop-request.json',{'instance_id':'test'})
            runner=Runner();server=web.AppRunner(application(ModelQueue(runner),'t'*40,root=root))
            await server.setup();site=web.TCPSite(server,'127.0.0.1',0);await site.start()
            try:
                async with ClientSession(trust_env=False) as client:
                    port=site._server.sockets[0].getsockname()[1]
                    async with client.post(f'http://127.0.0.1:{port}/v1/chat/completions',headers={'Authorization':'Bearer '+'t'*40},json={'model':'workbuddy-local','messages':[{'role':'user','content':'hello'}]}) as response:
                        self.assertEqual((await response.json())['error']['code'],'SHUTTING_DOWN')
                self.assertEqual(runner.attempts,0)
            finally:await server.cleanup()
