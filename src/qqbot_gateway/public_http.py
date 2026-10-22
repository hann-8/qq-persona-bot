"""Project public HTTP; compatibility boundary for webpage and image callers."""
import asyncio
from dataclasses import dataclass,field
import ipaddress
import json
import re
import socket
import time
from urllib.parse import urlsplit, urljoin
import zlib
import aiohttp
from .public_network import validate_network, tls_context, doh_resolve, page_url

class WebFailure(Exception):pass


def public_ip(value):
    ip=ipaddress.ip_address(value)
    if not ip.is_global or ip.is_multicast or ip.is_reserved or getattr(ip,'ipv4_mapped',None):raise WebFailure('blocked_ip')
    return str(ip)


def safe_url(value):
    if not isinstance(value,str) or len(value)>2048 or re.search(r'[\x00-\x20\\]',value):raise WebFailure('blocked_url')
    try:
        u=urlsplit(value)
        if (u.scheme not in ('http','https') or not u.hostname or u.username is not None or u.password is not None
                or u.fragment or u.port not in (None,80 if u.scheme=='http' else 443)):
            raise WebFailure('blocked_url')
        host=u.hostname.encode('idna').decode('ascii')
        if '%' in host or host.endswith('.') or host.lower()=='localhost' or '.' not in host and ':' not in host:raise WebFailure('blocked_host')
        try:public_ip(host)
        except ValueError:
            if re.fullmatch(r'[0-9.xXa-fA-F]+',host):raise WebFailure('ambiguous_ip')
        return value
    except (ValueError,UnicodeError):raise WebFailure('blocked_url') from None


class PublicResolver(aiohttp.abc.AbstractResolver):
    def __init__(self,network=None,context=None,audit=None):
        self.network=validate_network(network or {});self.context=context
        self.audit=audit or Audit();self.cache={}
    async def resolve(self,host,port=0,family=socket.AF_UNSPEC):
        safe_url('https://'+('['+host+']' if ':' in host else host))
        if self.network['resolver']=='cloudflare_doh':
            rows=await doh_resolve(self,host)
            return [dict(hostname=host,host=ip,port=port,family=socket.AF_INET,proto=0,flags=socket.AI_NUMERICHOST) for ip in rows]
        loop=asyncio.get_running_loop()
        rows=await loop.getaddrinfo(host,port,type=socket.SOCK_STREAM,family=family)
        if not rows:raise WebFailure('dns_empty')
        # Reject mixed public/private results too. The connector uses these exact IPs.
        for row in rows:public_ip(row[4][0])
        return [dict(hostname=host,host=row[4][0],port=port,family=row[0],proto=0,flags=socket.AI_NUMERICHOST) for row in rows]
    async def close(self):pass


class PublicConnector(aiohttp.TCPConnector):
    async def _wrap_create_connection(self,*args,**kwargs):
        expected={public_ip(row[4][0]) for row in kwargs['addr_infos']}
        transport,protocol=await super()._wrap_create_connection(*args,**kwargs)
        try:
            peer=public_ip(transport.get_extra_info('peername')[0])
            if peer not in expected:raise WebFailure('peer_mismatch')
        except Exception:
            transport.close();raise WebFailure('peer_blocked') from None
        return transport,protocol


@dataclass
class Audit:
    dns_calls: int=0
    failures: list=field(default_factory=list)
    search_calls: int=0
    fetch_calls: int=0
    http_calls: int=0
    redirect_hops: int=0
    bytes: int=0
    latency: float=0


