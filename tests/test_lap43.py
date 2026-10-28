"""LAP-43 admission, final sending fence, current-input facts and attention contracts."""
import asyncio
from dataclasses import replace
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT)]
from qqbot_gateway.attention import Attention,called
from qqbot_gateway.config import GateConfig
from qqbot_gateway.onebot_gate import OneBotGate
from qqbot_gateway.participation import validate_participation
from qqbot_gateway.input_policy import facts,notice
from qqbot_gateway.group_silence import resume_request
from test_group_silence import event,Capture,Duplex,frames


class Contracts(unittest.TestCase):
    def test_name_boundaries_and_current_material(self):
        names=['鱼鱼','鲸鱼娘','DSH']
        for text in ('鱼鱼查查最新消息','鱼鱼这个怎么看？','我想问鱼鱼一个问题','帮我看看这个，鱼鱼','ＤＳＨ，帮我看看','dsh?', '鱼鱼在吗'):
            with self.subTest(text=text):self.assertTrue(called(text,names))
        for text in ('鱼鱼这个名字不错','我把鱼鱼的回复转给你','他说“鱼鱼在吗”','`鱼鱼查查最新消息`','https://example.org/鱼鱼','> 鱼鱼你好','ADSHE你好','鱼鱼的粉丝你好'):
            with self.subTest(text=text):self.assertFalse(called(text,names))

    def test_ack_focus_and_interruption(self):
        now=[1.];cfg=validate_participation(dict(mode='free',attention=dict(enabled=True)))
        att=Attention(cfg,'epoch',clock=lambda:now[0]);att.bot='222'
        row,kind,req=att.observe('111','333','1','甲','你好',['222'])
        ticket=att.freeze('111',kind,row,req,'a'*32)
        att.acknowledge(ticket,[('好呀','ack-1')],row['seq']);att.finish(ticket)
        self.assertEqual(att.observe('111','333','2','甲','那怎么办')[1],'focused_followup')
        att.observe('111','555','3','乙','插话')
        self.assertNotEqual(att.observe('111','333','4','甲','继续')[1],'focused_followup')

    def test_facts_do_not_erase_literal_text(self):
        result=facts([dict(type='text',data=dict(text='[非文本未解析]')),dict(type='video',data={})])
        self.assertTrue(result['has_direct_text']);self.assertEqual(result['media_types'],['video'])
        self.assertIn('视频',notice(result['media_types'],False,True))
        self.assertEqual(notice([],False,False),'我在～')
        self.assertIn('图片',notice(['image'],False,True))
        self.assertIsNone(notice(['image'],True,False))

    def test_single_operator_and_exact_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            base=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,Path(folder)/'db')
            for owners,blocked in [(frozenset(),frozenset()),(frozenset({'333','555'}),frozenset()),(frozenset({'222'}),frozenset()),(frozenset({'333'}),frozenset({'333'}))]:
                with self.assertRaises(ValueError):replace(base,admin_users=owners,blocked_users=blocked)
        for text in ('恢复发言','鱼鱼可以说话了','鱼鱼继续说话'):
            self.assertTrue(resume_request(text,['鱼鱼'],text=='恢复发言'))
        for text in ('你好','鱼鱼不要恢复发言','如果鱼鱼恢复发言','“恢复发言”','> 恢复发言'):
            self.assertFalse(resume_request(text,['鱼鱼'],True))

    def test_trial_authorization_does_not_claim_quality_or_shrink_binding(self):
        from copy import deepcopy
        from qqbot_gateway.vision_trial import diagnostics,durable_diagnostics
        bound='b'*64;runtime={'artifact_sha256':'c'*64};record='d'*64
        value=dict(binding=bound,runtime=runtime,record_hash=record,authorized_at='2026-10-28T14:00:00+00:00',
            authorization_source='operator_submitted_prompt',quality_state='pending_user_test',
            previous_active_sha256='a'*64,technical_report_sha256='e'*64)
        self.assertFalse(diagnostics(value,bound,runtime,record))
        for key,new in [('binding','f'*64),('runtime',{}),('quality_state','passed'),('authorization_source','model')]:
            changed=deepcopy(value);changed[key]=new
            self.assertTrue(diagnostics(changed,bound,runtime,record))
        with tempfile.TemporaryDirectory() as folder:
            self.assertTrue(durable_diagnostics(Path(folder),dict(binding=bound,operator_trial=value),{}))


