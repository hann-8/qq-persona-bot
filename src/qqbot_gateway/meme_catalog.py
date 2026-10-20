"""Local, hash-bound image library. No user content is logged or uploaded."""
from pathlib import Path
import hashlib
import io
import json
import os
import re
import tempfile
import warnings
import yaml
from PIL import Image

DEFAULTS=dict(enabled=False,inbox_dir='assets/memes/inbox',library_dir='assets/memes/library',
    catalog_file='config/memes.local.yaml',max_candidates=16,catalog_prompt_max_bytes=2000,
    max_images_per_turn=1,cooldown_seconds=60,same_meme_cooldown_seconds=300,
    allow_meme_only=True,max_file_bytes=8388608,import_count=48)
FORMATS={'PNG':('image/png','.png'),'JPEG':('image/jpeg','.jpg'),'WEBP':('image/webp','.webp'),'GIF':('image/gif','.gif')}


def validate_memes(value):
    if not isinstance(value,dict) or set(value)-set(DEFAULTS):raise ValueError('Invalid memes settings')
    cfg=DEFAULTS|value
    for key in ('enabled','allow_meme_only'):
        if type(cfg[key]) is not bool:raise ValueError('Invalid memes boolean')
    for key,lo,hi in [('max_candidates',1,32),('catalog_prompt_max_bytes',500,4000),('max_images_per_turn',1,1),
        ('cooldown_seconds',0,600),('same_meme_cooldown_seconds',0,3600),('max_file_bytes',1048576,8388608),('import_count',1,48)]:
        if type(cfg[key]) is not int or not lo<=cfg[key]<=hi:raise ValueError('Invalid memes range')
    for key in ('inbox_dir','library_dir','catalog_file'):
        v=cfg[key]
        if not isinstance(v,str) or not v or '\\' in v or ':' in v or v.startswith('/') or any(x in ('.','..','') for x in v.split('/')):raise ValueError('Invalid memes path')
        # All accepted locations are already ignored before any user asset is created.
        if v!=DEFAULTS[key]:raise ValueError('Memes paths must use reserved ignored locations')
    return cfg


def controlled_path(root,relative):
    root=Path(root).resolve();p=root/relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts:raise ValueError('Unsafe image path')
    current=p
    while current!=root:
        if current.is_symlink() or current.is_junction():raise ValueError('Linked image path')
        if current.parent==current:raise ValueError('Unsafe image path')
        current=current.parent
    if not p.resolve().is_relative_to(root):raise ValueError('Image outside project')
    return p


def inspect_image(data,maximum=8388608,suffix=None):
    if not 0<len(data)<=maximum:raise ValueError('Image byte limit')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as im:
                mime,ext=FORMATS[im.format]
                if suffix and suffix.lower() not in ({'.jpg','.jpeg'} if ext=='.jpg' else {ext}):raise ValueError('Disguised image')
                w,h=im.size;frames=getattr(im,'n_frames',1)
                if not 0<w<=4096 or not 0<h<=4096 or w*h>16000000 or frames>120 or w*h*frames>128000000:raise ValueError('Image decode limit')
                decoded_pixels=0
                for i in range(frames):
                    im.seek(i)
                    decoded_pixels+=im.width*im.height
                    if im.width>4096 or im.height>4096 or im.width*im.height>16000000 or decoded_pixels>128000000:raise ValueError('Frame limit')
                    im.load()
        return dict(sha256=hashlib.sha256(data).hexdigest(),media_type=mime,extension=ext)
    except Exception:raise ValueError('Invalid or unsupported image') from None


