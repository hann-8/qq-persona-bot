"""Original recovery fixtures only: no real processes, sockets or model calls."""
import asyncio
from copy import deepcopy
import hashlib
import hmac
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import time

from qqbot_gateway.config import configuration_lock, GateConfig
from qqbot_gateway.lifecycle import atomic_json
from qqbot_gateway.onebot_gate import OneBotGate
from qqbot_gateway.qq_transport import DEFAULTS
from qqbot_gateway.transport_owner import HealthMonitor, initialize_control_sequence, owner_record
from qqbot_gateway.transport_health import HealthProducer, canonical
from qqbot_gateway.transport_launch import ManagementRecovery
from qqbot_gateway.transport_supervisor import RecoveryLedger, RecoveryClosed, RecoverySupervisor, AREA
import test_transport_lifecycle as fixture
from test_transport_health import KEY, observation
from test_group_silence import Capture, Duplex, frames, event


class RecoveryFixture(unittest.TestCase):
    def setUp(self):
        fixture.Fixture.setUp(self);self.now=1700000100.
        timer=patch('qqbot_gateway.onebot_gate.time.time',lambda:self.now);timer.start();self.addCleanup(timer.stop)
        record=json.loads((self.root/'state/qq-transport/runtime.local.json').read_text())
        record.update(format='qqbot-transport-owner-v2',control_secret_file='secrets/snowluma-control.local.json')
        atomic_json(self.root/'state/qq-transport/runtime.local.json',record)
        with configuration_lock(self.root) as lease:initialize_control_sequence(self.root,self.b,lease,clock=lambda:self.now)
        self.ledger=RecoveryLedger(self.root,clock=lambda:self.now)

    def prepare(self):
        rows=(self.root/'state/managed-processes.json').read_bytes();atomic_json(self.root/'state/managed-processes.json',[])
        with configuration_lock(self.root) as lease,patch('qqbot_gateway.transport_supervisor.require_stopped') as stopped:
            self.ledger.initialize(lease);stopped.assert_called_once_with(self.root)
        (self.root/'state/managed-processes.json').write_bytes(rows)

    def incident(self):
        obj=self.ledger.read();stamp=int(self.now*1000)
        obj['incident']=dict(id=__import__('uuid').uuid4().hex,binding=self.b.fields(),phase='drain',started_ms=stamp,
            deadline_ms=stamp+150000,action_id=None,reason='down')
        return obj

    def reserve(self,kind='snowluma',cfg=None):
        with configuration_lock(self.root) as lease:
            obj=self.incident();self.ledger.write(obj,lease)
            return self.ledger.reserve(obj,kind,cfg or DEFAULTS['recovery'],lease)


