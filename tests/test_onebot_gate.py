import asyncio
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest

import aiohttp
from aiohttp import web

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from qqbot_gateway.config import GateConfig
from qqbot_gateway.onebot_gate import OneBotGate, admitted_message, allowed_action, DedupStore


def configuration(path):
    return GateConfig('222', frozenset({'111'}), frozenset({'333'}), 'a'*40, 'b'*40, Path(path)/'seen.sqlite')


def message():
    return {'post_type':'message','message_type':'group','self_id':222,'user_id':333,
            'group_id':111,'message_id':1,
            'message':[{'type':'at','data':{'qq':'222'}},{'type':'text','data':{'text':'hello'}}]}


class PredicateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = configuration(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_real_at_and_scope(self):
        self.assertTrue(admitted_message(message(),self.config))
        cases = [ {'message_type':'private'}, {'group_id':444}, {'self_id':444},
                  {'user_id':222}, {'user_id':True}, {'post_type':'notice'},
                  {'message':[]}, {'message':'[CQ:at,qq=222]'},
                  {'message':[{'type':'at','data':{'qq':'all'}}]},
                  {'message':[{'type':'at','data':{'qq':'444'}}]},
                  {'message':[{'type':'reply','data':{'id':'1'}}]},
                  {'message':[{'type':'text','data':{'text':'@bot [CQ:at,qq=222] /总结 https://b23.tv/test'}}]},
                  {'message':[{'type':'text','data':{'text':'{"type":"at","data":{"qq":"222"}}'}}]},
                  {'message':[{'type':'at','data':'222'}]} ]
        for patch in cases:
            with self.subTest(patch=patch):
                event=message();event.update(patch)
                self.assertFalse(admitted_message(event,self.config))

    def test_empty_configuration_fails(self):
        for patch in ({'allowed_groups':frozenset()}, {'admin_users':frozenset()},
                      {'inbound_token':''},{'host':'0.0.0.0'}, {'upstream':'ws://192.168.1.1:6199/ws'}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                replace(self.config, **patch)

    def test_blocklist_admins_and_mentions_do_not_bypass(self):
        config = replace(self.config, blocked_users=frozenset({'333', '555'}))
        for user in (333, 555):
            for segments in (message()['message'], [], [{'type':'text','data':{'text':'222'}}]):
                event = message(); event.update(user_id=user, message=segments)
                self.assertFalse(admitted_message(event, config))
        event = message(); event['user_id'] = 666
        event['message'].append({'type':'text','data':{'text':'333'}})
        self.assertTrue(admitted_message(event, config))

    def test_persistent_dedup(self):
        store=DedupStore(self.config.database)
        self.assertTrue(store.reserve(message()))
        self.assertFalse(store.reserve(message()))
        store.close()
        store=DedupStore(self.config.database)
        self.assertFalse(store.reserve(message()))
        event=message();event['message_id']=2
        self.assertTrue(store.reserve(event))
        store.close()

    def test_outgoing_scope(self):
        allowed=[{'action':'get_login_info'}, {'action':'get_status'},
                 {'action':'get_stranger_info','params':{'user_id':222}},
                 {'action':'send_group_msg','params':{'group_id':111,'message':[{'type':'text','data':{'text':'hello'}}]}}]
        denied=[{'action':'send_private_msg','params':{'user_id':333,'message':[{'type':'text','data':{'text':'hello'}}]}},
                {'action':'get_stranger_info','params':{'user_id':333}},
                {'action':'get_stranger_info','params':{'user_id':True}},
                {'action':'get_stranger_info'},
                {'action':'send_group_msg','params':{'group_id':444}},
                {'action':'send_msg','params':{'message_type':'private','group_id':111}},
                {'action':'set_group_ban','params':{'group_id':111}},
                {'action':'get_group_member_list','params':{'group_id':444}},
                {'action':'send_group_msg','params':[]}, {'action':'unknown'}]
        for action in allowed:self.assertTrue(allowed_action(action,self.config))
        for action in denied:self.assertFalse(allowed_action(action,self.config))


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.received=asyncio.Queue()
        self.connections=asyncio.Queue()
        self.headers=[]

        async def upstream(request):
            self.headers.append(dict(request.headers))
            ws=web.WebSocketResponse();await ws.prepare(request)
            await self.connections.put(ws)
            async for frame in ws:
                if frame.type==aiohttp.WSMsgType.TEXT:await self.received.put(json.loads(frame.data))
            return ws

        app=web.Application();app.router.add_get('/ws',upstream)
        self.up_runner=web.AppRunner(app,access_log=None);await self.up_runner.setup()
        self.up_site=web.TCPSite(self.up_runner,'127.0.0.1',0);await self.up_site.start()
        port=self.up_site._server.sockets[0].getsockname()[1]
        self.config=replace(configuration(self.temp.name),upstream=f'ws://127.0.0.1:{port}/ws')
        self.gate=OneBotGate(self.config)
        self.runner=web.AppRunner(self.gate.application(),access_log=None);await self.runner.setup()
        self.site=web.TCPSite(self.runner,'127.0.0.1',0);await self.site.start()
        self.url=f'http://127.0.0.1:{self.site._server.sockets[0].getsockname()[1]}/ws'
        self.client=aiohttp.ClientSession(trust_env=False)
        self.auth={'Authorization':'Bearer '+self.config.inbound_token,'X-Self-ID':'222','X-Client-Role':'Universal'}

    async def asyncTearDown(self):
        await self.client.close();await self.runner.cleanup();await self.up_runner.cleanup();self.temp.cleanup()

    async def connect(self):
        ws=await self.client.ws_connect(self.url,headers=self.auth)
        upstream=await asyncio.wait_for(self.connections.get(),2)
        probe=await ws.receive_json(timeout=2)
        self.assertEqual(probe['action'],'get_status')
        await ws.send_json({'status':'ok','retcode':0,'data':{'online':True},'echo':probe['echo']})
        return ws,upstream

    async def test_health_online_unknown_stale_disconnect_and_probe_echo_is_private(self):
        import time
        self.assertEqual(self.gate.status()['channel_state'],'waiting_login')
        ws,up=await self.connect()
        await asyncio.sleep(.02)
        self.assertTrue(self.gate.status()['online'])
        self.assertTrue(self.received.empty())
        heartbeat={'post_type':'meta_event','meta_event_type':'heartbeat','self_id':222,'status':{'online':False}}
        await ws.send_json(heartbeat)
        await asyncio.wait_for(self.received.get(),2)
        self.assertEqual(self.gate.status()['channel_state'],'disconnected')
        self.gate.observe_online({'online':'true'})
        self.assertIsNone(self.gate.status()['online'])
        self.gate.observe_online({'online':True});self.gate.online_at=time.time()-46
        self.assertEqual(self.gate.status()['channel_state'],'unknown')
        async with self.client.get(self.url.replace('/ws','/health')) as response:
            data=await response.json()
        self.assertNotIn('self_id',data);self.assertNotIn('token',str(data))
        await ws.close()
        for _ in range(20):
            if not self.gate.connected:break
            await asyncio.sleep(.01)
        self.assertFalse(self.gate.status()['connected'])

    async def test_stop_marker_rejects_new_message_but_keeps_accepted_outbound(self):
        from unittest.mock import patch
        from qqbot_gateway.lifecycle import atomic_json
        self.gate.root=Path(self.temp.name)
        ws,up=await self.connect()
        atomic_json(self.gate.root/'state/stop-request.json',{'instance_id':'current'})
        with patch.dict('os.environ',{'QQBOT_INSTANCE_ID':'current'}), \
             patch.object(self.gate.store,'reserve',side_effect=AssertionError('draining must not reserve')):
            await ws.send_json(message())
            action={'action':'send_group_msg','params':{'group_id':111,'message':[{'type':'text','data':{'text':'already accepted'}}]},'echo':'final'}
            await up.send_json(action)
            self.assertEqual(await ws.receive_json(timeout=2),action)
            await ws.send_json({'status':'ok','retcode':0,'data':{'message_id':2},'echo':'final'})
            answer=await asyncio.wait_for(self.received.get(),2)
            self.assertEqual(answer['echo'],'final')
            self.assertTrue(self.received.empty())
        await ws.close()

    async def test_drops_and_heartbeat_and_dedup(self):
        ws,up=await self.connect()
        for patch in ({'group_id':444},{'message':[]},{'message_type':'private'},{'user_id':222},{'post_type':'notice'}):
            event=message();event.update(patch);await ws.send_json(event)
        await ws.send_str('bad json')
        for i in range(3):await ws.send_json(message())
        heartbeat={'post_type':'meta_event','meta_event_type':'heartbeat','self_id':222}
        await ws.send_json(heartbeat)
        self.assertEqual(await asyncio.wait_for(self.received.get(),2),message())
        self.assertEqual(await asyncio.wait_for(self.received.get(),2),heartbeat)
        self.assertTrue(self.received.empty())
        self.assertEqual(self.headers[0]['Authorization'],'Bearer '+self.config.upstream_token)
        self.assertEqual(self.headers[0]['X-Self-ID'],'222')
        await ws.close()

    async def test_actions_echo_and_rejection(self):
        ws,up=await self.connect()
        denied={'action':'send_private_msg','params':{'user_id':333},'echo':'denied'}
        await up.send_json(denied)
        reply=await asyncio.wait_for(self.received.get(),2)
        self.assertEqual(reply['echo'],'denied');self.assertEqual(reply['status'],'failed');self.assertEqual(reply['retcode'],1403)
        action={'action':'get_status','params':{},'echo':'query'}
        await up.send_json(action)
        self.assertEqual((await ws.receive_json(timeout=2)),action)
        response={'status':'ok','retcode':0,'data':{'online':True},'echo':'query'}
        await ws.send_json(response)
        self.assertEqual(await asyncio.wait_for(self.received.get(),2),response)
        await ws.close()

    async def test_blocked_never_reserves_or_forwards_then_unblock_admits(self):
        from unittest.mock import patch
        self.gate.config = replace(self.config, blocked_users=frozenset({'333'}))
        ws, up = await self.connect()
        with patch.object(self.gate.store, 'reserve', wraps=self.gate.store.reserve) as reserve:
            await ws.send_json(message())
            heartbeat = {'post_type':'meta_event','meta_event_type':'heartbeat','self_id':222}
            await ws.send_json(heartbeat)
            self.assertEqual(await asyncio.wait_for(self.received.get(), 2), heartbeat)
            reserve.assert_not_called()
            self.assertTrue(self.received.empty())
        self.gate.config = self.config  # Simulates a new, unblocked startup snapshot.
        await ws.send_json(message())
        self.assertEqual(await asyncio.wait_for(self.received.get(), 2), message())
        await ws.close()

    async def test_bad_auth_and_identity(self):
        for patch,status in [({'Authorization':'Bearer wrong'},401),({'X-Self-ID':'999'},403)]:
            headers=dict(self.auth);headers.update(patch)
            with self.assertRaises(aiohttp.WSServerHandshakeError) as result:
                await self.client.ws_connect(self.url,headers=headers)
            self.assertEqual(result.exception.status,status)

    async def test_second_connection_rejected(self):
        ws,up=await self.connect()
        with self.assertRaises(aiohttp.WSServerHandshakeError) as result:
            await self.client.ws_connect(self.url,headers=self.auth)
        self.assertEqual(result.exception.status,409)
        await ws.send_json(message())
        self.assertEqual(await asyncio.wait_for(self.received.get(),2),message())
        await ws.close()

    async def test_upstream_close_closes_downstream(self):
        ws,up=await self.connect()
        await up.close()
        frame=await asyncio.wait_for(ws.receive(),2)
        self.assertIn(frame.type,(aiohttp.WSMsgType.CLOSE,aiohttp.WSMsgType.CLOSED))

    async def test_reconnect_preserves_dedup(self):
        ws,up=await self.connect()
        await ws.send_json(message())
        await asyncio.wait_for(self.received.get(),2)
        await ws.close()
        for _ in range(20):
            if self.gate.active is None:break
            await asyncio.sleep(.01)
        ws,up=await self.connect()
        await ws.send_json(message())
        next_message=message();next_message['message_id']=2
        await ws.send_json(next_message)
        self.assertEqual(await asyncio.wait_for(self.received.get(),2),next_message)
        self.assertTrue(self.received.empty())
        await ws.close()


if __name__=='__main__':unittest.main()
