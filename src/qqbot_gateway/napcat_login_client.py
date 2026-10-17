"""Bounded fixed loopback WebUI login, invoked only during a new owned startup."""
import hashlib
import http.client
import io
import json
import time

from .napcat_login import (Attempt, data_scope, decrypt_credentials,
                           load_credentials, strict_json)


class LoginFailure(Exception):
    def __init__(self, reason):self.reason = reason


class DeadlineReader(io.RawIOBase):
    def __init__(self, source, owner):
        super().__init__();self.source=source;self.owner=owner
    def readable(self):return True
    def readinto(self, buffer):
        self.owner.prepare()
        return self.source.readinto(buffer)
    def close(self):
        try:self.source.close()
        finally:super().close()


class DeadlineSocket:
    """Bound every actual recv, including HTTP headers and a trickling body."""
    def __init__(self, sock, client, end):self.sock=sock;self.client=client;self.end=end
    def prepare(self):
        self.client.check()
        remaining=self.end-self.client.clock()
        if remaining<=0:raise LoginFailure('transport')
        self.sock.settimeout(remaining)
    def sendall(self, raw):self.prepare();self.sock.sendall(raw)
    def makefile(self, mode):return io.BufferedReader(DeadlineReader(self.sock.makefile(mode,buffering=0),self))
    def close(self):self.sock.close()
    def settimeout(self, timeout):self.sock.settimeout(timeout)


class WebUI:
    ROUTES = {'auth': ('POST','/auth/login'), 'status': ('POST','/QQLogin/CheckLoginStatus'),
              'info': ('POST','/QQLogin/GetQQLoginInfo'), 'quick': ('GET','/QQLogin/GetQuickLoginList'),
              'password': ('POST','/QQLogin/PasswordLogin')}

    def __init__(self, valid, *, clock=time.monotonic):
        self.valid = valid;self.clock = clock;self.deadline = clock() + 20
        self.counts = {};self.credential = None

    def check(self):
        if not self.valid():raise LoginFailure('identity_lost')
        if self.clock() >= self.deadline:raise LoginFailure('transport')

    def request(self, kind, payload=None):
        self.check()
        limit = 4 if kind == 'status' else 1
        if kind not in self.ROUTES or self.counts.get(kind, 0) >= limit or sum(self.counts.values()) >= 8:
            raise LoginFailure('protocol')
        self.counts[kind] = self.counts.get(kind, 0) + 1
        method, route = self.ROUTES[kind]
        end = min(self.deadline, self.clock() + 3)
        connection = http.client.HTTPConnection('127.0.0.1', 6099, timeout=max(.001, end-self.clock()))
        try:
            connection.connect()
            connection.sock=DeadlineSocket(connection.sock,self,end)
            headers = {'Content-Type':'application/json', 'Connection':'close'}
            if self.credential:headers['Authorization'] = 'Bearer ' + self.credential
            connection.request(method, '/api'+route, body=json.dumps(payload or {}) if method=='POST' else None, headers=headers)
            connection.sock.settimeout(max(.001, end-self.clock()))
            response = connection.getresponse()
            if response.status != 200:raise LoginFailure('protocol')  # Includes redirects; never follow.
            raw = bytearray()
            while True:
                self.check()
                remaining = end-self.clock()
                if remaining <= 0:raise LoginFailure('transport')
                chunk = response.read1(min(8192, 65537-len(raw)))
                if not chunk:break
                raw.extend(chunk)
                if len(raw)>65536:raise LoginFailure('protocol')
            envelope = strict_json(bytes(raw))
            if (not isinstance(envelope, dict) or type(envelope.get('code')) is not int or
                    envelope['code'] != 0 or 'data' not in envelope):raise LoginFailure('rejected')
            value = envelope['data']
            if kind == 'password':
                if value is not None and not isinstance(value, dict):raise LoginFailure('protocol')
            elif kind == 'quick':
                if not isinstance(value, list):raise LoginFailure('protocol')
            elif not isinstance(value, dict):raise LoginFailure('protocol')
            return value
        except LoginFailure:raise
        except (ValueError, TypeError, OSError, http.client.HTTPException, AttributeError):
            raise LoginFailure('transport') from None
        finally:
            if 'response' in locals():response.close()
            connection.close()


def waiting(value):
    return (isinstance(value, dict) and all(type(value.get(k)) is bool and value[k] is False
            for k in ('isLogin','isOffline','qrLoginAccepted','coreReady')) and
            value.get('loginPhase') == 'waiting_qrcode')


