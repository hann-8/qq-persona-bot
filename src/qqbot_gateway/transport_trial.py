"""Bounded metadata sampling owned by the existing gate health task, no extra IO client."""
import hashlib
import json
import os
import re
from pathlib import Path
import time

from .config_files import safe_mkdir, plain_path
from .lifecycle import atomic_json
from .transport_owner import read_json

AREA='state/qq-transport/'
LIMIT=16*1024*1024
RETENTION=14*86400


def _default():
    return dict(format='qqbot-trial-v1',last=0,start=None,fingerprint=None,segments=0,
        interruptions=0,unknown=0,continuous_seconds=0,samples=0,latest=None)


def _validate(obj):
    if not isinstance(obj,dict) or set(obj)!=set(_default()) or obj['format']!='qqbot-trial-v1':raise ValueError()
    for key in ('last','segments','interruptions','unknown','continuous_seconds','samples'):
        if type(obj[key]) is not int or not 0<=obj[key]<=9007199254740991:raise ValueError()
    if obj['fingerprint'] is not None and (not isinstance(obj['fingerprint'],str) or not re.fullmatch('[a-f0-9]{64}',obj['fingerprint'])):raise ValueError()
    if obj['start'] is not None and (type(obj['start']) is not int or not 0<=obj['start']<=obj['last'] or obj['continuous_seconds']!=obj['last']-obj['start']):raise ValueError()
    if obj['start'] is None and obj['continuous_seconds']!=0:raise ValueError()
    row=obj['latest']
    if row is None and (obj['samples']!=0 or obj['start'] is not None):raise ValueError()
    if row is not None:
        if not isinstance(row,dict) or set(row)!={'t','ready','unknown','rss_handles','metadata_bytes','armed','pipe','online','good','health_seq','control_acks','ack_ms','recoveries','operator','send_acked','send_failed','send_unknown','send_ms'}:raise ValueError()
        for key in ('ready','unknown','armed','pipe','online','good','operator'):
            if type(row[key]) is not bool:raise ValueError()
        for key in ('t','health_seq','control_acks','recoveries','send_acked','send_failed','send_unknown'):
            if type(row[key]) is not int or not 0<=row[key]<=9007199254740991:raise ValueError()
        if row['t']>obj['last']:raise ValueError()
        if obj['start'] is not None and (not row['ready'] or row['unknown'] or row['t']!=obj['last'] or obj['fingerprint'] is None or obj['segments']==0):raise ValueError()
        if row['rss_handles'] is not None and (not isinstance(row['rss_handles'],list) or len(row['rss_handles'])!=4 or any(type(v) is not int or not 0<=v<=9007199254740991 for v in row['rss_handles'])):raise ValueError()
        if row['metadata_bytes'] is not None and (type(row['metadata_bytes']) is not int or not 0<=row['metadata_bytes']<=9007199254740991):raise ValueError()
        if row['ack_ms'] is not None and (type(row['ack_ms']) is not int or not 0<=row['ack_ms']<=3000):raise ValueError()
        if row['send_ms'] is not None and (type(row['send_ms']) is not int or not 0<=row['send_ms']<=15000):raise ValueError()
    return obj


def status(root,*,clock=time.time):
    path=Path(root)/(AREA+'trial.local.json')
    if not path.exists():return dict(started=False,state='UNSTARTED',initial_72h=False,total_168h=False,actual_send_receive_verified=False)
    try:
        obj=_validate(read_json(root,AREA+'trial.local.json','state'))
        if obj['last']>int(clock()) or int(clock())-obj['last']>90:raise ValueError()
        elapsed=obj['continuous_seconds']
        return dict(started=True,state='UNKNOWN' if obj['start'] is None else 'OBSERVING',
            continuous_seconds=elapsed,segments=obj['segments'],interruptions=obj['interruptions'],unknown=obj['unknown'],
            samples=obj['samples'],initial_72h=elapsed>=72*3600,total_168h=elapsed>=168*3600,
            actual_send_receive_verified=False,latest=obj['latest'])
    except (ValueError,OSError,TypeError,KeyError,OverflowError):return dict(started=True,state='UNKNOWN',initial_72h=False,total_168h=False,actual_send_receive_verified=False)


def metadata_bytes(root):
    """Only directory-entry metadata, bounded traversal, no contents/symlink following."""
    total=0;entries=0
    for name in ('logs','state/qq-transport'):
        base=Path(root)/name
        if not base.exists():continue
        plain_path(root,base,directory=True);pending=[base]
        while pending:
            path=pending.pop()
            with os.scandir(path) as rows:
                for row in rows:
                    entries+=1
                    if entries>10000:raise ValueError('TRIAL_METADATA_UNKNOWN')
                    if row.is_symlink():raise ValueError('TRIAL_METADATA_UNKNOWN')
                    info=row.stat(follow_symlinks=False)
                    if getattr(info,'st_file_attributes',0)&0x400:raise ValueError('TRIAL_METADATA_UNKNOWN')
                    if row.is_dir(follow_symlinks=False):pending.append(Path(row.path))
                    elif row.is_file(follow_symlinks=False):total+=info.st_size
    return total


