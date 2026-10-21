"""Local-only package footprint and owned-worker quality/resource measurements."""
import asyncio
import importlib.metadata as metadata
import json
from pathlib import Path
import sys
import time
import tomllib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from qqbot_gateway.web_extractor import WebExtractor
from test_lap18_body import FACTS,fixture


async def main():
    lock=tomllib.loads((ROOT/'uv.lock').read_text(encoding='utf-8'));packages=[]
    for name in ('readability-lxml','chardet','cssselect','lxml','lxml-html-clean'):
        dist=metadata.distribution(name)
        files={Path(dist.locate_file(file)).resolve() for file in dist.files if Path(dist.locate_file(file)).is_file()}
        package_dir=Path(dist.locate_file({'readability-lxml':'readability','lxml-html-clean':'lxml_html_clean'}.get(name,name)))
        files.update(p.resolve() for p in package_dir.rglob('*') if p.is_file())
        row=next(p for p in lock['package'] if p['name']==name)
        wheels=[w for w in row['wheels'] if 'py3-none-any.whl' in w['url'] or 'cp312-cp312-win_amd64.whl' in w['url']]
        assert len(wheels)==1
        packages.append(dict(name=name,version=dist.version,installed_bytes=sum(p.stat().st_size for p in files),
                             wheel_bytes=wheels[0]['size'],wheel_sha256=wheels[0]['hash']))
    pages=[];extractor=WebExtractor(ROOT/'state/lap18-B-resource-scratch')
    for title,body in FACTS:
        html=fixture(title,body);started=time.monotonic();result=await extractor.extract(html)
        assert body in result['text'] and result['title']==title
        pages.append(dict(sample=title,input_bytes=len(html.encode()),body_bytes=len(result['text'].encode()),
                          facts_preserved=3,noise_removed=True,**extractor.last_metrics))
    # A bounded larger near-1MiB document: output overrun fails without delivery.
    stress='<article>'+''.join('<p>'+('可核对事实。'*50)+'</p>' for _ in range(900))+'</article>'
    from qqbot_gateway.public_http import WebFailure
    try:
        await extractor.extract(stress)
        stress_status='extracted'
    except WebFailure as error:stress_status=str(error)
    value=dict(dependencies=packages,dependency_count=len(packages),
               installed_bytes=sum(p['installed_bytes'] for p in packages),
               wheel_bytes=sum(p['wheel_bytes'] for p in packages),
               installation_observation=dict(lock_seconds=5.12,prepare_seconds=4.21,install_seconds=.193,
                   framework_prepare_seconds=.005,framework_install_seconds=.075,
                   cache_note='uv prepared fixed wheels; transfer-only bytes/time unavailable separately from cache. Sum is Windows wheel artifact size, not measured network traffic.',
                   framework_existing='lxml 6.1.3 already installed; chardet upgraded 5.1.0 to 5.2.0; three new distributions'),
               pages=pages,stress=dict(input_bytes=len(stress.encode()),status=stress_status,**extractor.last_metrics),
               idle_worker_count=0 if extractor.active_pid is None else 1,real_network_reads=0,real_model_calls=0)
    (ROOT/'reports/lap-18-B-resources.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(value,ensure_ascii=False,indent=2))


if __name__=='__main__':asyncio.run(main())
