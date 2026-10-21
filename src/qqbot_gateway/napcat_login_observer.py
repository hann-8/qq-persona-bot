"""Controller-only, bounded read-only WebUI telemetry. Never performs QQ login."""
import base64
import getpass
import hashlib
import http.client
import json
import re
import sys
import time
import warnings
from pathlib import Path

import psutil

from .config import configuration_lock, require_stopped
from .lifecycle import atomic_json
from .napcat_login import (bounded_read, strict_json, dpapi, file_digest, private_atomic)
from .napcat_login_client import DeadlineSocket, LoginFailure
from .ssh_transport import secrets_path

SECRET = 'secrets/napcat-observer.local.json'
CODES = {'0', '140022008', '140022010', '140022011'}
STATES = {'starting','qq_ready','qq_session_ready','verification_required','waiting_login',
          'account_mismatch','transport_unavailable','telemetry_unavailable','quick_login_failed',
          'management_verification_required','identity_lost'}


def load_token_record(root):
    path = secrets_path(root, SECRET)
    if not path.exists():return None
    try:
        value = strict_json(bounded_read(path, 16384))
        if (not isinstance(value, dict) or set(value) != {'schema_version','management_token_dpapi_b64'} or
            type(value['schema_version']) is not int or value['schema_version'] != 1 or
            not isinstance(value['management_token_dpapi_b64'], str) or
            not base64.b64decode(value['management_token_dpapi_b64'], validate=True)):raise ValueError()
        return value
    except (ValueError, TypeError, KeyError):raise ValueError('OBSERVER_INVALID') from None


def token_status(root):
    # Deliberately no decryption, network, or QQ password lookup.
    try:return {'state':'configured' if load_token_record(root) else 'missing'}
    except (OSError, ValueError):return {'state':'invalid'}


def configure_token(settings_path, action, *, root=None, prompt=None):
    from .config_files import read_management, management_root
    root = management_root(settings_path, root)
    if action == 'observer-status':return token_status(root)
    if action not in ('set-observer-token','clear-observer-token'):raise ValueError('OBSERVER_INVALID')
    _, digest = read_management(settings_path, root=root)
    target = secrets_path(root, SECRET)
    with configuration_lock(root):
        require_stopped(root)
        previous = file_digest(target)
        def unchanged():
            require_stopped(root)
            if (secrets_path(root, SECRET) != target or file_digest(target) != previous or
                read_management(settings_path, root=root)[1] != digest):raise ValueError('OBSERVER_CONFLICT')
        if action == 'clear-observer-token':
            unchanged();target.unlink(missing_ok=True);return {'state':'cleared'}
        if prompt is None:
            if not sys.stdin.isatty():raise ValueError('OBSERVER_TTY_REQUIRED')
            def prompt(message):
                with warnings.catch_warnings():
                    warnings.simplefilter('error', getpass.GetPassWarning)
                    try:return getpass.getpass(message)
                    except getpass.GetPassWarning:raise ValueError('OBSERVER_TTY_REQUIRED') from None
        try:
            token = prompt('NapCat管理token（回车取消，无需QQ密码）：')
            if not token:return {'state':'cancelled'}
            if not isinstance(token,str) or not 1 <= len(token.encode('utf-8')) <= 4096:raise ValueError('OBSERVER_INVALID')
            protected = dpapi(token.encode('utf-8'))
            record = dict(schema_version=1, management_token_dpapi_b64=base64.b64encode(protected).decode('ascii'))
            private_atomic(target, record, pre_replace=unchanged)
            return {'state':'saved'}
        except (EOFError, KeyboardInterrupt):return {'state':'cancelled'}


