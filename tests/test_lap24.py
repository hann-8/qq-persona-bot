import base64
from contextlib import ExitStack
import hashlib
import itertools
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT)]
from qqbot_gateway import napcat_login as login
from qqbot_gateway import napcat_login_client as client
from qqbot_gateway.persona import compose_persona
from qqbot_gateway.reply_plan import DEFAULTS

SECRETS = dict(qq_password=' 合成 口令 q ', webui_token=' 本地 token T ')
WAITING = dict(isLogin=False, isOffline=False, qrLoginAccepted=False, coreReady=False, loginPhase='waiting_qrcode')


class PersonaMatrix(unittest.TestCase):
    def test_all_prompt_paths_and_budget(self):
        character = (ROOT/'config/persona.md').read_text(encoding='utf-8')
        sizes = []
        for participation, mode, media, maximum in itertools.product(('mentions','free'),('single','adaptive'),(False,True),(1,2,3)):
            with self.subTest(participation=participation, mode=mode, media=media, maximum=maximum):
                output=DEFAULTS | dict(delivery_mode=mode,max_bubbles=maximum)
                args=(character,output,{'enabled':True},{'mode':participation},{'enabled':media})
                prompt=compose_persona(*args)
                effective=maximum if mode=='adaptive' else 1
                self.assertEqual(prompt.count('表达规则：'),1)
                self.assertIn(f'文字最多{effective}条只是上限，不是目标',prompt)
                self.assertEqual('才第二条' in prompt,effective>=2)
                self.assertEqual('才第三条' in prompt,effective>=3)
                self.assertIn('认真回答完整一条',prompt)
                self.assertIn('网页答复使用answer且为单条',prompt)
                self.assertNotIn('15—60',prompt)
                if media:self.assertIn('不预留图片位置',prompt)
                if mode=='single' and participation=='mentions' and not media:
                    self.assertNotIn('只输出完整JSON对象',prompt)
                sizes.append(len(prompt.encode('utf-8')))
        # Default 8K input policy still leaves room for the question and fixed overhead.
        self.assertLess(max(sizes)+1024,8192)

    def test_production_composers_use_same_inputs(self):
        import ast
        from types import SimpleNamespace
        import yaml
        settings=yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
        calls=[]
        for filename in ('scripts/configure_astrbot.py','plugins/qq_router/main.py'):
            tree=ast.parse((ROOT/filename).read_text(encoding='utf-8'))
            call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='compose_persona')
            scope=dict(ROOT=ROOT,settings=settings,compose_persona=compose_persona,
                       self=SimpleNamespace(root=ROOT,output=settings['output'],web=settings['web'],participation=settings['participation']))
            calls.append(eval(compile(ast.Expression(call),filename,'eval'),scope))
        self.assertEqual(calls[0],calls[1])


