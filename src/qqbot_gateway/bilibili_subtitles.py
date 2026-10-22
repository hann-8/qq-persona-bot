"""One video/P/track, bounded RAM only; no player, media or model API."""
import asyncio
import copy
import hashlib
import json
import math
import re
import secrets
import time
from collections import OrderedDict
from pathlib import Path
from urllib.parse import urlencode

from .public_http import PublicHTTP, Audit, WebFailure, bilibili_url
from .bilibili_policy import DEFAULTS, BV, locator
from .vendor.bilibili_fields import PLAYER_API, subtitle_tracks, subtitle_fields


def encoded(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()


def credentials(cfg,root):
    if cfg['auth_mode']=='none':return None,'none'
    from .config_files import plain_path
    try:
        path=plain_path(Path(root),Path(root)/'secrets/bilibili-session.local.json')
        if path.stat().st_size>8192:raise ValueError()
        with path.open('rb') as stream:raw=stream.read(8193)
        if len(raw)>8192:raise ValueError()
        obj=json.loads(raw)
        if set(obj)!={'SESSDATA'} or not isinstance(obj['SESSDATA'],str) or not re.fullmatch(r'[A-Za-z0-9%_,.-]{1,4096}',obj['SESSDATA']):raise ValueError()
        value=obj['SESSDATA']
        return value,hashlib.sha256(value.encode()).hexdigest()
    except (OSError,ValueError,TypeError):raise WebFailure('auth_missing') from None


def integer(value,lo=1,hi=2**63-1):
    if type(value) is not int or not lo<=value<=hi:raise WebFailure('metadata_shape')
    return value


def parsed(text):
    try:
        def pairs(rows):
            result={}
            for k,v in rows:
                if k in result:raise ValueError()
                result[k]=v
            return result
        obj=json.loads(text,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))
        if not isinstance(obj,dict):raise ValueError()
        return obj
    except (ValueError,TypeError,RecursionError):raise WebFailure('bad_json') from None


def api_data(obj):
    if type(obj.get('code')) is not int:raise WebFailure('api_shape')
    if obj['code']!=0:
        code=obj['code']
        raise WebFailure('auth_expired' if code in (-101,-111) else 'video_missing' if code in (-404,62002) else 'video_restricted')
    if not isinstance(obj.get('data'),dict):raise WebFailure('api_shape')
    return obj['data']


def choose_track(info,preferred):
    api_data(info)
    data=info['data']
    if type(data.get('need_login_subtitle',False)) is not bool or not isinstance(data.get('subtitle',{}),dict):raise WebFailure('track_shape')
    need,tracks=subtitle_tracks(info)
    if need:raise WebFailure('need_login_subtitle')
    if not isinstance(tracks,list) or len(tracks)>64:raise WebFailure('track_shape')
    choices=[]
    for i,s in enumerate(tracks):
        if not isinstance(s,dict):raise WebFailure('track_shape')
        lan,url=subtitle_fields(s)
        if not isinstance(lan,str) or not re.fullmatch(r'[A-Za-z0-9-]{1,32}',lan) or not isinstance(url,str) or len(url)>2048:raise WebFailure('track_shape')
        if type(s.get('ai_type',0)) is not int:raise WebFailure('track_shape')
        auto=lan.startswith('ai-') or s.get('ai_type',0)!=0
        language=lan.removeprefix('ai-').split('-')[0]
        if language not in ([preferred,'en'] if preferred=='zh' else ['en']):continue
        choices.append(((0 if language==preferred else 1,1 if auto else 0,i),url,lan,auto))
    if not choices:raise WebFailure('no_subtitle')
    _,url,lan,auto=min(choices)
    if url.startswith('//'):url='https:'+url
    return bilibili_url(url,'subtitle'),lan,auto


def normalize(obj,duration):
    rows=obj.get('body')
    if not isinstance(rows,list) or not 1<=len(rows)<=10000:raise WebFailure('subtitle_shape')
    cues=[]
    for row in rows:
        if not isinstance(row,dict):raise WebFailure('subtitle_shape')
        a,b,text=row.get('from'),row.get('to'),row.get('content')
        if (type(a) not in (int,float) or type(b) not in (int,float) or not math.isfinite(a) or not math.isfinite(b)
            or not 0<=a<b<=duration or not isinstance(text,str) or len(text)>4096):raise WebFailure('subtitle_time')
        text=' '.join(text.split())
        if text:cues.append((a,b,text))
    cues.sort(key=lambda r:(r[0],r[1]))
    clean=[]
    for a,b,text in cues:
        if clean and clean[-1][2]==text and a<=clean[-1][1]+.01:
            old=clean[-1];clean[-1]=(old[0],max(old[1],b),text)
        else:clean.append((a,b,text))
    if not clean or len('\n'.join(r[2] for r in clean).encode())<80:raise WebFailure('subtitle_empty')
    return clean