class ReadOnlyWebUI:
    ROUTES = {'auth':('POST','/api/auth/login'), 'status':('POST','/api/QQLogin/CheckLoginStatus'),
              'quick':('GET','/api/QQLogin/GetQuickLoginList'), 'info':('POST','/api/QQLogin/GetQQLoginInfo')}
    LIMITS = {'auth':1, 'status':12, 'quick':2, 'info':1}

    def __init__(self, valid, deadline, *, clock=time.monotonic):
        self.valid=valid;self.clock=clock;self.deadline=min(deadline,clock()+120)
        self.counts={};self.credential=None;self.last_status=None

    def check(self):
        if not self.valid():raise LoginFailure('identity_lost')
        if self.clock() >= self.deadline:raise LoginFailure('transport_unavailable')

    def request(self, kind, payload=None):
        self.check()
        if (kind not in self.ROUTES or self.counts.get(kind,0)>=self.LIMITS[kind] or
            sum(self.counts.values())>=16):raise LoginFailure('telemetry_unavailable')
        if kind=='status':
            if self.last_status is not None and self.clock()-self.last_status<5:raise LoginFailure('telemetry_unavailable')
            self.last_status=self.clock()
        self.counts[kind]=self.counts.get(kind,0)+1
        method, route=self.ROUTES[kind]
        end=min(self.deadline,self.clock()+3)
        connection=http.client.HTTPConnection('127.0.0.1',6099,timeout=max(.001,end-self.clock()))
        response=None
        try:
            connection.connect()
            # Recheck owner immediately before sending a credential-bearing request.
            self.check()
            connection.sock=DeadlineSocket(connection.sock,self,end)
            headers={'Content-Type':'application/json','Connection':'close'}
            if self.credential:headers['Authorization']='Bearer '+self.credential
            connection.request(method,route,body=json.dumps(payload or {}) if method=='POST' else None,headers=headers)
            response=connection.getresponse()
            if response.status!=200:raise LoginFailure('telemetry_unavailable')
            raw=bytearray()
            while True:
                self.check()
                chunk=response.read1(min(8192,65537-len(raw)))
                if not chunk:break
                raw.extend(chunk)
                if len(raw)>65536:raise LoginFailure('telemetry_unavailable')
            self.check()
            envelope=strict_json(bytes(raw))
            if (not isinstance(envelope,dict) or type(envelope.get('code')) is not int or
                envelope['code']!=0 or 'data' not in envelope):raise LoginFailure('telemetry_unavailable')
            value=envelope['data']
            if not isinstance(value,list if kind=='quick' else dict):raise LoginFailure('telemetry_unavailable')
            return value
        except LoginFailure:raise
        except (ValueError, TypeError, OSError, http.client.HTTPException, AttributeError):
            raise LoginFailure('transport_unavailable') from None
        finally:
            if response:response.close()
            connection.close()


def listener_identity(entries, component, port):
    """Freeze listener + all live recorded roots/descendants; never adopt a replacement."""
    try:
        identities=set()
        for entry in entries:
            if entry['component']!=component:continue
            process=psutil.Process(entry['pid'])
            if not process.is_running() or abs(process.create_time()-entry['created'])>=.01:continue
            identities.add((process.pid,process.create_time()))
            for child in process.children(recursive=True):
                identities.add((child.pid,child.create_time()))
        owners={c.pid for c in psutil.net_connections('tcp') if c.status=='LISTEN' and c.laddr and
                c.laddr.ip=='127.0.0.1' and c.laddr.port==port}
        if not owners or not owners.issubset({pid for pid,_ in identities}):return None
        return frozenset(identities),frozenset(owners)
    except (psutil.Error,OSError,KeyError,TypeError):return None


def native_metadata(root, identities):
    # open_files is best-effort on Windows; absence is unknown, never absence of history.
    roots=set()
    try:
        for pid,created in identities:
            process=psutil.Process(pid)
            if abs(process.create_time()-created)>=.01:return {'native_scope':'unknown','native_root_fingerprints':[]}
            for item in process.open_files():
                path=Path(item.path)
                for parent in (path,*path.parents):
                    if parent.name.lower()=='nt_qq':roots.add(parent.resolve());break
        ordered=sorted(roots,key=str)
        if not ordered or len(ordered)>4:return {'native_scope':'unknown','native_root_fingerprints':[]}
        return {'native_scope':'project' if all(p.is_relative_to(Path(root).resolve()) for p in ordered) else 'external',
                'native_root_fingerprints':[hashlib.sha256(str(p).casefold().encode('utf-8')).hexdigest() for p in ordered]}
    except (psutil.Error,OSError,ValueError):return {'native_scope':'unknown','native_root_fingerprints':[]}


