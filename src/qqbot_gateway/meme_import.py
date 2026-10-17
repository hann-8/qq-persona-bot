"""Explicit favorites management client. Never exposed as a model tool."""
import asyncio
import json
import secrets
import time
from urllib.parse import urlsplit,urljoin
import aiohttp
from .meme_catalog import MemeCatalog,controlled_path
from .web_retrieval import safe_url,PublicResolver,PublicConnector,WebFailure

# Exact hosts in installed NapCat 4.18.38 napcat.mjs:4883/14351.
MEDIA_HOSTS=frozenset({'gchat.qpic.cn','multimedia.nt.qq.com.cn'})


def media_url(url):
    try:safe_url(url)
    except WebFailure:raise ValueError('Invalid QQ media URL') from None
    u=urlsplit(url)
    if u.scheme!='https' or u.hostname not in MEDIA_HOSTS:raise ValueError('Unverified QQ media host')
    return url


def admin_token(root,create=False):
    path=controlled_path(root,'secrets/memes-admin.local.json')
    if not path.exists():
        if not create:return None
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('x',encoding='utf-8') as f:json.dump({'token':secrets.token_urlsafe(48)},f)
    obj=json.loads(path.read_text(encoding='utf-8'))
    token=obj.get('token')
    if not isinstance(token,str) or len(token)<32:raise ValueError('Invalid memes admin token')
    return token


async def download(url,maximum,budget=None):
    connector=PublicConnector(resolver=PublicResolver(),use_dns_cache=False,force_close=True,limit=1)
    async with aiohttp.ClientSession(connector=connector,trust_env=False,cookie_jar=aiohttp.DummyCookieJar(),
            auto_decompress=False,timeout=aiohttp.ClientTimeout(total=10),headers={'Accept-Encoding':'identity'}) as session:
        for hop in range(3):
            media_url(url)
            async with session.get(url,allow_redirects=False) as response:
                if response.status in (301,302,303,307,308):
                    if hop==2:raise ValueError('Redirect limit')
                    url=media_url(urljoin(url,response.headers.get('Location','')));continue
                if response.status!=200 or response.headers.get('Content-Encoding','identity')!='identity':raise ValueError('Media unavailable')
                if response.headers.get('Content-Type','').split(';')[0] not in ('image/png','image/jpeg','image/webp','image/gif','application/octet-stream'):raise ValueError('Non-image response')
                data=bytearray()
                async for chunk in response.content.iter_chunked(16384):
                    if budget is not None:
                        budget['bytes']+=len(chunk)
                        if budget['bytes']>128*1024*1024:raise ValueError('Import total limit')
                    data.extend(chunk)
                    if len(data)>maximum:raise ValueError('Media size limit')
                return bytes(data)
    raise ValueError('Media unavailable')


async def favorites(root,cfg,port,*,basic=False,fetch=download):
    catalog=MemeCatalog(root,cfg);cfg=catalog.cfg;token=admin_token(root)
    if not token:raise ValueError('Initialize admin token, then next gate startup loads it')
    accepted=failed=total=0
    wire_budget={'bytes':0}
    # Fixed endpoint/action only; URL input cannot come from caller/model.
    async with asyncio.timeout(60):
        async with aiohttp.ClientSession(trust_env=False,cookie_jar=aiohttp.DummyCookieJar(),timeout=aiohttp.ClientTimeout(total=8)) as session:
            async with session.post(f'http://127.0.0.1:{port}/admin/memes/favorites',
                    headers={'Authorization':'Bearer '+token},json={'count':cfg['import_count'],'mode':'basic' if basic else 'detail'},allow_redirects=False) as response:
                if response.status!=200:raise ValueError('Favorites unavailable; no login/start/retry attempted')
                raw=await response.content.read(1048577)
                if len(raw)>1048576:raise ValueError('Favorites response too large')
                rows=json.loads(raw)
        if not isinstance(rows,list) or len(rows)>cfg['import_count']:raise ValueError('Invalid favorites response')
        for row in rows:
            try:
                url=row if isinstance(row,str) else row.get('url') if isinstance(row,dict) else None
                media_url(url)
                if wire_budget['bytes']>=128*1024*1024:raise ValueError('Import total limit')
                maximum=min(cfg['max_file_bytes'],128*1024*1024-total)
                data=await download(url,maximum,wire_budget) if fetch is download else await fetch(url,maximum)
                total+=len(data)
                if total>128*1024*1024:raise ValueError('Import total limit')
                catalog.add(data);accepted+=1
            except (ValueError,OSError,aiohttp.ClientError,TimeoutError,WebFailure):failed+=1
        # Metadata/URLs from QQ are never persisted. Operator confirms labels locally.
        catalog.stage()
    return accepted,failed
