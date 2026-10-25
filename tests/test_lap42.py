"""Snow integration: project boundaries with synthetic bottom transports."""
import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT)]
from qqbot_gateway.members import Members,DEFAULTS,CountObservation,count_proof,suspend_unverified
from qqbot_gateway.onebot_gate import OneBotGate,echo_key
from qqbot_gateway.config import GateConfig,load_gate_config


class ObservationTests(unittest.IsolatedAsyncioTestCase):
    async def test_large_invalid_and_rpc_failure_pause_until_ttl_or_notice(self):
        now=[100.];calls=[]
        for failure in (False,True):
            m=Members(DEFAULTS|dict(enabled=True),clock=lambda:now[0]);calls.clear()
            async def rpc(action,params):
                calls.append(action)
                if failure:raise ConnectionError('fixture')
                return CountObservation('111',50,now[0]-.1,now[0],'c')
            if failure:
                with self.assertRaises(ConnectionError):await m.roster('111',rpc)
            else:self.assertIsNone(await m.roster('111',rpc))
            self.assertIsNone(await m.roster('111',rpc));self.assertEqual(calls,['get_group_info'])
            m.invalidate('111');self.assertFalse(m.pauses)

    async def test_gate_force_scope_wrong_group_count_error_disconnect_late(self):
        for case in ('ok','wrong_group','boolean','zero','fifty','retcode','disconnect','late'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as directory:
                gate=OneBotGate(GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,
                    Path(directory)/'db',transport_provider='snowluma',members_enabled=True))
                gate.channel_ready=lambda:True;calls=[]
                async def send(value):
                    calls.append(value)
                    if case=='disconnect':gate.connection_id='new'
                    gate.admin_pending[echo_key(value['echo'])].set_result(dict(status='ok',retcode=1 if case=='retcode' else 0,
                        data=dict(group_id=999 if case=='wrong_group' else 111,member_count={'boolean':True,'zero':0,'fifty':50}.get(case,3),fresh=True,observed_at=0)))
                gate.active=SimpleNamespace(send_json=send)
                try:
                    if case=='ok':
                        before=time.monotonic();result=await gate.member_rpc('get_group_info',dict(group_id=111,no_cache=True))
                        self.assertIsInstance(result,CountObservation);self.assertEqual(result.group,'111')
                        self.assertEqual(result.connection,gate.connection_id);self.assertLessEqual(before,result.started)
                        self.assertLessEqual(result.started,result.completed);self.assertLessEqual(result.completed,time.monotonic())
                        for params in (dict(group_id=999,no_cache=True),dict(group_id=111),dict(group_id=111,no_cache=False)):
                            with self.assertRaises(ValueError):await gate.member_rpc('get_group_info',params)
                    elif case=='late':
                        real=time.monotonic
                        ticks=iter((100.,104.))
                        # Patch only the gate's clock, leaving asyncio's clock intact.
                        with patch('qqbot_gateway.onebot_gate.time',SimpleNamespace(monotonic=lambda:next(ticks))):
                            with self.assertRaises(ValueError):await gate.member_rpc('get_group_info',dict(group_id=111,no_cache=True))
                    else:
                        with self.assertRaises(ValueError):await gate.member_rpc('get_group_info',dict(group_id=111,no_cache=True))
                    self.assertEqual(len(calls),1);self.assertEqual(calls[0]['params'],dict(group_id=111,no_cache=True))
                    self.assertFalse(gate.admin_pending)
                finally:gate.store.close()

    async def test_json_not_proof_conservative_age_double_ttl_no_repeated_roster(self):
        now=[100.];calls=[];m=Members(DEFAULTS|dict(enabled=True),clock=lambda:now[0])
        async def fake(action,params):return dict(group_id=111,member_count=2,fresh=True,observed_at=100,received_at=100)
        self.assertIsNone(await m.roster('111',fake))
        m.invalidate('111')
        for o in (CountObservation('999',2,99,100,'c'),CountObservation('111',2,39,100,'c'),CountObservation('111',2,101,102,'c')):
            self.assertIsNone(count_proof(o,'111',lambda:100.))
        self.assertEqual(count_proof(CountObservation('111',2,97,99,'c'),'111',lambda:100.)['age'],3)
        async def rpc(action,params):
            calls.append((action,params))
            if action=='get_group_info':return CountObservation('111',2,now[0]-.2,now[0],'c')
            return [dict(group_id=111,user_id=u,card='test'+str(u),nickname='') for u in (222,333)]
        first=await m.roster('111',rpc);self.assertIs(await m.roster('111',rpc),first)
        now[0]+=61;self.assertIs(await m.roster('111',rpc),first)
        self.assertEqual([a for a,_ in calls],['get_group_info','get_group_member_list','get_group_info'])
        self.assertTrue(all(p['no_cache'] is True for _,p in calls))
        now[0]+=301;self.assertIsNot(await m.roster('111',rpc),first)
        m.clear();self.assertFalse(m.counts);self.assertFalse(m.rosters)

    async def test_cli_low_actual_runner_same_image_hash_and_return(self):
        from test_cli_runner import RunnerTests
        from PIL import Image
        from qqbot_gateway.vision import CURRENT,NativeImage,normalize
        for fmt in ('JPEG','PNG','WEBP','GIF'):
            with self.subTest(format=fmt):
                f=RunnerTests();f.setUp()
                try:
                    raw=io.BytesIO();Image.new('RGB',(12,8),'red').save(raw,format=fmt);blob=normalize(raw.getvalue())
                    runner=f.runner(effort='low');token=CURRENT.set(NativeImage(blob,4096,time.monotonic()+60,time.monotonic()+15))
                    try:result=await runner.run('policy','current image','lap42-pixels')
                    finally:CURRENT.reset(token)
                    source=json.loads((f.root/'user.json').read_text())['message']['content'][1]['source']
                    self.assertEqual(source['media_type'],blob.mime)
                    self.assertEqual(hashlib.sha256(base64.b64decode(source['data'])).hexdigest(),blob.sha256)
                    self.assertEqual((runner.attempts,runner.user_messages_sent),(1,1));self.assertEqual(result.text,'answer')
                    args=json.loads((f.root/'argv.json').read_text())['argv'];self.assertEqual(args[args.index('--effort')+1],'low')
                finally:f.tearDown()


