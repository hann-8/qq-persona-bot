"""Trusted RAM identities, frozen tickets and router-owned single-turn dispatcher.

No identity is read from model output, no RPC/history lookup, no background turns.
"""
import asyncio
import copy
import json
import logging
import re
import time
import unicodedata
import uuid
from collections import deque
from dataclasses import dataclass,field
from .participation import Participation,clean
from .session_queue import SessionError

LOG=logging.getLogger(__name__)
PRIORITY={'mention':0,'direct_name':1,'reply_bot':1,'focused_followup':2,'focused_candidate':3,'ambient':4}
DIRECT={'mention','direct_name','reply_bot','focused_followup'}

def canonical(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def called(text,names):
    text=unicodedata.normalize('NFKC',text).strip().casefold()
    # Match the call outside quoted/code/web material. A real call can itself
    # ask about a URL or a quotation without losing its direct classification.
    if text.startswith(('他说','她说','有人说')):return False
    text=re.sub(r'```.*?```|`[^`]*`|"[^"]*"|“[^”]*”|「[^」]*」|https?://\S+',' ',text,flags=re.S)
    text=' '.join(line for line in text.splitlines() if not line.lstrip().startswith('>'))
    text=re.sub(r'\s+',' ',text).strip()
    for name in sorted(names,key=len,reverse=True):
        name=unicodedata.normalize('NFKC',name).strip().casefold()
        boundary=r'[\s,，。.!！?？:：~～、]'
        if text==name or re.match('^'+re.escape(name)+boundary,text) or re.search(boundary+re.escape(name)+'[!！?？~～。]*$',text):return True
        if name.isascii():continue  # word boundaries above apply to Latin aliases
        request=r'(?:请|帮我|帮忙|能不能|能否|你|在吗|说说|解释|看看|算一下|查查|查一下|给我|来(?:看看|说说)|这个.*怎么看)'
        if re.match('^'+re.escape(name)+request,text):return True
        if re.match(r'^我想问'+re.escape(name)+r'(?:一个问题|一下|[，,：: ?？])',text):return True
    return False

@dataclass
class State:
    refs:dict=field(default_factory=dict)
    focus:dict|None=None
    version:int=0
    candidates:deque=field(default_factory=deque)
    ack:deque=field(default_factory=lambda:deque(maxlen=200))
    last_sender:str|None=None
    run_start:int=0
    barrier:int=0
    web_evaluated_seq:int=0

@dataclass(eq=False)
class Ticket:
    group:str
    addressing:str
    order:int
    source:dict
    required:set
    received:float
    deadline:float
    epoch:str
    trace:str
    size:int
    identities:dict=field(default_factory=dict)
    cancelled:bool=False
    released:bool=False

class Attention(Participation):
    def __init__(self,cfg,epoch,limit=5,timeout=600,clock=time.monotonic):
        super().__init__(cfg,epoch,limit,timeout,clock)
        self.states={};self.pending=[];self.current=None;self.frozen={}

    def state(self,group):return self.states.setdefault(group,State())

    def mention_pending(self):return any(t.addressing=='mention' and not t.cancelled for t in self.pending)

    def reset(self,group):
        super().reset(group);self.states.pop(group,None)
        for t in self.pending:
            if t.group==group:t.cancelled=True

    def invalidate(self):
        super().invalidate();self.states.clear()
        for t in self.pending:t.cancelled=True

    def observe(self,group,sender,mid,name,text,at_ids=(),reply=None):
        state=self.state(group);now=self.clock()
        while state.ack and now-state.ack[0]['at']>900:state.ack.popleft()
        if sender not in state.refs:state.refs[sender]='p_'+uuid.uuid4().hex[:16]
        if state.focus and now-state.focus['at']>self.cfg['attention']['focus_ttl_seconds']:
            state.focus=None;state.version+=1
        other=any(q!=self.bot for q in at_ids)
        known=list(self.window(group).rows)+list(state.ack)
        reference=next((r for r in reversed(known) if r['mid']==reply),None) if reply else None
        if state.focus and (state.focus['sender']!=sender or other or reference and reference['sender']!='bot'):
            state.focus=None;state.version+=1
        row=super().append(group,sender,mid,name,text,reply)
        if state.last_sender!=sender:state.last_sender=sender;state.run_start=row['seq']
        if other or reply and (not reference or reference['sender']!='bot'):state.barrier=row['seq']
        # Retain only identities reachable by current RAM or frozen/current turns.
        reachable={sender}|{r['sender'] for r in self.window(group).rows if r['sender']!='bot'}
        if state.focus:reachable.add(state.focus['sender'])
        reachable.update(s for t in self.frozen.values() if t.group==group for s in t.identities.values())
        state.refs={s:r for s,r in state.refs.items() if s in reachable}
        row['at_refs']=[('bot' if q==self.bot else state.refs.get(q,'other_member')) for q in at_ids][:8]
        if reference:row['reply']=reference['seq']
        addressing='ambient';required={row['seq']}
        if reference and reference['sender']=='bot':required.add(reference['seq'])
        if self.bot in at_ids:addressing='mention'
        elif not other and not (reply and (not reference or reference['sender']!='bot')):
            if called(text,self.cfg['attention']['aliases']):addressing='direct_name'
            elif reference and reference['sender']=='bot':addressing='reply_bot';required.add(reference['seq'])
            elif state.focus and now-state.focus['at']<=self.cfg['attention']['focus_ttl_seconds']:
                addressing='focused_followup' if (re.fullmatch(r'(?:那怎么办|为什么呢|再详细点|继续|还有呢)[。!！?？\s]*',text.strip()) or re.search(r'你|您',text) and re.search(r'[?？]|吗|么|请|帮|能|要|说|解释|觉得|怎么|为何|为什么',text)) else 'focused_candidate'
                required.update(r['seq'] for r in state.focus['rows'])
        if other or reply and (not reference or reference['sender']!='bot'):
            state.focus=None
        return row,addressing,required

    def source(self,group,target,required):
        state=self.state(group);w=self.window(group);self.trim(w)
        rows={r['seq']:r for r in w.rows}
        # Required ACK rows survive RAM trimming; no get_msg or old disk ledger.
        rows.update({r['seq']:r for r in state.ack if r['seq'] in required})
        if state.focus:rows.update({r['seq']:r for r in state.focus['rows'] if r['seq'] in required})
        rows[target['seq']]=target
        def visible(row):
            return dict(seq=row['seq'],member_ref='bot' if row['sender']=='bot' else state.refs[row['sender']],
                name=row['name'],text=row['text'],reply_seq=row['reply'] if row['reply'] in rows else ('unresolved' if row['reply'] else None),
                at_refs=row.get('at_refs',[]),age_ms=min(900000,max(0,int((self.clock()-row['at'])*1000))),images=[])
        ordered=[r for _,r in sorted(rows.items())]
        while len(ordered)>200:
            ordered.pop(next(i for i,r in enumerate(ordered) if r['seq'] not in required and r['seq']!=target['seq']))
        chosen=[visible(r) for r in ordered]
        focus=None
        if state.focus and all(r['seq'] in {c['seq'] for c in chosen} for r in state.focus['rows']):
            focus=dict(version=state.version,member_ref=state.refs[state.focus['sender']],bot_seqs=[r['seq'] for r in state.focus['rows']],
                received_age_ms=min(900000,max(0,int((self.clock()-state.focus['at'])*1000))))
        return dict(self={'speaker':'bot','names':self.cfg['attention']['aliases']},target_seq=target['seq'],
            eligible_seq=[r['seq'] for r in chosen if r['member_ref']!='bot'],messages=chosen,focus=focus,
            member_candidates=[],memory=None,images=[],web_anchor=None,meme_question=None)

    def freeze(self,group,addressing,target,required,trace):
        source=self.source(group,target,required)
        # Only required lines are frozen. Optional window is reconstructed at dispatch.
        source['messages']=[r for r in source['messages'] if r['seq'] in required]
        from .turn_v2 import close_refs
        close_refs(source)
        identities={}
        self.request_refs(group,source,identities)
        size=len(canonical(dict(source=source,identities=identities)).encode())
        if size>32768:raise SessionError('SESSION_QUEUE_FULL')
        self.order+=1
        ticket=Ticket(group,addressing,self.order,copy.deepcopy(source),set(required),target['at'],self.clock()+self.timeout,
            self.group_epoch(group),trace,size,identities)
        self.frozen[id(ticket)]=ticket
        return ticket

    def request_refs(self,group,source,identities):
        """Translate RAM aliases to a fresh per-ticket namespace, locally reversible."""
        state=self.state(group);by_alias={r:s for s,r in state.refs.items()}
        by_sender={s:r for r,s in identities.items()}
        def convert(ref):
            if ref in ('bot','other_member'):return ref
            sender=by_alias.get(ref)
            if sender is None:return 'other_member'
            if sender not in by_sender:
                new='p_'+uuid.uuid4().hex[:16];identities[new]=sender;by_sender[sender]=new
            return by_sender[sender]
        for row in source['messages']:
            row['member_ref']=convert(row['member_ref'])
            row['at_refs']=[convert(r) for r in row['at_refs']]
        if source['focus']:source['focus']['member_ref']=convert(source['focus']['member_ref'])

    async def dispatch(self,ticket,valid):
        live=[t for t in self.pending if not t.cancelled];kind=ticket.addressing
        immediate=self.current is None and not live
        if not immediate:
            nonmention=[t for t in live if t.addressing!='mention']
            pergroup=[t for t in live if t.group==ticket.group and
                (t.addressing=='mention' if kind=='mention' else t.addressing=='ambient' if kind=='ambient' else t.addressing not in ('mention','ambient'))]
            bound=self.cfg['mention_queue_limit'] if kind=='mention' else 1 if kind=='ambient' else self.cfg['attention']['direct_queue_limit']
            if (len(live)>=self.limit or kind!='mention' and len(nonmention)>=max(0,self.limit-min(2,self.limit)) or
                len(pergroup)>=bound or sum(t.size for t in live)+ticket.size>262144):
                raise SessionError('SESSION_QUEUE_FULL',kind in DIRECT)
        self.pending.append(ticket)
        LOG.info('ATTENTION trace=%s stage=queued queue_result=accepted addressing=%s',ticket.trace,kind)
        try:
            while True:
                if ticket.cancelled or not valid() or ticket.epoch!=self.group_epoch(ticket.group):raise SessionError('INVALIDATED',False)
                if self.clock()>ticket.deadline:raise SessionError('SESSION_QUEUE_TIMEOUT',kind in DIRECT)
                if kind not in DIRECT and self.clock()-ticket.received>min(90,self.cfg['max_ambient_age_seconds']):raise SessionError('INVALIDATED',False)
                ready=[t for t in self.pending if not t.cancelled]
                if self.current is None and min(ready,key=lambda t:(PRIORITY[t.addressing],t.order)) is ticket:
                    state=self.state(ticket.group);self.prune(state.candidates)
                    if kind=='focused_candidate':
                        if len(state.candidates)>=self.cfg['attention']['focus_candidate_evaluations_per_minute']:raise SessionError('INVALIDATED',False)
                        state.candidates.append(self.clock())
                    self.current=ticket;self.pending.remove(ticket)
                    LOG.info('ATTENTION trace=%s stage=model_started wait_ms=%s',ticket.trace,int((self.clock()-ticket.received)*1000))
                    return ticket
                await asyncio.sleep(.01)
        finally:
            if ticket in self.pending:self.pending.remove(ticket)

    def rebuild(self,ticket):
        frozen=copy.deepcopy(ticket.source)
        # Rebuild optional rows even when the original target has been RAM-trimmed.
        # A local copy of the target is used only to satisfy source(), never to
        # reinterpret addressing/focus. Frozen required rows overwrite it below.
        target=next(r for r in frozen['messages'] if r['seq']==frozen['target_seq'])
        sender=ticket.identities[target['member_ref']]
        local=dict(seq=target['seq'],sender=sender,mid='',name=target['name'],text=target['text'],
            at=ticket.received,reply=target['reply_seq'],at_refs=target['at_refs'])
        optional=self.source(ticket.group,local,ticket.required)
        self.request_refs(ticket.group,optional,ticket.identities)
        rows={r['seq']:r for r in optional['messages']}
        rows.update({r['seq']:r for r in frozen['messages']})
        frozen['messages']=[r for _,r in sorted(rows.items())]
        if len(frozen['messages'])>200:
            optional=[r for r in frozen['messages'] if r['seq'] not in ticket.required]
            drop={r['seq'] for r in optional[:len(frozen['messages'])-200]}
            frozen['messages']=[r for r in frozen['messages'] if r['seq'] not in drop]
        frozen['eligible_seq']=[r['seq'] for r in frozen['messages'] if r['member_ref']!='bot']
        from .turn_v2 import close_refs
        close_refs(frozen)
        return frozen

    def finish(self,ticket):
        if ticket.released:return
        ticket.released=True
        self.frozen.pop(id(ticket),None)
        if self.current is ticket:self.current=None
        LOG.info('ATTENTION trace=%s stage=released elapsed_ms=%s',ticket.trace,int((self.clock()-ticket.received)*1000))

    def acknowledge(self,ticket,parts,response_to):
        state=self.state(ticket.group)
        target=next((r for r in ticket.source['messages'] if r['seq']==response_to and r['member_ref']!='bot'),None)
        # Ambient may choose an optional visible human, using the final verified source.
        sender=ticket.identities.get(target['member_ref']) if target else None
        rows=[]
        for text,mid in parts:
            if not mid:continue
            row=copy.deepcopy(super().confirm(ticket.group,text,mid));state.ack.append(row);rows.append(row)
        if not rows or sender is None:return
        if state.last_sender!=sender or response_to<state.run_start or response_to<=state.barrier:return
        state.version+=1
        state.focus=dict(sender=sender,at=self.clock(),rows=rows[-3:])
