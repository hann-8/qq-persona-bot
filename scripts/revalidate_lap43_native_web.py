"""Current checks, real zero-generation CLI probe, and explicit operator trial activation."""
import argparse
import asyncio
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT)]


def check(root):
    import os
    os.environ['QQBOT_TEST_ASTRBOT_SITE']=str(root/'runtime/astrbot-tool/astrbot/Lib/site-packages')
    modules=('test_lap43','test_cli_native_web','test_lap44_memory')
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromNames(modules))
    from qqbot_gateway.vision import adapter_signature
    from qqbot_gateway.vision_capabilities import digest,selected_record
    from qqbot_gateway.config_files import read_project
    from qqbot_gateway.vision_trial import sha,OFFLINE
    from scripts.activate_lap42_vision import atomic
    settings=read_project(root).settings
    from scripts.lap42_rollout import budget_check
    from qqbot_gateway.vision_capabilities import static_diagnostics,runtime_identity,final_budget
    from qqbot_gateway.token_budget import InputBudget
    from qqbot_gateway.vision import member_source
    from qqbot_gateway.persona import compose_persona
    budget=budget_check(root,settings)
    static=static_diagnostics(settings,runtime_identity(root,settings))
    system=compose_persona((root/'config/persona.md').read_text(encoding='utf-8'),settings['output'],settings['web'],settings['participation'],settings['memes'],settings['vision'],settings['members'],settings['memory'])
    native=final_budget(selected_record(settings),InputBudget.from_settings(settings),system,
        json.dumps(member_source('合成当前图片问题',settings['participation']['attention']['aliases']),ensure_ascii=False)+
        'x'*6000+json.dumps(__import__('qqbot_gateway.meme_catalog',fromlist=['MemeCatalog']).MemeCatalog(root,settings['memes']).candidates(''),ensure_ascii=False),1000,1000)
    from qqbot_gateway.vision import binding
    from qqbot_gateway.cli_web_policy import PROOF_FILES
    files=PROOF_FILES
    value=dict(schema_version=1,passed=result.wasSuccessful() and not static and budget['passed'],adapter_signature=adapter_signature(),
        binding=binding(settings,runtime_identity(root,settings)),
        rule_hash=digest(selected_record(settings)),files={p:sha(root/p) for p in files},
        tests_run=result.testsRun,budget=budget,native=native,tool_policy={k:v for k,v in settings['web'].items() if k.startswith('cli_') or k in ('engine','enabled','search_enabled')},thinking_enabled=False,static_missing=static,real_model_calls=0,real_qq_outputs=0,quality_state='pending_user_test')
    atomic(root/OFFLINE,json.dumps(value,sort_keys=True,indent=2).encode())
    return dict(passed=value['passed'],tests_run=result.testsRun)


def activate(root,expected_binding,expected_active):
    from scripts.activate_lap42_vision import current,atomic
    from qqbot_gateway.vision_capabilities import digest,selected_record,read_json,validate_production_evidence,load_production
    from qqbot_gateway.vision_trial import MODE,OFFLINE,JOURNALS,sha
    from qqbot_gateway.config_files import safe_mkdir
    project,runtime,bound=current(root);active=root/'state/vision-evidence/active.json'
    if bound!=expected_binding or sha(active)!=expected_active or not project.settings['vision']['enabled']:raise ValueError('PAIRING_BASELINE_CHANGED')
    old=read_json(active)
    folder=root/JOURNALS/bound;safe_mkdir(root,folder)
    authorization=dict(binding=bound,runtime=runtime,record_hash=digest(selected_record(project.settings)),
        authorized_at=datetime.now(timezone.utc).isoformat(),authorization_source='operator_submitted_prompt',
        quality_state='pending_user_test',previous_active_sha256=expected_active,technical_report_sha256=sha(root/OFFLINE))
    if (folder/'authorization.json').exists():
        existing=read_json(folder/'authorization.json')
        if any(existing.get(k)!=v for k,v in authorization.items() if k!='authorized_at') or sha(folder/'active.before')!=expected_active:
            raise ValueError('TRIAL_PREPARATION_CHANGED')
        authorization=existing
    evidence=dict(binding=bound,runtime=runtime,record_hash=authorization['record_hash'],offline_passed=True,
        ingress_decoded=old.get('ingress_decoded'),ingress_instance=old.get('ingress_instance'),
        unresolved_attempts=False,acceptance_mode=MODE,operator_trial=authorization)
    atomic(folder/'active.before',active.read_bytes())
    atomic(folder/'authorization.json',json.dumps(authorization,sort_keys=True).encode())
    atomic(folder/'candidate.json',json.dumps(evidence,sort_keys=True).encode())
    _,missing=validate_production_evidence(project.settings,evidence,root)
    if missing:raise ValueError('TRIAL_REJECTED: '+','.join(missing))
    if current(root)[2]!=bound or sha(active)!=expected_active:raise ValueError('PAIRING_BASELINE_CHANGED')
    try:
        atomic(active,(folder/'candidate.json').read_bytes())
        _,missing=load_production(project.settings,root)
        if missing:raise ValueError('SAVED_TRIAL_REJECTED')
    except BaseException:
        atomic(active,(folder/'active.before').read_bytes());raise
    return dict(state='activated',acceptance_mode=MODE,quality_state='pending_user_test',binding=bound)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('check','probe','activate'))
    parser.add_argument('--authorize-operator-trial',action='store_true')
    parser.add_argument('--expected-binding');parser.add_argument('--expected-active')
    args=parser.parse_args()
    from qqbot_gateway.config import configuration_lock,require_stopped
    from scripts.activate_lap42_vision import current,atomic
    if args.action=='check':result=check(ROOT)
    elif args.action=='probe':
        from scripts.probe_lap42_vision_contract import probe
        from qqbot_gateway.vision_mod_guard import probe_unknown_unresolved
        from qqbot_gateway.vision_trial import PROBE,JOURNALS
        with configuration_lock(ROOT):
            require_stopped(ROOT);project,_,before=current(ROOT)
            if before!=args.expected_binding or probe_unknown_unresolved(ROOT):raise ValueError('PROBE_BASELINE_OR_UNKNOWN')
            if (ROOT/'state/lap43-native-web-trial/probe-unknown.json').exists():raise ValueError('PROBE_UNKNOWN')
        value=asyncio.run(probe(ROOT,project.settings,ROOT/JOURNALS/('probe-'+uuid.uuid4().hex+'.json'),trial=True))
        with configuration_lock(ROOT):
            require_stopped(ROOT)
            if current(ROOT)[2]!=before:raise ValueError('PROBE_BINDING_CHANGED')
            atomic(ROOT/PROBE,json.dumps(value).encode())
        result=dict(passed=True,real_generations=value['real_generations'],positive_next_calls=value['positive_next_calls'],negative_users=value['negative_users'])
    else:
        if not args.authorize_operator_trial or not args.expected_binding or not args.expected_active:parser.error('explicit authorization and expected digests required')
        with configuration_lock(ROOT):
            require_stopped(ROOT);result=activate(ROOT,args.expected_binding,args.expected_active)
    print(json.dumps(result));return 0 if result.get('passed',True) else 1


if __name__=='__main__':raise SystemExit(main())
