"""Independent LAP-35 verifier. Synthetic temp roots only; no old main() calls."""
import asyncio
import copy
from contextlib import ExitStack
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / 'tests')]
os.environ['ASTRBOT_DISABLE_METRICS'] = '1'


def main():
    if sys.argv[1:] != ['--frameworks-only']:
        # A tracked user-owned persona is deliberately not part of LAP-35.
        # The old LAP-24 fixed-size regression uses its committed test baseline;
        # no workspace persona is read, changed, staged, or printed by this run.
        baseline = subprocess.run(['git','show','HEAD:config/persona.md'],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8')
        read_text = Path.read_text
        def fixture_read(path, *args, **kwargs):
            if path.resolve() == (ROOT/'config/persona.md').resolve():return baseline
            return read_text(path, *args, **kwargs)
        with patch.object(Path,'read_text',fixture_read):
            result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
        if not result.wasSuccessful():return 1
        subprocess.run([str(ROOT/'runtime/astrbot-tool/astrbot/Scripts/python.exe'),'-X','utf8',str(Path(__file__).resolve()),'--frameworks-only'],cwd=ROOT/'runtime/astrbot',check=True)
        rows=json.loads((ROOT/'reports/lap-35-framework-offline.json').read_text(encoding='utf-8'))
        summary=dict(passed=True,unit_tests=result.testsRun,persona_fixture='committed HEAD baseline; workspace untouched',
                     framework_combinations=len(rows),framework_cases=sum(len(row['cases']) for row in rows),
                     real_model_calls=0,real_qq_calls=0,real_bot_operations=0,local_migrated=False,
                     real_acceptance=False,complete_acceptance=False)
        (ROOT/'reports/lap-35-offline.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('PASS LAP-35 offline; real migration/loading pending')
        return 0
    rows=[];previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap35-framework-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    for participation in ('mentions','free'):
                        for family,opts in [('plain',{}),('attention',{'attention':True}),('memory',{'memory':True}),('media',{'memes':True}),('members',{'members':True}),('combined',{'attention':True,'memory':True,'memes':True,'members':True})]:
                            if family=='attention' and participation=='mentions':continue
                            root=Path(directory)/(backend+mode+participation+family);root.mkdir()
                            from scripts.verify_lap35_framework import verify
                            rows.append(asyncio.run(verify(root,backend,mode,participation,**opts)))
                            print('PASS',backend,mode,participation,family,len(rows[-1]['cases']))
        finally:os.chdir(previous)
    (ROOT/'reports/lap-35-framework-offline.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0


if __name__ == '__main__':raise SystemExit(main())