class LedgerTests(RecoveryFixture):
    def test_preparation_requires_stopped_and_partial_preparation_never_retries_empty(self):
        with configuration_lock(self.root) as lease,patch('qqbot_gateway.transport_supervisor.require_stopped',side_effect=ValueError('owned running')):
            with self.assertRaises(ValueError):self.ledger.initialize(lease)
        self.assertFalse((self.root/(AREA+'recovery-prepared.local.json')).exists())
        original=atomic_json
        def split(path,value):
            if Path(path).name=='recovery.local.json':raise OSError('synthetic split preparation')
            original(path,value)
        with configuration_lock(self.root) as lease,patch('qqbot_gateway.transport_supervisor.require_stopped'),patch('qqbot_gateway.transport_supervisor.atomic_json',split):
            with self.assertRaises(OSError):self.ledger.initialize(lease)
        with configuration_lock(self.root) as lease,patch('qqbot_gateway.transport_supervisor.require_stopped'):
            with self.assertRaises(RecoveryClosed):self.ledger.initialize(lease)

    def test_provider_has_only_physical_components(self):
        from qqbot_gateway.qq_transport import provider_description
        self.assertEqual(provider_description(self.settings).components,('qq_client','snowluma'))

    def test_unprepared_missing_corrupt_and_clock_rollback_never_reinitialize(self):
        with self.assertRaises(RecoveryClosed):self.ledger.read()
        self.prepare();self.ledger.read();self.now-=1
        with self.assertRaises(RecoveryClosed):self.ledger.read()
        self.now+=1;path=self.root/(AREA+'recovery.local.json');path.unlink()
        with self.assertRaises(RecoveryClosed):self.ledger.read()
        with configuration_lock(self.root) as lease,patch('qqbot_gateway.transport_supervisor.require_stopped'):
            with self.assertRaises(RecoveryClosed):self.ledger.initialize(lease)
        path.write_bytes(b'{"format":NaN}')
        with self.assertRaises(RecoveryClosed):self.ledger.read()

    def test_sliding_budgets_cooldown_and_consumed_unknown_survive_new_objects(self):
        self.prepare();self.reserve()
        self.ledger=RecoveryLedger(self.root,clock=lambda:self.now)
        with self.assertRaises(RecoveryClosed):self.reserve()
        self.now+=1800;self.reserve('qq')
        self.now+=1800
        with self.assertRaises(RecoveryClosed):self.reserve()
        with self.assertRaises(RecoveryClosed):self.reserve('qq')
        self.now+=86400;self.reserve()
        self.assertEqual(len(self.ledger.read()['actions']),1)

    def test_failed_budget_commit_leaves_write_ahead_poison_and_cannot_retry_for_free(self):
        self.prepare();original=atomic_json
        def fail(path,value):
            if Path(path).name=='recovery.local.json' and value['incident']['phase']=='reserved':raise OSError('synthetic disk failure')
            original(path,value)
        with patch('qqbot_gateway.transport_supervisor.atomic_json',fail):
            with self.assertRaises(OSError):self.reserve()
        with self.assertRaises(RecoveryClosed):RecoveryLedger(self.root,clock=lambda:self.now).read()
        self.assertTrue((self.root/(AREA+'recovery-intent.local.json')).exists())

    def test_action_requires_same_binding_and_held_writer_lease(self):
        self.prepare();action=self.reserve()
        with self.assertRaises(ValueError):self.ledger.require_action(action,self.b,object())
        with configuration_lock(self.root) as lease:
            self.ledger.require_action(action,self.b,lease)
            from dataclasses import replace
            with self.assertRaises(ValueError):self.ledger.require_action(action,replace(self.b,transport_epoch='c'*64),lease)

    def test_epoch_reset_rejects_each_corrupt_sequence_shape_without_refund(self):
        self.prepare();action=self.reserve()
        from dataclasses import replace
        from qqbot_gateway.transport_owner import replace_control_sequence
        new=replace(self.b,transport_epoch='e'*64);record=owner_record(self.root);record['binding']=new.fields()
        atomic_json(self.root/'state/qq-transport/runtime.local.json',record)
        path=self.root/'state/qq-transport/control-sequence.local.json'
        normal=dict(binding=self.b.fields(),sequence=0,clock_ms=int(self.now*1000))
        for change in (dict(sequence=True),dict(sequence=1.0),dict(sequence=9007199254740992),dict(clock_ms=-1),
                       dict(clock_ms=int(self.now*1000)+1),dict(extra=True)):
            with self.subTest(change=change):
                atomic_json(path,normal|change);before=path.read_bytes()
                with configuration_lock(self.root) as lease:
                    with self.assertRaises(ValueError):replace_control_sequence(self.root,new,self.b,action,self.ledger,lease,clock=lambda:self.now)
                self.assertEqual(path.read_bytes(),before)
        self.assertEqual(len(self.ledger.read()['actions']),1)


