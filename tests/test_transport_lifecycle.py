"""All creation, sockets, runtime files and QQ identities are synthetic.

Node only runs our original pure handler over stdin/stdout, never a server.
"""
import asyncio
from contextlib import ExitStack, redirect_stdout
from dataclasses import replace
from io import StringIO
import json
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from qqbot_gateway.config import configuration_lock, require_configuration_lease, GateConfig
from qqbot_gateway.config_files import snapshot_environment
from qqbot_gateway.lifecycle import atomic_json, stopping
from qqbot_gateway.transport_launch import OwnerWriter, PrivateLayout, snow_specs
from qqbot_gateway.transport_owner import (HealthMonitor, initialize_control_sequence, reserve_control_sequences,
    prepare_stop_control, owner_record, startup_unknown, sign_command, verify_ack)
from qqbot_gateway.onebot_gate import OneBotGate
from scripts import manage
import test_transport_owner as owner_fixture
from test_transport_health import KEY

ROOT=Path(__file__).resolve().parents[1]


class Fixture(unittest.TestCase):
    def setUp(self):
        owner_fixture.OwnerTests.setUp(self)
        atomic_json(self.root/self.settings['secrets_file'],dict(onebot_inbound='x'*40,onebot_upstream='y'*40))
        atomic_json(self.root/'secrets/snowluma-control.local.json',dict(schema=1,key=KEY.hex()))
        self.layout=PrivateLayout(self.node,'runtime/snowluma-private/build.mjs')
        for pid,proc in self.procs.items():proc.pid=pid

    def v2(self):
        path=self.root/'state/qq-transport/runtime.local.json';record=json.loads(path.read_text())
        record.update(format='qqbot-transport-owner-v2',control_secret_file='secrets/snowluma-control.local.json')
        atomic_json(path,record)
        with configuration_lock(self.root) as lease:initialize_control_sequence(self.root,self.b,lease)

    def fresh(self):
        (self.root/'state/managed-processes.json').unlink()
        (self.root/'state/qq-transport/runtime.local.json').unlink()


