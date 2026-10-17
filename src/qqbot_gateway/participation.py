"""Bounded RAM windows and event-driven arbitration; no background generation."""
import asyncio
from collections import deque
from dataclasses import dataclass,field
import json
import time
import unicodedata
import uuid
from .reply_plan import digest
from .session_queue import SessionError

DEFAULTS=dict(mode='mentions',debounce_seconds=2,max_batch_wait_seconds=5,min_evaluation_interval_seconds=5,
    max_evaluations_per_minute=12,unsolicited_cooldown_seconds=15,max_unsolicited_per_minute=4,
    context_messages=60,context_ttl_seconds=900,context_max_bytes=32768,message_max_chars=2000,
    mention_queue_limit=8,max_ambient_age_seconds=90,allow_ambient_web=True)
RANGES=dict(debounce_seconds=(.5,5),max_batch_wait_seconds=(2,10),min_evaluation_interval_seconds=(1,30),
    max_evaluations_per_minute=(1,60),unsolicited_cooldown_seconds=(0,120),max_unsolicited_per_minute=(1,20),
    context_messages=(10,200),context_ttl_seconds=(60,3600),context_max_bytes=(4096,131072),
    message_max_chars=(200,4000),mention_queue_limit=(1,32),max_ambient_age_seconds=(10,180))


def validate_participation(raw):
    if not isinstance(raw,dict) or set(raw)-set(DEFAULTS):raise ValueError('Invalid participation fields')
    cfg=DEFAULTS|raw
    if cfg['mode'] not in ('mentions','free') or type(cfg['allow_ambient_web']) is not bool:raise ValueError('Invalid participation mode/web')
    for k,(lo,hi) in RANGES.items():
        value=cfg[k]
        types=(int,float) if k in ('debounce_seconds','max_batch_wait_seconds') else (int,)
        if type(value) not in types or not lo<=value<=hi:raise ValueError(f'participation.{k}: {lo}..{hi}')
    if cfg['max_batch_wait_seconds']<cfg['debounce_seconds']:raise ValueError('Batch wait must cover debounce')
    return cfg


def clean(text):
    return ''.join(c for c in str(text) if c in '\n\t' or not unicodedata.category(c).startswith('C'))


@dataclass
class Window:
    generation:str=field(default_factory=lambda:uuid.uuid4().hex)
    rows:deque=field(default_factory=deque)
    aliases:dict=field(default_factory=dict)
    seq:int=0
    evaluated_seq:int=0
    candidate:object=None
    evaluations:deque=field(default_factory=deque)
    spoken:deque=field(default_factory=deque)


