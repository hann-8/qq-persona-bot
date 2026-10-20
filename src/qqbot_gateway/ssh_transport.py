"""Pinned SSH, one authentication, fixed loopback HTTP; no remote commands."""
import base64
import hashlib
import http.client
import io
import ipaddress
import json
from pathlib import Path
import re
import secrets
import socket
import threading
import time

from .errors import GatewayError


class ChannelReader(io.RawIOBase):
    """Preserve HTTP CRLF bytes (Paramiko ChannelFile.readline normalizes them)."""
    def __init__(self,channel):
        super().__init__();self.channel=channel
    def readable(self):return True
    def readinto(self,buffer):
        data=self.channel.recv(len(buffer));buffer[:len(data)]=data
        return len(data)


class ChannelSocket:
    def __init__(self,channel):self.channel=channel
    def sendall(self,data):self.channel.sendall(data)
    def makefile(self,mode):
        if mode!='rb':raise ValueError('Read-only HTTP response stream required')
        return io.BufferedReader(ChannelReader(self.channel))
    def close(self):
        # HTTPConnection drops its socket reference before reading will-close bodies.
        # The request's finally block (or cancellation transport.close) owns channel closure.
        pass


def secrets_path(root, value):
    root = Path(root).resolve()
    path = (root / value).resolve()
    if not path.is_relative_to((root/'secrets').resolve()) or path == root/'secrets':
        raise ValueError('Path must remain inside project secrets')
    # A junction at secrets itself must not move the trust boundary.
    if not path.is_relative_to(root/'secrets'):raise ValueError('Secrets path escapes project')
    return path


