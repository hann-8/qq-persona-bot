"""Offline contract tests: real project plugin code, mocked host events; no CLI/model."""
import asyncio
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from qqbot_gateway.vision_mod_guard import Guard, assets_signature
from qqbot_gateway.hosted_cli_budget import final_budget,review_record,framework_upper
from test_lap42_vision import settings,model
from qqbot_gateway.token_budget import InputBudget
from qqbot_gateway.vision import normalize
from PIL import Image


def blob():
    out=io.BytesIO();Image.new('RGB',(24,16),'red').save(out,format='PNG')
    return normalize(out.getvalue())


# Executes the shipped TS module on the locked Node runtime's built-in TS loader.
# This proves handler/catch behavior only; it is explicitly NOT a real CLI probe.
HARNESS=r'''
import {pathToFileURL} from 'node:url';
import {readFileSync,writeFileSync,statSync,realpathSync,readdirSync} from 'node:fs';
const root=process.argv[2], variant=process.argv[3];
const manifest=JSON.parse(readFileSync(root+'/.codebuddy-plugin/plugin.json','utf8'));
const request=manifest.userConfig.request.default;
const q=JSON.parse(request), handlers={}, catches={};
const on=(name,fn)=>{handlers[name]=fn;return {catch: f=>{catches[name]=f}}};
const {register}=await import(pathToFileURL(root+'/hooks/register.ts').href);
register(on,{request});
let failWrite=false;
const host={plugin:{root},fs:{
 read:async(path,options)=>options?.as==='bytes'?{base64:readFileSync(path).toString('base64')}:readFileSync(path,'utf8'),
 write:async(path,text)=>{if(failWrite)throw Error('synthetic IO failure');writeFileSync(path,text)},
 stat:async(path)=>({realPath:realpathSync(path),isLink:false}),
 list:async(path)=>readdirSync(path).map(name=>({name}))
},tool:{list:async()=>[]}};
await handlers['engine.create']({}, {}, async()=>host);
const composed=await handlers['prompt.compose'](host, {model:q.model,promptModel:q.model,tools:[]});
const context=await handlers['prompt.context'](host);
if(composed.sections.length!==1 || composed.sections[0].text!==q.system ||
   context.blocks.length || context.instructionFiles.length) throw Error('projection');
const image=JSON.parse(readFileSync(process.argv[4],'utf8'));
let nextCalls=0;
const e={turnId:'synthetic-turn',index:0,model:q.model,effort:'low',messageCount:1};
if(variant==='wrong_model') e.model='other';
if(variant==='wrong_effort') e.effort='high';
if(variant==='step_one') e.index=1;
if(variant==='subagent') e.agentId='other';
if(variant==='wrong_count') e.messageCount=2;
host.session={messages:async()=>[{role:'user',content:[{type:'text',text:
    variant==='injected_context'?'extra':q.prompt}]}]};
if(variant==='blocks_missing')host.session.messages=async()=>[{role:'user',content:[]}];
if(variant==='messages_io_failure')host.session.messages=async()=>{throw Error('synthetic read failure')};
const result={...e,answer:'original result',toolUses:[],stopReason:'end_turn',usage:null};
const next=async()=>{if(next.called)return result;next.called=true;nextCalls++;
 if(variant==='after_next_receipt_failure')failWrite=true;return result};
if(variant==='receipt_failure') failWrite=true;
let answer;
if(variant==='catch_before') {next.called=false;answer=await catches['turn.step'](host,e,next)}
else if(variant==='host_called_without_admission') {next.called=true;answer=await catches['turn.step'](host,e,next)}
else if(variant==='catch_after') {
 writeFileSync(q.receipt_root+'/phase-next-test.json',JSON.stringify({nonce:q.nonce,stage:'next'}));
 next.called=true;nextCalls=1;answer=await catches['turn.step'](host,e,next)
}
else if(variant==='context_catch') {await catches['prompt.context'](host,e,{error:{message:'test'}});answer=await handlers['turn.step'](host,e,next)}
else if(variant==='compose_catch') {await catches['prompt.compose'](host,e,{error:{message:'test'}});answer=await handlers['turn.step'](host,e,next)}
else {
 try {answer=await handlers['turn.step'](host,e,next)}
 catch(err) {next.called=nextCalls>0;answer=await catches['turn.step'](host,e,next)}
}
if(variant==='twice') await handlers['turn.step'](host,e,next);
if(variant==='ready_refresh_after_probe'){
 const original=JSON.parse(readFileSync(q.receipt,'utf8'));original.stages=['ready'];original.next_calls=0;writeFileSync(q.receipt,JSON.stringify(original));
 await Promise.all([handlers['prompt.context'](host),handlers['prompt.compose'](host,{model:q.model,promptModel:q.model,tools:[]})]);
}
console.log(JSON.stringify({nextCalls,answer,system:composed.sections[0].text,context}));
'''