class Participation:
    def __init__(self,cfg,epoch,limit=5,timeout=600,clock=time.monotonic):
        self.cfg=cfg;self.epoch=epoch;self.limit=limit;self.timeout=timeout;self.clock=clock
        self.groups={};self.tickets=[];self.active=False;self.order=0;self.last_group=None

    def window(self,group):return self.groups.setdefault(group,Window())

    def group_epoch(self,group):return digest(self.epoch+self.window(group).generation)

    def reset(self,group):
        self.preempt(group)
        self.groups.pop(group,None)

    def trim(self,w):
        while w.rows and (self.clock()-w.rows[0]['at']>self.cfg['context_ttl_seconds'] or len(w.rows)>self.cfg['context_messages'] or
            len(json.dumps(list(w.rows),ensure_ascii=False).encode())>self.cfg['context_max_bytes']):w.rows.popleft()
        live={r['sender'] for r in w.rows}
        w.aliases={k:v for k,v in w.aliases.items() if k in live}

    def append(self,group,sender,mid,name,text,reply=None):
        w=self.window(group);self.trim(w);w.seq+=1
        if sender not in w.aliases:w.aliases[sender]='bot' if sender=='bot' else 'u'+str(w.seq)
        reference=next((r['seq'] for r in w.rows if r['mid']==reply),None) if reply else None
        w.rows.append(dict(seq=w.seq,at=self.clock(),sender=sender,mid=mid,speaker=w.aliases[sender],
                           name=clean(name)[:40],text=text if sender=='bot' else clean(text)[:self.cfg['message_max_chars']],reply=reference if reference else ('引用未解析' if reply else None)))
        self.trim(w)

    def snapshot(self,group):
        w=self.window(group);self.trim(w)
        return [dict(seq=r['seq'],speaker=r['speaker'],name=r['name'],text=r['text'],reply=r['reply']) for r in w.rows]

    def confirm(self,group,text,mid):self.append(group,'bot',mid,'bot',text)

    def preempt(self,group):
        w=self.window(group)
        if w.candidate:w.candidate['cancelled']=True
        for ticket in self.tickets:
            if ticket['group']==group and not ticket['mention']:ticket['cancelled']=True

    def mention_pending(self):return any(t['mention'] and not t['cancelled'] for t in self.tickets)

    async def batch(self,group,valid):
        w=self.window(group);now=self.clock()
        if any(t['group']==group and not t['mention'] and not t['cancelled'] for t in self.tickets):return False
        if w.candidate:
            w.candidate['last']=now
            return False
        candidate=dict(first=now,last=now,cancelled=False);w.candidate=candidate
        try:
            while True:
                if candidate['cancelled'] or not valid():return False
                delay=min(candidate['last']+self.cfg['debounce_seconds'],candidate['first']+self.cfg['max_batch_wait_seconds'])-self.clock()
                if delay<=0:break
                await asyncio.sleep(min(.1,delay))
            while True:
                if candidate['cancelled'] or not valid():return False
                self.prune(w.evaluations)
                wait=max(0,(w.evaluations[-1]+self.cfg['min_evaluation_interval_seconds']-self.clock()) if w.evaluations else 0,
                    (w.evaluations[0]+60-self.clock()) if len(w.evaluations)>=self.cfg['max_evaluations_per_minute'] else 0)
                if not wait:break
                await asyncio.sleep(min(.1,wait))
            return True
        finally:
            if w.candidate is candidate:w.candidate=None

    def prune(self,items):
        while items and self.clock()-items[0]>=60:items.popleft()

    def may_speak(self,group):
        w=self.window(group);self.prune(w.spoken)
        return not self.mention_pending() and len(w.spoken)<self.cfg['max_unsolicited_per_minute'] and (not w.spoken or self.clock()-w.spoken[-1]>=self.cfg['unsolicited_cooldown_seconds'])

    async def acquire(self,group,mention,valid):
        if mention:self.preempt(group)
        live=[t for t in self.tickets if not t['cancelled']]
        if len(live)>=self.limit or mention and sum(t['mention'] and t['group']==group for t in live)>=self.cfg['mention_queue_limit']:
            raise SessionError('SESSION_QUEUE_FULL')
        if not mention and any(t['group']==group and not t['mention'] for t in live):raise SessionError('SESSION_QUEUE_FULL',False)
        self.order+=1
        ticket=dict(group=group,mention=mention,order=self.order,cancelled=False);self.tickets.append(ticket)
        deadline=self.clock()+self.timeout
        try:
            while True:
                if ticket['cancelled'] or not valid():raise SessionError('INVALIDATED',False)
                if self.clock()>deadline:raise SessionError('SESSION_QUEUE_TIMEOUT')
                ready=[t for t in self.tickets if not t['cancelled']]
                first=min(ready,key=lambda t:(not t['mention'],t['group']==self.last_group if not t['mention'] else False,t['order']))
                if not self.active and first is ticket:
                    self.active=True;self.last_group=group;self.tickets.remove(ticket)
                    return self
                await asyncio.sleep(.02)
        finally:
            if ticket in self.tickets:self.tickets.remove(ticket)

    def release(self):self.active=False

    def invalidate(self):
        self.epoch=digest(self.epoch+'disconnect'+str(self.clock()))
        for w in self.groups.values():
            if w.candidate:w.candidate['cancelled']=True
        self.groups.clear()
        for t in self.tickets:t['cancelled']=True
