"""Focused hosted units: no remote generation and no local configuration writes."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT)]
from PIL import Image
from qqbot_gateway import vision_capabilities as vc
from qqbot_gateway.hosted_cli_budget import (KIND,RUNTIME,review_record,reviewed,
    effective_capacity,model_terms,known_template_parts,final_budget)
from qqbot_gateway.token_budget import InputBudget
from qqbot_gateway.vision import CURRENT,NativeImage,normalize,text_budget


def settings():
    from test_lap28_capability import settings as base
    value=base();value['llm']['backend']='codebuddy_cli'
    value['llm']['profiles']['codebuddy_cli']['reasoning_effort']='low'
    value['llm']['profiles']['codebuddy_cli']['input_budget']['context_input_limit_tokens']=30000
    return value


def model(**changes):
    return dict(id='deepseek-v4.1-flash',supportsImages=True,maxInputTokens=1000000,
                maxOutputTokens=128000,reasoning=dict(supportedEfforts=['low','high','max']))|changes


def image():
    out=io.BytesIO();Image.new('RGB',(12,8),'red').save(out,format='PNG')
    return NativeImage(normalize(out.getvalue()),4096,time.monotonic()+60,time.monotonic()+15)


class HostedBudgetTests(unittest.TestCase):
    def test_iq_runner_does_not_inherit_outer_configuration_lock(self):
        from scripts import observe_lap28 as observer
        from qqbot_gateway.config import configuration_lock,require_stopped
        from qqbot_gateway.vision_quality import BatchLedger
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);bound='b'*64;batch='lap42-lock-test'
            data=b'synthetic fixture';sha=hashlib.sha256(data).hexdigest()
            spec={'cases':{case:dict(sha256=sha,truth={}) for case in vc.CASES}}
            spec_path=root/'spec.json';spec_path.write_text(json.dumps(spec),encoding='utf-8')
            for case in vc.CASES:(root/(case+'.png')).write_bytes(data)
            ledger=BatchLedger(root/'state/vision-evidence/iq-batches.sqlite3')
            ledger.create(batch,bound,spec,6,'SIX_NATIVE_IMAGE_CALLS')
            acquired=[]
            async def failing_observation(*args):
                with configuration_lock(root):
                    require_stopped(root);acquired.append(True)
                # Stop after the first consumed case, never manufacture a pass.
                raise ValueError('intentional observation failure')
            argv=['observe','--root',str(root),'--backend','codebuddy_cli','--spec',str(spec_path),
                  '--batch-id',batch,'--run-batch','--expected-binding',bound,
                  '--max-total-generations','6','--authorize-native','SIX_NATIVE_IMAGE_CALLS']
            from types import SimpleNamespace
            with patch.object(sys,'argv',argv),patch.object(observer,'runtime_identity',return_value=RUNTIME),\
                 patch.object(observer,'observe',side_effect=failing_observation),\
                 patch('qqbot_gateway.config_files.read_project',return_value=SimpleNamespace(settings=settings())),\
                 patch('qqbot_gateway.vision.binding',return_value=bound),\
                 patch.object(vc,'static_diagnostics',return_value=[]),patch.object(vc,'offline_valid',return_value=True):
                self.assertEqual(observer.main(),1)
            self.assertEqual(acquired,[True])
            snapshot=ledger.snapshot(batch)
            self.assertEqual(set(snapshot['cases']),{'IQ-01'})
            self.assertEqual(snapshot['cases']['IQ-01']['state'],'failed_or_unknown')
            self.assertEqual(snapshot['cases']['IQ-01']['attempts'],1)

    def test_bytes_not_tokens_in_early_fitter_and_iq(self):
        from scripts.observe_lap28 import inputs
        s=settings();budget=InputBudget.from_settings(s)
        self.assertEqual(budget.vision_kind,KIND)
        token=CURRENT.set(image())
        try:
            self.assertIs(text_budget(budget),budget)
            text_budget(budget).check('x'*23895,'')
            self.assertGreater(budget.usage('x'*23895,''),30000-4096)
            system,prompt=inputs(s,budget,'IQ-05')
            self.assertTrue(29872<budget.usage(system,prompt)<=29936)
            # Unrelated local budgets retain their original reserve contract.
            legacy=InputBudget(limit=30000)
            self.assertEqual(text_budget(legacy).limit,25904)
        finally:CURRENT.reset(token)

    def test_current_persona_and_optional_fit_without_body_output(self):
        from qqbot_gateway.config_files import read_project
        from scripts.lap42_rollout import budget_check
        s=copy.deepcopy(read_project(ROOT).settings);s['vision']['enabled']=True
        token=CURRENT.set(image())
        try:
            result=budget_check(ROOT,s)
            self.assertEqual(result['persona_bytes'],19256)
            self.assertEqual(result['limit'],30000)
            self.assertLessEqual(result['final_visible_policy_bytes'],30000)
            self.assertTrue(result['passed'])
        finally:CURRENT.reset(token)

    def test_capacity_exact_default_smallest_and_override_semantics(self):
        self.assertEqual(effective_capacity(model()),1000000)
        self.assertEqual(effective_capacity(model(contextWindow={'default':200000})),1000000)
        for lengths,default,expected in (([200000,1000000],1000000,1000000),
            ([200000,1000000],None,200000),([200000],200000,1000000),
            ([True,-1,200000,1000000,2000000],200000,200000),
            ([200000,1000000],300000,200000)):
            metadata=model(contextWindow=dict(defaultLength=default,supportedLengths=lengths))
            self.assertEqual(effective_capacity(metadata),expected)
        m=model(contextWindow=dict(defaultLength=1000000,supportedLengths=[200000,1000000]))
        self.assertEqual(effective_capacity(m,200000),200000)
        self.assertEqual(effective_capacity(m,300000),1000000)

    def test_selected_output_is_not_project_reserve(self):
        self.assertEqual(model_terms(model(),2048),(1000000,128000))
        for changed in (dict(supportsImages=False),dict(maxOutputTokens=None),dict(maxInputTokens=True),
                        dict(reasoning={}),dict(id='another')):
            with self.subTest(changed=changed),self.assertRaises(ValueError):model_terms(model(**changed),2048)

    def test_review_strict_kind_runtime_and_no_user_eligible_override(self):
        reviewed(review_record())
        for field,value in (('runtime',RUNTIME|dict(node_sha256='0'*64)),
            ('template_contract','passed'),('kind','unknown'),('production_eligible',True)):
            row=review_record();row[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):vc.reviewed(row)
        with self.assertRaisesRegex(ValueError,'UNKNOWN_VISION_RULE_KIND'):vc.reviewed({'kind':'unknown'})

    def test_null_window_is_valid_but_partial_template_never_grants_native(self):
        s=settings();record=review_record()
        with patch('qqbot_gateway.token_budget.known_models',return_value={record['model']:model()}):
            missing=vc.static_diagnostics(s,RUNTIME)
            self.assertEqual(missing,['CLI_POST_OVERRIDE_TEMPLATE_UNBOUNDED'])
            self.assertIn('HOSTED_RUNTIME_MISMATCH',vc.static_diagnostics(s,RUNTIME|dict(version='other')))
        b=InputBudget.from_settings(s)
        with self.assertRaisesRegex(ValueError,'CLI_POST_OVERRIDE_TEMPLATE_UNBOUNDED'):
            final_budget(record,b,'policy','text',12,8,model())
        with self.assertRaisesRegex(ValueError,'FINAL_NATIVE_CAPACITY_EXCEEDED'):
            final_budget(record,b,'policy','text',12,8,model(contextWindow=dict(defaultLength=10000,supportedLengths=[10000,1000000])))

    def test_metadata_whitelist_legacy_and_new_fields_no_secret(self):
        from qqbot_gateway.cli_control import model_metadata
        m=model(contextWindow=dict(default=42,defaultLength=200000,supportedLengths=[True,0,200000,1000000],other='secret'),
            url='secret',apiKey='secret',unknown='secret')
        result=model_metadata(dict(rawModels=[m]))[0]
        self.assertIs(result['supportsImages'],True)
        self.assertEqual(result['contextWindow'],dict(default=42,defaultLength=200000,supportedLengths=[200000,1000000]))
        self.assertNotIn('secret',json.dumps(result))

    def test_report_fixed_path_and_current_binding(self):
        s=settings()
        self.assertEqual(vc.offline_path(s),ROOT/'reports/lap-42-vision-offline.json')
        from test_lap28_capability import settings as legacy
        self.assertEqual(vc.offline_path(legacy()),ROOT/'reports/lap-28-C-offline.json')
        # Wrong record hash cannot grant proof even if "passed" is written.
        with patch.object(vc,'read_json',return_value=dict(passed=True,adapter_signature='old',rule_hash='old')):
            self.assertFalse(vc.offline_valid(s))

    def test_text_byte_bound_and_model_template_from_actual_public_sources(self):
        from qqbot_gateway.hosted_cli_budget import SOURCE_HASHES
        cache=ROOT/'state/lap42-vision-finish/sources'
        for name,expected in SOURCE_HASHES.items():
            self.assertEqual(hashlib.sha256((cache/name.replace('/','_')).read_bytes()).hexdigest(),expected)
        token=json.loads((cache/'tokenizer.json').read_text(encoding='utf-8'))
        self.assertEqual(token['normalizer'],dict(type='Sequence',normalizers=[]))
        self.assertEqual(token['model']['type'],'BPE')
        self.assertIsNone(token['model']['continuing_subword_prefix'])
        self.assertIsNone(token['model']['end_of_word_suffix'])
        self.assertTrue(all(row['content'] for row in token['added_tokens']))
        pre=token['pre_tokenizer']['pretokenizers']
        self.assertTrue(all(p['behavior']=='Isolated' for p in pre[:-1]))
        self.assertEqual(pre[-1],dict(type='ByteLevel',add_prefix_space=False,trim_offsets=True,use_regex=False))
        # ByteLevel's bijection covers all 256 initial byte symbols in vocab.
        bs=list(range(33,127))+list(range(161,173))+list(range(174,256))
        chars=dict(zip(bs,bs));n=0
        for b in range(256):
            if b not in chars:chars[b]=256+n;n+=1
        self.assertTrue(all(chr(c) in token['model']['vocab'] for c in chars.values()))
        audit=json.loads((ROOT/'reports/lap-42-vision-sources.json').read_text(encoding='utf-8'))
        rust=(cache/'tokenizers_byte_level.rs').read_bytes()
        self.assertEqual(hashlib.sha256(rust).hexdigest(),audit['public_resources']['tokenizers/byte_level.rs']['sha256'])
        self.assertIn(b'fn added_tokens(&self, _is_pair: bool) -> usize {\n        0',rust)
        constants={}
        tree=ast.parse((cache/'encoding_encoding.py').read_text(encoding='utf-8'))
        for node in tree.body:
            if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
                try:constants[node.targets[0].id]=ast.literal_eval(node.value)
                except (ValueError,TypeError):pass
            elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name):
                try:constants[node.target.id]=ast.literal_eval(node.value)
                except (ValueError,TypeError):pass
        self.assertIn(constants['REASONING_EFFORT_TEMPLATE'].format(budget=50),known_template_parts())
        for text in ('hello','中文🙂','<think>','<｜System｜>','{"x":"\\n"}','e\u0301','\x00'):
            self.assertGreaterEqual(len(text.encode('utf-8')),len(text))


class HostedRunnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_runner_control_only_zero_user(self):
        from test_cli_runner import RunnerTests
        f=RunnerTests();f.setUp()
        try:
            runner=f.runner(effort='low')
            models=await runner.inspect_models('lap42-control-only')
            self.assertEqual(models[0]['id'],'deepseek-v4.1-flash')
            self.assertEqual(runner.user_messages_sent,0)
            self.assertEqual(runner.control_attempts,1)
            self.assertFalse((f.root/'user.json').exists())
            self.assertFalse(runner.cleanup_status()['blocked'])
        finally:f.tearDown()

    async def test_final_handshake_failure_zero_user(self):
        from test_cli_runner import RunnerTests
        for change in ('complete','unsupported','output_changed','identity_changed'):
            f=RunnerTests();f.setUp()
            try:
                fixture=f.script.read_text(encoding='utf-8')
                metadata=model()
                if change=='unsupported':metadata['supportsImages']=False
                if change=='output_changed':metadata['maxOutputTokens']=64000
                fixture=fixture.replace("models=[{'id':'deepseek-v4.1-flash','maxInputTokens':1000000,'reasoning':{'supportedEfforts':['low','high','max']}}]",'models='+repr([metadata]))
                f.script.write_text(fixture,encoding='utf-8')
                s=settings();runner=f.runner(effort='low',budget=InputBudget.from_settings(s));runner.vision_settings=s
                token=CURRENT.set(image())
                identity=RUNTIME if change!='identity_changed' else RUNTIME|dict(version='changed')
                try:
                    with patch.object(vc,'runtime_identity',return_value=identity),patch('qqbot_gateway.workbuddy_cli_runner.known_models',return_value={metadata['id']:model()}):
                        from qqbot_gateway.errors import GatewayError
                        with self.assertRaises(GatewayError):await runner.run('policy','user','lap42-zero-user')
                    reason={'complete':'CLI_POST_OVERRIDE_TEMPLATE_UNBOUNDED','identity_changed':'HOSTED_RUNTIME_MISMATCH'}.get(change,'HOSTED_CURRENT_CAPABILITIES_CHANGED')
                    self.assertEqual(runner.last_parameters['vision_rejection'],reason)
                    self.assertEqual(runner.control_attempts,1)
                    self.assertEqual(runner.user_messages_sent,0,change)
                    self.assertFalse((f.root/'user.json').exists(),change)
                finally:CURRENT.reset(token)
            finally:f.tearDown()
