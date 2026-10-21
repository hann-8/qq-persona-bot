"""Explicit project trust/DoH policy. Never changes machine network settings."""
import asyncio
import json
from pathlib import Path
import re
import socket
import ssl
import time
from urllib.parse import urlsplit, parse_qsl
import aiohttp

DEFAULTS = dict(resolver='system', ca_bundle_file=None)
CA_FILE = 'secrets/public-network-ca.local.pem'
DOH_HOST = 'cloudflare-dns.com'


def failure_status(error):
    """aiohttp may wrap a DoH TLS failure as a DNS OSError: keep its cause."""
    seen=set();current=error
    while current is not None and id(current) not in seen and len(seen)<8:
        seen.add(id(current))
        if isinstance(current,aiohttp.ClientConnectorCertificateError):
            return dict(status='NETWORK_TLS_UNVERIFIED',verify_code=getattr(current.certificate_error,'verify_code',None))
        if isinstance(current,ssl.SSLCertVerificationError):
            return dict(status='NETWORK_TLS_UNVERIFIED',verify_code=getattr(current,'verify_code',None))
        current=current.__cause__ or current.__context__
    from .public_http import WebFailure
    return dict(status=str(error) if isinstance(error,WebFailure) else type(error).__name__)


def validate_network(raw):
    if not isinstance(raw,dict) or set(raw)-set(DEFAULTS):raise ValueError('Invalid public_network')
    cfg=DEFAULTS | raw
    if cfg['resolver'] not in ('system','cloudflare_doh') or cfg['ca_bundle_file'] not in (None,CA_FILE):
        raise ValueError('Invalid public_network mode/CA')
    return cfg


def tls_context(network=None,root=None):
    from .public_http import WebFailure
    cfg=validate_network(network or {})
    # Avoid SSL_CERT_FILE/SSL_CERT_DIR environment overrides. Windows system CA
    # store plus Python's compiled defaults, then an explicitly reviewed project CA.
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    if hasattr(ssl,'enum_certificates'):
        for store in ('CA','ROOT'):
            for cert,encoding,trust in ssl.enum_certificates(store):
                if encoding=='x509_asn' and (trust is True or ssl.Purpose.SERVER_AUTH.oid in trust):
                    ctx.load_verify_locations(cadata=cert)
    paths=ssl.get_default_verify_paths()
    for key in ('openssl_cafile','openssl_capath'):
        path=getattr(paths,key)
        if path and Path(path).exists():
            ctx.load_verify_locations(**{('cafile' if key.endswith('cafile') else 'capath'):path})
    if cfg['ca_bundle_file']:
        if root is None:raise WebFailure('ca_root_required')
        from .config_files import plain_path
        from cryptography import x509
        try:
            path=plain_path(root,Path(root)/CA_FILE)
            if path.stat().st_size>1048576:raise ValueError()
            with path.open('rb') as stream:data=stream.read(1048577)
            if len(data)>1048576:raise ValueError()
            pattern=rb'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----'
            blocks=re.findall(pattern,data,re.S)
            if not blocks or re.sub(pattern,b'',data,flags=re.S).strip():raise ValueError()
            for block in blocks:
                cert=x509.load_pem_x509_certificate(block)
                if not cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca:raise ValueError()
            ctx.load_verify_locations(cadata=data.decode('ascii'))
        except (OSError,ValueError,x509.ExtensionNotFound):raise WebFailure('ca_invalid') from None
    return ctx


def page_url(value):
    from .public_http import safe_url,WebFailure
    safe_url(value);u=urlsplit(value)
    if u.hostname.lower().endswith(('.local','.internal','.lan','.home','.localhost','.test','.invalid')):raise WebFailure('blocked_host')
    for key,_ in parse_qsl(u.query):
        if re.search(r'pass|token|session|secret|credential|api.?key|auth|^key$|signature',key,re.I):raise WebFailure('credential_query')
    return value


