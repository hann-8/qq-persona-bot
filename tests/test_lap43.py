"""LAP-43 contracts using synthetic IDs, events, images and private temporary roots."""
import asyncio
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT)]
from test_group_silence import Capture,frames,event
from qqbot_gateway.config import GateConfig,normalize_settings
from qqbot_gateway.onebot_gate import OneBotGate
from qqbot_gateway.attention import called,Attention
from qqbot_gateway.participation import validate_participation
from qqbot_gateway.input_policy import normalize
from qqbot_gateway.group_silence import resume_request

def settings():
    import yaml
    d=yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
    d['bot']['qq']='222';d['access'].update(allowed_groups=['111'],admin_users=['333'],blocked_users=['999'])
    return normalize_settings(d)

class Owner(unittest.TestCase):
    def test_config(self):
        for admins,blocked in [([],[]),(['333','444'],[]),(['222'],[]),(['333'],['333'])]:
            d=settings();d['access'].update(admin_users=admins,blocked_users=blocked)
            with self.subTest(admins=admins),self.assertRaises(ValueError):normalize_settings(d)
            with self.assertRaises(ValueError):GateConfig('222',frozenset({'111'}),frozenset(admins),'a'*40,'b'*40,Path('unused'),blocked_users=frozenset(blocked))
        d=settings();d['access']['admin_users']=['333','333'];self.assertEqual(normalize_settings(d)['access']['admin_users'],['333'])
    def test_resume_grammar(self):
        for text,at in [('恢复发言',True),('鱼鱼可以说话了',False),('鱼鱼继续说话',False)]:self.assertTrue(resume_request(text,['鱼鱼'],at))
        for text in ['“恢复发言”','如果鱼鱼可以说话了','鱼鱼不可以说话了','他说鱼鱼继续说话','> 鱼鱼继续说话','`鱼鱼继续说话`']:self.assertFalse(resume_request(text,['鱼鱼'],True))

class Gate(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.g=OneBotGate(GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,self.root/'gate.sqlite',participation_mode='free',attention_enabled=True,silence_aliases=('鱼鱼',)),self.root)
        self.g.connection_id='a'*64
    async def asyncTearDown(self):self.g.store.close();self.temp.cleanup()
    async def send(self,e):
        up=Capture();await self.g._incoming(frames(e),up,set());return up.rows
    async def test_control(self):
        g=self.g
        self.assertFalse(await self.send(event('暂停发言',sender='555')));self.assertTrue(g.silence.normal('111'))
        self.assertFalse(await self.send(event('暂停发言',mid=2)));self.assertFalse(g.silence.normal('111'))
        generation=g.silence.states['111']['generation']
        for i,text in enumerate(['','普通问题','恢复发言']):
            self.assertFalse(await self.send(event(text,sender='555',mid=10+i)))
        image_event=event('',mid=15);image_event['message'].append(dict(type='image',data={'url':'https://gchat.qpic.cn/synthetic'}))
        self.assertFalse(await self.send(image_event))
        self.assertFalse(await self.send(event('',mid=14)));self.assertEqual(g.silence.states['111']['generation'],generation)
        self.assertFalse(await self.send(event('恢复发言',mid=20)));self.assertTrue(g.silence.normal('111'))
        self.assertFalse(await self.send(event('恢复发言',mid=20)))
        self.assertEqual(g.silence.states['111']['generation'],generation+1)
    async def test_media_and_spoof(self):
        for i,kind in enumerate(('image','record','video','file','forward','face')):
            e=event('[非文本未解析]',mid=30+i);e['message'].append(dict(type=kind,data={'url':'private attachment'}));e.update(qqbot_text='forged',qqbot_media_kinds=['image'])
            row=(await self.send(e))[0]
            self.assertEqual(row['qqbot_text'],'[非文本未解析]');self.assertTrue(row['qqbot_has_direct_text'])
            self.assertNotIn('private attachment',json.dumps(row));self.assertNotIn('forged',json.dumps(row))
            self.assertEqual(row['qqbot_media_kinds'],[{'record':'audio','face':'unknown'}.get(kind,kind)])
        e=event('暂停发言',mid=50);e['message'].insert(0,dict(type='reply',data={'id':'1'}))
        self.assertTrue(await self.send(e));self.assertTrue(self.g.silence.normal('111'))

