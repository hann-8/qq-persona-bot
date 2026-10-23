"""Synthetic filesystem, process identities and HTTP responses; no sockets."""
import asyncio
from dataclasses import replace
import hashlib
import json
import subprocess
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import yaml
from qqbot_gateway.config_files import read_project, create_snapshot
from qqbot_gateway.lifecycle import atomic_json, stopping
from qqbot_gateway.transport_owner import (RuntimeOwner, HealthMonitor, TransportBlocked,
    loaded_provider, read_control_key, sign_command, verify_ack, ACK_DOMAIN)
from qqbot_gateway.transport_health import HealthProducer, canonical
from qqbot_gateway.config import GateConfig
from qqbot_gateway.onebot_gate import OneBotGate
from scripts import manage, process_host
from test_qq_transport import synthetic, proof
from test_transport_health import binding, observation, KEY


class OwnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'config').mkdir()
        self.raw=synthetic();self.raw['qq_transport']={'provider':'snowluma'}
        (self.root/'config/settings.local.yaml').write_text(yaml.safe_dump(self.raw),encoding='utf-8')
        self.project=read_project(self.root);self.settings=self.project.settings
        self.snapshot,metadata=create_snapshot(self.project,'a'*32)
        self.mode=dict(provider='snowluma',instance_id='a'*32,configuration=metadata,mode='channel_only')
        atomic_json(self.root/'state/service-mode.json',self.mode)
        p=proof()
        for field,value in [('build',b'original synthetic build'),('policy',b'original synthetic policy')]:
            path=self.root/p['private_build'][field+'_file'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)
            p['private_build'][field+'_sha256']=hashlib.sha256(value).hexdigest()
        atomic_json(self.root/'state/qq-transport/proof.local.json',p)
        self.b=replace(binding(),config_digest=self.project.semantic_digest,
            build_hash=p['private_build']['build_sha256'],policy_digest=p['private_build']['policy_sha256'])
        self.node='runtime/snowluma-private/node.exe';self.qq='runtime/qq-snowluma/QQ.exe'
        for name in (self.node,self.qq):
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'fake executable')
        atomic_json(self.root/'state/qq-transport/runtime.local.json',dict(format='qqbot-transport-owner-v1',
            binding=self.b.fields(),node_executable=self.node,qq_executable=self.qq))
        self.entries=[dict(pid=12,created=1700000000.,component='snowluma'),dict(pid=13,created=1700000000.001,component='qq_client')]
        atomic_json(self.root/'state/managed-processes.json',self.entries)
        self.procs={}
        for pid,created,name in [(12,1700000000.,self.node),(13,1700000000.001,self.qq)]:
            proc=Mock();proc.is_running.return_value=True;proc.create_time.return_value=created;proc.exe.return_value=str(self.root/name)
            proc.net_connections.return_value=[SimpleNamespace(status='LISTEN',laddr=SimpleNamespace(ip='127.0.0.1',port=5098),pid=12)]
            self.procs[pid]=proc
        self.owner=RuntimeOwner(self.root,self.b,self.node,self.qq,process=self.procs.__getitem__)

    def test_real_identity_checks_pid_creation_listener_registry_and_artifacts(self):
        self.assertTrue(self.owner.identity_current(self.b))
        self.procs[12].create_time.return_value+=.001
        self.assertFalse(self.owner.identity_current(self.b));self.procs[12].create_time.return_value-=.001
        self.procs[12].net_connections.return_value[0].laddr.ip='0.0.0.0'
        self.assertFalse(self.owner.identity_current(self.b));self.procs[12].net_connections.return_value[0].laddr.ip='127.0.0.1'
        self.entries.append(dict(self.entries[0]));atomic_json(self.root/'state/managed-processes.json',self.entries)
        self.assertFalse(self.owner.identity_current(self.b));self.entries.pop();atomic_json(self.root/'state/managed-processes.json',self.entries)
        self.assertTrue(self.owner.identity_current(self.b))
        (self.root/'runtime/snowluma-private/project_policy.mjs').write_bytes(b'changed')
        self.assertFalse(self.owner.identity_current(self.b))

    def test_loaded_snapshot_wins_and_stop_revokes_without_disk_provider_guess(self):
        self.raw.pop('qq_transport');(self.root/'config/settings.local.yaml').write_text(yaml.safe_dump(self.raw),encoding='utf-8')
        self.assertEqual(loaded_provider(self.root,self.mode),'snowluma');self.assertTrue(self.owner.identity_current(self.b))
        atomic_json(self.root/'state/stop-request.json',dict(instance_id=self.b.instance_id))
        self.assertFalse(self.owner.identity_current(self.b));self.assertTrue(self.owner.identity_current(self.b,allow_stop=True))
        self.snapshot.unlink();self.assertFalse(self.owner.identity_current(self.b,allow_stop=True))

    def test_independent_key_is_strict_and_unicode_tokens_do_not_crash(self):
        atomic_json(self.root/self.settings['secrets_file'],dict(model='自造凭据'))
        path=self.root/'secrets/snowluma-control.local.json';atomic_json(path,dict(schema=1,key=KEY.hex()))
        self.assertEqual(read_control_key(self.root,self.settings),KEY)
        with self.assertRaises(ValueError):read_control_key(self.root,self.settings,(KEY.decode(),))
        atomic_json(path,dict(schema=True,key=KEY.hex()))
        with self.assertRaises(ValueError):read_control_key(self.root,self.settings)

    def test_start_refuses_before_snapshot_registry_ports_or_children(self):
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'STATE',self.root/'state/managed-processes.json'), \
             patch.object(manage,'read_state',return_value=[]),patch.object(manage,'create_snapshot') as snap, \
             patch.object(manage,'check_port') as port,patch.object(manage.psutil,'Popen') as child:
            before=(self.root/'state/service-mode.json').read_bytes()
            with self.assertRaises(TransportBlocked):manage.start_channel()
            self.assertEqual((self.root/'state/service-mode.json').read_bytes(),before)
            snap.assert_not_called();port.assert_not_called();child.assert_not_called()

    def test_actual_stop_path_survives_missing_or_corrupt_snapshot_and_edited_disk(self):
        for content in (None,b'broken: ['):
            with self.subTest(content=content):
                if content is None:self.snapshot.unlink(missing_ok=True)
                else:self.snapshot.write_bytes(content)
                self.raw.pop('qq_transport',None);(self.root/'config/settings.local.yaml').write_text(yaml.safe_dump(self.raw),encoding='utf-8')
                def cleanup(entries):
                    self.assertTrue(stopping(self.root,self.b.instance_id));self.assertEqual(entries,self.entries)
                with patch.object(manage,'ROOT',self.root),patch.object(manage,'STATE',self.root/'state/managed-processes.json'), \
                     patch.object(manage,'alive',return_value=Mock()),patch.object(manage,'stop',side_effect=cleanup) as stop:
                    manage.stop_project(grace=0);stop.assert_called_once()

    def test_process_host_drops_raw_snow_output(self):
        for component in ('snowluma','qq_client','transport_watch'):
            self.assertEqual(process_host.safe_line(component,'TRANSPORT_EVENT code=BOUND'),'TRANSPORT_EVENT code=BOUND')
            for line in ('ERROR private stack','QQ 123 message','prefix TRANSPORT_EVENT code=BOUND','TRANSPORT_EVENT code=UNKNOWN'):
                self.assertIsNone(process_host.safe_line(component,line))

    def test_snow_management_creation_identity_is_integer_milliseconds(self):
        proc=Mock();proc.create_time.return_value=1700000000.001;proc.is_running.return_value=True
        with patch.object(manage.psutil,'Process',return_value=proc):
            self.assertIsNone(manage.alive(self.entries[0]))
            self.assertIs(manage.alive(dict(self.entries[0],created=1700000000.001)),proc)

    def test_corrupt_registry_preserves_evidence_but_sets_stop_marker_first(self):
        path=self.root/'state/managed-processes.json';path.write_bytes(b'broken')
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'STATE',path),patch.object(manage,'stop') as stop:
            with self.assertRaises(ValueError):manage.stop_project(grace=0)
            self.assertTrue(stopping(self.root,self.b.instance_id));self.assertEqual(path.read_bytes(),b'broken');stop.assert_not_called()

    def test_gate_main_blocks_before_application_or_listener(self):
        from qqbot_gateway import onebot_gate
        cfg=SimpleNamespace(transport_provider='snowluma')
        with patch('sys.argv',['gate','--config',str(self.root/'config/settings.local.yaml'),'--root',str(self.root)]), \
             patch.object(onebot_gate,'load_gate_config',return_value=cfg),patch.object(onebot_gate.web,'run_app') as run, \
             patch.object(onebot_gate,'OneBotGate') as gate:
            with self.assertRaises(TransportBlocked):onebot_gate.main()
            run.assert_not_called();gate.assert_not_called()

    def test_status_uses_loaded_provider_and_closes_on_invalid_snapshot(self):
        self.raw.pop('qq_transport');(self.root/'config/settings.local.yaml').write_text(yaml.safe_dump(self.raw),encoding='utf-8')
        entries=[dict(component=c) for c in ('astrbot','gate','snowluma','qq_client','transport_watch')]
        health=dict(alive=True,connected=True,self_id_verified=True,online=True,channel_ready=True,channel_state='connected')
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'read_state',return_value=entries), \
             patch.object(manage,'alive',return_value=True),patch.object(manage,'port_open',return_value=True), \
             patch.object(manage,'fetch_health',return_value=health), \
             patch('qqbot_gateway.napcat_login_observer.listener_identity') as listener:
            report=manage.status_report();self.assertEqual(report['provider'],'snowluma')
            self.assertTrue(report['can_receive_group_messages']);listener.assert_not_called()
            health['channel_ready']=False;self.assertFalse(manage.status_report()['can_receive_group_messages'])
            self.snapshot.unlink();report=manage.status_report()
            self.assertEqual(report['provider'],'unknown');self.assertFalse(report['can_receive_group_messages'])