class Subtitles:
    def __init__(self,cfg,web,network=None,root=None,http_factory=PublicHTTP):
        self.cfg=DEFAULTS|cfg;self.web={k:v for k,v in web.items() if not k.startswith('_') and k!='public_network'};self.network=network or {};self.root=root
        self.http_factory=http_factory;self.cache=OrderedDict();self.flights={};self.last_audit={}

    async def get(self,locators,scope):
        self.last_audit={}
        # Unknown scope never shares a cache/flight with another caller.
        scope=scope or secrets.token_hex(32)
        cookie,revision=credentials(self.cfg,self.root)
        policy=hashlib.sha256(encoded([self.cfg,self.network,self.web,'lap06-v1'])).hexdigest()
        prefix=(scope,self.cfg['preferred_language'],self.cfg['auth_mode'],revision,policy)
        now=time.monotonic()
        for key in list(self.cache):
            if self.cache[key][0]<=now:self.cache.pop(key)
        aliases=set(locators)
        for key,(expiry,size,known,payload) in list(self.cache.items()):
            if key[:5]==prefix and aliases<=known:
                self.cache.move_to_end(key);self.last_audit={'cache_hit':True,'http_calls':0}
                return json.loads(payload)
        flight_key=prefix+(tuple(sorted(locators,key=str)),)
        if flight_key not in self.flights:
            if len(self.flights)>=32:raise WebFailure('subtitle_busy')
            self.flights[flight_key]=[asyncio.create_task(self._load(locators,prefix,cookie)),0]
        flight=self.flights[flight_key];flight[1]+=1
        try:return copy.deepcopy(await asyncio.shield(flight[0]))
        finally:
            flight[1]-=1
            if not flight[1]:
                self.flights.pop(flight_key,None)
                if not flight[0].done():flight[0].cancel()
                await asyncio.gather(flight[0],return_exceptions=True)

    async def _load(self,locators,prefix,cookie):
        audit=Audit();known=set(locators);started=time.monotonic()
        cfg=dict(self.web,timeout_seconds=min(15,self.web['timeout_seconds']),max_redirects=2,
                 max_response_bytes=self.cfg['max_subtitle_response_bytes'],public_network=self.network,_root=self.root)
        http=self.http_factory(cfg,audit)
        async def get(url,purpose):
            bilibili_url(url,purpose)
            # PublicHTTP counts every redirect. Fakes must preserve this contract.
            if audit.http_calls>=6:raise WebFailure('http_limit')
            kwargs={'purpose':purpose}
            if cookie is not None and purpose=='bilibili_api':kwargs['credential']=cookie
            text,final,mime=await http.get(url,**kwargs)
            if len(text.encode())>cfg['max_response_bytes']:raise WebFailure('response_limit')
            return text,final,mime
        async def api(url):
            text,_,_=await get(url,'bilibili_api');return parsed(text)
        try:
            async with asyncio.timeout_at(started+cfg['timeout_seconds']):
                resolved={};canonical=None;metadata=None
                short_hops=0
                for ident,page in locators:
                    while page is None:
                        if short_hops>=2:raise WebFailure('redirect_limit')
                        _,final,_=await get(ident,'bilibili_short');short_hops+=1
                        ident,page=locator(final);known.add((ident,page))
                    if ident not in resolved:
                        field='bvid' if ident.startswith('BV') else 'aid'
                        obj=api_data(await api('https://api.bilibili.com/x/web-interface/view?'+urlencode({field:ident if field=='bvid' else ident[2:]})))
                        if not isinstance(obj.get('bvid'),str) or not re.fullmatch(BV,obj['bvid']):raise WebFailure('metadata_shape')
                        aid=integer(obj.get('aid'))
                        if (field=='bvid' and obj['bvid']!=ident) or (field=='aid' and str(aid)!=ident[2:]):raise WebFailure('metadata_identity')
                        resolved[ident]=obj;resolved[obj['bvid']]=obj;resolved['av'+str(aid)]=obj
                    obj=resolved[ident];pages=obj.get('pages')
                    if not isinstance(pages,list) or not 1<=len(pages)<=1000 or page>len(pages):raise WebFailure('bilibili_page')
                    item=pages[page-1]
                    if not isinstance(item,dict) or integer(item.get('page'))!=page:raise WebFailure('metadata_shape')
                    cid=integer(item.get('cid'));duration=integer(item.get('duration'),1,864000)
                    if duration>self.cfg['max_duration_seconds']:raise WebFailure('video_too_long')
                    current=(obj['bvid'],cid,page)
                    if canonical is not None and current!=canonical:raise WebFailure('bilibili_multiple')
                    canonical=current;metadata=(obj,item,duration)
                    known.update(((obj['bvid'],page),('av'+str(obj['aid']),page)))
                bvid,cid,page=canonical;obj,item,duration=metadata
                info=await api(PLAYER_API+'?'+urlencode({'bvid':bvid,'cid':cid}))
                url,lan,auto=choose_track(info,self.cfg['preferred_language'])
                text,_,_=await get(url,'subtitle');cues=[list(row) for row in normalize(parsed(text),duration)]
                title=obj.get('title');part=item.get('part')
                if not isinstance(title,str) or not isinstance(part,str):raise WebFailure('metadata_shape')
                body='\n'.join(r[2] for r in cues)
                source=dict(title=title[:120],url='https://www.bilibili.com/video/'+bvid+(f'?p={page}' if page!=1 else ''),
                            status='subtitle',_policy=self.cfg['long_subtitle_policy'],_cap=self.cfg['max_evidence_bytes'],text=body,_full_text=body,_cues=cues,duration=duration,page=page,
                            bvid=bvid,cid=cid,part=part[:80],language=lan,subtitle_type='automatic' if auto else 'manual')
                if time.monotonic()>=started+cfg['timeout_seconds']:raise TimeoutError()
                payload=encoded(source);size=len(payload)+2048;key=prefix+(bvid,cid,page,lan)
                if self.cfg['cache_ttl_seconds'] and size<=128*1024:
                    self.cache[key]=(time.monotonic()+self.cfg['cache_ttl_seconds'],size,known,payload)
                    self.cache.move_to_end(key)
                    while len(self.cache)>32 or sum(x[1] for x in self.cache.values())>4*1024*1024:self.cache.popitem(last=False)
                return source
        finally:
            audit.latency=round(time.monotonic()-started,3);self.last_audit=vars(audit)