def classify_status(value):
    keys=('isLogin','isOffline','qrLoginAccepted','coreReady')
    if not isinstance(value,dict) or any(type(value.get(k)) is not bool for k in keys):raise LoginFailure('telemetry_unavailable')
    phase=value.get('loginPhase')
    if not isinstance(phase,str):raise LoginFailure('telemetry_unavailable')
    error=value.get('loginError')
    result={'state':'waiting_login'}
    if error is not None and not isinstance(error,str):raise LoginFailure('telemetry_unavailable')
    code=re.fullmatch(r'快速登录失败，错误码: (0|140022008|140022010|140022011)',error or '')
    if code:result['error_code']=int(code[1])
    if (code and code[1] in CODES-{'0'}) or error in (
        '密码回退需要验证码，请在 WebUi 中继续完成验证',
        '密码回退需要新设备验证，请在 WebUi 中继续完成验证',
        '需要验证码','新设备需要扫码验证','异常设备需要验证'):
        result['state']='verification_required'
    elif error:
        result['state']='quick_login_failed' if error.startswith(('快速登录','未找到该 QQ 历史')) else 'waiting_login'
    # isLogin alone cannot establish gate readiness.
    return result


def gate_state(value, *, paused=False):
    if all(value.get(k) is True for k in ('alive','connected','online','self_id_verified')):
        if paused:return 'qq_session_ready'
        if value.get('stopping') is False:return 'qq_ready'
    return 'waiting_login'


def historical_status(root, instance):
    """Status displays a sanitized historical cause, never authenticates to refresh it."""
    try:
        value=strict_json(bounded_read(Path(root)/'state/napcat-login-observation.json',16384))
        if value.get('schema_version')!=1 or value.get('instance_id')!=instance or value.get('state') not in STATES:return None
        result={'state':value['state'],'historical':True}
        if type(value.get('observed_at')) in (int,float):result['observed_at']=value['observed_at']
        if value.get('cache_eligibility') in ('present','missing','unknown'):result['cache_eligibility']=value['cache_eligibility']
        return result
    except (OSError,ValueError,AttributeError,TypeError):return None