class ModTests(unittest.TestCase):
    def test_reauthorization_accounts_only_the_exact_prior_marker(self):
        from qqbot_gateway.vision_mod_guard import probe_unknown_unresolved,sha
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);base=root/'state/vision-evidence';base.mkdir(parents=True)
            marker=base/'lap42-cli-probe-unknown.json';marker.write_bytes(b'prior consumed attempt')
            grant=dict(schema_version=1,authorization='USER_CONFIRMED_7_TOTAL_WITH_SIX_FIXED_CASES',
                previous_real_requests=1,max_local_real_requests=7,fixed_batch='lap42-vision-closure-v2',
                max_group_generations=2,backend='codebuddy_cli',model='deepseek-v4.1-flash',effort='low',
                prior_marker_sha256=sha(marker.read_bytes()),source='explicit_current_conversation')
            path=base/'lap42-native-authorization.json';path.write_text(json.dumps(grant))
            self.assertFalse(probe_unknown_unresolved(root))
            marker.write_bytes(b'new unexpected generation')
            self.assertTrue(probe_unknown_unresolved(root))
            self.assertEqual(marker.read_bytes(),b'new unexpected generation')

    def test_generation_quarantine_stops_probe_before_async_runner_or_new_journal(self):
        from scripts import probe_lap42_vision_contract as probe
        from types import SimpleNamespace
        from qqbot_gateway.hosted_cli_budget import RUNTIME
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);marker=root/'state/vision-evidence/lap42-cli-probe-unknown.json'
            marker.parent.mkdir(parents=True);marker.write_text('{"state":"generation_observed_completion_unverified"}')
            with patch.object(probe,'ROOT',root),patch.object(sys,'argv',['probe','--run']),\
                 patch('qqbot_gateway.config_files.read_project',return_value=SimpleNamespace(settings=settings())),\
                 patch('qqbot_gateway.vision_capabilities.runtime_identity',return_value=RUNTIME),\
                 patch('qqbot_gateway.vision.binding',return_value='b'*64),\
                 patch.object(probe.asyncio,'run',side_effect=AssertionError('must not invoke runner')):
                with self.assertRaisesRegex(ValueError,'UNRESOLVED_PROBE_GENERATION'):probe.main()
            self.assertFalse((root/'state/lap42-vision-closure').exists())

    def test_quality_flags_without_explicit_human_provenance_cannot_activate(self):
        from qqbot_gateway import vision_capabilities as vc
        s=settings()
        with patch('qqbot_gateway.vision.binding',return_value='b'*64):
            batch=dict(selected_binding='b'*64,max_total_generations=6,fixture_hash='f',cases={})
            for case in vc.CASES:
                batch['cases'][case]=dict(state='scored',attempts=1,quality_passed=True,native_image_verified=True,
                    budget_passed=True,runtime_verified=True,no_truncation=True,no_tools=True)
            evidence=dict(binding='b'*64,record_hash=vc.digest(review_record()),offline_passed=True,
                ingress_decoded=True,batch=batch,fixture_hash='f',unresolved_attempts=False)
            from qqbot_gateway.hosted_cli_budget import RUNTIME
            missing=vc.production_diagnostics(s,evidence,RUNTIME)
            self.assertTrue(all(case+'_HUMAN_REVIEW_MISSING' in missing for case in vc.CASES))
            for case,row in batch['cases'].items():
                row['human_review']=dict(case=case,source='conversation_explicit_feedback',timestamp=1,answer_sha256='a'*64)
            self.assertEqual(vc.production_diagnostics(s,evidence,RUNTIME),[])

    def guard(self,work,mode='probe'):
        system='全项目policy🙂 {{literal}}\r\nnot just persona'
        prompt='Original project memory/member/web context'
        b=blob();terms=final_budget(review_record(),InputBudget.from_settings(settings()),system,prompt,b.width,b.height,model())
        return Guard(work,system,prompt,b,terms,mode=mode)

    def test_manifest_independent_of_static_package_and_request_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            g=self.guard(Path(directory))
            self.assertEqual(g.request['assets_sha256'],assets_signature())
            self.assertNotIn('.codebuddy-plugin/plugin.json',g.request['assets'])
            self.assertNotEqual(g.manifest_hash,assets_signature())
            with self.assertRaises(FileNotFoundError):g.read()
            g.receipt.write_text(json.dumps(dict(stages=['ready'],nonce='wrong')),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'MISMATCH'):g.read()

    def test_current_framework_source_and_model_output_upper(self):
        self.assertGreater(framework_upper(),219)
        terms=final_budget(review_record(),InputBudget.from_settings(settings()),'中🙂','{{literal}}',24,16,model())
        self.assertEqual(terms['T'],len('中🙂{{literal}}'.encode()))
        self.assertEqual((terms['V'],terms['O'],terms['C']),(1024,128000,1000000))

    def test_plugin_projection_refusal_catch_and_single_next(self):
        lock=json.loads((ROOT/'config/versions.lock.json').read_text(encoding='utf-8'))
        import base64
        for mode,variants in [('probe',['normal','ready_refresh_after_probe']),('live',['normal','wrong_model','wrong_effort','step_one',
            'subagent','wrong_count','injected_context','blocks_missing','messages_io_failure','catch_before','catch_after',
            'host_called_without_admission','after_next_receipt_failure','context_catch','compose_catch','receipt_failure','twice'])]:
            for variant in variants:
                with self.subTest(mode=mode,variant=variant),tempfile.TemporaryDirectory() as directory:
                    work=Path(directory);g=self.guard(work,mode)
                    harness=work/'harness.mjs';harness.write_text(HARNESS,encoding='utf-8')
                    image=dict(type='image',source=dict(type='base64',media_type='image/png',data=base64.b64encode(blob().data).decode()))
                    imagepath=work/'image.json';imagepath.write_text(json.dumps(image),encoding='utf-8')
                    result=subprocess.run([lock['node']['path'],str(harness),str(g.root),variant,str(imagepath)],
                        cwd=work,capture_output=True,text=True,encoding='utf-8',timeout=15)
                    self.assertEqual(result.returncode,0,result.stderr)
                    value=json.loads(result.stdout)
                    expected=1 if mode=='live' and variant in ('normal','twice','catch_after','after_next_receipt_failure','context_catch','compose_catch') else 0
                    self.assertEqual(value['nextCalls'],expected)
                    self.assertEqual(value['system'],g.request['system'])
                    self.assertEqual(value['context'],dict(blocks=[],instructionFiles=[]))
                    if variant in ('normal','ready_refresh_after_probe','context_catch','compose_catch'):g.finish()
                    elif variant not in ('catch_after',):
                        with self.assertRaises(ValueError):g.finish()


