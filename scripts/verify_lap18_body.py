"""LAP-18B isolated actual AstrBot + actual runners with synthetic transports."""
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
    rows=[];started=time.monotonic();previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='lap18-B-framework-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    root=Path(directory)/(backend+mode);root.mkdir()
                    rows.append(await web(root,backend,mode))
                    for participation in ('mentions','free'):
                        root=Path(directory)/(backend+mode+participation+'image');root.mkdir()
                        rows.append(await image(root,backend,mode,participation=participation,attention=True,
                            web_enabled=True,memes=True,memory_enabled=True,body_reader=True))
                    root=Path(directory)/(backend+mode+'silence');root.mkdir()
                    rows.append(await silence(root,backend,mode,'free',attention=True,memory=True,memes=True,members=True,web_enabled=True))
        finally:os.chdir(previous)
    value=dict(passed=True,combinations=len(rows),cases=sum(len(r['cases']) for r in rows),elapsed_seconds=round(time.monotonic()-started,3),
               real_model_calls=0,real_qq_outputs=0,real_bot_operations=0,rows=rows)
    (ROOT/'reports/lap-18-B-framework-offline.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('LAP18_B_FRAMEWORK',value['combinations'],value['cases'],value['elapsed_seconds'])


if __name__=='__main__':asyncio.run(main())
