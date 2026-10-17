"""LAP-25 actual framework/runner synthesis in temporary roots only."""
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
os.environ['ASTRBOT_DISABLE_METRICS']='1'
from scripts.verify_lap20 import verify as group_verify
from scripts.verify_lap21 import verify as media_verify


def main():
    results=[];previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap25-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    root=Path(directory)/(backend+'-'+mode+'-group');root.mkdir()
                    result=asyncio.run(group_verify(root,backend,mode,full_lifecycle=True,lap24=True,lap25=True))
                    results.append(result);print('PASS group',backend,mode,len(result['cases']),flush=True)
                    for participation in ('mentions','free'):
                        root=Path(directory)/(backend+'-'+mode+'-'+participation+'-media');root.mkdir()
                        result=asyncio.run(media_verify(root,backend,mode,participation,full_lifecycle=True,lap24=True,lap25=True))
                        results.append(result);print('PASS media',backend,mode,participation,len(result['cases']),flush=True)
        finally:os.chdir(previous)
    (ROOT/'reports/lap-25-framework-offline.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
