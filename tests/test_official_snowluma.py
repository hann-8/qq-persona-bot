"""Official OneBot contract; synthetic events, temp state and local test sockets only."""
import asyncio
from contextlib import ExitStack, redirect_stdout
from dataclasses import replace
from io import StringIO
import json
import os
from pathlib import Path
import site
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import aiohttp
import yaml

import test_onebot_gate as gate_fixtures
from test_onebot_gate import message
from test_config_files import synthetic
from qqbot_gateway.lifecycle import atomic_json
from scripts import manage


class OfficialWireTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await gate_fixtures.TransportTests.asyncSetUp(self)
        self.sockets=[]

    async def asyncTearDown(self):
        for ws in self.sockets:await ws.close()
        await gate_fixtures.TransportTests.asyncTearDown(self)

    async def connect(self):
        self.gate.config=replace(self.config,transport_provider='snowluma',
            transport_instance_id='a'*32,transport_config_digest='c'*64)
        self.gate.root=Path(self.temp.name)
        ws=await self.client.ws_connect(self.url,headers=self.auth)
        self.sockets.append(ws)
        up=await asyncio.wait_for(self.connections.get(),2)
        probe=await ws.receive_json(timeout=2)
        await ws.send_json(dict(status='ok',retcode=0,data=dict(online=True,good=True),echo=probe['echo']))
        for _ in range(100):
            if self.gate.channel_ready():break
            await asyncio.sleep(.001)
        self.assertTrue(self.gate.channel_ready())
        self.assertIsNone(self.gate.transport_monitor_task)
        self.assertIsNone(self.gate.transport_health)
        return ws,up

    async def test_standard_handshake_text_and_correlated_ack(self):
        ws,up=await self.connect()
        await ws.send_json(message())
        row=await asyncio.wait_for(self.received.get(),2)
        self.assertEqual(row['message'],message()['message'])
        action=dict(action='send_group_msg',params=dict(group_id=111,
            message=[dict(type='text',data=dict(text='synthetic answer'))],
            qqbot_output_ticket=row['qqbot_output_ticket']),echo='answer')
        await up.send_json(action)
        wire=await ws.receive_json(timeout=2)
        self.assertEqual(wire['params'],{k:v for k,v in action['params'].items() if k!='qqbot_output_ticket'})
        await ws.send_json(dict(status='ok',retcode=0,data=dict(message_id=-99),echo='unrelated'))
        await ws.send_json(dict(status='ok',retcode=0,data=dict(message_id=-99),echo='answer'))
        ack=await asyncio.wait_for(self.received.get(),2)
        self.assertEqual(ack['echo'],'answer');self.assertEqual(ack['data']['message_id'],-99)
        self.assertEqual(self.gate.send_metrics()['acked'],1)
        self.assertTrue(self.received.empty())

    async def test_account_group_private_and_outgoing_scope(self):
        ws,up=await self.connect()
        for delta in (dict(self_id=999),dict(group_id=999),dict(message_type='private'),dict(user_id=222)):
            await ws.send_json(message()|delta)
        await ws.send_json(message())
        row=await asyncio.wait_for(self.received.get(),2)
        self.assertEqual(row['group_id'],111);self.assertTrue(self.received.empty())
        for action,params in [('send_private_msg',dict(user_id=333)),('send_group_msg',dict(group_id=999))]:
            await up.send_json(dict(action=action,params=params,echo='denied'))
            denied=await asyncio.wait_for(self.received.get(),2)
            self.assertEqual(denied['retcode'],1403)
        for headers in (self.auth|{'Authorization':'Bearer wrong'},self.auth|{'X-Self-ID':'999'}):
            with self.assertRaises(aiohttp.WSServerHandshakeError):
                await self.client.ws_connect(self.url,headers=headers)

    async def test_onebot_status_offline_bad_missing_and_stale(self):
        ws,up=await self.connect()
        for status in (dict(online=False,good=False),dict(online=True,good=False),dict(online=True),None):
            self.gate.observe_online(status)
            self.assertFalse(self.gate.channel_ready())
            if status and status['online'] is False:
                self.assertEqual(self.gate.status()['channel_state'],'disconnected')
        self.gate.observe_online(dict(online=True,good=True))
        self.gate.online_at=time.time()-46
        self.assertFalse(self.gate.channel_ready())
        self.gate.observe_online(dict(online=True,good=True))
        self.assertTrue(self.gate.channel_ready())

    async def test_free_mode_remains_explicit(self):
        ws,up=await self.connect()
        plain=message();plain['message']=[dict(type='text',data=dict(text='plain'))]
        await ws.send_json(plain)
        await ws.send_json(message()|dict(message_id=2))
        self.assertEqual((await asyncio.wait_for(self.received.get(),2))['message_id'],2)
        self.gate.config=replace(self.gate.config,participation_mode='free')
        await ws.send_json(plain|dict(message_id=3))
        self.assertEqual((await asyncio.wait_for(self.received.get(),2))['message_id'],3)

    async def test_actual_astrbot_conversion_router_and_reply(self):
        extra=os.environ.get('QQBOT_TEST_ASTRBOT_SITE')
        if extra:site.addsitedir(extra)
        with tempfile.TemporaryDirectory() as import_dir:
            old=os.getcwd();os.chdir(import_dir)
            try:
                from plugins.qq_router.main import QQRouter
                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_platform_adapter import AiocqhttpAdapter
                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                from astrbot.api.platform import PlatformMetadata
                from aiocqhttp import Event
            finally:os.chdir(old)
        ws,up=await self.connect()
        await ws.send_json(message()|dict(time=1700000000,sender=dict(user_id=333,nickname='fixture')))
        row=await asyncio.wait_for(self.received.get(),2)
        test=self
        class Bot:
            async def call_action(self,action,**params):
                if action=='get_group_member_info':return dict(card='fixture')
                raise AssertionError(action)
            async def send_group_msg(self,**params):
                await up.send_json(dict(action='send_group_msg',params=params,echo='framework'))
                ack=await asyncio.wait_for(test.received.get(),2)
                test.assertEqual(ack['status'],'ok')
                return ack['data']
        bot=Bot();adapter=AiocqhttpAdapter.__new__(AiocqhttpAdapter);adapter.bot=bot
        msg=await adapter.convert_message(Event(row))
        e=AiocqhttpMessageEvent(msg.message_str,msg,PlatformMetadata(name='aiocqhttp',description='fixture',id='qqbot'),'111',bot)
        router=QQRouter.__new__(QQRouter)
        router.root=Path(self.temp.name);router.bot='222';router.groups={'111'};router.blocked=set()
        router.transport_provider='snowluma';router.transport_instance_id='a'*32;router.transport_config_digest='c'*64
        router.participation=dict(mode='mentions',silence=dict(enabled=False))
        e.set_extra('qq_transport_connection',row['qqbot_connection'])
        e.set_extra('qq_output_ticket',row['qqbot_output_ticket']);e.set_extra('qq_silence_enabled',True)
        from qqbot_gateway.event_guard import EventSendGuard
        guard=EventSendGuard(e);e.set_extra('qq_send_guard',guard)
        self.assertIn('hello',e.message_str)
        self.assertEqual(e.get_sender_id(),'333')
        self.assertTrue(router.transport_allowed(e))
        async def acknowledge():
            action=await ws.receive_json(timeout=2)
            self.assertEqual(action['action'],'send_group_msg')
            self.assertEqual(action['params']['message'],[dict(type='text',data=dict(text='synthetic framework reply'))])
            await ws.send_json(dict(status='ok',retcode=0,data=dict(message_id=-100),echo=action['echo']))
        task=asyncio.create_task(acknowledge())
        with guard.grant():await e.send(e.plain_result('synthetic framework reply'))
        await task
        self.gate.observe_online(dict(online=True,good=False))
        self.assertFalse(router.transport_allowed(e))
        self.gate.observe_online(dict(online=True,good=True))
        self.assertFalse(router.transport_allowed(e))  # old event belongs to prior connection epoch