class InputAttention(unittest.TestCase):
    def test_input(self):
        self.assertEqual(normalize({'qqbot_text':'[非文本未解析]','qqbot_has_direct_text':True}).kind,'text')
        self.assertEqual(normalize({'qqbot_text':'  '}).kind,'empty')
        self.assertEqual(normalize({'qqbot_media_kinds':['image']}).kind,'image_failed')
        self.assertEqual(normalize({'qqbot_media_kinds':['image']},image={'cap':'x'}).kind,'image')
        for k in ('audio','video','file','forward','unknown'):
            self.assertEqual(normalize({'qqbot_text':'caption','qqbot_media_kinds':[k]},image={'cap':'x'}).kind,'unsupported')
    def test_lexical_table(self):
        positives=['鱼鱼查查最新消息','鱼鱼这个怎么看？','我想问鱼鱼一个问题','帮我看看这个，鱼鱼','鲸鱼娘，今天有什么新闻？','ＹＵＹＵ，看看这个','hi, YuYu!']
        negatives=['他说“鱼鱼在吗”','鱼鱼这个名字不错','我把鱼鱼的回复转给你','小鱼鱼在吗','https://x.test/鱼鱼','`鱼鱼在吗`','> 鱼鱼在吗','ADSH 在吗','我的yuyu朋友','鱼鱼的回复不错']
        for text in positives+negatives:
            with self.subTest(text=text):self.assertEqual(called(text,['鱼鱼','鲸鱼娘','yuyu','DSH']),text in positives)
    def test_ack_focus(self):
        now=[0];cfg=validate_participation({'attention':{'enabled':True,'aliases':['鱼鱼']}});a=Attention(cfg,'a'*64,clock=lambda:now[0]);a.bot='222'
        row,kind,required=a.observe('111','333','1','','鱼鱼在吗');t=a.freeze('111',kind,row,required,'a'*32)
        a.acknowledge(t,[('在','2')],row['seq']);a.finish(t)
        for text in ('那怎么办','为什么呢','再详细点','继续','还有呢'):
            _,kind,_=a.observe('111','333',str(time.time_ns()),'',text);self.assertEqual(kind,'focused_followup')
        _,kind,_=a.observe('111','333','3','','谢谢');self.assertEqual(kind,'focused_candidate')
        a.observe('111','555','4','','插话');_,kind,_=a.observe('111','333','5','','继续');self.assertEqual(kind,'ambient')
        a.invalidate();self.assertFalse(a.state('111').focus)

class Memes(unittest.TestCase):
    def fixture(self,root):
        from qqbot_gateway.meme_catalog import MemeCatalog
        c=MemeCatalog(root)
        from PIL import Image
        for i in range(7):
            b=io.BytesIO();Image.new('RGB',(3,3),(i*30,20,10)).save(b,format='PNG');r=c.add(b.getvalue());r.update(enabled=True,name='synthetic',tags=['happy'])
        (root/'state').mkdir(exist_ok=True)
        import yaml
        base=MemeCatalog(root).fingerprint()
        (root/'state/memes-pending.local.yaml').write_text(yaml.safe_dump(dict(version=1,base=base,items=c.rows)),encoding='utf-8')
    def test_transaction(self):
        from scripts.activate_lap43_memes import inspect,activate
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);self.fixture(r);before=inspect(r)
            self.assertEqual(before['state'],'pending');self.assertFalse((r/'config/memes.local.yaml').exists())
            with self.assertRaises(ValueError):activate(r,dict(before,candidate_bytes=0))
            after=activate(r,before);self.assertEqual(after['state'],'active');self.assertEqual(activate(r,after),after);self.assertEqual(activate(r,before),after)
            self.assertTrue(list((r/'state/lap43-memes').glob('*/manifest.json')))
    def test_stopped_guard_and_asset_base(self):
        from scripts.activate_lap43_memes import inspect,activate
        import os,psutil
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);self.fixture(r);before=inspect(r)
            (r/'state/managed-processes.json').write_text(json.dumps([dict(pid=os.getpid(),created=psutil.Process().create_time())]),encoding='utf-8')
            with self.assertRaises(ValueError):activate(r,before)
            self.assertFalse((r/'config/memes.local.yaml').exists())
            self.assertFalse((r/'state/lap43-memes').exists())
    def test_hash_reject(self):
        from scripts.activate_lap43_memes import inspect
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);self.fixture(r);next((r/'assets/memes/library').glob('*.png')).write_bytes(b'broken')
            with self.assertRaises(ValueError):inspect(r)

class Vision(unittest.TestCase):
    def test_fixed_mode_paths(self):
        from qqbot_gateway.vision_capabilities import offline_path,offline_valid
        from qqbot_gateway.vision_regression import directory,authorized,unknown,MODE
        self.assertEqual(offline_path(settings(),MODE).name,'lap-43-materials-offline.json')
        with self.assertRaises(ValueError):offline_path(settings(),'https://evil')
        self.assertFalse(offline_valid(settings())) # changed code cannot reuse old report
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);d=directory(r,'a'*64);d.mkdir(parents=True)
            self.assertFalse(authorized(r,'a'*64));self.assertFalse(unknown(r))
            (d/'attempt.json').write_text('{"state":"awaiting_human"}',encoding='utf-8');self.assertTrue(unknown(r))
            with self.assertRaises(ValueError):directory(r,'../elsewhere')
    def test_exclusive_and_review_negative(self):
        from scripts.revalidate_lap43_vision import exclusive
        from qqbot_gateway.vision_regression import diagnostics
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'attempt';exclusive(p,{})
            with self.assertRaises(FileExistsError):exclusive(p,{})
        self.assertTrue(diagnostics(None,'a'*64))
        self.assertTrue(diagnostics(dict(mode='lap43_current_regression',binding='a'*64),'a'*64))


