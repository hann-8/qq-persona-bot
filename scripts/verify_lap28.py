"""Independent LAP-28 offline verifier. Never invokes old verifier main/report writes."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
os.environ['ASTRBOT_DISABLE_METRICS']='1'


def main():
    if sys.argv[1:]!=['--frameworks-only']:
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
        if not result.wasSuccessful():return 1
        subprocess.run([str(ROOT/'runtime/astrbot-tool/astrbot/Scripts/python.exe'),'-X','utf8',str(Path(__file__).resolve()),'--frameworks-only'],
                       cwd=ROOT/'runtime/astrbot',check=True)
        from qqbot_gateway.vision import adapter_signature
        framework=json.loads((ROOT/'reports/lap-28-framework-offline.json').read_text(encoding='utf-8'))
        report=dict(passed=True,adapter_signature=adapter_signature(),unit_tests=result.testsRun,
            framework_combinations=len(framework),framework_cases=sum(len(r['cases']) for r in framework),
            real_model_calls=0,real_qq_calls=0,real_bot_operations=0,production_eligible=False,
            capability_state='offline_passed',native_observed=False,visual_reserve_upper_bound_verified=False)
        (ROOT/'reports/lap-28-offline.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
        return 0
    from scripts.verify_lap28_framework import verify as vision
    from scripts.verify_lap27 import verify as attention
    from scripts.verify_lap20 import verify as legacy
    from scripts.verify_lap21 import verify as media
    results=[];previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap28-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    for participation,enabled in (('free',False),('free',True),('mentions',False)):
                        root=Path(directory)/(backend+mode+participation+str(enabled));root.mkdir()
                        results.append(asyncio.run(vision(root,backend,mode,participation,enabled)))
                    root=Path(directory)/(backend+mode+'vision-web');root.mkdir()
                    results.append(asyncio.run(vision(root,backend,mode,web_enabled=True)))
                    root=Path(directory)/(backend+mode+'vision-memes');root.mkdir()
                    results.append(asyncio.run(vision(root,backend,mode,memes=True)))
                    root=Path(directory)/(backend+mode+'vision-web-memes');root.mkdir()
                    results.append(asyncio.run(vision(root,backend,mode,memes=True,web_enabled=True)))
                    root=Path(directory)/(backend+mode+'vision-member-web');root.mkdir()
                    results.append(asyncio.run(vision(root,backend,mode,participation='mentions',attention=False,web_enabled=True)))
                    for web,memes in ((False,False),(False,True),(True,False),(True,True)):
                        root=Path(directory)/(backend+mode+'attention'+str(web)+str(memes));root.mkdir()
                        results.append(asyncio.run(attention(root,backend,mode,memes,web)))
                    root=Path(directory)/(backend+mode+'v1');root.mkdir()
                    results.append(asyncio.run(legacy(root,backend,mode,full_lifecycle=True,lap24=True,lap25=True)))
                    for participation in ('mentions','free'):
                        root=Path(directory)/(backend+mode+'media'+participation);root.mkdir()
                        results.append(asyncio.run(media(root,backend,mode,participation,full_lifecycle=True,lap24=True,lap25=True)))
        finally:os.chdir(previous)
    (ROOT/'reports/lap-28-framework-offline.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS LAP-28 framework: synthetic inputs/transports, zero real model/QQ/bot operations',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
