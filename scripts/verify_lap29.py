"""Independent LAP-29 verification. Synthetic inputs and local fake transports only."""
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
        framework=json.loads((ROOT/'reports/lap-29-framework-offline.json').read_text(encoding='utf-8'))
        summary=dict(passed=True,unit_tests=result.testsRun,framework_combinations=len(framework),
            framework_cases=sum(len(row['cases']) for row in framework),member_combinations=sum(row.get('lap29',False) for row in framework),
            real_model_calls=0,real_qq_calls=0,real_bot_operations=0,production_eligible=False,
            count_freshness_verified=False,capability_state='offline_passed',activation_error='capability_unverified')
        (ROOT/'reports/lap-29-offline.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
        print('PASS LAP-29 offline; production members remain capability_unverified',flush=True)
        return 0
    from scripts.verify_lap29_framework import verify as member
    from scripts.verify_lap27 import verify as attention
    from scripts.verify_lap28_framework import verify as vision
    from scripts.verify_lap20 import verify as legacy
    from scripts.verify_lap21 import verify as media
    results=[];previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap29-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    for participation in ('mentions','free'):
                        for web,memes in ((False,False),(False,True),(True,False),(True,True)):
                            root=Path(directory)/(backend+mode+participation+str(web)+str(memes));root.mkdir()
                            row=asyncio.run(member(root,backend,mode,participation,memes=memes,web_enabled=web))
                            row['lap29']=True;results.append(row)
                        root=Path(directory)/(backend+mode+participation+'old-media');root.mkdir()
                        results.append(asyncio.run(media(root,backend,mode,participation,full_lifecycle=True,lap24=True,lap25=True)))
                    root=Path(directory)/(backend+mode+'attention');root.mkdir()
                    results.append(asyncio.run(attention(root,backend,mode,True,True)))
                    root=Path(directory)/(backend+mode+'v1');root.mkdir()
                    results.append(asyncio.run(legacy(root,backend,mode,full_lifecycle=True,lap24=True,lap25=True)))
                    root=Path(directory)/(backend+mode+'vision');root.mkdir()
                    results.append(asyncio.run(vision(root,backend,mode)))
        finally:os.chdir(previous)
    (ROOT/'reports/lap-29-framework-offline.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS LAP-29 actual framework/native-runner fakes; zero real model/QQ/bot operations',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