def single_fallback(root, instance_id, account, *, valid, channel_ready, secrets,
                    client_factory=WebUI, sleep=time.sleep):
    """Secrets are lazy: only an enabled, verified new startup enters this function.

    Caller holds configuration_lock. This function never retries an HTTP request.
    """
    attempt = Attempt(root, instance_id, account)
    client = client_factory(lambda: attempt.current() and valid())
    def pause():
        end = min(client.deadline, client.clock()+1)
        while client.clock() < end:
            client.check();sleep(min(.1, end-client.clock()))
    def confirm(status):
        if (type(status.get('isLogin')) is not bool or status['isLogin'] is not True or
                status.get('coreReady') is not True):return None
        info = client.request('info')
        # uin is a protocol string. No names or other accounts escape the controller.
        if info.get('uin') != account:return 'account_mismatch'
        return 'confirmed' if channel_ready() else 'channel_waiting'
    try:
        if attempt.path.exists():return 'attempt_exists'
        client.check()
        if channel_ready():return 'already_online'
        values = secrets()
        token = values['webui_token']
        auth = client.request('auth', {'hash':hashlib.sha256((token+'.napcat').encode('utf-8')).hexdigest()})
        if 'require2FA' in auth and type(auth['require2FA']) is not bool:return 'protocol'
        if auth.get('require2FA') is True:return 'verification_required'
        credential = auth.get('Credential')
        if not isinstance(credential, str) or not credential or len(credential)>8192 or '\r' in credential or '\n' in credential:
            return 'protocol'
        client.credential = credential
        first = client.request('status')
        result = confirm(first)
        if result:return result
        if not waiting(first):return 'waiting_login'
        pause()
        second = client.request('status')
        result = confirm(second)
        if result:return result
        if not waiting(second):return 'waiting_login'
        client.check()
        if channel_ready():return 'already_online'
        if not attempt.reserve():return 'attempt_exists'
        # Reserve before the sensitive POST; unknown survives errors, worker restarts and cancellation.
        response = client.request('password', {'uin':account, 'passwordMd5':hashlib.md5(values['qq_password'].encode('utf-8')).hexdigest()})
        if response is not None:
            for key in ('needCaptcha','needNewDevice'):
                if key in response and type(response[key]) is not bool:raise LoginFailure('protocol')
            if response.get('needCaptcha') is True or response.get('needNewDevice') is True:
                attempt.write('verification_required','verification_required');return 'verification_required'
            # Success in the pinned bundle is data=null. Never interpret arbitrary challenge data as accepted.
            raise LoginFailure('protocol')
        attempt.write('accepted')
        for _ in range(2):
            pause();status = client.request('status');result = confirm(status)
            if result:
                if result == 'confirmed':attempt.write('confirmed','confirmed')
                elif result == 'channel_waiting':attempt.write('accepted','channel_waiting')
                else:attempt.write('failed','rejected')
                return result
        attempt.write('unknown','transport');return 'unknown'
    except (LoginFailure, OSError, ValueError, KeyboardInterrupt) as error:
        if attempt.claimed:
            rejected = isinstance(error, LoginFailure) and error.reason == 'rejected'
            try:attempt.write('failed' if rejected else 'unknown','rejected' if rejected else 'transport')
            except OSError:pass  # An existing attempting record still blocks replay.
            return 'rejected' if rejected else 'unknown'
        return 'unavailable'


def owned_listener(entries):
    """Positive PID + creation identity and current loopback LISTEN ownership."""
    import psutil
    try:
        owners = {c.pid for c in psutil.net_connections('tcp') if c.status == 'LISTEN' and c.laddr
                  and c.laddr.ip == '127.0.0.1' and c.laddr.port == 6099}
        if not owners:return False
        identities = set()
        for entry in entries:
            if entry['component'] != 'napcat':continue
            try:
                process = psutil.Process(entry['pid'])
                if process.is_running() and abs(process.create_time()-entry['created']) < .01:identities.add(process.pid)
            except psutil.NoSuchProcess:continue
        return owners.issubset(identities)
    except (psutil.Error, KeyError, TypeError, OSError):return False


def startup_fallback(root, bundle, instance_id, account, *, entries, channel_ready):
    """Only the newly created startup calls this. Unverified data never authenticates."""
    try:
        if channel_ready():return 'already_online'
        record = load_credentials(root)
        if record is None or not record['fallback_enabled']:return 'disabled'
        if record['bot_qq'] != account:return 'account_mismatch'
        if data_scope(root, bundle) != 'project_only':return 'data_unverified'
        if not owned_listener(entries()):return 'identity_lost'
        return single_fallback(root, instance_id, account, valid=lambda: owned_listener(entries()),
                               channel_ready=channel_ready, secrets=lambda: decrypt_credentials(record))
    except (OSError, ValueError):return 'unavailable'
