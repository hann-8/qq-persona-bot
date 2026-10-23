"""Project-owned launch contract; never discovers an upstream package layout.

The production qualification function currently rejects every Snow launch. These
specs describe our future private entry's CLI, not the upstream QQ/native loader.
"""
from dataclasses import dataclass
from contextlib import closing
import asyncio
import os
import sqlite3
from pathlib import Path
import math
import re
import time

import psutil

from .config import require_configuration_lease, configuration_lock
from .config_files import canonical, sha, load_consumer, snapshot_environment
from .lifecycle import atomic_json, stopping
from .qq_transport import checked_path, resolve_transport, validate_static_proof
from .transport_health import HealthBinding
from .transport_owner import read_json


@dataclass(frozen=True)
class PrivateLayout:
    node_executable: str
    entry_file: str


@dataclass(frozen=True)
class LaunchSpec:
    component: str
    argv: tuple
    cwd: Path
    executable: Path


def snow_specs(root, settings, snapshot, metadata, layout):
    """Pure fixed argv construction from explicit reviewed private-entry paths."""
    root=Path(root).resolve()
    if not isinstance(layout,PrivateLayout):raise ValueError('TRANSPORT_LAYOUT_UNAVAILABLE')
    loaded=load_consumer(root,snapshot,environ=snapshot_environment(root,snapshot,metadata))
    if canonical(settings)!=canonical(loaded) or resolve_transport(loaded)['provider']!='snowluma':
        raise ValueError('TRANSPORT_LOADED_SNAPSHOT_INVALID')
    cfg=resolve_transport(loaded)['snowluma']
    proof=validate_static_proof(read_json(root,cfg['proof_file'],'state'))
    if layout.entry_file!=proof['private_build']['build_file']:raise ValueError('TRANSPORT_LAYOUT_INVALID')
    node=checked_path(root,layout.node_executable,'runtime')
    entry=checked_path(root,layout.entry_file,'runtime')
    qq=checked_path(root,cfg['qq_executable'],'runtime')
    if any(not p.is_file() for p in (node,entry,qq)) or len({node,entry,qq})!=3:
        raise ValueError('TRANSPORT_LAYOUT_INVALID')
    return (
        LaunchSpec('qq_client',(str(qq),),qq.parent,qq),
        LaunchSpec('snowluma',(str(node),str(entry),'--root',str(root),'--config',str(snapshot),
            '--owner-record',str(root/'state/qq-transport/runtime.local.json')),entry.parent,node),
    )


