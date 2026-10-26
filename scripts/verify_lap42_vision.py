"""Focused LAP-42 offline writer. Never invokes historical report writers.

Public source files are read from the private source cache with pinned hashes.
Real IQ eligibility is intentionally distinct from passing these regression tests.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import subprocess

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
os.environ['ASTRBOT_DISABLE_METRICS']='1'


async def frameworks():
    rows=[];previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='lap42-vision-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            from scripts.verify_lap28_framework import verify as images
            from scripts.verify_lap29_framework import verify as members
            from scripts.verify_lap35_framework import verify as silence
            for name,verify,flags in (
                ('images',images,dict(memory_enabled=True,body_reader=False)),
                ('members',members,dict(memory_enabled=True)),
                ('silence',silence,dict(memory=True,members=True))):
                root=Path(directory)/name;root.mkdir()
                rows.append(await verify(root,'codebuddy_cli','adaptive',participation='free',
                    attention=True,memes=True,web_enabled=True,**flags))
        finally:os.chdir(previous)
    return rows


def main():
    modules=('test_lap42_vision','test_vision_mod_guard','test_lap28','test_lap28_ingress','test_lap28_capability',
             'test_cli_runner','test_cli_control','test_token_budget','test_lap42')
    suite=unittest.defaultTestLoader.loadTestsFromNames(modules)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    rows=[]
    if result.wasSuccessful():
        work=ROOT/'state/lap42-vision-finish/framework-work';work.mkdir(exist_ok=True)
        output=work/'result.json'
        with (work/'console.log').open('w',encoding='utf-8') as console:
            check=subprocess.run([str(ROOT/'runtime/astrbot-tool/astrbot/Scripts/python.exe'),str(Path(__file__)),
                                  '--framework-only',str(output)],cwd=work,stdout=console,stderr=subprocess.STDOUT)
        if check.returncode==0:rows=json.loads(output.read_text(encoding='utf-8'))
    from qqbot_gateway.vision import adapter_signature
    from qqbot_gateway.vision_capabilities import digest
    from qqbot_gateway.hosted_cli_budget import review_record
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    value=dict(schema_version=1,passed=result.wasSuccessful() and len(rows)==3,
        adapter_signature=adapter_signature(),rule_hash=digest(review_record()),
        verifier_sha256=sha(Path(__file__)),tests_sha256=sha(ROOT/'tests/test_lap42_vision.py'),
        source_audit_sha256=sha(ROOT/'reports/lap-42-vision-closure-sources.json'),
        unit_tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),modules=modules,
        frameworks=rows,framework_combinations=len(rows),framework_cases=sum(len(r['cases']) for r in rows),
        real_model_calls=0,real_qq_outputs=0,bot_start_stop_operations=0,
        native_iq_eligible=False,production_eligible=False,
        remaining_source_gap=None,real_cli_contract='pending_actual_probe',
        scope='Current hosted regression and existing original AstrBot event/actual runner bottom substitutes; legacy harnesses do not prove hosted native eligibility.')
    (ROOT/'reports/lap-42-vision-offline.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:value[k] for k in ('passed','unit_tests','framework_cases','remaining_source_gap')}))
    return 0 if value['passed'] else 1


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--framework-only':
        Path(sys.argv[2]).write_text(json.dumps(asyncio.run(frameworks()),ensure_ascii=False,indent=2),encoding='utf-8')
    else:raise SystemExit(main())