class LoginStorage(unittest.TestCase):
    def setUp(self):
        import yaml
        self.tmp=tempfile.TemporaryDirectory(prefix='LAP24 合成 ');self.root=Path(self.tmp.name)
        (self.root/'config').mkdir()
        value=yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
        value['bot']['qq']='222';value['access'].update(allowed_groups=['111'],admin_users=['333'])
        self.settings=self.root/'config/settings.local.yaml'
        self.settings.write_text(yaml.safe_dump(value),encoding='utf-8')
        self.path=self.root/login.SECRET_FILE
    def tearDown(self):self.tmp.cleanup()
    def save(self, **kwargs):
        values=iter(SECRETS.values())
        return login.configure_credentials(self.settings,'set-password',prompt=lambda _:next(values),**kwargs)
    def test_dpapi_actual_synthetic_roundtrip(self):
        if os.name!='nt':self.skipTest('Windows only')
        self.assertEqual(self.save()['state'],'saved')
        record=login.load_credentials(self.root)
        self.assertFalse(record['fallback_enabled'])
        self.assertEqual(login.decrypt_credentials(record),SECRETS)
        raw=self.path.read_text()
        for value in SECRETS.values():self.assertNotIn(value,raw)
        with patch.object(login,'dpapi',side_effect=AssertionError('status decrypted')):
            self.assertEqual(login.credential_status(self.root,'222')['state'],'configured')
        login.configure_credentials(self.settings,'clear-password');self.assertFalse(self.path.exists())
    def test_missing_disabled_and_bad_credentials(self):
        self.assertFalse(login.credential_status(self.root,'222')['present'])
        self.path.parent.mkdir();self.path.write_text('{}')
        self.assertEqual(login.credential_status(self.root,'222')['state'],'invalid')
        valid=dict(schema_version=1,bot_qq='222',fallback_enabled=False,credentials_dpapi_b64=base64.b64encode(b'x').decode())
        for key,value in (('schema_version',True),('fallback_enabled',1),('bot_qq',None),('extra','bad'),('credentials_dpapi_b64','!')):
            self.path.write_text(json.dumps(valid|{key:value}))
            with self.assertRaises(ValueError):login.load_credentials(self.root)
        self.path.write_bytes(b'x'*16385)
        with self.assertRaises(ValueError):login.load_credentials(self.root)
    def test_cancel_keeps_old(self):
        self.path.parent.mkdir();self.path.write_bytes(b'old')
        for effect in ([''],['some',''],[EOFError()],[KeyboardInterrupt()]):
            with patch('builtins.input',side_effect=AssertionError()),patch.object(login.getpass,'getpass',side_effect=effect):
                prompt=__import__('unittest').mock.Mock(side_effect=effect)
                self.assertEqual(login.configure_credentials(self.settings,'set-password',prompt=prompt)['state'],'cancelled')
                self.assertEqual(self.path.read_bytes(),b'old')
    def test_dpapi_failure_and_atomic_failure_preserve_old(self):
        self.path.parent.mkdir();self.path.write_bytes(b'old')
        for where in ('dpapi','private_atomic'):
            with patch.object(login,where,side_effect=ValueError('synthetic')):
                with self.assertRaises(ValueError):self.save()
                self.assertEqual(self.path.read_bytes(),b'old')
        with patch.object(login.os,'replace',side_effect=OSError('synthetic')):
            with self.assertRaises(OSError):login.private_atomic(self.path,{'cipher':'synthetic'})
        self.assertEqual(self.path.read_bytes(),b'old')
        self.assertEqual(list(self.path.parent.glob('.napcat-login-*')),[])
    def test_settings_and_secret_conflicts(self):
        for target in (self.settings,self.path):
            self.path.parent.mkdir(exist_ok=True);self.path.write_bytes(b'old')
            def encrypt(raw):
                target.write_bytes(target.read_bytes()+b' ')
                return b'synthetic cipher'
            with patch.object(login,'dpapi',side_effect=encrypt):
                with self.assertRaisesRegex(ValueError,'CONFLICT'):self.save()
    def test_concurrent_edit_during_fsync_preserves_external_change(self):
        self.path.parent.mkdir();self.path.write_bytes(b'old')
        with patch.object(login.os,'fsync',side_effect=lambda _:self.path.write_bytes(b'external edit')):
            with self.assertRaisesRegex(ValueError,'CONFLICT'):self.save()
        self.assertEqual(self.path.read_bytes(),b'external edit')
    def test_running_rejected_and_no_redirected_password(self):
        import psutil
        state=self.root/'state';state.mkdir()
        (state/'managed-processes.json').write_text(json.dumps([dict(pid=os.getpid(),created=psutil.Process().create_time())]))
        with self.assertRaises(ValueError):self.save()
        (state/'managed-processes.json').unlink()
        with patch.object(sys.stdin,'isatty',return_value=False):
            with self.assertRaisesRegex(ValueError,'TTY'):login.configure_credentials(self.settings,'set-password')
    def test_resource_bounds(self):
        with self.assertRaises(ValueError):login.configure_credentials(self.settings,'set-password',prompt=lambda _:'x'*4097)
        with patch.object(login,'dpapi',return_value=b'x'*20000):
            with self.assertRaises(ValueError):self.save()
        self.assertFalse(self.path.exists())
    def test_environment_case_insensitive_and_no_mutation(self):
        env={'NAPCAT_QUICK_PASSWORD':'synthetic','napcat_quick_password_md5':'synthetic','NAPCAT_QUICK_ACCOUNT':'222','KEEP':'yes'}
        self.assertEqual(login.child_environment(env),{'KEEP':'yes'});self.assertEqual(len(env),4)
    def test_identity_declaration_is_insufficient(self):
        path=self.root/'state/napcat-login-identity.json';path.parent.mkdir()
        path.write_text(json.dumps(dict(data_scope='project_only')))
        self.assertEqual(login.data_scope(self.root,self.root/'bundle'),'unverified')
        with patch.object(client,'WebUI',side_effect=AssertionError('real connection')):
            self.path.parent.mkdir();self.path.write_text(json.dumps(dict(schema_version=1,bot_qq='222',fallback_enabled=True,credentials_dpapi_b64='eA==')))
            self.assertEqual(client.startup_fallback(self.root,self.root/'bundle','a'*32,'222',entries=lambda:[],channel_ready=lambda:False),'data_unverified')

    def test_bad_ciphertext_and_wrong_account_never_authenticate(self):
        for enabled,account in ((False,'222'),(True,'444')):
            self.path.parent.mkdir(exist_ok=True)
            self.path.write_text(json.dumps(dict(schema_version=1,bot_qq=account,fallback_enabled=enabled,credentials_dpapi_b64='eA==')))
            with patch.object(client,'single_fallback',side_effect=AssertionError('authenticated')):
                self.assertEqual(client.startup_fallback(self.root,self.root/'bundle','a'*32,'222',entries=lambda:[],channel_ready=lambda:False),
                                 'disabled' if not enabled else 'account_mismatch')
        with patch.object(login,'dpapi',side_effect=ValueError('private raw failure')):
            with self.assertRaisesRegex(ValueError,'^LOGIN_DECRYPT_FAILED$'):login.decrypt_credentials(login.load_credentials(self.root))

    def test_native_identity_cross_checks_and_clear_preserves_ledger(self):
        bundle=self.root/'bundle';bundle.mkdir();data=self.root/'qq-data';data.mkdir()
        evidence=dict(qq_data_root=str(data),bundle_path=str(bundle),windows_user_sid_sha256='b'*64,evidence_method='native_path_report')
        identity=self.root/'state/napcat-login-identity.json';identity.parent.mkdir()
        identity.write_text(json.dumps(dict(schema_version=1,data_scope='project_only',**evidence)))
        self.assertEqual(login.data_scope(self.root,bundle,lambda:evidence),'project_only')
        self.assertEqual(login.data_scope(self.root,bundle,lambda:evidence|{'windows_user_sid_sha256':'c'*64}),'unverified')
        ledger=identity.parent/'napcat-login-attempts';ledger.mkdir();(ledger/'old.json').write_text('unknown')
        self.path.parent.mkdir();self.path.write_text('cipher')
        login.configure_credentials(self.settings,'clear-password')
        self.assertTrue(identity.exists());self.assertEqual((ledger/'old.json').read_text(),'unknown')

    def test_startup_environments_and_only_new_start_hook(self):
        from types import SimpleNamespace
        from scripts import manage
        from qqbot_gateway.lifecycle import atomic_json
        root=self.root;napcat=root/'napcat'
        (napcat/'versions/9.9.33-52230/resources/app/napcat/config').mkdir(parents=True)
        atomic_json(root/'runtime/astrbot/data/cmd_config.json',{'platform_settings':{},'provider_settings':{'proactive_capability':{}}})
        atomic_json(root/'state/router-ready.json',{'instance_id':'a'*32})
        gate=SimpleNamespace(upstream_token='synthetic',allowed_groups={'111'},admin_users={'333'},bot_qq='222')
        with ExitStack() as stack:
            for name,value in (('ROOT',root),('STATE',root/'state/managed-processes.json'),('NAPCAT',napcat)):
                stack.enter_context(patch.object(manage,name,value))
            stack.enter_context(patch.object(manage,'load_gate_config',return_value=gate))
            stack.enter_context(patch.object(manage,'check_port'))
            stack.enter_context(patch.object(manage.socket.socket,'connect_ex',return_value=0))
            stack.enter_context(patch.object(manage,'capture'))
            stack.enter_context(patch.object(manage,'alive',return_value=True))
            stack.enter_context(patch.object(manage.uuid,'uuid4',return_value=SimpleNamespace(hex='a'*32)))
            stack.enter_context(patch.object(manage,'show_status'))
            env=stack.enter_context(patch.dict(os.environ,{'NAPCAT_QUICK_PASSWORD':'synthetic','NAPCAT_QUICK_ACCOUNT':'222','NAPCAT_QUICK_PASSWORD_MD5':'synthetic'}))
            def prepared(*args,**kwargs):
                atomic_json(root/'state/router-ready.json',{'instance_id':'a'*32,'config_digest':kwargs['env']['QQBOT_CONFIG_DIGEST']})
                return SimpleNamespace(returncode=0)
            prepare=stack.enter_context(patch.object(manage.subprocess,'run',side_effect=prepared))
            spawn=stack.enter_context(patch.object(manage.psutil,'Popen'))
            fallback=stack.enter_context(patch.object(client,'startup_fallback',return_value='disabled'))
            manage.start_channel(full=True)
            self.assertEqual(spawn.call_count,4);fallback.assert_called_once()
            for call in [prepare.call_args,*spawn.call_args_list]:
                self.assertFalse(login.QUICK_ENV.intersection(k.upper() for k in call.kwargs['env']))
                self.assertNotIn('synthetic',str(call.args[0]))
            fallback.reset_mock()
            with patch.object(manage,'read_state',return_value=[{}]),patch.object(manage,'status_report',return_value={'process_state':'running','mode':'text'}):
                manage.start_channel(full=True)
            fallback.assert_not_called()

    def test_configuration_menu_and_cli_status_are_read_only(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from scripts import configure_bot
        from scripts.console_ui import Console
        values=iter(['5','7','','','0','0'])
        ui=Console(read=lambda _:next(values),write=lambda *a,**kw:None,interactive=False)
        with patch.object(client,'startup_fallback',side_effect=AssertionError('login')),redirect_stdout(StringIO()):
            configure_bot.menu(self.settings,ui)
            with patch.object(configure_bot,'ROOT',self.root),patch.object(sys,'argv',['configure_bot.py','napcat-login','status']):
                self.assertEqual(configure_bot.main(),0)
        self.assertFalse(self.path.exists())


class FakeWebUI:
    def __init__(self, valid, statuses, *, password=None, auth=None, info=None, fault=None):
        self.valid=valid;self.statuses=iter(statuses);self.password=password
        self.auth=auth or {'Credential':'synthetic-bearer'};self.info=info or {'uin':'222'};self.fault=fault
        self.calls=[];self.clock=lambda:0;self.deadline=0;self.credential=None
    def check(self):
        if not self.valid():raise client.LoginFailure('identity_lost')
    def request(self,kind,payload=None):
        self.check();self.calls.append((kind,payload))
        if kind=='auth':return self.auth
        if kind=='status':return next(self.statuses)
        if kind=='info':return self.info
        if self.fault:raise self.fault
        return self.password


class LoginFlow(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'state').mkdir()
        (self.root/'state/service-mode.json').write_text(json.dumps({'instance_id':'a'*32}))
        self.factory=lambda valid:FakeWebUI(valid,[WAITING,WAITING,{'isLogin':True,'coreReady':True}])
        self.web=None
    def tearDown(self):self.tmp.cleanup()
    def run_flow(self,**kwargs):
        def make(valid):self.web=self.factory(valid);return self.web
        return client.single_fallback(self.root,'a'*32,'222',valid=kwargs.get('valid',lambda:True),
            channel_ready=kwargs.get('channel',lambda:False),secrets=lambda:SECRETS,client_factory=make)
    def ledger(self):return json.loads((self.root/'state/napcat-login-attempts'/('a'*32+'.json')).read_text())
    def test_once_accepted_and_reentry_blocked(self):
        self.assertEqual(self.run_flow(),'channel_waiting')
        calls=self.web.calls
        self.assertEqual([k for k,_ in calls],['auth','status','status','password','status','info'])
        self.assertEqual(calls[0][1]['hash'],hashlib.sha256((SECRETS['webui_token']+'.napcat').encode()).hexdigest())
        self.assertEqual(calls[3][1]['passwordMd5'],hashlib.md5(SECRETS['qq_password'].encode()).hexdigest())
        self.assertEqual(self.ledger()['state'],'accepted')
        self.assertEqual(self.run_flow(),'attempt_exists');self.assertEqual(self.web.calls,[])
    def test_ledger_exists_before_post_and_failure_no_replay(self):
        class Observer(FakeWebUI):
            def request(web,kind,payload=None):
                if kind=='password':self.assertEqual(self.ledger()['state'],'attempting')
                return super().request(kind,payload)
        for failure in (client.LoginFailure('transport'),KeyboardInterrupt(),client.LoginFailure('rejected')):
            target=self.root/'state/napcat-login-attempts'/('a'*32+'.json');target.unlink(missing_ok=True)
            self.factory=lambda valid:Observer(valid,[WAITING,WAITING],fault=failure)
            expected='rejected' if isinstance(failure,client.LoginFailure) and failure.reason=='rejected' else 'unknown'
            self.assertEqual(self.run_flow(),expected)
            self.assertEqual(self.run_flow(),'attempt_exists')
    def test_verification_and_2fa(self):
        for flag in ('needCaptcha','needNewDevice'):
            target=self.root/'state/napcat-login-attempts'/('a'*32+'.json');target.unlink(missing_ok=True)
            self.factory=lambda valid:FakeWebUI(valid,[WAITING,WAITING],password={flag:True,'jumpUrl':'sensitive ignored'})
            self.assertEqual(self.run_flow(),'verification_required')
            self.assertNotIn('jumpUrl',json.dumps(self.ledger()))
        target.unlink()
        self.factory=lambda valid:FakeWebUI(valid,[],auth={'require2FA':True})
        self.assertEqual(self.run_flow(),'verification_required');self.assertEqual(len(self.web.calls),1)
    def test_missing_fields_scanned_initializing_reconnecting(self):
        for status in ({}, WAITING|{'qrLoginAccepted':True}, WAITING|{'loginPhase':'initializing'},WAITING|{'loginPhase':'reconnecting'},WAITING|{'coreReady':0}):
            self.factory=lambda valid:FakeWebUI(valid,[status])
            self.assertEqual(self.run_flow(),'waiting_login');self.assertNotIn('password',[k for k,_ in self.web.calls])
        self.factory=lambda valid:FakeWebUI(valid,[WAITING, WAITING|{'qrLoginAccepted':True}])
        self.assertEqual(self.run_flow(),'waiting_login')
    def test_account_mismatch_and_already_online(self):
        self.factory=lambda valid:FakeWebUI(valid,[{'isLogin':True,'coreReady':True}],info={'uin':'444'})
        self.assertEqual(self.run_flow(),'account_mismatch')
        self.assertEqual(self.run_flow(channel=lambda:True),'already_online');self.assertEqual(self.web.calls,[])
    def test_reservation_failure_corrupt_ledger_and_invalid_instance(self):
        with patch.object(login,'private_atomic',side_effect=OSError()):
            self.assertEqual(self.run_flow(),'unavailable')
            self.assertNotIn('password',[k for k,_ in self.web.calls])
        path=self.root/'state/napcat-login-attempts'/('a'*32+'.json');path.parent.mkdir(exist_ok=True);path.write_text('broken')
        self.assertEqual(self.run_flow(),'attempt_exists')
        with self.assertRaises(ValueError):login.Attempt(self.root,'../other','222')
    def test_identity_lost_and_stop_prevent_auth(self):
        self.assertEqual(self.run_flow(valid=lambda:False),'unavailable');self.assertEqual(self.web.calls,[])
        (self.root/'state/stop-request.json').write_text('{}')
        self.assertEqual(self.run_flow(),'unavailable');self.assertEqual(self.web.calls,[])
    def test_unconfirmed_accepted_becomes_unknown(self):
        self.factory=lambda valid:FakeWebUI(valid,[WAITING]*4)
        self.assertEqual(self.run_flow(),'unknown');self.assertEqual(self.ledger()['state'],'unknown')
        self.assertEqual(sum(k=='status' for k,_ in self.web.calls),4)
    def test_confirmed_requires_channel_and_account(self):
        states=iter([False,False,True])
        self.assertEqual(self.run_flow(channel=lambda:next(states)),'confirmed')
        self.assertEqual(self.ledger()['state'],'confirmed')
    def test_listener_requires_creation_identity(self):
        from types import SimpleNamespace
        listener=SimpleNamespace(status='LISTEN',laddr=SimpleNamespace(ip='127.0.0.1',port=6099),pid=123)
        process=__import__('unittest').mock.Mock(pid=123);process.create_time.return_value=99
        with patch('psutil.net_connections',return_value=[listener]),patch('psutil.Process',return_value=process):
            self.assertFalse(client.owned_listener([]))
            self.assertFalse(client.owned_listener([dict(component='napcat',pid=123,created=98)]))
            self.assertTrue(client.owned_listener([dict(component='napcat',pid=123,created=99)]))
        import psutil
        with patch('psutil.net_connections',return_value=[listener]),patch('psutil.Process',side_effect=[psutil.NoSuchProcess(12),process]):
            self.assertTrue(client.owned_listener([dict(component='napcat',pid=12,created=1),dict(component='napcat',pid=123,created=99)]))


if __name__=='__main__':unittest.main()
