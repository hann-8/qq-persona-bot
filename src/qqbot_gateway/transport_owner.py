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
from .config import configuration_lock, require_configuration_lease
from .lifecycle import atomic_json

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
    try:return strict_json(content,limit)
    except (ValueError,UnicodeError,RecursionError,OverflowError):
        raise ValueError('TRANSPORT_LOCAL_RECORD_INVALID') from None


def read_control_key(root, settings, forbidden=()):
    cfg=resolve_transport(settings)['snowluma']
    binary=read_key_reference(root,cfg['control_secret_file'])
    key=binary.hex()
    # OneBot and model tokens are in the existing independent project token file.
    tokens=read_json(root,settings['secrets_file'],'secrets')
    if not isinstance(tokens,dict):raise ValueError('TRANSPORT_CONTROL_SECRET_INVALID')
    for other in tuple(tokens.values())+tuple(forbidden):
        if isinstance(other,str) and (hmac.compare_digest(key.encode(),other.encode('utf-8')) or binary==other.encode('utf-8')):
            raise ValueError('TRANSPORT_CONTROL_SECRET_REUSED')
    return binary


def read_key_reference(root,reference):
    obj=read_json(root,reference,'secrets',4096)
    if not isinstance(obj,dict) or set(obj)!={'schema','key'} or type(obj['schema']) is not int or obj['schema']!=1:
        raise ValueError('TRANSPORT_CONTROL_SECRET_INVALID')
    key=obj['key']
    import re
    if not isinstance(key,str) or re.fullmatch('[a-f0-9]{64}',key) is None:raise ValueError('TRANSPORT_CONTROL_SECRET_INVALID')
    return bytes.fromhex(key)


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

    def component_state(self,component):
        """NoSuchProcess/reused PID proves old identity gone, never adopts it."""
        try:
            record=owner_record(self.root)
            if record['binding']!=self.binding.fields():return 'unknown'
            ident=self.binding.node if component=='snowluma' else self.binding.qq
            expected=self.node_executable if component=='snowluma' else self.qq_executable
            rows=read_json(self.root,'state/managed-processes.json','state',128*1024)
            matches=[e for e in rows if e['pid']==ident['pid']]
            if len(matches)!=1 or matches[0]['component']!=component or round(matches[0]['created']*1000)!=ident['created']:return 'unknown'
            proc=self.process(ident['pid'])
            if not proc.is_running() or round(proc.create_time()*1000)!=ident['created']:return 'exited'
            return 'owned' if Path(proc.exe()).resolve()==expected.resolve() else 'unknown'
        except psutil.NoSuchProcess:return 'exited'
        except (ValueError,OSError,KeyError,TypeError,AttributeError,psutil.Error):return 'unknown'

    def identity_current(self,binding,*,allow_stop=False):
        try:
            if binding!=self.binding or not allow_stop and stopping(self.root,binding.instance_id):return False
            mode=read_json(self.root,'state/service-mode.json','state')
            settings=loaded_settings(self.root,mode)
            if (loaded_provider(self.root,mode)!='snowluma' or mode['instance_id']!=binding.instance_id or
                sha(config_canonical(settings))!=binding.config_digest or not self.artifacts_current(settings)):return False
            return self.registered_identity_current(binding,allow_stop=allow_stop)
        except (ValueError,OSError,KeyError,TypeError,AttributeError,OverflowError,psutil.Error):return False

    def registered_identity_current(self,binding,*,allow_stop=False,require_listener=True):
        """Stop-only ownership check survives a damaged configuration snapshot.

        This weaker check never grants channel admission, bind or health readiness.
        """
        try:
            if binding!=self.binding or not allow_stop and stopping(self.root,binding.instance_id):return False
            record=owner_record(self.root)
            if (record['binding']!=binding.fields() or
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
            if not require_listener:return True  # writer registration only; never ready/commands
            node=self.process(binding.node_pid)
            listeners=[c for c in node.net_connections(kind='tcp') if c.status==psutil.CONN_LISTEN and c.laddr and c.laddr.port==binding.listener_port]
            return (len(listeners)==1 and listeners[0].laddr.ip=='127.0.0.1' and
                    getattr(listeners[0],'pid',binding.node_pid) in (None,binding.node_pid))
        except (ValueError,OSError,KeyError,TypeError,AttributeError,OverflowError,psutil.Error):return False


def binding_from_fields(fields):
    if not isinstance(fields,dict) or type(fields.get('schema')) is not int or fields['schema']!=1:
        raise ValueError('TRANSPORT_OWNER_INVALID')
    result=HealthBinding(fields['instance_id'],fields['transport_epoch'],fields['config_digest'],fields['policy_digest'],fields['build_hash'],
        fields['node']['pid'],fields['node']['created'],fields['qq']['pid'],fields['qq']['created'],fields['listener_port'])
    if result.fields()!=fields:raise ValueError('TRANSPORT_OWNER_INVALID')
    return result


def owner_record(root):
    obj=read_json(root,'state/qq-transport/runtime.local.json','state')
    base={'format','binding','node_executable','qq_executable'}
    if not isinstance(obj,dict):raise ValueError('TRANSPORT_OWNER_INVALID')
    if obj.get('format')=='qqbot-transport-owner-v2':
        if set(obj)!=base|{'control_secret_file'}:raise ValueError('TRANSPORT_OWNER_INVALID')
        checked_path(root,obj['control_secret_file'],'secrets')
    elif obj.get('format')!='qqbot-transport-owner-v1' or set(obj)!=base:raise ValueError('TRANSPORT_OWNER_INVALID')
    binding_from_fields(obj['binding'])
    checked_path(root,obj['node_executable'],'runtime');checked_path(root,obj['qq_executable'],'runtime')
    return obj


def reserve_control_sequences(root,binding,count=1,*,lease=None,clock=time.time):
    """One write-ahead issuer for gate and manager; never hold lock over network."""
    if lease is None:
        with configuration_lock(root) as held:return reserve_control_sequences(root,binding,count,lease=held,clock=clock)
    require_configuration_lease(root,lease)
    if type(count) is not int or not 1<=count<=2:raise ValueError('TRANSPORT_SEQUENCE_INVALID')
    if owner_record(root)['binding']!=binding.fields():raise ValueError('TRANSPORT_OWNER_INVALID')
    path=Path(root)/'state/qq-transport/control-sequence.local.json'
    stamp=round(clock()*1000);seq=0
    if not path.exists():raise ValueError('TRANSPORT_SEQUENCE_UNKNOWN')
    if path.exists():
        obj=read_json(root,'state/qq-transport/control-sequence.local.json','state')
        if (not isinstance(obj,dict) or set(obj)!={'binding','sequence','clock_ms'} or type(obj['sequence']) is not int or
            not 0<=obj['sequence']<=9007199254740991 or type(obj['clock_ms']) is not int or stamp<obj['clock_ms']):
            raise ValueError('TRANSPORT_SEQUENCE_UNKNOWN')
        binding_from_fields(obj['binding'])
        if obj['binding']!=binding.fields():raise ValueError('TRANSPORT_SEQUENCE_UNKNOWN')
        seq=obj['sequence']
    if seq+count>9007199254740991:raise ValueError('TRANSPORT_SEQUENCE_UNKNOWN')
    atomic_json(path,dict(binding=binding.fields(),sequence=seq+count,clock_ms=stamp))
    return tuple(range(seq+1,seq+count+1))


def read_control_sequence(root,binding,*,clock=time.time):
    obj=read_json(root,'state/qq-transport/control-sequence.local.json','state')
    if (not isinstance(obj,dict) or set(obj)!={'binding','sequence','clock_ms'} or
        type(obj['sequence']) is not int or not 0<=obj['sequence']<=9007199254740991 or
        type(obj['clock_ms']) is not int or not 0<=obj['clock_ms']<=round(clock()*1000)):
        raise ValueError('TRANSPORT_SEQUENCE_UNKNOWN')
    binding_from_fields(obj['binding'])
    if obj['binding']!=binding.fields():raise ValueError('TRANSPORT_SEQUENCE_UNKNOWN')
    return obj


def initialize_control_sequence(root,binding,lease,*,clock=time.time):
    require_configuration_lease(root,lease)
    path=Path(root)/'state/qq-transport/control-sequence.local.json';stamp=round(clock()*1000)
    if path.exists():
        obj=read_json(root,'state/qq-transport/control-sequence.local.json','state')
        if (not isinstance(obj,dict) or set(obj)!={'binding','sequence','clock_ms'} or
            type(obj['clock_ms']) is not int or stamp<obj['clock_ms'] or type(obj['sequence']) is not int or
            not 0<=obj['sequence']<=9007199254740991):raise ValueError('TRANSPORT_SEQUENCE_UNKNOWN')
        binding_from_fields(obj['binding'])
        if obj['binding']['instance_id']==binding.instance_id:raise ValueError('TRANSPORT_SEQUENCE_UNKNOWN')
    atomic_json(path,dict(binding=binding.fields(),sequence=0,clock_ms=stamp))


def replace_control_sequence(root,binding,previous,action_id,ledger,lease,*,clock=time.time):
    require_configuration_lease(root,lease)
    ledger.require_action(action_id,previous,lease)
    obj=read_control_sequence(root,previous,clock=clock)
    stamp=round(clock()*1000)
    if (not isinstance(obj,dict) or set(obj)!={'binding','sequence','clock_ms'} or
        type(obj['sequence']) is not int or not 0<=obj['sequence']<=9007199254740991 or
        type(obj['clock_ms']) is not int or not 0<=obj['clock_ms']<=stamp):raise ValueError('TRANSPORT_SEQUENCE_UNKNOWN')
    binding_from_fields(obj['binding'])
    if (obj['binding']!=previous.fields() or binding.instance_id!=previous.instance_id or
        binding.transport_epoch==previous.transport_epoch or owner_record(root)['binding']!=binding.fields()):
        raise ValueError('TRANSPORT_SEQUENCE_UNKNOWN')
    atomic_json(Path(root)/'state/qq-transport/control-sequence.local.json',dict(binding=binding.fields(),sequence=0,clock_ms=stamp))


def startup_unknown(root):
    path=Path(root)/'state/qq-transport/startup.local.json'
    if not path.exists():return False
    try:
        obj=read_json(root,'state/qq-transport/startup.local.json','state')
        return (not isinstance(obj,dict) or set(obj)!={'instance_id','component','status'} or
            obj['component'] not in ('qq_client','snowluma') or obj['status']!='recorded')
    except (ValueError,OSError,KeyError,TypeError):return True


def sign_command(binding,key,action,sequence,*,now=time.time,nonce=None):
    if action not in ('bind','drain','stop') or type(sequence) is not int or sequence<1:raise ValueError('TRANSPORT_CONTROL_INVALID')
    # Conservative 100ms floor avoids a command looking future-dated across
    # runtime clock precision. Its validity still ends 3s after this earlier time.
    issued=(int(now()*1000)//100)*100
    obj=binding.fields()|dict(domain=CONTROL_DOMAIN,action=action,seq=sequence,nonce=nonce or secrets.token_hex(32),issued_ms=issued,expires_ms=issued+3000)
    obj['mac']=hmac.new(key,canonical(obj),hashlib.sha256).hexdigest()
    return canonical(obj)


def verify_ack(content,binding,key,command):
    try:
        obj=strict_json(content);sent=strict_json(command)
        expected=binding.fields()|dict(domain=ACK_DOMAIN,action=sent['action'],seq=sent['seq'],nonce=sent['nonce'],status={'bind':'bound','drain':'draining','stop':'stopped'}[sent['action']])
        if not isinstance(obj,dict) or set(obj)!=set(expected)|{'mac'} or any(obj[k]!=v for k,v in expected.items()):return False
        return hmac.compare_digest(obj['mac'],hmac.new(key,canonical(expected),hashlib.sha256).hexdigest())
    except (ValueError,TypeError,KeyError,UnicodeError,RecursionError,OverflowError):return False


class HealthMonitor:
    def __init__(self,gate,owner,key,*,session=None,sleep=asyncio.sleep,clock=time.time,proof_clock=time.monotonic):
        self.gate,self.owner,self.key=gate,owner,key
        self.verifier=HealthVerifier(owner.binding,key,owner.identity_current,ttl=gate.config.transport_health_ttl,clock=proof_clock)
        self.session=session;self.owns_session=session is None;self.task=None;self.sequence=0
        self.sleep=sleep
        self.clock=clock
        self.proof_clock=proof_clock
        self.supervisor=None
        self.control_ack_count=0;self.control_ack_latency_ms=None
        gate.bind_transport_health(self.verifier)

    def health_ready(self):
        return bool(self.verifier.ready() and self.gate.connected and self.gate.online is True and self.gate.good is True and
            self.gate.online_at is not None and 0<=self.clock()-self.gate.online_at<self.gate.config.transport_health_ttl)

    async def replace_owner(self,owner,*,deadline=None):
        if stopping(self.owner.root,self.owner.binding.instance_id) or owner.binding.instance_id!=self.owner.binding.instance_id:
            raise ValueError('TRANSPORT_STOP_REQUESTED')
        self.verifier.invalidate();self.owner=owner
        self.verifier=HealthVerifier(owner.binding,self.key,owner.identity_current,ttl=self.gate.config.transport_health_ttl,clock=self.proof_clock)
        self.gate.bind_transport_health(self.verifier)
        deadline=deadline if deadline is not None else self.clock()*1000+self.gate.config.transport_ready_timeout*1000
        mono_deadline=time.monotonic()+max(0,(deadline-self.clock()*1000)/1000);last=self.clock()
        while True:
            now=self.clock();remaining=min((deadline-now*1000)/1000,mono_deadline-time.monotonic())
            mode=read_json(owner.root,'state/service-mode.json','state')
            if (now<last or remaining<=0 or stopping(owner.root,owner.binding.instance_id) or
                mode.get('instance_id')!=owner.binding.instance_id or owner_record(owner.root)['binding']!=owner.binding.fields()):
                raise ValueError('TRANSPORT_BIND_UNKNOWN')
            last=now
            if owner.identity_current(owner.binding):
                if self.clock()*1000>=deadline or time.monotonic()>=mono_deadline:raise ValueError('TRANSPORT_BIND_UNKNOWN')
                if await self.command('bind'):return
                if self.command_sent:raise ValueError('TRANSPORT_BIND_UNKNOWN')
            await self.sleep(min(self.gate.config.transport_health_poll,remaining))

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
        self.sequence_busy=False
        self.command_sent=False
        try:
            if not self.owner.identity_current(self.owner.binding,allow_stop=action in ('stop','drain')):return False
            if action=='bind' and stopping(self.owner.root,self.owner.binding.instance_id):return False
            self.sequence=reserve_control_sequences(self.owner.root,self.owner.binding,clock=self.clock)[0]
            body=sign_command(self.owner.binding,self.key,action,self.sequence,now=self.clock)
            self.command_sent=True
            began=time.monotonic()
            content=await self.exchange('POST','/'+action,body)
            if action!='stop' and not self.owner.identity_current(self.owner.binding):return False
            accepted=verify_ack(content,self.owner.binding,self.key,body)
            if accepted:
                self.control_ack_count=min(9007199254740991,self.control_ack_count+1)
                self.control_ack_latency_ms=max(0,min(3000,int((time.monotonic()-began)*1000)))
            return accepted
        except ValueError as error:
            self.sequence_busy=str(error)=='Configuration/start/stop operation already in progress'
            return False
        except (OSError,TimeoutError,aiohttp.ClientError):return False

    async def run(self):
        # OS-lock allocation is nonblocking. Only an allocation that sent nothing
        # may wait/retry; an uncertain bind response never triggers reinjection.
        deadline=time.monotonic()+self.gate.config.transport_ready_timeout;bound=False
        while True:
            if stopping(self.owner.root,self.owner.binding.instance_id):break
            if await self.command('bind'):bound=True;break
            if not self.sequence_busy or time.monotonic()>=deadline:break
            await getattr(self,'sleep',asyncio.sleep)(self.gate.config.transport_health_poll)
        if stopping(self.owner.root,self.owner.binding.instance_id) or not bound and self.supervisor is None:
            self.verifier.invalidate();self.gate.channel_ready();return
        while not stopping(self.owner.root,self.owner.binding.instance_id):
            await self.poll_once()
            if self.supervisor:await self.supervisor.step()
            sampler=getattr(self,'trial_sampler',None)
            if sampler:sampler.sample()
            await getattr(self,'sleep',asyncio.sleep)(self.gate.config.transport_health_poll)
        self.verifier.invalidate();self.gate.channel_ready()

    async def close(self):
        if self.task:
            self.task.cancel();await asyncio.gather(self.task,return_exceptions=True)
        self.verifier.invalidate();self.gate.channel_ready()
        if self.session and self.owns_session:await self.session.close()


def monitor_from_loaded(gate):
    mode=read_json(gate.root,'state/service-mode.json','state')
    settings=loaded_settings(gate.root,mode)
    require_runtime(gate.root,settings)  # always closed while stage-3 qualification is missing
    record=owner_record(gate.root)
    binding=binding_from_fields(record['binding'])
    owner=RuntimeOwner(gate.root,binding,record['node_executable'],record['qq_executable'])
    if not owner.identity_current(binding):raise ValueError('TRANSPORT_OWNER_INVALID')
    key=read_control_key(gate.root,settings,(gate.config.inbound_token,gate.config.upstream_token,gate.admin_token,gate.context_token))
    monitor=HealthMonitor(gate,owner,key)
    from .transport_supervisor import RecoverySupervisor
    from .transport_launch import ManagementRecovery
    monitor.supervisor=RecoverySupervisor(monitor,resolve_transport(settings)['recovery'],ManagementRecovery(gate))
    gate.transport_supervisor=monitor.supervisor
    from .transport_trial import TrialSampler
    if (gate.root/'state/qq-transport/trial-request.local.json').exists():
        request=read_json(gate.root,'state/qq-transport/trial-request.local.json','state')
        if (set(request)!={'format','source_digest','instance_id'} or request['format']!='qqbot-trial-request-v1' or
            request['instance_id'] not in (None,binding.instance_id) or request['source_digest']!=mode.get('configuration',{}).get('source_digest')):
            raise ValueError('TRIAL_REQUEST_UNKNOWN')
        monitor.trial_sampler=TrialSampler(monitor)
    return monitor


class StopControl:
    """Prepared under the writer lock; only fixed drain/stop are sent outside it."""
    exchange=HealthMonitor.exchange

    def __init__(self,owner,key,sequences,*,session=None,clock=time.time):
        self.owner=owner;self.key=key;self.sequences=sequences
        self.session=session;self.owns_session=session is None
        self.clock=clock

    async def run(self):
        results=[]
        try:
            for action,sequence in zip(('drain','stop'),self.sequences):
                if not self.owner.registered_identity_current(self.owner.binding,allow_stop=True):
                    results.append('IDENTITY_UNKNOWN');break
                body=sign_command(self.owner.binding,self.key,action,sequence,now=self.clock)
                try:
                    response=await self.exchange('POST','/'+action,body)
                    accepted=verify_ack(response,self.owner.binding,self.key,body)
                    # Stop ACK may legitimately precede process exit. A changed
                    # PID/listener during drain must never authorize a next send.
                    if action=='drain' and not self.owner.registered_identity_current(self.owner.binding,allow_stop=True):accepted=False
                    results.append('ACKED' if accepted else 'ACK_UNKNOWN')
                except (ValueError,OSError,TimeoutError,aiohttp.ClientError):results.append('ACK_UNKNOWN')
            return 'ACKED' if results==['ACKED','ACKED'] else 'ACK_UNKNOWN'
        finally:
            if self.session and self.owns_session:await self.session.close()


def prepare_stop_control(root,mode,lease,*,process=psutil.Process,session=None,clock=time.time):
    """Use frozen owner reference, never the edited disk provider/secrets path."""
    require_configuration_lease(root,lease)
    record=owner_record(root)
    if record['format']!='qqbot-transport-owner-v2':raise ValueError('TRANSPORT_CONTROL_UNAVAILABLE')
    binding=binding_from_fields(record['binding'])
    if mode.get('provider')!='snowluma' or mode.get('instance_id')!=binding.instance_id:
        raise ValueError('TRANSPORT_OWNER_INVALID')
    owner=RuntimeOwner(root,binding,record['node_executable'],record['qq_executable'],process=process)
    if not owner.registered_identity_current(binding,allow_stop=True):raise ValueError('TRANSPORT_OWNER_INVALID')
    key=read_key_reference(root,record['control_secret_file'])
    sequences=reserve_control_sequences(root,binding,2,lease=lease,clock=clock)
    return StopControl(owner,key,sequences,session=session,clock=clock)
