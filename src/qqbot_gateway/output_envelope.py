"""Recover presentation deviations without interpreting model text as capabilities."""
import json
import re

from .reply_plan import _pairs, check_decoded_tools


def decode_envelope(raw, *, group, must_reply):
    if not isinstance(raw,str) or not raw.strip():raise ValueError('empty')
    check_decoded_tools(raw)
    body=raw.strip().lstrip('\ufeff')
    fence=re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```',body,re.S|re.I)
    if fence:body=fence[1].strip()
    marker='qqbot_group_reply' if group else 'qqbot_media_reply'
    internal=bool(re.search(r'qqbot_(?:group|media|reply)|QQBOT_INTERNAL_',body,re.I))
    try:obj=json.loads(body,object_pairs_hook=_pairs)
    except ValueError:
        # Never render broken envelopes or internal JSON as ordinary chat.
        if not must_reply or body.startswith(('{','[','```')) or internal:
            raise ValueError('invalid_json') from None
        return {marker:1,'decision':'speak','kind':'answer','bubbles':[raw],'meme_id':None}
    if not isinstance(obj,dict):
        if must_reply and not isinstance(obj,list) and not internal:
            return {marker:1,'decision':'speak','kind':'answer','bubbles':[raw],'meme_id':None}
        raise ValueError('not_object')
    if any(k.lower() in ('tools','tool_calls','tool_call','function_call','function_calls','functions') for k in obj):
        raise ValueError('tool_fields')
    if any(k.startswith('qqbot_') and k!=marker for k in obj):raise ValueError('wrong_envelope')
    if type(obj.get(marker,1)) is not int or obj.get(marker,1)!=1:raise ValueError('marker')
    if 'bubbles' not in obj:raise ValueError('missing_bubbles')
    bubbles=obj['bubbles']
    if isinstance(bubbles,str):bubbles=[bubbles]
    if not isinstance(bubbles,list) or any(not isinstance(x,str) for x in bubbles):raise ValueError('bubbles')
    bubbles=[x for x in bubbles if x.strip()]
    kind=obj.get('kind','answer')
    if kind not in ('chat','answer'):raise ValueError('kind')
    decision=obj.get('decision','speak' if must_reply else None)
    if group and decision not in ('speak','silent'):raise ValueError('decision')
    if group and must_reply and decision=='silent' and bubbles:decision='speak'
    mid=obj.get('meme_id')
    # Image selection is optional; bad image metadata must not discard good text.
    if mid is not None and not isinstance(mid,str):mid=None
    return {marker:1,'decision':decision,'kind':kind,'bubbles':bubbles,'meme_id':mid}
