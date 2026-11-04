"""LAP-48 stopped schema3 migration, with current local data backed up privately."""
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from qqbot_gateway.config import configuration_lock,require_stopped
from qqbot_gateway.config_files import read_project
from qqbot_gateway.group_memory import MemoryStore,texts,chars,locked
from scripts.deploy_lap44_memory import protected,patch_scalars,sha
from scripts.activate_lap42_vision import atomic


def migrate(root=ROOT):
    folder=root/'state/lap48-deployment'
    with configuration_lock(root):
        require_stopped(root)
        if (folder/'migration.json').exists():return json.loads((folder/'migration.json').read_text(encoding='utf-8'))
        before=read_project(root).settings
        # Refresh only live business data at the actual stopped window. The
        # original persona and technical materials were backed up before edits.
        files=protected(root)
        for name in files:
            if name=='config/persona.md':continue
            dest=folder/'before'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,dest)
        atomic(folder/'stopped-files.json',json.dumps(files,indent=2).encode())
        model=root/'config/local/models.yaml'
        atomic(model,patch_scalars(model.read_bytes(),{('llm','profiles','codebuddy_cli','run_timeout_seconds'):180}))
        after=read_project(root).settings;expected=deepcopy(before)
        expected['llm']['profiles']['codebuddy_cli']['run_timeout_seconds']=180
        if after!=expected:raise ValueError('UNEXPECTED_CONFIG_CHANGE')
        # Candidate numbers are already present in project-local configuration
        # or logs. Only an exact keyed old actor match associates an identity.
        candidates=set(after['access']['admin_users'])|set(after['access']['blocked_users'])
        for p in (root/'logs').glob('*'):
            if p.is_file():candidates.update(re.findall(r'(?<!\d)\d{5,20}(?!\d)',p.read_text(encoding='utf-8',errors='ignore')))
        store=MemoryStore(root,after['bot']['qq'],after['access']['allowed_groups'],after['access']['blocked_users'],after['access']['admin_users'],after['memory'])
        stats=[]
        with locked(root):
            for group in sorted(store.groups|set(store._namespace_overrides)):
                if group in store.disabled:continue # preserve any pre-existing invalid/empty retired file
                doc=store.associate(group,candidates)
                if doc is None:continue
                original=folder/'before'/store.path(group).relative_to(root)
                old=json.loads(original.read_text(encoding='utf-8'))
                count=len(old['records']) if old['schema_version'] in (1,2) else len(texts(old))
                if len(texts(doc))!=count:raise ValueError('MIGRATION_CONTENT_COUNT_CHANGED')
                stats.append(dict(records=len(texts(doc)),members=len(doc['members']),unassigned=len(doc['unassigned']),chars=chars(doc)))
        result=dict(groups=stats,preserved_unavailable=len(store.disabled),run_timeout_seconds=180,
            provider_timeout=after['llm']['queue_wait_seconds']+180+25,protected_files=len(files))
        atomic(folder/'migration.json',json.dumps(result,indent=2).encode())
        return result

if __name__=='__main__':print(json.dumps(migrate()))
