"""All identities, observations, keys and transports are synthetic; no listeners."""
import asyncio
from copy import deepcopy
from dataclasses import replace
import hashlib
import hmac
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import aiohttp
from aiohttp import web

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src'), str(ROOT/'tests')]
from qqbot_gateway.transport_health import (HealthBinding, HealthProducer, HealthVerifier,
    FLAGS, canonical, strict_json)
from qqbot_gateway.config import GateConfig
from qqbot_gateway.onebot_gate import OneBotGate, echo_key
from test_group_silence import Capture, Duplex, frames, event

KEY = b'k'*32


def binding():
    return HealthBinding('a'*32, 'b'*64, 'c'*64, 'd'*64, 'e'*64, 12, 1700000000000, 13, 1700000000001, 5098)


def observation(**values):
    return {k:True for k in FLAGS} | dict(phase='ready', last_rx_age_ms=1) | values


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.;self.owned = True
        self.v = HealthVerifier(binding(), KEY, lambda b:self.owned, clock=lambda:self.now)
        self.p = HealthProducer(binding(), KEY)

    def proof(self, **values):return self.p.response(self.v.challenge(), observation(**values))

    def test_nonce_hmac_freshness_replay_and_ttl(self):
        proof = self.proof();self.assertTrue(self.v.accept(proof));self.assertTrue(self.v.ready())
        self.assertFalse(self.v.accept(proof));self.assertFalse(self.v.ready())
        proof = self.proof();self.now += 3.01
        self.assertFalse(self.v.accept(proof))
        self.assertTrue(self.v.accept(self.proof()));self.now += 15
        self.assertFalse(self.v.ready());self.assertEqual(self.v.mirror()['expires_mono'], 0)

    def test_identity_registry_listener_and_binding_changes_never_self_attest(self):
        self.assertTrue(self.v.accept(self.proof()));self.owned = False
        self.assertFalse(self.v.ready())
        self.assertFalse(self.v.accept(self.proof()))
        self.owned = True
        for field, value in [('qq_created',1700000000099), ('node_pid',99), ('listener_port',5097),
                             ('policy_digest','1'*64), ('build_hash','2'*64), ('config_digest','3'*64),
                             ('transport_epoch','4'*64), ('instance_id','5'*32)]:
            producer = HealthProducer(replace(binding(), **{field:value}), KEY)
            self.assertFalse(self.v.accept(producer.response(self.v.challenge(), observation())))

    def test_unarmed_good_is_not_enough_and_health_flags_strict(self):
        for values in [dict(rx_watch_armed=False),dict(receive_healthy=False),dict(account_match=False),
                       dict(pipe_connected=False),dict(logged_in=False),dict(outbound_healthy=False),
                       dict(phase='draining'),dict(last_rx_age_ms=105001)]:
            self.assertTrue(self.v.accept(self.proof(**values)))
            self.assertFalse(self.v.ready())
        with self.assertRaises(ValueError):self.proof(rx_watch_armed=1)
        with self.assertRaises(ValueError):HealthVerifier(binding(), b'short', lambda b:True)

    def test_bad_json_nan_unknown_fields_size_wrong_nonce_key_or_sequence(self):
        valid = self.proof()
        for content in [b'x'*8193, b'{}', b'{"schema":1,"schema":1}', b'{"seq":NaN}', b'[]']:
            self.v.challenge();self.assertFalse(self.v.accept(content))
        for mutate in [lambda o:o.update(unknown=True),lambda o:o.update(seq=True),
                       lambda o:o.update(seq=0),lambda o:o.update(mac='0'*64),
                       lambda o:o.update(nonce='0'*64), lambda o:o.update(last_rx_age_ms=float('nan'))]:
            obj=json.loads(self.proof());mutate(obj)
            self.assertFalse(self.v.accept(json.dumps(obj).encode()))
        self.assertFalse(self.v.accept(HealthProducer(binding(), b'q'*32).response(self.v.challenge(),observation())))
        self.assertTrue(self.v.accept(self.proof()))
        stale = HealthProducer(binding(),KEY).response(self.v.challenge(),observation())
        self.assertFalse(self.v.accept(stale))
        self.assertFalse(self.v.ready())

    def test_clock_rollback_and_status_no_identity_or_secret(self):
        self.assertTrue(self.v.accept(self.proof()));self.now -= 1
        self.assertFalse(self.v.ready())
        self.assertEqual(set(self.v.safe_status()), {'trusted','ready','sequence','armed'})
        self.assertNotIn('pid', json.dumps(self.v.safe_status()))

    def test_configured_thirty_second_ttl_is_respected_without_45_second_mirror(self):
        self.v=HealthVerifier(binding(),KEY,lambda b:True,ttl=30,clock=lambda:self.now)
        self.assertTrue(self.v.accept(self.proof()))
        self.now+=16;self.assertTrue(self.v.ready())
        self.assertEqual(self.v.mirror()['expires_mono']-self.now,14)
        self.now+=14;self.assertFalse(self.v.ready())

    def test_js_producer_interoperates_with_actual_python_verifier(self):
        nonce=self.v.challenge()
        source = ("import {createHealthProducer} from '"+(ROOT/'adapters/snowluma/project_policy.mjs').as_uri()+"';"
            "let s='';for await(const x of process.stdin)s+=x;const i=JSON.parse(s);"
            "process.stdout.write(createHealthProducer(i.binding,Buffer.alloc(32,107)).response(i.nonce,i.observation));")
        result=subprocess.run(['node','--input-type=module','-e',source],
            input=json.dumps(dict(binding=binding().fields(),nonce=nonce,observation=observation())).encode(),
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,cwd=ROOT)
        self.assertTrue(self.v.accept(result.stdout));self.assertTrue(self.v.ready())


class GateHealthTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.cfg=GateConfig('222',frozenset({'111','444'}),frozenset({'333'}),'a'*40,'b'*40,self.root/'seen.sqlite',
            blocked_users=frozenset({'999'}),transport_provider='snowluma',transport_instance_id='a'*32,
            transport_config_digest='c'*64,silence_enabled=False)
        self.g=OneBotGate(self.cfg,self.root);self.up=Capture();self.down=Capture();self.pending=set()
        self.owned=True;self.v=HealthVerifier(binding(),KEY,lambda b:self.owned)
        self.p=HealthProducer(binding(),KEY)
        self.g.bind_transport_health(self.v)
        self.g.connected=True;self.g.active=self.down
        self.g.observe_online({'online':True,'good':True})
        self.mid=0

    async def asyncTearDown(self):self.g.store.close();self.temp.cleanup()

    def ready(self, **values):
        self.g.accept_transport_health(self.p.response(self.v.challenge(),observation(**values)))
        return self.g.channel_ready()

    async def inbound(self, **values):
        self.mid+=1;e=event(mid=self.mid);e.update(values);out=Capture()
        await self.g._incoming(frames(e),out,self.pending)
        return out.rows

    async def output(self,ticket,action='send_group_msg'):
        params=dict(group_id='111',message=[dict(type='text',data={'text':'synthetic'})])
        if action=='send_msg':params['message_type']='group'
        if ticket is not None:params['qqbot_output_ticket']=ticket
        await self.g._outgoing(Duplex(frames(dict(action=action,params=params,echo='send-'+str(self.mid))),self.up),self.down,self.pending)

    async def test_no_health_and_unarmed_drop_before_actual_dedup_or_capabilities(self):
        with patch.object(self.g.store,'reserve',side_effect=AssertionError('dedup reached')), \
             patch.object(self.g.materials,'issue',side_effect=AssertionError('material reached')):
            self.assertFalse(await self.inbound())
            self.assertFalse(self.ready(rx_watch_armed=False))
            self.assertFalse(await self.inbound())
        self.assertTrue(self.ready());rows=await self.inbound()
        self.assertEqual(len(rows),1);self.assertIn('qqbot_output_ticket',rows[0])
        self.assertEqual(rows[0]['qqbot_connection'],self.g.connection_id)

    async def test_blacklist_scope_free_and_quotes_use_actual_gate(self):
        self.assertTrue(self.ready());self.g.config=replace(self.cfg,participation_mode='free')
        for values in [dict(user_id='999'),dict(user_id='222'),dict(group_id='777'),dict(message_type='private')]:
            with patch.object(self.g.store,'reserve',side_effect=AssertionError('reject persisted')):
                self.assertFalse(await self.inbound(**values))
        rows=await self.inbound(message=[dict(type='reply',data=dict(id='9',content='PRIVATE_QUOTE')),
                                       dict(type='text',data=dict(text='#sl'))])
        self.assertEqual(len(rows),1);self.assertNotIn('PRIVATE_QUOTE',json.dumps(rows))
        self.assertEqual(rows[0]['qqbot_reference'],'9')

    async def test_health_and_ack_frames_flow_while_user_channel_closed(self):
        future=asyncio.get_running_loop().create_future();key=echo_key('h');self.g.health_pending[key]=future
        await self.g._incoming(frames(dict(post_type='meta_event',meta_event_type='heartbeat',self_id='222',status=dict(online=True,good=True)),
            dict(status='ok',retcode=0,data=dict(online=True,good=True),echo='h')),
            self.up,self.pending)
        self.assertTrue(future.done());self.assertTrue(self.g.good);self.assertEqual(len(self.up.rows),1)
        self.pending.add(echo_key('old-send'))
        await self.g._incoming(frames(dict(status='ok',retcode=0,data=dict(message_id='-77'),echo='old-send')),self.up,self.pending)
        self.assertEqual(self.up.rows[-1]['data']['message_id'],'-77')
        self.assertFalse(self.g.channel_ready())
        await self.g._outgoing(Duplex(frames(dict(action='get_status',params={},echo='status')),self.up),self.down,self.pending)
        self.assertEqual(self.down.rows[-1]['action'],'get_status')

    async def test_good_missing_false_pid_reuse_stop_and_expiry_revoke_epoch(self):
        for status in [dict(online=True),dict(online=True,good=False)]:
            self.g.observe_online(dict(online=True,good=True));self.assertTrue(self.ready())
            old=self.g.connection_id;self.g.observe_online(status)
            self.assertFalse(self.g.channel_ready());self.assertNotEqual(old,self.g.connection_id)
        self.g.observe_online(dict(online=True,good=True));self.assertTrue(self.ready())
        old=self.g.connection_id;self.owned=False
        self.assertFalse(self.g.channel_ready());self.assertNotEqual(old,self.g.connection_id)
        self.owned=True;self.assertTrue(self.ready());old=self.g.connection_id
        with patch('qqbot_gateway.onebot_gate.stopping',return_value=True):self.assertFalse(self.g.channel_ready())
        self.assertNotEqual(old,self.g.connection_id)

    async def test_no_ws_frames_expiry_loop_revokes_materials_and_mirror(self):
        self.assertTrue(self.ready());old=self.g.connection_id
        self.g.members.caps['fixture']={}
        self.g.mention_pending['fixture']=True
        self.v.expires=time.monotonic()-1
        async def stop_tick(_):raise asyncio.CancelledError()
        with patch('qqbot_gateway.onebot_gate.asyncio.sleep',stop_tick):
            with self.assertRaises(asyncio.CancelledError):await self.g._transport_expiry_loop()
        self.assertNotEqual(old,self.g.connection_id);self.assertFalse(self.g.members.caps)
        self.assertFalse(self.g.mention_pending)
        mirror=json.loads((self.root/'state/gate-connection.json').read_text())
        self.assertFalse(mirror['channel_ready']);self.assertFalse(mirror['health']['ready'])

    async def test_deadline_timer_uses_poll_bound_then_exact_remaining_and_delayed_proof_rotates(self):
        self.assertTrue(self.ready());old=self.g.connection_id
        self.v.expires=time.monotonic()+.02;delays=[]
        async def tick(delay):
            delays.append(delay)
            if len(delays)==1:self.v.expires=time.monotonic()-1
            else:raise asyncio.CancelledError()
        with patch('qqbot_gateway.onebot_gate.asyncio.sleep',tick):
            with self.assertRaises(asyncio.CancelledError):await self.g._transport_expiry_loop()
        self.assertAlmostEqual(delays[0],.02,places=5);self.assertGreater(delays[0],0)
        self.assertEqual(delays[1],self.cfg.transport_health_poll)
        self.assertNotEqual(old,self.g.connection_id)
        self.assertTrue(self.ready());old=self.g.connection_id
        self.v.expires=time.monotonic()-1
        self.assertTrue(self.ready()) # new proof arrives before any separate ready/status call
        self.assertNotEqual(old,self.g.connection_id)

    async def test_final_gate_output_requires_current_ticket_even_silence_disabled(self):
        self.assertTrue(self.ready());row=(await self.inbound())[0]
        await self.output(None);self.assertFalse(self.down.rows)
        await self.output(row['qqbot_output_ticket']);self.assertEqual(len(self.down.rows),1)
        self.v.expires=time.monotonic()-1;self.g.channel_ready()
        self.assertTrue(self.ready());await self.output(row['qqbot_output_ticket'])
        self.assertEqual(len(self.down.rows),1)
        new=(await self.inbound())[0];await self.output(new['qqbot_output_ticket'])
        self.assertEqual(len(self.down.rows),2)
        # A transport exception is still unknown, never rewritten as a known denial.
        latest=(await self.inbound())[0]
        async def transport_failure(_):raise ValueError('synthetic transport failure')
        before=len(self.up.rows)
        with patch.object(self.down,'send_json',transport_failure), self.assertRaises(ValueError):
            await self.output(latest['qqbot_output_ticket'])
        self.assertEqual(len(self.up.rows),before)

    async def test_send_alias_image_and_typed_mention_all_share_health_fence(self):
        self.assertTrue(self.ready());row=(await self.inbound())[0]
        await self.output(row['qqbot_output_ticket'],action='send_msg')
        self.assertEqual(self.down.rows[-1]['action'],'send_msg')
        self.g.observe_online(dict(online=True,good=False));before=len(self.down.rows)
        outputs=[dict(action='send_msg',params=dict(message_type='group',group_id='111',message=[dict(type='text',data=dict(text='fixture'))])),
            dict(action='send_group_msg',params=dict(group_id='111',message=[dict(type='image',data=dict(file='file:///fixture'))])),
            dict(action='send_group_msg',params=dict(group_id='111',message=[dict(type='text',data=dict(text='fixture'))],qqbot_mention_permission='fixture'))]
        with patch.object(self.g.members,'consume',side_effect=AssertionError('member permission used while closed')), \
             patch('qqbot_gateway.onebot_gate.allowed_segments',side_effect=AssertionError('image inspected while closed')):
            for n,output in enumerate(outputs):
                await self.g._outgoing(Duplex(frames(output|dict(echo='denied-'+str(n))),self.up),self.down,self.pending)
        self.assertEqual(len(self.down.rows),before)

    async def test_all_context_and_favorites_rpc_paths_closed_before_reading_body_or_sending(self):
        self.g.config=replace(self.cfg,vision_enabled=True,members_enabled=True)
        self.g.context_token='context';self.g.admin_token='admin'
        class Headers(dict):
            def getall(self,key,default):return [self[key]] if key in self else default
        class Request:
            remote='127.0.0.1';content_length=2;path='/context/vision/resolve'
            headers=Headers(Authorization='Bearer context')
            async def text(self):raise AssertionError('context body read')
            async def json(self):return dict(count=1,mode='basic')
        req=Request()
        for operation in ('bind','resolve'):
            req.path='/context/vision/'+operation
            with self.assertRaises(web.HTTPServiceUnavailable):await self.g.resolve_vision(req)
        for operation in ('bind','resolve','permit'):
            req.path='/context/members/'+operation
            with self.assertRaises(web.HTTPServiceUnavailable):await self.g.resolve_members(req)
        self.assertFalse(self.g.member_allowed(('222','111','333','1')))
        with self.assertRaises(ValueError):await self.g.member_rpc('get_group_info',dict(group_id='111'))
        req.headers=Headers(Authorization='Bearer admin')
        with self.assertRaises(web.HTTPServiceUnavailable):await self.g.favorites(req)
        self.assertFalse(self.down.rows)

    async def test_context_return_after_expiry_is_rechecked(self):
        self.assertTrue(self.ready())
        original=self.down.send_json
        async def expire_and_reply(value):
            await original(value);self.v.expires=time.monotonic()-1
            self.g.admin_pending[echo_key(value['echo'])].set_result(dict(status='ok',retcode=0,data={}))
        self.down.send_json=expire_and_reply
        with self.assertRaises(ValueError):await self.g.member_rpc('get_group_info',dict(group_id='111'))

    async def test_vision_and_member_final_http_results_recheck_health_after_await(self):
        self.g.config=replace(self.cfg,vision_enabled=True,members_enabled=True)
        self.g.context_token='context'
        class Headers(dict):
            def getall(self,key,default):return [self[key]] if key in self else default
        req=SimpleNamespace(remote='127.0.0.1',content_length=2,path='/context/vision/resolve',
                            headers=Headers(Authorization='Bearer context'))
        async def body():return '{}'
        req.text=body
        async def late(*args):
            self.v.expires=time.monotonic()-1
            return dict(fixture='never released')
        for target,operation in [(self.g.materials,self.g.resolve_vision),(self.g.members,self.g.resolve_members)]:
            self.assertTrue(self.ready())
            with patch.object(target,'resolve',late), self.assertRaises(web.HTTPBadRequest):await operation(req)

    async def test_load_gate_config_consumes_provider_digest_and_ttl_without_proof_secret(self):
        from test_qq_transport import synthetic
        from qqbot_gateway.config import normalize_settings,load_gate_config
        from qqbot_gateway.config_files import sha,canonical as config_canonical
        raw=synthetic();raw['qq_transport']=dict(provider='snowluma',snowluma=dict(health_poll_seconds=10,health_ttl_seconds=30))
        data=normalize_settings(raw)
        path=self.root/data['secrets_file'];path.parent.mkdir();path.write_text(json.dumps(dict(onebot_inbound='a'*40,onebot_upstream='b'*40)))
        with patch.dict(os.environ,{'QQBOT_INSTANCE_ID':'a'*32}):cfg=load_gate_config(root=self.root,settings=data)
        self.assertEqual(cfg.transport_provider,'snowluma');self.assertEqual(cfg.transport_health_ttl,30)
        self.assertEqual(cfg.transport_config_digest,sha(config_canonical(data)))
        self.assertFalse((self.root/'secrets/snowluma-control.local.json').exists())

    async def test_missing_binding_bad_frames_safe_status_and_napcat_legacy(self):
        self.g.transport_health=None
        self.assertFalse(self.g.channel_ready());self.assertFalse(await self.inbound())
        self.g.config=replace(self.cfg,transport_provider='napcat')
        # Old direct _incoming use has no connected/online precondition.
        self.g.connected=False;self.g.online=None
        self.assertEqual(len(await self.inbound()),1)
        self.g.config=self.cfg;self.g.connected=True;self.g.online=True
        for raw in ('{"post_type":"message","value":NaN}', 'x'*1048577, '{"a":1,"a":2}'):
            async def raw_frames():yield SimpleNamespace(type=aiohttp.WSMsgType.TEXT,data=raw)
            await self.g._incoming(raw_frames(),self.up,self.pending)
        status=self.g.status()
        self.assertFalse(status['channel_ready'])
        self.assertNotIn('instance_id',json.dumps(status));self.assertNotIn('pid',json.dumps(status))


if __name__=='__main__':unittest.main()