class GateContracts(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,self.root/'db',participation_mode='free')
        self.g=OneBotGate(cfg,self.root);self.g.connected=True;self.g.online=True
        self.up=Capture();self.down=Capture();self.pending=set();self.mid=0
    async def asyncTearDown(self):self.g.store.close();self.tmp.cleanup()
    async def incoming(self,text,sender='333',extra=()):
        self.mid+=1;row=event(text,True,self.mid,sender=sender);row['message'].extend(extra)
        before=len(self.up.rows);await self.g._incoming(frames(row),self.up,self.pending)
        return self.up.rows[before:]
    async def test_owner_only_pause_explicit_resume_stale_send(self):
        ticket=(await self.incoming('问题'))[0]['qqbot_output_ticket']
        self.assertFalse(await self.incoming('暂停发言','555'));self.assertTrue(self.g.silence.normal('111'))
        self.assertFalse(await self.incoming('暂停发言'));self.assertFalse(self.g.silence.normal('111'))
        generation=self.g.silence.states['111']['generation']
        for sender in ('333','555'):
            self.assertFalse(await self.incoming('',sender))
            self.assertFalse(await self.incoming('新问题',sender,[dict(type='image',data=dict(url='https://example.org/image'))]))
        self.assertFalse(await self.incoming('恢复发言','555'));self.assertFalse(self.g.silence.normal('111'))
        self.assertEqual(self.g.silence.states['111']['generation'],generation)
        self.assertFalse(await self.incoming('恢复发言'));self.assertTrue(self.g.silence.normal('111'))
        request=dict(action='send_group_msg',params=dict(group_id='111',message=[dict(type='text',data=dict(text='旧回复'))],qqbot_output_ticket=ticket),echo='old')
        await self.g._outgoing(Duplex(frames(request),self.up),self.down,self.pending)
        self.assertFalse(self.down.rows)
        self.assertTrue(await self.incoming('新问题','555'))
    async def test_gate_fact_binding_and_media_control_not_executed(self):
        row=(await self.incoming('[非文本未解析]',extra=[dict(type='video',data={})]))[0]
        self.assertEqual(row['qqbot_input']['media_types'],['video'])
        self.assertEqual(row['qqbot_input']['text'],'[非文本未解析]')
        self.assertTrue(await self.incoming('暂停发言',extra=[dict(type='image',data={})]))
        self.assertTrue(self.g.silence.normal('111'))


class MemeActivation(unittest.TestCase):
    def test_digest_lock_backup_and_changed_asset_rejection(self):
        import io
        import yaml
        from PIL import Image
        from scripts.activate_lap43_memes import inspect,activate
        from qqbot_gateway.meme_catalog import MemeCatalog
        from test_config_files import synthetic
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'config').mkdir()
            data=synthetic();data['memes']['enabled']=True
            (root/'config/settings.local.yaml').write_text(yaml.safe_dump(data),encoding='utf-8')
            c=MemeCatalog(root,data['memes'])
            for n in range(7):
                out=io.BytesIO();Image.new('RGB',(2,2),(n*30,0,0)).save(out,format='PNG')
                row=c.add(out.getvalue());row.update(name='合成'+str(n),context='测试',tags=['开心'],enabled=True)
            c.stage();before=inspect(root)
            with patch('qqbot_gateway.config.require_stopped',side_effect=ValueError('running')):
                with self.assertRaises(ValueError):activate(root,before)
            self.assertTrue((root/'state/memes-pending.local.yaml').exists())
            result=activate(root,before);self.assertEqual(result['state'],'activated')
            self.assertEqual(activate(root,inspect(root))['state'],'already_active')
            backup=root/'state/lap43-memes'/before['pending_sha256']
            self.assertTrue((backup/'pending.before').exists())
            path,_=MemeCatalog(root,data['memes']).resolve(c.rows[0]['id']);path.write_bytes(b'changed')
            with self.assertRaises(ValueError):inspect(root)


