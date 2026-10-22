"""I4/I5 proofs use invented records and synthetic fixtures, zero real I/O."""
import asyncio
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1])]
from qqbot_gateway.vision_capabilities import CASES,digest,production_diagnostics,reviewed,visual_upper,final_budget
from qqbot_gateway.vision_quality import BatchLedger,fixtures,score,PROMPTS
from qqbot_gateway.vision import binding,normalize,CURRENT,NativeImage,AUDIT,wire_check,cli_message,native_payload_images
from qqbot_gateway.token_budget import InputBudget


def settings():
    import yaml
    from qqbot_gateway.config import normalize_settings
    root=Path(__file__).resolve().parents[1]
    value=yaml.safe_load((root/'config/settings.example.yaml').read_text(encoding='utf-8'))
    value['bot']['qq']='222';value['access'].update(allowed_groups=['111'],admin_users=['333'])
    value['llm']['backend']='ollama_ssh'
    value['llm']['profiles']['ollama_ssh']['expected_digest']='a'*64
    value['llm']['profiles']['ollama_ssh']['input_budget']['context_input_limit_tokens']=12000
    return normalize_settings(value)


def record():
    return dict(backend='ollama_ssh',model='qwen3.5:9b-q4_K_M',vision_supported=True,
        runtime=dict(version='synthetic-v1',model_digest='a'*64,platform='Windows',architecture='NVIDIA-GGUF',
            processor='synthetic-processor',projector='synthetic-projector',runner_path='synthetic',artifact_sha256='b'*64),
        bounds=dict(visual_max_tokens=2048,image_marker_tokens=16,template_max_tokens=128,text_tokens_per_byte=1,
            native_window=16384,max_width=1024,max_height=1024,max_pixels=1000000,max_images=1),
        sources={k:dict(url='https://example.invalid/review',sha256='c'*64,symbol='synthetic',applicability='TEST ONLY')
                 for k in ('vision','runtime_path','visual','template','text_conversion','window')})


def evidence(s,r):
    bound=binding(s,r['runtime'])
    return dict(binding=bound,record_hash=digest(r),offline_passed=True,ingress_decoded=True,fixture_hash='f'*64,
        unresolved_attempts=False,batch=dict(batch_id='synthetic-batch',selected_binding=bound,max_total_generations=6,
            fixture_hash='f'*64,cases={k:dict(state='scored',attempts=1,quality_passed=True,native_image_verified=True,
                budget_passed=True,runtime_verified=True,no_truncation=True,no_tools=True) for k in CASES}))


