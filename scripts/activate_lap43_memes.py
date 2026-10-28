"""Inspect by default; activate the seven existing rows under MemeCatalog's lock."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def inspect(root):
    from qqbot_gateway.config_files import read_project
    from qqbot_gateway.meme_catalog import MemeCatalog,controlled_path,read_catalog_yaml
    project=read_project(root);catalog=MemeCatalog(root,project.settings['memes'])
    active=controlled_path(root,project.settings['memes']['catalog_file']);pending=controlled_path(root,'state/memes-pending.local.yaml')
    if pending.exists():
        obj=read_catalog_yaml(pending)
        if obj.get('version')!=1 or obj.get('base')!=catalog.fingerprint():raise ValueError('PENDING_BASE_CHANGED')
        catalog.rows=obj['items']
    if len(catalog.rows)!=7:raise ValueError('EXPECTED_SEVEN_EXISTING_MEMES')
    for row in catalog.rows:catalog.resolve(row['id'])
    candidates=catalog.candidates('')
    if len(candidates)!=7:raise ValueError('CANDIDATE_BUDGET_OR_DISABLED_ROWS')
    return dict(source_digest=project.source_digest,active_sha256=sha(active),pending_sha256=sha(pending),
        items=7,candidate_bytes=len(json.dumps(candidates,ensure_ascii=False,separators=(',',':')).encode()),
        assets={r['file']:r['sha256'] for r in catalog.rows})


def activate(root,expected):
    from qqbot_gateway.config_files import read_project,safe_mkdir
    from qqbot_gateway.meme_catalog import MemeCatalog,controlled_path
    from scripts.activate_lap42_vision import atomic
    before=inspect(root)
    if before!=expected:raise ValueError('ACTIVATION_BASELINE_CHANGED')
    if before['pending_sha256'] is None:return dict(state='already_active',items=7)
    project=read_project(root);cfg=project.settings['memes'];catalog=MemeCatalog(root,cfg)
    active=controlled_path(root,cfg['catalog_file']);pending=controlled_path(root,'state/memes-pending.local.yaml')
    folder=root/'state/lap43-memes'/before['pending_sha256'];safe_mkdir(root,folder)
    # This guard runs again inside the existing non-reentrant configuration lock.
    def guard():
        if read_project(root).source_digest!=before['source_digest'] or sha(active)!=before['active_sha256'] or sha(pending)!=before['pending_sha256']:
            raise ValueError('ACTIVATION_BASELINE_CHANGED')
        if not (folder/'manifest.json').exists():
            atomic(folder/'pending.before',pending.read_bytes())
            if active.exists():atomic(folder/'active.before',active.read_bytes())
            atomic(folder/'manifest.json',json.dumps(before,sort_keys=True).encode())
    # _save_locked calls guard again before it deletes pending, which is intended.
    catalog.config_guard=guard
    catalog.activate_pending()
    after=inspect(root)
    if after['assets']!=before['assets'] or after['pending_sha256'] is not None:raise ValueError('ACTIVATION_POSTCHECK_FAILED')
    return dict(state='activated',items=7,candidate_bytes=after['candidate_bytes'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--activate',action='store_true')
    p.add_argument('--expected-source');p.add_argument('--expected-active');p.add_argument('--expected-pending')
    args=p.parse_args();before=inspect(ROOT)
    if args.activate:
        expected=(args.expected_source,args.expected_active,args.expected_pending)
        actual=(before['source_digest'],before['active_sha256'] or 'absent',before['pending_sha256'] or 'absent')
        if expected!=actual:raise ValueError('EXPECTED_DIGESTS_REQUIRED_OR_CHANGED')
        result=activate(ROOT,before)
    else:result=before
    print(json.dumps(result,sort_keys=True));return 0


if __name__=='__main__':raise SystemExit(main())
