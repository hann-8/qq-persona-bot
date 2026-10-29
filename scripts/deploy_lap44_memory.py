"""LAP-44 stopped configuration/memory migration with private recoverable backups."""
import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sys
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from qqbot_gateway.config_files import read_project
from qqbot_gateway.config import configuration_lock,require_stopped
from scripts.activate_lap42_vision import atomic

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def protected(root):
    paths=[*root.glob('config/local/*.yaml'),root/'config/persona.md',root/'config/memes.local.yaml',root/'state/memes-pending.local.yaml',root/'secrets/group-memory-key.local.json',*root.glob('assets/memes/library/**/*'),*root.glob('state/group-memory/**/memory.json')]
    return {p.relative_to(root).as_posix():sha(p) for p in paths if p.is_file()}
def prepare(root,folder):
    project=read_project(root)
    if folder.exists():raise ValueError('BACKUP_ALREADY_EXISTS')
    files=protected(root)
    files.update({p:sha(root/p) for p in ('state/vision-evidence/active.json','reports/lap-43-native-web-offline.json','state/lap43-native-web-trial/cli-probe.json','config/vision-capabilities.json') if (root/p).exists()})
    folder.mkdir(parents=True)
    for name in files:
        dest=folder/'before'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,dest)
    memory=[]
    for p in root.glob('state/group-memory/**/memory.json'):
        obj=json.loads(p.read_text(encoding='utf-8'));memory.append(dict(schema=obj.get('schema_version'),records=len(obj.get('records',[]))))
    value=dict(source_digest=project.source_digest,semantic_digest=project.semantic_digest,files=files,memory_before=memory)
    atomic(folder/'baseline.json',json.dumps(value,indent=2).encode());return dict(backup=folder.relative_to(root).as_posix(),memory_before=memory,protected=len(files))

def patch_scalars(raw,changes):
    text=raw.decode('utf-8-sig');tree=yaml.compose(text);replacements=[]
    for path,value in changes.items():
        node=tree
        for name in path[:-1]:
            matches=[v for k,v in node.value if k.value==name]
            if len(matches)!=1:raise ValueError('PATCH_PATH')
            node=matches[0]
        matches=[v for k,v in node.value if k.value==path[-1]]
        if not matches:
            line_start=text.rfind('\n',0,node.end_mark.index)+1
            if text[line_start:node.end_mark.index].strip():line_start=node.end_mark.index
            replacements.append((line_start,line_start,'  '*len(path[:-1])+path[-1]+': '+str(value)+'\n'))
        elif len(matches)==1 and isinstance(matches[0],yaml.ScalarNode) and matches[0].tag=='tag:yaml.org,2002:int':
            leaf=matches[0];replacements.append((leaf.start_mark.index,leaf.end_mark.index,str(value)))
        else:raise ValueError('PATCH_INTEGER')
    for start,end,value in sorted(replacements,reverse=True):text=text[:start]+value+text[end:]
    return (b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+text.encode('utf-8')

def apply(root,folder):
    with configuration_lock(root):
        require_stopped(root);base=json.loads((folder/'baseline.json').read_text())
        project=read_project(root)
        if project.source_digest!=base['source_digest']:raise ValueError('CONFIG_CHANGED')
        # Source/technical reports may have changed with the fast-forward; private data must match.
        if any(sha(root/p)!=h for p,h in base['files'].items() if p.startswith(('config/local/','secrets/','assets/','state/group-memory/')) or p in ('config/persona.md','config/memes.local.yaml','state/memes-pending.local.yaml')):raise ValueError('PROTECTED_DATA_CHANGED')
        patches={'features.yaml':{('memory','max_chars_per_group'):50000,('memory','max_group_file_bytes'):1048576},
                 'models.yaml':{('llm','profiles','codebuddy_cli','input_budget','context_input_limit_tokens'):524288}}
        candidates={name:patch_scalars((root/'config/local'/name).read_bytes(),fields) for name,fields in patches.items()}
        before=deepcopy(project.settings)
        try:
            for name,raw in candidates.items():atomic(root/'config/local'/name,raw)
            after=read_project(root).settings;expected=deepcopy(before)
            expected['memory'].update(max_chars_per_group=50000,max_group_file_bytes=1048576)
            expected['llm']['profiles']['codebuddy_cli']['input_budget']['context_input_limit_tokens']=524288
            if after!=expected:raise ValueError('UNEXPECTED_CONFIG_CHANGE')
            from qqbot_gateway.token_budget import validate_model_settings,InputBudget
            validate_model_settings(after)
            from qqbot_gateway.group_memory import MemoryStore
            store=MemoryStore(root,after['bot']['qq'],after['access']['allowed_groups'],after['access']['blocked_users'],after['access']['admin_users'],after['memory'])
            if store.key is None or store.disabled:raise ValueError('MEMORY_MIGRATION_FAILED_SOURCE_PRESERVED')
            # Verify every owned namespace after migration without creating empty files.
            count=characters=groups=0
            for group in store.groups|set(store._namespace_overrides):
                doc=store._load(group,create=False)
                if doc is not None:groups+=1;count+=len(doc['records']);characters+=sum(map(len,doc['records'].values()))
        except BaseException:
            # Keep migration originals/schema2 in place; only revert our two local files.
            for name in candidates:atomic(root/'config/local'/name,(folder/'before/config/local'/name).read_bytes())
            raise
        value=dict(state='configured_and_migrated',groups=groups,records=count,chars=characters,memory=after['memory'],input_policy=524288,
            protected_after=protected(root))
        atomic(folder/'migration.json',json.dumps(value,indent=2).encode())
        return {k:v for k,v in value.items() if k!='protected_after'}

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','apply']);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--backup',required=True)
    args=p.parse_args();root=args.root.resolve();folder=(root/args.backup).resolve()
    if not folder.is_relative_to(root/'state/lap44-deployment'):raise ValueError('BACKUP_PATH')
    result=prepare(root,folder) if args.action=='prepare' else apply(root,folder)
    print(json.dumps(result));return 0
if __name__=='__main__':raise SystemExit(main())