class Observation:
    def __init__(self, root, instance, account, *, entries, mode, gate_health, paused=False,
                 clock=time.monotonic, sleep=time.sleep):
        self.root=Path(root);self.instance=instance;self.account=account
        self.entries=entries;self.mode=mode;self.gate_health=gate_health;self.paused=paused
        self.clock=clock;self.sleep=sleep
        self.used_webui=False
        self.previous_fingerprints=[]
        try:
            previous=strict_json(bounded_read(self.root/'state/napcat-login-observation.json',16384))
            values=previous.get('native_root_fingerprints',[])
            if isinstance(values,list) and len(values)<=4 and all(isinstance(v,str) and re.fullmatch('[a-f0-9]{64}',v) for v in values):
                self.previous_fingerprints=values
        except (OSError,ValueError,AttributeError):pass
        self.marker=file_digest(self.root/'state/stop-request.json')
        self.gate_identity=listener_identity(entries(),'gate',6200)
        self.web_identity=listener_identity(entries(),'napcat',6099)

    def current(self):
        try:
            mode=self.mode()
            return (mode.get('instance_id')==self.instance and mode.get('phase')=='running' and
                    file_digest(self.root/'state/stop-request.json')==self.marker and
                    (self.paused or self.marker is None) and self.gate_identity is not None and
                    listener_identity(self.entries(),'gate',6200)==self.gate_identity and
                    (self.web_identity is None or listener_identity(self.entries(),'napcat',6099)==self.web_identity))
        except (OSError,ValueError,psutil.Error,KeyError,TypeError):return False

    def web_valid(self):
        return self.current() and self.web_identity is not None and listener_identity(self.entries(),'napcat',6099)==self.web_identity

    def publish(self, result):
        if result.get('state') not in STATES:raise ValueError('OBSERVER_INVALID')
        try:
            with configuration_lock(self.root):
                if not self.current():return False
                private_atomic(self.root/'state/napcat-login-observation.json',dict(schema_version=1,
                    instance_id=self.instance,observed_at=time.time(),source='cached_webui' if self.used_webui else 'gate',**result),
                    pre_replace=lambda: self._require_current())
                return self.current()
        except (ValueError,OSError):return False

    def _require_current(self):
        if not self.current():raise ValueError('OBSERVER_INSTANCE_CHANGED')

    def run(self, seconds, diagnostics=False):
        end=self.clock()+min(300,max(0,seconds))
        client=None;result={'state':'telemetry_unavailable','cache_eligibility':'unknown'}
        if diagnostics and self.web_valid():
            try:
                record=load_token_record(self.root)
                if record:
                    client=ReadOnlyWebUI(self.web_valid,min(end,self.clock()+120),clock=self.clock)
                    token=dpapi(base64.b64decode(record['management_token_dpapi_b64']),decrypt=True).decode('utf-8')
                    if not 1<=len(token.encode('utf-8'))<=4096:raise ValueError()
                    auth=client.request('auth',{'hash':hashlib.sha256((token+'.napcat').encode('utf-8')).hexdigest()})
                    del token
                    self.used_webui=True
                    if 'require2FA' in auth and type(auth['require2FA']) is not bool:raise LoginFailure('telemetry_unavailable')
                    if auth.get('require2FA') is True:
                        result['state']='management_verification_required';client=None
                    else:
                        credential=auth.get('Credential')
                        if not isinstance(credential,str) or not 1<=len(credential)<=8192 or any(c in credential for c in '\r\n'):raise ValueError()
                        client.credential=credential
                        quick=client.request('quick')
                        if any(not isinstance(v,dict) or not isinstance(v.get('uin'),str) for v in quick):raise ValueError()
                        result['cache_eligibility']='present' if any(v['uin']==self.account for v in quick) else 'missing'
            except LoginFailure as error:result['state']=error.reason if error.reason in STATES else 'transport_unavailable';client=None
            except (ValueError,OSError,UnicodeError):result['state']='telemetry_unavailable';client=None
        while self.current():
            if client and (client.counts.get('status',0)>=12 or self.clock()>=client.deadline):client=None
            if client:
                try:
                    status=client.request('status')
                    result.update(classify_status(status))
                    if status['isLogin'] is True and status['coreReady'] is True and status['isOffline'] is False:
                        result['state']='transport_unavailable'
                    if client.counts.get('info',0)==0 and status['isLogin'] is True:
                        info=client.request('info')
                        if not isinstance(info.get('uin'),str):raise LoginFailure('telemetry_unavailable')
                        result['account_matches']=info['uin']==self.account
                        if not result['account_matches']:result['state']='account_mismatch'
                except LoginFailure as error:
                    result['state']=error.reason if error.reason in STATES else 'transport_unavailable';client=None
            if not self.current():break
            health=self.gate_health()
            if not self.current():break
            ready=gate_state(health,paused=self.paused)
            if ready!='waiting_login' and result.get('account_matches') is not False:result['state']=ready
            if self.web_identity:
                result.update(native_metadata(self.root,self.web_identity[0]))
            else:result.update(native_scope='unknown',native_root_fingerprints=[])
            fingerprints=result.get('native_root_fingerprints',[])
            if fingerprints and self.previous_fingerprints:
                result['native_path_matches_previous']=fingerprints==self.previous_fingerprints
            if not self.publish(result):break
            if ready!='waiting_login' or self.clock()>=end: return result
            self.sleep(min(5,max(0,end-self.clock())))
        return {'state':'identity_lost'}
