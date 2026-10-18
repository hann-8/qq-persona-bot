"""Closed v2 wire contract. Future private materials deliberately remain empty."""
import copy
import json
import logging
import re
from .errors import GatewayError
from .reply_plan import _pairs,digest,ReplyPlan
from .attention import canonical,DIRECT,PRIORITY

HEAD={'version','kind','request_key','epoch','config_version','source_digest','mode','addressing','must_reply','target_seq','resource_caps'}
BODY={'self','target_seq','eligible_seq','messages','focus','member_candidates','memory','images','web_anchor','meme_question'}
ROW={'seq','member_ref','name','text','reply_seq','at_refs','age_ms','images'}
LOG=logging.getLogger(__name__)

def integer(x,lo=1,hi=2**63-1):return type(x) is int and lo<=x<=hi
def hexa(x,n):return isinstance(x,str) and re.fullmatch('[a-f0-9]{'+str(n)+'}',x) is not None
def ref(x):return isinstance(x,str) and (x=='bot' or re.fullmatch(r'p_[a-f0-9]{16}',x) is not None)
def sha(obj):return digest(canonical(obj))

def validate_header(obj):
    if (not isinstance(obj,dict) or set(obj)!=HEAD or type(obj['version']) is not int or obj['version']!=2 or
        obj['mode'] not in ('free','mentions') or obj['kind']!=('group_turn' if obj['mode']=='free' else 'member_turn') or
        obj['addressing'] not in PRIORITY or type(obj['must_reply']) is not bool or obj['must_reply']!=(obj['addressing'] in DIRECT) or
        obj['mode']=='mentions' and obj['addressing']!='mention' or not integer(obj['target_seq']) or
        any(not hexa(obj[k],64) for k in ('request_key','epoch','config_version','source_digest')) or
        obj['resource_caps']!=[]):raise GatewayError('UNSUPPORTED_REQUEST')
    return dict(obj)

def validate_source(text,request):
    try:
        obj=json.loads(text,object_pairs_hook=_pairs)
        if not isinstance(obj,dict) or set(obj)!=BODY or sha(obj)!=request['source_digest']:raise ValueError()
        who=obj['self']
        if (not isinstance(who,dict) or set(who)!={'speaker','names'} or who['speaker']!='bot' or
            not isinstance(who['names'],list) or not 1<=len(who['names'])<=16 or
            any(not isinstance(n,str) or not 1<=len(n)<=16 for n in who['names'])):raise ValueError()
        if obj['target_seq']!=request['target_seq'] or type(obj['target_seq']) is not int:raise ValueError()
        rows=obj['messages']
        if not isinstance(rows,list) or not 1<=len(rows)<=200:raise ValueError()
        previous=0
        for row in rows:
            if (not isinstance(row,dict) or set(row)!=ROW or not integer(row['seq'],previous+1) or not ref(row['member_ref']) or
                not isinstance(row['name'],str) or len(row['name'])>40 or not isinstance(row['text'],str) or
                len(row['text'])>(8000 if row['member_ref']=='bot' else 4000) or not integer(row['age_ms'],0,900000) or
                not (row['reply_seq'] in (None,'unresolved') or integer(row['reply_seq'])) or
                not isinstance(row['at_refs'],list) or len(row['at_refs'])>8 or any(not (ref(r) or r=='other_member') for r in row['at_refs']) or
                row['images']!=[]):raise ValueError()
            previous=row['seq']
        seqs={r['seq'] for r in rows};humans={r['seq'] for r in rows if r['member_ref']!='bot'}
        refs={r['member_ref'] for r in rows}
        if (obj['target_seq'] not in humans or not isinstance(obj['eligible_seq'],list) or not 1<=len(obj['eligible_seq'])<=200 or
            any(not integer(s) or s not in humans for s in obj['eligible_seq']) or len(set(obj['eligible_seq']))!=len(obj['eligible_seq']) or
            any(integer(r['reply_seq']) and r['reply_seq'] not in seqs for r in rows) or
            any(a not in refs|{'bot','other_member'} for r in rows for a in r['at_refs'])):raise ValueError()
        focus=obj['focus']
        if focus is not None:
            if (not isinstance(focus,dict) or set(focus)!={'version','member_ref','bot_seqs','received_age_ms'} or
                not integer(focus['version'],0) or focus['member_ref'] not in refs-{'bot'} or
                not integer(focus['received_age_ms'],0,900000) or not isinstance(focus['bot_seqs'],list) or
                not 1<=len(focus['bot_seqs'])<=3 or len(set(focus['bot_seqs']))!=len(focus['bot_seqs']) or
                any(not integer(s) or not any(r['seq']==s and r['member_ref']=='bot' for r in rows) for s in focus['bot_seqs'])):raise ValueError()
        if obj['member_candidates']!=[] or obj['memory'] is not None or obj['images']!=[]:raise ValueError()
        target=next(r for r in rows if r['seq']==obj['target_seq'])
        for key in ('web_anchor','meme_question'):
            anchor=obj[key]
            if anchor is not None and (not isinstance(anchor,str) or not any(r['text']==anchor and r['seq'] in obj['eligible_seq'] for r in rows) or
                request['must_reply'] and anchor!=target['text']):raise ValueError()
        return obj
    except (ValueError,TypeError,KeyError):raise GatewayError('UNSUPPORTED_REQUEST') from None

