"""Actual AstrBot conversion/router hooks with fake transport; zero listeners/model."""
import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
import site
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
import test_transport_health as health_fixtures
from test_group_silence import Capture, Duplex, frames


class RouterTests(health_fixtures.GateHealthTests):
    """Inherited gate cases also run, plus actual framework output/mirror paths."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.dont_write_bytecode=True
        if os.environ.get('QQBOT_TEST_ASTRBOT_SITE'):site.addsitedir(os.environ['QQBOT_TEST_ASTRBOT_SITE'])
        os.environ['ASTRBOT_DISABLE_METRICS']='1'
        cls.import_temp=tempfile.TemporaryDirectory()
        old=os.getcwd();os.chdir(cls.import_temp.name)
        try:
            from plugins.qq_router.main import QQRouter
            from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_platform_adapter import AiocqhttpAdapter
            from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
            from astrbot.api.platform import PlatformMetadata
            from aiocqhttp import Event
            cls.Router,cls.Adapter,cls.MessageEvent,cls.PlatformMetadata,cls.Event=QQRouter,AiocqhttpAdapter,AiocqhttpMessageEvent,PlatformMetadata,Event
        finally:os.chdir(old)

    @classmethod
    def tearDownClass(cls):cls.import_temp.cleanup();super().tearDownClass()

    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.router=self.Router.__new__(self.Router)
        self.router.root=self.root;self.router.bot='222';self.router.groups={'111','444'}
        self.router.blocked={'999'};self.router.admins={'333'};self.router.persona_id='fixture-persona'
        self.router.transport_provider='snowluma';self.router.transport_instance_id='a'*32
        self.router.transport_config_digest='c'*64;self.router.transport_health_ttl=15
        self.router.participation=dict(mode='mentions',silence=dict(enabled=False))
        self.router.connection_id=None;self.router.silence_mirror=None
        self.invalidations=0
        def invalidate():self.invalidations+=1
        self.router.group_turns=SimpleNamespace(invalidate=invalidate,group_epoch=lambda group:'fixture-epoch')
        self.router.tasks=SimpleNamespace(group_blocked=lambda group:False)
        from qqbot_gateway.reply_delivery import GroupDeliveryQueue
        self.router.delivery=SimpleNamespace(queue=GroupDeliveryQueue())

    async def framework_event(self, row):
        test=self
        class Bot:
            def __init__(self):self.sent=[];self.rpc=[]
            async def call_action(self,action,**kwargs):
                self.rpc.append(action)
                if action=='get_group_member_info' and kwargs['user_id']==222:return dict(card='fixture-bot')
                raise AssertionError('Unexpected history/other RPC')
            async def send_group_msg(self,**kwargs):
                before=len(test.down.rows)
                await test.g._outgoing(Duplex(frames(dict(action='send_group_msg',params=kwargs,echo='fixture-send')),test.up),test.down,test.pending)
                if len(test.down.rows)==before:
                    from aiocqhttp.exceptions import ActionFailed
                    raise ActionFailed(dict(status='failed',retcode=1403))
                self.sent.append(deepcopy(test.down.rows[-1]['params']))
                return dict(message_id='-99')
        bot=Bot();adapter=self.Adapter.__new__(self.Adapter);adapter.bot=bot
        msg=await adapter.convert_message(self.Event(row))
        result=self.MessageEvent(msg.message_str,msg,self.PlatformMetadata(name='aiocqhttp',description='fixture',id='qqbot'),'111',bot)
        result.set_extra('qq_transport_connection',row.get('qqbot_connection'))
        result.set_extra('qq_output_ticket',row.get('qqbot_output_ticket'))
        result.set_extra('qq_silence_enabled',True)
        result.set_extra('qq_delivery_version',self.router.persona_id)
        result.set_extra('qq_delivery_identity',('222','111','333'))
        from qqbot_gateway.event_guard import EventSendGuard
        result.set_extra('qq_send_guard',EventSendGuard(result))
        return result

    async def test_actual_js_gate_astrbot_parser_time_sender_image_and_no_reply_fetch(self):
        from dataclasses import replace
        self.assertTrue(self.ready());self.g.config=replace(self.cfg,vision_enabled=True)
        e=dict(instance_id='a'*32,transport_epoch='b'*64,post_type='message',message_type='group',self_id='222',
            group_id='111',user_id='333',message_id='-123',time=1700000000,message=[
                dict(type='at',data={'qq':'222'}),dict(type='text',data={'text':'fixture-current'}),
                dict(type='reply',data={'id':'9','content':'PRIVATE_QUOTE'}),
                dict(type='image',data={'url':'https://gchat.qpic.cn/fixture','file':'fixture.jpg'})])
        source=("import {createProjectPolicy} from '"+(ROOT/'adapters/snowluma/project_policy.mjs').as_uri()+"';"
            "let s='';for await(const x of process.stdin)s+=x;const e=JSON.parse(s);"
            "createProjectPolicy({instanceId:e.instance_id,transportEpoch:e.transport_epoch,bot:'222',allowedGroups:['111'],blockedUsers:['999'],identityCurrent:()=>true}).process(e,x=>process.stdout.write(JSON.stringify(x)));")
        wire=json.loads(subprocess.run(['node','--input-type=module','-e',source],input=json.dumps(e).encode(),
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,cwd=ROOT).stdout)
        self.assertEqual(wire['time'],1700000000);self.assertEqual(wire['sender'],{'user_id':'333'})
        self.assertNotIn('PRIVATE_QUOTE',json.dumps(wire))
        out=Capture();await self.g._incoming(frames(wire),out,self.pending)
        row=out.rows[0];self.assertTrue(row.get('qqbot_image'));self.assertEqual(row['time'],1700000000)
        actual=await self.framework_event(row)
        self.assertEqual(actual.message_obj.sender.user_id,'333')
        self.assertIn('fixture-current',actual.message_str)
        self.assertNotIn('get_msg',actual.bot.rpc)
        self.assertTrue(self.router.transport_allowed(actual))

    async def test_actual_router_final_output_expires_before_45s_and_old_event_never_revives(self):
        self.assertTrue(self.ready());row=(await self.inbound(sender={'user_id':'333'},time=1700000000))[0]
        e=await self.framework_event(row)
        self.router.observe_gate()
        self.assertTrue(self.router.delivery_allowed(e))
        await self.router.local_notice(e,'fixture reply')
        self.assertEqual(len(self.down.rows),1)
        self.v.expires=time.monotonic()-1
        # Gate has received no new frame and mirror updated remains <45 seconds old.
        data=json.loads((self.root/'state/gate-connection.json').read_text())
        data['health']['expires_mono']=time.monotonic()-1
        (self.root/'state/gate-connection.json').write_text(json.dumps(data),encoding='utf-8')
        self.assertIsNone(self.router.connection());self.assertFalse(self.router.delivery_allowed(e))
        self.router.observe_gate();self.assertGreater(self.invalidations,0)
        await self.router.local_notice(e,'late model reply');self.assertEqual(len(self.down.rows),1)
        self.g.channel_ready();self.assertTrue(self.ready())
        self.assertFalse(self.router.delivery_allowed(e))
        # Even a direct granted event.send is denied by the authoritative gate ticket.
        with e.get_extra('qq_send_guard').grant():
            from aiocqhttp.exceptions import ActionFailed
            with self.assertRaises(ActionFailed):await e.send(e.plain_result('stale direct'))
        self.assertEqual(len(self.down.rows),1)

    async def test_actual_router_model_hook_and_all_free_windows_reject_expired(self):
        self.assertTrue(self.ready());row=(await self.inbound(sender={'user_id':'333'},time=1700000000))[0]
        e=await self.framework_event(row)
        self.v.expires=time.monotonic()-1;self.g.channel_ready()
        await self.router.before_provider(e,SimpleNamespace())
        self.assertFalse(e.call_llm)
        self.assertFalse(self.router.memory_allowed(e))
        # These actual generator paths must exit before reading/adding RAM context.
        for method in (self.router.on_group,self.router.on_mentions,self.router.on_free_group,self.router.on_attention_group):
            rows=[r async for r in method(e)]
            self.assertFalse(rows)

    async def test_mirror_exact_config_binding_and_configured_ttl30(self):
        self.assertTrue(self.ready());path=self.root/'state/gate-connection.json'
        good=json.loads(path.read_text())
        for change in [dict(provider='napcat'),dict(instance_id='f'*32),dict(config_digest='0'*64),
                       dict(channel_ready=False),dict(health=dict(ready=True,expires_mono=float('nan'),sequence=1)),
                       dict(health=dict(ready=True,expires_mono=time.monotonic()+31,sequence=1))]:
            path.write_text(json.dumps(good|change),encoding='utf-8');self.assertIsNone(self.router.gate_metadata())
        self.router.transport_health_ttl=30
        good['health']['expires_mono']=time.monotonic()+25
        path.write_text(json.dumps(good),encoding='utf-8');self.assertIsNotNone(self.router.gate_metadata())
        self.router.transport_provider='napcat'
        good.pop('health');good['updated']=time.time()-20
        path.write_text(json.dumps(good),encoding='utf-8');self.assertIsNotNone(self.router.gate_metadata())


if __name__=='__main__':unittest.main()
