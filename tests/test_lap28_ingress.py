"""Self-made images/events, ephemeral servers and owned synthetic processes only."""
import asyncio
import copy
from contextlib import ExitStack, redirect_stdout, redirect_stderr
from dataclasses import replace
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from PIL import Image
import psutil

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
from qqbot_gateway import vision_ingress as evidence
from qqbot_gateway.vision_intake_gate import IntakeGate, serve
from qqbot_gateway.vision import Materials, validate_config, require_production
from qqbot_gateway.onebot_gate import OneBotGate
from scripts import manage, process_host, observe_lap28_intake as command
from test_onebot_gate import configuration, message
from test_lap28 import event, png
from test_config_files import synthetic


class EvidenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_three_exits_and_closed_safe_logs(self):
        rows=await command.synthetic()
        self.assertEqual([r['stage'] for r in rows],['ingress_observed','decoded','text_only'])
        self.assertEqual(rows[0]['attempt_counts']['download'],0)
        self.assertEqual(rows[1]['normalized_dimensions'],[12,8])
        self.assertEqual(rows[2]['failure_enum'],'NO_IMAGE_SEGMENT')
        for row in rows:
            line=evidence.encode(row)
            self.assertEqual(process_host.safe_line('gate',line),line)
            self.assertEqual(process_host.safe_line('gate','2026-10-21 20:00:00,001 INFO '+line),line)
            self.assertIsNone(process_host.safe_line('model',line))
            self.assertIsNone(process_host.safe_line('gate','private '+line))
            self.assertIsNone(process_host.safe_line('gate','123456789123456789 INFO '+line))
            for suffix in (' url=https://gchat.qpic.cn/private',' 123456789123456789','\nprivate'):
                self.assertIsNone(process_host.safe_line('gate',line+suffix))

    async def test_private_values_never_serialized_or_echoed(self):
        stages=[];fetch=AsyncMock(return_value=png())
        row=await evidence.observe(event(first='https://gchat.qpic.cn/PRIVATE_PATH?token=PRIVATE_TOKEN'),
            'connection',lambda identity:True,fetch=fetch,emit=stages.append)
        serialized=json.dumps(stages)
        for private in ('PRIVATE_PATH','PRIVATE_TOKEN','private raw','private-file','C:/private','message_id','cap','sha256','https://'):
            self.assertNotIn(private,serialized)
        self.assertEqual([r['stage'] for r in stages],['ingress_observed','locator_resolved','bytes_fetched','decoded'])
        self.assertEqual(row['image_segment_count'],2);fetch.assert_awaited_once()

    async def test_first_image_bad_never_reads_file_or_tries_second(self):
        for locator in (None,'file:///C:/private.png','C:\\private.png','http://gchat.qpic.cn/x','https://other.example/x'):
            fetch=AsyncMock(side_effect=AssertionError('no download'))
            row=await evidence.observe(event(first=locator),'c',lambda _:True,fetch=fetch)
            self.assertEqual(row['failure_enum'],'SOURCE_UNSUPPORTED');fetch.assert_not_awaited()

    async def test_placeholder_reply_forward_do_not_become_pixels(self):
        for segment in (dict(type='text',data={'text':'[图片] [非文本未解析]'}),
                        dict(type='reply',data={'id':'private','message':event()['message']}),
                        dict(type='forward',data={'content':event()['message']})):
            fetch=AsyncMock()
            row=await evidence.observe(dict(event(),message=[segment]),'c',lambda _:True,fetch=fetch)
            self.assertEqual(row['stage'],'text_only');fetch.assert_not_awaited()

    async def test_failed_decode_empty_fetch_timeout_closed_categories(self):
        for raw,failure,stage in ((b'bad','DECODE_FAILED','bytes_fetched'),(b'','EMPTY_BYTES','locator_resolved')):
            row=await evidence.observe(event(),'c',lambda _:True,fetch=AsyncMock(return_value=raw))
            self.assertEqual((row['stage'],row['failure_enum']),(stage,failure))
        for error,failure in ((TimeoutError('private'),'TIMEOUT'),(OSError('private token'),'FETCH_FAILED')):
            row=await evidence.observe(event(),'c',lambda _:True,fetch=AsyncMock(side_effect=error))
            self.assertEqual(row['failure_enum'],failure)

    async def test_cancellation_releases_material_lease(self):
        entered=asyncio.Event();rows=[];instances=[]
        class Tracked(Materials):
            def __init__(self,*a,**kw):super().__init__(*a,**kw);instances.append(self)
        async def fetch(url):entered.set();await asyncio.Event().wait()
        with patch.object(evidence,'Materials',Tracked):
            task=asyncio.create_task(evidence.observe(event(),'c',lambda _:True,fetch=fetch,emit=rows.append))
            await entered.wait();task.cancel()
            with self.assertRaises(asyncio.CancelledError):await task
        self.assertEqual(rows[-1]['failure_enum'],'CANCELLED')
        self.assertFalse(instances[0].busy or instances[0].entries or instances[0].blobs or instances[0].timers)

    async def test_expiry_after_download_cannot_claim_decoded(self):
        allowed=True
        async def fetch(url):
            nonlocal allowed
            allowed=False;return png()
        row=await evidence.observe(event(),'c',lambda _:allowed,fetch=fetch)
        self.assertEqual(row['failure_enum'],'MATERIAL_DENIED');self.assertNotEqual(row['stage'],'decoded')

    async def test_schema_rejects_unknown_text_numbers_duplicate_keys(self):
        row=evidence.inspect_event(event())
        for change in ({'url':'private'},{'bytes':999999999999},{'mime':'private'}, {'backend_calls':1},
                       {'random_trace':'1'*25},{'stage':'native_observed'}, {'attempt_counts':{'download':2,'redirect':0}},
                       {'first_image_field_flags':{'url':'PRIVATE'}},{'normalized_dimensions':[1025,1]}):
            bad=row|change
            with self.assertRaises(ValueError):evidence.validate_record(bad)
        self.assertIsNone(evidence.safe_log(evidence.encode(row)[:-1]+',"bytes":0}'))

    async def test_actual_url_fetch_path_metadata_redirect_and_security(self):
        from qqbot_gateway import vision, web_retrieval
        class Response:
            def __init__(self,status=200,location=None,data=None,content_type='image/png'):
                self.status=status;self.content_length=None
                self.headers={'Content-Type':content_type}
                if location:self.headers['Location']=location
                async def chunks(size):yield png() if data is None else data
                self.content=SimpleNamespace(iter_chunked=chunks)
            async def __aenter__(self):return self
            async def __aexit__(self,*args):pass
        class Session:
            def __init__(self,responses):self.responses=iter(responses);self.urls=[]
            async def __aenter__(self):return self
            async def __aexit__(self,*args):pass
            def get(self,url,**kw):self.urls.append(url);self.assert_redirect=kw;return next(self.responses)
        for responses,stage,failure,n in (
            ([Response(302,'https://multimedia.nt.qq.com.cn/private'),Response()], 'decoded','none',2),
            ([Response(302,'https://127.0.0.1/private')], 'locator_resolved','FETCH_FAILED',1),
            ([Response(content_type='text/html')], 'locator_resolved','FETCH_FAILED',1),
            ([Response(data=b'')], 'locator_resolved','EMPTY_BYTES',1),
            ([Response(302,'https://gchat.qpic.cn/x')]*3, 'locator_resolved','FETCH_FAILED',3)):
            session=Session(responses)
            with patch.object(web_retrieval,'PublicConnector'),patch.object(vision.aiohttp,'ClientSession',return_value=session) as factory:
                row=await evidence.observe(event(),'c',lambda _:True)
            self.assertEqual((row['stage'],row['failure_enum']),(stage,failure));self.assertEqual(len(session.urls),n)
            self.assertFalse(factory.call_args.kwargs['trust_env']);self.assertFalse(session.assert_redirect['allow_redirects'])
            self.assertIsInstance(factory.call_args.kwargs['cookie_jar'],aiohttp.DummyCookieJar)
            if stage=='decoded':
                self.assertEqual(row['http_status_class'],'2xx');self.assertEqual(row['mime'],'image/png')
                self.assertEqual(row['attempt_counts'],dict(download=1,redirect=1))


class GateTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.cfg=replace(configuration(self.root),blocked_users=frozenset({'999'}))
        self.rows=[];self.fetch=AsyncMock(return_value=png())
        self.gate=IntakeGate(self.cfg,'111','333',fetch=self.fetch,emit=self.rows.append)
        self.client=TestClient(TestServer(self.gate.application()));await self.client.start_server()
    async def asyncTearDown(self):await self.client.close();self.temp.cleanup()
    async def connect(self,**headers):
        return await self.client.ws_connect('/ws',headers={'Authorization':'Bearer '+self.cfg.inbound_token,'X-Self-ID':'222'}|headers)

    async def test_reject_headers_binary_no_routes_or_output(self):
        for headers in ({'Authorization':'wrong'},{'X-Self-ID':'444'}):
            with self.assertRaises(aiohttp.WSServerHandshakeError):await self.connect(**headers)
        for path in ('/context/vision/resolve','/context/vision/bind','/admin/favorites'):
            response=await self.client.post(path,json={});self.assertEqual(response.status,404)
        ws=await self.connect();await ws.send_bytes(b'not a JSON event');await ws.receive(timeout=1)
        self.assertFalse(self.rows);self.fetch.assert_not_awaited()

    async def test_denied_events_no_diagnostics_then_one_sample(self):
        ws=await self.connect()
        for changes in ({'user_id':999},{'user_id':222},{'group_id':444},{'message_type':'private'},
                        {'self_id':444},{'message':[dict(type='image',data={'url':'https://gchat.qpic.cn/x'})]},
                        {'message':[dict(type='text',data={'text':'@222 [图片]'})]}):
            await ws.send_json(event()|changes)
        await asyncio.sleep(.02);self.assertFalse(self.rows);self.fetch.assert_not_awaited()
        await ws.send_json(event());await asyncio.wait_for(self.gate.done.wait(),1)
        self.assertEqual(self.gate.result['stage'],'decoded')
        await ws.send_json(event(mid=2));await asyncio.sleep(.02);self.fetch.assert_awaited_once()
        with self.assertRaises(TimeoutError):await ws.receive(timeout=.02)
        self.assertFalse(list(self.root.iterdir()))  # no history/DB/disk images

    async def test_target_sender_and_group_restrictions(self):
        for group,sender in (('444','333'),('111','999'),('111','222'),('111','bad')):
            with self.assertRaises(ValueError):IntakeGate(self.cfg,group,sender)
        ws=await self.connect();await ws.send_json(event(sender=444));await asyncio.sleep(.02)
        self.assertFalse(self.rows)

    async def test_text_placeholder_is_not_success(self):
        ws=await self.connect();e=message();e['message'][1]['data']['text']='[图片]'
        await ws.send_json(e);await asyncio.wait_for(self.gate.done.wait(),1)
        self.assertEqual(self.gate.result['stage'],'text_only');self.fetch.assert_not_awaited()

    async def test_disconnect_cancels_owned_materials(self):
        entered=asyncio.Event()
        async def blocked(url):entered.set();await asyncio.Event().wait()
        self.gate.fetch=blocked
        ws=await self.connect();await ws.send_json(event());await entered.wait();await ws.close()
        await asyncio.wait_for(self.gate.done.wait(),1)
        self.assertTrue(self.gate.task.done());self.assertEqual(self.rows[-1]['failure_enum'],'CANCELLED')

    async def test_free_mode_scope_and_silence_controls(self):
        await self.client.close()
        cfg=replace(self.cfg,participation_mode='free',silence_enabled=True)
        self.gate=IntakeGate(cfg,'111','333',fetch=self.fetch,emit=self.rows.append)
        self.client=TestClient(TestServer(self.gate.application()));await self.client.start_server()
        ws=await self.connect();stop=message();stop['message'][1]['data']['text']='先别说话'
        await ws.send_json(stop)
        ambient=event();ambient['message']=ambient['message'][1:]
        await ws.send_json(ambient);await asyncio.sleep(.02);self.assertFalse(self.rows)
        await ws.send_json(event());await asyncio.wait_for(self.gate.done.wait(),1)
        self.assertEqual(self.gate.result['stage'],'decoded')

    async def test_serve_timeout_login_required_cleanup(self):
        cfg=replace(self.cfg,port=await free_port())
        with patch('qqbot_gateway.vision_intake_gate.IntakeGate.emit',create=True):
            await serve(cfg,self.root,'a'*32,'111','333',.03)
        value=json.loads((self.root/'state/vision-evidence'/('a'*32+'.json')).read_text())
        self.assertEqual(value,dict(state='login_required',record=None))
        # Port has been released on timeout.
        import socket
        with socket.socket() as sock:sock.bind((cfg.host,cfg.port))

    async def test_production_diagnostics_after_admission_before_stripping(self):
        async def incoming(events):
            for e in events:yield SimpleNamespace(type=aiohttp.WSMsgType.TEXT,data=json.dumps(e))
        gate=OneBotGate(replace(self.cfg,ingress_diagnostics=True))
        gate.materials.fetch=AsyncMock(side_effect=AssertionError('no production diagnostics download'))
        upstream=SimpleNamespace(send_json=AsyncMock(),send_str=AsyncMock())
        denied=[event(sender=999),event()|{'group_id':444},event()|{'message_type':'private'}]
        with self.assertNoLogs('qqbot_gateway.onebot_gate',level='INFO'):
            await gate._incoming(incoming(denied),upstream,set())
        with self.assertLogs('qqbot_gateway.onebot_gate',level='INFO') as logs:
            await gate._incoming(incoming([event()]),upstream,set())
        logged=logs.records[0].getMessage()
        self.assertIsNotNone(evidence.safe_log(logged));self.assertNotIn('https://',logged)
        forwarded=upstream.send_json.call_args[0][0]
        self.assertEqual(forwarded['raw_message'],'');self.assertNotIn('https://',json.dumps(forwarded))
        gate.materials.fetch.assert_not_awaited();gate.materials.clear();gate.store.db.close()


