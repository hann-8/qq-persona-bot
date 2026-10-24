"""Fake-clock/PID sampling and the actual monitor task hook; zero sockets."""
import asyncio
from dataclasses import replace
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock,Mock,patch

from qqbot_gateway.transport_health import HealthBinding
from qqbot_gateway.transport_trial import TrialSampler,status,LIMIT,RETENTION,metadata_bytes
from qqbot_gateway.transport_owner import HealthMonitor


class TrialTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.now=1700000000
        self.ready=False
        self.b=HealthBinding('a'*32,'b'*64,'c'*64,'d'*64,'e'*64,1,1000,2,1001,5098)
        self.gate=SimpleNamespace(root=self.root,channel_ready=lambda:self.ready,online=True,good=True)
        self.monitor=SimpleNamespace(gate=self.gate,owner=SimpleNamespace(binding=self.b),supervisor=None,
            verifier=SimpleNamespace(observation={'rx_watch_armed':True,'pipe_connected':True},seq=1))
        self.sampler=TrialSampler(self.monitor,clock=lambda:self.now,resources=lambda:[10,2,30,4],metadata=lambda _:100)

    def sample(self,seconds=60):self.now+=seconds;self.sampler.sample()
    def state(self):return json.loads((self.root/'state/qq-transport/trial.local.json').read_text())

    def test_first_ready_quiet_continuity_gap_new_epoch_and_stale_status(self):
        self.sampler.sample();self.assertFalse(status(self.root)['started'])
        self.ready=True;self.sample();self.sample();self.assertEqual(self.state()['continuous_seconds'],60)
        self.assertFalse(status(self.root,clock=lambda:self.now)['actual_send_receive_verified'])
        self.sample(120);self.assertEqual(self.state()['unknown'],1);self.assertIsNone(self.state()['start'])
        self.sample();self.assertEqual(self.state()['segments'],2)
        self.monitor.owner.binding=replace(self.b,transport_epoch='f'*64);self.sample()
        self.assertEqual(self.state()['segments'],3)
        self.assertEqual(status(self.root,clock=lambda:self.now+91)['state'],'UNKNOWN')

    def test_resource_unknown_clock_rollback_and_restart_preserve_failure(self):
        self.ready=True;self.sample();self.sample()
        self.sampler.resources=Mock(side_effect=PermissionError('private exception never stored'))
        self.sample();self.assertEqual(self.state()['unknown'],1)
        self.assertIsNone(self.state()['latest']['rss_handles'])
        self.now-=120;self.sampler.sample();self.assertEqual(self.state()['unknown'],2)
        again=TrialSampler(self.monitor,clock=lambda:self.now,resources=lambda:[1,2,3,4],metadata=lambda _:0)
        self.now+=60;again.sample();self.assertEqual(self.state()['unknown'],2)
        text=(self.root/'state/qq-transport/trial.local.json').read_text();self.assertNotIn('private exception',text)

    def test_record_bound_total_capacity_retention_and_corrupt_evidence_not_reset(self):
        self.ready=True;self.sample();base=self.root/'state/qq-transport'
        for path in base.glob('trial-samples-*.jsonl'):
            self.assertTrue(all(len(row)+1<=512 for row in path.read_bytes().splitlines()))
        old=base/('trial-samples-'+str((self.now-RETENTION-172800)//86400)+'.jsonl');old.write_bytes(b'{}\n')
        self.sample();self.assertFalse(old.exists())
        huge=base/('trial-samples-'+str(self.now//86400)+'.jsonl')
        with huge.open('wb') as stream:stream.truncate(LIMIT)
        self.sample();self.assertEqual(self.state()['unknown'],1);self.assertIsNone(self.state()['start'])
        path=base/'trial.local.json';path.write_bytes(b'{broken')
        self.sample();self.assertEqual(path.read_bytes(),b'{broken');self.assertEqual(status(self.root)['state'],'UNKNOWN')

    def test_metadata_only_bounded_and_no_contents_read(self):
        (self.root/'logs').mkdir();(self.root/'logs/private.log').write_bytes(b'private'*10)
        (self.root/'unrelated').mkdir();(self.root/'unrelated/ignored').write_bytes(b'x'*500)
        self.assertEqual(metadata_bytes(self.root),70)

    def test_72h_is_subset_of_168_and_no_actual_message_claim(self):
        self.ready=True;self.sample()
        obj=self.state();obj['start']=self.now-168*3600;obj['continuous_seconds']=168*3600
        path=self.root/'state/qq-transport/trial.local.json';path.write_text(json.dumps(obj))
        result=status(self.root,clock=lambda:self.now)
        self.assertTrue(result['initial_72h']);self.assertTrue(result['total_168h']);self.assertFalse(result['actual_send_receive_verified'])

    def test_bad_latest_never_prints_content_or_qualifies(self):
        self.ready=True;self.sample();obj=self.state();obj['latest']['payload']='private synthetic text'
        path=self.root/'state/qq-transport/trial.local.json';path.write_text(json.dumps(obj))
        result=status(self.root,clock=lambda:self.now)
        self.assertEqual(result['state'],'UNKNOWN');self.assertNotIn('private synthetic',json.dumps(result))
        self.sample();self.assertIn('payload',json.loads(path.read_text())['latest'])


class TaskHookTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_gate_send_ack_and_unknown_are_sampled_without_retry(self):
        from qqbot_gateway.onebot_gate import OneBotGate
        from qqbot_gateway.config import GateConfig
        from test_group_silence import Capture,Duplex,frames,event
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,root/'db',transport_provider='snowluma')
            gate=OneBotGate(cfg);self.addCleanup(gate.store.close);gate.root=root;gate.channel_ready=lambda:True
            sink=Capture();pending=set()
            for index in (1,2):
                ticket=gate.silence.issue(event(mid=index),gate.connection_id)
                message=dict(action='send_group_msg',params=dict(group_id='111',message=[dict(type='text',data={'text':'synthetic'})],qqbot_output_ticket=ticket),echo='synthetic-'+str(index))
                await gate._outgoing(Duplex(frames(message),Capture()),sink,pending)
            self.assertEqual(len(sink.rows),2)
            upstream=Capture()
            await gate._incoming(Duplex(frames(dict(status='ok',retcode=0,data={'message_id':123},echo='synthetic-1')),Capture()),upstream,pending)
            gate.send_metrics(disconnect=True)
            metrics=gate.send_metrics();self.assertEqual(metrics['acked'],1);self.assertEqual(metrics['unknown'],1)
            monitor=SimpleNamespace(gate=gate,owner=SimpleNamespace(binding=HealthBinding('a'*32,'b'*64,'c'*64,'d'*64,'e'*64,1,1000,2,1001,5098)),
                verifier=SimpleNamespace(observation={},seq=1),supervisor=None)
            sampler=TrialSampler(monitor,clock=lambda:1700000000,resources=lambda:[1,2,3,4],metadata=lambda _:0);sampler.sample()
            latest=status(root,clock=lambda:1700000000)['latest']
            self.assertEqual(latest['send_acked'],1);self.assertEqual(latest['send_unknown'],1);self.assertIsInstance(latest['send_ms'],int)
            self.assertNotIn('synthetic-',json.dumps(latest));self.assertEqual(len(sink.rows),2)
            gate.store.close()

    async def test_real_health_monitor_task_invokes_sampler_without_new_transport(self):
        obj=SimpleNamespace(owner=SimpleNamespace(root=Path('.'),binding=SimpleNamespace(instance_id='a'*32)),
            gate=SimpleNamespace(config=SimpleNamespace(transport_ready_timeout=180,transport_health_poll=5),channel_ready=Mock()),
            command=AsyncMock(return_value=True),poll_once=AsyncMock(),supervisor=None,
            verifier=SimpleNamespace(invalidate=Mock()),trial_sampler=SimpleNamespace(sample=Mock()),sleep=AsyncMock())
        with patch('qqbot_gateway.transport_owner.stopping',side_effect=[False,False,False,True]):
            await HealthMonitor.run(obj)
        obj.poll_once.assert_awaited_once();obj.trial_sampler.sample.assert_called_once();obj.command.assert_awaited_once_with('bind')
