"""VIS-01..04: synthetic media only; no QQ, public downloads or models."""
import asyncio
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1])]
from PIL import Image
from qqbot_gateway.vision import (Materials,normalize,image_url,attach_image,member_source,CURRENT,NativeImage,
    text_budget,cli_message,native_payload_images,wire_check,capability,binding,validate_config,require_production,
    MAX_RAW,MAX_BLOB,NORMALIZER)
from qqbot_gateway.turn_v2 import sha,validate_source,validate_header,metadata,verify
from qqbot_gateway.attention import canonical
from qqbot_gateway.token_budget import InputBudget
from qqbot_gateway.errors import GatewayError
from qqbot_gateway.reply_plan import ReplyPlan,DEFAULTS


def png(size=(12,8),color='red',fmt='PNG'):
    out=io.BytesIO();Image.new('RGB',size,color).save(out,format=fmt);return out.getvalue()


def event(sender=333,first='https://gchat.qpic.cn/test',mid=1):
    return dict(post_type='message',message_type='group',self_id=222,group_id=111,user_id=sender,message_id=mid,
        message=[dict(type='at',data={'qq':'222'}),dict(type='image',data=dict(url=first,file='private-file',filePath='C:/private')),
                 dict(type='image',data=dict(url='https://multimedia.nt.qq.com.cn/second'))],raw_message='private raw')


def body(image,**kwargs):
    return dict(purpose='vision.resolve',cap=image['cap'],image_ref=image['image_ref'],request_key='a'*64,
                target_seq=1,source_digest='b'*64,epoch='e'*64)|kwargs


def source_request(image,mode='free'):
    source=member_source('合成问题',['鱼片']);attach_image(source,image)
    request=dict(version=2,kind='group_turn' if mode=='free' else 'member_turn',request_key='a'*64,
        epoch='e'*64,config_version='c'*64,source_digest=sha(source),mode=mode,addressing='mention',must_reply=True,
        target_seq=1,resource_caps=[image['cap']])
    return source,request


