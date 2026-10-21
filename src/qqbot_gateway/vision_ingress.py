"""Closed, identity-free LAP-28 intake evidence. Never an eligibility proof."""
import asyncio
import json
import re
import secrets
import time
from urllib.parse import urlsplit

from .vision import HOSTS, MAX_RAW, MAX_BLOB, Materials, fetch_image, image_url

PREFIX = 'VISION_INGRESS '
STAGES = {'ingress_observed', 'locator_resolved', 'bytes_fetched', 'decoded', 'text_only'}
FAILURES = {'none', 'NO_IMAGE_SEGMENT', 'SOURCE_UNSUPPORTED', 'FETCH_FAILED', 'TIMEOUT',
            'CANCELLED', 'EMPTY_BYTES', 'DECODE_FAILED', 'MATERIAL_DENIED'}
REPRESENTATIONS = {'absent', 'https', 'http', 'path_or_uri', 'opaque', 'other'}
MIMES = {'none', 'image/png', 'image/jpeg', 'image/gif', 'image/webp'}


def representation(value):
    if value is None:return 'absent'
    if not isinstance(value, str) or not value or len(value)>4096:return 'other'
    if value.startswith('https://'):return 'https'
    if value.startswith('http://'):return 'http'
    if re.search(r'[/\\:\x00-\x1f]', value):return 'path_or_uri'
    return 'opaque'


def inspect_event(event):
    """Caller MUST admit first. Values never enter the returned record."""
    images=[s for s in event['message'] if s['type']=='image']
    first=images[0]['data'] if images else {}
    url=first.get('url')
    try:host='qq_allowed' if urlsplit(url).hostname in HOSTS else 'other' if url else 'none'
    except (ValueError, TypeError, AttributeError):host='other'
    return dict(schema_version=1, stage='ingress_observed' if images else 'text_only',
        random_trace=secrets.token_hex(8), image_segment_count=min(1024,len(images)),
        first_image_field_flags={k:k in first for k in ('url','file','file_size')},
        representation_enum={k:representation(first.get(k)) for k in ('url','file')},
        locator_source='none', host_class=host, http_status_class='none', bytes=0,
        original_dimensions=[0,0], normalized_dimensions=[0,0], normalized_bytes=0,
        mime='none', format='none', attempt_counts=dict(download=0,redirect=0),
        failure_enum='none' if images else 'NO_IMAGE_SEGMENT', elapsed_ms=0,
        backend_calls=0, qq_outputs=0)


def validate_record(row):
    """Reject unknown fields, free text, identities, URLs and oversized numbers."""
    template=inspect_event({'message':[]})
    if not isinstance(row,dict) or set(row)!=set(template):raise ValueError('INVALID_INGRESS_METADATA')
    def number(value, maximum):return type(value) is int and 0<=value<=maximum
    def enum(key, values):return isinstance(row[key],str) and row[key] in values
    if (type(row['schema_version']) is not int or row['schema_version']!=1 or
        not enum('stage',STAGES) or not isinstance(row['random_trace'],str) or
        not re.fullmatch('[a-f0-9]{16}',row['random_trace']) or
        not number(row['image_segment_count'],1024) or not enum('failure_enum',FAILURES) or
        not enum('locator_source',{'none','current_segment'}) or not enum('host_class',{'none','qq_allowed','other'}) or
        not enum('http_status_class',{'none','2xx','3xx','4xx','5xx','other'}) or
        not enum('mime',MIMES) or not enum('format',{'none','PNG','JPEG','GIF','WEBP'}) or
        not number(row['bytes'],MAX_RAW) or not number(row['normalized_bytes'],MAX_BLOB) or
        not number(row['elapsed_ms'],15000) or
        type(row['backend_calls']) is not int or row['backend_calls']!=0 or
        type(row['qq_outputs']) is not int or row['qq_outputs']!=0):raise ValueError('INVALID_INGRESS_METADATA')
    for key,fields in (('first_image_field_flags',{'url','file','file_size'}),('representation_enum',{'url','file'}),
                       ('attempt_counts',{'download','redirect'})):
        if not isinstance(row[key],dict) or set(row[key])!=fields:raise ValueError('INVALID_INGRESS_METADATA')
    if any(type(v) is not bool for v in row['first_image_field_flags'].values()):raise ValueError('INVALID_INGRESS_METADATA')
    if any(not isinstance(v,str) or v not in REPRESENTATIONS for v in row['representation_enum'].values()):raise ValueError('INVALID_INGRESS_METADATA')
    if not number(row['attempt_counts']['download'],1) or not number(row['attempt_counts']['redirect'],2):raise ValueError('INVALID_INGRESS_METADATA')
    for key,limit in (('original_dimensions',16000000),('normalized_dimensions',1024)):
        if not isinstance(row[key],list) or len(row[key])!=2 or any(not number(v,limit) for v in row[key]):raise ValueError('INVALID_INGRESS_METADATA')
    return row


