"""Backend-independent reply protocol. Convert Markdown exactly once, at the gateway."""
from dataclasses import dataclass
import hashlib
import json
import re
import html

from .chat_text import plain_chat
from .errors import GatewayError
from .text_safety import has_tool_markup

DEFAULTS = dict(delivery_mode='single', max_bubbles=3, casual_max_chars=80,
                bubble_max_chars=40, bubble_delay_min_ms=800, bubble_delay_max_ms=1600,
                max_reply_chars=1200)


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def truncate(text, maximum):
    if len(text) <= maximum:
        return text, False
    notice = '……（内容未展示完）'
    available = maximum - len(notice)
    prefix = text[:available]
    boundary = max((i+1 for i, c in enumerate(prefix) if c in '\n。！？；.!?'), default=0)
    if boundary >= available // 2:
        prefix = prefix[:boundary]
    return prefix.rstrip() + notice, True


@dataclass(frozen=True)
class PreparedPart:
    type: str
    digest: str
    payload_ref: str
    semantic_label: str

    def metadata(self):return dict(type=self.type,digest=self.digest,payload_ref=self.payload_ref,semantic_label=self.semantic_label)


@dataclass(frozen=True)
class ReplyPlan:
    kind: str
    bubbles: tuple[str, ...]
    canonical_text: str
    limited: bool = False
    fallback_reason: str | None = None
    prepared_parts: tuple[PreparedPart,...] = ()

    @property
    def parts(self):
        return self.prepared_parts or tuple(PreparedPart('text',digest(x),x,x) for x in self.bubbles)

    def metadata(self, response_id):
        value=dict(version=2 if self.prepared_parts else 1, response_id=response_id, kind=self.kind, bubbles=list(self.bubbles),
                    content_sha256=digest(self.canonical_text), limited=self.limited,
                    fallback_reason=self.fallback_reason)
        if self.prepared_parts:
            value['parts']=[p.metadata() for p in self.parts]
            value['plan_sha256']=digest(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')))
        return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate field')
        result[key] = value
    return result


def check_decoded_tools(text):
    # Check nested JSON escape/HTML representations without changing displayed literals.
    for _ in range(8):
        if has_tool_markup(text):raise GatewayError('TOOL_ISOLATION_FAILED')
        decoded=html.unescape(re.sub(r'\\u([0-9a-fA-F]{4})',lambda m:chr(int(m[1],16)),text)).replace('\\/','/')
        if decoded==text:return
        text=decoded
    if has_tool_markup(text):raise GatewayError('TOOL_ISOLATION_FAILED')


def make_reply_plan(raw, output=None, question=''):
    cfg = DEFAULTS | (output or {})
    if not isinstance(raw, str):
        raise GatewayError('PROTOCOL_ERROR')
    if has_tool_markup(raw):
        raise GatewayError('TOOL_ISOLATION_FAILED')
    body = raw.strip()
    fenced = re.fullmatch(r'```json\s*\n(.*?)\n```', body, re.S | re.I)
    candidate = fenced.group(1).strip() if fenced else body
    kind, parts, reason = 'answer', [raw], None
    # Ordinary JSON remains literal; never search arbitrary prose for an object.
    attempted = (candidate == 'qqbot_reply' or
                 bool(re.search(r'["\']qqbot_reply["\']\s*:',candidate)) or
                 bool(re.search(r'[{,]\s*["\']?qqbot_reply\b',candidate)))
    if cfg['delivery_mode'] == 'adaptive' and attempted:
        try:
            obj = json.loads(candidate, object_pairs_hook=_pairs)
            if (not isinstance(obj, dict) or set(obj) != {'qqbot_reply', 'kind', 'bubbles'} or
                    type(obj['qqbot_reply']) is not int or obj['qqbot_reply'] != 1 or
                    obj['kind'] not in ('chat', 'answer') or not isinstance(obj['bubbles'], list) or
                    not obj['bubbles'] or any(not isinstance(x, str) or not x.strip() for x in obj['bubbles'])):
                raise ValueError('invalid reply object')
            kind, parts = obj['kind'], obj['bubbles']
        except (ValueError, TypeError, KeyError):
            raise GatewayError('PROTOCOL_ERROR') from None
    elif cfg['delivery_mode'] == 'adaptive':
        reason = 'protocol_missing'
    # Check decoded values as well as the raw envelope. plain_chat also rejects HTML-escaped tools.
    for part in parts:check_decoded_tools(part)
    parts = [plain_chat(p) for p in parts]
    canonical = '\n'.join(parts)
    canonical, limited = truncate(canonical, cfg['max_reply_chars'])
    serious = bool(re.search(r'详细解释|详细说明|给(?:出)?步骤|逐步|代码|```|字面量|原样|json',question,re.I))
    source_parts=obj['bubbles'] if attempted and cfg['delivery_mode']=='adaptive' else [raw]
    literal=any('```' in p or '\n    ' in p for p in source_parts)
    for part in source_parts:
        try:literal=literal or isinstance(json.loads(part), (dict,list))
        except (ValueError,TypeError):pass
    if kind == 'chat' and (serious or literal):
        kind, reason = 'answer', 'answer_required'
    if kind == 'chat' and (len(parts) > cfg['max_bubbles'] or
                          sum(map(len, parts)) > cfg['casual_max_chars'] or
                          any(len(p) > cfg['bubble_max_chars'] for p in parts)):
        reason = 'chat_limit'
    if kind != 'chat' or reason or limited or cfg['delivery_mode'] == 'single':
        parts = [canonical]
    return ReplyPlan(kind, tuple(parts), canonical, limited, reason)


def trusted_plan(metadata, text, response_id, output):
    """Validate gateway metadata without parsing or converting canonical body again."""
    fallback = ReplyPlan('answer', (text,), text, fallback_reason='metadata_missing_or_mismatch')
    if not isinstance(metadata, dict):
        return fallback
    if metadata.get('version')==2:
        from .media_protocol import trusted_media_plan
        return trusted_media_plan(metadata,text,response_id,output)
    parts = metadata.get('bubbles')
    if (type(metadata.get('version')) is not int or metadata['version'] != 1 or
            metadata.get('response_id') != response_id or metadata.get('content_sha256') != digest(text) or
            metadata.get('kind') not in ('chat', 'answer') or not isinstance(parts, list) or
            not parts or any(not isinstance(p, str) or not p.strip() for p in parts) or
            '\n'.join(parts) != text or len(parts) > output['max_bubbles'] or
            (metadata['kind'] == 'answer' and len(parts) != 1) or
            (len(parts) > 1 and (sum(map(len, parts)) > output['casual_max_chars'] or
                                any(len(p) > output['bubble_max_chars'] for p in parts)))):
        return fallback
    return ReplyPlan(metadata['kind'], tuple(parts), text, bool(metadata.get('limited')),
                     metadata.get('fallback_reason'))