class TrialSampler:
    def __init__(self,monitor,*,clock=time.time,resources=None,metadata=metadata_bytes):
        self.monitor=monitor;self.root=monitor.gate.root;self.clock=clock;self.next=0
        self.resources=resources or self._resources;self.metadata=metadata

    def _resources(self):
        owner=self.monitor.owner
        if not owner.identity_current(owner.binding):raise ValueError('TRIAL_IDENTITY_UNKNOWN')
        values=[]
        for pid in (owner.binding.node_pid,owner.binding.qq_pid):
            process=owner.process(pid)
            values.extend((int(process.memory_info().rss),int(process.num_handles())))
        if not owner.identity_current(owner.binding):raise ValueError('TRIAL_IDENTITY_UNKNOWN')
        return values

    def _rotate(self,now,extra):
        base=self.root/AREA;files=list(base.glob('trial-samples-*.jsonl'))
        if len(files)>16:raise ValueError('TRIAL_CAPACITY_UNKNOWN')
        total=0
        for path in files:
            plain_path(self.root,path)
            try:day=int(path.stem.removeprefix('trial-samples-'))
            except ValueError:raise ValueError('TRIAL_CAPACITY_UNKNOWN') from None
            if not 0<=day<=9007199254740991//86400:raise ValueError('TRIAL_CLOCK_UNKNOWN')
            if day*86400>now:raise ValueError('TRIAL_CLOCK_UNKNOWN')
            if now-day*86400>=RETENTION:path.unlink()
            else:total+=path.stat().st_size
        if total+extra>LIMIT:raise ValueError('TRIAL_CAPACITY_UNKNOWN')

    def sample(self):
        try:
            now=int(self.clock())
            if not 0<=now<=9007199254740991:raise ValueError()
        except (ValueError,TypeError,OverflowError):now=0
        if now>=self.next and now>=0:self.next=now+60
        elif now>=0 and now>=self.next-60:return
        # A wall-clock rollback is recorded rather than silently waiting for time to catch up.
        path=self.root/(AREA+'trial.local.json')
        try:
            obj=_validate(read_json(self.root,AREA+'trial.local.json','state')) if path.exists() else _default()
            ready=self.monitor.gate.channel_ready() is True
            if not obj['samples'] and not ready:return  # continuous trial begins at actual admission
            fingerprint=hashlib.sha256(json.dumps(self.monitor.owner.binding.fields(),sort_keys=True).encode()).hexdigest()
            unknown=now<obj['last'] or obj['last']>0 and now-obj['last']>90
            values=None;size=None
            try:
                values=self.resources();size=self.metadata(self.root)
                if len(values)!=4 or any(type(v) is not int or not 0<=v<=9007199254740991 for v in values) or type(size) is not int or not 0<=size<=9007199254740991:raise ValueError()
            except Exception:unknown=True;values=None;size=None
            observation=self.monitor.verifier.observation or {}
            sends=self.monitor.gate.send_metrics() if hasattr(self.monitor.gate,'send_metrics') else dict(acked=0,failed=0,unknown=0,latency_ms=None)
            record=dict(t=now,ready=ready,unknown=bool(unknown),rss_handles=values,metadata_bytes=size,
                armed=observation.get('rx_watch_armed') is True,pipe=observation.get('pipe_connected') is True,
                online=self.monitor.gate.online is True,good=self.monitor.gate.good is True,
                health_seq=self.monitor.verifier.seq,control_acks=getattr(self.monitor,'control_ack_count',0),
                ack_ms=getattr(self.monitor,'control_ack_latency_ms',None),
                recoveries=len(self.monitor.supervisor.ledger.read()['actions']) if self.monitor.supervisor and self.monitor.supervisor.cfg['enabled'] else 0,
                operator=bool(self.monitor.supervisor and self.monitor.supervisor.phase=='operator_required'),
                send_acked=sends['acked'],send_failed=sends['failed'],send_unknown=sends['unknown'],send_ms=sends['latency_ms'])
            raw=(json.dumps(record,separators=(',',':'),allow_nan=False)+'\n').encode()
            if len(raw)>512:raise ValueError('TRIAL_RECORD_UNKNOWN')
            base=safe_mkdir(self.root,self.root/AREA);self._rotate(now,len(raw))
            log=base/('trial-samples-'+str(now//86400)+'.jsonl')
            if log.exists():plain_path(self.root,log)
            with log.open('ab') as stream:stream.write(raw)
            changed=obj['fingerprint']!=fingerprint
            if unknown or not ready or changed:
                if obj['start'] is not None:obj['interruptions']+=1
                obj['start']=None;obj['continuous_seconds']=0
            if unknown:obj['unknown']+=1
            if ready and not unknown:
                if obj['start'] is None:obj['start']=now;obj['segments']+=1
                obj['continuous_seconds']=now-obj['start']
            obj.update(last=now,fingerprint=fingerprint,samples=obj['samples']+1,latest=record)
            atomic_json(path,obj)
        except Exception:
            # No arbitrary exception text, identities, paths or message content in diagnostics.
            try:
                if path.exists():
                    obj=_validate(read_json(self.root,AREA+'trial.local.json','state'))
                else:obj=_default()
                obj.update(start=None,continuous_seconds=0,last=max(0,now),unknown=obj['unknown']+1)
                atomic_json(path,obj)
            except Exception:pass  # read-only status will be UNKNOWN; never kill the health task
