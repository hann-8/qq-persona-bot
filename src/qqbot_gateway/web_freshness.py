"""Bounded date facts and Shanghai windows. No I/O, no guessed timestamps."""
from datetime import datetime,timedelta,timezone
import re
SH=timezone(timedelta(hours=8))
SOURCES={'meta','jsonld','time','none'}
FIELDS={'requested_at','fetched_at','published_at','modified_at','date_source','date_precision','freshness_status'}

def parse(value):
    if not isinstance(value,str) or len(value)>80:return None,'unknown'
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:\d{2})?)?',value):return None,'unknown'
    try:d=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError:return None,'unknown'
    if d.tzinfo is None:return d.replace(hour=0,minute=0,second=0,microsecond=0,tzinfo=SH),'date'
    return d.astimezone(timezone.utc),'second'

def window(question,requested_at,days=7):
    now,p=parse(requested_at)
    if not now or p!='second':raise ValueError('REQUEST_TIME_INVALID')
    n=re.search(r'(?:近|过去|最近)(\d+)天',question)
    if n:
        days=int(n[1])
        if not 1<=days<=30:raise ValueError('WINDOW_TOO_LONG')
    if re.search(r'过去24小时|近24小时',question):return now-timedelta(hours=24),now,True
    if '今天' in question:return now.astimezone(SH).replace(hour=0,minute=0,second=0,microsecond=0),now,False
    if '本周' in question:
        day=now.astimezone(SH).replace(hour=0,minute=0,second=0,microsecond=0)
        return day-timedelta(days=day.weekday()),now,False
    dates=re.findall(r'\d{4}-\d{2}-\d{2}',question)
    if dates:
        start,_=parse(dates[0]);end,_=parse(dates[-1])
        if not start or not end or end<start or (end-start).days>=30:raise ValueError('WINDOW_INVALID')
        return start,min(end+timedelta(days=1)-timedelta(microseconds=1),now),False
    if re.search(r'近\d+|过去\d+|去年|上个月',question):raise ValueError('WINDOW_UNSUPPORTED')
    return now-timedelta(days=days),now,False

def validate_candidates(rows):
    if not isinstance(rows,list) or len(rows)>24:raise ValueError('DATE_PROTOCOL')
    for row in rows:
        if not isinstance(row,dict) or set(row)!={'kind','source','value'} or row['kind'] not in ('published','modified') or row['source'] not in SOURCES-{'none'} or not isinstance(row['value'],str) or len(row['value'])>80:raise ValueError('DATE_PROTOCOL')
    return rows

def facts(rows,requested_at,fetched_at,question='',days=7):
    validate_candidates(rows)
    start,end,hour=window(question,requested_at,days)
    result=dict(requested_at=requested_at,fetched_at=fetched_at,published_at=None,modified_at=None,date_source='none',date_precision='unknown',freshness_status='unknown')
    for kind in ('published','modified'):
        candidates=[r for r in rows if r['kind']==kind]
        if not candidates:continue
        parsed=[parse(r['value']) for r in candidates]
        if any(d is None for d,p in parsed):result['freshness_status']='invalid';return result
        dates={d.astimezone(SH).date() for d,p in parsed}
        exact={d for d,p in parsed if p=='second'}
        if len(dates)>1 or len(exact)>1:result['freshness_status']='conflict';return result
        d,precision=parsed[0]
        if d>end and (precision=='second' or d.astimezone(SH).date()>end.astimezone(SH).date()):result['freshness_status']='invalid';return result
        result[kind+'_at']=d.isoformat() if precision=='second' else d.date().isoformat()
        if kind=='published':
            result.update(date_source=candidates[0]['source'],date_precision=precision)
            if hour and precision!='second':continue
            # Day precision can prove a natural-day window, never a rolling-hour boundary.
            in_range=(start<=d<=end) if precision=='second' else (start.astimezone(SH).date()<=d.date()<=end.astimezone(SH).date())
            result['freshness_status']='fresh' if in_range else 'stale'
            if re.search(r'最新.*(?:发布|版本)|最新版本',question) and not hour:result['freshness_status']='version_dated'
    if result['published_at'] and result['modified_at']:
        published,_=parse(result['published_at']);modified,_=parse(result['modified_at'])
        if modified<published:result['freshness_status']='conflict'
    return result

def validate_facts(row):
    if not isinstance(row,dict) or set(row)!=FIELDS:raise ValueError('FRESHNESS_FIELDS')
    if row['date_source'] not in SOURCES or row['date_precision'] not in ('unknown','date','second') or row['freshness_status'] not in ('unknown','conflict','invalid','fresh','stale','version_dated'):raise ValueError('FRESHNESS_ENUM')
    for k in ('requested_at','fetched_at'):
        if parse(row[k])[1]!='second':raise ValueError('FRESHNESS_TIME')
    for k in ('published_at','modified_at'):
        if row[k] is not None and parse(row[k])[0] is None:raise ValueError('FRESHNESS_DATE')
    if row['freshness_status'] in ('fresh','stale','version_dated') and (not row['published_at'] or row['date_source']=='none' or row['date_precision']=='unknown'):raise ValueError('FRESHNESS_PROOF')
    if row['published_at']:
        published,precision=parse(row['published_at']);requested,_=parse(row['requested_at'])
        if precision!=row['date_precision']:raise ValueError('FRESHNESS_PRECISION')
        future=published>requested if precision=='second' else published.date()>requested.astimezone(SH).date()
        if future and row['freshness_status'] in ('fresh','stale','version_dated'):raise ValueError('FRESHNESS_FUTURE')
    return row