def encode(row):
    return PREFIX+json.dumps(validate_record(row),sort_keys=True,separators=(',',':'))


def safe_log(line):
    # Only a known logger prefix may precede the closed object; never salvage a
    # valid suffix from arbitrary text containing a private prefix.
    match=re.fullmatch(r'(?:\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:[.,]\d{3})? (?:INFO|WARNING) )?VISION_INGRESS (\{[^\r\n]*\})',line)
    if not match or len(line)>2048:return None
    try:
        from .reply_plan import _pairs
        return encode(json.loads(match[1],object_pairs_hook=_pairs))
    except (ValueError, TypeError, KeyError):return None


async def observe(event, connection, allowed, *, fetch=None, emit=lambda row:None):
    """One admitted event; same cap/binding/expiry/8MiB lease as production.

    Synthetic tests inject only the bottom transport. No path/file fallback.
    """
    row=inspect_event(event);started=time.monotonic()
    def publish():
        row['elapsed_ms']=min(15000,int((time.monotonic()-started)*1000))
        emit(json.loads(json.dumps(validate_record(row))))
    publish()
    if not row['image_segment_count']:return row
    materials=None
    try:
        first=next(s['data'] for s in event['message'] if s['type']=='image')
        image_url(first.get('url'))
        row.update(stage='locator_resolved',locator_source='current_segment');publish()
        async def transport(url):
            row['attempt_counts']['download']=1
            raw=await fetch(url) if fetch else await fetch_image(url,diagnostic=row)
            if not isinstance(raw,bytes) or not raw:raise ValueError('EMPTY_BYTES')
            if len(raw)>MAX_RAW:raise ValueError('IMAGE_TOO_LARGE')
            row.update(stage='bytes_fetched',bytes=len(raw));publish()
            return raw
        materials=Materials(fetch=transport)
        cap=materials.issue(event,connection)
        if cap is None:raise ValueError('MATERIAL_UNAVAILABLE')
        body=dict(purpose='vision.resolve',**cap,request_key=secrets.token_hex(32),target_seq=1,
                  source_digest=secrets.token_hex(32),epoch=secrets.token_hex(32))
        materials.bind(body,connection,allowed)
        result=await materials.resolve(body,connection,allowed,diagnostic=row)
        d=result['descriptor']
        row.update(stage='decoded',normalized_dimensions=[d['width'],d['height']],normalized_bytes=d['byte_length'])
    except asyncio.CancelledError:
        row['failure_enum']='CANCELLED';publish();raise
    except TimeoutError:row['failure_enum']='TIMEOUT'
    except Exception as error:
        row['failure_enum']=('SOURCE_UNSUPPORTED' if row['stage']=='ingress_observed' else
            'EMPTY_BYTES' if isinstance(error,ValueError) and str(error)=='EMPTY_BYTES' else
            'MATERIAL_DENIED' if isinstance(error,ValueError) and str(error).startswith('MATERIAL_') else
            'DECODE_FAILED' if row['stage']=='bytes_fetched' else
            'MATERIAL_DENIED' if row['attempt_counts']['download']==0 else 'FETCH_FAILED')
    finally:
        if materials:materials.clear()
    publish()
    return row
