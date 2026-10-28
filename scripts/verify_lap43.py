"""LAP-43 only: focused units, actual AstrBot/two runner substitutes and capacity."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
os.environ['ASTRBOT_DISABLE_METRICS']='1'

def capacity(persona_path):
    from test_lap43 import settings
    from qqbot_gateway.persona import compose_persona
    from qqbot_gateway.token_budget import InputBudget,dialog_text
    from qqbot_gateway.vision import normalize,NativeImage,CURRENT,text_budget,member_source
    from qqbot_gateway.turn_v2 import fit,sha
    from qqbot_gateway.evidence_selection import sources_for_budget
    from qqbot_gateway.web_freshness import facts
    from qqbot_gateway.turn_budget import candidate_instruction
    from qqbot_gateway.hosted_cli_budget import final_budget,review_record
    import io,time
    from PIL import Image
    character=persona_path.read_text(encoding='utf-8') if persona_path else '合成人设'
    rows=[]
    for backend in ('codebuddy_cli','ollama_ssh'):
        d=settings();d['llm']['backend']=backend
        if backend=='codebuddy_cli':
            d['llm']['profiles'][backend]['input_budget']['context_input_limit_tokens']=48000
            d['llm']['profiles'][backend]['reasoning_effort']='low'
        else:d['llm']['profiles'][backend]['expected_digest']='a'*64
        d['participation']['mode']='free';d['participation']['attention']['enabled']=True
        for k in ('vision','members','memes','memory','web'):d[k]['enabled']=True
        b=InputBudget.from_settings(d);system=compose_persona(character,d['output'],d['web'],d['participation'],d['memes'],d['vision'],d['members'],d['memory'])
        source=member_source('鱼鱼查查最新消息',d['participation']['attention']['aliases'])
        source['member_candidates']=[dict(member_ref='p_'+'1'*16,name='synthetic')]
        # Use valid protocol source; bounded material additions are measured explicitly.
        source['member_candidates']=[]
        request=dict(addressing='direct_name',target_seq=1)
        image=io.BytesIO();Image.new('RGB',(1000,1000),'red').save(image,format='PNG')
        blob=normalize(image.getvalue());token=CURRENT.set(NativeImage(blob,4096,time.monotonic()+60,time.monotonic()+15))
        try:
            memes=[dict(id='m_'+str(i)*64,name='synthetic',context='happy',tags=['happy']) for i in range(7)]
            suffix=candidate_instruction(memes)
            try:body=fit(source,request,system,text_budget(b),suffix)
            except Exception as error:
                from qqbot_gateway.errors import GatewayError
                if not isinstance(error,GatewayError) or error.code!='INPUT_TOO_LONG':raise
                rows.append(dict(backend=backend,persona_source='current_in_process_only' if persona_path else 'synthetic',persona_bytes=len(character.encode()),policy_limit=b.limit,admitted=False,reason=error.code,passed=True,scope='Mandatory persona plus turn rejected before generation; optional materials not submitted'))
                continue
            web=sources_for_budget([dict(title='Public '+str(i),url='https://example.com/'+str(i),status='body',text='public facts '*100,published_at='2026-10-27',freshness=facts([dict(kind='published',source='meta',value='2026-10-27')],'2026-10-27T11:00:00+00:00','2026-10-27T11:00:01+00:00')) for i in range(2)],6000,4000,'excerpt','latest news')
            final=dialog_text([dict(role='user',content=body+'\n'+json.dumps(web,ensure_ascii=False)+'\n'+json.dumps(dict(member_material='m'*768,memory_material='k'*1536)))])
            text_budget(b).check(system+suffix,final)
            native=final_budget(review_record(),b,system+suffix,final,1000,1000,dict(id='deepseek-v4.1-flash',maxInputTokens=1000000,maxOutputTokens=128000,supportsImages=True,reasoning=dict(supportedEfforts=['low']))) if backend=='codebuddy_cli' else None
            rows.append(dict(backend=backend,persona_source='current_in_process_only' if persona_path else 'synthetic',persona_bytes=len(character.encode()),policy_limit=b.limit,combined_bytes=text_budget(b).usage(system+suffix,final),web_sources=2,meme_candidates=7,member_bytes=768,memory_bytes=1536,normalized_pixels=blob.width*blob.height,native=native,admitted=True,passed=True))
        finally:CURRENT.reset(token)
    return rows

async def frameworks():
    from scripts.verify_lap43_framework import verify
    previous=Path.cwd();rows=[]
    with tempfile.TemporaryDirectory(prefix='lap43-framework-',ignore_cleanup_errors=True) as t:
        os.chdir(t)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                root=Path(t)/backend;root.mkdir()
                rows.append(await verify(root,backend,'adaptive',participation='free',attention=True,memes=True,web_enabled=True,memory=True,members=True))
                from scripts.verify_lap28_framework import verify as images
                image_root=Path(t)/(backend+'-images');image_root.mkdir()
                rows.append(await images(image_root,backend,'adaptive',participation='free',attention=True,memes=True,web_enabled=True,memory_enabled=True,body_reader=True))
        finally:os.chdir(previous)
    return rows


async def builtin_configuration(root):
    import copy,shutil,yaml
    from test_lap43 import settings
    from astrbot.core.config.default import DEFAULT_CONFIG
    from scripts import configure_astrbot as module
    from astrbot.core import sp
    from unittest.mock import patch
    from types import SimpleNamespace
    d=settings();(root/'config').mkdir(parents=True);(root/'state').mkdir();(root/'secrets').mkdir()
    (root/'config/settings.local.yaml').write_text(yaml.safe_dump(d),encoding='utf-8')
    (root/'config/persona.md').write_text('synthetic character',encoding='utf-8')
    (root/d['secrets_file']).write_text(json.dumps(dict(model_gateway='a'*40,onebot_inbound='b'*40,onebot_upstream='c'*40)),encoding='utf-8')
    data=root/'runtime/astrbot/data';(data/'plugins').mkdir(parents=True)
    (data/'cmd_config.json').write_text(json.dumps(DEFAULT_CONFIG),encoding='utf-8')
    shutil.copytree(ROOT/'plugins/qq_router',root/'plugins/qq_router')
    disabled=[];close=sp.close
    async def capture_close():
        disabled.extend(await sp.global_get('inactivated_plugins',[]));await close()
    with patch.object(module,'ROOT',root),patch.object(sp,'close',side_effect=capture_close):await module.configure()
    saved=json.loads((data/'cmd_config.json').read_text(encoding='utf-8-sig'))
    assert saved['admins_id']==['333']
    from astrbot.core.star.star_handler import StarHandlerRegistry,EventType
    import astrbot.core.star.star_handler as registry_module
    registry=StarHandlerRegistry()
    builtin=('astrbot.builtin_stars.astrbot.main','astrbot.builtin_stars.builtin_commands.main')
    assert all(n in disabled for n in builtin)
    # The real dispatcher excludes the entire disabled command modules for every syntax.
    for name in builtin:
        registry._handlers.append(SimpleNamespace(event_type=EventType.AdapterMessageEvent,enabled=True,handler_module_path=name))
    with patch.dict(registry_module.star_map,{name:SimpleNamespace(activated=False,name=name) for name in builtin}):
        assert not registry.get_handlers_by_event_type(EventType.AdapterMessageEvent)
    (data/'plugins/unreviewed').mkdir()
    with patch.object(module,'ROOT',root):
        try:await module.configure();raise AssertionError('unknown plugin accepted')
        except RuntimeError as error:assert 'Unexpected project-instance plugins' in str(error)
    return dict(actual_configure=True,persisted_builtin_modules_disabled=2,actual_registry_filters=True,owner_same_source=True,unknown_plugin_rejected=True,scope='Isolated configuration/database and real registry; full QQ runtime is not started')

def main():
    p=argparse.ArgumentParser();p.add_argument('--current-persona',type=Path);p.add_argument('--builtin-child',type=Path);a=p.parse_args()
    if a.builtin_child:
        print(json.dumps(asyncio.run(builtin_configuration(a.builtin_child))));return 0
    suite=unittest.defaultTestLoader.loadTestsFromNames(('test_lap43','test_web_freshness','test_memes.CatalogTests','test_vision_mod_guard.ModTests','test_lap42_vision.OperatorAcceptanceTests','test_lap42_vision.ImageMemberCapTests.test_image_with_optional_member_cap_resolves_image_cap_only'))
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():return 1
    rows=asyncio.run(frameworks());budget=capacity(a.current_persona)
    import subprocess
    with tempfile.TemporaryDirectory(prefix='lap43-builtins-',ignore_cleanup_errors=True) as t:
        root=Path(t)/'project'
        process=subprocess.run([sys.executable,'-B','-X','utf8',str(Path(__file__)),'--builtin-child',str(root)],cwd=t,env=dict(os.environ,QQBOT_ROOT=str(root)),capture_output=True,text=True,encoding='utf-8')
        if process.returncode:raise RuntimeError('builtin child failed: '+process.stdout[-3000:]+process.stderr[-3000:])
        builtin=json.loads(process.stdout.strip().splitlines()[-1])
    from qqbot_gateway.vision import adapter_signature
    from qqbot_gateway.vision_capabilities import digest
    from qqbot_gateway.hosted_cli_budget import review_record
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    value=dict(schema_version=1,passed=True,adapter_signature=adapter_signature(),rule_hash=digest(review_record()),
        verifier_sha256=sha(Path(__file__)),tests_sha256=sha(ROOT/'tests/test_lap43.py'),freshness_tests_sha256=sha(ROOT/'tests/test_web_freshness.py'),
        source_audit_sha256=sha(ROOT/'reports/lap-43-vision-sources.json'),unit_tests=result.testsRun,frameworks=rows,builtin_configuration=builtin,framework_cases=sum(len(r['cases']) for r in rows),capacity=budget,
        real_model_calls=0,real_qq_outputs=0,bot_start_stop_operations=0,public_network_calls=0,native_iq_eligible=False,production_eligible=False,real_cli_contract='not_run_stage_A')
    (ROOT/'reports/lap-43-vision-offline.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,units=result.testsRun,framework_cases=value['framework_cases'],capacity=len(budget))))
    return 0
if __name__=='__main__':raise SystemExit(main())
