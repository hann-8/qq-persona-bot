"""Stopped, digest-bound LAP-42 vision prepare/activate/rollback transaction.

No models, network, bot start or messages. Only paired active and vision.enabled.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]


def sha(data):return hashlib.sha256(data).hexdigest()


def atomic(path,data):
    path=Path(path)
    from qqbot_gateway.config_files import safe_mkdir
    safe_mkdir(ROOT if path.is_relative_to(ROOT) else path.parent,path.parent)
    if path.is_symlink():raise ValueError('TRANSACTION_LINK_REFUSED')
    fd,temp=tempfile.mkstemp(prefix=path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)


def current(root):
    from qqbot_gateway.config_files import read_project
    from qqbot_gateway.vision import binding
    from qqbot_gateway.vision_capabilities import runtime_identity
    project=read_project(root);runtime=runtime_identity(root,project.settings)
    return project,runtime,binding(project.settings,runtime)


def prepare(root,batch_id,ingress,expected_binding):
    from qqbot_gateway.vision_quality import BatchLedger
    from qqbot_gateway.vision_capabilities import digest,selected_record,validate_production_evidence,offline_valid,read_json
    from qqbot_gateway.vision_ingress import validate_record
    import re
    project,runtime,bound=current(root)
    if bound!=expected_binding or project.settings['vision']['enabled']:raise ValueError('PREPARE_STATE_CHANGED')
    ledger_path=root/'state/vision-evidence/iq-batches.sqlite3'
    if not ledger_path.is_file():raise ValueError('DURABLE_IQ_LEDGER_MISSING')
    ledger=BatchLedger(ledger_path)
    batch=ledger.snapshot(batch_id)
    if not isinstance(ingress,str) or not re.fullmatch('[a-f0-9]{32}',ingress):raise ValueError('INVALID_INGRESS_INSTANCE')
    intake=read_json(root/'state/vision-evidence'/(ingress+'.json'))
    row=validate_record(intake['record'])
    decoded=(intake.get('state')=='observed' and row['stage']=='decoded' and row['failure_enum']=='none' and
        row['bytes']>0 and row['normalized_bytes']>0 and row['attempt_counts']['download']==1)
    evidence=dict(binding=bound,runtime=runtime,record_hash=digest(selected_record(project.settings)),
        fixture_hash=batch['fixture_hash'],batch=batch,offline_passed=offline_valid(project.settings),ingress_decoded=decoded,
        ingress_instance=ingress,unresolved_attempts=ledger.unresolved(bound))
    _,missing=validate_production_evidence(project.settings,evidence,root)
    if missing:raise ValueError('CANDIDATE_REJECTED: '+','.join(missing))
    active=root/'state/vision-evidence/active.json'
    candidate=dict(schema_version=2,evidence=evidence,source_digest=project.source_digest,
        semantic_digest=project.semantic_digest,binding=bound,
        active_before_sha256=sha(active.read_bytes()) if active.exists() else None)
    raw=json.dumps(candidate,sort_keys=True,separators=(',',':')).encode()
    atomic(root/'state/lap42-vision-closure/candidate.json',raw)
    return dict(state='prepared',candidate_sha256=sha(raw),binding=bound)


def activate(root,expected_candidate,expected_binding):
    from qqbot_gateway.vision_capabilities import read_json,validate_production_evidence,load_production
    from scripts.lap42_rollout import patch_fields
    from qqbot_gateway.config_files import read_project
    path=root/'state/lap42-vision-closure/candidate.json'
    if sha(path.read_bytes())!=expected_candidate:raise ValueError('CANDIDATE_DIGEST_CHANGED')
    candidate=read_json(path);project,runtime,bound=current(root)
    if (bound!=expected_binding or candidate['binding']!=bound or
        project.source_digest!=candidate['source_digest'] or project.semantic_digest!=candidate['semantic_digest']):
        raise ValueError('SOURCE_OR_BINDING_CHANGED')
    _,missing=validate_production_evidence(project.settings,candidate['evidence'],root)
    if missing:raise ValueError('CANDIDATE_REJECTED: '+','.join(missing))
    feature=root/'config/local/features.yaml';active=root/'state/vision-evidence/active.json'
    original=feature.read_bytes();old=active.read_bytes() if active.exists() else None
    if (sha(old) if old is not None else None)!=candidate['active_before_sha256']:raise ValueError('ACTIVE_CHANGED')
    updated=patch_fields(original,{('vision','enabled'):True})
    evidence=json.dumps(candidate['evidence'],sort_keys=True,separators=(',',':')).encode()
    import uuid
    from qqbot_gateway.config_files import safe_mkdir
    backup_id=uuid.uuid4().hex
    backup=root/'state/lap42-vision-closure/activation'/backup_id
    safe_mkdir(root,backup)
    atomic(backup/'features.before',original)
    if old is not None:atomic(backup/'active.before',old)
    transaction=dict(binding=bound,backup_id=backup_id,features_before=sha(original),features_after=sha(updated),
        active_before=sha(old) if old is not None else None,active_after=sha(evidence))
    atomic(backup/'transaction.json',json.dumps(transaction).encode())
    atomic(backup.parent/'transaction.json',json.dumps(transaction).encode())
    try:
        atomic(active,evidence)  # interrupted here still leaves vision=false
        if feature.read_bytes()!=original:raise ValueError('FEATURES_CHANGED')
        atomic(feature,updated)
        saved=read_project(root).settings
        _,missing=load_production(saved,root)
        if missing or not saved['vision']['enabled']:raise ValueError('SAVED_ACTIVATION_REJECTED')
    except BaseException:
        restore(root,transaction)
        raise
    return dict(state='activated',vision_enabled=True,binding=bound)


def restore(root,transaction):
    """Only restore bytes still owned by this transaction; never overwrite drift."""
    backup=root/'state/lap42-vision-closure/activation'
    backup_id=transaction.get('backup_id')
    if backup_id is not None:
        import re
        if not isinstance(backup_id,str) or not re.fullmatch('[a-f0-9]{32}',backup_id):raise ValueError('BACKUP_PATH_INVALID')
        backup=backup/backup_id
    feature=root/'config/local/features.yaml';active=root/'state/vision-evidence/active.json'
    original=(backup/'features.before').read_bytes()
    if sha(original)!=transaction['features_before']:raise ValueError('BACKUP_CHANGED')
    # Check both destinations before touching either.
    fhash=sha(feature.read_bytes());ahash=sha(active.read_bytes()) if active.exists() else None
    if fhash not in (transaction['features_before'],transaction['features_after']) or ahash not in (transaction['active_before'],transaction['active_after']):
        raise ValueError('ROLLBACK_OWNERSHIP_CONFLICT')
    old=(backup/'active.before').read_bytes() if transaction['active_before'] is not None else None
    if old is not None and sha(old)!=transaction['active_before']:raise ValueError('BACKUP_CHANGED')
    atomic(feature,original)  # disable before removing paired active
    if old is None:
        if active.exists():active.unlink()
    else:atomic(active,old)
    return dict(state='rolled_back')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','activate','rollback'))
    parser.add_argument('--expected-binding',required=True)
    parser.add_argument('--candidate-sha256')
    parser.add_argument('--batch-id')
    parser.add_argument('--ingress-instance')
    args=parser.parse_args()
    from qqbot_gateway.config import configuration_lock,require_stopped
    from qqbot_gateway.vision_capabilities import read_json
    with configuration_lock(ROOT):
        require_stopped(ROOT)
        if current(ROOT)[2]!=args.expected_binding:raise ValueError('CURRENT_BINDING_CHANGED')
        if args.action=='prepare':
            if not args.batch_id or not args.ingress_instance:parser.error('batch and ingress required')
            result=prepare(ROOT,args.batch_id,args.ingress_instance,args.expected_binding)
        elif args.action=='activate':
            if not args.candidate_sha256:parser.error('candidate digest required')
            result=activate(ROOT,args.candidate_sha256,args.expected_binding)
        else:
            transaction=read_json(ROOT/'state/lap42-vision-closure/activation/transaction.json')
            if transaction['binding']!=args.expected_binding:raise ValueError('ROLLBACK_BINDING_CHANGED')
            result=restore(ROOT,transaction)
    print(json.dumps(result));return 0


if __name__=='__main__':raise SystemExit(main())
