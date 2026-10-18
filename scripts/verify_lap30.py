"""Independent synthetic LAP-30 verification; never invokes prior report writers."""
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
        subprocess.run([str(ROOT/'runtime/astrbot-tool/astrbot/Scripts/python.exe'),'-X','utf8',str(Path(__file__).resolve()),'--frameworks-only'],cwd=ROOT/'runtime/astrbot',check=True)
        rows=json.loads((ROOT/'reports/lap-30-framework-offline.json').read_text(encoding='utf-8'))
        summary=dict(passed=True,unit_tests=result.testsRun,framework_combinations=len(rows),framework_cases=sum(len(r['cases']) for r in rows),
            memory_combinations=sum(r.get('lap30',False) for r in rows),real_model_calls=0,real_qq_calls=0,real_bot_operations=0,
            memory_default_enabled=False,learning_default_enabled=False,real_acceptance=False,complete_acceptance=False)
        (ROOT/'reports/lap-30-offline.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
        print('PASS LAP-30 offline; real/complete acceptance pending',flush=True);return 0
    from scripts.verify_lap30_framework import verify as memory
    from scripts.verify_lap29_framework import verify as members
    from scripts.verify_lap28_framework import verify as vision
    from scripts.verify_lap27 import verify as attention
    from scripts.verify_lap20 import verify as legacy
    from scripts.verify_lap21 import verify as media
    rows=[];previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap30-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    for participation in ('mentions','free'):
                        for web,memes in ((False,False),(False,True),(True,False),(True,True)):
                            root=Path(directory)/(backend+mode+participation+str(web)+str(memes));root.mkdir()
                            row=asyncio.run(memory(root,backend,mode,participation,memes=memes,web_enabled=web));row['lap30']=True;rows.append(row)
                        root=Path(directory)/(backend+mode+participation+'members');root.mkdir()
                        rows.append(asyncio.run(members(root,backend,mode,participation,memes=True,web_enabled=True,memory_enabled=True)))
                        root=Path(directory)/(backend+mode+participation+'memory-vision');root.mkdir()
                        rows.append(asyncio.run(vision(root,backend,mode,participation,memory_enabled=True)))
                        root=Path(directory)/(backend+mode+participation+'media');root.mkdir()
                        rows.append(asyncio.run(media(root,backend,mode,participation,full_lifecycle=True,lap24=True,lap25=True)))
                    for label,fn in [('attention',attention),('vision',vision)]:
                        root=Path(directory)/(backend+mode+label);root.mkdir()
                        rows.append(asyncio.run(fn(root,backend,mode)))
                    root=Path(directory)/(backend+mode+'v1');root.mkdir()
                    rows.append(asyncio.run(legacy(root,backend,mode,full_lifecycle=True,lap24=True,lap25=True)))
        finally:os.chdir(previous)
    (ROOT/'reports/lap-30-framework-offline.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS LAP-30 actual framework + two native runner fakes',flush=True);return 0

if __name__=='__main__':raise SystemExit(main())
