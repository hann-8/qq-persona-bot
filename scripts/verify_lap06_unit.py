"""Affected unit suite with legacy cross-test imports resolved; no real services."""
import json
from pathlib import Path
import sys
import time
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
modules=['test_bilibili','test_web','test_lap18_body','test_config_files','test_config_comments','test_config',
         'test_token_budget','test_lap27','test_lap28','test_lap29','test_lap30','test_group_silence','test_participation','test_model_gateway']
if __name__=='__main__':
    started=time.monotonic()
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromNames(modules))
    value=dict(passed=result.wasSuccessful(),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
               elapsed_seconds=round(time.monotonic()-started,3),modules=modules,real_model_calls=0,real_qq_outputs=0)
    (ROOT/'reports/lap-06-unit.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    sys.exit(0 if result.wasSuccessful() else 1)
