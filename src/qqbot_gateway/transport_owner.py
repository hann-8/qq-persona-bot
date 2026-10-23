"""Instance-bound transport ownership and bounded control consumption.

Management is the sole registry writer under configuration_lock. This monitor
only reads that registry and never adopts, discovers, injects or restarts a PID.
Private upstream execution is unavailable until its separate qualification exists.
"""
import asyncio
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import time

import aiohttp
import psutil

from .config_files import load_consumer, snapshot_environment, canonical as config_canonical, sha
from .lifecycle import stopping
from .qq_transport import checked_path, inspect_transport, resolve_transport, validate_static_proof, _file_digest
from .transport_health import HealthBinding, HealthVerifier, canonical, strict_json, LIMIT

CONTROL_DOMAIN = 'qqbot-snowluma-control-v1'
ACK_DOMAIN = 'qqbot-snowluma-control-ack-v1'


class TransportBlocked(ValueError):
    def __init__(self, codes):
        self.codes=tuple(codes)
        super().__init__('SNOWLUMA_RUNTIME_BLOCKED codes='+','.join(self.codes))


def require_runtime(root, settings):
    """Static hashes cannot authorize missing upstream wiring or native conditions."""
    report=inspect_transport(root,settings)
    # Stage 3 has not delivered a protected, qualified private runtime entry.
    # Deliberately no config/manifest boolean can turn this into production approval.
    raise TransportBlocked(tuple(report['blockers'])+('private_runtime_entry_unavailable',))


def loaded_settings(root, mode):
    try:
        instance=mode['instance_id'];metadata=mode['configuration']
        path=Path(root)/'state/config-runtime'/instance/'settings.yaml'
        return load_consumer(root,path,environ=snapshot_environment(root,path,metadata))
    except (ValueError,OSError,KeyError,TypeError):raise ValueError('TRANSPORT_LOADED_SNAPSHOT_INVALID') from None


def loaded_provider(root, mode):
    if 'provider' not in mode:return 'napcat'  # historical mode records
    if mode['provider'] not in ('napcat','snowluma'):raise ValueError('TRANSPORT_LOADED_PROVIDER_INVALID')
    settings=loaded_settings(root,mode)
    provider=resolve_transport(settings)['provider']
    if provider!=mode['provider']:raise ValueError('TRANSPORT_LOADED_PROVIDER_INVALID')
    return provider


def read_json(root, name, area, limit=16384):
    path=checked_path(root,name,area)
    if not path.is_file() or path.stat().st_size>limit:raise ValueError('TRANSPORT_LOCAL_RECORD_INVALID')
    with path.open('rb') as stream:content=stream.read(limit+1)
    return strict_json(content,limit)


def read_control_key(root, settings, forbidden=()):
    cfg=resolve_transport(settings)['snowluma']
    obj=read_json(root,cfg['control_secret_file'],'secrets',4096)
    if not isinstance(obj,dict) or set(obj)!={'schema','key'} or type(obj['schema']) is not int or obj['schema']!=1:
        raise ValueError('TRANSPORT_CONTROL_SECRET_INVALID')
    key=obj['key']
    import re
    if not isinstance(key,str) or re.fullmatch('[a-f0-9]{64}',key) is None:raise ValueError('TRANSPORT_CONTROL_SECRET_INVALID')
    binary=bytes.fromhex(key)
    # OneBot and model tokens are in the existing independent project token file.
    tokens=read_json(root,settings['secrets_file'],'secrets')
    if not isinstance(tokens,dict):raise ValueError('TRANSPORT_CONTROL_SECRET_INVALID')
    for other in tuple(tokens.values())+tuple(forbidden):
        if isinstance(other,str) and (hmac.compare_digest(key.encode(),other.encode('utf-8')) or binary==other.encode('utf-8')):
            raise ValueError('TRANSPORT_CONTROL_SECRET_REUSED')
    return binary


