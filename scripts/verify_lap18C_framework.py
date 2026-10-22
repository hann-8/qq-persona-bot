"""LAP-18C isolated actual AstrBot + actual runners with synthetic transports."""
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
os.environ['ASTRBOT_DISABLE_METRICS']='1'


async def main():
    from scripts.verify_lap18 import verify as web
    from scripts.verify_lap28_framework import verify as image
    from scripts.verify_lap35_framework import verify as silence
    from scripts.verify_lap06 import verify as subtitles
    from scripts.verify_lap34 import framework_case
    compatibility=sys.argv[1:]==['--compat-only']
    rows=[];started=time.monotonic();previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='lap18-C-framework-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    if compatibility:
                        for family in ('memory','media','plain'):
                            for participation in (('free',) if family=='plain' else ('mentions','free')):
                                root=Path(directory)/(backend+mode+participation+family);root.mkdir()
                                rows.append(await framework_case(root,backend,mode,participation,family))
                        continue
                    root=Path(directory)/(backend+mode);root.mkdir()
                    rows.append(await web(root,backend,mode))
                    for participation in ('mentions','free'):
                        root=Path(directory)/(backend+mode+participation+'image');root.mkdir()
                        rows.append(await image(root,backend,mode,participation=participation,attention=True,
                            web_enabled=True,memes=True,memory_enabled=True,body_reader=True,selection_policy='question'))
                        root=Path(directory)/(backend+mode+participation+'subtitles');root.mkdir()
                        rows.append(await subtitles(root,backend,mode,participation,attention=(mode=='adaptive'),memory_enabled=(mode=='adaptive')))
                        root=Path(directory)/(backend+mode+participation+'silence');root.mkdir()
                        rows.append(await silence(root,backend,mode,participation,attention=True,memory=True,memes=True,members=True,web_enabled=True))
        finally:os.chdir(previous)
    value=dict(passed=True,combinations=len(rows),cases=sum(len(r['cases']) for r in rows),elapsed_seconds=round(time.monotonic()-started,3),
               real_model_calls=0,real_qq_outputs=0,real_bot_operations=0,rows=rows)
    report='lap-18-C-compat-framework-offline.json' if compatibility else 'lap-18-C-framework-offline.json'
    (ROOT/'reports'/report).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('LAP18_C_FRAMEWORK',value['combinations'],value['cases'],value['elapsed_seconds'])


if __name__=='__main__':asyncio.run(main())
