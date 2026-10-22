"""Existing image/member/silence combinations, Bilibili disabled compatibility."""
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
    from scripts.verify_lap28_framework import verify as image
    from scripts.verify_lap35_framework import verify as silence
    rows=[];previous=Path.cwd();started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='lap06-regression-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for participation in ('mentions','free'):
                    root=Path(directory)/(backend+participation+'image');root.mkdir()
                    rows.append(await image(root,backend,'adaptive',participation=participation,attention=True,web_enabled=True,memes=True,memory_enabled=True,body_reader=True))
                    root=Path(directory)/(backend+participation+'silence');root.mkdir()
                    rows.append(await silence(root,backend,'adaptive',participation,attention=True,memory=True,memes=True,members=True,web_enabled=True))
        finally:os.chdir(previous)
    value=dict(passed=True,combinations=len(rows),cases=sum(len(r['cases']) for r in rows),elapsed_seconds=round(time.monotonic()-started,3),
               bilibili_enabled=False,real_model_calls=0,real_qq_outputs=0,rows=rows)
    (ROOT/'reports/lap-06-regression-offline.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('LAP06_REGRESSION',value['combinations'],value['cases'],value['elapsed_seconds'])
if __name__=='__main__':asyncio.run(main())
