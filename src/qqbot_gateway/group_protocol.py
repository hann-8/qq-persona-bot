"""Strict authenticated group-turn envelope and one-generation decision."""
import json
import re
import logging
from .errors import GatewayError
from .reply_plan import make_reply_plan,ReplyPlan,_pairs,digest

SILENT='QQBOT_INTERNAL_SILENT'
FIELDS={'version','kind','trigger','must_reply','epoch','snapshot_digest','request_key'}
LOG=logging.getLogger(__name__)


def validate_request(value):
    if isinstance(value,dict) and type(value.get('version')) is int and value['version']==2:
        from .turn_v2 import validate_header
        return validate_header(value)
    if (not isinstance(value,dict) or set(value)!=FIELDS or type(value['version']) is not int or
        value['version']!=1 or value['kind']!='group_turn' or value['trigger'] not in ('mention','ambient') or
        type(value['must_reply']) is not bool or value['must_reply']!=(value['trigger']=='mention') or
        any(not isinstance(value[k],str) or not re.fullmatch(r'[a-f0-9]{64}',value[k]) for k in ('epoch','snapshot_digest','request_key'))):
        raise GatewayError('UNSUPPORTED_REQUEST')
    return dict(value)


def validate_snapshot(text,request):
    try:
        obj=json.loads(text,object_pairs_hook=_pairs)
        if (not isinstance(obj,dict) or set(obj)!={'must_reply','target_seq','web_anchor','messages'} or
            type(obj['must_reply']) is not bool or obj['must_reply']!=request['must_reply'] or
            not isinstance(obj['messages'],list) or not 1<=len(obj['messages'])<=200):raise ValueError()
        previous=0
        for row in obj['messages']:
            if (not isinstance(row,dict) or set(row)!={'seq','speaker','name','text','reply'} or
                type(row['seq']) is not int or row['seq']<=previous or
                not isinstance(row['speaker'],str) or not re.fullmatch(r'bot|u[0-9]+',row['speaker']) or
                not isinstance(row['name'],str) or len(row['name'])>40 or not isinstance(row['text'],str) or len(row['text'])>(8000 if row['speaker']=='bot' else 4000) or
                not (row['reply'] is None or type(row['reply']) is int or row['reply']=='引用未解析')):raise ValueError()
            previous=row['seq']
        if request['must_reply']:
            if type(obj['target_seq']) is not int or not any(r['seq']==obj['target_seq'] and r['speaker']!='bot' for r in obj['messages']):raise ValueError()
        elif obj['target_seq'] is not None:raise ValueError()
        if obj['web_anchor'] is not None and (not isinstance(obj['web_anchor'],str) or not any(r['text']==obj['web_anchor'] and r['speaker']!='bot' for r in obj['messages'])):raise ValueError()
        return obj
    except (ValueError,TypeError,KeyError):raise GatewayError('UNSUPPORTED_REQUEST') from None


def group_plan(raw,output,question,must_reply):
    try:
        from .output_envelope import decode_envelope
        obj=decode_envelope(raw,group=True,must_reply=must_reply)
        # This path has no enabled image catalog. Ignore image suggestions when
        # usable text exists rather than discarding the whole answer.
        if obj['bubbles']:obj['meme_id']=None
        if (not isinstance(obj,dict) or set(obj)!={'qqbot_group_reply','decision','kind','bubbles','meme_id'} or
            type(obj['qqbot_group_reply']) is not int or obj['qqbot_group_reply']!=1 or
            obj['decision'] not in ('speak','silent') or obj['kind'] not in ('chat','answer') or
            obj['meme_id'] is not None or not isinstance(obj['bubbles'],list)):
            raise ValueError()
        if obj['decision']=='silent':
            if obj['bubbles']:raise ValueError()
            if must_reply:raise ValueError()
            return 'silent',None
        plan=make_reply_plan(json.dumps(dict(qqbot_reply=1,kind=obj['kind'],bubbles=obj['bubbles']),ensure_ascii=False),
                             output|{'delivery_mode':'adaptive'},question)
        if output['delivery_mode']=='single':plan=ReplyPlan(plan.kind,(plan.canonical_text,),plan.canonical_text,plan.limited,plan.fallback_reason)
        return 'speak',plan
    except (ValueError,TypeError,KeyError,GatewayError):
        LOG.warning('GROUP_OUTPUT_INVALID category=group_protocol_error')
        if not must_reply:return 'error',None
        text='这条没接住，请再说一次。'
        return 'error',ReplyPlan('answer',(text,),text,fallback_reason='group_protocol_error')


def metadata(request,response_id,decision,plan):
    value=dict(request=request,response_id=response_id,decision=decision,plan=plan.metadata(response_id) if plan else None)
    value['plan_hash']=digest(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')))
    return value


def verify_metadata(value,request,response_id,text,output,source=None):
    if request.get('version')==2:
        from .turn_v2 import verify
        return verify(value,request,response_id,text,output,source)
    from .reply_plan import trusted_plan
    if not isinstance(value,dict) or set(value)!={'request','response_id','decision','plan','plan_hash'}:raise ValueError('Missing group metadata')
    body={k:v for k,v in value.items() if k!='plan_hash'}
    if (value['request']!=request or value['response_id']!=response_id or
        value['plan_hash']!=digest(json.dumps(body,sort_keys=True,ensure_ascii=False,separators=(',',':')))):
        raise ValueError('Group identity mismatch')
    decision=value['decision']
    if decision not in ('speak','silent','error'):raise ValueError('Invalid decision')
    if value['plan'] is None:
        if request['must_reply'] or decision=='speak' or text!=SILENT:raise ValueError('Invalid silent')
        return None
    plan=trusted_plan(value['plan'],text,response_id,output)
    if plan.fallback_reason=='metadata_missing_or_mismatch':raise ValueError('Invalid plan')
    if decision=='silent':raise ValueError('Silent with output')
    return plan
