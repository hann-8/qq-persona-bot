"""Independent stage C offline report; never writes older LAP-28/18 reports."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
os.environ['ASTRBOT_DISABLE_METRICS']='1'


async def frameworks():
    from scripts.verify_lap28_framework import verify as image
    from scripts.verify_lap35_framework import verify as silence
    rows=[];previous=Path.cwd();started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='lap28-C-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    for participation in ('mentions','free'):
                        root=Path(directory)/(backend+mode+participation);root.mkdir()
                        rows.append(await image(root,backend,mode,participation=participation,attention=True,
                            web_enabled=True,memes=True,memory_enabled=True,body_reader=True))
                    root=Path(directory)/(backend+mode+'silence');root.mkdir()
                    rows.append(await silence(root,backend,mode,'free',attention=True,memory=True,memes=True,members=True,web_enabled=True))
        finally:os.chdir(previous)
    value=dict(passed=True,combinations=len(rows),cases=sum(len(r['cases']) for r in rows),
        elapsed_seconds=round(time.monotonic()-started,3),rows=rows,real_model_calls=0,real_qq_outputs=0)
    from qqbot_gateway.vision import adapter_signature
    value['adapter_signature']=adapter_signature()
    (ROOT/'reports/lap-28-C-framework-offline.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('LAP28_C_FRAMEWORK',value['combinations'],value['cases'],value['elapsed_seconds'])


def units():
    modules=('test_lap28_capability','test_lap28','test_lap28_ingress','test_lap18_body','test_web',
        'test_token_budget','test_cli_runner','test_cli_control','test_lap27','test_lap29','test_lap30',
        'test_group_silence','test_config','test_config_files','test_config_comments','test_configure_menu')
    suite=unittest.defaultTestLoader.loadTestsFromNames(modules)
    started=time.monotonic();result=unittest.TextTestRunner(verbosity=1).run(suite)
    value=dict(passed=result.wasSuccessful(),tests=result.testsRun,modules=modules,elapsed_seconds=round(time.monotonic()-started,3),
        failures=len(result.failures),errors=len(result.errors),real_model_calls=0,real_qq_outputs=0)
    from qqbot_gateway.vision import adapter_signature
    value['adapter_signature']=adapter_signature()
    (ROOT/'reports/lap-28-C-unit.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
    return result.wasSuccessful()


def finalize():
    from qqbot_gateway.vision import adapter_signature
    unit=json.loads((ROOT/'reports/lap-28-C-unit.json').read_text(encoding='utf-8'))
    framework=json.loads((ROOT/'reports/lap-28-C-framework-offline.json').read_text(encoding='utf-8'))
    signature=adapter_signature()
    value=dict(passed=unit['passed'] and framework['passed'] and unit.get('adapter_signature')==signature and
        framework.get('adapter_signature')==signature,adapter_signature=signature,unit_tests=unit['tests'],
        framework_combinations=framework['combinations'],framework_cases=framework['cases'],
        real_model_calls=0,real_qq_outputs=0,real_bot_operations=0,production_eligible=False,
        ingress_state='ingress_unverified',capability_state='offline_passed',trusted_visual_upper_bound=False)
    (ROOT/'reports/lap-28-C-offline.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
    return value['passed']


def fixture_audit():
    """Native encodings and final policy measurements; no token-bound claim."""
    from test_lap28_capability import settings
    from scripts.observe_lap28 import inputs
    from qqbot_gateway.vision import normalize,NativeImage,CURRENT,AUDIT,wire_check,cli_message,native_payload_images,text_budget
    from qqbot_gateway.vision_capabilities import CASES
    from qqbot_gateway.backends import resolve_backend
    from qqbot_gateway.ollama_ssh_runner import native_payload
    from qqbot_gateway.token_budget import InputBudget
    rows=[];spec=json.loads((ROOT/'tests/fixtures/lap28-C/spec.json').read_text(encoding='utf-8'))
    for backend in ('codebuddy_cli','ollama_ssh'):
        s=settings();s['llm']['backend']=backend
        cfg=resolve_backend(s);budget=InputBudget.from_settings(s)
        for case in CASES:
            blob=normalize((ROOT/'tests/fixtures/lap28-C'/(case+'.png')).read_bytes())
            token=CURRENT.set(NativeImage(blob,4096,time.monotonic()+60,time.monotonic()+15));metrics={};audit=AUDIT.set(metrics)
            try:
                system,prompt=inputs(s,budget,case)
                payload=dict(system=system,input=cli_message(prompt)) if backend=='codebuddy_cli' else native_payload_images(native_payload(cfg,system,prompt))
                wire_check(payload)
                rows.append(dict(backend=backend,case=case,width=blob.width,height=blob.height,normalized_bytes=len(blob.data),
                    fixture_sha256=spec['cases'][case]['sha256'],visible_policy_bytes=text_budget(budget).usage(system,prompt),
                    text_policy_limit=text_budget(budget).limit,visual_reserve_policy=4096,output_reserve=budget.output,
                    trusted_visual_upper_bound=False,**metrics))
            finally:AUDIT.reset(audit);CURRENT.reset(token)
    (ROOT/'reports/lap-28-C-fixtures.json').write_text(json.dumps(dict(rows=rows,real_generations=0),indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('units','frameworks','fixtures','finalize'))
    mode=parser.parse_args().mode
    if mode=='frameworks':asyncio.run(frameworks())
    elif mode=='fixtures':fixture_audit()
    else:raise SystemExit(0 if (units() if mode=='units' else finalize()) else 1)