class OwnerWriter:
    """Only manager code in the original OS lock may mutate owner/registry.

    Creation is captured directly from the supplied Popen result. No PID may be
    imported by callers or found through a process-name/global scan.
    """
    def __init__(self,root,lease,instance,*,process=psutil.Process,clock=time.time):
        self.root=Path(root).resolve();self.lease=lease;self.instance=instance
        self.process=process;self.clock=clock;self.created={}
        if not isinstance(instance,str) or re.fullmatch('[a-f0-9]{32}',instance) is None:raise ValueError('TRANSPORT_INSTANCE_INVALID')
        self._held()

    def _held(self):
        require_configuration_lease(self.root,self.lease)
        if stopping(self.root,self.instance):raise ValueError('TRANSPORT_STOP_REQUESTED')
        mode=read_json(self.root,'state/service-mode.json','state')
        if mode.get('provider')!='snowluma' or mode.get('instance_id')!=self.instance:
            raise ValueError('TRANSPORT_OWNER_INVALID')

    def create(self,spec,launch):
        self._held()
        if not isinstance(spec,LaunchSpec) or spec.component not in ('qq_client','snowluma') or spec.component in self.created:
            raise ValueError('TRANSPORT_CREATE_INVALID')
        intent_path=self.root/'state/qq-transport/startup.local.json'
        if intent_path.exists():
            old=read_json(self.root,'state/qq-transport/startup.local.json','state')
            if not isinstance(old,dict) or set(old)!={'instance_id','component','status'} or old.get('status')!='recorded':
                raise ValueError('TRANSPORT_CREATE_UNKNOWN')
        entries_path=self.root/'state/managed-processes.json'
        entries=read_json(self.root,'state/managed-processes.json','state',128*1024) if entries_path.exists() else []
        if not isinstance(entries,list) or any(not isinstance(e,dict) or type(e.get('pid')) is not int or
            type(e.get('created')) not in (int,float) or not math.isfinite(e['created']) or not isinstance(e.get('component'),str)
            for e in entries):raise ValueError('TRANSPORT_REGISTRY_INVALID')
        if any(e.get('component') in ('qq_client','snowluma') and e.get('component')==spec.component for e in entries):
            raise ValueError('TRANSPORT_CREATE_ALREADY_REGISTERED')
        # Write-ahead intent survives failure to obtain a trustworthy create time.
        intent=dict(instance_id=self.instance,component=spec.component,status='launching')
        atomic_json(intent_path,intent)
        proc=None
        try:
            started=self.clock();proc=launch(spec)
            pid=proc.pid;created=proc.create_time()
            if (type(pid) is not int or pid<=0 or type(created) not in (int,float) or not math.isfinite(created) or
                created<started-.01 or created>self.clock()+.01):
                raise ValueError('TRANSPORT_CREATE_UNKNOWN')
            entry=dict(pid=pid,created=created,component=spec.component)
            if any(e.get('pid')==pid for e in entries):raise ValueError('TRANSPORT_CREATE_UNKNOWN')
            entries.append(entry);atomic_json(entries_path,entries)
            # Even later exe/identity failure leaves a recorded owned PID to stop.
            actual=self.process(pid)
            if (not actual.is_running() or round(actual.create_time()*1000)!=round(created*1000) or
                Path(actual.exe()).resolve()!=spec.executable.resolve()):raise ValueError('TRANSPORT_CREATE_UNKNOWN')
            self._held();self.created[spec.component]=entry
            atomic_json(intent_path,intent|dict(status='recorded'))
            return entry
        except BaseException:
            atomic_json(intent_path,intent|dict(status='unknown'))
            raise

    def register(self,settings,metadata,snapshot,layout,epoch,*,replacement=None):
        self._held()
        if set(self.created)!={'qq_client','snowluma'}:raise ValueError('TRANSPORT_OWNER_INCOMPLETE')
        specs=snow_specs(self.root,settings,snapshot,metadata,layout)
        mode=read_json(self.root,'state/service-mode.json','state')
        if mode.get('provider')!='snowluma' or mode.get('instance_id')!=self.instance or mode.get('configuration')!=metadata:
            raise ValueError('TRANSPORT_OWNER_INVALID')
        cfg=resolve_transport(settings)['snowluma'];proof=validate_static_proof(read_json(self.root,cfg['proof_file'],'state'))
        from .transport_owner import read_control_key
        read_control_key(self.root,settings)
        node=self.created['snowluma'];qq=self.created['qq_client']
        binding=HealthBinding(self.instance,epoch,sha(canonical(settings)),proof['private_build']['policy_sha256'],
            proof['private_build']['build_sha256'],node['pid'],round(node['created']*1000),qq['pid'],round(qq['created']*1000),cfg['control_port'])
        record=dict(format='qqbot-transport-owner-v2',binding=binding.fields(),node_executable=layout.node_executable,
            qq_executable=cfg['qq_executable'],control_secret_file=cfg['control_secret_file'])
        if replacement:
            previous,action_id,ledger=replacement
            ledger.require_action(action_id,previous,self.lease)
            if read_json(self.root,'state/qq-transport/runtime.local.json','state')['binding']!=previous.fields():raise ValueError('TRANSPORT_OWNER_INVALID')
        # Check actual hashes/process identities through the same consumer after write.
        path=self.root/'state/qq-transport/runtime.local.json';atomic_json(path,record)
        from .transport_owner import RuntimeOwner
        owner=RuntimeOwner(self.root,binding,layout.node_executable,cfg['qq_executable'],process=self.process)
        if not owner.artifacts_current(settings) or not owner.registered_identity_current(binding,require_listener=False):
            raise ValueError('TRANSPORT_OWNER_INVALID')
        from .transport_owner import initialize_control_sequence
        if replacement:
            from .transport_owner import replace_control_sequence
            replace_control_sequence(self.root,binding,previous,action_id,ledger,self.lease,clock=self.clock)
        else:initialize_control_sequence(self.root,binding,self.lease,clock=self.clock)
        return owner


