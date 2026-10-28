"""Deterministic page dates and Shanghai request windows; no inferred current dates."""
from datetime import datetime, timedelta, timezone
import json
import re

SHANGHAI=timezone(timedelta(hours=8))
FIELDS={'requested_at','fetched_at','published_at','modified_at','date_source','date_precision','freshness_status'}


def parse_date(value):
    if not isinstance(value,str) or len(value)>80:return None,'unknown'
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:[T ][0-9:.+Z-]{5,35})?',value):return None,'unknown'
        date=datetime.fromisoformat(value.replace('Z','+00:00'))
        if date.tzinfo is None:return date.replace(hour=0,minute=0,second=0,microsecond=0,tzinfo=SHANGHAI),'date'
        return date.astimezone(timezone.utc),'instant'
    except ValueError:return None,'unknown'


def page_dates(tree,body=None):
    """Bounded meta/Article JSON-LD/main time extraction inside the worker."""
    published=[];modified=[]
    def add(bucket,value,source):
        if parse_date(value)[0] is not None:bucket.append((value,source))
    for node in tree.xpath('//meta')[:256]:
        key=(node.get('property') or node.get('name') or '').lower()
        if key in ('article:published_time','date','pubdate'):add(published,node.get('content'),'meta')
        if key=='article:modified_time':add(modified,node.get('content'),'meta')
    size=0;nodes=0
    canonical=tree.xpath('//link[@rel="canonical"]/@href')[:1]
    def walk(value,depth=0):
        nonlocal nodes
        nodes+=1
        if depth>8 or nodes>256:return
        if isinstance(value,list):
            for child in value[:256]:walk(child,depth+1)
        if isinstance(value,dict):
            kind=value.get('@type',[]);kind=[kind] if isinstance(kind,str) else kind
            page=value.get('url') or value.get('mainEntityOfPage')
            if isinstance(page,dict):page=page.get('@id')
            if isinstance(kind,list) and any(k in ('Article','NewsArticle','BlogPosting') for k in kind) and (not canonical or not page or page==canonical[0]):
                add(published,value.get('datePublished'),'json_ld');add(modified,value.get('dateModified'),'json_ld')
            for child in value.values():
                if isinstance(child,(dict,list)):walk(child,depth+1)
    for node in tree.xpath('//script[@type="application/ld+json"]')[:8]:
        raw=node.text or '';size+=len(raw.encode())
        if size>65536:break
        try:walk(json.loads(raw))
        except (ValueError,RecursionError):pass
    if body is not None:
        for value in body.xpath('.//time/@datetime')[:8]:add(published,value,'main_time')
    def choose(values):
        if not values:return None,'none',False
        dates=[parse_date(v)[0].astimezone(SHANGHAI).date() for v,_ in values]
        return values[0][0],values[0][1],len(set(dates))>1
    pub,source,conflict=choose(published);mod,_,mod_conflict=choose(modified)
    return dict(published_at=pub,modified_at=mod,date_source=source,date_conflict=conflict or mod_conflict)


def window(question,requested,days=7):
    if re.search(r'最新.*版本|最新发布|当前.*版本',question):return None,'release'
    if '今天' in question or '当日' in question:
        return requested.astimezone(SHANGHAI).replace(hour=0,minute=0,second=0,microsecond=0),'day'
    if '本周' in question:
        local=requested.astimezone(SHANGHAI)
        return (local-timedelta(days=local.weekday())).replace(hour=0,minute=0,second=0,microsecond=0),'day'
    hours=re.search(r'(?:过去|近)(\d+)小时',question)
    count=re.search(r'(?:过去|近|最近)(\d+)天',question)
    if hours:
        n=int(hours[1])
        if not 1<=n<=720:raise ValueError('window')
        return requested-timedelta(hours=n),'hour'
    if count:
        days=int(count[1])
        if not 1<=days<=30:raise ValueError('window')
    return requested-timedelta(days=days),'day'


def assess(source,question,requested,days=7):
    pub,precision=parse_date(source.get('published_at'));mod,mod_precision=parse_date(source.get('modified_at'))
    start,kind=window(question,requested,days)
    status='unknown'
    if source.get('date_conflict'):status='conflict'
    elif pub:
        if pub>requested+timedelta(minutes=5) or mod and (mod<pub or mod>requested+timedelta(minutes=5)):status='invalid'
        elif kind=='hour' and precision!='instant':status='unknown'
        elif start is None:status='release_unverified'
        elif (pub+timedelta(days=1) if precision=='date' else pub)<=start:status='stale'
        elif precision=='date' and pub<start:status='unknown'
        else:status='fresh'
    return dict(requested_at=requested.astimezone(timezone.utc).isoformat(),fetched_at=source['fetched_at'],
        published_at=source.get('published_at'),modified_at=source.get('modified_at'),
        date_source=source.get('date_source','none'),date_precision=precision,freshness_status=status)


def validate(value):
    if not isinstance(value,dict) or set(value)!=FIELDS:raise ValueError('freshness fields')
    if value['date_source'] not in ('none','meta','json_ld','main_time','legacy'):raise ValueError('date source')
    if value['date_precision'] not in ('unknown','date','instant'):raise ValueError('date precision')
    if value['freshness_status'] not in ('fresh','stale','unknown','invalid','conflict','release_unverified'):raise ValueError('freshness status')
    for key in ('requested_at','fetched_at'):
        if parse_date(value[key])[1]!='instant':raise ValueError('request date')
    for key in ('published_at','modified_at'):
        if value[key] is not None and parse_date(value[key])[0] is None:raise ValueError('page date')
    return value


def official_release(source,question):
    from urllib.parse import urlsplit
    url=urlsplit(source['url']);host=(url.hostname or '').lower()
    query=question.casefold();body=(source['title']+' '+source['_full_text']).casefold()
    subjects={'python.org':'python','nodejs.org':'node','rust-lang.org':'rust','go.dev':'go','kernel.org':'linux'}
    entity=next((name for domain,name in subjects.items() if (host==domain or host.endswith('.'+domain)) and name in query),None)
    if host=='github.com':
        parts=url.path.strip('/').split('/')
        if len(parts)>=4 and parts[2]=='releases' and parts[1].casefold() in query:entity=parts[1].casefold()
    index=bool(re.search(r'/(?:downloads?/?|releases/latest/?)$',url.path) and re.search(r'latest|最新|当前版本',body))
    return bool(entity and index and re.search(r'\b\d+\.\d+(?:\.\d+)?',body) and re.search(r'release|发布|版本',body))