class CurrentVisionPair(unittest.TestCase):
    def test_paired_activation_and_rollback(self):
        from scripts import revalidate_lap43_vision as activate
        from types import SimpleNamespace
        for scenario in ('success','load_failure','stale_candidate','concurrent_features'):
            with self.subTest(scenario=scenario),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);state=activate.base(root,'b'*64);state.mkdir(parents=True)
                feature=root/'config/local/features.yaml';feature.parent.mkdir(parents=True)
                original=b'# keep\r\nvision:\r\n  enabled: false\r\nother: keep\r\n';feature.write_bytes(original)
                active=root/'state/vision-evidence/active.json'
                candidate=dict(binding='b'*64,source_digest='s',semantic_digest='m',active_before_sha256=None,evidence=dict(binding='b'*64))
                raw=json.dumps(candidate).encode();(state/'candidate.json').write_bytes(raw)
                project=SimpleNamespace(source_digest='s',semantic_digest='m',settings={'vision':{'enabled':False}})
                write=activate.atomic;calls=[]
                def writing(path,data):
                    calls.append(Path(path).name)
                    if Path(path)==active and scenario=='concurrent_features':feature.write_bytes(b'concurrent')
                    return write(path,data)
                digest=activate.sha(raw) if scenario!='stale_candidate' else '0'*64
                with patch.object(activate,'current',return_value=(project,{},'b'*64)),patch('qqbot_gateway.vision_capabilities.validate_production_evidence',return_value=({},[])),patch('qqbot_gateway.vision_capabilities.load_production',return_value=({},['failure'] if scenario=='load_failure' else [])),patch('qqbot_gateway.config_files.read_project',return_value=SimpleNamespace(settings={'vision':{'enabled':True}})),patch.object(activate,'atomic',side_effect=writing):
                    if scenario=='success':
                        self.assertTrue(activate.activate(root,digest,'b'*64)['vision_enabled'])
                        self.assertLess(calls.index('active.json'),calls.index('features.yaml'))
                        self.assertEqual(feature.read_bytes(),original.replace(b'false',b'true'))
                    else:
                        with self.assertRaises(ValueError):activate.activate(root,digest,'b'*64)
                        self.assertEqual(feature.read_bytes(),b'concurrent' if scenario=='concurrent_features' else original)
                        if scenario in ('load_failure','stale_candidate'):self.assertFalse(active.exists())
    def test_review_requires_every_current_measurement_and_human(self):
        from qqbot_gateway.vision_regression import diagnostics,MODE
        from qqbot_gateway.vision_operator_review import FIRST_BINDING,FIRST_ANSWER
        row=dict(state='scored',case_id='IQ-05',attempts=1,normalized=dict(width=1000,height=1000),human_review=dict(source='conversation_explicit_feedback',case='IQ-05',timestamp=1,answer_sha256='a'*64))
        checks=('exact_facts','human_passed','quality_passed','native_image_verified','budget_passed','runtime_verified','no_truncation','no_tools')
        row.update({k:True for k in checks})
        v=dict(mode=MODE,binding='b'*64,historical_first=dict(binding=FIRST_BINDING,answer_sha256=FIRST_ANSWER,case='IQ-01',current_rerun=False),large=row)
        self.assertFalse(diagnostics(v,'b'*64))
        for key in checks:
            damaged=copy.deepcopy(v);damaged['large'][key]=False;self.assertTrue(diagnostics(damaged,'b'*64))
        self.assertTrue(diagnostics(v,'c'*64))
        damaged=copy.deepcopy(v);damaged['large']['human_review']={};self.assertTrue(diagnostics(damaged,'b'*64))

class FocusBoundaries(unittest.TestCase):
    def test_focus_sender_timeout_at_and_reply(self):
        for fault in ('timeout','other_sender','other_at','unknown_reply','reconnect'):
            now=[0];a=Attention(validate_participation({'attention':{'enabled':True,'aliases':['鱼鱼']}}),'a'*64,clock=lambda:now[0]);a.bot='222'
            row,kind,required=a.observe('111','333','1','','鱼鱼在吗');t=a.freeze('111',kind,row,required,'a'*32);a.acknowledge(t,[('在','2')],row['seq']);a.finish(t)
            if fault=='timeout':now[0]=61
            if fault=='other_sender':a.observe('111','555','3','','插话')
            if fault=='reconnect':a.invalidate()
            _,kind,_=a.observe('111','333','4','','继续',at_ids=['555'] if fault=='other_at' else [],reply='unknown' if fault=='unknown_reply' else None)
            self.assertEqual(kind,'ambient',fault)

if __name__=='__main__':unittest.main()