def select_source(source,cap,policy,complete):
    cues=source['_cues'];body=source['_full_text'];total=len(body.encode())
    rows=[];pos=0
    for a,b,text in cues:
        rows.append((a,b,text,pos,pos+len(text)));pos+=len(text)+1
    if total<=cap:chosen=rows;coverage='full'
    else:
        if policy=='reject' or complete:raise WebFailure('evidence_full_required')
        zones=[[] for _ in range(6)]
        for row in rows:zones[min(5,int(row[0]*6/source['duration']))].append(row)
        populated=sum(bool(z) for z in zones);chosen=[];used_zones=0
        for i,zone in enumerate(zones):
            used=0;window=[]
            for row in (reversed(zone) if i==5 else zone):
                size=len(row[2].encode())+1
                if used+size>(cap-6)//6:break
                window.append(row);used+=size
            if window:used_zones+=1;chosen.extend(window)
        chosen.sort(key=lambda r:r[3])
        if used_zones<min(4,populated) or populated<min(4,len(rows)):raise WebFailure('evidence_insufficient')
        coverage='excerpt'
    text='\n'.join(r[2] for r in chosen);size=len(text.encode())
    if coverage=='excerpt' and size<1200:raise WebFailure('evidence_insufficient')
    intervals=[]
    for a,b,*_ in chosen:
        if intervals and a<=intervals[-1][1]:intervals[-1][1]=max(b,intervals[-1][1])
        else:intervals.append([a,b])
    gaps=[];last=0
    for a,b in intervals:
        if a>last:gaps.append([last,a])
        last=b
    if last<source['duration']:gaps.append([last,source['duration']])
    ranges=[]
    for r in chosen:
        if ranges and r[3]==ranges[-1][1]+1:ranges[-1][1]=r[4]
        else:ranges.append([r[3],r[4]])
    row={k:v for k,v in source.items() if not k.startswith('_')}
    row.update(text=text,coverage=coverage,ranges=[[0,len(body)]] if coverage=='full' else ranges,
               input_bytes=total,selected_bytes=size,truncated=coverage=='excerpt',time_ranges=intervals,time_gaps=gaps,
               time_coverage=round(sum(b-a for a,b in intervals)/source['duration'],6))
    return row
