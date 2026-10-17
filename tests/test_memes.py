import asyncio
import io
import json
from pathlib import Path
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch
from PIL import Image
from aiohttp import web,ClientSession
from qqbot_gateway.meme_catalog import MemeCatalog,inspect_image,controlled_path,validate_memes
from qqbot_gateway.media_protocol import media_plan,trusted_media_plan
from qqbot_gateway.reply_plan import DEFAULTS
from qqbot_gateway.meme_import import media_url,admin_token,favorites
from qqbot_gateway.onebot_gate import OneBotGate,allowed_action
from qqbot_gateway.config import GateConfig


def picture(fmt='PNG',size=(3,3)):
    f=io.BytesIO();Image.new('RGB',size,'red').save(f,format=fmt);return f.getvalue()


def registered(root):
    c=MemeCatalog(root,{'enabled':True});r=c.add(picture());r.update(name='自造红块',context='开心',tags=['开心'],enabled=True);c.save();return c,r


class CatalogTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_types_and_disguise(self):
        for fmt in ('PNG','JPEG','WEBP','GIF'):self.assertTrue(inspect_image(picture(fmt))['sha256'])
        for data,suffix in [(picture(),'.gif'),(b'<svg/>','.png'),(b'MZexe','.jpg')]:
            with self.assertRaises(ValueError):inspect_image(data,suffix=suffix)
    def test_limits(self):
        for data,maximum in [(picture(),1),(picture(size=(4097,1)),8388608)]:
            with self.assertRaises(ValueError):inspect_image(data,maximum)
        frames=[Image.new('RGB',(2,2),(i,0,0)) for i in range(121)];out=io.BytesIO()
        frames[0].save(out,format='GIF',save_all=True,append_images=frames[1:],duration=20)
        with self.assertRaises(ValueError):inspect_image(out.getvalue())
    def test_config(self):
        self.assertFalse(validate_memes({})['enabled'])
        for cfg in ({'enabled':1},{'inbox_dir':'../x'},{'max_images_per_turn':2},{'library_dir':'state/else'}):
            with self.assertRaises(ValueError):validate_memes(cfg)
    def test_unconfirmed_dedup(self):
        c=MemeCatalog(self.root);a=c.add(picture());b=c.add(picture());self.assertIs(a,b);self.assertEqual(c.candidates('开心'),[])
    def test_hash_change(self):
        c,r=registered(self.root);p,_=c.resolve(r['id']);p.write_bytes(picture('GIF'))
        self.assertEqual(c.candidates('开心'),[])

    def test_disabled_preview_keeps_selection_closed_and_escapes_gallery(self):
        c=MemeCatalog(self.root);row=c.add(picture());row['name']='<script>alert(1)</script>'
        c.save();before=c.path.read_bytes()
        path,_=c.preview(row['id']);self.assertTrue(path.is_file())
        with self.assertRaises(ValueError):c.resolve(row['id'])
        page=c.preview_page();html=page.read_text(encoding='utf-8')
        self.assertIn('1 · &lt;script&gt;',html);self.assertNotIn('<script>',html)
        self.assertIn(path.as_uri(),html);self.assertIn("default-src 'none'",html)
        self.assertEqual(c.path.read_bytes(),before)
        path.write_bytes(picture('GIF'))
        with self.assertRaises(ValueError):c.preview(row['id'])
        self.assertIn('文件缺失或校验失败',c.preview_page().read_text(encoding='utf-8'))
    def test_paths(self):
        with self.assertRaises(ValueError):controlled_path(self.root,'../escape')
        outside=self.root/'outside';outside.mkdir();link=self.root/'link'
        import subprocess
        subprocess.run(['cmd','/c','mklink','/J',str(link),str(outside)],capture_output=True,check=True)
        try:
            with self.assertRaises(ValueError):controlled_path(self.root,'link/xx')
        finally:link.rmdir()
    def test_scan_and_candidate_budget(self):
        folder=self.root/'assets/memes/inbox';folder.mkdir(parents=True);(folder/'ok.png').write_bytes(picture());(folder/'bad.png').write_bytes(b'html')
        c=MemeCatalog(self.root);self.assertEqual(c.scan(),(1,1));self.assertFalse(c.rows[0]['enabled'])
        c.rows[0].update(name='自造',tags=['开心'],enabled=True);c.save()
        self.assertEqual(len(c.candidates('开心')),1)
        self.assertLessEqual(len(json.dumps(c.candidates('开心'),ensure_ascii=False).encode()),2000)
    def test_catalog_competition_and_stage(self):
        c,r=registered(self.root);other=MemeCatalog(self.root,c.cfg);other.rows[0]['name']='另名';other.save()
        c.rows[0]['name']='冲突'
        with self.assertRaises(ValueError):c.save()
        c=MemeCatalog(self.root,c.cfg);c.rows[0]['context']='暂存';c.stage()
        self.assertNotEqual(MemeCatalog(self.root,c.cfg).rows,c.rows)
        fresh=MemeCatalog(self.root,c.cfg);fresh.activate_pending();self.assertEqual(fresh.rows[0]['context'],'暂存')
    def test_protocol_and_id(self):
        c,r=registered(self.root);raw=dict(qqbot_media_reply=1,kind='chat',bubbles=['开心'],meme_id=r['id'])
        _,p=media_plan(json.dumps(raw),DEFAULTS,'开心',c,c.candidates('开心'))
        self.assertEqual([x.type for x in p.parts],['text','image']);self.assertEqual(trusted_media_plan(p.metadata('r'),p.canonical_text,'r',DEFAULTS),p)
        for mid in ('file:///secret','https://gchat.qpic.cn/x','unknown'):
            raw['meme_id']=mid;_,p=media_plan(json.dumps(raw),DEFAULTS,'开心',c,c.candidates('开心'));self.assertEqual(len(p.parts),1)
    def test_only_and_serious_limits(self):
        c,r=registered(self.root);raw=dict(qqbot_media_reply=1,kind='chat',bubbles=[],meme_id=r['id'])
        for question,expect in [('发个表情','image'),('普通问题','text')]:
            _,p=media_plan(json.dumps(raw),DEFAULTS,question,c,c.candidates(question));self.assertEqual(p.parts[0].type,expect)
        raw['bubbles']=['回复']
        for cfg,q in [(DEFAULTS|{'max_bubbles':1},'开心'),(DEFAULTS,'详细解释代码')]:
            _,p=media_plan(json.dumps(raw),cfg,q,c,c.candidates(q));self.assertEqual(len(p.parts),1)
    def test_bad_protocol(self):
        c,r=registered(self.root)
        for raw in ('{"broken"','{"qqbot_media_reply":1,"qqbot_media_reply":1}','{"url":"x"}'):
            decision,p=media_plan(raw,DEFAULTS,'x',c,[]);self.assertEqual(decision,'error');self.assertNotIn('{',p.canonical_text)
    def test_media_hosts(self):
        self.assertTrue(media_url('https://gchat.qpic.cn/x?rkey=transient'))
        for url in ('http://gchat.qpic.cn/x','https://evil.qpic.cn/x','https://127.0.0.1/x','https://gchat.qpic.cn@localhost/x'):
            with self.assertRaises(Exception):media_url(url)

    def test_candidate_limits_and_missing_restore(self):
        c,r=registered(self.root);path,_=c.resolve(r['id']);path.unlink();c.add(picture());self.assertTrue(path.exists())
        for i in range(32):
            f=io.BytesIO();Image.new('RGB',(2,2),(i,0,0)).save(f,format='PNG')
            row=c.add(f.getvalue());row.update(name='自造'+str(i),tags=['开心'],context='仅测试'*8,enabled=True)
        rows=c.candidates('开心')
        self.assertLessEqual(len(rows),16)
        self.assertLessEqual(len(json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode()),2000)


class ImportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.cfg=GateConfig('222',frozenset({'111'}),frozenset({'333'}),'a'*32,'b'*32,self.root/'gate.sqlite')
        token=admin_token(self.root,True);self.gate=OneBotGate(self.cfg,self.root);self.token=token
        self.server=web.AppRunner(self.gate.application(),access_log=None);await self.server.setup();site=web.TCPSite(self.server,'127.0.0.1',0);await site.start();self.port=site._server.sockets[0].getsockname()[1]
    async def asyncTearDown(self):await self.server.cleanup();self.tmp.cleanup()
    async def test_fixed_rpc_auth_scope_offline(self):
        async with ClientSession() as s:
            url=f'http://127.0.0.1:{self.port}/admin/memes/favorites'
            for token,body,expected in [('a'*32,{'count':1,'mode':'detail'},401),(self.token,{'count':True,'mode':'detail'},400),(self.token,{'count':1,'mode':'detail','action':'get_cookies'},400),(self.token,{'count':1,'mode':'detail'},503)]:
                async with s.post(url,headers={'Authorization':'Bearer '+token},json=body) as r:self.assertEqual(r.status,expected)
        for action in ('fetch_custom_face_detail','fetch_custom_face','get_cookies','get_credentials','add_custom_face','get_group_msg_history'):
            self.assertFalse(allowed_action({'action':action,'params':{}},self.cfg))
    async def test_fake_favorites_import(self):
        gate=self.gate;calls=[]
        class Downstream:
            async def send_json(self,obj):
                calls.append(obj)
                from types import SimpleNamespace
                import aiohttp
                class Frames:
                    def __aiter__(self):return self.iterate()
                    async def iterate(self):
                        yield SimpleNamespace(type=aiohttp.WSMsgType.TEXT,data=json.dumps({'status':'ok','retcode':0,'echo':obj['echo'],'data':[{'url':'https://gchat.qpic.cn/fake?rkey=never_saved','desc':'PRIVATE_METADATA'}]}))
                class Upstream:
                    async def send_str(self,value):raise AssertionError('Admin result leaked to framework')
                await gate._incoming(Frames(),Upstream(),set())
        gate.active=Downstream();gate.connected=True;gate.online=True
        async def fetch(url,maximum):self.assertIn('never_saved',url);return picture()
        try:
            result=await favorites(self.root,validate_memes({}),self.port,fetch=fetch)
            self.assertEqual(result,(1,0));self.assertEqual(len(calls),1);self.assertEqual(calls[0]['action'],'fetch_custom_face_detail')
            staged=(self.root/'state/memes-pending.local.yaml').read_text();self.assertNotIn('rkey',staged);self.assertNotIn('PRIVATE_METADATA',staged)
            self.assertFalse((self.root/'config/memes.local.yaml').exists())
        finally:gate.active=None
    async def test_cancel_no_retry(self):
        gate=self.gate;calls=[]
        class Downstream:
            async def send_json(self,obj):calls.append(obj)
        gate.active=Downstream();gate.connected=True;gate.online=True
        try:
            task=asyncio.create_task(favorites(self.root,validate_memes({}),self.port))
            while not calls:await asyncio.sleep(.001)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):await task
            self.assertEqual(len(calls),1)
        finally:gate.active=None

    async def test_basic_partial_invalid_url_single_attempt(self):
        gate=self.gate;calls=[];downloads=[]
        class Downstream:
            async def send_json(self,obj):
                calls.append(obj)
                gate.admin_pending[next(iter(gate.admin_pending))].set_result({'status':'ok','retcode':0,'data':['file:///private','https://gchat.qpic.cn/fixture']})
        gate.active=Downstream();gate.connected=True;gate.online=True
        async def fetch(url,maximum):downloads.append(url);return picture()
        try:
            result=await favorites(self.root,validate_memes({}),self.port,basic=True,fetch=fetch)
            self.assertEqual(result,(1,1));self.assertEqual(len(calls),1);self.assertEqual(len(downloads),1)
            self.assertEqual(calls[0]['action'],'fetch_custom_face')
        finally:gate.active=None
    async def test_gate_media_scope(self):
        c,r=registered(self.root);cfg=replace(self.cfg,media_catalog=c);path,_=c.resolve(r['id'])
        def action(part):return {'action':'send_group_msg','params':{'group_id':'111','message':[part]}}
        self.assertTrue(allowed_action(action({'type':'image','data':{'file':path.as_uri()}}),cfg))
        for part in ({'type':'image','data':{'file':'https://gchat.qpic.cn/x'}},{'type':'image','data':{'file':'base64://xx'}},{'type':'text','data':{'text':'[CQ:image,file=x]'}},{'type':'at','data':{'qq':'all'}},{'type':'file','data':{'file':path.as_uri()}}):self.assertFalse(allowed_action(action(part),cfg))

    async def test_download_failures_redirect_and_total_budget(self):
        from qqbot_gateway.meme_import import download
        class Content:
            async def iter_chunked(self,n):yield picture()
        class Response:
            status=200;headers={'Content-Type':'image/png'};content=Content()
            async def __aenter__(self):return self
            async def __aexit__(self,*args):pass
        response=Response();calls=[]
        class Session:
            def __init__(self,**kwargs):
                # Close real connector created by function; no socket is opened.
                self.connector=kwargs['connector']
            async def __aenter__(self):return self
            async def __aexit__(self,*args):await self.connector.close()
            def get(self,url,**kwargs):calls.append(url);return response
        with patch('qqbot_gateway.meme_import.aiohttp.ClientSession',Session):
            self.assertEqual(await download('https://gchat.qpic.cn/x',8388608),picture())
            response.status=403
            with self.assertRaises(ValueError):await download('https://gchat.qpic.cn/x',8388608)
            response.status=302;response.headers={'Location':'https://evil.example/private'}
            with self.assertRaises(ValueError):await download('https://gchat.qpic.cn/x',8388608)
            response.status=200;response.headers={'Content-Type':'image/png'}
            with self.assertRaises(ValueError):await download('https://gchat.qpic.cn/x',1)
            with self.assertRaises(ValueError):await download('https://gchat.qpic.cn/x',8388608,{'bytes':128*1024*1024})
        self.assertEqual(len(calls),5)