async def free_port():
    import socket
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));return sock.getsockname()[1]


class CommandTests(unittest.TestCase):
    def test_default_inspect_no_mutation_network_or_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir()
            import yaml
            (root/'config/settings.local.yaml').write_text(yaml.safe_dump(synthetic()),encoding='utf-8')
            before={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with patch.object(command,'ROOT',root),patch.object(manage,'intake_only',side_effect=AssertionError('real mode forbidden')):
                with redirect_stdout(io.StringIO()) as out:self.assertEqual(command.main([]),0)
            self.assertEqual(json.loads(out.getvalue())['ingress_state'],'ingress_unverified')
            self.assertEqual(before,{p:p.read_bytes() for p in root.rglob('*') if p.is_file()})
    def test_intake_flags_never_imply_authorization(self):
        with patch.object(manage,'intake_only') as intake:
            for args in (['--intake-only'],['--sample-group','111'],['--intake-only','--authorize','ONE_IMAGE_INGRESS']):
                with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):command.main(args)
            intake.assert_not_called()
    def test_defaults_and_production_gate_remain_closed(self):
        self.assertFalse(validate_config({})['ingress_diagnostics'])
        for value in (None,1,'true'):
            with self.assertRaises(ValueError):validate_config({'ingress_diagnostics':value})
        with self.assertRaises(ValueError):require_production({'vision':validate_config({'enabled':True,'ingress_diagnostics':True})})