def atomic_yaml(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.memes-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            yaml.safe_dump(value,f,allow_unicode=True,sort_keys=False);f.flush();os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


def read_catalog_yaml(path):
    if path.stat().st_size>1048576:raise ValueError('Catalog too large')
    try:return yaml.safe_load(path.read_text(encoding='utf-8'))
    except (yaml.YAMLError,UnicodeError):raise ValueError('Invalid local catalog YAML') from None


class MemeCatalog:
    def __init__(self,root,cfg=None,*,config_guard=None):
        self.config_guard=config_guard
        self.root=Path(root).resolve();self.cfg=validate_memes(cfg or {});self.rows=[]
        self.path=controlled_path(self.root,self.cfg['catalog_file'])
        if self.path.exists():
            if self.path.stat().st_size>1048576:raise ValueError('Catalog too large')
            obj=read_catalog_yaml(self.path)
            if not isinstance(obj,dict) or obj.get('version')!=1 or not isinstance(obj.get('items'),list) or len(obj['items'])>1000:raise ValueError('Invalid catalog')
            seen=set()
            for row in obj['items']:
                self.validate_row(row)
                if row['id'] in seen:raise ValueError('Duplicate meme ID')
                seen.add(row['id']);self.rows.append(row)
        self.loaded_hash=self.fingerprint()

    def validate_row(self,row):
        if not isinstance(row,dict) or set(row)!={'id','name','context','tags','enabled','file','sha256','media_type'}:raise ValueError('Invalid catalog row')
        if not isinstance(row['sha256'],str) or not re.fullmatch('[a-f0-9]{64}',row['sha256']) or row['id']!='m_'+row['sha256']:raise ValueError('Invalid meme hash')
        if type(row['enabled']) is not bool or not isinstance(row['tags'],list) or len(row['tags'])>8:raise ValueError('Invalid meme tags')
        if row['enabled'] and (not isinstance(row['name'],str) or not row['name'].strip() or not row['tags']):raise ValueError('Confirm name and tags before enabling')
        for text in [row['name'],row['context']]+row['tags']:
            if not isinstance(text,str) or len(text)>80 or re.search(r'[\x00-\x1f]|https?://|file:|base64',text,re.I):raise ValueError('Invalid meme label')
        if not isinstance(row['media_type'],str) or row['media_type'] not in {x[0] for x in FORMATS.values()} or row['file']!=row['sha256']+next(x[1] for x in FORMATS.values() if x[0]==row['media_type']):raise ValueError('Invalid library reference')

    def add(self,data,suffix=None):
        info=inspect_image(data,self.cfg['max_file_bytes'],suffix)
        mid='m_'+info['sha256']
        existing=next((x for x in self.rows if x['id']==mid),None)
        if not existing and len(self.rows)>=1000:raise ValueError('Catalog item limit')
        file=info['sha256']+info['extension'];path=controlled_path(self.root,self.cfg['library_dir']+'/'+file)
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            if path.read_bytes()!=data:raise ValueError('Library collision')
        else:
            with path.open('xb') as f:f.write(data)
        if existing:return existing
        row=dict(id=mid,name='',context='',tags=[],enabled=False,file=file,sha256=info['sha256'],media_type=info['media_type'])
        self.rows.append(row);return row

    def save(self):
        from .config import configuration_lock,require_stopped
        with configuration_lock(self.root):
            require_stopped(self.root)
            self._save_locked()

    def _save_locked(self):
        if self.config_guard:self.config_guard()
        current=MemeCatalog(self.root,self.cfg)
        if self.loaded_hash!=current.fingerprint():raise ValueError('Catalog changed; reload')
        for row in self.rows:self.validate_row(row)
        if len(self.rows)>1000 or len({r['id'] for r in self.rows})!=len(self.rows):raise ValueError('Catalog item limit/duplicates')
        atomic_yaml(controlled_path(self.root,self.cfg['catalog_file']),dict(version=1,items=self.rows))
        self.loaded_hash=self.fingerprint()

    def fingerprint(self):return hashlib.sha256(json.dumps(self.rows,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

    def stage(self):
        from .config import configuration_lock
        with configuration_lock(self.root):
            if self.config_guard:self.config_guard()
            if MemeCatalog(self.root,self.cfg).fingerprint()!=self.loaded_hash:raise ValueError('Active catalog changed')
            path=controlled_path(self.root,'state/memes-pending.local.yaml')
            if path.exists():
                if path.stat().st_size>1048576:raise ValueError('Staged catalog too large')
                old=read_catalog_yaml(path)
                if not isinstance(old,dict) or old.get('base')!=self.loaded_hash or not isinstance(old.get('items'),list):raise ValueError('Pending catalog changed')
                for row in old['items']:self.validate_row(row)
                ids={r['id'] for r in self.rows}
                self.rows.extend(r for r in old['items'] if r['id'] not in ids)
            if len(self.rows)>1000:raise ValueError('Catalog item limit')
            atomic_yaml(path,dict(version=1,base=self.loaded_hash,items=self.rows))

    def activate_pending(self):
        from .config import configuration_lock,require_stopped
        with configuration_lock(self.root):
            require_stopped(self.root)
            if self.config_guard:self.config_guard()
            path=controlled_path(self.root,'state/memes-pending.local.yaml')
            if path.stat().st_size>1048576:raise ValueError('Staged catalog too large')
            obj=read_catalog_yaml(path)
            if not isinstance(obj,dict) or obj.get('version')!=1 or obj.get('base')!=self.fingerprint() or not isinstance(obj.get('items'),list):raise ValueError('Staged catalog changed; rescan')
            self.rows=obj['items'];self._save_locked();path.unlink()

    def resolve(self,mid):
        row=next((x for x in self.rows if x['id']==mid and x['enabled'] and x['name'].strip() and x['tags']),None)
        if row is None:raise ValueError('Unavailable meme')
        return self.preview(mid)

    def preview(self,mid):
        """Read-only local inspection also permits unconfirmed, disabled images."""
        row=next((x for x in self.rows if x['id']==mid),None)
        if row is None:raise ValueError('Unavailable meme')
        self.validate_row(row)
        p=controlled_path(self.root,self.cfg['library_dir']+'/'+row['file'])
        if not p.is_file() or p.stat().st_size>self.cfg['max_file_bytes']:raise ValueError('Missing image')
        data=p.read_bytes();info=inspect_image(data,self.cfg['max_file_bytes'],p.suffix)
        if info['sha256']!=row['sha256'] or info['media_type']!=row['media_type']:raise ValueError('Image changed')
        return p,row

    def preview_page(self):
        """Numbered local-only gallery; no remote resources or JavaScript."""
        from html import escape
        cards=[]
        for index,row in enumerate(self.rows,1):
            try:
                path,_=self.preview(row['id'])
                uri=escape(path.as_uri(),quote=True)
                image=f'<a href="{uri}"><img loading="lazy" src="{uri}" alt="图片 {index}"></a>'
            except (ValueError,OSError):image='<p>文件缺失或校验失败，不能预览</p>'
            name=escape(row['name'] or '未命名')
            state='已登记启用' if row['enabled'] else '未启用'
            cards.append(f'<article><h2>{index} · {name}</h2>{image}<p>{state}</p></article>')
        page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src file:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>表情包编号预览</title><style>body{font:16px system-ui;margin:24px;background:#f4f5f7;color:#20242a}main{display:flex;flex-wrap:wrap;gap:16px}article{background:white;padding:16px;border-radius:12px;width:240px}h2{font-size:18px;overflow-wrap:anywhere}img{width:240px;height:200px;object-fit:contain}p{color:#505864}</style>
<h1>表情包编号预览</h1><p>先看图，再回配置窗口选择相同编号填写标签。点击图片可查看原图；本页只读取本机文件，不会启用或发送表情。编辑后重新按 P 刷新预览页。</p><main>'''+''.join(cards)+'</main></html>'
        target=controlled_path(self.root,'state/meme-preview/index.html')
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(page,encoding='utf-8')
        return target

    def candidates(self,question):
        rows=[]
        for row in self.rows:
            try:self.resolve(row['id'])
            except (ValueError,OSError):continue
            rows.append(row)
        rows.sort(key=lambda r:(-sum(t.lower() in question.lower() for t in r['tags']),r['id']))
        result=[]
        for r in rows:
            item={k:r[k] for k in ('id','name','context','tags')}
            if len(json.dumps(result+[item],ensure_ascii=False,separators=(',',':')).encode())>self.cfg['catalog_prompt_max_bytes']:continue
            result.append(item)
            if len(result)>=self.cfg['max_candidates']:break
        return result

    def scan(self):
        self.loaded_hash=self.fingerprint()
        folder=controlled_path(self.root,self.cfg['inbox_dir']);folder.mkdir(parents=True,exist_ok=True)
        accepted=failed=0
        for p in sorted(folder.iterdir())[:self.cfg['import_count']]:
            if p.name=='README.md':continue
            try:
                p=controlled_path(self.root,p.relative_to(self.root))
                if not p.is_file() or p.stat().st_size>self.cfg['max_file_bytes']:raise ValueError()
                self.add(p.read_bytes(),p.suffix);accepted+=1
            except (ValueError,OSError):failed+=1
        self.save();return accepted,failed