def close_refs(obj):
    seqs={r['seq'] for r in obj['messages']};refs={r['member_ref'] for r in obj['messages']}
    obj['eligible_seq']=[s for s in obj['eligible_seq'] if s in seqs]
    for row in obj['messages']:
        if integer(row['reply_seq']) and row['reply_seq'] not in seqs:row['reply_seq']='unresolved'
        row['at_refs']=[a if a in refs|{'bot','other_member'} else 'other_member' for a in row['at_refs']]
    if obj['focus'] and (not set(obj['focus']['bot_seqs'])<=seqs or obj['focus']['member_ref'] not in refs):obj['focus']=None
    for key in ('web_anchor','meme_question'):
        if obj[key] is not None and not any(r['text']==obj[key] and r['seq'] in obj['eligible_seq'] for r in obj['messages']):obj[key]=None

def required_seqs(obj,request):
    required={obj['target_seq']}
    row=next(r for r in obj['messages'] if r['seq']==obj['target_seq'])
    if integer(row['reply_seq']) and any(r['seq']==row['reply_seq'] and r['member_ref']=='bot' for r in obj['messages']):
        required.add(row['reply_seq'])
    if request['addressing'] in ('focused_followup','focused_candidate'):
        if not obj['focus']:raise GatewayError('UNSUPPORTED_REQUEST')
        required.update(obj['focus']['bot_seqs'])
    return required

def fit(obj,request,system,budget,suffix='',history=()):
    from .token_budget import dialog_text
    obj=copy.deepcopy(obj);required=required_seqs(obj,request)
    while True:
        close_refs(obj);body=canonical(obj)
        try:
            budget.check(system+suffix,dialog_text(list(history)+[dict(role='user',content=body)]))
            return body
        except GatewayError as error:
            if error.code!='INPUT_TOO_LONG':raise
            index=next((i for i,r in enumerate(obj['messages']) if r['seq'] not in required),None)
            if index is None:raise
            obj['messages'].pop(index)

def manifest(obj):
    return dict(seqs=[r['seq'] for r in obj['messages']],member_refs=sorted({r['member_ref'] for r in obj['messages']}),
        fact_refs=[],images=[],eligible_seq=list(obj['eligible_seq']))

