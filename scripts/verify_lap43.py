"""LAP-43 native web: focused offline units and existing event/ACK harness.
Never invokes the real CLI/model, public network, QQ, SSH or production runtime.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
os.environ['ASTRBOT_DISABLE_METRICS']='1'

async def frameworks():
    from scripts.verify_lap43_framework import verify
    previous=Path.cwd();rows=[]
    with tempfile.TemporaryDirectory(prefix='lap43-native-framework-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                root=Path(directory)/backend;root.mkdir()
                rows.append(await verify(root,backend,'adaptive',participation='free',attention=True,
                    memes=True,web_enabled=True,memory=True,members=True))
        finally:os.chdir(previous)
    return rows


def main():
    modules=('test_native_web','test_cli_runner',
        'test_lap42_vision.HostedRunnerTests.test_real_runner_control_only_zero_user',
        'test_lap42_vision.ImageMemberCapTests.test_image_with_optional_member_cap_resolves_image_cap_only')
    suite=unittest.defaultTestLoader.loadTestsFromNames(modules)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():return 1
    rows=asyncio.run(frameworks())
    from qqbot_gateway.vision import adapter_signature
    from qqbot_gateway.vision_capabilities import digest
    from qqbot_gateway.hosted_cli_budget import review_record
    from qqbot_gateway.hosted_cli_budget import template_diagnostics
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    value=dict(schema_version=1,mode='lap43_current_regression',passed=True,
        adapter_signature=adapter_signature(),rule_hash=digest(review_record()),
        verifier_sha256=sha(Path(__file__)),tests_sha256=sha(ROOT/'tests/test_native_web.py'),
        source_audit_sha256=sha(ROOT/'reports/lap-43-native-web-sources.json'),
        framework_verifier_sha256=sha(ROOT/'scripts/verify_lap43_framework.py'),
        unit_tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),modules=modules,
        frameworks=rows,framework_cases=sum(len(row['cases']) for row in rows),
        real_model_calls=0,real_qq_outputs=0,public_network_calls=0,bot_start_stop_operations=0,
        real_cli_contract='not_run_native_web',native_search='unverified_not_enabled',
        native_iq_eligible=False,production_eligible=False,
        installed_visual_template_diagnostics=template_diagnostics(),
        scope='Existing Harness/actual runner/provider/event ACK with synthetic CLI/RPC; no live tool or image acceptance.')
    path=ROOT/'reports/lap-43-native-web-offline.json'
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,units=result.testsRun,framework_cases=value['framework_cases'])))
    return 0

if __name__=='__main__':raise SystemExit(main())
