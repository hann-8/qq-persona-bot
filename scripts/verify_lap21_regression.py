"""Affected LAP-18/20 and legacy paths, all synthetic and separate reports."""
import asyncio,json,os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
os.environ['ASTRBOT_DISABLE_METRICS']='1'
async def main(root):
    from scripts.verify_lap18 import main as web_regression
    from scripts.verify_lap20 import verify as group_regression
    from scripts.verify_lap20_gate import verify as guard_regression
    await guard_regression()
    results=[]
    for backend in ('codebuddy_cli','ollama_ssh'):
        for mode in ('single','adaptive'):
            folder=root/(backend+'-'+mode);folder.mkdir()
            results.append(await group_regression(folder,backend,mode))
    (ROOT/'reports/lap-21-regression-group.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    folder=root/'web';folder.mkdir();await web_regression(folder,'lap-21-regression')
if __name__=='__main__':
    with tempfile.TemporaryDirectory(prefix='qqbot-lap21-regression-',ignore_cleanup_errors=True) as folder:
        os.chdir(folder);asyncio.run(main(Path(folder)))