def plan(raw,output,question,request,effective,catalog=None,candidates=()):
    """Validate core first; aux never repairs broken core or carries future powers."""
    from .group_protocol import group_plan
    # LAP-25's bounded decoder handles complete fenced objects, prose and damaged
    # core only as text fallback; no aux is recovered in that case.
    try:
        text=raw.strip()
        if text.startswith('```'):
            text=re.sub(r'^```(?:json)?\s*','',text,flags=re.I);text=re.sub(r'\s*```$','',text)
        obj=json.loads(text,object_pairs_hook=_pairs)
        fields={'qqbot_turn_reply','decision','kind','bubbles','meme_id','response_to_seq','mention','memory_proposals'}
        if (not isinstance(obj,dict) or set(obj)-fields or type(obj.get('qqbot_turn_reply')) is not int or obj['qqbot_turn_reply']!=2 or
            not {'decision','kind','bubbles','meme_id'}<=set(obj) or obj['decision'] not in ('speak','silent') or
            obj['kind'] not in ('chat','answer') or not isinstance(obj['bubbles'],list) or
            any(not isinstance(b,str) or not b.strip() for b in obj['bubbles']) or
            not (obj['meme_id'] is None or isinstance(obj['meme_id'],str)) or
            obj['decision']=='silent' and (obj['bubbles'] or obj['meme_id'] is not None or obj.get('mention') is not None)):
            raise ValueError()
        core=dict(qqbot_group_reply=1,**{k:obj[k] for k in ('decision','kind','bubbles','meme_id')})
        if catalog is not None and catalog.cfg['enabled']:
            from .media_protocol import media_plan
            decision,result=media_plan(canonical(core),output,question,catalog,candidates,group=True,must_reply=request['must_reply'])
        else:decision,result=group_plan(canonical(core),output,question,request['must_reply'])
        if decision=='error':return decision,result,None
        for key in ('response_to_seq','mention','memory_proposals'):
            if key not in obj:LOG.info('V2_AUX category=missing_%s',key)
        if obj.get('mention') is not None:LOG.info('V2_AUX category=mention_unavailable')
        if obj.get('memory_proposals',[])!=[]:LOG.info('V2_AUX category=memory_unavailable')
        response=obj.get('response_to_seq')
        if request['must_reply']:response=request['target_seq']
        elif not integer(response) or response not in effective['eligible_seq']:
            if response is not None:LOG.info('V2_AUX category=invalid_response_object')
            response=None
        # LAP-29/30 are not delivered: mention and proposals cannot escape v2.
        if result and result.fallback_reason:response=None
        return decision,result,response
    except (ValueError,TypeError,KeyError):
        # Only bounded text recovery, never salvage aux from malformed output.
        decision,result=group_plan(raw,output,question,request['must_reply'])
        if result:result=ReplyPlan(result.kind,result.bubbles,result.canonical_text,result.limited,'v2_core_recovery')
        return decision,result,None

def metadata(request,response_id,decision,result,effective,response_to=None):
    value=dict(request=request,response_id=response_id,decision=decision,plan=result.metadata(response_id) if result else None,
        effective_digest=sha(effective),manifest=manifest(effective),response_to_seq=response_to)
    value['plan_hash']=sha(value)
    return value

def verify(value,request,response_id,text,output,source):
    from .reply_plan import trusted_plan
    if not isinstance(value,dict) or set(value)!={'request','response_id','decision','plan','effective_digest','manifest','response_to_seq','plan_hash'}:raise ValueError('Missing v2 identity')
    if value['request']!=request or value['response_id']!=response_id or sha({k:v for k,v in value.items() if k!='plan_hash'})!=value['plan_hash']:raise ValueError('v2 identity mismatch')
    m=value['manifest']
    if not isinstance(m,dict) or set(m)!={'seqs','member_refs','fact_refs','images','eligible_seq'}:raise ValueError('manifest')
    if not isinstance(m['seqs'],list) or len(set(m['seqs']))!=len(m['seqs']) or any(not integer(s) for s in m['seqs']):raise ValueError('seqs')
    effective=copy.deepcopy(source);effective['messages']=[r for r in effective['messages'] if r['seq'] in m['seqs']];close_refs(effective)
    if not required_seqs(source,request)<=set(m['seqs']) or manifest(effective)!=m or sha(effective)!=value['effective_digest']:raise ValueError('effective identity')
    response=value['response_to_seq']
    if response is not None and (not integer(response) or response not in effective['eligible_seq'] or request['must_reply'] and response!=request['target_seq']):raise ValueError('response identity')
    if value['decision'] not in ('speak','silent','error'):raise ValueError('decision')
    if value['plan'] is None:
        from .group_protocol import SILENT
        if request['must_reply'] or value['decision']=='speak' or text!=SILENT:raise ValueError('silent')
        return None
    result=trusted_plan(value['plan'],text,response_id,output)
    if result.fallback_reason=='metadata_missing_or_mismatch' or value['decision']=='silent':raise ValueError('plan')
    return result