class FrameworkContracts(unittest.IsolatedAsyncioTestCase):
    async def test_actual_astrbot_empty_media_reset_and_muted_fence(self):
        if not os.environ.get('QQBOT_TEST_ASTRBOT_SITE'):self.skipTest('actual AstrBot site supplied by current verifier')
        from types import SimpleNamespace
        import test_transport_router as fixture
        from qqbot_gateway.task_store import TaskStore
        fixture.RouterTests.setUpClass()
        f=fixture.RouterTests('test_actual_js_gate_astrbot_parser_time_sender_image_and_no_reply_fetch')
        await f.asyncSetUp();tasks=None
        try:
            self.assertTrue(f.ready());r=f.router
            f.g.config=replace(f.g.config,silence_enabled=True,participation_mode='free')
            f.g.silence.enabled=True
            f.g.publish_connection()
            r.participation=validate_participation(dict(mode='free',attention=dict(enabled=True,aliases=['鱼鱼'])))
            r.attention_effective=True;r.vision=dict(enabled=True);r.members=dict(enabled=False)
            r.group_turns=Attention(r.participation,'epoch');r.group_turns.bot='222'
            tasks=r.tasks=TaskStore(f.root/'tasks.sqlite3')
            async def incoming(text,sender='333',extra=()):
                f.mid+=1;e=event(text,True,mid=f.mid,sender=sender);e['sender']=dict(user_id=sender);e['time']=1700000000;e['message'].extend(extra)
                out=Capture();await f.g._incoming(frames(e),out,f.pending)
                return out.rows
            for text,extra,expected in [('',[],'我在'),('',[dict(type='video',data={})],'视频'),('[非文本未解析]',[dict(type='record',data={})],'语音')]:
                row=(await incoming(text,extra=extra))[0];e=await f.framework_event(row)
                outputs=[v async for v in r.on_attention_group(e)]
                self.assertFalse(outputs);self.assertEqual(len(e.bot.sent),1)
                self.assertIn(expected,json.dumps(e.bot.sent,ensure_ascii=False))
            # A nonowner cannot reset the actual router RAM; owner's explicit command can.
            row=(await incoming('重置本群上下文','555'))[0];e=await f.framework_event(row)
            e.set_extra('qq_delivery_identity',('222','111','555'))
            epoch=r.group_turns.group_epoch('111');[v async for v in r.on_attention_group(e)]
            self.assertEqual(r.group_turns.group_epoch('111'),epoch)
            row=(await incoming('重置本群上下文'))[0];e=await f.framework_event(row)
            [v async for v in r.on_attention_group(e)]
            self.assertNotEqual(r.group_turns.group_epoch('111'),epoch)
            self.assertFalse(await incoming('暂停发言'))
            before=len(f.down.rows);await r.local_notice(e,'不能绕过暂停')
            self.assertEqual(len(f.down.rows),before)
            self.assertFalse(await incoming(''))
            self.assertFalse(await incoming('恢复发言','555'))
            self.assertFalse(f.g.silence.normal('111'))
            self.assertFalse(await incoming('恢复发言'));self.assertTrue(f.g.silence.normal('111'))
        finally:
            if tasks:tasks.db.close()
            await f.asyncTearDown();fixture.RouterTests.tearDownClass()


if __name__=='__main__':unittest.main()
