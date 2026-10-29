"""Bounded LAP-42 field-only rollout. Never starts a process or sends a message.

prepare writes private candidates; apply requires a stopped project, the shared
OS lock, original source/semantic digests, and unchanged protected bytes.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
import yaml
from qqbot_gateway.config import configuration_lock,require_stopped
from qqbot_gateway.config_files import read_project,validate,parse,canonical,sha,plain_path

PATCHES={'features.yaml':{('memory','enabled'):True,('memory','learning_enabled'):True,
                         ('members','enabled'):True,('members','mentions_enabled'):True},
         'chat.yaml':{('participation','attention','enabled'):True}}


def patch_fields(content,changes):
    """Replace only scalar boolean spans. Preserve all other UTF-8/CRLF bytes."""
    text=content.decode('utf-8-sig');node=yaml.compose(text);replacements=[]
    for path,value in changes.items():
        current=node
        for name in path:
            if not isinstance(current,yaml.MappingNode):raise ValueError('PATCH_PATH_INVALID')
            matches=[v for k,v in current.value if k.value==name]
            if len(matches)!=1:raise ValueError('PATCH_PATH_MISSING_OR_DUPLICATE')
            current=matches[0]
        if not isinstance(current,yaml.ScalarNode) or current.tag!='tag:yaml.org,2002:bool':raise ValueError('PATCH_BOOLEAN_REQUIRED')
        replacements.append((current.start_mark.index,current.end_mark.index,'true' if value else 'false'))
    for start,end,value in sorted(replacements,reverse=True):text=text[:start]+value+text[end:]
    return (b'\xef\xbb\xbf' if content.startswith(b'\xef\xbb\xbf') else b'')+text.encode('utf-8')


def protection(root):
    paths=sorted(set([*root.glob('config/local/*.yaml'),root/'config/persona.md',
        root/'state/memes-pending.local.yaml',root/'config/memes.local.yaml',*root.glob('assets/memes/library/**/*')]))
    return {str(p.relative_to(root)):sha(p.read_bytes()) if p.is_file() else None for p in paths if not p.is_dir()}


def candidate_settings(root,project,candidates):
    raw={}
    for key in project.files:
        name=Path(key).name
        content=candidates.get(name,(root/'config/local'/name).read_bytes())
        raw.update(parse(content,name))
    if raw.pop('layout_version')!=1:raise ValueError('PATCH_LAYOUT_INVALID')
    raw.update(raw.pop('legacy_extensions',{}))
    return validate(root,raw)


def budget_check(root,settings):
    from qqbot_gateway.persona import compose_persona
    from qqbot_gateway.members import POLICY as MEMBERS_POLICY
    from qqbot_gateway.token_budget import InputBudget,validate_model_settings,dialog_text
    from qqbot_gateway.turn_v2 import fit,sha as turn_sha
    from qqbot_gateway.vision import member_source
    persona=(root/'config/persona.md').read_text(encoding='utf-8')
    system=compose_persona(persona,settings['output'],settings['web'],settings['participation'],settings['memes'],
        settings['vision'],settings['members'],settings['memory'],settings['bilibili'])
    system=system.replace('mention必须null；','')+MEMBERS_POLICY
    budget=InputBudget.from_settings(settings,validate_model_settings(settings))
    source=member_source('synthetic current target',settings['participation']['attention']['aliases'])
    header=dict(must_reply=True,target_seq=source['target_seq'],addressing='mention')
    # Exercise the same final subset fitter with full optional quotas and long
    # old context. Only sizes/counts escape; no persona/body is ever printed.
    for i in range(8):source['member_candidates'].append(dict(member_ref='p_'+f'{i:016x}',name='synthetic-'+str(i)))
    source['memory']=dict(generation='a'*32,base_revision=0,records={f'{i:032x}':'synthetic '+('x'*180) for i in range(8)},actors={})
    body=fit(source,header,system,budget)
    prompt=dialog_text([dict(role='user',content=body)])
    budget.check(system,prompt)
    effective=json.loads(body)
    return dict(persona_bytes=len(persona.encode()),persona_sha256=sha(persona.encode()),system_bytes=len(system.encode()),
        final_visible_policy_bytes=budget.usage(system,prompt),limit=budget.limit,overhead=budget.overhead,
        output_reserve=budget.output,memory_records=len((effective['memory'] or {}).get('records',[])),
        member_candidates=len(effective['member_candidates']),passed=True)


def prepare(root=ROOT):
    root=Path(root).resolve();directory=root/'state/lap42-rollout';directory.mkdir(parents=True,exist_ok=True)
    project=read_project(root)
    if project.layout!='split':raise ValueError('LAP42_SPLIT_REQUIRED')
    baseline=json.loads((directory/'protection-before.json').read_text(encoding='utf-8'))
    if protection(root)!=baseline:raise ValueError('PROTECTED_BYTES_CHANGED')
    candidates={name:patch_fields((root/'config/local'/name).read_bytes(),changes) for name,changes in PATCHES.items()}
    settings=candidate_settings(root,project,candidates)
    desired=deepcopy(project.settings)
    for name,changes in PATCHES.items():
        for path,value in changes.items():
            target=desired
            for key in path[:-1]:target=target[key]
            target[path[-1]]=value
    if settings!=desired:raise ValueError('UNOWNED_CONFIG_CHANGE')
    from qqbot_gateway.members import require_production
    require_production(settings)
    budget=budget_check(root,settings)
    metadata=dict(stage='prepared',source_digest=project.source_digest,semantic_digest=project.semantic_digest,
        desired_semantic_digest=sha(canonical(settings)),budget=budget,
        files={name:dict(before=sha((root/'config/local'/name).read_bytes()),after=sha(content)) for name,content in candidates.items()})
    for name,content in candidates.items():
        (directory/('candidate-'+name)).write_bytes(content)
    (directory/'prepared.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    return dict(stage='prepared',changed_files=list(candidates),budget=budget,vision_enabled=False)


def apply(root=ROOT):
    root=Path(root).resolve();directory=root/'state/lap42-rollout'
    metadata=json.loads((directory/'prepared.json').read_text(encoding='utf-8'))
    with configuration_lock(root):
        require_stopped(root);project=read_project(root)
        if (project.source_digest!=metadata['source_digest'] or project.semantic_digest!=metadata['semantic_digest']):
            raise ValueError('CONFIG_DOUBLE_DIGEST_CHANGED')
        baseline=json.loads((directory/'protection-before.json').read_text(encoding='utf-8'))
        if protection(root)!=baseline:raise ValueError('PROTECTED_BYTES_CHANGED')
        candidates={name:(directory/('candidate-'+name)).read_bytes() for name in PATCHES}
        for name,content in candidates.items():
            if sha(content)!=metadata['files'][name]['after'] or sha((root/'config/local'/name).read_bytes())!=metadata['files'][name]['before']:
                raise ValueError('CANDIDATE_DOUBLE_DIGEST_CHANGED')
        settings=candidate_settings(root,project,candidates)
        if sha(canonical(settings))!=metadata['desired_semantic_digest']:raise ValueError('CANDIDATE_SEMANTICS_CHANGED')
        # Credentials are created explicitly here under the stopped writer lock,
        # never by gate/model startup. Existing malformed/missing-key stores fail.
        from qqbot_gateway.vision import context_token
        token_path=root/'secrets/context-service.local.json'
        if not token_path.exists():
            if os.path.lexists(token_path):raise ValueError('TOKEN_PATH_INVALID')
            with token_path.open('x',encoding='utf-8') as stream:
                json.dump(dict(context_service_token=secrets.token_hex(32)),stream);stream.flush();os.fsync(stream.fileno())
        context_token(root)
        from qqbot_gateway.config import load_gate_config
        gate=load_gate_config(root=root,settings=settings)
        if not gate.members_enabled:raise ValueError('MEMBERS_EFFECTIVE_PAUSED')
        from qqbot_gateway.group_memory import MemoryStore
        memory=MemoryStore(root,gate.bot_qq,gate.allowed_groups,gate.blocked_users,gate.admin_users,settings['memory'])
        if memory.key is None or memory.disabled:raise ValueError('MEMORY_INITIALIZATION_UNAVAILABLE')
        written=[]
        try:
            for name,content in candidates.items():
                require_stopped(root)
                path=root/'config/local'/name
                if sha(path.read_bytes())!=metadata['files'][name]['before']:raise ValueError('CONFIG_CHANGED_DURING_APPLY')
                # Original bytes were already backed up at S0. A unique temp is
                # fsynced then replaced; never regenerate the complete YAML.
                with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as stream:
                    temp=Path(stream.name);stream.write(content);stream.flush();os.fsync(stream.fileno())
                os.replace(temp,path);written.append(name)
            actual=read_project(root)
            if actual.semantic_digest!=metadata['desired_semantic_digest']:raise ValueError('SAVED_SEMANTICS_MISMATCH')
        except BaseException:
            # Only still-owned candidate bytes may be restored. New key/store
            # and all purge/pending/unknown/locks always remain recoverable.
            for name in written:
                path=root/'config/local'/name
                if sha(path.read_bytes())==metadata['files'][name]['after']:
                    path.write_bytes((directory/('before-'+name)).read_bytes())
            raise
        after=protection(root)
        changed={key for key in baseline if baseline[key]!=after.get(key)}
        if changed!={str(Path('config/local')/name) for name in PATCHES}:raise ValueError('UNOWNED_PROTECTION_CHANGE')
        (directory/'protection-after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
        result=dict(stage='saved_not_loaded',source_digest=actual.source_digest,semantic_digest=actual.semantic_digest,
            changed_files=list(PATCHES),memory_key_ready=True,context_token_independent=True,
            memory_enabled=True,learning_enabled=True,attention_enabled=True,members_enabled=True,mentions_enabled=True,vision_enabled=False)
        (directory/'applied.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('prepare','apply'));args=parser.parse_args()
    print(json.dumps(prepare() if args.command=='prepare' else apply(),indent=2))
