"""Persistent, bounded recovery consumed by the gate's existing health task.

No nonce producer, process discovery, CLI, model call or automatic preparation.
"""
from pathlib import Path
import re
import time
import uuid
import psutil

from .config import configuration_lock, require_configuration_lease, require_stopped
from .lifecycle import atomic_json, stopping
from .transport_owner import read_json, binding_from_fields, owner_record, startup_unknown

AREA='state/qq-transport/'
PHASES={'grace','drain','reserved','waiting_ready','operator_required'}
REASONS={'down','disabled','unknown','drain_unknown','drain_timeout','budget','action_unknown','ready_timeout','unprepared','stopped'}


class RecoveryClosed(ValueError):pass


class RecoveryLedger:
    def __init__(self,root,*,clock=time.time):self.root=Path(root);self.clock=clock

    def _now(self):
        stamp=int(self.clock()*1000)
        if not 0<=stamp<=9007199254740991:raise RecoveryClosed('RECOVERY_CLOCK_UNKNOWN')
        return stamp

    def initialize(self,lease):
        """Explicit first stopped preparation API, for the later operator CLI."""
        require_configuration_lease(self.root,lease);require_stopped(self.root)
        if startup_unknown(self.root):raise RecoveryClosed('RECOVERY_CREATION_UNKNOWN')
        sentinel=self.root/(AREA+'recovery-prepared.local.json')
        path=self.root/(AREA+'recovery.local.json')
        if sentinel.exists() or path.exists() or (self.root/(AREA+'recovery-intent.local.json')).exists():
            raise RecoveryClosed('RECOVERY_ALREADY_PREPARED')
        stamp=self._now();generation=uuid.uuid4().hex
        # Sentinel first: partial preparation cannot later be mistaken for fresh.
        atomic_json(sentinel,dict(format='qqbot-recovery-prepared-v1',generation=generation))
        atomic_json(path,dict(format='qqbot-recovery-v1',generation=generation,clock_ms=stamp,actions=[],incident=None,interruptions=0))

    def read(self):
        try:
            sentinel=read_json(self.root,AREA+'recovery-prepared.local.json','state')
            obj=read_json(self.root,AREA+'recovery.local.json','state')
            if (set(sentinel)!={'format','generation'} or sentinel['format']!='qqbot-recovery-prepared-v1' or
                not re.fullmatch('[a-f0-9]{32}',sentinel['generation']) or
                set(obj)!={'format','generation','clock_ms','actions','incident','interruptions'} or obj['format']!='qqbot-recovery-v1' or
                obj['generation']!=sentinel['generation'] or type(obj['clock_ms']) is not int or not 0<=obj['clock_ms']<=self._now()):raise ValueError()
            if type(obj['interruptions']) is not int or not 0<=obj['interruptions']<=9007199254740991:raise ValueError()
            actions=obj['actions']
            if not isinstance(actions,list) or len(actions)>4:raise ValueError()
            for action in actions:
                if (set(action)!={'id','incident','kind','at_ms','outcome'} or not re.fullmatch('[a-f0-9]{32}',action['id']) or
                    not re.fullmatch('[a-f0-9]{32}',action['incident']) or action['kind'] not in ('snowluma','qq') or
                    type(action['at_ms']) is not int or not 0<=action['at_ms']<=obj['clock_ms'] or
                    action['outcome'] not in ('reserved','applied','unknown','recovered')):raise ValueError()
            if len({a['id'] for a in actions})!=len(actions):raise ValueError()
            if len({a['incident'] for a in actions})!=len(actions):raise ValueError()
            incident=obj['incident']
            if incident is not None:
                if (set(incident)!={'id','binding','phase','started_ms','deadline_ms','action_id','reason'} or
                    not re.fullmatch('[a-f0-9]{32}',incident['id']) or incident['phase'] not in PHASES or
                    incident['reason'] not in REASONS or type(incident['started_ms']) is not int or
                    type(incident['deadline_ms']) is not int or not 0<=incident['started_ms']<=obj['clock_ms'] or
                    incident['deadline_ms']<incident['started_ms']):raise ValueError()
                binding_from_fields(incident['binding'])
                if incident['action_id'] is not None and not any(a['id']==incident['action_id'] and a['incident']==incident['id'] for a in actions):raise ValueError()
                if incident['phase'] in ('reserved','waiting_ready') and incident['action_id'] is None:raise ValueError()
            intent_path=self.root/(AREA+'recovery-intent.local.json')
            if intent_path.exists():
                intent=read_json(self.root,AREA+'recovery-intent.local.json','state')
                if set(intent)!={'action_id','incident'} or not any(a['id']==intent['action_id'] and a['incident']==intent['incident'] for a in actions):raise ValueError()
            return obj
        except (ValueError,OSError,KeyError,TypeError,AttributeError):raise RecoveryClosed('RECOVERY_LEDGER_UNKNOWN') from None

    def write(self,obj,lease):
        require_configuration_lease(self.root,lease)
        obj['clock_ms']=self._now()
        atomic_json(self.root/(AREA+'recovery.local.json'),obj)

    def require_action(self,action_id,binding,lease):
        require_configuration_lease(self.root,lease);obj=self.read();incident=obj['incident']
        if not incident or incident['phase']!='reserved' or incident['action_id']!=action_id or incident['binding']!=binding.fields():
            raise RecoveryClosed('RECOVERY_ACTION_UNKNOWN')
        return obj

    def reserve(self,obj,kind,cfg,lease):
        require_configuration_lease(self.root,lease)
        current=self.read()
        if current!=obj or not obj['incident'] or obj['incident']['phase']!='drain' or obj['incident']['action_id'] is not None:
            raise RecoveryClosed('RECOVERY_ACTION_UNKNOWN')
        now=self._now();actions=obj['actions'];recent=[a for a in actions if now-a['at_ms']<86400000]
        # QQ replacement also creates a Node: charge both resource budgets.
        if (kind not in ('snowluma','qq') or len(recent)>=cfg['max_snowluma_per_24h'] or
            kind=='qq' and sum(a['kind']=='qq' for a in recent)>=cfg['max_qq_per_24h'] or
            actions and now-max(a['at_ms'] for a in actions)<cfg['cooldown_seconds']*1000):
            raise RecoveryClosed('RECOVERY_BUDGET')
        action_id=uuid.uuid4().hex;incident=obj['incident']
        # Intent precedes budget. If budget write fails, the unmatched intent
        # poisons reads, preventing restart from obtaining a free second attempt.
        atomic_json(self.root/(AREA+'recovery-intent.local.json'),dict(action_id=action_id,incident=incident['id']))
        obj['actions']=recent+[dict(id=action_id,incident=incident['id'],kind=kind,at_ms=now,outcome='reserved')]
        incident.update(phase='reserved',action_id=action_id)
        self.write(obj,lease)
        return action_id