class WriterTests(Fixture):
    def test_writer_requires_current_thread_lock_and_expires_after_scope(self):
        with self.assertRaises(ValueError):OwnerWriter(self.root,object(),'a'*32)
        with configuration_lock(self.root) as lease:
            writer=OwnerWriter(self.root,lease,'a'*32)
            errors=[]
            import threading
            def worker():
                try:require_configuration_lease(self.root,lease)
                except ValueError:errors.append('closed')
            thread=threading.Thread(target=worker);thread.start();thread.join();self.assertEqual(errors,['closed'])
        with self.assertRaises(ValueError):writer._held()

    def test_fixed_specs_and_writer_capture_then_register_real_consumer_binding(self):
        self.fresh();specs=snow_specs(self.root,self.settings,self.snapshot,self.mode['configuration'],self.layout)
        self.assertEqual([s.component for s in specs],['qq_client','snowluma'])
        self.assertEqual(specs[0].argv,(str(self.root/self.qq),))
        self.assertEqual(specs[1].argv[:2],(str(self.root/self.node),str(self.root/self.layout.entry_file)))
        self.assertNotIn(KEY.hex(),' '.join(specs[1].argv))
        with self.assertRaises(ValueError):snow_specs(self.root,self.settings,self.snapshot,self.mode['configuration'],PrivateLayout(self.node,'runtime/guess.mjs'))
        with configuration_lock(self.root) as lease:
            writer=OwnerWriter(self.root,lease,'a'*32,process=self.procs.__getitem__,clock=lambda:1700000000.)
            for spec in specs:writer.create(spec,lambda item:self.procs[13 if item.component=='qq_client' else 12])
            # Mock process.pid must be a real integer, not dynamically invented.
            owner=writer.register(self.settings,self.mode['configuration'],self.snapshot,self.layout,'b'*64)
            self.assertTrue(owner.identity_current(owner.binding));self.assertEqual(owner.binding,self.b)
            record=owner_record(self.root);self.assertEqual(record['format'],'qqbot-transport-owner-v2')
            with self.assertRaises(ValueError):writer.create(specs[0],Mock())
        self.assertEqual(reserve_control_sequences(self.root,self.b),(1,))

    def test_unknown_creation_is_write_ahead_preserved_and_blocks_both_providers(self):
        self.fresh();spec=snow_specs(self.root,self.settings,self.snapshot,self.mode['configuration'],self.layout)[0]
        bad=Mock();bad.pid=42;bad.create_time.side_effect=OSError('private exception must not be logged')
        with configuration_lock(self.root) as lease:
            writer=OwnerWriter(self.root,lease,'a'*32)
            def launch(item):
                self.assertTrue(startup_unknown(self.root));return bad
            with self.assertRaises(OSError):writer.create(spec,launch)
        self.assertTrue(startup_unknown(self.root));self.assertFalse((self.root/'state/managed-processes.json').exists())
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'STATE',self.root/'state/managed-processes.json'):
            with self.assertRaisesRegex(RuntimeError,'CREATION_UNKNOWN'):manage.start_channel()
            with self.assertRaisesRegex(RuntimeError,'CREATION_UNKNOWN'):manage.stop_project(grace=0)
            self.assertTrue(stopping(self.root,'a'*32))

    def test_creation_callback_cannot_adopt_a_preexisting_process(self):
        self.fresh();spec=snow_specs(self.root,self.settings,self.snapshot,self.mode['configuration'],self.layout)[0]
        self.procs[13].pid=13
        with configuration_lock(self.root) as lease:
            writer=OwnerWriter(self.root,lease,'a'*32,clock=lambda:1700000100.)
            with self.assertRaises(ValueError):writer.create(spec,lambda s:self.procs[13])
        self.assertTrue(startup_unknown(self.root));self.assertFalse((self.root/'state/managed-processes.json').exists())

    def test_actual_manage_fake_creation_uses_writer_and_no_napcat_fallback(self):
        self.fresh()
        for pid,p in self.procs.items():p.pid=pid
        output=StringIO();framework=[]
        def writer(root,lease,instance,**kw):
            return OwnerWriter(root,lease,instance,process=self.procs.__getitem__,clock=lambda:1700000000.)
        def launch(spec,env):
            self.assertNotIn(KEY.hex(),json.dumps(env));return self.procs[13 if spec.component=='qq_client' else 12]
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'STATE',self.root/'state/managed-processes.json'), \
             patch.object(manage,'require_runtime',return_value=self.layout),patch.object(manage,'OwnerWriter',side_effect=writer), \
             patch.object(manage.psutil,'Process',side_effect=self.procs.__getitem__),patch.object(manage.psutil,'Popen') as real_spawn, \
             patch.object(manage,'check_port'),patch.object(manage,'_configure_snow_framework'), \
             patch.object(manage,'_launch_snow_component',side_effect=launch) as create, \
             patch.object(manage,'_launch_snow_framework',side_effect=lambda *args:framework.append(args)),redirect_stdout(output):
            result=manage.start_channel()
            self.assertEqual(result['provider'],'snowluma');self.assertEqual(create.call_count,2);real_spawn.assert_not_called()
            record=owner_record(self.root);self.assertEqual(record['binding']['instance_id'],result['instance_id'])
            self.assertEqual([s[0] for s in framework[0][0]],['astrbot','gate'])
            self.assertNotIn('6099',output.getvalue());self.assertEqual(manage.service_mode()['phase'],'running')

    def test_status_hint_is_provider_aware_and_processes_are_only_real_pids(self):
        report=dict(provider='snowluma',process_state='partial',channel_state='unknown',channel={},model={},task_counts={},can_receive_group_messages=False)
        for provider in ('snowluma','unknown','napcat'):
            output=StringIO()
            with redirect_stdout(output):manage.show_status(report|dict(provider=provider))
            self.assertEqual('6099' in output.getvalue(),provider=='napcat')

    def test_stop_wins_between_create_callback_and_registration(self):
        self.fresh();specs=snow_specs(self.root,self.settings,self.snapshot,self.mode['configuration'],self.layout)
        with configuration_lock(self.root) as lease:
            writer=OwnerWriter(self.root,lease,'a'*32,process=self.procs.__getitem__,clock=lambda:1700000000.)
            def launch(spec):
                atomic_json(self.root/'state/stop-request.json',dict(instance_id='a'*32));return self.procs[13]
            with self.assertRaisesRegex(ValueError,'STOP_REQUESTED'):writer.create(specs[0],launch)
            with self.assertRaises(ValueError):writer.create(specs[1],Mock())
        self.assertTrue(startup_unknown(self.root));self.assertFalse((self.root/'state/qq-transport/runtime.local.json').exists())
        self.assertEqual(json.loads((self.root/'state/managed-processes.json').read_text()),[self.entries[1]])

    def test_registered_hash_change_does_not_initialize_control_or_open_owner(self):
        self.fresh();specs=snow_specs(self.root,self.settings,self.snapshot,self.mode['configuration'],self.layout)
        with configuration_lock(self.root) as lease:
            writer=OwnerWriter(self.root,lease,'a'*32,process=self.procs.__getitem__,clock=lambda:1700000000.)
            for spec in specs:writer.create(spec,lambda s:self.procs[13 if s.component=='qq_client' else 12])
            (self.root/self.layout.entry_file).write_bytes(b'changed after launch')
            with self.assertRaises(ValueError):writer.register(self.settings,self.mode['configuration'],self.snapshot,self.layout,'b'*64)
        self.assertFalse((self.root/'state/qq-transport/control-sequence.local.json').exists())
        self.assertFalse(self.owner.identity_current(self.b))

    def test_framework_prepare_preserves_scope_and_actual_launch_helper_records_only_created_pids(self):
        path=self.root/'runtime/astrbot/data/cmd_config.json'
        atomic_json(path,dict(platform_settings={},provider_settings=dict(proactive_capability={})))
        gate=SimpleNamespace(upstream_token='y'*40,allowed_groups={'111'},admin_users={'333'})
        env=snapshot_environment(self.root,self.snapshot,self.mode['configuration'])
        proc=Mock();proc.pid=21;proc.create_time.return_value=1700000001.;proc.children.return_value=[]
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'STATE',self.root/'state/managed-processes.json'), \
             patch.object(manage.psutil,'Popen',return_value=proc) as create,patch.object(manage,'port_open',return_value=True):
            manage._configure_snow_framework(gate,False,env)
            manage._launch_snow_framework([('gate',['fake-gate'],self.root,(6200,),1)],env,self.entries.copy(),self.snapshot,False)
            rows=manage.read_state();self.assertEqual(rows[-1],dict(pid=21,created=1700000001.,component='gate'))
            self.assertEqual(len(rows),3);self.assertIn('process_host.py',str(create.call_args.args))
        cfg=json.loads(path.read_text(encoding='utf-8-sig'))
        self.assertEqual(cfg['platform_settings']['id_whitelist'],['111']);self.assertFalse(cfg['provider_settings']['enable'])
        self.assertEqual(cfg['admins_id'],['333']);self.assertEqual(cfg['wake_prefix'],[])

    def test_control_secret_reuse_of_admin_rejected_before_snapshot_or_creation(self):
        self.fresh();atomic_json(self.root/'secrets/memes-admin.local.json',dict(token=KEY.hex()))
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'STATE',self.root/'state/managed-processes.json'), \
             patch.object(manage,'require_runtime',return_value=self.layout),patch.object(manage,'create_snapshot') as snapshot, \
             patch.object(manage.psutil,'Popen') as process:
            with self.assertRaisesRegex(ValueError,'SECRET_REUSED'):manage.start_channel()
            snapshot.assert_not_called();process.assert_not_called()

    def test_deep_bad_ack_and_record_are_closed_and_command_timestamp_never_extends_three_seconds(self):
        body=sign_command(self.b,KEY,'bind',1,now=lambda:1.2999,nonce='f'*64);obj=json.loads(body)
        self.assertEqual(obj['issued_ms'],1200);self.assertEqual(obj['expires_ms'],4200)
        self.assertLessEqual(obj['expires_ms'],1299+3000)
        deep=b'['*1200+b']'*1200
        self.assertFalse(verify_ack(deep,self.b,KEY,body))
        (self.root/'state/qq-transport/runtime.local.json').write_bytes(deep)
        self.assertFalse(self.owner.identity_current(self.b))