def unprotect_password(protected):
    import ctypes
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_ = [('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]
    raw = bytes.fromhex(protected)
    buf = (ctypes.c_ubyte*len(raw)).from_buffer_copy(raw)
    source, target = Blob(len(raw),buf), Blob()
    api = ctypes.windll.crypt32.CryptUnprotectData
    api.argtypes = [ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    api.restype = wintypes.BOOL
    if not api(ctypes.byref(source),None,None,None,None,1,ctypes.byref(target)):
        raise GatewayError('SSH_ACCESS_INVALID')
    try:return ctypes.string_at(target.data,target.size).decode('utf-16-le')
    finally:ctypes.windll.kernel32.LocalFree(ctypes.cast(target.data,ctypes.c_void_p))


def validate_access(root,access):
    if (not isinstance(access,dict) or not isinstance(access.get('host'),str) or
        not re.fullmatch(r'[A-Za-z0-9.:-]{1,253}',access['host']) or
        not isinstance(access.get('user'),str) or not access['user'] or
        type(access.get('port')) is not int or not 1 <= access['port'] <= 65535 or
        not isinstance(access.get('fingerprint'),str) or
        not re.fullmatch(r'SHA256:[A-Za-z0-9+/]{43}',access['fingerprint'])):raise ValueError()
    ipaddress.ip_address(access['host'])  # The existing home IP avoids unbounded OS DNS resolution.
    if bool(access.get('password_dpapi')) == bool(access.get('key_file')):raise ValueError()
    if 'password' in access:raise ValueError()
    if access.get('password_dpapi') and (not isinstance(access['password_dpapi'],str) or not re.fullmatch(r'(?:[a-fA-F0-9]{2})+',access['password_dpapi'])):raise ValueError()
    if access.get('key_file'):secrets_path(root,access['key_file'])
    return access


def load_access(root, filename):
    try:
        path = secrets_path(root,filename)
        if path.stat().st_size > 32768:raise ValueError()
        access = json.loads(path.read_text(encoding='utf-8'))
        validate_access(root,access)
        return access
    except Exception:raise GatewayError('SSH_ACCESS_INVALID') from None


def initialize_access(root, filename, *, config_guard=None):
    """Explicit local action only: copy existing DPAPI ciphertext and recorded pin."""
    from .config import configuration_lock, require_stopped
    with configuration_lock(root):
        require_stopped(root)
        if config_guard:config_guard()
        target = secrets_path(root,filename)
        if target.exists():raise ValueError('Access file already exists; preserve it')
        note = secrets_path(root,'secrets/home-5070-access.local.md').read_text(encoding='utf-8')
        if not all(re.search(pattern,note,re.M) for pattern in (r'^- 主机：(.+)$',r'^- SSH用户：(.+)$')) or '<!-- DPAPI_PASSWORD_BEGIN -->' not in note or '<!-- DPAPI_PASSWORD_END -->' not in note:raise ValueError('Invalid local initialization source')
        inventory = json.loads((Path(root)/'state/home-5070-inventory-2026-10-17.json').read_text(encoding='utf-8'))
        access = dict(host=re.search(r'^- 主机：(.+)$',note,re.M).group(1).strip(),
            user=re.search(r'^- SSH用户：(.+)$',note,re.M).group(1).strip(),port=22,
            fingerprint=inventory['ssh_server_fingerprint'],
            password_dpapi=note.split('<!-- DPAPI_PASSWORD_BEGIN -->',1)[1].split('<!-- DPAPI_PASSWORD_END -->',1)[0].strip())
        validate_access(root,access)
        target.parent.mkdir(parents=True,exist_ok=True)
        if config_guard:config_guard()
        with target.open('x',encoding='utf-8') as stream:json.dump(access,stream)
        load_access(root,filename)


class SSHTransport:
    def __init__(self, root, filename, access=None):
        self.root,self.filename = Path(root),filename
        self.access = access  # Injectable only by local verification, never HTTP input.
        self.transport = None
        self.channel = None
        self.socket = None
        self.closed = threading.Event()

    def close(self):
        self.closed.set()
        for item in (self.channel,self.transport,self.socket):
            if item is not None:item.close()

    def remaining(self, deadline, cap=10):
        remaining = deadline-time.monotonic()
        if self.closed.is_set() or remaining <= 0:raise TimeoutError()
        return min(cap,remaining)

    def connect(self, deadline):
        import paramiko
        if self.transport is not None and self.transport.is_authenticated():return
        access = self.access or load_access(self.root,self.filename)
        try:
            self.socket = socket.create_connection((access['host'],access['port']),timeout=self.remaining(deadline,5))
            self.transport = paramiko.Transport(self.socket)
            self.transport.banner_timeout = self.remaining(deadline,5)
            self.transport.auth_timeout = self.remaining(deadline,5)
            self.transport.start_client(timeout=self.remaining(deadline,5))
            key = self.transport.get_remote_server_key()
            observed = 'SHA256:'+base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip('=')
            if not secrets.compare_digest(observed,access['fingerprint']):raise GatewayError('SSH_HOST_KEY_MISMATCH')
            self.remaining(deadline)
            if access.get('key_file'):
                key = paramiko.PKey.from_path(secrets_path(self.root,access['key_file']))
                self.transport.auth_publickey(access['user'],key)
            else:
                password = unprotect_password(access['password_dpapi'])
                try:self.transport.auth_password(access['user'],password,fallback=False)
                finally:password = None
            self.remaining(deadline)
            if not self.transport.is_authenticated():raise GatewayError('SSH_AUTH_FAILED')
        except GatewayError:raise
        except paramiko.AuthenticationException:raise GatewayError('SSH_AUTH_FAILED') from None
        except Exception:raise GatewayError('SSH_UNAVAILABLE') from None

    def request(self, method, path, payload=None, *, deadline, before_send=None):
        if (method,path) not in {('GET','/api/version'),('GET','/api/tags'),('GET','/api/ps'),('POST','/api/show'),('POST','/api/chat')}:
            raise ValueError('Unsupported native endpoint')
        self.connect(deadline)
        connection = None
        try:
            self.channel = self.transport.open_channel('direct-tcpip',('127.0.0.1',11434),('127.0.0.1',0),timeout=self.remaining(deadline,5))
            self.channel.settimeout(self.remaining(deadline,120 if path == '/api/chat' else 5))
            connection = http.client.HTTPConnection('127.0.0.1',11434,timeout=self.remaining(deadline))
            connection.sock = ChannelSocket(self.channel)
            body = json.dumps(payload,ensure_ascii=False,allow_nan=False).encode('utf-8') if payload is not None else None
            if before_send:before_send()
            connection.request(method,path,body,{'Content-Type':'application/json','Connection':'close','Accept-Encoding':'identity'})
            response = connection.getresponse()
            if response.status != 200:raise GatewayError('OLLAMA_UNAVAILABLE')
            if response.getheader('Content-Encoding','identity') != 'identity':raise GatewayError('PROTOCOL_ERROR')
            length = response.getheader('Content-Length')
            if length is not None and (not length.isdecimal() or int(length)>2*1024*1024):raise GatewayError('PROTOCOL_ERROR')
            data = bytearray()
            while True:
                self.channel.settimeout(self.remaining(deadline,120 if path == '/api/chat' else 5))
                chunk = response.read(min(65536,2*1024*1024+1-len(data)))
                if not chunk:break
                data.extend(chunk)
                if len(data)>2*1024*1024:raise GatewayError('PROTOCOL_ERROR')
            self.remaining(deadline)
            if length is not None and len(data)!=int(length):raise GatewayError('PROTOCOL_ERROR')
            result = json.loads(data.decode('utf-8'))
            if not isinstance(result,dict):raise GatewayError('PROTOCOL_ERROR')
            return result
        except GatewayError:raise
        except Exception:raise GatewayError('OLLAMA_UNAVAILABLE') from None
        finally:
            if connection:connection.close()
            if self.channel:self.channel.close()
            self.channel = None
