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
    async def get(self,url,*,rss=False,purpose=None):
        purpose=purpose or ('search' if rss else 'page')
        # Future Bilibili/JSON purposes need their own fixed endpoint policy;
        # declaring a purpose never grants a generic JSON downloader.
        if purpose not in ('page','search') or (purpose=='search')!=rss:raise WebFailure('purpose_denied')
        if rss and (urlsplit(url).hostname!='cn.bing.com' or urlsplit(url).path!='/search'):raise WebFailure('search_endpoint')
        connector=PublicConnector(resolver=self.resolver,ssl=self.context,use_dns_cache=False,force_close=True,limit=1)
        timeout=aiohttp.ClientTimeout(total=self.cfg['timeout_seconds'],connect=3,sock_read=6)
        async with aiohttp.ClientSession(connector=connector,timeout=timeout,trust_env=False,
                cookie_jar=aiohttp.DummyCookieJar(),auto_decompress=False,
                headers={'User-Agent':'QQbot-PublicReader/1.0','Accept-Encoding':'identity'}) as session:
            # aiohttp 3.14.5 otherwise retries idempotent requests on disconnect.
            session._retry_connection=False
            for hop in range(self.cfg['max_redirects']+1):
                page_url(url);self.audit.http_calls+=1
                if self.audit.http_calls>8:raise WebFailure('http_limit')
                async with session.get(url,allow_redirects=False) as response:
                    if response.status in (301,302,303,307,308):
                        if rss:raise WebFailure('search_redirect')
                        if hop==self.cfg['max_redirects']:raise WebFailure('redirect_limit')
                        url=page_url(urljoin(url,response.headers.get('Location','')))
                        self.audit.redirect_hops+=1;continue
                    if response.status!=200:raise WebFailure('http_status')
                    if getattr(response,'content_length',None) is not None and response.content_length>self.cfg['max_response_bytes']:raise WebFailure('response_limit')
                    mime=response.headers.get('Content-Type','').split(';')[0].lower()
                    if mime not in (('text/xml','application/rss+xml','application/xml') if rss else ('text/html','text/plain','application/xhtml+xml')):raise WebFailure('non_text')
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
                    if re.search(r'captcha|verify you are human|人机验证|验证码|access denied|sign in to continue|登录后阅读|付费阅读',text,re.I):raise WebFailure('restricted')
                    return text,str(response.url),mime
            raise WebFailure('redirect_limit')
