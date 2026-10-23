"""Project-owned launch contract; never discovers an upstream package layout.

The production qualification function currently rejects every Snow launch. These
specs describe our future private entry's CLI, not the upstream QQ/native loader.
"""
from dataclasses import dataclass
from pathlib import Path
import math
import re
import time

import psutil

from .config import require_configuration_lease
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

    def register(self,settings,metadata,snapshot,layout,epoch):
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
        # Check actual hashes/process identities through the same consumer after write.
        path=self.root/'state/qq-transport/runtime.local.json';atomic_json(path,record)
        from .transport_owner import RuntimeOwner
        owner=RuntimeOwner(self.root,binding,layout.node_executable,cfg['qq_executable'],process=self.process)
        if not owner.artifacts_current(settings) or not owner.registered_identity_current(binding,require_listener=False):
            raise ValueError('TRANSPORT_OWNER_INVALID')
        from .transport_owner import initialize_control_sequence
        initialize_control_sequence(self.root,binding,self.lease,clock=self.clock)
        return owner
