"""LAP-22 actual run_agent completion/decorate flow; synthetic transports only."""
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from scripts.verify_lap20 import verify


def main():
    results=[];previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap22-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    root=Path(directory)/(backend+'-'+mode);root.mkdir()
                    results.append(asyncio.run(verify(root,backend,mode,full_lifecycle=True)))
                    print('PASS',backend,mode,len(results[-1]['cases']))
        finally:os.chdir(previous)
    (ROOT/'reports/lap-22-framework-offline.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