class PublicHTTP:
    def __init__(self,cfg,audit):
        self.cfg=cfg;self.audit=audit
        self.context=tls_context(cfg.get('public_network'),cfg.get('_root'))
        self.resolver=PublicResolver(cfg.get('public_network'),self.context,audit)
    async def get(self,url,*,rss=False,purpose=None,credential=None):
        purpose=purpose or ('search' if rss else 'page')
        # Future Bilibili/JSON purposes need their own fixed endpoint policy;
        # declaring a purpose never grants a generic JSON downloader.
        special=purpose in ('bilibili_api','subtitle','bilibili_short')
        if not special and (purpose not in ('page','search') or (purpose=='search')!=rss):raise WebFailure('purpose_denied')
        if special and rss:raise WebFailure('purpose_denied')
        if credential is not None and (purpose!='bilibili_api' or not re.fullmatch(r'[A-Za-z0-9%_,.-]{1,4096}',credential)):raise WebFailure('credential_denied')
        if special:bilibili_url(url,purpose)
        if rss and (urlsplit(url).hostname!='cn.bing.com' or urlsplit(url).path!='/search'):raise WebFailure('search_endpoint')
        connector=PublicConnector(resolver=self.resolver,ssl=self.context,use_dns_cache=False,force_close=True,limit=1)
        timeout=aiohttp.ClientTimeout(total=self.cfg['timeout_seconds'],connect=3,sock_read=6)
        async with aiohttp.ClientSession(connector=connector,timeout=timeout,trust_env=False,
                cookie_jar=aiohttp.DummyCookieJar(),auto_decompress=False,
                headers={'User-Agent':'QQbot-PublicReader/1.0','Accept-Encoding':'identity'}) as session:
            # aiohttp 3.14.5 otherwise retries idempotent requests on disconnect.
            session._retry_connection=False
            for hop in range(self.cfg['max_redirects']+1):
                bilibili_url(url,purpose) if special else page_url(url)
                if self.audit.http_calls>=(6 if special else 8):raise WebFailure('http_limit')
                self.audit.http_calls+=1
                headers={'Cookie':'SESSDATA='+credential} if credential is not None else {}
                async with session.get(url,allow_redirects=False,headers=headers) as response:
                    if response.status in (301,302,303,307,308):
                        if rss or purpose=='bilibili_api':raise WebFailure('api_redirect' if special else 'search_redirect')
                        if purpose=='bilibili_short':
                            final=urljoin(url,response.headers.get('Location',''))
                            from .bilibili_policy import locator
                            locator(final)  # validate before caller considers any next request
                            return '',final,'redirect'
                        if hop==self.cfg['max_redirects']:raise WebFailure('redirect_limit')
                        url=urljoin(url,response.headers.get('Location',''))
                        bilibili_url(url,purpose) if special else page_url(url)
                        self.audit.redirect_hops+=1;continue
                    if response.status!=200:raise WebFailure('http_'+str(response.status) if special else 'http_status')
                    if purpose=='bilibili_short':raise WebFailure('short_no_redirect')
                    if getattr(response,'content_length',None) is not None and response.content_length>self.cfg['max_response_bytes']:raise WebFailure('response_limit')
                    mime=response.headers.get('Content-Type','').split(';')[0].lower()
                    if mime not in (('application/json','text/json') if special else ('text/xml','application/rss+xml','application/xml') if rss else ('text/html','text/plain','application/xhtml+xml')):raise WebFailure('non_text')
                    encoding=response.headers.get('Content-Encoding','identity').lower()
                    if encoding not in ('identity','gzip','deflate'):raise WebFailure('encoding')
                    decoder=zlib.decompressobj(31 if encoding=='gzip' else 15) if encoding!='identity' else None
                    out=bytearray();wire=0;cap=self.cfg['max_response_bytes']
                    async for chunk in response.content.iter_chunked(16384):
                        wire+=len(chunk);self.audit.bytes+=len(chunk)
                        if wire>cap:raise WebFailure('response_limit')
                        try:part=decoder.decompress(chunk,cap+1-len(out)) if decoder else chunk
                        except zlib.error:raise WebFailure('encoding') from None
                        out.extend(part)
                        if len(out)>cap or decoder and decoder.unconsumed_tail:raise WebFailure('response_limit')
                    if decoder and (not decoder.eof or decoder.unused_data):raise WebFailure('encoding')
                    charset=response.charset or 'utf-8'
                    try:text=out.decode(charset,errors='replace')
                    except LookupError:raise WebFailure('charset') from None
                    if not special and re.search(r'captcha|verify you are human|人机验证|验证码|access denied|sign in to continue|登录后阅读|付费阅读',text,re.I):raise WebFailure('restricted')
                    return text,str(response.url),mime
            raise WebFailure('redirect_limit')


def bilibili_url(url,purpose):
    """Purpose-bound HTTPS endpoints; credentials can only reach these two APIs."""
    safe_url(url);u=urlsplit(url)
    if u.scheme!='https':raise WebFailure('bilibili_url')
    if purpose=='bilibili_api':
        from urllib.parse import parse_qs
        from .bilibili_policy import BV
        q=parse_qs(u.query,keep_blank_values=True,max_num_fields=4)
        if u.hostname!='api.bilibili.com' or u.path not in ('/x/web-interface/view','/x/player/wbi/v2'):raise WebFailure('bilibili_api')
        fields={'bvid','cid'} if 'bvid' in q else {'aid','cid'}
        if u.path.endswith('/view'):fields.discard('cid')
        if set(q)!=fields or any(len(v)!=1 for v in q.values()):raise WebFailure('bilibili_api')
        for k,v in q.items():
            if not re.fullmatch(BV if k=='bvid' else '[1-9][0-9]{0,18}',v[0]):raise WebFailure('bilibili_api')
    elif purpose=='subtitle':
        if u.hostname not in ('aisubtitle.hdslb.com','i0.hdslb.com','i1.hdslb.com') or not re.fullmatch(r'/bfs/(?:ai_subtitle|subtitle)/[A-Za-z0-9_./-]+',u.path) or any(x in u.path.split('/') for x in ('.','..')):raise WebFailure('subtitle_url')
    elif purpose=='bilibili_short':
        if u.hostname!='b23.tv' or u.query or not re.fullmatch('/[A-Za-z0-9]{1,32}',u.path):raise WebFailure('short_url')
    else:raise WebFailure('purpose_denied')
    return url
