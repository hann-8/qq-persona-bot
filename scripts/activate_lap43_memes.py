"""Current-root seven-image transaction. Inspect is read-only; activation is explicit."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from qqbot_gateway.meme_catalog import MemeCatalog,controlled_path,read_catalog_yaml

def fingerprint(root):
    files=['config/memes.local.yaml','state/memes-pending.local.yaml']
    files+=['config/local/'+n for n in ('bot.yaml','models.yaml','chat.yaml','features.yaml','runtime.yaml')]
    return {n:hashlib.sha256(controlled_path(root,n).read_bytes()).hexdigest() if controlled_path(root,n).exists() else None for n in files}

def inspect(root,cfg=None):
    root=Path(root)
    if root.is_symlink() or root.is_junction():raise ValueError('LINKED_ROOT')
    root=root.resolve();catalog=MemeCatalog(root,cfg)
    pending=controlled_path(root,'state/memes-pending.local.yaml')
    if not pending.exists():
        if len(catalog.rows)!=7:raise ValueError('SEVEN_IMAGES_REQUIRED')
        rows=catalog.rows;state='active'
    else:
        obj=read_catalog_yaml(pending)
        if set(obj)!={'version','base','items'} or obj['version']!=1 or obj['base']!=catalog.fingerprint():raise ValueError('PENDING_BASE_CHANGED')
        if catalog.rows:raise ValueError('UNEXPECTED_ACTIVE')
        rows=obj['items'];state='pending'
    if not isinstance(rows,list) or len(rows)!=7 or len({r['id'] for r in rows})!=7:raise ValueError('SEVEN_IMAGES_REQUIRED')
    catalog.rows=rows
    assets=[]
    for row in rows:
        p,_=catalog.preview(row['id'])
        from PIL import Image
        with Image.open(p) as image:details=dict(width=image.width,height=image.height,frames=getattr(image,'n_frames',1),format=image.format)
        assets.append(dict(file=row['file'],sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,**details))
    candidates=catalog.candidates('')
    size=len(json.dumps(candidates,ensure_ascii=False,separators=(',',':')).encode())
    if len(candidates)!=7 or size>2000:raise ValueError('CANDIDATE_BUDGET')
    return dict(state=state,files=fingerprint(root),assets=assets,candidate_bytes=size,rows_sha256=hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode()).hexdigest())

def activate(root,expected,cfg=None):
    root=Path(root);before=inspect(root,cfg);root=root.resolve()
    if before['state']=='active' and expected.get('state')=='pending':
        stable=all(before['files'][n]==h for n,h in expected['files'].items() if n not in ('config/memes.local.yaml','state/memes-pending.local.yaml'))
        if stable and all(before.get(k)==expected.get(k) for k in ('assets','candidate_bytes','rows_sha256')):return before
    if before!=expected:raise ValueError('BASELINE_CHANGED')
    if before['state']=='active':return before
    backed_up=False
    def guard():
        nonlocal backed_up
        if inspect(root,cfg)!=expected:raise ValueError('BASELINE_CHANGED')
        # This is called under activate_pending's own non-reentrant lock.
        if backed_up:return
        batch=controlled_path(root,'state/lap43-memes/'+hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest())
        batch.mkdir(parents=True,exist_ok=False)
        for n,h in expected['files'].items():
            if h is not None:(batch/n.replace('/','_')).write_bytes(controlled_path(root,n).read_bytes())
        (batch/'manifest.json').write_text(json.dumps(expected,sort_keys=True),encoding='utf-8')
        backed_up=True
    catalog=MemeCatalog(root,cfg,config_guard=guard)
    catalog.activate_pending()
    after=inspect(root,cfg)
    if after['state']!='active' or after['assets']!=before['assets']:raise ValueError('POSTCHECK_FAILED')
    return after

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--activate',action='store_true')
    p.add_argument('--expected',type=Path,help='Exact inspect JSON approved for this transaction')
    a=p.parse_args()
    if a.activate and not a.expected:p.error('--activate requires --expected')
    result=activate(a.root,json.loads(a.expected.read_text(encoding='utf-8'))) if a.activate else inspect(a.root)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