class NormalizeTests(unittest.TestCase):
    def test_VIS01_dimensions_hash_and_no_metadata(self):
        raw=png((1600,1000));blob=normalize(raw)
        self.assertLessEqual(max(blob.width,blob.height),1024)
        self.assertLessEqual(blob.width*blob.height,1000000)
        self.assertLessEqual(len(blob.data),MAX_BLOB)
        self.assertEqual(blob.original_sha256,hashlib.sha256(raw).hexdigest())
        self.assertEqual(blob.sha256,hashlib.sha256(blob.data).hexdigest())
        with Image.open(io.BytesIO(blob.data)) as im:self.assertFalse(im.info)
        with self.assertRaises(ValueError):replace(blob,data=b'changed').checked()
        with self.assertRaises(ValueError):replace(blob,width=True).checked()

    def test_VIS01_exif_orientation_and_first_gif_frame(self):
        im=Image.new('RGB',(4,2),'red');exif=Image.Exif();exif[274]=6;out=io.BytesIO();im.save(out,format='JPEG',exif=exif)
        b=normalize(out.getvalue());self.assertEqual((b.width,b.height),(2,4))
        out=io.BytesIO();im.save(out,format='GIF',save_all=True,append_images=[Image.new('RGB',(4,2),'blue')],duration=100,loop=0)
        b=normalize(out.getvalue())
        with Image.open(io.BytesIO(b.data)) as image:self.assertGreater(image.getpixel((0,0))[0],200)

    def test_VIS01_bad_format_size_bomb_and_no_semantic_crop(self):
        for raw in (b'<svg/>',b'bad',b'0'*(MAX_RAW+1),png(fmt='BMP')):
            with self.subTest(length=len(raw)),self.assertRaises(ValueError):normalize(raw)
        with patch('qqbot_gateway.vision.Image.open') as opened:
            opened.return_value.__enter__.return_value=SimpleNamespace(format='PNG',width=16000001,height=1)
            with self.assertRaises(ValueError):normalize(png())
        # Excess entropy is rejected rather than cropping or repeatedly lowering
        # dimensions/quality until content happens to fit.
        im=Image.frombytes('RGB',(1000,1000),__import__('random').Random(4).randbytes(3000000))
        out=io.BytesIO();im.save(out,format='PNG')
        with self.assertRaises(ValueError):normalize(out.getvalue())

    def test_VIS01_exact_https_source_allowlist(self):
        for value in ('file:///x','https://127.0.0.1/x','https://gchat.qpic.cn.evil/x','http://gchat.qpic.cn/x',
                      'https://u:p@gchat.qpic.cn/x','https://gchat.qpic.cn:444/x','https://gchat.qpic.cn/x#frag','https://localhost/x'):
            with self.subTest(value=value),self.assertRaises(ValueError):image_url(value)
        self.assertEqual(image_url('https://gchat.qpic.cn/a'),'https://gchat.qpic.cn/a')

    def test_VIS04_states_never_infer_capacity_from_sample(self):
        for value in ({'status':'production_eligible'},{'enabled':1},{'input_reserve_tokens':True},{'input_reserve_tokens':0}):
            with self.assertRaises(ValueError):validate_config(value)
        self.assertEqual(capability({},'x'),'unverified')
        proof=dict(binding='x',offline_passed=True)
        self.assertEqual(capability(proof,'x'),'offline_passed')
        proof['observations']=[dict(native_success=True,visual_token_upper_bound=4096)]
        self.assertEqual(capability(proof,'x'),'native_observed')
        self.assertEqual(capability(proof,'changed'),'unverified')
        for reserve in (1,4096,65536):
            with self.assertRaises(ValueError):require_production({'vision':dict(enabled=True,input_reserve_tokens=reserve)})

    def test_VIS04_bound_versions_parameters_and_reserve_invalidate(self):
        import yaml
        from qqbot_gateway.config import normalize_settings
        s=yaml.safe_load((Path(__file__).resolve().parents[1]/'config/settings.example.yaml').read_text(encoding='utf-8'))
        s['bot']['qq']='222';s['access'].update(allowed_groups=['111'],admin_users=['333']);s=normalize_settings(s)
        key=binding(s,{'bundle':'a'})
        for changed in ('reserve','model','backend','runtime'):
            value=copy.deepcopy(s);runtime={'bundle':'a'}
            if changed=='reserve':value['vision']['input_reserve_tokens']-=1
            if changed=='model':value['llm']['profiles']['codebuddy_cli']['model']='changed'
            if changed=='backend':value['llm']['backend']='ollama_ssh'
            if changed=='runtime':runtime={'bundle':'b'}
            self.assertNotEqual(binding(value,runtime),key)

    def test_VIS03_final_text_visual_and_wire_budgets(self):
        native=NativeImage(normalize(png()),4096,time.monotonic()+60,time.monotonic()+15)
        token=CURRENT.set(native)
        try:
            b=text_budget(InputBudget(limit=12000,window=16384,output=2048))
            self.assertEqual(b.limit,7904)
            with self.assertRaises(GatewayError):text_budget(InputBudget(limit=4096))
            with self.assertRaises(GatewayError):text_budget(InputBudget(limit=15000,window=16384,output=2048))
            with self.assertRaises(GatewayError):wire_check({'x':'x'*(2*1024*1024)})
            c=cli_message('literal text');self.assertEqual(c['message']['content'][0]['text'],'literal text')
            self.assertEqual(c['message']['content'][1]['source']['media_type'],'image/png')
            self.assertNotIn('cap',json.dumps(c))
            p=native_payload_images(dict(messages=[{'role':'user','content':'literal text'}]))
            self.assertEqual(len(p['messages'][-1]['images']),1)
        finally:CURRENT.reset(token)

    def test_VIS03_expiry_rechecked_before_native_input(self):
        token=CURRENT.set(NativeImage(normalize(png()),4096,time.monotonic()-1,time.monotonic()+15))
        try:
            with self.assertRaises(GatewayError):text_budget(InputBudget())
        finally:CURRENT.reset(token)

    def test_ATT01_source_closed_current_target_only_and_effective_hash(self):
        image=dict(image_ref='i_'+'a'*32,cap='d'*64)
        for mode in ('free','mentions'):
            s,r=source_request(image,mode);validate_header(r);validate_source(canonical(s),r)
            self.assertNotIn(image['cap'],canonical(s))
            effective=copy.deepcopy(s);effective['images']=[normalize(png()).descriptor(image['image_ref'])]
            plan=ReplyPlan('answer',('合成正文',),'合成正文')
            meta=metadata(r,'r','speak',plan,effective,1)
            self.assertEqual(verify(meta,r,'r',plan.canonical_text,DEFAULTS,s),plan)
            meta['manifest']['images'][0]['width']=2048;meta['plan_hash']=sha({k:v for k,v in meta.items() if k!='plan_hash'})
            with self.assertRaises(ValueError):verify(meta,r,'r',plan.canonical_text,DEFAULTS,s)
            bad=copy.deepcopy(s);bad['messages'][0]['images']=[]
            with self.assertRaises(GatewayError):validate_source(canonical(bad),r|dict(source_digest=sha(bad)))