class CapabilityTests(unittest.TestCase):
    def test_startup_reads_fixed_ledger_ingress_and_offline_proofs(self):
        import qqbot_gateway.vision_capabilities as vc
        from qqbot_gateway.vision import require_production,adapter_signature
        from qqbot_gateway.vision_ingress import inspect_event
        s=settings();r=record();bound=binding(s,r['runtime'])
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'state/vision-evidence';folder.mkdir(parents=True)
            (root/'reports').mkdir()
            spec={'cases':{case:{'sha256':case} for case in CASES}}
            ledger=BatchLedger(folder/'iq-batches.sqlite3')
            ledger.create('test-batch-01',bound,spec,6,'SIX_NATIVE_IMAGE_CALLS')
            e=evidence(s,r)
            for case in CASES:
                ledger.reserve('test-batch-01',case,bound,case)
                ledger.finish('test-batch-01',case,e['batch']['cases'][case])
            e['batch']=ledger.snapshot('test-batch-01');e['fixture_hash']=digest(spec)
            e['runtime']=r['runtime'];e['ingress_instance']='d'*32
            row=inspect_event({'message':[{'type':'image','data':{'url':'https://gchat.qpic.cn/synthetic'}}]})
            row.update(stage='decoded',bytes=100,normalized_bytes=90,normalized_dimensions=[10,10])
            row['attempt_counts']['download']=1
            (folder/('d'*32+'.json')).write_text(json.dumps(dict(state='observed',record=row)),encoding='utf-8')
            (folder/'active.json').write_text(json.dumps(e),encoding='utf-8')
            (root/'reports/lap-28-C-offline.json').write_text(json.dumps(dict(passed=True,adapter_signature=adapter_signature())),encoding='utf-8')
            s['vision']['enabled']=True
            with patch.object(vc,'ROOT',root),patch.object(vc,'registry',return_value={'records':[r]}):
                self.assertTrue(require_production(s,root=root))
                ledger.create('test-batch-02',bound,spec,6,'SIX_NATIVE_IMAGE_CALLS')
                ledger.reserve('test-batch-02','IQ-01',bound,'IQ-01')
                with self.assertRaisesRegex(ValueError,'FAILED_OR_UNKNOWN'):require_production(s,root=root)
                # A handwritten eligible flag cannot clear durable unknown.
                e['production_eligible']=True
                (folder/'active.json').write_text(json.dumps(e),encoding='utf-8')
                with self.assertRaises(ValueError):require_production(s,root=root)

    def test_all_conjuncts_positive_and_each_missing(self):
        s=settings();r=record();e=evidence(s,r);table={'records':[r]}
        self.assertEqual(production_diagnostics(s,e,r['runtime'],table=table),[])
        for field in ('offline_passed','ingress_decoded','unresolved_attempts','binding','record_hash'):
            bad=copy.deepcopy(e);bad[field]=True if field=='unresolved_attempts' else False
            self.assertTrue(production_diagnostics(s,bad,r['runtime'],table=table),field)
        for case in CASES:
            for field in ('state','attempts','quality_passed','native_image_verified','budget_passed','runtime_verified','no_truncation','no_tools'):
                bad=copy.deepcopy(e);bad['batch']['cases'][case][field]=False
                self.assertTrue(production_diagnostics(s,bad,r['runtime'],table=table),(case,field))
        self.assertTrue(production_diagnostics(s,e,r['runtime']|{'platform':'Mac MLX'},table=table))
        self.assertTrue(production_diagnostics(s,e,r['runtime'],table={'records':[]}))

    def test_review_budget_domain_and_unsupported(self):
        r=record();s=settings();e=evidence(s,r)
        self.assertEqual(visual_upper(r,1,1024),2064)
        for dims in ((1025,1),(1001,1000),(True,8),(0,1)):
            with self.assertRaises(ValueError):visual_upper(r,*dims)
        for key in ('visual','template','runtime_path','text_conversion'):
            bad=copy.deepcopy(r);del bad['sources'][key]
            with self.assertRaises(ValueError):reviewed(bad)
        s['vision']['input_reserve_tokens']=1
        self.assertIn('VISUAL_RESERVE_INSUFFICIENT',production_diagnostics(s,e,r['runtime'],table={'records':[r]}))
        r['vision_supported']=False
        self.assertIn('SELECTED_MODEL_VISION_UNSUPPORTED',production_diagnostics(s,e,r['runtime'],table={'records':[r]}))
        final_budget(record(),InputBudget(limit=12000,window=16384,output=1024),'sys','text',1000,1000)
        with self.assertRaises(ValueError):final_budget(record(),InputBudget(limit=16000,window=16384,output=1024),'s'*14000,'text',1000,1000)

    def test_default_registry_cannot_be_activated_and_bindings_change(self):
        from qqbot_gateway.vision import require_production
        s=settings();self.assertFalse(require_production(s))
        s['vision']['enabled']=True
        with self.assertRaises(ValueError):require_production(s)
        s=settings();key=binding(s,{})
        s['public_network']['resolver']='cloudflare_doh'
        self.assertNotEqual(binding(s,{}),key)


