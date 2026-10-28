"""R1 offline writer: new report, old A/B/42 evidence remains immutable.

All generated fixtures and framework work use temporary roots. Optional persona
is read only inside the capacity calculation; its contents are never serialized.
This writer cannot perform public requests, real CLI probes or native IQ.
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
os.environ['ASTRBOT_DISABLE_METRICS']='1'


async def frameworks():
    from scripts.verify_lap43_framework import verify
    from scripts.verify_lap28_framework import verify as images
    previous=Path.cwd();rows=[]
    with tempfile.TemporaryDirectory(prefix='lap43-materials-framework-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                root=Path(directory)/backend;root.mkdir()
                rows.append(await verify(root,backend,'adaptive',participation='free',attention=True,
                    memes=True,web_enabled=True,memory=True,members=True,material_kind='search_snippet'))
                v1_root=Path(directory)/(backend+'-v1');v1_root.mkdir()
                rows.append(await verify(v1_root,backend,'adaptive',participation='free',attention=False,
                    memes=True,web_enabled=True,memory=False,members=False,material_kind='search_snippet'))
                image_root=Path(directory)/(backend+'-images');image_root.mkdir()
                rows.append(await images(image_root,backend,'adaptive',participation='free',attention=True,
                    memes=True,web_enabled=True,memory_enabled=True,body_reader=True))
        finally:os.chdir(previous)
    return rows


def capacity(persona):
    import io,time
    from PIL import Image
    from test_lap43 import settings
    from qqbot_gateway.persona import compose_persona
    from qqbot_gateway.vision import POLICY,CURRENT,NativeImage,normalize,text_budget,member_source
    from qqbot_gateway.members import POLICY as MEMBER_POLICY
    from qqbot_gateway.token_budget import InputBudget,dialog_text
    from qqbot_gateway.turn_v2 import fit
    from qqbot_gateway.turn_budget import candidate_instruction
    from qqbot_gateway.web_retrieval import Retrieval,evidence_prompt
    from qqbot_gateway.evidence_selection import material
    from qqbot_gateway.web_freshness import facts
    from qqbot_gateway.hosted_cli_budget import final_budget,review_record
    from qqbot_gateway.errors import GatewayError
    character=persona.read_text(encoding='utf-8') if persona else '合成人设'
    rows=[]
    for backend in ('codebuddy_cli','ollama_ssh'):
        d=settings();d['llm']['backend']=backend
        if backend=='codebuddy_cli':
            d['llm']['profiles'][backend]['input_budget']['context_input_limit_tokens']=48000
            d['llm']['profiles'][backend]['reasoning_effort']='low'
        else:d['llm']['profiles'][backend]['expected_digest']='a'*64
        d['participation']['mode']='free';d['participation']['attention']['enabled']=True
        for key in ('vision','members','memes','memory','web'):d[key]['enabled']=True
        budget=InputBudget.from_settings(d)
        system=compose_persona(character,d['output'],d['web'],d['participation'],d['memes'],d['vision'],d['members'],d['memory'])+POLICY+MEMBER_POLICY
        source=member_source('鱼鱼查查Python最近消息',d['participation']['attention']['aliases'])
        suffix=candidate_instruction([dict(id='m_'+str(i)*64,name='synthetic',context='happy',tags=['happy']) for i in range(7)])
        image=io.BytesIO();Image.new('RGB',(1000,1000),'red').save(image,format='PNG');blob=normalize(image.getvalue())
        token=CURRENT.set(NativeImage(blob,4096,time.monotonic()+60,time.monotonic()+15))
        try:
            try:body=fit(source,dict(addressing='direct_name',target_seq=1),system,text_budget(budget),suffix)
            except GatewayError as error:
                if error.code!='INPUT_TOO_LONG':raise
                rows.append(dict(backend=backend,persona_source='current_in_process_only' if persona else 'synthetic',policy_limit=budget.limit,admitted=False,reason=error.code,passed=True))
                continue
            # Conservative optional material maxima, synthetic text only.
            prompt=dialog_text([dict(role='user',content=body+'\n'+json.dumps(dict(member_material='m'*768,memory_material='k'*1536)))])
            web=[dict(title='Synthetic Python source '+str(i),url='https://example.com/'+str(i),status='summary',text='Python supports the current stable release. '*20,published_at=None,fetched_at='2026-10-28T10:00:00+00:00',freshness=facts([],'2026-10-28T10:00:00+00:00','2026-10-28T10:00:00+00:00'),material=material('search_snippet','summary'),time_policy='recent_hint') for i in range(2)]
            enriched,selected=evidence_prompt(system+suffix,prompt,Retrieval('search',web,time_policy='recent_hint'),text_budget(budget),d['web'])
            if len(selected)!=2:raise ValueError('CAPACITY_OPTIONAL_MATERIALS_MISSING')
            text_budget(budget).check(system+suffix,enriched)
            native=final_budget(review_record(),budget,system+suffix,enriched,1000,1000,dict(id='deepseek-v4.1-flash',maxInputTokens=1000000,maxOutputTokens=128000,supportsImages=True,reasoning=dict(supportedEfforts=['low']))) if backend=='codebuddy_cli' else None
            rows.append(dict(backend=backend,persona_source='current_in_process_only' if persona else 'synthetic',policy_limit=budget.limit,admitted=True,combined_bytes=text_budget(budget).usage(system+suffix,enriched),web_sources=2,meme_candidates=7,member_bytes=768,memory_bytes=1536,normalized_pixels=blob.width*blob.height,native=native,passed=True))
        finally:CURRENT.reset(token)
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current-persona',type=Path)
    args=parser.parse_args()
    modules=('test_lap43_materials','test_web','test_web_freshness','test_lap43',
        'test_vision_mod_guard','test_lap42_vision.HostedRunnerTests',
        'test_lap42_vision.OperatorAcceptanceTests',
        'test_lap42_vision.ImageMemberCapTests.test_image_with_optional_member_cap_resolves_image_cap_only')
    previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='lap43-materials-unit-',ignore_cleanup_errors=True) as directory:
        root=Path(directory);(root/'config').mkdir()
        shutil.copyfile(ROOT/'config/settings.example.yaml',root/'config/settings.example.yaml')
        os.chdir(root)
        try:
            suite=unittest.defaultTestLoader.loadTestsFromNames(modules)
            result=unittest.TextTestRunner(verbosity=1).run(suite)
            if not result.wasSuccessful():return 1
            rows=asyncio.run(frameworks());budget=capacity(args.current_persona)
        finally:os.chdir(previous)
    from qqbot_gateway.vision import adapter_signature
    from qqbot_gateway.vision_capabilities import digest
    from qqbot_gateway.hosted_cli_budget import review_record
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    value=dict(schema_version=1,mode='lap43_current_regression',passed=True,
        adapter_signature=adapter_signature(),rule_hash=digest(review_record()),
        verifier_sha256=sha(Path(__file__)),tests_sha256=sha(ROOT/'tests/test_lap43_materials.py'),
        source_audit_sha256=sha(ROOT/'reports/lap-43-materials-sources.json'),
        unit_tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),modules=modules,
        frameworks=rows,framework_cases=sum(len(r['cases']) for r in rows),capacity=budget,
        real_model_calls=0,real_qq_outputs=0,public_network_calls=0,bot_start_stop_operations=0,
        real_cli_contract='not_run_R1',native_iq_eligible=False,production_eligible=False,
        scope='Synthetic HTML/events/images/RPC; actual provider and runner bottom substitutes. No real response naturalness claim.')
    path=ROOT/'reports/lap-43-materials-offline.json'
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,units=result.testsRun,framework_cases=value['framework_cases'],capacity=budget)))
    return 0


if __name__=='__main__':raise SystemExit(main())