class NodeHandler:
    def __init__(self,binding):
        source="""import readline from 'node:readline';
import {createControlHandler} from './adapters/snowluma/control_plane.mjs';
const [binding,key]=JSON.parse(process.argv[1]);let stop=false;
const handler=createControlHandler({binding,key:Buffer.from(key,'hex'),identityCurrent:()=>true,
stopRequested:()=>stop,observe:()=>({}),onBind:()=>{},onDrain:()=>{},onStop:()=>{stop=true;}});
for await(const line of readline.createInterface({input:process.stdin})) {
const request=JSON.parse(line);if(request.marker){stop=true;console.log('{}');continue;}
console.log(JSON.stringify(await handler.handle(request)));}
"""
        self.process=subprocess.Popen(['node','--input-type=module','-e',source,json.dumps([binding.fields(),KEY.hex()])],
            cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        self.requests=[]
    def send(self,request):
        self.requests.append(request);self.process.stdin.write(json.dumps(request)+'\n');self.process.stdin.flush()
        return json.loads(self.process.stdout.readline())
    def close(self):
        self.process.stdin.close();self.process.wait(timeout=5)
        self.process.stdout.close();self.process.stderr.close()


class ControlTests(Fixture,unittest.IsolatedAsyncioTestCase):
    async def test_gate_bind_then_new_manage_client_drain_stop_use_one_persisted_sequence(self):
        self.v2();handler=NodeHandler(self.b);self.addCleanup(handler.close)
        cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'x'*40,'y'*40,self.root/'seen.sqlite',
            transport_provider='snowluma',transport_instance_id=self.b.instance_id,transport_config_digest=self.b.config_digest)
        gate=OneBotGate(cfg,self.root);self.addCleanup(gate.store.close)
        monitor=HealthMonitor(gate,self.owner,KEY,session=object())
        async def exchange(method,path,body=None):
            # Each command preallocated and released the lock before doing I/O.
            with configuration_lock(self.root):pass
            response=handler.send(dict(method=method,url=path,body=body.decode()))
            self.assertEqual(response['status'],200,(path,response));return response['body'].encode()
        monitor.exchange=exchange
        self.assertTrue(await monitor.command('bind'))
        atomic_json(self.root/'state/stop-request.json',dict(instance_id=self.b.instance_id))
        handler.send(dict(marker=True))
        self.snapshot.unlink()  # Stop-only ownership remains provable.
        with configuration_lock(self.root) as lease:
            control=prepare_stop_control(self.root,self.mode,lease,process=self.procs.__getitem__,session=object())
        control.exchange=exchange
        self.assertEqual(await control.run(),'ACKED')
        rows=[r for r in handler.requests if 'body' in r]
        self.assertEqual([json.loads(r['body'])['seq'] for r in rows],[1,2,3])
        self.assertEqual(handler.send(rows[0])['status'],403)
        await monitor.close()

    async def test_allocator_is_atomic_across_clients_and_clock_rollback_or_corruption_closed(self):
        self.v2()
        with configuration_lock(self.root) as lease:
            first=reserve_control_sequences(self.root,self.b,lease=lease)
            with self.assertRaises(ValueError):reserve_control_sequences(self.root,self.b)
        second=reserve_control_sequences(self.root,self.b);self.assertEqual(first+second,(1,2))
        path=self.root/'state/qq-transport/control-sequence.local.json';before=path.read_bytes()
        with self.assertRaises(ValueError):reserve_control_sequences(self.root,self.b,clock=lambda:1)
        self.assertEqual(path.read_bytes(),before)
        path.write_bytes(b'{"sequence":NaN}')
        with self.assertRaises(ValueError):reserve_control_sequences(self.root,self.b)
        path.unlink()
        with self.assertRaises(ValueError):reserve_control_sequences(self.root,self.b)

    async def test_startup_lock_contention_yields_event_loop_and_retries_only_unsent_bind(self):
        self.v2();handler=NodeHandler(self.b);self.addCleanup(handler.close)
        cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'x'*40,'y'*40,self.root/'seen.sqlite',
            transport_provider='snowluma',transport_instance_id=self.b.instance_id,transport_config_digest=self.b.config_digest)
        gate=OneBotGate(cfg,self.root);self.addCleanup(gate.store.close)
        monitor=HealthMonitor(gate,self.owner,KEY,session=object(),sleep=lambda _:asyncio.sleep(0))
        async def exchange(method,path,body=None):
            response=handler.send(dict(method=method,url=path,body=body.decode()));return response['body'].encode()
        async def poll():atomic_json(self.root/'state/stop-request.json',dict(instance_id=self.b.instance_id));return True
        monitor.exchange=exchange;monitor.poll_once=poll
        with configuration_lock(self.root):
            task=asyncio.create_task(monitor.run())
            await asyncio.sleep(0);await asyncio.sleep(0)
            self.assertTrue(monitor.sequence_busy);self.assertFalse(task.done());self.assertEqual(handler.requests,[])
        await asyncio.wait_for(task,1)
        self.assertEqual(len(handler.requests),1);await monitor.close()

    async def test_uncertain_bind_ack_is_never_automatically_retried(self):
        self.v2()
        cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'x'*40,'y'*40,self.root/'seen.sqlite',
            transport_provider='snowluma',transport_instance_id=self.b.instance_id,transport_config_digest=self.b.config_digest)
        gate=OneBotGate(cfg,self.root);self.addCleanup(gate.store.close)
        monitor=HealthMonitor(gate,self.owner,KEY,session=object());sent=[]
        async def exchange(*args):sent.append(args);raise TimeoutError()
        monitor.exchange=exchange
        await monitor.run();self.assertEqual(len(sent),1);self.assertFalse(gate.channel_ready())
        self.assertEqual(json.loads((self.root/'state/qq-transport/control-sequence.local.json').read_text())['sequence'],1)
        await monitor.close()