class BatchTests(unittest.TestCase):
    def test_geometry_transparency_and_known_unsupported_has_zero_generation(self):
        from PIL import Image
        from scripts.observe_lap28 import observe
        from unittest.mock import AsyncMock
        for size in ((1024,1),(1,1024),(1023,977),(1001,1000),(2000,501)):
            raw=io.BytesIO();Image.new('RGBA',size,(255,0,0,0)).save(raw,format='PNG')
            blob=normalize(raw.getvalue())
            self.assertLessEqual(blob.width*blob.height,1000000)
            self.assertLessEqual(max(blob.width,blob.height),1024)
            with Image.open(io.BytesIO(blob.data)) as image:self.assertEqual(image.getpixel((0,0)),(255,255,255))
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'fixtures';spec=fixtures(folder);s=settings()
            runner=type('SyntheticRunner',(),{})()
            runner.preflight=AsyncMock(return_value={'vision_supported':False})
            runner.run=AsyncMock();runner.cleanup_close=AsyncMock()
            from qqbot_gateway.vision_capabilities import runtime_identity
            bound=binding(s,runtime_identity(Path(temp),s))
            with patch('qqbot_gateway.backends.create_runner',return_value=runner):
                with self.assertRaisesRegex(ValueError,'SELECTED_MODEL_VISION_UNSUPPORTED'):
                    asyncio.run(observe(Path(temp),s,folder/'IQ-01.png','IQ-01',spec['cases']['IQ-01']['truth'],bound,
                        lambda text: {},spec['cases']['IQ-01']['sha256']))
            runner.run.assert_not_called();runner.cleanup_close.assert_awaited_once()

    def test_atomic_duplicate_total_failed_cancelled_unknown_and_new_trace(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger=BatchLedger(Path(temp)/'ledger.sqlite3')
            spec={'cases':{k:{'sha256':k} for k in CASES}}
            ledger.create('batch-0001','binding',spec,6,'SIX_NATIVE_IMAGE_CALLS')
            def attempt(i):
                try:ledger.reserve('batch-0001','IQ-01','binding','IQ-01');return True
                except ValueError:return False
            with ThreadPoolExecutor(max_workers=8) as pool:self.assertEqual(sum(pool.map(attempt,range(8))),1)
            # Restart and different trace cannot claim the same case again.
            again=BatchLedger(Path(temp)/'ledger.sqlite3')
            for state in ('failed_or_unknown','cancelled','unknown'):
                with self.assertRaises(ValueError):again.reserve('batch-0001','IQ-01','binding','IQ-01')
            ledger.finish('batch-0001','IQ-01',dict(state='failed_or_unknown'))
            self.assertTrue(ledger.unresolved('binding'))
            for case in CASES[1:]:ledger.reserve('batch-0001',case,'binding',case)
            with self.assertRaises(ValueError):ledger.reserve('batch-0001','IQ-06','binding','IQ-06')
            with self.assertRaises(ValueError):ledger.create('batch-0001','binding',spec,6,'SIX_NATIVE_IMAGE_CALLS')
            with self.assertRaises(ValueError):ledger.create('batch-0002','binding',spec,6,'')
            ledger.create('batch-0002','binding',spec,6,'SIX_NATIVE_IMAGE_CALLS')
            self.assertTrue(ledger.unresolved('binding'))
            self.assertEqual(len(ledger.snapshot('batch-0001')['cases']),6)

    def test_fixture_truth_separation_hash_scoring_and_final_native_payloads(self):
        from scripts.observe_lap28 import inputs
        with tempfile.TemporaryDirectory() as temp:
            spec=fixtures(Path(temp)/'fixtures')
            self.assertEqual(set(spec['cases']),set(CASES))
            self.assertNotEqual(spec['cases']['IQ-02']['sha256'],spec['cases']['IQ-04']['sha256'])
            for case in CASES:
                raw=(Path(temp)/'fixtures'/(case+'.png')).read_bytes()
                blob=normalize(raw);self.assertEqual(hashlib.sha256(raw).hexdigest(),spec['cases'][case]['sha256'])
                metrics={};token=CURRENT.set(NativeImage(blob,4096,time.monotonic()+60,time.monotonic()+15));a=AUDIT.set(metrics)
                try:
                    budget=InputBudget(limit=12288,window=16384,output=1024)
                    system,prompt=inputs(settings(),budget,case)
                    if case=='IQ-05':
                        self.assertGreaterEqual(blob.width*blob.height,990000)
                        self.assertLess(12288-4096-(budget.usage(system,prompt)),128)
                    # Dynamic six-character truth never appears in either final prompt.
                    for value in spec['cases'][case]['truth'].values():
                        if isinstance(value,str) and len(value)==6 and value not in ('center',):self.assertNotIn(value,system+prompt)
                    wire_check(dict(system=system,input=cli_message(prompt)))
                    self.assertTrue(metrics['native_image_verified']);self.assertEqual(metrics['native_image_count'],1)
                    wire_check(native_payload_images(dict(messages=[dict(role='system',content=system),dict(role='user',content=prompt)])))
                    self.assertEqual(metrics['normalized_sha256'],blob.sha256)
                    human={k:True for k in ('no_hallucination','visible_facts_correct','injection_safe')}
                    self.assertTrue(score(case,json.dumps(spec['cases'][case]['truth']),spec['cases'][case]['truth'],human)['quality_passed'])
                    self.assertFalse(score(case,'I see '+str(spec['cases'][case]['truth']),spec['cases'][case]['truth'],human)['quality_passed'])
                    self.assertFalse(score(case,json.dumps(spec['cases'][case]['truth']),spec['cases'][case]['truth'],{})['quality_passed'])
                finally:AUDIT.reset(a);CURRENT.reset(token)


if __name__=='__main__':unittest.main()