class RuntimeOwner:
    """Trusted binding from the unique manager, checked against actual processes."""
    def __init__(self,root,binding,node_executable,qq_executable,*,process=psutil.Process):
        if not isinstance(binding,HealthBinding):raise ValueError('TRANSPORT_OWNER_INVALID')
        self.root=Path(root).resolve();self.binding=binding;self.process=process
        self.node_executable=checked_path(root,node_executable,'runtime')
        self.qq_executable=checked_path(root,qq_executable,'runtime')
        self.artifact_witness=None

    def artifacts_current(self,settings):
        proof=read_json(self.root,resolve_transport(settings)['snowluma']['proof_file'],'state')
        private=validate_static_proof(proof)['private_build']
        if private['build_sha256']!=self.binding.build_hash or private['policy_sha256']!=self.binding.policy_digest:return False
        witness=[]
        for field,digest,limit in (('build_file','build_sha256',128*1024*1024),('policy_file','policy_sha256',1024*1024)):
            path=checked_path(self.root,private[field],'runtime');info=path.stat()
            witness.append((str(path),info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns))
            if self.artifact_witness is None and _file_digest(self.root,private[field],'runtime',limit)[0]!=private[digest]:return False
        if self.artifact_witness is None:self.artifact_witness=tuple(witness)
        return tuple(witness)==self.artifact_witness

    def identity_current(self,binding,*,allow_stop=False):
        try:
            if binding!=self.binding or not allow_stop and stopping(self.root,binding.instance_id):return False
            mode=read_json(self.root,'state/service-mode.json','state')
            settings=loaded_settings(self.root,mode)
            if (loaded_provider(self.root,mode)!='snowluma' or mode['instance_id']!=binding.instance_id or
                sha(config_canonical(settings))!=binding.config_digest or not self.artifacts_current(settings)):return False
            record=read_json(self.root,'state/qq-transport/runtime.local.json','state')
            if (not isinstance(record,dict) or set(record)!={'format','binding','node_executable','qq_executable'} or
                record['format']!='qqbot-transport-owner-v1' or record['binding']!=binding.fields() or
                checked_path(self.root,record['node_executable'],'runtime')!=self.node_executable or
                checked_path(self.root,record['qq_executable'],'runtime')!=self.qq_executable):return False
            entries=read_json(self.root,'state/managed-processes.json','state',128*1024)
            if not isinstance(entries,list):return False
            for entry in entries:
                if (not isinstance(entry,dict) or type(entry.get('pid')) is not int or
                    type(entry.get('created')) not in (int,float) or not isinstance(entry.get('component'),str)):return False
            for ident,component,exe in ((binding.node,'snowluma',self.node_executable),(binding.qq,'qq_client',self.qq_executable)):
                matches=[e for e in entries if e['pid']==ident['pid']]
                if (len(matches)!=1 or matches[0]['component']!=component or
                    round(matches[0]['created']*1000)!=ident['created']):return False
                proc=self.process(ident['pid'])
                if (not proc.is_running() or round(proc.create_time()*1000)!=ident['created'] or
                    Path(proc.exe()).resolve()!=exe.resolve()):return False
            node=self.process(binding.node_pid)
            listeners=[c for c in node.net_connections(kind='tcp') if c.status==psutil.CONN_LISTEN and c.laddr and c.laddr.port==binding.listener_port]
            return (len(listeners)==1 and listeners[0].laddr.ip=='127.0.0.1' and
                    getattr(listeners[0],'pid',binding.node_pid) in (None,binding.node_pid))
        except (ValueError,OSError,KeyError,TypeError,AttributeError,OverflowError,psutil.Error):return False


def sign_command(binding,key,action,sequence,*,now=time.time,nonce=None):
    if action not in ('bind','drain','stop') or type(sequence) is not int or sequence<1:raise ValueError('TRANSPORT_CONTROL_INVALID')
    issued=round(now()*1000)
    obj=binding.fields()|dict(domain=CONTROL_DOMAIN,action=action,seq=sequence,nonce=nonce or secrets.token_hex(32),issued_ms=issued,expires_ms=issued+3000)
    obj['mac']=hmac.new(key,canonical(obj),hashlib.sha256).hexdigest()
    return canonical(obj)


