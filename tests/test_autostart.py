import asyncio
from contextlib import ExitStack
from dataclasses import replace
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch,Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from scripts import autostart,manage
from qqbot_gateway.config import configuration_lock
from qqbot_gateway.lifecycle import atomic_json
import test_onebot_gate as gate_tests
message=gate_tests.message


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='开机 中文 path ');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.startup=self.root/'临时 Startup'
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(manage,'ROOT',self.root))
        self.calls=[]
    def create(self,path,target,arguments,working):
        self.calls.append((path,target,arguments,working))
        path.write_text(json.dumps([str(target),arguments,str(working)]),encoding='utf-8')
    def register(self,action,**kwargs):return autostart.registration(self.root,action,startup=self.startup,create=self.create,**kwargs)
    def test_registration_idempotency_unicode_and_removal(self):
        self.assertEqual(self.register('status')['state'],'not_installed')
        self.assertFalse(self.startup.exists())
        self.assertEqual(self.register('install')['state'],'installed')
        self.assertEqual(self.register('install')['state'],'installed');self.assertEqual(len(self.calls),1)
        _,target,args,working=self.calls[0]
        self.assertEqual(target,self.root/'开机启动机器人.cmd');self.assertEqual(working,self.root)
        self.assertEqual(args,'--delay-seconds 30 --network-wait-seconds 120')
        self.assertEqual(self.register('status')['state'],'installed')
        unrelated=self.startup/'Other.lnk';unrelated.write_bytes(b'outside')
        self.assertEqual(self.register('remove')['state'],'removed')
        self.assertEqual(unrelated.read_bytes(),b'outside');self.assertEqual(self.register('remove')['state'],'not_installed')
    def test_foreign_and_changed_links_preserved(self):
        self.startup.mkdir();link=self.startup/autostart.LINK_NAME;link.write_bytes(b'foreign')
        for action in ('install','remove'):
            with self.assertRaises(ValueError):self.register(action)
        self.assertEqual(link.read_bytes(),b'foreign')
        link.unlink();self.register('install');link.write_bytes(b'changed')
        for action in ('install','remove'):
            with self.assertRaises(ValueError):self.register(action)
        self.assertEqual(self.register('status')['state'],'ownership_unknown');self.assertEqual(link.read_bytes(),b'changed')
    def test_ledger_tampering_or_missing_link_blocks(self):
        self.register('install')
        ledger=self.root/'state/autostart-registration.json';value=json.loads(ledger.read_text())
        value['owner']['target']='foreign.cmd';atomic_json(ledger,value)
        with self.assertRaises(ValueError):self.register('remove')
        self.assertTrue((self.startup/autostart.LINK_NAME).exists())
    def test_install_failure_rolls_back_only_new_own_link(self):
        with patch.object(autostart,'atomic_json',side_effect=OSError('synthetic')):
            with self.assertRaises(OSError):self.register('install')
        self.assertEqual(list(self.startup.iterdir()),[])
        self.assertFalse((self.root/'state/autostart-registration.json').exists())
    def test_single_run_reuses_manage_once_and_waits_without_config_lock(self):
        now=[0];sleeps=[]
        def sleep(seconds):
            with configuration_lock(self.root):pass
            sleeps.append(seconds);now[0]+=seconds
        def start(**kwargs):
            self.assertEqual(kwargs,dict(full=True,login_diagnostics=True,wait_login_seconds=120))
            # Concurrent wrapper cannot start another instance even though config is unlocked.
            with self.assertRaises(ValueError):autostart.run(self.root,0,0,start=lambda **_:self.fail('duplicate'),network=lambda:True,sleep=lambda _:None)
            atomic_json(self.root/'state/service-mode.json',{'instance_id':'a'*32})
            return dict(state='qq_ready',instance_id='a'*32)
        launcher=Mock(side_effect=start)
        result=autostart.run(self.root,start=launcher,network=lambda:now[0]>=32,sleep=sleep,clock=lambda:now[0])
        self.assertEqual(result['state'],'qq_ready');launcher.assert_called_once();self.assertEqual(sleeps,[30,1,1])
        status=json.loads((self.root/'state/autostart-status.json').read_text());self.assertTrue(status['qq_ready'])
    def test_dependency_timeout_never_starts_and_does_not_replace_new_instance(self):
        now=[0];start=Mock()
        def sleep(seconds):
            now[0]+=seconds
            atomic_json(self.root/'state/service-mode.json',{'instance_id':'new'})
        result=autostart.run(self.root,0,2,start=start,network=lambda:False,sleep=sleep,clock=lambda:now[0])
        self.assertEqual(result['state'],'dependency_timeout');start.assert_not_called()
        self.assertFalse((self.root/'state/autostart-status.json').exists())
    def test_partial_blocks_once_no_retry_or_cleanup(self):
        for failure in ('PARTIAL_RUNNING','PORT_CONFLICT','cleanup_unknown'):
            with self.subTest(failure=failure):
                start=Mock(side_effect=RuntimeError(failure))
                result=autostart.run(self.root,0,0,start=start,network=lambda:True,sleep=lambda _:None)
                self.assertEqual(result['state'],'start_blocked');start.assert_called_once()
    def test_stop_marker_blocks_late_ready_write(self):
        atomic_json(self.root/'state/service-mode.json',{'instance_id':'old'})
        atomic_json(self.root/'state/stop-request.json',{'instance_id':'old'})
        self.assertFalse(autostart.write_status(self.root,'old',0,'finished','qq_ready',True))
        self.assertFalse((self.root/'state/autostart-status.json').exists())

    def test_old_wait_result_cannot_overwrite_new_instance(self):
        atomic_json(self.root/'state/service-mode.json',{'instance_id':'new'})
        atomic_json(self.root/'state/autostart-status.json',{'instance_id':'new','phase':'starting'})
        self.assertFalse(autostart.write_status(self.root,'old',0,'finished','qq_ready',True))
        self.assertEqual(json.loads((self.root/'state/autostart-status.json').read_text())['phase'],'starting')
    def test_cli_rejects_login_check_for_text_and_bad_bounds_before_start(self):
        with patch.object(manage,'start_channel') as start:
            for argv in (['start-text','--login-check-only'],['status','--login-diagnostics'],['start-channel','--wait-login-seconds','301']):
                with patch.object(sys,'argv',['manage.py',*argv]),self.assertRaises(SystemExit):manage.main()
            start.assert_not_called()
    def test_windows_helper_arguments_are_structured_hidden(self):
        with patch.object(autostart.subprocess,'run') as run:
            autostart.shortcut(self.root/'中文 file.lnk',self.root/'开机启动机器人.cmd','--delay-seconds 30',self.root)
        argv=run.call_args.args[0]
        self.assertIn('-File',argv);self.assertEqual(argv[-4],str(self.root/'中文 file.lnk'))
        self.assertNotIn('-Command',argv);self.assertEqual(run.call_args.kwargs['creationflags'],autostart.subprocess.CREATE_NO_WINDOW)


class LoginCheckGateTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=gate_tests.TransportTests.asyncSetUp
    asyncTearDown=gate_tests.TransportTests.asyncTearDown
    connect=gate_tests.TransportTests.connect
    # Existing socket setup connects only ephemeral fake OneBot and upstream servers.
    async def test_free_paused_gate_blocks_messages_before_store_or_upstream(self):
        from unittest.mock import patch
        self.gate.root=Path(self.temp.name)
        self.gate.config=replace(self.gate.config,participation_mode='free')
        atomic_json(self.gate.root/'state/stop-request.json',{'instance_id':'login-check'})
        with patch.dict('os.environ',{'QQBOT_INSTANCE_ID':'login-check'}):
            ws,up=await self.connect()
            with patch.object(self.gate.store,'reserve',side_effect=AssertionError('paused must not reserve')):
                event=message();event['message']=[{'type':'text','data':{'text':'synthetic free input'}}]
                await ws.send_json(event)
                await ws.send_json({'post_type':'meta_event','meta_event_type':'heartbeat','self_id':222,'status':{'online':True},'interval':5000})
                # Heartbeat provides an ordering barrier through the real gate loop.
                await asyncio.wait_for(self.received.get(),2)
                self.assertTrue(self.received.empty())
                from qqbot_gateway.napcat_login_observer import gate_state
                self.assertEqual(gate_state(self.gate.status(),paused=True),'qq_session_ready')
            await ws.close()
