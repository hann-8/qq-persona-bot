"""LAP-43 current binding regression. Default inspect; every action explicit."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from scripts.activate_lap42_vision import atomic,current,sha
from qqbot_gateway.vision_regression import MODE,directory as base,authorized,historical,unknown,diagnostics,PROBE_BASE
from qqbot_gateway.vision_capabilities import read_json,offline_valid,selected_record,digest,validate_production_evidence
from qqbot_gateway.config import configuration_lock,require_stopped

def exclusive(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,sort_keys=True)

def prerequisites(root,settings,bound):
    if settings['vision']['enabled'] or not authorized(root,bound) or not historical(root) or unknown(root):raise ValueError('REGRESSION_PREREQUISITES')
    if not offline_valid(settings,MODE):raise ValueError('CURRENT_OFFLINE_REQUIRED')

def prepare(root,ingress,bound):
    project,runtime,now=current(root)
    if now!=bound or project.settings['vision']['enabled']:raise ValueError('PREPARE_STATE_CHANGED')
    review=read_json(base(root,bound)/'review.json')
    evidence=dict(acceptance_mode=MODE,binding=bound,runtime=runtime,record_hash=digest(selected_record(project.settings)),
        offline_passed=offline_valid(project.settings,MODE),ingress_decoded=True,ingress_instance=ingress,
        operator_review=review,unresolved_attempts=False)
    _,missing=validate_production_evidence(project.settings,evidence,root)
    if missing:raise ValueError('CANDIDATE_REJECTED: '+','.join(missing))
    active=root/'state/vision-evidence/active.json'
    candidate=dict(schema_version=3,evidence=evidence,source_digest=project.source_digest,semantic_digest=project.semantic_digest,
        binding=bound,active_before_sha256=sha(active.read_bytes()) if active.exists() else None)
    raw=json.dumps(candidate,sort_keys=True,separators=(',',':')).encode()
    exclusive(base(root,bound)/'candidate.json',candidate)
    return dict(state='prepared',candidate_sha256=sha((base(root,bound)/'candidate.json').read_bytes()))

def activate(root,expected_candidate,expected_binding):
    from qqbot_gateway.vision_capabilities import read_json,validate_production_evidence,load_production
    from scripts.lap42_rollout import patch_fields
    from qqbot_gateway.config_files import read_project
    path=base(root,expected_binding)/'candidate.json'
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
    backup=base(root,bound)/'activation'/backup_id
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
    backup=base(root,transaction['binding'])/'activation'
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
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',nargs='?',default='inspect',choices=('inspect','authorize','probe','run','accept','reject','prepare','activate','rollback'))
    p.add_argument('--expected-binding');p.add_argument('--authorize',choices=('ONE_CURRENT_LARGE_CASE',))
    p.add_argument('--answer-sha256');p.add_argument('--ingress-instance');p.add_argument('--candidate-sha256')
    a=p.parse_args()
    if a.action=='inspect':
        try:
            project,runtime,bound=current(ROOT);d=base(ROOT,bound)
            attempt=read_json(d/'attempt.json').get('state') if (d/'attempt.json').exists() else 'not_attempted'
            print(json.dumps(dict(mode=MODE,binding=bound,offline_valid=offline_valid(project.settings,MODE),
                authorized=authorized(ROOT,bound),historical_accepted=historical(ROOT),unresolved=unknown(ROOT),
                attempt=attempt,vision_enabled=project.settings['vision']['enabled'],real_actions=0)))
        except (OSError,ValueError,KeyError):
            print(json.dumps(dict(mode=MODE,state='current_configuration_unavailable',real_actions=0)))
        return 0
    if not a.expected_binding:p.error('expected binding required')
    with configuration_lock(ROOT):
        require_stopped(ROOT);project,runtime,bound=current(ROOT)
        if bound!=a.expected_binding:raise ValueError('CURRENT_BINDING_CHANGED')
        d=base(ROOT,bound);path=d/'attempt.json'
        if a.action=='authorize':
            if a.authorize!='ONE_CURRENT_LARGE_CASE':p.error('explicit current one-case authorization required')
            if unknown(ROOT):raise ValueError('UNRESOLVED_ATTEMPTS')
            exclusive(d/'authorization.json',dict(mode=MODE,binding=bound,source='explicit_current_conversation',max_local_real_requests=1,
                case='IQ-05',historical_case='IQ-01',prior_failures_preserved=True));return 0
        if a.action in ('probe','run'):prerequisites(ROOT,project.settings,bound)
        if a.action=='probe':
            exclusive(d/'probe-attempt.json',dict(binding=bound,state='reserved'))
        elif a.action=='run':
            from qqbot_gateway.vision_mod_guard import probe_valid
            if not probe_valid(ROOT,project.settings,MODE):raise ValueError('CURRENT_PROBE_REQUIRED')
            spec=read_json(ROOT/'state/vision-evidence/iq-fixtures-lap42-v2/spec.json')
            sample=ROOT/'state/vision-evidence/iq-fixtures-lap42-v2/IQ-05.png'
            image_hash=sha(sample.read_bytes())
            if image_hash!=spec['cases']['IQ-05']['sha256']:raise ValueError('FIXTURE_CHANGED')
            attempt=dict(binding=bound,state='reserved',attempts=1,fixture_hash=image_hash)
            exclusive(path,attempt)
        elif a.action in ('accept','reject'):
            attempt=read_json(path);row=attempt['result']
            if (attempt['binding']!=bound or attempt['state']!='awaiting_human' or row['human_review']['answer_sha256']!=a.answer_sha256):raise ValueError('REVIEW_MISMATCH')
            accepted=a.action=='accept';row.update(human_passed=accepted,quality_passed=bool(accepted and row['exact_facts']),native_success=bool(accepted and row['exact_facts']))
            row['human_review']['timestamp']=time.time();attempt.update(state='scored' if row['quality_passed'] else 'failed_or_unknown')
            atomic(path,json.dumps(attempt).encode())
            if not row['quality_passed']:return 1
            from qqbot_gateway.vision_operator_review import FIRST_BINDING,FIRST_ANSWER
            review=dict(mode=MODE,binding=bound,historical_first=dict(binding=FIRST_BINDING,answer_sha256=FIRST_ANSWER,case='IQ-01',current_rerun=False),large=row)
            if diagnostics(review,bound):raise ValueError('REVIEW_INVALID')
            exclusive(d/'review.json',review);return 0
        elif a.action=='prepare':print(json.dumps(prepare(ROOT,a.ingress_instance,bound)));return 0
        elif a.action=='activate':print(json.dumps(activate(ROOT,a.candidate_sha256,bound)));return 0
        elif a.action=='rollback':
            transaction=read_json(d/'activation/transaction.json')
            if transaction['binding']!=bound:raise ValueError('ROLLBACK_BINDING_CHANGED')
            print(json.dumps(restore(ROOT,transaction)));return 0
    if a.action=='probe':
        from scripts.probe_lap42_vision_contract import probe
        token=PROBE_BASE.set(d/'probe-request-evidence')
        async def perform():return await probe(ROOT,project.settings,d/('probe-'+__import__('uuid').uuid4().hex+'.json'),MODE)
        try:
            value=asyncio.run(perform())
            with configuration_lock(ROOT):
                require_stopped(ROOT)
                if current(ROOT)[2]!=bound:raise ValueError('PROBE_BINDING_CHANGED')
                exclusive(d/'probe.json',value)
                atomic(d/'probe-attempt.json',json.dumps(dict(binding=bound,state='verified')).encode())
        except BaseException:
            atomic(d/'probe-unknown.json',b'{"state":"failed_or_unknown"}');raise
        finally:PROBE_BASE.reset(token)
        return 0
    def pending(text):
        print('answer_sha256='+hashlib.sha256(text.encode()).hexdigest(),flush=True);print(text,flush=True)
        return dict(no_hallucination=False,visible_facts_correct=False,injection_safe=False)
    pending.review_source='conversation_explicit_feedback'
    from scripts.observe_lap28 import observe
    try:
        row=asyncio.run(observe(ROOT,project.settings,sample,'IQ-05',spec['cases']['IQ-05']['truth'],bound,pending,image_hash));row['attempts']=1
        with configuration_lock(ROOT):
            require_stopped(ROOT)
            if current(ROOT)[2]!=bound:raise ValueError('ATTEMPT_BINDING_CHANGED')
            attempt.update(state='awaiting_human',result=row);atomic(path,json.dumps(attempt).encode())
        print('Awaiting explicit human feedback; no additional generation');return 0
    except BaseException as exc:
        attempt.update(state='failed_or_unknown',failure=type(exc).__name__);atomic(path,json.dumps(attempt).encode());raise
if __name__=='__main__':raise SystemExit(main())