class ManagementTests(unittest.TestCase):
    def test_require_stopped_and_cleanup_blocks_before_spawn(self):
        with tempfile.TemporaryDirectory() as directory,ExitStack() as stack:
            root=Path(directory);stack.enter_context(patch.object(manage,'ROOT',root))
            popen=stack.enter_context(patch.object(manage.psutil,'Popen'))
            with patch('qqbot_gateway.config.require_stopped',side_effect=ValueError('not stopped')):
                with self.assertRaises(ValueError):manage.intake_only(authorize='ONE_IMAGE_INGRESS',group='111',sender='333')
            with patch('qqbot_gateway.config.require_stopped'),patch('qqbot_gateway.cleanup_identity.CleanupOwner.status',return_value={'blocked':True}):
                with self.assertRaises(ValueError):manage.intake_only(authorize='ONE_IMAGE_INGRESS',group='111',sender='333')
            popen.assert_not_called()

    def run_fake(self, cancel=False):
        with tempfile.TemporaryDirectory() as directory,ExitStack() as stack:
            root=Path(directory);cfg=configuration(root)
            stack.enter_context(patch.object(manage,'ROOT',root));stack.enter_context(patch.object(manage,'NAPCAT',root/'napcat'))
            stack.enter_context(patch('qqbot_gateway.config.require_stopped'))
            stack.enter_context(patch('qqbot_gateway.cleanup_identity.CleanupOwner.status',return_value={'blocked':False}))
            stack.enter_context(patch.object(manage,'task_counts',return_value={}))
            stack.enter_context(patch.object(manage,'check_port'))
            stack.enter_context(patch.object(manage,'read_project',return_value=SimpleNamespace(settings=synthetic())))
            stack.enter_context(patch.object(manage,'load_gate_config',return_value=cfg))
            stack.enter_context(patch.object(manage,'require_intake_logging'))
            stack.enter_context(patch.object(manage,'create_snapshot',return_value=(root/'snapshot',{'instance_id':'a'*32,'snapshot_digest':'b'*64})))
            def health(port):
                mode=json.loads((root/'state/service-mode.json').read_text())
                return dict(intake_only=True,online=False,instance_id=mode['instance_id'],pid=101,created=1.)
            stack.enter_context(patch.object(manage,'fetch_health',side_effect=health))
            stack.enter_context(patch.object(manage,'alive',return_value=True))
            def capture(entries,process,component,started):
                entry=dict(pid=process.pid,created=1.,component=component)
                if entry not in entries:entries.append(entry)
            stack.enter_context(patch.object(manage,'capture',side_effect=capture))
            stop=stack.enter_context(patch.object(manage,'stop'))
            calls=[]
            def launch(args,**kw):
                calls.append((args,kw));return SimpleNamespace(pid=100+len(calls),poll=lambda:None)
            stack.enter_context(patch.object(manage.psutil,'Popen',side_effect=launch))
            stack.enter_context(patch.object(manage.time,'sleep',side_effect=KeyboardInterrupt if cancel else lambda _:None))
            if not cancel:
                ticks=iter([0,0,0,0,2])
                stack.enter_context(patch.object(manage.time,'monotonic',side_effect=lambda:next(ticks,2)))
            result=manage.intake_only(authorize='ONE_IMAGE_INGRESS',group='111',sender='333',timeout_seconds=1)
            self.assertEqual(result['state'],'cancelled' if cancel else 'login_required')
            self.assertEqual([args[2] for args,_ in calls],['gate','napcat'])
            self.assertFalse(any('astrbot' in str(args) or 'model_gateway' in str(args) for args,_ in calls))
            self.assertNotIn('333',str(calls[0][0]));self.assertNotIn('222',str(calls[1][0]))
            self.assertEqual({e['pid'] for e in stop.call_args[0][0]},{101,102})
    def test_timeout_reaps_only_diagnostic_owned_identities(self):self.run_fake()
    def test_cancel_reaps_only_diagnostic_owned_identities(self):self.run_fake(cancel=True)

    def test_actual_synthetic_process_reaped_unrelated_process_survives(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(manage,'STATE',Path(directory)/'owned.json'):
            own=psutil.Popen([sys.executable,'-c','import time; time.sleep(30)'])
            other=psutil.Popen([sys.executable,'-c','import time; time.sleep(30)'])
            try:
                manage.stop([dict(pid=own.pid,created=own.create_time(),component='gate')])
                self.assertIsNotNone(own.poll());self.assertIsNone(other.poll())
            finally:
                for process in (own,other):
                    if process.poll() is None:process.kill()
                    process.wait(timeout=3)

    def test_unsafe_napcat_file_logging_refused_without_rewriting(self):
        with tempfile.TemporaryDirectory() as directory,ExitStack() as stack:
            root=Path(directory);napcat=root/'napcat';base=napcat/'versions/9.9.33-52230/resources/app/napcat/config';base.mkdir(parents=True)
            stack.enter_context(patch.object(manage,'ROOT',root));stack.enter_context(patch.object(manage,'NAPCAT',napcat))
            for name in ('napcat.json','napcat_222.json'):(base/name).write_text('{"fileLog":false}')
            manage.require_intake_logging('222')
            path=base/'napcat_222.json';path.write_text('{"fileLog":true}')
            with self.assertRaises(ValueError):manage.require_intake_logging('222')
            self.assertEqual(path.read_text(),'{"fileLog":true}')


if __name__=='__main__':unittest.main()
