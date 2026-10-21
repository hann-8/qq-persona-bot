"""Synthetic secrets, ephemeral HTTP, fake ownership; never contacts real 6099."""
import base64
from contextlib import ExitStack, contextmanager
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
from io import StringIO, BytesIO
from contextlib import redirect_stdout
import time
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from qqbot_gateway import napcat_login_observer as obs
from qqbot_gateway.napcat_login_client import LoginFailure
from qqbot_gateway.config import configuration_lock
from qqbot_gateway.lifecycle import atomic_json
from scripts import manage, process_host
from test_napcat_login_http import fake_server
from test_config_files import synthetic
import yaml

STATUS=dict(isLogin=False,isOffline=False,qrLoginAccepted=False,coreReady=False,loginPhase='waiting_qrcode',loginError=None)
READY=dict(alive=True,connected=True,online=True,self_id_verified=True,stopping=False)


@contextmanager
def fake_observer_server(responses, delay=0):
    calls=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            calls.append((self.command,self.path))
            self.rfile.read(int(self.headers.get('Content-Length',0)))
            value=responses[self.path]
            if delay:time.sleep(delay)
            self.send_response(200);self.send_header('Connection','close');self.end_headers()
            try:self.wfile.write(json.dumps({'code':0,'data':value}).encode())
            except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass
        do_GET=do_POST
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    original=http.client.HTTPConnection
    def connection(host,port,**kwargs):
        assert (host,port)==('127.0.0.1',6099)
        return original('127.0.0.1',server.server_port,**kwargs)
    try:
        with patch.object(obs.http.client,'HTTPConnection',side_effect=connection):yield calls
    finally:server.shutdown();server.server_close();thread.join()


class ObserverHTTPTests(unittest.TestCase):
    def test_fixed_readonly_routes_and_auth_only(self):
        now=[0]
        for kind in ('auth','status','quick','info'):
            with self.subTest(kind=kind),fake_server(body={'code':0,'data':[] if kind=='quick' else {}}) as calls:
                web=obs.ReadOnlyWebUI(lambda:True,120,clock=lambda:now[0]);web.credential='synthetic'
                # Existing HTTP fixture intentionally supports POST only; quick GET must fail, not change method.
                if kind=='quick':
                    with self.assertRaises(LoginFailure):web.request(kind)
                else:web.request(kind)
                if calls:self.assertEqual(calls[0][0],web.ROUTES[kind][1])
        for kind in ('password','refresh','SetQuickLogin','device','../../login'):
            with self.assertRaises(LoginFailure):obs.ReadOnlyWebUI(lambda:True,120,clock=lambda:0).request(kind)

    def test_bad_http_envelopes_no_raw_error_or_redirect(self):
        for body in ({'code':-1,'data':'secret'}, {'code':True,'data':{}}, {'code':0}, {'code':0,'data':[]},[], {'code':'0','data':{}}):
            with self.subTest(body=body),fake_server(body=body),self.assertRaises(LoginFailure) as caught:
                obs.ReadOnlyWebUI(lambda:True,120,clock=lambda:0).request('auth')
            self.assertNotIn('secret',str(caught.exception))
        for status,raw in ((302,b'private-url'),(200,b'x'*65537),(200,b'{"code":0,"code":0,"data":{}}')):
            with fake_server(status=status,raw=raw) as calls,self.assertRaises(LoginFailure):
                obs.ReadOnlyWebUI(lambda:True,120,clock=lambda:0).request('auth')
            self.assertEqual(len(calls),1)

    def test_request_budget_interval_and_deadline(self):
        now=[0];web=obs.ReadOnlyWebUI(lambda:True,999,clock=lambda:now[0])
        with fake_server(body={'code':0,'data':{}}) as calls:
            for i in range(12):
                now[0]=i*5;web.request('status')
                with self.assertRaises(LoginFailure):web.request('status')
            now[0]=60
            with self.assertRaises(LoginFailure):web.request('status')
            self.assertEqual(len(calls),12)
            web.request('auth')
            with self.assertRaises(LoginFailure):web.request('auth')
            now[0]=120
            with self.assertRaises(LoginFailure):web.request('info')

    def test_all_four_http_routes_and_16_request_ceiling(self):
        responses={route:([] if kind=='quick' else {}) for kind,(_,route) in obs.ReadOnlyWebUI.ROUTES.items()}
        now=[0]
        with fake_observer_server(responses) as calls:
            web=obs.ReadOnlyWebUI(lambda:True,120,clock=lambda:now[0])
            web.request('auth');web.request('quick');web.request('quick');web.request('info')
            for i in range(12):now[0]=i*5;web.request('status')
            with self.assertRaises(LoginFailure):web.request('quick')
        self.assertEqual(len(calls),16)
        self.assertEqual(set(calls),set(obs.ReadOnlyWebUI.ROUTES.values()))

    def test_slow_headers_are_bounded_and_pre_send_identity_rechecked(self):
        with fake_observer_server({'/api/auth/login':{}},delay=3.5):
            started=time.monotonic()
            with self.assertRaises(LoginFailure):obs.ReadOnlyWebUI(lambda:True,started+120).request('auth')
            self.assertLess(time.monotonic()-started,3.4)
        valid=iter([True,False])
        with fake_server(body={'code':0,'data':{}}) as calls:
            with self.assertRaises(LoginFailure):obs.ReadOnlyWebUI(lambda:next(valid),120,clock=lambda:0).request('auth',{'hash':'synthetic'})
            self.assertEqual(calls,[])

    def test_identity_lost_sends_nothing(self):
        with fake_server(body={'code':0,'data':{}}) as calls:
            with self.assertRaises(LoginFailure):obs.ReadOnlyWebUI(lambda:False,120,clock=lambda:0).request('auth',{'hash':'synthetic'})
            self.assertEqual(calls,[])

    def test_strict_classification_and_no_payload(self):
        for code in ('140022008','140022010','140022011'):
            value=obs.classify_status(dict(STATUS,loginError='快速登录失败，错误码: '+code))
            self.assertEqual(value,dict(state='verification_required',error_code=int(code)))
        value=obs.classify_status(dict(STATUS,loginError='快速登录错误 secret https://private/123456789',qrcodeurl='private'))
        self.assertEqual(value,{'state':'quick_login_failed'})
        for key in STATUS:
            bad=dict(STATUS);bad.pop(key)
            if key=='loginError':continue
            with self.assertRaises(LoginFailure):obs.classify_status(bad)
        self.assertEqual(obs.gate_state(dict(READY,online=None)),'waiting_login')
        self.assertEqual(obs.gate_state(dict(READY,stopping=True)),'waiting_login')
        self.assertEqual(obs.gate_state(dict(READY,stopping=True),paused=True),'qq_session_ready')


class ObserverFixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='登录 合成 ');self.root=Path(self.temp.name)
        self.stack=ExitStack();self.addCleanup(self.stack.close);self.addCleanup(self.temp.cleanup)
        self.mode=dict(instance_id='a'*32,phase='running')
        self.identity=(frozenset({(123,1.)}),frozenset({123}))
        self.stack.enter_context(patch.object(obs,'listener_identity',return_value=self.identity))
        self.stack.enter_context(patch.object(obs,'native_metadata',return_value={'native_scope':'unknown','native_root_fingerprints':[]}))
        self.health=dict(READY);self.now=0
    def observation(self,paused=False):
        return obs.Observation(self.root,'a'*32,'222',entries=lambda:[],mode=lambda:self.mode,
            gate_health=lambda:self.health,paused=paused,clock=lambda:self.now,sleep=self.advance)
    def advance(self,seconds):self.now+=seconds
    def token(self):
        atomic_json(self.root/obs.SECRET,dict(schema_version=1,management_token_dpapi_b64=base64.b64encode(b'cipher').decode()))
    def test_paused_diagnostics_runs_and_only_session_ready(self):
        self.token();atomic_json(self.root/'state/stop-request.json',{'instance_id':'a'*32})
        self.health['stopping']=True
        calls=[]
        def request(client,kind,payload=None):
            calls.append(kind)
            return {'Credential':'synthetic'} if kind=='auth' else [] if kind=='quick' else dict(STATUS)
        with patch.object(obs,'dpapi',return_value=b'synthetic-token'),patch.object(obs.ReadOnlyWebUI,'request',request):
            result=self.observation(paused=True).run(120,True)
        self.assertEqual(result['state'],'qq_session_ready');self.assertEqual(calls,['auth','quick','status'])
        stored=(self.root/'state/napcat-login-observation.json').read_text(encoding='utf-8')
        for secret in ('synthetic','222','qrcode','Credential'):self.assertNotIn(secret,stored)
    def test_2fa_no_challenge_and_gate_can_later_win(self):
        self.token();self.health={}
        with patch.object(obs,'dpapi',return_value=b'synthetic'),patch.object(obs.ReadOnlyWebUI,'request',return_value={'require2FA':True}) as request:
            result=self.observation().run(1,True)
        self.assertEqual(result['state'],'management_verification_required');self.assertEqual(request.call_count,1)
        self.health=dict(READY)
        self.assertEqual(self.observation().run(0)['state'],'qq_ready')
    def test_wrong_account_and_cached_missing_never_native_history(self):
        self.token()
        def request(client,kind,payload=None):
            return {'Credential':'synthetic'} if kind=='auth' else [] if kind=='quick' else dict(STATUS,isLogin=True) if kind=='status' else {'uin':'999','nickname':'secret'}
        with patch.object(obs,'dpapi',return_value=b'synthetic'),patch.object(obs.ReadOnlyWebUI,'request',request):
            result=self.observation().run(1,True)
        self.assertEqual(result['state'],'account_mismatch');self.assertEqual(result['cache_eligibility'],'missing')
        self.assertEqual(result['native_scope'],'unknown');self.assertNotIn('secret',str(result))
    def test_webui_online_but_gate_not_ready_is_transport_unavailable(self):
        self.token();self.health={}
        def request(client,kind,payload=None):
            return {'Credential':'synthetic'} if kind=='auth' else [] if kind=='quick' else dict(STATUS,isLogin=True,coreReady=True) if kind=='status' else {'uin':'222'}
        with patch.object(obs,'dpapi',return_value=b'synthetic'),patch.object(obs.ReadOnlyWebUI,'request',request):
            result=self.observation().run(1,True)
        self.assertEqual(result['state'],'transport_unavailable')
        self.assertTrue(result['account_matches'])

    def test_replacement_and_stop_cancel_without_publishing(self):
        observation=self.observation();self.mode['instance_id']='b'*32
        self.assertEqual(observation.run(0)['state'],'identity_lost')
        self.assertFalse((self.root/'state/napcat-login-observation.json').exists())
        self.mode['instance_id']='a'*32;observation=self.observation()
        atomic_json(self.root/'state/stop-request.json',{'instance_id':'a'*32})
        self.assertFalse(observation.current())
        self.assertFalse(observation.publish({'state':'qq_ready'}))
    def test_wait_does_not_hold_configuration_lock_and_stop_is_respected(self):
        self.health={}
        def stop_during_sleep(seconds):
            with configuration_lock(self.root):
                atomic_json(self.root/'state/stop-request.json',{'instance_id':'a'*32})
            self.now+=seconds
        observation=self.observation();observation.sleep=stop_during_sleep
        self.assertEqual(observation.run(120)['state'],'identity_lost')
        self.assertLess(self.now,120)
    def test_worker_replacement_never_authenticates(self):
        self.token();observation=self.observation()
        with patch.object(obs,'listener_identity',side_effect=lambda entries,component,port:self.identity if component=='gate' else None),patch.object(obs,'dpapi') as decrypt:
            self.assertEqual(observation.run(1,True)['state'],'identity_lost')
        decrypt.assert_not_called()
    def test_actual_channel_launch_pauses_before_first_child_and_omits_model(self):
        path=self.root/'config/settings.local.yaml';path.parent.mkdir()
        path.write_text(yaml.safe_dump(synthetic()),encoding='utf-8')
        napcat=self.root/'napcat';(napcat/'versions/9.9.33-52230/resources/app/napcat/config').mkdir(parents=True)
        atomic_json(self.root/'runtime/astrbot/data/cmd_config.json',{'platform_settings':{},'provider_settings':{'proactive_capability':{}}})
        gate=SimpleNamespace(upstream_token='synthetic',allowed_groups={'111'},admin_users={'333'},bot_qq='222')
        components=[]
        def spawn(argv,**kwargs):
            mode=manage.service_mode()
            marker=json.loads((self.root/'state/stop-request.json').read_text())
            self.assertEqual(marker['instance_id'],mode['instance_id'])
            components.append(argv[2]);return Mock()
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'STATE',self.root/'state/managed-processes.json'),patch.object(manage,'NAPCAT',napcat),patch.object(manage,'load_gate_config',return_value=gate),patch.object(manage,'check_port'),patch.object(manage.socket.socket,'connect_ex',return_value=0),patch.object(manage,'capture'),patch.object(manage.psutil,'Popen',side_effect=spawn),patch.object(manage,'show_status'),patch.object(manage,'status_report',return_value={}),patch('qqbot_gateway.napcat_login_client.startup_fallback') as fallback:
            result=manage._start_channel(paused=True)
        self.assertEqual(components,['astrbot','gate','napcat']);fallback.assert_not_called()
        config=json.loads((self.root/'runtime/astrbot/data/cmd_config.json').read_text(encoding='utf-8-sig'))
        self.assertFalse(config['provider_settings']['enable']);self.assertEqual(result[1],'222')

    def test_manage_observes_after_lock_and_idempotent_skips(self):
        def run(*args,**kwargs):
            with configuration_lock(self.root):pass
            return {'state':'qq_session_ready','native_root_fingerprints':['a'*64]}
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'_start_channel',return_value=('a'*32,'222')) as start,patch.object(obs.Observation,'__init__',return_value=None),patch.object(obs.Observation,'run',side_effect=run) as observe:
            result=manage.start_channel(paused=True,login_diagnostics=True)
            start.assert_called_once_with(False,True);self.assertEqual(result['state'],'qq_session_ready');self.assertNotIn('native_root_fingerprints',result)
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'_start_channel',return_value=None),patch.object(obs,'Observation') as observe:
            manage.start_channel(login_diagnostics=True,wait_login_seconds=120)
            observe.assert_not_called()
    def test_path_comparison_keeps_prior_instance_baseline(self):
        atomic_json(self.root/'state/napcat-login-observation.json',{'native_root_fingerprints':['a'*64]})
        self.health={};observation=self.observation()
        with patch.object(obs,'native_metadata',return_value={'native_scope':'external','native_root_fingerprints':['b'*64]}):
            result=observation.run(10)
        self.assertFalse(result['native_path_matches_previous']);self.assertEqual(self.now,10)
    def test_historical_status_never_echoes_raw_fields(self):
        atomic_json(self.root/'state/napcat-login-observation.json',dict(schema_version=1,instance_id='a'*32,state='verification_required',qrcodeurl='secret',error_code=123456))
        self.assertEqual(obs.historical_status(self.root,'a'*32),{'state':'verification_required','historical':True})
        self.assertIsNone(obs.historical_status(self.root,'b'*32))

    def test_current_live_state_ignores_old_observation(self):
        atomic_json(self.root/'state/napcat-login-observation.json',{'state':'qq_ready'})
        self.health=dict(READY,online=False)
        self.assertNotEqual(self.observation().run(0)['state'],'qq_ready')
        self.health=dict(READY)
        self.assertEqual(self.observation().run(0)['state'],'qq_ready')


class TokenTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.path=self.root/'config/settings.local.yaml';self.path.parent.mkdir()
        self.path.write_text(yaml.safe_dump(synthetic()),encoding='utf-8')
    def test_save_cancel_status_clear_no_plaintext(self):
        with patch.object(obs,'dpapi',return_value=b'synthetic-cipher') as dpapi:
            self.assertEqual(obs.configure_token(self.path,'set-observer-token',prompt=lambda _:''),{'state':'cancelled'})
            self.assertFalse((self.root/obs.SECRET).exists())
            self.assertEqual(obs.configure_token(self.path,'set-observer-token',prompt=lambda _:'synthetic-management-secret')['state'],'saved')
            dpapi.assert_called_once_with(b'synthetic-management-secret')
        raw=(self.root/obs.SECRET).read_bytes();self.assertNotIn(b'synthetic-management-secret',raw)
        with patch.object(obs,'dpapi',side_effect=AssertionError('status must not decrypt')):
            self.assertEqual(obs.configure_token(self.path,'observer-status'),{'state':'configured'})
        self.assertEqual(obs.configure_token(self.path,'clear-observer-token'),{'state':'cleared'})
    def test_conflict_and_bad_record_preserve_existing(self):
        def conflict(_):
            atomic_json(self.root/obs.SECRET,{'other_session':'preserved'})
            return 'synthetic'
        with patch.object(obs,'dpapi',return_value=b'cipher'),self.assertRaisesRegex(ValueError,'CONFLICT'):
            obs.configure_token(self.path,'set-observer-token',prompt=conflict)
        self.assertEqual(obs.token_status(self.root),{'state':'invalid'})
        self.assertEqual(json.loads((self.root/obs.SECRET).read_text())['other_session'],'preserved')
    def test_real_currentuser_dpapi_synthetic_only(self):
        protected=obs.dpapi(b'synthetic-token-only')
        self.assertNotIn(b'synthetic-token-only',protected)
        self.assertEqual(obs.dpapi(protected,decrypt=True),b'synthetic-token-only')
        with self.assertRaises(ValueError):obs.dpapi(b'bad-cipher',decrypt=True)


