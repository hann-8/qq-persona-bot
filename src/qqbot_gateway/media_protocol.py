"""Strict one-generation media envelope; model chooses only offered IDs."""
import json
import re
import logging
from .reply_plan import ReplyPlan,PreparedPart,digest,make_reply_plan,_pairs
from .errors import GatewayError

MEDIA_REQUEST={'version':1,'kind':'media_turn'}
LOG=logging.getLogger(__name__)


def explicit_meme(question):
    return bool(re.search(r'(?:发|来|给).{0,12}(?:表情|梗图)|(?:表情|梗图).{0,8}(?:发|来)',question))


def media_plan(raw,output,question,catalog,candidates,*,group=False,must_reply=True):
    try:
        from .output_envelope import decode_envelope
        obj=decode_envelope(raw,group=group,must_reply=must_reply)
        if not group:obj.pop('decision',None)
        fields={'qqbot_group_reply','decision','kind','bubbles','meme_id'} if group else {'qqbot_media_reply','kind','bubbles','meme_id'}
        marker='qqbot_group_reply' if group else 'qqbot_media_reply'
        if not isinstance(obj,dict) or set(obj)!=fields or type(obj[marker]) is not int or obj[marker]!=1 or obj['kind'] not in ('chat','answer') or not isinstance(obj['bubbles'],list):raise ValueError()
        if group:
            if obj['decision'] not in ('silent','speak'):raise ValueError()
            if obj['decision']=='silent':
                if must_reply or obj['bubbles'] or obj['meme_id'] is not None:raise ValueError()
                return 'silent',None
        if any(not isinstance(x,str) or not x.strip() for x in obj['bubbles']):raise ValueError()
        if obj['meme_id'] is not None and not isinstance(obj['meme_id'],str):raise ValueError()
        plan=None
        if obj['bubbles']:
            plan=make_reply_plan(json.dumps(dict(qqbot_reply=1,kind=obj['kind'],bubbles=obj['bubbles']),ensure_ascii=False),output|{'delivery_mode':'adaptive'},question)
            if output['delivery_mode']=='single':plan=ReplyPlan(plan.kind,(plan.canonical_text,),plan.canonical_text,plan.limited,plan.fallback_reason)
        parts=list(plan.parts) if plan else []
        mid=obj['meme_id']
        serious=bool(re.search(r'代码|详细|解释|步骤|json|https?://',question,re.I))
        if (mid in {x['id'] for x in candidates} and obj['kind']=='chat' and not serious and
            (plan is None or plan.kind=='chat') and len(parts)<output['max_bubbles'] and
            (parts or catalog.cfg['allow_meme_only'] and (not must_reply or explicit_meme(question)))):
            try:
                _,row=catalog.resolve(mid)
                label='[bot发了表情：'+row['name']+']'
                parts.append(PreparedPart('image',row['sha256'],mid,label))
            except (ValueError,OSError):pass
        if not parts:
            if not must_reply:return 'silent',None
            text='这张表情暂时发不了。' if explicit_meme(question) else '这条没接住，请再说一次。'
            return 'error',ReplyPlan('answer',(text,),text)
        labels=tuple(x.semantic_label for x in parts)
        return 'speak',ReplyPlan(plan.kind if plan else 'chat',labels,'\n'.join(labels),plan.limited if plan else False,
                                plan.fallback_reason if plan else None,tuple(parts))
    except (ValueError,TypeError,KeyError,GatewayError):
        LOG.warning('GROUP_OUTPUT_INVALID category=media_protocol_error')
        if not must_reply:return 'error',None
        text='这条没接住，请再说一次。'
        return 'error',ReplyPlan('answer',(text,),text,fallback_reason='media_protocol_error')


def trusted_media_plan(meta,text,response_id,output):
    try:
        if type(meta.get('version')) is not int or meta.get('version') not in (2,3) or meta.get('plan_sha256')!=digest(json.dumps({k:v for k,v in meta.items() if k!='plan_sha256'},sort_keys=True,ensure_ascii=False,separators=(',',':'))):raise ValueError()
        if meta['response_id']!=response_id or meta['content_sha256']!=digest(text) or meta['kind'] not in ('chat','answer'):raise ValueError()
        parts=tuple(PreparedPart(**x) for x in meta['parts'])
        if not 1<=len(parts)<=output['max_bubbles'] or sum(x.type=='image' for x in parts)>1:raise ValueError()
        mentions=[p for p in parts if p.mention_ref is not None]
        if (len(mentions)>1 or bool(mentions)!=(meta['version']==3) or
            any(p.type!='text' or not isinstance(p.mention_ref,str) or not re.fullmatch('p_[a-f0-9]{16}',p.mention_ref) for p in mentions)):
            raise ValueError()
        for p in parts:
            if p.type=='text':
                if p.digest!=digest(p.payload_ref) or p.payload_ref!=p.semantic_label or not p.payload_ref.strip() or '[CQ:' in p.payload_ref:raise ValueError()
            elif p.type=='image':
                if p.payload_ref!='m_'+p.digest or not re.fullmatch('[a-f0-9]{64}',p.digest) or meta['kind']!='chat':raise ValueError()
            else:raise ValueError()
        labels=tuple(p.semantic_label for p in parts)
        if list(labels)!=meta['bubbles'] or '\n'.join(labels)!=text:raise ValueError()
        return ReplyPlan(meta['kind'],labels,text,bool(meta.get('limited')),meta.get('fallback_reason'),parts)
    except (ValueError,TypeError,KeyError):raise ValueError('Invalid typed plan') from None
