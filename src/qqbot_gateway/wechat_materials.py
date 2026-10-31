"""One-use source-specific material handoff; model/normalizer remain shared."""
import asyncio
import json
import os
from pathlib import Path
import time
import uuid
from .vision import normalize,NativeImage

CONFIG=Path('E:/CodexWS/WeChatbot/config/local/akasha.json')

def private_ids():
    if not CONFIG.exists():return []
    cfg=json.loads(CONFIG.read_text(encoding='utf-8'))
    return [cfg['bridge']['bot_wxid'],cfg['bridge'].get('owner_wxid',''),
            *[v for s in cfg['bridge']['sessions']+cfg['bridge']['private_sessions'] for v in (s['id'],s['name'])],
            *[v for pair in cfg.get('pairings',[]) for link in pair.get('actor_links',{}).items() for v in link]]

class WeChatMaterials:
    def __init__(self,reserve):self.reserve=reserve
    async def resolve(self,header,source,deadline):
        def read():
            root=CONFIG.parents[2]/'state/akasha-wechat';cap=header['resource_caps'][0]
            path=root/'media-caps'/(cap+'.json');used=path.with_suffix('.used')
            os.replace(path,used)  # consume before decode; never retry a different image
            try:
                value=json.loads(used.read_text(encoding='utf-8'));image=Path(value['path']).resolve()
                if value['expires']<=time.time() or value['image_ref']!=source['images'][0]['image_ref'] or not image.is_relative_to((root/'media').resolve()):raise ValueError('CURRENT_IMAGE_UNAVAILABLE')
                if image.stat().st_size>8*1024*1024:raise ValueError('IMAGE_TOO_LARGE')
                return normalize(image.read_bytes()),value['image_ref'],value['expires']
            finally:used.unlink(missing_ok=True)
        blob,ref,expiry=await asyncio.to_thread(read)
        return NativeImage(blob,self.reserve,time.monotonic()+max(0,expiry-time.time()),deadline),blob.descriptor(ref)

class WeChatMembers:
    async def resolve(self,request,source,deadline):
        cap=request['resource_caps'][len(source['images'])]
        path=CONFIG.parents[2]/'state/akasha-wechat/member-caps'/(cap+'.json')
        used=path.with_suffix('.used');os.replace(path,used)
        try:value=json.loads(used.read_text(encoding='utf-8'))
        finally:used.unlink(missing_ok=True)
        if value['expires']<=time.time():raise ValueError('MEMBER_SOURCE_EXPIRED')
        target=next(r for r in source['messages'] if r['seq']==source['target_seq']);names={}
        for m in value['members']:
            if m.get('wxid') and m.get('name'):names.setdefault(m['name'],set()).add(m['wxid'])
        candidates=[]
        for name,ids in names.items():
            if len(ids)!=1:continue
            sender=value['sender'] in ids
            if not sender and name not in target['text']:continue
            if not 1<=len(name)<=40:continue
            row=dict(member_ref=target['member_ref'] if sender else 'p_'+uuid.uuid4().hex[:16],name=name)
            if len(candidates)>=8 or len(json.dumps(candidates+[row],ensure_ascii=False).encode())>768:break
            candidates.append(row)
        return dict(candidates=candidates,receipt=uuid.uuid4().hex+uuid.uuid4().hex)