class ManagementRecovery:
    """Automatic actions use the same manager writer and short OS-lock scopes."""
    def __init__(self,gate,*,qualify=None,qualify_qq=None,launch=None,process=psutil.Process,
                 clock=time.time,sleep=asyncio.sleep,drain_check=None,control=None):
        from .transport_owner import require_runtime
        self.gate=gate;self.root=gate.root;self.qualify=qualify or require_runtime
        self.qualify_qq=qualify_qq or self._qq_unavailable;self.launch=launch;self.process=process
        self.clock=clock;self.sleep=sleep;self.drain_check=drain_check;self.control=control

    @staticmethod
    def _qq_unavailable(*args):raise ValueError('QQ_3_OF_3_UNVERIFIED')

    def current(self,owner):
        mode=read_json(self.root,'state/service-mode.json','state')
        if stopping(self.root,owner.binding.instance_id) or mode.get('instance_id')!=owner.binding.instance_id:
            raise ValueError('TRANSPORT_STOP_REQUESTED')
        return mode

    async def drain(self,monitor):
        if self.drain_check:return await self.drain_check(monitor)
        self.current(monitor.owner)
        if self.gate.transport_pending or self.gate.admin_pending or self.gate.admin_busy:return False
        from .cleanup_identity import CleanupOwner
        if CleanupOwner(self.root).status().get('blocked') is not False:return None
        path=Path(self.root)/'state/tasks.sqlite'
        if path.exists():
            try:
                with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=1)) as db:
                    if db.execute("SELECT count(*) FROM tasks WHERE status NOT IN ('completed','failed','cancelled')").fetchone()[0]:return False
                    if db.execute("SELECT count(*) FROM delivery WHERE state NOT IN ('sent','failed') OR repair IN ('pending','history_repair_required')").fetchone()[0]:return False
            except sqlite3.Error:return None
        mode=self.current(monitor.owner)
        if mode.get('mode')=='channel_only':return True
        # Inspect only registered model PIDs/listeners, never a global scan.
        rows=read_json(self.root,'state/managed-processes.json','state',128*1024)
        owned=None
        for row in rows:
            if row['component']!='model':continue
            try:
                proc=self.process(row['pid'])
                if not proc.is_running() or round(proc.create_time()*1000)!=round(row['created']*1000):continue
                if any(c.status==psutil.CONN_LISTEN and c.laddr and c.laddr.ip=='127.0.0.1' and c.laddr.port==8765 for c in proc.net_connections(kind='tcp')):owned=row
            except psutil.Error:return None
        if not owned:return None
        import aiohttp
        from .transport_health import strict_json
        try:
            async with aiohttp.ClientSession(trust_env=False,timeout=aiohttp.ClientTimeout(total=1)) as session:
                async with session.get('http://127.0.0.1:8765/health',allow_redirects=False) as response:
                    if response.status!=200:return None
                    content=await response.content.read(16385)
                    obj=strict_json(content,16384)
            if not isinstance(obj,dict):return None
            cleanup=obj.get('cli_cleanup',{})
            if obj.get('alive') is not True or obj.get('remote_result_unknown') is not False:return None
            if type(obj.get('active')) is not bool or type(obj.get('queue')) is not int or not 0<=obj['queue']<=10000:return None
            if obj['active'] or obj['queue']!=0:return False
            if obj.get('backend')=='codebuddy_cli' and (not isinstance(cleanup,dict) or cleanup.get('blocked') is not False or cleanup.get('coverage')!='job_complete' or cleanup.get('cleanup_outcome')!='observed_empty'):return None
            if obj.get('backend') not in ('codebuddy_cli','ollama_ssh'):return None
            proc=self.process(owned['pid'])
            if not proc.is_running() or round(proc.create_time()*1000)!=round(owned['created']*1000):return None
            if not any(c.status==psutil.CONN_LISTEN and c.laddr and c.laddr.ip=='127.0.0.1' and c.laddr.port==8765 for c in proc.net_connections(kind='tcp')):return None
            self.current(monitor.owner);return True
        except (ValueError,OSError,TimeoutError,aiohttp.ClientError,psutil.Error):return None

    def choose(self,monitor,cfg):
        owner=monitor.owner;qq=owner.component_state('qq_client');node=owner.component_state('snowluma')
        if qq=='exited':return 'qq' if cfg['allow_qq_restart'] else None
        if qq!='owned' or node=='unknown':return None
        if node=='exited':return 'snowluma'
        obs=monitor.verifier.observation if monitor.verifier.trusted else None
        if not obs:return None
        stalled=obs['rx_watch_armed'] and (not obs['receive_healthy'] or obs['last_rx_age_ms']>105000)
        if stalled and cfg['allow_qq_restart']:return 'qq'
        if stalled or not obs['pipe_connected']:return 'snowluma'
        if (obs['rx_watch_armed'] and obs['receive_healthy'] and obs['outbound_healthy'] and
            obs['account_match'] and obs['logged_in'] and
            (not self.gate.connected or self.gate.online is False or self.gate.good is False)):return 'snowluma'
        return None

    async def execute(self,monitor,kind,action_id,ledger,deadline):
        from .transport_owner import loaded_settings, prepare_stop_control, read_control_sequence
        owner=monitor.owner
        def current():
            value=self.current(owner)
            if self.clock()*1000>=deadline:raise ValueError('TRANSPORT_READY_TIMEOUT')
            return value
        mode=current();settings=loaded_settings(self.root,mode)
        layout=self.qualify(self.root,settings)  # production still always closed
        if kind=='qq':self.qualify_qq(self.root,owner)
        if not isinstance(layout,PrivateLayout):raise ValueError('TRANSPORT_LAYOUT_UNAVAILABLE')
        if not owner.artifacts_current(settings):raise ValueError('TRANSPORT_OWNER_INVALID')
        node=owner.component_state('snowluma');qq=owner.component_state('qq_client')
        if node=='unknown' or qq not in (('owned','exited') if kind=='qq' else ('owned',)):raise ValueError('TRANSPORT_OWNER_INVALID')
        with configuration_lock(self.root) as lease:
            current();ledger.require_action(action_id,owner.binding,lease)
            read_control_sequence(self.root,owner.binding,clock=self.clock)
            control=prepare_stop_control(self.root,mode,lease,process=self.process,clock=self.clock) if node=='owned' else None
        if control:
            if self.control:result=await self.control(control)
            else:result=await control.run()
            if result!='ACKED':raise ValueError('TRANSPORT_DRAIN_UNKNOWN')
        if await self.drain(monitor) is not True:raise ValueError('TRANSPORT_DRAIN_UNKNOWN')
        targets=('snowluma','qq_client') if kind=='qq' else ('snowluma',)
        for component in targets:
            with configuration_lock(self.root) as lease:
                current();ledger.require_action(action_id,owner.binding,lease)
                state=owner.component_state(component)
                if state=='unknown':raise ValueError('TRANSPORT_OWNER_INVALID')
                if state=='owned':
                    ident=owner.binding.node if component=='snowluma' else owner.binding.qq
                    self.process(ident['pid']).terminate()
            while owner.component_state(component)!='exited':
                current()
                if self.clock()*1000>=deadline:raise ValueError('TRANSPORT_EXIT_UNKNOWN')
                await self.sleep(.1)
        with configuration_lock(self.root) as lease:
            current();ledger.require_action(action_id,owner.binding,lease)
            rows=read_json(self.root,'state/managed-processes.json','state',128*1024)
            removed={owner.binding.node_pid}|({owner.binding.qq_pid} if kind=='qq' else set())
            if any(owner.component_state(c)!='exited' for c in targets):raise ValueError('TRANSPORT_EXIT_UNKNOWN')
            atomic_json(Path(self.root)/'state/managed-processes.json',[r for r in rows if r['pid'] not in removed])
            writer=OwnerWriter(self.root,lease,owner.binding.instance_id,process=self.process,clock=self.clock)
            if kind=='snowluma':writer.created['qq_client']=next(r for r in rows if r['pid']==owner.binding.qq_pid)
            snapshot=Path(self.root)/'state/config-runtime'/owner.binding.instance_id/'settings.yaml'
            specs=snow_specs(self.root,settings,snapshot,mode['configuration'],layout)
            from scripts.manage import _launch_snow_component, _snow_environment
            from .napcat_login import child_environment
            env=child_environment(os.environ);env.update(snapshot_environment(self.root,snapshot,mode['configuration']))
            env.update(PYTHONPATH=str(Path(self.root)/'src'),PYTHONUTF8='1');env=_snow_environment(env)
            for spec in specs:
                if spec.component not in targets:continue
                current();ledger.require_action(action_id,owner.binding,lease)
                writer.create(spec,lambda item:(self.launch or _launch_snow_component)(item,env))
            epoch=__import__('secrets').token_hex(32)
            return writer.register(settings,mode['configuration'],snapshot,layout,epoch,replacement=(owner.binding,action_id,ledger))
