"""Current visible text only. No card, reply or history expansion."""
import re
from urllib.parse import urlsplit, parse_qs
from .public_http import safe_url, WebFailure

DEFAULTS = dict(enabled=False, trigger='explicit', auth_mode='none', preferred_language='zh',
                long_subtitle_policy='excerpt', max_duration_seconds=1200,
                max_subtitle_response_bytes=1048576, max_evidence_bytes=6000, cache_ttl_seconds=600)
BV = r'BV[A-Za-z0-9]{10}'
ID = r'(?:'+BV+r'|av[1-9][0-9]{0,18})'
LINK = re.compile(r'(?:https?://)?(?:(?:www\.|m\.)?bilibili\.com/video/[^\s<>"，。！？；、（）]+|b23\.tv/[^\s<>"，。！？；、（）]+)', re.I)
BARE = re.compile(r'(?<![A-Za-z0-9_/])('+ID+r')(?![A-Za-z0-9])')
REQUEST = re.compile(r'总结|概括|讲了什么|要点|分析这个视频|summari[sz]e', re.I)
FORBID = re.compile(r'不要联网|别联网|不联网|禁止联网|只根据这段文字|只凭记忆')


def validate(raw, web):
    if not isinstance(raw, dict) or set(raw)-set(DEFAULTS):raise ValueError('Invalid bilibili fields')
    cfg=DEFAULTS|raw
    if (type(cfg['enabled']) is not bool or cfg['trigger']!='explicit' or cfg['auth_mode'] not in ('none','sessdata')
        or cfg['preferred_language'] not in ('zh','en') or cfg['long_subtitle_policy'] not in ('excerpt','reject')
        or cfg['enabled'] and not web['enabled']):raise ValueError('Invalid bilibili mode')
    for key,lo,hi in [('max_duration_seconds',60,1200),('max_subtitle_response_bytes',65536,1048576),
                      ('max_evidence_bytes',1000,6000),('cache_ttl_seconds',0,600)]:
        if type(cfg[key]) is not int or not lo<=cfg[key]<=hi:raise ValueError('Invalid bilibili.'+key)
    return cfg


def locator(value):
    if re.fullmatch(ID,value):return (value,1)
    if not value.startswith(('http://','https://')):value='https://'+value
    safe_url(value)
    u=urlsplit(value)
    if u.scheme!='https':raise WebFailure('bilibili_url')
    if u.hostname=='b23.tv':
        if not re.fullmatch(r'/[A-Za-z0-9]{1,32}/?',u.path):raise WebFailure('bilibili_url')
        return ('https://b23.tv'+u.path.rstrip('/'),None)
    if u.hostname not in ('www.bilibili.com','bilibili.com','m.bilibili.com'):raise WebFailure('bilibili_url')
    match=re.fullmatch('/video/('+ID+')/?',u.path)
    if not match:raise WebFailure('bilibili_url')
    query=parse_qs(u.query,keep_blank_values=True,max_num_fields=32);pages=query.get('p',['1'])
    if len(pages)!=1 or not re.fullmatch('[1-9][0-9]{0,3}',pages[0]):raise WebFailure('bilibili_page')
    return match[1],int(pages[0])


def current_locators(question, mentioned=False):
    if FORBID.search(question):return None
    links=list(LINK.finditer(question));remaining=question
    for m in reversed(links):remaining=remaining[:m.start()]+' '*len(m.group())+remaining[m.end():]
    bare=BARE.findall(remaining)
    if not links and not bare:return None
    if not mentioned and not REQUEST.search(question):return None
    # Any other visible URL is ambiguity, never silently drop it.
    if re.search(r'https?://',remaining,re.I):raise WebFailure('bilibili_multiple')
    values=list(dict.fromkeys([locator(m.group().rstrip(')]')) for m in links]+[(x,1) for x in bare]))
    if len(values)>3:raise WebFailure('bilibili_multiple')
    return tuple(values)