class RecoverySupervisor:
    def __init__(self,monitor,cfg,actions,*,clock=time.time,ledger=None):
        self.monitor=monitor;self.gate=monitor.gate;self.cfg=cfg;self.actions=actions;self.clock=clock
        self.ledger=ledger or RecoveryLedger(self.gate.root,clock=clock)
        self.phase='observe';self.reason='down';self.loaded=False
        self.interruptions=0

    def current(self,owner=None):
        binding=(owner or self.monitor.owner).binding
        try:
            mode=read_json(self.gate.root,'state/service-mode.json','state')
            return not stopping(self.gate.root,binding.instance_id) and mode.get('instance_id')==binding.instance_id and owner_record(self.gate.root)['binding']==binding.fields()
        except (ValueError,OSError,KeyError,TypeError):return False

    def hold(self,value):
        self.gate.transport_recovery_closed=value;self.gate.channel_ready()

    def status(self):return dict(enabled=self.cfg['enabled'],phase=self.phase,operator_required=self.phase=='operator_required',interruptions=self.interruptions)

    def operator(self,obj,reason,lease):
        self.phase='operator_required';self.reason=reason;self.hold(True)
        if obj and obj['incident']:
            obj['incident'].update(phase=self.phase,reason=reason)
            action_id=obj['incident']['action_id']
            for action in obj['actions']:
                if action['id']==action_id:action['outcome']='unknown'
            self.ledger.write(obj,lease)

    async def step(self):
        if not self.cfg['enabled']:return
        if not self.current():
            self.hold(True)
            if self.phase!='operator_required':self.phase='stopped'
            return
        try:
            with configuration_lock(self.gate.root) as lease:
                obj=self.ledger.read();incident=obj['incident'];now=self.ledger._now()
                self.interruptions=obj['interruptions']
                if not self.loaded and incident and incident['phase']=='reserved':self.operator(obj,'action_unknown',lease);return
                self.loaded=True
                if incident and incident['binding']!=self.monitor.owner.binding.fields():self.operator(obj,'unknown',lease);return
                if incident and incident['phase']=='operator_required':self.hold(True);self.phase='operator_required';return
                if incident and incident['phase']=='waiting_ready' and now>=incident['deadline_ms']:
                    self.operator(obj,'ready_timeout',lease);return
                ready=self.monitor.health_ready()
                if ready:
                    if incident and incident['action_id'] is None:
                        obj['interruptions']+=1;self.interruptions=obj['interruptions']
                    if incident and incident['phase']=='waiting_ready':
                        for action in obj['actions']:
                            if action['id']==incident['action_id']:action['outcome']='recovered'
                    obj['incident']=None;self.ledger.write(obj,lease);self.phase='observe';self.hold(False);return
                self.hold(True)
                if incident is None:
                    incident=dict(id=uuid.uuid4().hex,binding=self.monitor.owner.binding.fields(),phase='grace',started_ms=now,
                        deadline_ms=now+self.cfg['down_grace_seconds']*1000,action_id=None,reason='down')
                    obj['incident']=incident;self.ledger.write(obj,lease)
                self.phase=incident['phase']
                if self.phase=='waiting_ready':
                    if now>=incident['deadline_ms']:self.operator(obj,'ready_timeout',lease)
                    return
                if self.phase=='grace':
                    if now<incident['deadline_ms']:return
                    incident.update(phase='drain',deadline_ms=now+self.cfg['drain_seconds']*1000);self.phase='drain';self.ledger.write(obj,lease)
            if not self.current():self.phase='stopped';return
            converged=await self.actions.drain(self.monitor)
            if not self.current():self.phase='stopped';return
            with configuration_lock(self.gate.root) as lease:
                obj=self.ledger.read();incident=obj['incident'];now=self.ledger._now()
                if now>=incident['deadline_ms']:self.operator(obj,'drain_timeout',lease);return
                if converged is None:self.operator(obj,'drain_unknown',lease);return
                if converged is not True:
                    if now>=incident['deadline_ms']:self.operator(obj,'drain_timeout',lease)
                    return
                kind=self.actions.choose(self.monitor,self.cfg)
                if kind not in ('snowluma','qq'):self.operator(obj,'unknown',lease);return
                action_id=self.ledger.reserve(obj,kind,self.cfg,lease)
                deadline=now+self.gate.config.transport_ready_timeout*1000
            if not self.current():self.phase='stopped';return
            await self.gate.revoke_transport_epoch()
            if not self.current():self.phase='stopped';return
            owner=await self.actions.execute(self.monitor,kind,action_id,self.ledger,deadline)
            if not self.current(owner):self.phase='stopped';return
            await self.monitor.replace_owner(owner,deadline=deadline)
            with configuration_lock(self.gate.root) as lease:
                obj=self.ledger.read();incident=obj['incident']
                incident.update(binding=owner.binding.fields(),phase='waiting_ready',deadline_ms=deadline)
                for action in obj['actions']:
                    if action['id']==action_id:action['outcome']='applied'
                self.ledger.write(obj,lease);self.phase='waiting_ready'
        except Exception:  # no upstream/OS exception text escapes; cancellation still propagates
            self.phase='operator_required';self.hold(True)
            try:
                with configuration_lock(self.gate.root) as lease:self.operator(self.ledger.read(),'action_unknown',lease)
            except (ValueError,OSError,KeyError,TypeError):pass