class CapTests(unittest.IsolatedAsyncioTestCase):
    async def test_VIS01_cancelled_queue_retains_ram_lease_until_cleanup_done(self):
        from qqbot_gateway.model_gateway import ModelQueue
        from qqbot_gateway.vision import BlobLease
        entered=asyncio.Event();cancelled=asyncio.Event();cleanup=asyncio.Event();released=[]
        class Runner:
            async def run(self,*args):
                entered.set()
                try:await asyncio.Event().wait()
                except asyncio.CancelledError:cancelled.set();await cleanup.wait();raise
        queue=ModelQueue(Runner());await queue.start()
        lease=BlobLease(lambda:released.append(True))
        image=NativeImage(normalize(png()),4096,time.monotonic()+60,time.monotonic()+15,lease)
        task=asyncio.create_task(queue.submit('policy','prompt','test',vision=image))
        try:
            await entered.wait();task.cancel();await asyncio.gather(task,return_exceptions=True)
            await cancelled.wait()
            self.assertTrue(lease.owned);self.assertFalse(lease.released);self.assertTrue(queue.active)
            cleanup.set()
            for _ in range(100):
                if not queue.active:break
                await asyncio.sleep(.001)
            self.assertEqual(released,[True])
        finally:cleanup.set();await queue.close()

    async def test_VIS03_cli_explicit_effort_control_then_one_image_input(self):
        from test_cli_runner import RunnerTests
        fixture=RunnerTests();fixture.setUp()
        try:
            runner=fixture.runner()
            token=CURRENT.set(NativeImage(normalize(png()),4096,time.monotonic()+60,time.monotonic()+15))
            try:result=await runner.run('policy','question','lap28-high')
            finally:CURRENT.reset(token)
            self.assertEqual((runner.attempts,runner.control_attempts,runner.user_messages_sent),(1,1,1))
            user=json.loads((fixture.root/'user.json').read_text())
            self.assertEqual([p['type'] for p in user['message']['content']],['text','image'])
            argv=json.loads((fixture.root/'argv.json').read_text())['argv']
            self.assertIn('--input-format',argv);self.assertEqual(argv[argv.index('--tools')+1],'')
            self.assertIn('--strict-mcp-config',argv);self.assertNotIn('Read',argv[:argv.index('--disallowedTools')])
        finally:fixture.tearDown()

    async def test_VIS03_preparation_deadline_shared_with_web(self):
        from qqbot_gateway.web_retrieval import WebRunner,Retriever,Retrieval
        from qqbot_gateway.backends import BackendResult
        runner=SimpleNamespace(run=AsyncMock(return_value=BackendResult('not used')))
        reader=Retriever({'enabled':False})
        reader.retrieve=AsyncMock(return_value=Retrieval('none'))
        wrapped=WebRunner(runner,reader,InputBudget(),DEFAULTS)
        s=member_source('https://example.com/',['鱼片']);s['web_anchor']=s['messages'][0]['text']
        token=CURRENT.set(NativeImage(normalize(png()),4096,time.monotonic()+60,time.monotonic()-1))
        try:result=await wrapped.run_v2('policy',json.dumps([dict(role='user',content=canonical(s))]),'test',{'must_reply':True})
        finally:CURRENT.reset(token)
        self.assertFalse(result.generation_performed);self.assertEqual(reader.retrieve.await_count,0);self.assertEqual(runner.run.await_count,0)

    async def test_VIS01_service_invalidation_while_fetching_no_blob(self):
        started=asyncio.Event();release=asyncio.Event()
        async def fetch(url):started.set();await release.wait();return png()
        m=Materials(fetch);i=m.issue(event(),'c');b=body(i);m.bind(b,'c',lambda _:True)
        task=asyncio.create_task(m.resolve(b,'c',lambda _:True));await started.wait();m.clear();release.set()
        with self.assertRaises(ValueError):await task
        self.assertFalse(m.blobs);self.assertFalse(m.entries)

    async def test_VIS02_once_concurrent_replay_and_request_binding(self):
        fetch=AsyncMock(return_value=png());m=Materials(fetch);i=m.issue(event(),'conn');b=body(i)
        m.bind(b,'conn',lambda _:True)
        results=await asyncio.gather(m.resolve(b,'conn',lambda _:True),m.resolve(b,'conn',lambda _:True),return_exceptions=True)
        self.assertEqual(sum(isinstance(x,dict) for x in results),1);self.assertEqual(fetch.await_count,1)
        with self.assertRaises(ValueError):await m.resolve(b,'conn',lambda _:True)
        self.assertEqual(fetch.await_count,1)

    async def test_VIS02_forged_wrong_purpose_target_epoch_connection_consume(self):
        for change in (dict(purpose='members.resolve'),dict(target_seq=2),dict(epoch='f'*64),dict(source_digest='f'*64),dict(request_key='f'*64)):
            fetch=AsyncMock(return_value=png());m=Materials(fetch);i=m.issue(event(),'conn');b=body(i);m.bind(b,'conn',lambda _:True)
            with self.assertRaises(ValueError):await m.resolve(b|change,'conn',lambda _:True)
            with self.assertRaises(ValueError):await m.resolve(b,'conn',lambda _:True)
            self.assertEqual(fetch.await_count,0)
        m=Materials(AsyncMock(return_value=png()))
        with self.assertRaises(ValueError):await m.resolve(body(dict(cap='0'*64,image_ref='i_'+'0'*32)),'conn',lambda _:True)
        i=m.issue(event(),'conn');b=body(i);m.bind(b,'conn',lambda _:True)
        with self.assertRaises(ValueError):await m.resolve(b,'new_connection',lambda _:True)

    async def test_VIS02_unbound_cannot_redeem_and_failed_bind_not_reusable(self):
        m=Materials(AsyncMock(return_value=png()));i=m.issue(event(),'conn');b=body(i)
        with self.assertRaises(ValueError):await m.resolve(b,'conn',lambda _:True)
        with self.assertRaises(ValueError):m.bind(b,'conn',lambda _:True)
        self.assertEqual(m.fetch.await_count,0)

    async def test_VIS02_expiry_cancel_invalidation_and_blacklist_change(self):
        now=[10.];fetch=AsyncMock(return_value=png());m=Materials(fetch,lambda:now[0]);i=m.issue(event(),'c');b=body(i);m.bind(b,'c',lambda _:True)
        now[0]+=61
        with self.assertRaises(ValueError):await m.resolve(b,'c',lambda _:True)
        self.assertEqual(fetch.await_count,0)
        i=m.issue(event(),'c');b=body(i);m.bind(b,'c',lambda _:True)
        with self.assertRaises(ValueError):await m.resolve(b,'c',lambda _:False)
        self.assertEqual(fetch.await_count,0)
        started=asyncio.Event()
        async def slow(url):started.set();await asyncio.Event().wait()
        m=Materials(slow);i=m.issue(event(),'c');b=body(i);m.bind(b,'c',lambda _:True)
        task=asyncio.create_task(m.resolve(b,'c',lambda _:True));await started.wait();task.cancel()
        await asyncio.gather(task,return_exceptions=True)
        self.assertFalse(m.busy)
        with self.assertRaises(ValueError):await m.resolve(b,'c',lambda _:True)
        m.clear();self.assertFalse(m.entries)

    async def test_VIS01_first_only_no_retry_and_bounded_ledger(self):
        fetch=AsyncMock(side_effect=ValueError('synthetic'));m=Materials(fetch)
        self.assertIsNone(m.issue(event(first='file:///bad'),'c'))
        i=m.issue(event(),'c');b=body(i);m.bind(b,'c',lambda _:True)
        with self.assertRaises(ValueError):await m.resolve(b,'c',lambda _:True)
        self.assertEqual(fetch.await_args.args,('https://gchat.qpic.cn/test',))
        for _ in range(200):m.issue(event(),'c')
        self.assertLessEqual(len(m.entries),128)

    async def test_VIS01_dns_mixed_private_blocked(self):
        import socket
        from qqbot_gateway.web_retrieval import PublicResolver,WebFailure
        rows=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',443)),(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))]
        with patch.object(asyncio.get_running_loop(),'getaddrinfo',AsyncMock(return_value=rows)):
            with self.assertRaises(WebFailure):await PublicResolver().resolve('gchat.qpic.cn',443)


