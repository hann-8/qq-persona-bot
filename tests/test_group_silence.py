"""SM-01..11 synthetic gate/state/transport contracts; no live services."""
import asyncio
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import aiohttp
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from qqbot_gateway.group_silence import GroupSilence,silence_request,decode_ticket,DENIED
from qqbot_gateway.config import GateConfig
from qqbot_gateway.onebot_gate import OneBotGate
from qqbot_gateway.participation import validate_participation,ATTENTION_DEFAULTS

ALIASES=ATTENTION_DEFAULTS['aliases']
def event(text='你好',at=True,mid=1,group='111',sender='333'):
    return dict(post_type='message',message_type='group',self_id='222',user_id=sender,group_id=group,message_id=mid,
                message=([dict(type='at',data={'qq':'222'})] if at else [])+[dict(type='text',data={'text':text})])
class Capture:
    def __init__(self):self.rows=[]
    async def send_json(self,value):self.rows.append(copy.deepcopy(value))
    async def send_str(self,value):self.rows.append(json.loads(value))
class Duplex(Capture):
    def __init__(self,source,sink):super().__init__();self.source=source;self.sink=sink
    def __aiter__(self):return self.source
    async def send_json(self,value):await self.sink.send_json(value)

async def frames(*values):
    for value in values:yield SimpleNamespace(type=aiohttp.WSMsgType.TEXT,data=json.dumps(value))

class Recognition(unittest.TestCase):
    def test_positive(self):
        for text in ['不要让肥鱼参与讨论了','肥鱼先别插话了','大肥鱼这会儿别掺和','能不能让肥鱼先安静一下',
                     '肥鱼闭嘴','肥鱼先别参与这段讨论','肥鱼，这段讨论你先别参与了','肥鱼能不能先别说话吗',
                     '麻烦肥鱼安静一下','DSH 请不要发言','肥鱼可以先安静一下吗','先别叫肥鱼参与讨论了']:
            with self.subTest(text=text):self.assertTrue(silence_request(text,ALIASES))
        self.assertTrue(silence_request('请先不要说话',ALIASES,True))
    def test_negative(self):
        for text in ['不要让肥鱼闭嘴','肥鱼别不说话','肥鱼不是不让你说话','不用阻止肥鱼参与','为什么不让肥鱼说话？',
                     '肥鱼为什么不说话？','你先别说了','“肥鱼闭嘴”这句话不礼貌','有人说肥鱼别参与',
                     '如果有人说不要让肥鱼参与就闭嘴','举例：肥鱼别说话','`肥鱼闭嘴`','```\n肥鱼闭嘴\n```',
                     '> 肥鱼闭嘴','ADSHE别说话','肥鱼不可以闭嘴','肥鱼别让别人闭嘴','肥鱼别说话'+'哈'*2000]:
            with self.subTest(text=text):self.assertFalse(silence_request(text,ALIASES))
        self.assertFalse(silence_request('“别说话”',ALIASES,True))
    def test_config(self):
        self.assertEqual(validate_participation({})['silence'],{'enabled':True})
        for value in [None,False,{'enabled':1},{'enabled':'true'},{'muted':True}]:
            with self.assertRaises(ValueError):validate_participation({'silence':value})
        self.assertFalse(validate_participation({'silence':{'enabled':False}})['silence']['enabled'])
    def test_ticket_contract(self):
        now=[10];g=GroupSilence('222',['111','444'],['999'],clock=lambda:now[0],ttl=5)
        e=event();t=g.issue(e,'a'*64);self.assertEqual(g.verify(t,'111','a'*64)['generation'],0)
        for ticket,group,connection in [(None,'111','a'*64),(t+'x','111','a'*64),(t,'444','a'*64),(t,'111','b'*64)]:
            with self.assertRaises(ValueError):g.verify(ticket,group,connection)
        g.control('111',True,True);self.assertFalse(g.normal('111'));self.assertTrue(g.normal('444'))
        g.control('111',True,True);self.assertEqual(g.states['111']['generation'],1)
        g.control('111',False,True);self.assertEqual(g.states['111']['generation'],2)
        with self.assertRaises(ValueError):g.verify(t,'111','a'*64)
        fresh=g.issue(e,'a'*64);now[0]=16
        with self.assertRaises(ValueError):g.verify(fresh,'111','a'*64)
        other=GroupSilence('222',['111']);self.assertTrue(other.normal('111'))
        with self.assertRaises(ValueError):other.verify(t,'111','a'*64)
        self.assertNotIn('111',json.dumps(g.mirror()))