class ManageStopTests(Fixture):
    def begin(self):
        self.v2();handler=NodeHandler(self.b);self.addCleanup(handler.close)
        seq=reserve_control_sequences(self.root,self.b)[0]
        body=sign_command(self.b,KEY,'bind',seq)
        ack=handler.send(dict(method='POST',url='/bind',body=body.decode()))
        self.assertTrue(verify_ack(ack['body'],self.b,KEY,body));return handler

    def stack(self):
        stack=ExitStack();self.addCleanup(stack.close)
        stack.enter_context(patch.object(manage,'ROOT',self.root))
        stack.enter_context(patch.object(manage,'STATE',self.root/'state/managed-processes.json'))
        stack.enter_context(patch.object(manage.psutil,'Process',side_effect=self.procs.__getitem__))
        stack.enter_context(patch.object(manage.psutil,'wait_procs',return_value=([],[])))
        for proc in self.procs.values():
            proc.children.return_value=[]
            proc.terminate.side_effect=lambda p=proc:p.is_running.configure_mock(return_value=False)
        return stack

    def test_actual_stop_drain_stop_ack_before_owned_cleanup_despite_corrupt_snapshot(self):
        handler=self.begin();self.stack();self.snapshot.write_bytes(b'broken: [')
        # Disk provider changed, but targets and key remain from the loaded owner.
        disk=self.root/'config/settings.local.yaml';disk.write_text('qq_transport: {provider: napcat}',encoding='utf-8')
        async def exchange(control,method,path,body=None):
            with configuration_lock(self.root):pass
            self.assertTrue(stopping(self.root,self.b.instance_id))
            handler.send(dict(marker=True))
            response=handler.send(dict(method=method,url=path,body=body.decode()))
            self.assertEqual(response['status'],200);return response['body'].encode()
        output=StringIO()
        with patch('qqbot_gateway.transport_owner.StopControl.exchange',exchange),redirect_stdout(output):manage.stop_project(grace=0)
        self.assertIn('TRANSPORT_STOP code=ACKED',output.getvalue())
        self.assertEqual([r.get('url') for r in handler.requests if 'url' in r],['/bind','/drain','/stop'])
        for proc in self.procs.values():proc.terminate.assert_called_once()
        self.assertEqual(manage.read_state(),[])

    def test_bad_ack_is_unknown_and_never_retries_or_changes_owned_cleanup_targets(self):
        handler=self.begin();self.stack()
        async def exchange(control,method,path,body=None):
            with configuration_lock(self.root):pass
            handler.send(dict(method=method,url=path,body=body.decode()))
            return b'{"private":"not an authenticated ACK"}'
        output=StringIO()
        with patch('qqbot_gateway.transport_owner.StopControl.exchange',exchange),redirect_stdout(output):manage.stop_project(grace=0)
        self.assertIn('TRANSPORT_STOP code=ACK_UNKNOWN',output.getvalue());self.assertNotIn('private',output.getvalue())
        self.assertEqual(len([r for r in handler.requests if 'url' in r]),3)
        for proc in self.procs.values():proc.terminate.assert_called_once()

    def test_missing_secret_skips_control_and_safe_cleanup_still_runs(self):
        self.v2();self.stack();(self.root/'secrets/snowluma-control.local.json').unlink()
        with patch('qqbot_gateway.transport_owner.StopControl.exchange') as exchange:
            manage.stop_project(grace=0);exchange.assert_not_called()
        for proc in self.procs.values():proc.terminate.assert_called_once()

    def test_identity_permission_unknown_preserves_registry_and_stop_marker(self):
        self.v2();self.stack();before=(self.root/'state/managed-processes.json').read_bytes()
        import psutil
        self.procs[12].create_time.side_effect=psutil.AccessDenied(12)
        with self.assertRaises(psutil.AccessDenied):manage.stop_project(grace=0)
        self.assertTrue(stopping(self.root,self.b.instance_id))
        self.assertEqual((self.root/'state/managed-processes.json').read_bytes(),before)
        for proc in self.procs.values():proc.terminate.assert_not_called()

    def test_instance_changes_during_control_prevent_cleanup_of_new_registry(self):
        self.begin();self.stack()
        async def exchange(control,*args):
            with configuration_lock(self.root):atomic_json(self.root/'state/service-mode.json',self.mode|dict(instance_id='f'*32))
            return b'{}'
        with patch('qqbot_gateway.transport_owner.StopControl.exchange',exchange):
            with self.assertRaisesRegex(RuntimeError,'OWNERSHIP_CHANGED'):manage.stop_project(grace=0)
        for proc in self.procs.values():proc.terminate.assert_not_called()
        self.assertEqual(manage.read_state(),self.entries)


if __name__=='__main__':unittest.main()