class GateTests(unittest.IsolatedAsyncioTestCase):
    async def test_VIS01_gateway_ram_leases_bounded_and_released(self):
        import aiohttp
        from aiohttp import web
        from qqbot_gateway.model_gateway import application,ModelQueue
        from qqbot_gateway.backends import BackendResult
        import random,weakref,gc
        out=io.BytesIO();Image.frombytes('RGB',(900,180),random.Random(9).randbytes(486000)).save(out,format='PNG')
        blob=normalize(out.getvalue());self.assertGreater(len(blob.data),480000)
        image=dict(image_ref='i_'+'a'*32,cap='d'*64);source,request=source_request(image)
        release=asyncio.Event();refs=[];rejected=[]
        class Client:
            async def resolve(self,header,source,deadline):
                value=NativeImage(blob,4096,time.monotonic()+60,deadline);refs.append(weakref.ref(value))
                return value,blob.descriptor(image['image_ref'])
        class Runner:
            attempts=0
            async def run(self,*args):
                refs.append(weakref.ref(CURRENT.get()))
                self.attempts+=1;await release.wait()
                return BackendResult(canonical(dict(qqbot_turn_reply=2,decision='speak',kind='answer',bubbles=['合成正文'],
                    meme_id=None,response_to_seq=1,mention=None,memory_proposals=[])))
        queue=ModelQueue(Runner(),limit=100)
        server=web.AppRunner(application(queue,'x'*40,v2=dict(mode='free',config_version='c'*64,aliases=['鱼片']),materials=Client()),access_log=None)
        await server.setup();site=web.TCPSite(server,'127.0.0.1',0);await site.start();port=site._server.sockets[0].getsockname()[1]
        payload=dict(model='workbuddy-local',stream=False,messages=[dict(role='user',content=canonical(source))],qqbot_request=request)
        try:
            async with aiohttp.ClientSession() as session:
                async def call():
                    async with session.post(f'http://127.0.0.1:{port}/v1/chat/completions',json=payload,
                        headers={'Authorization':'Bearer '+'x'*40,'X-QQBot-Trace':'a'*32}) as response:
                        value=await response.json()
                        if value.get('qqbot_gateway_error')=='INPUT_TOO_LONG':rejected.append(value)
                calls=[asyncio.create_task(call()) for _ in range(20)]
                try:
                    for _ in range(100):
                        if rejected:break
                        await asyncio.sleep(.01)
                    self.assertTrue(rejected)
                finally:release.set();await asyncio.gather(*calls)
            for _ in range(100):
                if not queue.active and queue.queue.empty():break
                await asyncio.sleep(.001)
            gc.collect()
            self.assertTrue(all(r() is None for r in refs),'Idle worker retained an expired RAM image')
        finally:release.set();await server.cleanup()

    async def test_VIS01_blacklist_zero_issue_download_strip_all_modes(self):
        import aiohttp
        from qqbot_gateway.onebot_gate import OneBotGate
        from qqbot_gateway.config import GateConfig
        def configuration(path):return GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,Path(path)/'gate.db')
        class Up:
            def __init__(self):self.rows=[]
            async def send_json(self,x):self.rows.append(x)
            async def send_str(self,x):self.rows.append(json.loads(x))
        for mode in ('mentions','free'):
            with tempfile.TemporaryDirectory() as directory:
                gate=OneBotGate(replace(configuration(directory),participation_mode=mode,blocked_users=frozenset({'999'}),vision_enabled=True))
                gate.materials.fetch=AsyncMock(return_value=png());up=Up()
                async def frames():
                    for e in (event(999),event(333)):
                        e['qqbot_image']={'url':'https://evil'}
                        yield SimpleNamespace(type=aiohttp.WSMsgType.TEXT,data=json.dumps(e))
                try:
                    await gate._incoming(frames(),up,set())
                    self.assertEqual(len(up.rows),1);self.assertEqual(len(gate.materials.entries),1)
                    self.assertEqual(gate.materials.fetch.await_count,0)
                    text=json.dumps(up.rows[0]);self.assertNotIn('private',text);self.assertNotIn('https:',text)
                    self.assertEqual(set(up.rows[0]['qqbot_image']),{'cap','image_ref'})
                    self.assertTrue(all(s['type'] in ('text','at') for s in up.rows[0]['message']))
                finally:gate.store.close()

    async def test_VIS02_private_http_auth_and_fixed_schema(self):
        import aiohttp
        from aiohttp import web
        from qqbot_gateway.onebot_gate import OneBotGate
        from qqbot_gateway.config import GateConfig
        def configuration(path):return GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*40,'b'*40,Path(path)/'gate.db')
        from qqbot_gateway.vision import MaterialClient
        with tempfile.TemporaryDirectory() as directory:
            gate=OneBotGate(replace(configuration(directory),vision_enabled=True));gate.connected=True;gate.online=True
            gate.context_token='c'*64;gate.materials.fetch=AsyncMock(return_value=png())
            server=web.AppRunner(gate.application(),access_log=None);await server.setup()
            site=web.TCPSite(server,'127.0.0.1',0);await site.start();port=site._server.sockets[0].getsockname()[1]
            url=f'http://127.0.0.1:{port}/context/vision/resolve'
            try:
                async with aiohttp.ClientSession() as session:
                    for token in ('','a'*40,'b'*40):
                        async with session.post(url,json={},headers={'Authorization':'Bearer '+token}) as response:self.assertEqual(response.status,401)
                    async with session.post(url,json={'url':'file:///bad'},headers={'Authorization':'Bearer '+'c'*64}) as response:self.assertEqual(response.status,400)
                image=gate.materials.issue(event(),gate.connection_id);s,r=source_request(image)
                native,descriptor=await MaterialClient(url,'c'*64,4096).resolve(r,s,time.monotonic()+15)
                self.assertEqual(native.blob.sha256,descriptor['sha256']);self.assertEqual(gate.materials.fetch.await_count,1)
                self.assertLessEqual(native.expires,gate.materials.entries[image['cap']]['expires'])
                with self.assertRaises(ValueError):await MaterialClient(url,'c'*64,4096).resolve(r,s,time.monotonic()+15)
                self.assertEqual(gate.materials.fetch.await_count,1)
            finally:await server.cleanup()


if __name__=='__main__':unittest.main()