class ActivationTests(unittest.TestCase):
    def test_activation_order_load_failure_and_stale_candidate(self):
        from scripts import activate_lap42_vision as activate
        from types import SimpleNamespace
        for scenario in ('success','load_failure','stale_candidate','concurrent_features'):
            with self.subTest(scenario=scenario),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);state=root/'state/lap42-vision-closure';state.mkdir(parents=True)
                feature=root/'config/local/features.yaml';feature.parent.mkdir(parents=True)
                original=b'# keep comment\r\nvision:\r\n  enabled: false\r\nother: keep\r\n';feature.write_bytes(original)
                active=root/'state/vision-evidence/active.json'
                evidence=dict(binding='b'*64)
                candidate=dict(binding='b'*64,source_digest='source',semantic_digest='semantic',
                    active_before_sha256=None,evidence=evidence)
                raw=json.dumps(candidate).encode();(state/'candidate.json').write_bytes(raw)
                project=SimpleNamespace(source_digest='source',semantic_digest='semantic',settings={'vision':{'enabled':False}})
                calls=[];atomic=activate.atomic
                def observe_write(path,data):
                    calls.append(Path(path).name)
                    if Path(path)==active and scenario=='concurrent_features':feature.write_bytes(b'concurrent')
                    return atomic(path,data)
                digest=activate.sha(raw) if scenario!='stale_candidate' else '0'*64
                with patch.object(activate,'current',return_value=(project,{},'b'*64)),\
                     patch('qqbot_gateway.vision_capabilities.validate_production_evidence',return_value=({},[])),\
                     patch('qqbot_gateway.vision_capabilities.load_production',return_value=({},['failure'] if scenario=='load_failure' else [])),\
                     patch('qqbot_gateway.config_files.read_project',return_value=SimpleNamespace(settings={'vision':{'enabled':True}})),\
                     patch.object(activate,'atomic',side_effect=observe_write):
                    if scenario=='success':
                        result=activate.activate(root,digest,'b'*64)
                        self.assertTrue(result['vision_enabled'])
                        self.assertLess(calls.index('active.json'),calls.index('features.yaml'))
                        self.assertEqual(feature.read_bytes(),original.replace(b'false',b'true'))
                    else:
                        with self.assertRaises(ValueError):activate.activate(root,digest,'b'*64)
                        self.assertEqual(feature.read_bytes(),b'concurrent' if scenario=='concurrent_features' else original)
                        if scenario in ('load_failure','stale_candidate'):self.assertFalse(active.exists())

    def test_restore_conflict_preserves_both_destinations(self):
        from scripts.activate_lap42_vision import restore,sha
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);backup=root/'state/lap42-vision-closure/activation';backup.mkdir(parents=True)
            feature=root/'config/local/features.yaml';feature.parent.mkdir(parents=True);feature.write_bytes(b'concurrent')
            active=root/'state/vision-evidence/active.json';active.parent.mkdir();active.write_bytes(b'ours')
            (backup/'features.before').write_bytes(b'original')
            transaction=dict(features_before=sha(b'original'),features_after=sha(b'updated'),active_before=None,active_after=sha(b'ours'))
            with self.assertRaisesRegex(ValueError,'OWNERSHIP_CONFLICT'):restore(root,transaction)
            self.assertEqual(feature.read_bytes(),b'concurrent');self.assertEqual(active.read_bytes(),b'ours')

    def test_restore_only_owned_bytes(self):
        from scripts.activate_lap42_vision import restore,sha
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);backup=root/'state/lap42-vision-closure/activation';backup.mkdir(parents=True)
            feature=root/'config/local/features.yaml';feature.parent.mkdir(parents=True);feature.write_bytes(b'updated')
            active=root/'state/vision-evidence/active.json';active.parent.mkdir();active.write_bytes(b'ours')
            (backup/'features.before').write_bytes(b'original')
            transaction=dict(features_before=sha(b'original'),features_after=sha(b'updated'),active_before=None,active_after=sha(b'ours'))
            restore(root,transaction)
            self.assertEqual(feature.read_bytes(),b'original');self.assertFalse(active.exists())


if __name__=='__main__':unittest.main()