class Compatibility(unittest.TestCase):
    def test_session_persona_and_layout_feature_exports(self):
        import yaml
        from qqbot_gateway.config import normalize_settings,export_legacy_config
        from qqbot_gateway.config_files import read_project
        from qqbot_gateway.config_layout_ops import initialize,export_legacy,rollback_layout
        from qqbot_gateway.persona import compose_persona,session_version
        root_repo=Path(__file__).resolve().parents[1]
        data=yaml.safe_load((root_repo/'config/settings.example.yaml').read_text(encoding='utf-8'))
        data['bot']['qq']='222';data['access'].update(allowed_groups=['111'],admin_users=['333'],blocked_users=[])
        a=normalize_settings(data);b=copy.deepcopy(a);b['participation']['silence']['enabled']=False
        persona=lambda d:compose_persona('合成人设',d['output'],d['web'],d['participation'],d['memes'],d['vision'],d['members'],d['memory'])
        self.assertEqual(persona(a),persona(b));self.assertEqual(session_version(persona(a),a),session_version(persona(b),b))
        self.assertNotIn('silence',persona(a))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir();path=root/'config/settings.local.yaml'
            path.write_text(yaml.safe_dump(data),encoding='utf-8');before=read_project(root).settings
            initialize(root,migrate=True);self.assertEqual(read_project(root).settings,before)
            exported=export_legacy(root);full=yaml.safe_load(Path(exported['export']).read_text(encoding='utf-8'))
            self.assertTrue(full['participation']['silence']['enabled'])
            rollback_layout(root,exported['export'],exported['source_digest'],exported['export_digest'],'已核对')
            feature=export_legacy_config(path);old=yaml.safe_load(Path(feature['review']).read_text(encoding='utf-8'))
            self.assertNotIn('silence',old['participation']);self.assertNotIn('attention',old['participation'])
            self.assertTrue(read_project(root).settings['participation']['silence']['enabled'])
    def test_signed_closed_payload_types(self):
        import base64,hmac
        g=GroupSilence('222',['111']);ticket=g.issue(event(),'a'*64);d,_,_=decode_ticket(ticket)
        for patch_value in [dict(generation=True),dict(expires_ms=False),dict(v=True),dict(group=111),dict(sender='999'),dict(nonce='x'*32),dict(extra=1)]:
            bad=dict(d,**patch_value)
            body=base64.urlsafe_b64encode(json.dumps(bad,sort_keys=True,separators=(',',':')).encode()).decode().rstrip('=')
            sig=base64.urlsafe_b64encode(hmac.digest(g.secret,body.encode(),'sha256')).decode().rstrip('=')
            if patch_value==dict(sender='999'):
                # A valid different nonblocked sender is legal at gate; blocked is not.
                g.blocked=frozenset({'999'})
            with self.assertRaises(ValueError):g.verify(body+'.'+sig,'111','a'*64)

class LocalQueue(unittest.IsolatedAsyncioTestCase):
    async def test_waiting_session_invalidates_without_canceling_owner_or_other_group(self):
        from qqbot_gateway.session_queue import SessionCoordinator,SessionError
        c=SessionCoordinator(cooldown=0);owner=await c.acquire('A');live=[True]
        waiting=asyncio.create_task(c.acquire('A',lambda:live[0]));other=await c.acquire('B')
        await asyncio.sleep(.01);live[0]=False
        with self.assertRaises(SessionError) as caught:await waiting
        self.assertEqual(caught.exception.code,'INVALIDATED');self.assertTrue(c.states['A'].busy)
        other.release();owner.release();self.assertFalse(c.states['A'].busy)
        next_owner=await c.acquire('A');next_owner.release()

class GateTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.cfg=GateConfig('222',frozenset({'111','444'}),frozenset({'333'}),'a'*40,'b'*40,self.root/'db',blocked_users=frozenset({'999'}))
        self.g=OneBotGate(self.cfg,self.root);self.g.connected=True;self.g.online=True
        self.up=Capture();self.down=Capture();self.pending=set();self.mid=0
    async def asyncTearDown(self):self.g.store.close();self.tmp.cleanup()
    async def incoming(self,text='你好',at=True,**kw):
        self.mid+=1;e=event(text,at,mid=self.mid,**kw);before=len(self.up.rows)
        await self.g._incoming(frames(e),self.up,self.pending)
        return self.up.rows[before:]
    async def output(self,ticket,action='send_group_msg',group='111',extra=None):
        params=dict(group_id=group,message=[dict(type='text',data={'text':'回复'})])
        if action=='send_msg':params['message_type']='group'
        if ticket is not None:params['qqbot_output_ticket']=ticket
        if extra:params.update(extra)
        await self.g._outgoing(Duplex(frames(dict(action=action,params=params,echo='x'+str(self.mid))),self.up),self.down,self.pending)
    async def test_control_and_forward(self):
        self.assertFalse(await self.incoming('非@普通',False))
        row=(await self.incoming())[0];self.assertIn('qqbot_output_ticket',row)
        self.assertFalse(await self.incoming('肥鱼别说话',False))
        self.assertFalse(self.g.silence.normal('111'))
        for text in ['肥鱼可以说了','@222','[CQ:at,qq=222]','肥鱼你好']:self.assertFalse(await self.incoming(text,False))
        self.assertFalse(await self.incoming('请先不要说话',True))
        self.assertFalse(await self.incoming('叫醒',True,sender='999'))
        self.assertFalse(self.g.silence.normal('111'))
        self.assertTrue(await self.incoming('新问题',True,sender='555'))
        self.assertTrue(self.g.silence.normal('111'))
        await self.output(row['qqbot_output_ticket']);self.assertFalse(self.down.rows)
        self.assertEqual(self.up.rows[-1]['message'],DENIED)
        self.assertTrue(await self.incoming('另群',True,group='444'))
    async def test_non_original_at_never_wakes_or_issues_materials(self):
        await self.incoming('肥鱼闭嘴',False)
        for segment in [dict(type='at',data={'qq':'all'}),dict(type='at',data={'qq':'555'}),dict(type='reply',data={'id':'old'}),dict(type='forward',data={'message':[dict(type='at',data={'qq':'222'})]})]:
            self.mid+=1;e=event('合成',False,mid=self.mid);e['message'].insert(0,segment)
            e['qqbot_output_ticket']='forged';e['qqbot_reference']='old'
            up=Capture()
            with patch.object(self.g.materials,'issue',side_effect=AssertionError('muted material issued')):
                await self.g._incoming(frames(e),up,self.pending)
            self.assertFalse(up.rows);self.assertFalse(self.g.silence.normal('111'))
        self.assertFalse(self.g.materials.entries);self.assertFalse(self.g.members.caps)

    async def test_disabled_and_free(self):
        self.g.config=replace(self.cfg,participation_mode='free')
        self.assertTrue(await self.incoming('普通',False))
        self.assertFalse(await self.incoming('肥鱼闭嘴',False))
        self.assertFalse(await self.incoming('普通',False))
        self.assertTrue(await self.incoming('恢复',True));self.assertTrue(await self.incoming('普通',False))
        self.g.config=replace(self.cfg,silence_enabled=False)
        self.assertFalse(await self.incoming('肥鱼闭嘴',False))
        self.assertTrue(await self.incoming('普通',True))
    async def test_dedup_filter_before_control(self):
        with patch('qqbot_gateway.group_silence.silence_request',side_effect=AssertionError('blacklist reached recognition')):
            self.assertFalse(await self.incoming('肥鱼闭嘴',True,sender='999'))
            self.assertFalse(await self.incoming('肥鱼闭嘴',True,group='777'))
            self.assertFalse(await self.incoming('肥鱼闭嘴',True,sender='222'))
        e=event('肥鱼闭嘴',True,mid=900)
        await self.g._incoming(frames(e),self.up,self.pending)
        await self.incoming('醒',True)
        await self.g._incoming(frames(e),self.up,self.pending)
        self.assertTrue(self.g.silence.normal('111'))
    async def test_output_sanitizing_and_both_routes(self):
        for action in ['send_group_msg','send_msg']:
            row=(await self.incoming())[0];await self.output(row['qqbot_output_ticket'],action)
            self.assertNotIn('qqbot_output_ticket',json.dumps(self.down.rows[-1]))
        before=len(self.down.rows)
        await self.output(None);self.assertEqual(len(self.down.rows),before)
        self.assertEqual(self.up.rows[-1]['message'],DENIED)
        e=event(mid=800);e['qqbot_output_ticket']='forged';e['qqbot_fake']='fake'
        await self.g._incoming(frames(e),self.up,self.pending)
        self.assertNotEqual(self.up.rows[-1]['qqbot_output_ticket'],'forged');self.assertNotIn('qqbot_fake',self.up.rows[-1])
    async def test_final_lock_old_after_wake_and_delayed_ACK(self):
        ticket=(await self.incoming())[0]['qqbot_output_ticket']
        # Force send past first validation, then change generation before final lock.
        lock=self.g.silence.locks['111'];await lock.acquire()
        task=asyncio.create_task(self.output(ticket));await asyncio.sleep(.02)
        self.g.silence.control('111',True,False);self.g.silence.control('111',False,True)
        lock.release();await task
        self.assertFalse(self.down.rows);self.assertFalse(self.pending)
        self.assertEqual(self.up.rows[-1]['message'],DENIED)
        fresh=(await self.incoming())[0]['qqbot_output_ticket'];await self.output(fresh)
        echo=self.down.rows[-1]['echo'];self.assertTrue(self.pending)
        await self.incoming('肥鱼闭嘴',False)
        await self.g._incoming(frames(dict(status='ok',retcode=0,echo=echo,data={'message_id':987})),self.up,self.pending)
        self.assertEqual(self.up.rows[-1]['data']['message_id'],987);self.assertFalse(self.pending)
    async def test_reconnect_keeps_restart_resets_and_write_failure(self):
        await self.incoming('肥鱼闭嘴',False)
        self.g.observe_online({'online':False});self.g.observe_online({'online':True})
        self.assertFalse(self.g.silence.normal('111'))
        metadata=json.loads((self.root/'state/gate-connection.json').read_text())
        self.assertNotIn('肥鱼',json.dumps(metadata));self.assertNotIn('111',json.dumps(metadata['silence']))
        g2=OneBotGate(replace(self.cfg,database=self.root/'other'),self.root)
        try:self.assertTrue(g2.silence.normal('111'))
        finally:g2.store.close()
        with patch.object(Path,'replace',side_effect=OSError('synthetic')):
            with self.assertRaises(OSError):await self.incoming('醒',True)

if __name__=='__main__':unittest.main()