class BootstrapResolver(aiohttp.abc.AbstractResolver):
    async def resolve(self,host,port=0,family=socket.AF_UNSPEC):
        from .public_http import WebFailure
        if host!=DOH_HOST:raise WebFailure('doh_host')
        return [dict(hostname=host,host='1.1.1.1',port=port,family=socket.AF_INET,proto=0,flags=socket.AI_NUMERICHOST)]
    async def close(self):pass


def doh_answers(data,host):
    from .public_http import safe_url,public_ip,WebFailure
    def name(value):
        if not isinstance(value,str):raise WebFailure('doh_name')
        value=value.lower().removesuffix('.')
        page_url('https://'+value)
        return value
    try:
        if type(data['Status']) is not int or data['Status']!=0 or data.get('TC',False):raise WebFailure('doh_status')
        questions=data['Question']
        if len(questions)!=1 or type(questions[0]['type']) is not int or questions[0]['type']!=1 or name(questions[0]['name'])!=host:raise WebFailure('doh_question')
        answers=data['Answer']
        if not isinstance(answers,list) or not 1<=len(answers)<=16:raise WebFailure('doh_limit')
        aliases={};records={};ttls=[];count=0
        for row in answers:
            key=name(row['name']);ttl=row['TTL']
            if type(row['type']) is not int or not isinstance(row['data'],str):raise WebFailure('doh_type')
            if type(ttl) is not int or not 0<=ttl<=2**31:raise WebFailure('doh_ttl')
            ttls.append(ttl)
            if row['type']==5:
                if key in aliases:raise WebFailure('doh_cname')
                aliases[key]=name(row['data'])
            elif row['type']==1:
                ip=public_ip(row['data'])
                if ':' in ip:raise WebFailure('doh_address')
                records.setdefault(key,[]).append(ip);count+=1
            else:raise WebFailure('doh_type')
        if count>8:raise WebFailure('doh_limit')
        seen=set();current=host
        while current in aliases:
            if current in seen or len(seen)>=8 or current in records:raise WebFailure('doh_cname')
            seen.add(current);current=aliases[current]
        if current in seen or not records.get(current) or set(aliases)|set(records)!=seen|{current}:raise WebFailure('doh_cname')
        return list(dict.fromkeys(records[current])),min(60,*ttls)
    except (KeyError,TypeError,ValueError):raise WebFailure('doh_schema') from None


async def doh_resolve(resolver,host):
    from .public_http import PublicConnector,WebFailure
    host=host.lower()
    cached=resolver.cache.get(host)
    if cached and cached[0]>time.monotonic():return cached[1]
    if resolver.audit.dns_calls>=8:raise WebFailure('dns_limit')
    resolver.audit.dns_calls+=1
    connector=PublicConnector(resolver=BootstrapResolver(),ssl=resolver.context or tls_context(),use_dns_cache=False,force_close=True,limit=1)
    async with aiohttp.ClientSession(connector=connector,trust_env=False,cookie_jar=aiohttp.DummyCookieJar(),
            auto_decompress=False,timeout=aiohttp.ClientTimeout(total=3),headers={'Accept':'application/dns-json','Accept-Encoding':'identity'}) as session:
        session._retry_connection=False
        async with session.get('https://'+DOH_HOST+'/dns-query',params={'name':host,'type':'A'},allow_redirects=False) as response:
            if response.status!=200 or response.headers.get('Content-Encoding','identity')!='identity' or response.headers.get('Content-Type','').split(';')[0] not in ('application/dns-json','application/json'):raise WebFailure('doh_response')
            body=bytearray()
            async for chunk in response.content.iter_chunked(4096):
                body.extend(chunk)
                if len(body)>32768:raise WebFailure('doh_limit')
            try:data=json.loads(body)
            except (ValueError,UnicodeError):raise WebFailure('doh_json') from None
    ips,ttl=doh_answers(data,host)
    resolver.cache[host]=(time.monotonic()+ttl,ips)
    return ips
