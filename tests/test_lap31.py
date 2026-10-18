"""LAP-31: fakes and task-created processes only; no real CLI/QQ/model."""
import asyncio
from contextlib import redirect_stdout
from io import StringIO
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src'), str(ROOT/'tests')]
import psutil
import test_cli_runner as runner_fixture
from qqbot_gateway.cleanup_identity import CleanupOwner, CleanupLedger, identity
from qqbot_gateway.errors import GatewayError
from qqbot_gateway.model_gateway import ModelQueue
from qqbot_gateway.lifecycle import atomic_json
from scripts import process_host, manage


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.owner = CleanupOwner(self.root)
        self.owner.reserve()

    def tearDown(self):self.temp.cleanup()

    def entries(self):
        self.owner.record['identities'] = [dict(pid=i, created=1., outcome='pending', root=i==1) for i in range(1, 4)]

    def test_access_denied_does_not_skip_other_known_identities(self):
        self.entries(); second=Mock(); third=Mock()
        def probe(entry):
            return ('access_denied',None) if entry['pid']==1 else ('alive', {2:second,3:third}[entry['pid']])
        with patch('qqbot_gateway.cleanup_identity.inspect',side_effect=probe):
            self.assertEqual(self.owner.sweep(time.monotonic()+1),'identity_unknown')
        second.kill.assert_called_once();third.kill.assert_called_once()
        self.assertEqual(self.owner.record['identities'][0]['outcome'],'access_denied')

    def test_kill_all_before_wait_timeout_and_total_deadline(self):
        self.entries(); calls=[]
        def probe(entry):
            process=Mock();process.kill.side_effect=lambda:calls.append(('kill',entry['pid']))
            def wait(**kw):
                calls.append(('wait',entry['pid']))
                raise psutil.TimeoutExpired(kw['timeout'])
            process.wait.side_effect=wait
            return 'alive',process
        with patch('qqbot_gateway.cleanup_identity.inspect',side_effect=probe):
            self.assertEqual(self.owner.sweep(time.monotonic()+.05),'owned_alive')
        self.assertEqual([c[0] for c in calls[:3]],['kill']*3)
        self.assertEqual(len(calls),6)

    def test_pid_reuse_never_operates_replacement(self):
        self.entries(); replacement=Mock();replacement.create_time.return_value=2.
        with patch('qqbot_gateway.cleanup_identity.psutil.Process',return_value=replacement):
            self.assertEqual(self.owner.sweep(time.monotonic()+1),'observed_empty')
        replacement.kill.assert_not_called();replacement.wait.assert_not_called()
        self.assertEqual({e['outcome'] for e in self.owner.record['identities']},{'identity_changed'})

    def test_identity_limit_never_discards_unknown(self):
        for i in range(128):
            fake=Mock(pid=i+1);fake.create_time.return_value=1.
            self.assertTrue(self.owner.add(fake))
        extra=Mock(pid=1000);extra.create_time.return_value=1.
        self.assertFalse(self.owner.add(extra));self.owner.save()
        self.assertEqual(len(self.owner.ledger.read()['identities']),128)
        with self.assertRaises(GatewayError):self.owner.reserve()
        self.assertIn('capacity_exceeded',self.owner.record['reasons'])

    def test_bounded_resolved_rotation_and_strict_corrupt_ledger(self):
        value=self.owner.record
        value.update(blocked=False,generation_outcome='success',cleanup_outcome='observed_empty')
        for i in range(36):
            self.owner.ledger.write(value);self.owner.ledger.resolve(value,time.monotonic()+2)
        self.assertEqual(len(list(self.owner.ledger.directory.glob('resolved-*.json'))),32)
        self.owner.ledger.path.write_text('{bad',encoding='utf-8')
        self.assertTrue(CleanupOwner(self.root).status()['blocked'])
        with self.assertRaises(GatewayError):CleanupOwner(self.root).reserve()

    def test_oversized_or_unknown_field_ledger_fails_closed(self):
        self.owner.ledger.path.write_text(' '*32769,encoding='utf-8')
        self.assertTrue(CleanupOwner(self.root).status()['blocked'])
        value=self.owner.record|{'argv':'private'}
        atomic_json(self.owner.ledger.path,value)
        with self.assertRaises(ValueError):self.owner.ledger.read()
        for field in ('cleanup_outcome','generation_outcome','reasons','owner','updated'):
            value=self.owner.record|{field:{'invalid':'private'}}
            atomic_json(self.owner.ledger.path,value)
            self.assertTrue(CleanupOwner(self.root).status()['blocked'])

    def test_ledger_write_failure_prevents_any_spawn(self):
        with patch('qqbot_gateway.cleanup_identity.atomic_json',side_effect=OSError('secret path')):
            fresh=CleanupOwner(self.root/'new')
            with self.assertRaises(GatewayError):fresh.reserve()
            self.assertTrue(fresh.status()['blocked'])

    def test_diagnostics_fixed_schema_and_no_private_fields(self):
        self.owner.add(psutil.Process(),root=True)
        status=self.owner.status()
        for private in ('pid','created','owner','identities','argv','prompt','env'):
            self.assertNotIn(private,status)
        line='CLI_CLEANUP trace=0123456789 generation=MODEL_TIMEOUT outcome=identity_unknown coverage=observed_only reason=access_denied count=128 elapsed_ms=5000'
        self.assertEqual(process_host.safe_line('model','INFO '+line),line)
        for bad in (line+' prompt=private',line.replace('access_denied','private'),line.replace('128','129'),line.replace('MODEL_TIMEOUT','PRIVATE_SECRET')):
            self.assertIsNone(process_host.safe_line('model',bad))

    def test_correlated_trace_and_single_unresolved_across_owners(self):
        self.owner.record.update(blocked=False,generation_outcome='success',cleanup_outcome='observed_empty')
        self.owner.ledger.resolve(self.owner.record,time.monotonic()+1)
        self.owner.reserve('abcdef1234')
        self.assertEqual(self.owner.status()['trace'],'abcdef1234')
        competing=CleanupOwner(self.root)
        with self.assertRaises(GatewayError):competing.reserve('0123456789')
        self.assertEqual(self.owner.ledger.read()['trace'],'abcdef1234')

    def test_standalone_check_exits_within_bound_even_if_os_inspection_stalls(self):
        code='import sys,time,asyncio; from pathlib import Path; sys.path.insert(0,sys.argv[1]); import qqbot_gateway.cleanup_identity as c; c.inspect=lambda entry: time.sleep(20); asyncio.run(c.CleanupOwner(Path(sys.argv[2])).check())'
        started=time.monotonic()
        subprocess.run([sys.executable,'-c',code,str(ROOT/'src'),str(self.root)],timeout=4,check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        self.assertLess(time.monotonic()-started,3.5)
        self.assertIsNotNone(self.owner.ledger.read())


class RunnerCleanupTests(unittest.IsolatedAsyncioTestCase):
    setUp=runner_fixture.RunnerTests.setUp
    tearDown=runner_fixture.RunnerTests.tearDown
    runner=runner_fixture.RunnerTests.runner

    async def test_success_cleanup_failure_keeps_original_and_withholds_answer(self):
        runner=self.runner();owner=runner.cleanup_owner();original=owner.sweep
        def fail(deadline,kill=True):
            original(deadline,kill);owner.reason('access_denied');return 'identity_unknown'
        with patch.object(owner,'sweep',side_effect=fail):
            with self.assertRaises(GatewayError) as caught:await runner.run('private system','private prompt','secret-request')
        self.assertEqual(caught.exception.code,'CLEANUP_FAILED')
        record=owner.ledger.read()
        self.assertEqual(record['generation_outcome'],'success')
        self.assertEqual(record['cleanup_outcome'],'identity_unknown')
        self.assertNotIn('private',json.dumps(record));self.assertNotIn('secret-request',json.dumps(record))
        for _ in range(3):
            with self.assertRaises(GatewayError):await runner.run('','','new')
        self.assertEqual(runner.attempts,1)

    async def test_original_timeout_survives_cleanup_failure(self):
        runner=self.runner('timeout');runner.control_timeout=.15
        owner=runner.cleanup_owner();original=owner.sweep
        def fail(deadline,kill=True):
            original(deadline,kill);owner.reason('wait_timeout');return 'owned_alive'
        with patch.object(owner,'sweep',side_effect=fail):
            with self.assertRaises(GatewayError):await runner.run('','','timeout')
        self.assertEqual(owner.ledger.read()['generation_outcome'],'PROTOCOL_ERROR')
        # Control preflight timeout is protocol failure; generation deadline is MODEL_TIMEOUT.
        runner=self.runner('timeout');runner.timeout=.1;runner.control_timeout=2
        runner._cleanup_owner=CleanupOwner(self.root/'independent')
        owner=runner.cleanup_owner();original=owner.sweep
        def fail2(deadline,kill=True):
            original(deadline,kill);owner.reason('wait_timeout');return 'owned_alive'
        with patch.object(owner,'sweep',side_effect=fail2):
            with self.assertRaises(GatewayError):await runner.run('','','timeout2')
        self.assertEqual(owner.ledger.read()['generation_outcome'],'MODEL_TIMEOUT')

    async def test_repeated_cancel_and_close_take_over_same_task(self):
        runner=self.runner('timeout');queue=ModelQueue(runner);await queue.start()
        owner=runner.cleanup_owner();original=owner.sweep;entered=threading.Event();release=threading.Event();calls=[]
        def slow(deadline,kill=True):
            calls.append(1);entered.set();release.wait(.8);return original(deadline,kill)
        with patch.object(owner,'sweep',side_effect=slow):
            submitted=asyncio.create_task(queue.submit('','','cancel'))
            for _ in range(100):
                if (self.root/'child.pid').exists():break
                await asyncio.sleep(.01)
            submitted.cancel();await asyncio.gather(submitted,return_exceptions=True)
            for _ in range(100):
                if entered.is_set():break
                await asyncio.sleep(.01)
            self.assertTrue(entered.is_set());task=owner.task
            close1=asyncio.create_task(queue.close());await asyncio.sleep(.01);close1.cancel()
            await asyncio.gather(close1,return_exceptions=True)
            close2=asyncio.create_task(queue.close());await asyncio.sleep(.01)
            self.assertIs(owner.task,task);self.assertFalse(task.done())
            release.set();await close2
        self.assertEqual(len(calls),1);self.assertTrue(owner.task.done())
        self.assertEqual(owner.record['generation_outcome'],'cancelled')
        self.assertFalse(psutil.pid_exists(int((self.root/'child.pid').read_text())))

    async def test_slow_cleanup_deadline_blocks_queue_while_thread_remains(self):
        runner=self.runner();runner.cleanup_seconds=.05
        owner=runner.cleanup_owner();original=owner.sweep;release=threading.Event()
        def slow(deadline,kill=True):
            release.wait(.5);return original(deadline,kill)
        queue=ModelQueue(runner);await queue.start()
        with patch.object(owner,'sweep',side_effect=slow):
            started=time.monotonic()
            with self.assertRaises(GatewayError):await queue.submit('','','first')
            self.assertLess(time.monotonic()-started,.45)
            self.assertFalse(owner.task.done())
            for i in range(3):
                with self.assertRaises(GatewayError):await queue.submit('','',str(i))
            self.assertEqual(runner.attempts,1)
            release.set();await owner.task
        self.assertTrue(owner.status()['blocked']);self.assertIsNotNone(owner.ledger.read())
        await queue.close()

    async def test_persistence_is_within_same_deadline_and_retains_unknown(self):
        runner=self.runner();runner.cleanup_seconds=.05
        owner=runner.cleanup_owner();original=owner.ledger.resolve;release=threading.Event()
        def slow(value,deadline):
            release.wait(.3);return original(value,deadline)
        with patch.object(owner.ledger,'resolve',side_effect=slow):
            with self.assertRaises(GatewayError):await runner.run('','','disk')
            self.assertFalse(owner.task.done());self.assertTrue(owner.status()['blocked'])
            release.set();await owner.task
        self.assertIsNotNone(owner.ledger.read());self.assertTrue(owner.status()['blocked'])

    async def test_late_cancel_during_success_cleanup_does_not_return_answer(self):
        runner=self.runner();owner=runner.cleanup_owner();original=owner.sweep
        entered=threading.Event();release=threading.Event()
        def slow(deadline,kill=True):
            entered.set();release.wait(.5);return original(deadline,kill)
        with patch.object(owner,'sweep',side_effect=slow):
            task=asyncio.create_task(runner.run('','','latecancel'))
            for _ in range(100):
                if entered.is_set():break
                await asyncio.sleep(.01)
            self.assertTrue(entered.is_set());task.cancel();task.cancel();release.set()
            with self.assertRaises(asyncio.CancelledError):await task
        self.assertEqual(owner.record['generation_outcome'],'success')
        self.assertFalse(owner.status()['blocked'])

    async def test_observed_empty_does_not_unlock_failed_or_historical_job(self):
        runner=self.runner();owner=runner.cleanup_owner();owner.reserve()
        owner.record.update(generation_outcome='success',cleanup_outcome='observed_empty',coverage='job_complete',blocked=False)
        owner.save()
        restarted=self.runner();queue=ModelQueue(restarted);await queue.start()
        self.assertEqual(queue.state,'CLEANUP_FAILED')
        with patch('qqbot_gateway.cleanup_identity.inspect',return_value=('exited',None)),patch('qqbot_gateway.cleanup_identity.psutil.Process.kill') as kill:
            for i in range(3):
                with self.assertRaises(GatewayError):await queue.submit('','',str(i))
            self.assertEqual(restarted.attempts,0);kill.assert_not_called()
        self.assertTrue(restarted.cleanup_status()['blocked']);await queue.close()

    async def test_passive_check_is_rate_limited_no_kill_or_replay(self):
        owner=CleanupOwner(self.root);owner.reserve();owner.add(psutil.Process(),root=True)
        owner.record['cleanup_outcome']='identity_unknown';owner.save()
        with patch('qqbot_gateway.cleanup_identity.inspect',return_value=('exited',None)) as probe,patch('qqbot_gateway.cleanup_identity.psutil.Process.kill') as kill:
            await owner.check();count=probe.call_count;await owner.check()
            self.assertEqual(probe.call_count,count);kill.assert_not_called()
        self.assertTrue(owner.status()['blocked'])

    async def test_ledger_overflow_before_user_has_zero_user_messages(self):
        runner=self.runner();owner=runner.cleanup_owner()
        original=owner.add
        def overflow(*args,**kwargs):
            result=original(*args,**kwargs);owner.reason('capacity_exceeded');return result
        with patch.object(owner,'add',side_effect=overflow):
            with self.assertRaises(GatewayError):await runner.run('','','capacity')
        self.assertEqual(runner.user_messages_sent,0)

    async def test_legacy_success_stays_admissible_and_summaries_bounded(self):
        runner=self.runner();queue=ModelQueue(runner);await queue.start()
        try:
            for i in range(3):self.assertEqual((await queue.submit('','','ok'+str(i))).text,'answer')
            self.assertEqual(queue.state,'ready');self.assertFalse(runner.cleanup_status()['blocked'])
            self.assertEqual(runner.cleanup_status()['coverage'],'observed_only')
            self.assertFalse(runner.cleanup_owner().ledger.path.exists())
        finally:await queue.close()

    async def test_root_first_multilayer_tree_only_owned_processes(self):
        runner=self.runner(effort='auto');runner.timeout=.7
        grand=self.root/'grand.pid';child=self.root/'child.pid'
        grand_code='import time; time.sleep(60)'
        child_code='import subprocess,sys,time; from pathlib import Path; p=subprocess.Popen([sys.executable,"-c",'+repr(grand_code)+']); Path('+repr(str(grand))+').write_text(str(p.pid)); time.sleep(60)'
        preamble='p=subprocess.Popen([sys.executable,"-c",'+repr(child_code)+']); (base/"child.pid").write_text(str(p.pid)); time.sleep(.25)\n'
        text=self.script.read_text(encoding='utf-8').replace("send({'type':'system'",preamble+"send({'type':'system'",1)
        self.script.write_text(text,encoding='utf-8')
        outside=psutil.Popen([sys.executable,'-c','import time; time.sleep(60)'],creationflags=0x08000000 if os.name=='nt' else 0)
        outside_created=outside.create_time();owned=[]
        try:
            task=asyncio.create_task(runner.run('','','tree'))
            for _ in range(100):
                if grand.exists():break
                await asyncio.sleep(.01)
            self.assertTrue(grand.exists())
            for path in (child,grand):
                process=psutil.Process(int(path.read_text()));owned.append((process,process.create_time()))
            with self.assertRaises(GatewayError) as caught:await task
            self.assertEqual(caught.exception.code,'MODEL_TIMEOUT')
            self.assertTrue(outside.is_running());self.assertEqual(outside.create_time(),outside_created)
            for process,_ in owned:self.assertFalse(process.is_running())
            self.assertEqual(runner.cleanup_status()['coverage'],'observed_only')
        finally:
            for process,created in owned+[(outside,outside_created)]:
                try:
                    if process.is_running() and process.create_time()==created:process.kill()
                    process.wait(timeout=3)
                except psutil.NoSuchProcess:pass

    async def test_passive_inspection_timeout_is_bounded_and_retained(self):
        owner=CleanupOwner(self.root);owner.reserve();owner.save()
        done=threading.Event()
        def slow(entry):done.wait(2.2);return 'exited',None
        with patch('qqbot_gateway.cleanup_identity.inspect',side_effect=slow):
            start=time.monotonic();await owner.check()
            self.assertLess(time.monotonic()-start,2.15)
            self.assertTrue(owner.status()['blocked']);self.assertFalse(owner.check_task.done())
            done.set();await owner.check_task

    async def test_manage_cleanup_uses_same_fixed_path(self):
        runner=self.runner();owner=runner.cleanup_owner();owner.reserve()
        output=StringIO()
        with patch.object(manage,'ROOT',self.root),patch.object(sys,'argv',['manage.py','cleanup','status']),redirect_stdout(output):
            self.assertEqual(manage.main(),0)
        value=json.loads(output.getvalue());self.assertTrue(value['blocked']);self.assertNotIn('pid',value)


if __name__=='__main__':unittest.main()