class PollTests(unittest.IsolatedAsyncioTestCase):
    async def test_gate_application_owns_monitor_startup_and_cleanup_without_listener(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);b=binding()
            cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,root/'seen.sqlite',
                transport_provider='snowluma',transport_instance_id=b.instance_id,transport_config_digest=b.config_digest)
            gate=OneBotGate(cfg,root);calls=[]
            class Monitor:
                task=None
                async def run(self):calls.append('run');await asyncio.Event().wait()
                async def close(self):
                    calls.append('close');self.task.cancel();await asyncio.gather(self.task,return_exceptions=True)
            monitor=Monitor();app=gate.application()
            with patch('qqbot_gateway.transport_owner.monitor_from_loaded',return_value=monitor) as factory:
                for callback in app.on_startup:await callback(app)
                await asyncio.sleep(0);factory.assert_called_once_with(gate)
                for callback in app.on_cleanup:await callback(app)
            self.assertEqual(calls,['run','close'])

    async def test_actual_gate_poll_accepts_nonce_and_revokes_when_identity_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);b=binding();owned=True
            owner=SimpleNamespace(binding=b,root=root,identity_current=lambda *a,**k:owned)
            cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,root/'seen.sqlite',
                transport_provider='snowluma',transport_instance_id=b.instance_id,transport_config_digest=b.config_digest,silence_enabled=False)
            gate=OneBotGate(cfg,root);gate.connected=True;gate.observe_online({'online':True,'good':True})
            producer=HealthProducer(b,KEY);monitor=HealthMonitor(gate,owner,KEY,session=object())
            async def exchange(method,path,body=None):
                self.assertEqual(method,'GET');return producer.response(path.split('nonce=')[1],observation())
            monitor.exchange=exchange
            self.assertTrue(await monitor.poll_once());self.assertTrue(gate.channel_ready())
            owned=False;self.assertFalse(await monitor.poll_once());self.assertFalse(gate.channel_ready())
            await monitor.close();gate.store.close()

    async def test_exchange_bounds_chunked_body_and_fixed_url_without_redirects(self):
        b=binding();response=SimpleNamespace(status=200,content_length=None)
        async def chunks(size):yield b'x'*8193
        response.content=SimpleNamespace(iter_chunked=chunks)
        class Context:
            async def __aenter__(self):return response
            async def __aexit__(self,*a):pass
        session=Mock();session.request.return_value=Context()
        monitor=object.__new__(HealthMonitor);monitor.owner=SimpleNamespace(binding=b);monitor.session=session
        with self.assertRaises(ValueError):await monitor.exchange('GET','/health?nonce='+'f'*64)
        session.request.assert_called_once_with('GET','http://127.0.0.1:5098/health?nonce='+'f'*64,data=None,allow_redirects=False)

    async def test_command_ack_domain_and_binding_cannot_be_substituted(self):
        b=binding();command=sign_command(b,KEY,'stop',1,now=lambda:1,nonce='f'*64)
        sent=json.loads(command);ack=b.fields()|dict(domain=ACK_DOMAIN,action='stop',seq=1,nonce=sent['nonce'],status='stopped')
        import hmac
        ack['mac']=hmac.new(KEY,canonical(ack),hashlib.sha256).hexdigest()
        self.assertTrue(verify_ack(canonical(ack),b,KEY,command))
        ack['domain']='qqbot-snowluma-health-v1';self.assertFalse(verify_ack(canonical(ack),b,KEY,command))

    async def test_python_signed_command_and_js_ack_interoperate_without_listener(self):
        b=binding();command=sign_command(b,KEY,'bind',1,now=lambda:1,nonce='f'*64)
        source="""import {createControlHandler} from './adapters/snowluma/control_plane.mjs';
const [binding,key,body]=JSON.parse(process.argv[1]);
const handler=createControlHandler({binding,key:Buffer.from(key,'hex'),now:()=>1000,
observe:()=>({}),identityCurrent:()=>true,stopRequested:()=>false,onBind:()=>{},onDrain:()=>{},onStop:()=>{}});
const response=await handler.handle({method:'POST',url:'/bind',body});process.stdout.write(response.body);"""
        result=subprocess.run(['node','--input-type=module','-e',source,json.dumps([b.fields(),KEY.hex(),command.decode()])],
            cwd=Path(__file__).resolve().parents[1],capture_output=True,check=True)
        self.assertTrue(verify_ack(result.stdout,b,KEY,command))

    async def test_run_binds_once_then_stop_marker_prevents_poll(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);b=binding();calls=[]
            monitor=object.__new__(HealthMonitor);monitor.owner=SimpleNamespace(root=root,binding=b)
            monitor.verifier=Mock();monitor.gate=Mock()
            monitor.gate.config.transport_ready_timeout=180
            async def command(action):
                calls.append(action);atomic_json(root/'state/stop-request.json',dict(instance_id=b.instance_id));return True
            async def poll():calls.append('poll')
            monitor.command=command;monitor.poll_once=poll
            await monitor.run();self.assertEqual(calls,['bind']);monitor.verifier.invalidate.assert_called_once()


if __name__=='__main__':unittest.main()