class OfficialManagementTests(unittest.TestCase):
    def test_start_launches_only_framework_and_stop_has_no_private_control(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root=Path(directory);(root/'config').mkdir()
            data=synthetic();data['qq_transport']={'provider':'snowluma'}
            (root/'config/settings.local.yaml').write_text(yaml.safe_dump(data),encoding='utf-8')
            atomic_json(root/data['secrets_file'],dict(onebot_inbound='x'*40,onebot_upstream='y'*40))
            cfg=dict(platform_settings={},provider_settings=dict(proactive_capability={}))
            atomic_json(root/'runtime/astrbot/data/cmd_config.json',cfg)
            stack.enter_context(patch.object(manage,'ROOT',root))
            stack.enter_context(patch.object(manage,'STATE',root/'state/managed-processes.json'))
            stack.enter_context(patch.object(manage,'check_port'))
            stack.enter_context(patch.object(manage,'show_status'))
            stack.enter_context(patch.object(manage,'status_report',return_value={}))
            stack.enter_context(patch.object(manage,'require_runtime',side_effect=AssertionError('private runtime')))
            stack.enter_context(patch.object(manage,'prepare_stop_control',side_effect=AssertionError('private control')))
            stack.enter_context(patch.object(manage.subprocess,'run',return_value=SimpleNamespace(returncode=0)))
            class Socket:
                def __enter__(self):return self
                def __exit__(self,*a):pass
                def settimeout(self,*a):pass
                def connect_ex(self,*a):return 0
            stack.enter_context(patch.object(manage.socket,'socket',Socket))
            def capture(entries,process,component,started):
                entries.append(dict(component=component,pid=123,created=1.));manage.save(entries)
                mode=manage.service_mode()
                atomic_json(root/'state/router-ready.json',dict(instance_id=mode['instance_id'],config_digest=mode['configuration']['snapshot_digest']))
            stack.enter_context(patch.object(manage,'capture',side_effect=capture))
            stack.enter_context(patch.object(manage,'alive',return_value=Mock()))
            launch=stack.enter_context(patch.object(manage.psutil,'Popen'))
            stack.enter_context(redirect_stdout(StringIO()))
            manage._start_channel(full=True)
            components=[c.args[0][2] for c in launch.call_args_list]
            self.assertEqual(components,['astrbot','model','gate'])
            self.assertEqual(manage.service_mode()['transport_mode'],'official_onebot')
            stop=stack.enter_context(patch.object(manage,'stop'))
            manage.stop_project(grace=0)
            stop.assert_called_once()
            self.assertFalse((root/'state/qq-transport').exists())

    def test_status_needs_no_qq_owner_or_private_listener(self):
        with ExitStack() as stack:
            entries=[dict(component=c,pid=123,created=1.) for c in ('astrbot','model','gate')]
            stack.enter_context(patch.object(manage,'read_state',return_value=entries))
            stack.enter_context(patch.object(manage,'alive',return_value=Mock()))
            stack.enter_context(patch.object(manage,'loaded_provider',return_value='snowluma'))
            stack.enter_context(patch.object(manage,'service_mode',return_value=dict(mode='text')))
            stack.enter_context(patch.object(manage,'port_open',side_effect=lambda p:p in (6185,6199,6200,8765)))
            stack.enter_context(patch.object(manage,'fetch_health',return_value=dict(alive=True,router_ready=True,connected=True,self_id_verified=True,online=True,channel_ready=True)))
            stack.enter_context(patch.object(manage,'configuration_status',return_value={}))
            stack.enter_context(patch.object(manage,'autostart_status',return_value={}))
            stack.enter_context(patch.object(manage,'task_counts',return_value={}))
            report=manage.status_report(disk_config=SimpleNamespace(settings=synthetic()))
            self.assertEqual(report['process_state'],'running')
            self.assertTrue(report['can_receive_group_messages'])


if __name__=='__main__':unittest.main()