class OutputTests(unittest.TestCase):
    def test_secret_lines_only_rebuilt_events(self):
        for line in ('快速登录错误：secret token https://private/qrcode 999999999',
                     '\x1b[31m快速登录异常：private\x1b[0m',
                     '[NapCat] [WebUi] 自动快速登录失败: secret'):
            result=process_host.safe_line('napcat',line)
            self.assertEqual(result,'NAPCAT_LOGIN_EVENT event=quick_login_failed')
            self.assertIsNone(process_host.safe_line('model',line))
        self.assertEqual(process_host.safe_line('napcat','快速登录错误：快速登录失败，错误码: 140022010'),
                         'NAPCAT_LOGIN_EVENT event=verification_required code=140022010')
        self.assertIsNone(process_host.safe_line('napcat','group message 快速登录错误：private'))
    def test_host_rate_limit_never_writes_raw_lines(self):
        raw=('快速登录错误：synthetic-secret\n'*100).encode('utf-8')
        process=Mock();process.stdout=BytesIO(raw);process.wait.return_value=0
        output=StringIO()
        with patch.object(process_host.subprocess,'Popen',return_value=process),patch.object(sys,'argv',['process_host.py','napcat','--','fake']),redirect_stdout(output),self.assertRaises(SystemExit):
            process_host.main()
        value=output.getvalue();self.assertNotIn('synthetic-secret',value)
        self.assertEqual(value.count('NAPCAT_LOGIN_EVENT'),1)

    def test_overflow_tail_never_becomes_forged_event(self):
        stream=process_host.BoundedLines();self.assertEqual(list(stream.feed(b'x'*16384)),[])
        self.assertEqual(list(stream.feed(b'x'*4)),[])
        forged='[NapCat] 已通知主进程登录成功'.encode()
        self.assertEqual(list(stream.feed(forged+b'\n')),[])
        self.assertEqual(list(stream.feed(forged[:5])),[])
        lines=list(stream.feed(forged[5:]+b'\n'))
        self.assertEqual(len(lines),1);self.assertIn('login_success_hint',process_host.safe_line('napcat',lines[0]))
        self.assertLessEqual(len(stream.buffer),16384)