def verify_ack(content,binding,key,command):
    try:
        obj=strict_json(content);sent=strict_json(command)
        expected=binding.fields()|dict(domain=ACK_DOMAIN,action=sent['action'],seq=sent['seq'],nonce=sent['nonce'],status={'bind':'bound','drain':'draining','stop':'stopped'}[sent['action']])
        if not isinstance(obj,dict) or set(obj)!=set(expected)|{'mac'} or any(obj[k]!=v for k,v in expected.items()):return False
        return hmac.compare_digest(obj['mac'],hmac.new(key,canonical(expected),hashlib.sha256).hexdigest())
    except (ValueError,TypeError,KeyError,UnicodeError):return False


class HealthMonitor:
    def __init__(self,gate,owner,key,*,session=None):
        self.gate,self.owner,self.key=gate,owner,key
        self.verifier=HealthVerifier(owner.binding,key,owner.identity_current,ttl=gate.config.transport_health_ttl)
        self.session=session;self.owns_session=session is None;self.task=None;self.sequence=0
        gate.bind_transport_health(self.verifier)

    async def exchange(self,method,path,body=None):
        if self.session is None:self.session=aiohttp.ClientSession(trust_env=False,timeout=aiohttp.ClientTimeout(total=3))
        url=f'http://127.0.0.1:{self.owner.binding.listener_port}'+path
        async with asyncio.timeout(3):
            async with self.session.request(method,url,data=body,allow_redirects=False) as response:
                if response.status!=200 or response.content_length is not None and response.content_length>LIMIT:raise ValueError()
                data=bytearray()
                async for chunk in response.content.iter_chunked(2048):
                    data.extend(chunk)
                    if len(data)>LIMIT:raise ValueError()
                return bytes(data)

    async def poll_once(self):
        try:
            if not self.owner.identity_current(self.owner.binding):raise ValueError()
            nonce=self.verifier.challenge()
            content=await self.exchange('GET','/health?nonce='+nonce)
            if not self.owner.identity_current(self.owner.binding):raise ValueError()
            return self.gate.accept_transport_health(content)
        except (ValueError,OSError,TimeoutError,aiohttp.ClientError):
            self.verifier.invalidate();self.gate.channel_ready();return False

    async def command(self,action):
        try:
            if not self.owner.identity_current(self.owner.binding,allow_stop=action in ('stop','drain')):return False
            if action!='stop' and stopping(self.owner.root,self.owner.binding.instance_id):return False
            self.sequence+=1;body=sign_command(self.owner.binding,self.key,action,self.sequence)
            content=await self.exchange('POST','/'+action,body)
            if action!='stop' and not self.owner.identity_current(self.owner.binding):return False
            return verify_ack(content,self.owner.binding,self.key,body)
        except (ValueError,OSError,TimeoutError,aiohttp.ClientError):return False

    async def run(self):
        if stopping(self.owner.root,self.owner.binding.instance_id) or not await self.command('bind'):
            self.verifier.invalidate();self.gate.channel_ready();return
        while not stopping(self.owner.root,self.owner.binding.instance_id):
            await self.poll_once()
            await asyncio.sleep(self.gate.config.transport_health_poll)
        self.verifier.invalidate();self.gate.channel_ready()

    async def close(self):
        if self.task:
            self.task.cancel();await asyncio.gather(self.task,return_exceptions=True)
        self.verifier.invalidate();self.gate.channel_ready()
        if self.session and self.owns_session:await self.session.close()


def monitor_from_loaded(gate):
    settings=load_consumer(gate.root)
    require_runtime(gate.root,settings)  # always closed while stage-3 qualification is missing
    record=read_json(gate.root,'state/qq-transport/runtime.local.json','state')
    fields=record['binding']
    binding=HealthBinding(fields['instance_id'],fields['transport_epoch'],fields['config_digest'],fields['policy_digest'],fields['build_hash'],
        fields['node']['pid'],fields['node']['created'],fields['qq']['pid'],fields['qq']['created'],fields['listener_port'])
    owner=RuntimeOwner(gate.root,binding,record['node_executable'],record['qq_executable'])
    if not owner.identity_current(binding):raise ValueError('TRANSPORT_OWNER_INVALID')
    key=read_control_key(gate.root,settings,(gate.config.inbound_token,gate.config.upstream_token,gate.admin_token,gate.context_token))
    return HealthMonitor(gate,owner,key)