class SupervisorTests(RecoveryFixture,unittest.IsolatedAsyncioTestCase):
    def setup_monitor(self,*,prepare=True,drain=True,production=False):
        if prepare:self.prepare()
        cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'x'*40,'y'*40,self.root/'seen.sqlite',
            transport_provider='snowluma',transport_instance_id=self.b.instance_id,transport_config_digest=self.b.config_digest,silence_enabled=False)
        self.gate=OneBotGate(cfg,self.root);self.addCleanup(self.gate.store.close)
        self.monitor=HealthMonitor(self.gate,self.owner,KEY,session=object(),clock=lambda:self.now,proof_clock=lambda:self.now)
        self.gate.connected=True;self.gate.observe_online(dict(online=True,good=True));self.gate.online_at=self.now
        self.producers={};self.posts=[];self.launches=[];self.health_values={}
        async def exchange(method,path,body=None):
            if method=='GET':
                key=self.monitor.owner.binding.transport_epoch
                producer=self.producers.setdefault(key,HealthProducer(self.monitor.owner.binding,KEY))
                return producer.response(path.split('nonce=')[1],observation(**self.health_values))
            obj=json.loads(body);self.posts.append(obj)
            ack={k:obj[k] for k in self.monitor.owner.binding.fields()}|dict(domain='qqbot-snowluma-control-ack-v1',
                action=obj['action'],seq=obj['seq'],nonce=obj['nonce'],status={'bind':'bound','drain':'draining','stop':'stopped'}[obj['action']])
            ack['mac']=hmac.new(KEY,canonical(ack),hashlib.sha256).hexdigest();return canonical(ack)
        self.monitor.exchange=exchange
        async def drain_check(monitor):return drain
        def launch(spec,env):
            self.launches.append(spec.component);pid=21 if spec.component=='snowluma' else 22
            proc=Mock();proc.pid=pid;proc.create_time.return_value=self.now;proc.is_running.return_value=True
            proc.exe.return_value=str(spec.executable)
            proc.net_connections.return_value=[SimpleNamespace(status='LISTEN',laddr=SimpleNamespace(ip='127.0.0.1',port=5098),pid=pid)]
            self.procs[pid]=proc;return proc
        qualify={} if production else dict(qualify=lambda root,settings:self.layout)
        self.actions=ManagementRecovery(self.gate,process=self.procs.__getitem__,clock=lambda:self.now,
            drain_check=drain_check,launch=launch,**qualify)
        self.cfg=deepcopy(DEFAULTS['recovery']);self.cfg['enabled']=True
        self.supervisor=RecoverySupervisor(self.monitor,self.cfg,self.actions,clock=lambda:self.now,ledger=self.ledger)
        self.monitor.supervisor=self.supervisor;self.gate.transport_supervisor=self.supervisor

    async def tick(self):
        await self.monitor.poll_once();await self.supervisor.step()

    async def test_short_disconnect_recovers_without_action_and_healthy_ticks_keep_epoch(self):
        self.setup_monitor();await self.tick();epoch=self.gate.connection_id
        await self.tick();self.assertEqual(self.gate.connection_id,epoch)
        self.gate.connected=False;await self.tick();self.assertEqual(self.supervisor.phase,'grace')
        self.now+=29;self.gate.connected=True;self.gate.online_at=self.now;await self.tick()
        self.assertEqual(self.supervisor.phase,'observe');self.assertEqual(self.ledger.read()['actions'],[])
        self.assertEqual(self.ledger.read()['interruptions'],1)
        self.assertEqual(self.launches,[])

    async def test_gate_task_to_writer_new_epoch_proof_and_final_output_fence(self):
        self.setup_monitor();await self.tick()
        ticket=self.gate.silence.issue(event(),self.gate.connection_id);oldbinding=self.owner.binding
        oldproof=self.producers[oldbinding.transport_epoch].response(self.monitor.verifier.challenge(),observation())
        self.procs[12].is_running.return_value=False
        async def sleep(_):
            if self.supervisor.phase=='grace':self.now+=30
            elif self.supervisor.phase=='waiting_ready':
                self.gate.connected=True;self.gate.observe_online(dict(online=True,good=True));self.gate.online_at=self.now
            elif self.supervisor.phase=='observe':raise asyncio.CancelledError()
            else:raise AssertionError(self.supervisor.phase)
        self.monitor.sleep=sleep
        app=self.gate.application()
        with patch('qqbot_gateway.transport_owner.monitor_from_loaded',return_value=self.monitor):
            for start in app.on_startup:await start(app)
        with self.assertRaises(asyncio.CancelledError):await self.monitor.task
        self.assertEqual(self.launches,['snowluma']);self.assertNotEqual(self.monitor.owner.binding.transport_epoch,oldbinding.transport_epoch)
        self.assertEqual(self.monitor.owner.binding.qq,oldbinding.qq);self.assertTrue(self.gate.channel_ready())
        self.assertEqual(self.ledger.read()['actions'][0]['outcome'],'recovered')
        self.assertEqual(self.posts[-1]['seq'],1)  # Authorized replacement ledger reset.
        self.assertFalse(self.gate.accept_transport_health(oldproof));await self.monitor.poll_once()
        up=Capture();down=Capture()
        command=lambda t:dict(action='send_group_msg',params=dict(group_id='111',message=[dict(type='text',data={'text':'synthetic'})],qqbot_output_ticket=t),echo='x')
        await self.gate._outgoing(Duplex(frames(command(ticket)),up),down,set());self.assertFalse(down.rows)
        newticket=self.gate.silence.issue(event(mid=2),self.gate.connection_id)
        await self.gate._outgoing(Duplex(frames(command(newticket)),up),down,set());self.assertEqual(len(down.rows),1)
        await self.monitor.close()

    async def test_drain_unknown_and_pending_sends_never_terminate_or_spend(self):
        self.setup_monitor(drain=None);self.procs[12].is_running.return_value=False
        await self.tick();self.now+=30;await self.tick()
        self.assertEqual(self.supervisor.phase,'operator_required');self.assertEqual(self.ledger.read()['actions'],[])
        self.assertEqual(self.launches,[])

    async def test_drain_active_until_timeout_no_kill(self):
        self.setup_monitor(drain=False);self.procs[12].is_running.return_value=False
        await self.tick();self.now+=30;await self.tick();self.assertEqual(self.supervisor.phase,'drain')
        self.now+=150;await self.tick();self.assertEqual(self.supervisor.phase,'operator_required')
        self.assertEqual(self.launches,[])

    async def test_production_qualification_refusal_consumes_one_action_and_restart_never_retries(self):
        self.setup_monitor(production=True);self.procs[12].is_running.return_value=False
        await self.tick();self.now+=30;await self.tick()
        self.assertEqual(self.supervisor.phase,'operator_required');self.assertEqual(len(self.ledger.read()['actions']),1)
        self.assertEqual(self.launches,[])
        restarted=RecoverySupervisor(self.monitor,self.cfg,self.actions,clock=lambda:self.now,ledger=RecoveryLedger(self.root,clock=lambda:self.now))
        await restarted.step();self.assertEqual(restarted.phase,'operator_required')
        self.assertEqual(len(self.ledger.read()['actions']),1)

    async def test_reserved_crash_is_operator_required_without_reexecution(self):
        self.setup_monitor();self.reserve();await self.supervisor.step()
        self.assertEqual(self.supervisor.phase,'operator_required');self.assertEqual(self.launches,[])

    async def test_stop_during_drain_callback_prevents_reservation_and_writer(self):
        self.setup_monitor();self.procs[12].is_running.return_value=False
        async def drain(monitor):atomic_json(self.root/'state/stop-request.json',dict(instance_id=self.b.instance_id));return True
        self.actions.drain_check=drain
        await self.tick();self.now+=30;await self.tick()
        self.assertEqual(self.supervisor.phase,'stopped');self.assertEqual(self.ledger.read()['actions'],[]);self.assertEqual(self.launches,[])

    async def test_unprepared_enabled_and_disabled_default(self):
        self.setup_monitor(prepare=False);await self.tick();self.assertEqual(self.supervisor.phase,'operator_required')
        self.assertFalse(self.gate.channel_ready());self.assertEqual(self.launches,[])
        self.gate.transport_recovery_closed=False;self.cfg['enabled']=False;await self.supervisor.step()
        self.assertTrue(self.gate.channel_ready());self.assertFalse((self.root/(AREA+'recovery.local.json')).exists())

    async def test_never_armed_is_unknown_not_a_stalled_receiver_restart(self):
        self.setup_monitor();self.health_values=dict(rx_watch_armed=False)
        await self.tick();self.now+=30;await self.tick()
        self.assertEqual(self.supervisor.phase,'operator_required');self.assertEqual(self.launches,[])
        self.assertEqual(self.ledger.read()['actions'],[])

    async def test_successful_action_waits_fresh_ready_and_times_out_without_a_second_action(self):
        self.setup_monitor();self.procs[12].is_running.return_value=False
        await self.tick();self.now+=30;await self.tick();self.assertEqual(self.supervisor.phase,'waiting_ready')
        self.now+=180;await self.tick();self.assertEqual(self.supervisor.phase,'operator_required')
        self.now+=2000;await self.tick();self.assertEqual(self.launches,['snowluma'])
        self.assertEqual(len(self.ledger.read()['actions']),1)

    async def test_pending_send_and_unresolved_task_are_checked_by_actual_drain(self):
        self.setup_monitor();self.actions.drain_check=None
        self.gate.transport_pending.add('unacknowledged')
        self.assertIs(await self.actions.drain(self.monitor),False)
        self.gate.transport_pending.clear()
        from qqbot_gateway.task_store import TaskStore
        store=TaskStore(self.root/'state/tasks.sqlite');store.accept('fake','fake');store.set('fake','send_unknown');store.close()
        self.assertIs(await self.actions.drain(self.monitor),False)
        store=TaskStore(self.root/'state/tasks.sqlite');store.set('fake','failed')
        with store.db:store.db.execute("INSERT INTO delivery (message_key,umo,cid,response_id,content_sha256,bubbles,before_sha256,expected_sha256,tail_identity,state,repair) VALUES ('fake','x','x','x','x','[]','x','x','{}','partial','repaired')")
        store.close();self.assertIs(await self.actions.drain(self.monitor),False)
        with patch('qqbot_gateway.cleanup_identity.CleanupOwner.status',return_value={'blocked':True}):
            self.assertIsNone(await self.actions.drain(self.monitor))
        for proc in self.procs.values():proc.terminate.assert_not_called()

    async def test_control_unknown_with_owned_node_never_kills_and_consumes_once(self):
        self.setup_monitor()
        self.health_values=dict(pipe_connected=False)
        async def unknown(control):return 'ACK_UNKNOWN'
        self.actions.control=unknown
        await self.tick();self.now+=30;await self.tick()
        self.assertEqual(self.supervisor.phase,'operator_required');self.assertEqual(len(self.ledger.read()['actions']),1)
        for proc in self.procs.values():proc.terminate.assert_not_called()

    async def test_pipe_failure_drained_owned_node_then_writer_restarts_only_node(self):
        self.setup_monitor();self.health_values=dict(pipe_connected=False)
        async def ack(control):return 'ACKED'
        self.actions.control=ack
        self.procs[12].terminate.side_effect=lambda:self.procs[12].is_running.configure_mock(return_value=False)
        await self.tick();self.now+=30;await self.tick()
        self.assertEqual(self.supervisor.phase,'waiting_ready');self.assertEqual(self.launches,['snowluma'])
        self.procs[12].terminate.assert_called_once();self.procs[13].terminate.assert_not_called()

    async def test_stop_after_reservation_in_creation_callback_keeps_consumed_unknown(self):
        self.setup_monitor();self.procs[12].is_running.return_value=False
        create=self.actions.launch
        def racing(spec,env):
            proc=create(spec,env);atomic_json(self.root/'state/stop-request.json',dict(instance_id=self.b.instance_id));return proc
        self.actions.launch=racing
        await self.tick();self.now+=30;await self.tick()
        self.assertFalse(self.gate.channel_ready());self.assertEqual(len(self.ledger.read()['actions']),1)
        self.assertEqual(self.ledger.read()['actions'][0]['outcome'],'unknown')
        self.assertEqual(self.launches,['snowluma'])

    async def test_qq_flag_does_not_bypass_missing_real_three_of_three_qualification(self):
        self.setup_monitor();self.cfg['allow_qq_restart']=True
        self.procs[12].is_running.return_value=False;self.procs[13].is_running.return_value=False
        await self.tick();self.now+=30;await self.tick()
        self.assertEqual(self.supervisor.phase,'operator_required');self.assertEqual(self.launches,[])
        self.assertEqual(self.ledger.read()['actions'][0]['kind'],'qq')

    async def test_fake_qq_qualification_is_dependency_only_and_replaces_both_owned_identities(self):
        self.setup_monitor();self.cfg['allow_qq_restart']=True;self.actions.qualify_qq=lambda *args:None
        self.procs[12].is_running.return_value=False;self.procs[13].is_running.return_value=False
        await self.tick();self.now+=30;await self.tick()
        self.assertEqual(self.supervisor.phase,'waiting_ready');self.assertEqual(self.launches,['qq_client','snowluma'])
        self.assertNotEqual(self.monitor.owner.binding.qq_pid,self.b.qq_pid)

    async def test_drain_returning_true_after_deadline_cannot_reserve_or_kill(self):
        self.setup_monitor();self.procs[12].is_running.return_value=False
        async def late(monitor):self.now+=151;return True
        self.actions.drain_check=late
        await self.tick();self.now+=30;await self.tick()
        self.assertEqual(self.supervisor.phase,'operator_required');self.assertEqual(self.ledger.read()['actions'],[])
        self.assertEqual(self.launches,[])

    async def test_replacement_waits_delayed_listener_and_sends_only_one_bind(self):
        self.setup_monitor();self.procs[12].is_running.return_value=False;create=self.actions.launch;calls=[]
        def delayed(spec,env):
            proc=create(spec,env);listener=proc.net_connections.return_value
            def connections(**kwargs):calls.append(1);return [] if len(calls)<=2 else listener
            proc.net_connections.side_effect=connections;return proc
        async def sleep(delay):self.now+=delay
        self.actions.launch=delayed;self.monitor.sleep=sleep
        await self.tick();self.now+=30;await self.tick()
        self.assertEqual(self.supervisor.phase,'waiting_ready');self.assertGreaterEqual(len(calls),3)
        self.assertEqual(len(self.posts),1);self.assertEqual(self.posts[0]['action'],'bind')

    async def test_sent_replacement_bind_unknown_never_retries(self):
        self.setup_monitor();self.procs[12].is_running.return_value=False;exchange=self.monitor.exchange
        async def uncertain(method,path,body=None):
            if method=='POST':self.posts.append(json.loads(body));raise TimeoutError()
            return await exchange(method,path,body)
        self.monitor.exchange=uncertain
        await self.tick();self.now+=30;await self.tick();await self.tick()
        self.assertEqual(self.supervisor.phase,'operator_required');self.assertEqual(len(self.posts),1)
        self.assertEqual(len(self.ledger.read()['actions']),1)

    async def test_corrupt_old_sequence_cannot_be_laundered_by_recovery_epoch(self):
        self.setup_monitor();self.procs[12].is_running.return_value=False
        path=self.root/'state/qq-transport/control-sequence.local.json';obj=json.loads(path.read_text());obj['sequence']=True;atomic_json(path,obj)
        await self.tick();self.now+=30;await self.tick()
        self.assertEqual(self.supervisor.phase,'operator_required');self.assertEqual(len(self.ledger.read()['actions']),1)
        self.assertEqual(self.launches,[]);self.assertIs(json.loads(path.read_text())['sequence'],True)

    async def test_access_denied_during_termination_persists_operator_and_monitor_keeps_running(self):
        self.setup_monitor();self.health_values=dict(pipe_connected=False)
        import psutil
        async def ack(control):return 'ACKED'
        self.actions.control=ack;self.procs[12].terminate.side_effect=psutil.AccessDenied(12)
        async def sleep(_):
            if self.supervisor.phase=='grace':self.now+=30
            elif self.supervisor.phase=='operator_required':raise asyncio.CancelledError()
        self.monitor.sleep=sleep
        with self.assertRaises(asyncio.CancelledError):await self.monitor.run()
        self.assertEqual(self.ledger.read()['incident']['phase'],'operator_required')
        self.assertEqual(self.ledger.read()['actions'][0]['outcome'],'unknown');self.assertEqual(self.launches,[])

    async def test_actual_model_health_requires_owned_listener_and_complete_cleanup(self):
        self.setup_monitor();self.actions.drain_check=None
        atomic_json(self.root/'state/service-mode.json',self.mode|dict(mode='text'))
        proc=Mock();proc.is_running.return_value=True;proc.create_time.return_value=self.now
        proc.net_connections.return_value=[SimpleNamespace(status='LISTEN',laddr=SimpleNamespace(ip='127.0.0.1',port=8765))]
        self.procs[31]=proc
        atomic_json(self.root/'state/managed-processes.json',self.entries+[dict(pid=31,created=self.now,component='model')])
        payload=dict(alive=True,active=False,queue=0,remote_result_unknown=False,backend='codebuddy_cli',
            cli_cleanup=dict(blocked=False,coverage='observed_only',cleanup_outcome='observed_empty'))
        class Response:
            status=200
            async def __aenter__(self):return self
            async def __aexit__(self,*args):pass
            @property
            def content(self):return self
            async def read(self,limit):return canonical(payload)
        class Session(Response):
            def get(self,*args,**kwargs):return Response()
        with patch('aiohttp.ClientSession',return_value=Session()):
            self.assertIsNone(await self.actions.drain(self.monitor))
            payload['cli_cleanup']['coverage']='job_complete'
            self.assertIs(await self.actions.drain(self.monitor),True)
            payload['active']=True;self.assertIs(await self.actions.drain(self.monitor),False)
            payload['active']=False
            import psutil
            proc.create_time.side_effect=[self.now,psutil.AccessDenied(31)]
            self.assertIsNone(await self.actions.drain(self.monitor))


if __name__=='__main__':unittest.main()