class EffectiveTests(unittest.TestCase):
    def test_field_patch_preserves_bom_crlf_comments_other_values(self):
        from scripts.lap42_rollout import patch_fields
        raw=b'\xef\xbb\xbfmemory:  # keep\r\n  enabled: false # keep\r\n  learning_enabled: false\r\nother: unchanged\r\n'
        actual=patch_fields(raw,{('memory','enabled'):True})
        self.assertEqual(actual,raw.replace(b'enabled: false #',b'enabled: true #'))
        with self.assertRaises(ValueError):patch_fields(raw,{('unknown','enabled'):True})

    def test_known_snow_unknown_and_napcat(self):
        s=dict(members=DEFAULTS|dict(enabled=True,mentions_enabled=True),qq_transport=dict(provider='snowluma'))
        self.assertTrue(suspend_unverified(s)['enabled'])
        s['qq_transport']['snowluma']=dict(runtime_root='runtime/snowluma/unknown');self.assertFalse(suspend_unverified(s)['enabled'])
        s['qq_transport']=dict(provider='napcat');self.assertFalse(suspend_unverified(s)['enabled'])

    def test_members_only_token_uniqueness_in_loader_and_gate(self):
        import yaml
        from qqbot_gateway.config import normalize_settings
        s=yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
        s['bot']['qq']='222';s['access'].update(allowed_groups=['111'],admin_users=['333']);s=normalize_settings(s)
        s['members']=DEFAULTS|dict(enabled=True,mentions_enabled=True);s['qq_transport']=dict(provider='snowluma')
        with tempfile.TemporaryDirectory() as directory,patch('qqbot_gateway.members.snow_source',return_value=True):
            root=Path(directory);(root/'secrets').mkdir()
            (root/s['secrets_file']).write_text(json.dumps(dict(onebot_inbound='a'*64,onebot_upstream='b'*64,model_gateway='d'*64)))
            with patch('qqbot_gateway.vision.context_token',return_value='a'*64):
                with self.assertRaisesRegex(ValueError,'Independent context'):load_gate_config(root=root,settings=s)
            with patch('qqbot_gateway.vision.context_token',return_value='c'*64):
                cfg=load_gate_config(root=root,settings=s);self.assertTrue(cfg.members_enabled)
                gate=OneBotGate(cfg,root=root);self.assertEqual(gate.context_token,'c'*64);gate.store.close()
            with patch('qqbot_gateway.vision.context_token',return_value='b'*64):
                with self.assertRaisesRegex(ValueError,'Independent context'):OneBotGate(cfg,root=root)

if __name__=='__main__':unittest.main()