class OwnershipTests(unittest.TestCase):
    def test_external_pid_reuse_and_descendant_replacement(self):
        process=Mock();process.pid=10;process.create_time.return_value=1.;process.is_running.return_value=True;process.children.return_value=[]
        entry={'pid':10,'created':1.,'component':'napcat'}
        conn=SimpleNamespace(status='LISTEN',pid=10,laddr=SimpleNamespace(ip='127.0.0.1',port=6099))
        with patch.object(obs.psutil,'Process',return_value=process),patch.object(obs.psutil,'net_connections',return_value=[conn]):
            self.assertIsNotNone(obs.listener_identity([entry],'napcat',6099))
            conn.pid=20;self.assertIsNone(obs.listener_identity([entry],'napcat',6099))
            conn.pid=10;process.create_time.return_value=2.;self.assertIsNone(obs.listener_identity([entry],'napcat',6099))
    def test_external_native_paths_only_hash_no_scope_unlock(self):
        with tempfile.TemporaryDirectory() as directory:
            process=Mock();process.create_time.return_value=1.;process.open_files.return_value=[SimpleNamespace(path=str(Path(directory)/'outside/nt_qq/global/Registry20'))]
            with patch.object(obs.psutil,'Process',return_value=process):
                value=obs.native_metadata(Path(directory)/'project',[(10,1.)])
            self.assertEqual(value['native_scope'],'external');self.assertNotIn('outside',str(value));self.assertEqual(len(value['native_root_fingerprints']),1)
