"""Optional controller-only login credentials. No account discovery or migration."""
import base64
import ctypes
from ctypes import wintypes
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import warnings

from .config import configuration_lock, require_stopped, qq_id
from .ssh_transport import secrets_path

SECRET_FILE = 'secrets/napcat-login.local.json'
QUICK_ENV = {'NAPCAT_QUICK_PASSWORD', 'NAPCAT_QUICK_PASSWORD_MD5', 'NAPCAT_QUICK_ACCOUNT'}


def child_environment(environment):
    return {k: v for k, v in environment.items() if k.upper() not in QUICK_ENV}


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:raise ValueError('LOGIN_INVALID')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def bounded_read(path, limit):
    with path.open('rb') as stream:raw = stream.read(limit + 1)
    if len(raw) > limit:raise ValueError('LOGIN_INVALID')
    return raw


def dpapi(raw, *, decrypt=False):
    """CurrentUser, UI forbidden; LocalFree must receive a pointer on Win64."""
    if os.name != 'nt':raise ValueError('DPAPI_UNAVAILABLE')
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    buf = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    source, target = Blob(len(raw), buf), Blob()
    library = ctypes.WinDLL('crypt32', use_last_error=True)
    api = library.CryptUnprotectData if decrypt else library.CryptProtectData
    api.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                   ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    api.restype = wintypes.BOOL
    free = ctypes.WinDLL('kernel32').LocalFree
    free.argtypes = [ctypes.c_void_p];free.restype = ctypes.c_void_p
    if not api(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise ValueError('DPAPI_UNAVAILABLE')
    try:return ctypes.string_at(target.data, target.size)
    finally:free(ctypes.cast(target.data, ctypes.c_void_p))


def load_credentials(root):
    path = secrets_path(root, SECRET_FILE)
    if not path.exists():return None
    try:
        data = strict_json(bounded_read(path, 16384))
        if (not isinstance(data, dict) or set(data) != {'schema_version','bot_qq','fallback_enabled','credentials_dpapi_b64'} or
                type(data['schema_version']) is not int or data['schema_version'] != 1 or
                not isinstance(data['bot_qq'], str) or qq_id(data['bot_qq']) != data['bot_qq'] or type(data['fallback_enabled']) is not bool or
                not isinstance(data['credentials_dpapi_b64'], str)):
            raise ValueError()
        if not base64.b64decode(data['credentials_dpapi_b64'], validate=True):raise ValueError()
        return data
    except (ValueError, TypeError, KeyError):raise ValueError('LOGIN_INVALID') from None


def decrypt_credentials(data):
    try:
        value = strict_json(dpapi(base64.b64decode(data['credentials_dpapi_b64'], validate=True), decrypt=True))
        if not isinstance(value, dict) or set(value) != {'qq_password','webui_token'}:raise ValueError()
        for secret in value.values():
            if not isinstance(secret, str) or not 1 <= len(secret.encode('utf-8')) <= 4096:raise ValueError()
        return value
    except Exception:raise ValueError('LOGIN_DECRYPT_FAILED') from None


def file_digest(path):
    return hashlib.sha256(bounded_read(path, 16384)).digest() if path.exists() else None


def private_atomic(path, value, *, pre_replace=None):
    """Temporary ciphertext stays beside target; failed replace preserves old file."""
    raw = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if len(raw) > 16384:raise ValueError('LOGIN_INVALID')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.napcat-login-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        if pre_replace:pre_replace()
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def data_scope(root, bundle, native_report=None):
    """A local declaration alone is insufficient. Native runtime evidence is required.

    No verified native path reader exists in the pinned Windows launcher yet.
    The production caller deliberately supplies no report and remains unverified.
    """
    if native_report is None:return 'unverified'
    try:
        root = Path(root).resolve()
        path = (root/'state/napcat-login-identity.json').resolve()
        if not path.is_relative_to(root/'state'):return 'unverified'
        record = strict_json(bounded_read(path, 16384))
        if (set(record) != {'schema_version','data_scope','qq_data_root','bundle_path','windows_user_sid_sha256','evidence_method'} or
                type(record['schema_version']) is not int or record['schema_version'] != 1 or
                record['data_scope'] != 'project_only' or
                record['evidence_method'] not in ('native_path_report','verified_native_launcher')):return 'unverified'
        evidence = native_report()
        location = Path(record['qq_data_root']).resolve()
        if (not location.is_dir() or not location.is_relative_to(root) or
                Path(record['bundle_path']).resolve() != Path(bundle).resolve() or
                not re.fullmatch('[a-f0-9]{64}', record['windows_user_sid_sha256']) or
                evidence != {k: record[k] for k in ('qq_data_root','bundle_path','windows_user_sid_sha256','evidence_method')}):return 'unverified'
        return 'project_only'
    except (OSError, ValueError, TypeError, KeyError):return 'unverified'


def credential_status(root, account):
    try:
        record = load_credentials(root)
        return dict(present=record is not None, enabled=bool(record and record['fallback_enabled']),
                    account_matches=bool(record and record['bot_qq'] == account), state='configured' if record else 'missing',
                    data_scope='unverified', attempt_state=attempt_status(root))
    except (ValueError, OSError):
        return dict(present=True, enabled=False, account_matches=False, state='invalid', data_scope='unverified',attempt_state=attempt_status(root))


def attempt_status(root):
    """Local status only, no decryption or authentication and no raw error output."""
    try:
        root=Path(root).resolve()
        mode=strict_json(bounded_read(root/'state/service-mode.json',16384))
        instance=mode.get('instance_id')
        if not isinstance(instance,str) or not re.fullmatch('[a-f0-9]{32}',instance):return 'unavailable'
        path=(root/'state/napcat-login-attempts'/f'{instance}.json').resolve()
        if not path.is_relative_to(root/'state/napcat-login-attempts'):return 'invalid'
        if not path.exists():return 'not_attempted'
        value=strict_json(bounded_read(path,16384))
        if (not isinstance(value,dict) or value.get('instance_id')!=instance or
                value.get('state') not in Attempt.STATES):return 'invalid'
        return value['state']
    except (OSError,ValueError,AttributeError,TypeError):return 'unavailable'


def configure_credentials(settings_path, action, *, prompt=None, confirm=None):
    """No secret arguments, redirected input, or plaintext fallback."""
    from .config import read_settings
    settings_path = Path(settings_path)
    root = settings_path.resolve().parent.parent
    settings, config_digest = read_settings(settings_path)
    account = settings['bot']['qq']
    if action == 'status':return credential_status(root, account)
    if action not in ('set-password','clear-password'):raise ValueError('LOGIN_INVALID')
    target = secrets_path(root, SECRET_FILE)
    with configuration_lock(root):
        require_stopped(root)
        previous = file_digest(target)
        def unchanged():
            require_stopped(root)
            if (secrets_path(root, SECRET_FILE) != target or
                    read_settings(settings_path)[1] != config_digest or file_digest(target) != previous):
                raise ValueError('LOGIN_CONFLICT')
        if action == 'clear-password':
            unchanged()
            target.unlink(missing_ok=True)
            return dict(state='cleared')
        if prompt is None:
            if not sys.stdin.isatty():raise ValueError('LOGIN_TTY_REQUIRED')
            def prompt(message):
                with warnings.catch_warnings():
                    warnings.simplefilter('error', getpass.GetPassWarning)
                    try:return getpass.getpass(message)
                    except getpass.GetPassWarning:raise ValueError('LOGIN_TTY_REQUIRED') from None
        try:
            password = prompt('QQ密码（回车取消）：')
            if not password:return dict(state='cancelled')
            token = prompt('项目NapCat WebUI token（回车取消）：')
            if not token:return dict(state='cancelled')
            for value in (password, token):
                if not isinstance(value, str) or len(value.encode('utf-8')) > 4096:raise ValueError('LOGIN_INVALID')
            # Saving while path capability is missing is allowed only as disabled.
            enabled = False
            scope = data_scope(root, root/'runtime/napcat/installer/NapCat.52230.Shell')
            if scope == 'project_only':enabled = (confirm or input)('启用下次启动单次回退？输入YES：') == 'YES'
            protected = dpapi(json.dumps(dict(qq_password=password, webui_token=token), ensure_ascii=False).encode('utf-8'))
            record = dict(schema_version=1, bot_qq=account, fallback_enabled=enabled,
                          credentials_dpapi_b64=base64.b64encode(protected).decode('ascii'))
            unchanged()
            private_atomic(target, record, pre_replace=unchanged)
            return dict(state='saved', enabled=enabled, data_scope=scope)
        except (KeyboardInterrupt, EOFError):return dict(state='cancelled')


class Attempt:
    """Caller owns the existing startup OS lock. Existing/corrupt records block replay."""
    STATES = {'attempting','accepted','verification_required','failed','unknown','confirmed'}
    REASONS = {'verification_required','rejected','transport','protocol','identity_lost','channel_waiting','confirmed'}

    def __init__(self, root, instance_id, account):
        if not isinstance(instance_id, str) or not re.fullmatch('[a-f0-9]{32}', instance_id):raise ValueError('LOGIN_INSTANCE_INVALID')
        self.root = Path(root).resolve();self.instance = instance_id
        self.path = self.root/'state/napcat-login-attempts'/f'{instance_id}.json'
        if self.path.resolve() != self.path:raise ValueError('LOGIN_INSTANCE_INVALID')
        self.account_digest = hashlib.sha256(account.encode('ascii')).hexdigest()
        self.claimed = False

    def current(self):
        try:
            mode = strict_json(bounded_read(self.root/'state/service-mode.json', 16384))
            return mode.get('instance_id') == self.instance and not (self.root/'state/stop-request.json').exists()
        except (OSError, ValueError, AttributeError):return False

    def reserve(self):
        if not self.current() or os.path.lexists(self.path):return False
        self.write('attempting');self.claimed = True
        return True

    def write(self, state, reason=None):
        if state not in self.STATES or reason is not None and reason not in self.REASONS:raise ValueError('LOGIN_INVALID')
        value = dict(schema_version=1, instance_id=self.instance, bot_account_sha256=self.account_digest,
                     state=state, updated_at=time.time())
        if reason:value['reason'] = reason
        private_atomic(self.path, value)
