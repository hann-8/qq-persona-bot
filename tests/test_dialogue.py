"""Small synthetic checks for stage boundaries, provenance and shared time."""
import asyncio
import json
import time
import unittest
from copy import deepcopy
from unittest.mock import patch

from qqbot_gateway.backends import BackendResult
from qqbot_gateway.dialogue import effective_mode
from qqbot_gateway.errors import GatewayError
from qqbot_gateway.reply_plan import DEFAULTS
from qqbot_gateway.token_budget import InputBudget
from qqbot_gateway.vision import CURRENT,member_source
from qqbot_gateway.web_retrieval import WebRunner


def planned(**kw):
    return dict(qqbot_dialogue_plan=1,decision='speak',kind='chat',response_to_seq=1,
                reply_reference='接住上一句的玩笑，不追加建议。',meme_id=None,mention=None,
                memory_updates={'group':['这是一条由Planner决定的记忆']},memory_receipt=True)|kw


class Runner:
    timeout=180
    thinking_enabled=True
    native_web=True
    async def run(self,system,prompt,request_id,**options):
        self.calls.append(dict(system=system,prompt=prompt,request_id=request_id,image=CURRENT.get(),**options))
        await asyncio.sleep(0)
        result=self.results.pop(0)
        if isinstance(result,Exception):raise result
        return result
    def __init__(self,*results):self.results=list(results);self.calls=[]


class DialogueTests(unittest.IsolatedAsyncioTestCase):
    def setup_turn(self,*results,must=True):
        self.runner=Runner(*results)
        self.owner=WebRunner(self.runner,None,InputBudget(limit=524288),dict(DEFAULTS,max_reply_chars=4000))
        self.owner.dialogue_mode='planner_replyer';self.owner.replyer_reserve_seconds=30
        self.owner.dialogue_character='蓝色大肥鱼，聪明、懒散、嘴硬心软。'
        self.source=member_source('那刚才这张图呢？',['鱼鱼'])
        self.request=dict(version=2,must_reply=must,target_seq=1)
        self.prompt=json.dumps([dict(role='user',content=json.dumps(self.source,ensure_ascii=False))])
    async def execute(self):
        return await self.owner.run_v2('Planner policy',self.prompt,'same-task',self.request)
    async def test_speak_frozen_chat_capabilities_usage_and_deadline(self):
        self.setup_turn(BackendResult(json.dumps(planned()),{'input_tokens':8,'output_tokens':3}),
                        BackendResult('{"bubbles":["还是刚才那只鱼呀"],"memory_updates":{"new_2":"不可扩权"}}',{'input_tokens':5,'output_tokens':7}))
        before=deepcopy(self.source)
        # The enclosing path checks image preparation; keep that existing check satisfied.
        import io
        from PIL import Image
        from qqbot_gateway.vision import NativeImage,normalize
        data=io.BytesIO();Image.new('RGB',(24,16),'red').save(data,format='PNG')
        image=NativeImage(normalize(data.getvalue()),4096,time.monotonic()+60,time.monotonic()+60)
        token=CURRENT.set(image)
        try:result=await self.execute();self.assertIs(CURRENT.get(),image)
        finally:CURRENT.reset(token)
        first,second=self.runner.calls
        self.assertEqual([c['phase'] for c in self.runner.calls],['planner','replyer'])
        self.assertIs(first['image'],image);self.assertIsNone(second['image'])
        self.assertEqual(first['request_id'],second['request_id'])
        self.assertAlmostEqual(second['deadline']-first['deadline'],30,places=5)
        body=json.loads(json.loads(second['prompt'])[-1]['content'])
        self.assertEqual(body['messages'],before['messages']);self.assertEqual(self.source,before)
        self.assertNotIn('memory',body);self.assertIn('reply_reference',body)
        wire=json.loads(result.text)
        self.assertEqual(wire['memory_updates'],planned()['memory_updates'])
        self.assertEqual(result.usage,{'input_tokens':13,'output_tokens':10})
        self.assertEqual(result.parameters['generation_stages'],2)
        self.assertEqual(self.runner.timeout,180);self.assertTrue(self.runner.thinking_enabled)
    async def test_silent_one_stage_and_direct_cannot_silence(self):
        for must in (False,True):
            with self.subTest(must=must):
                self.setup_turn(BackendResult(json.dumps(planned(decision='silent',reply_reference=''))),must=must)
                result=await self.execute()
                self.assertEqual(len(self.runner.calls),1)
                if must:self.assertIsNotNone(result.prepared_plan);self.assertEqual(result.memory_aux,{})
                else:self.assertEqual(json.loads(result.text)['decision'],'silent')
    async def test_web_uses_planner_receipt_and_normalizes_answer(self):
        proof=dict(calls=1,urls=['https://example.com/page'],result_bytes=100,sha256='a'*64)
        self.setup_turn(BackendResult(json.dumps(planned()),parameters={'native_web':proof}),
                        BackendResult('{"bubbles":["事实 https://example.com/page"]}',parameters={'native_web':{'calls':0}}))
        result=await self.execute()
        self.assertEqual(result.prepared_plan.kind,'answer');self.assertEqual(result.web_evidence[0]['tool_calls'],1)
        self.assertEqual(result.parameters['generation_stages'],2)
        self.setup_turn(BackendResult(json.dumps(planned()),{'input_tokens':4},parameters={'native_web':proof}),
                        BackendResult('{"bubbles":["https://other.example.com/page"]}',{'input_tokens':5}))
        rejected=await self.execute()
        self.assertEqual(rejected.usage['input_tokens'],9);self.assertEqual(rejected.memory_aux,{})
        self.assertNotIn('other.example',rejected.text)
    async def test_failed_expression_cannot_leak_plan_or_write_memory(self):
        self.setup_turn(BackendResult(json.dumps(planned())),BackendResult('{"bubbles":['))
        result=await self.execute()
        self.assertIsNotNone(result.prepared_plan);self.assertEqual(result.memory_aux,{})
        self.assertNotIn('reply_reference',result.text);self.assertEqual(len(self.runner.calls),2)
        from qqbot_gateway.group_protocol import group_plan
        for raw in (json.dumps(planned()),'broken "qqbot_dialogue_plan":1 reply_reference'):
            decision,reply=group_plan(raw,DEFAULTS,'',True)
            self.assertEqual(decision,'error');self.assertNotIn('reply_reference',reply.canonical_text)
    async def test_cancel_cleans_stage_context_without_third_call(self):
        self.setup_turn(BackendResult(json.dumps(planned())),asyncio.CancelledError())
        # CancelledError derives directly from BaseException.
        original=self.runner.run
        async def run(*args,**kw):
            if kw['phase']=='replyer':raise asyncio.CancelledError()
            return await original(*args,**kw)
        self.runner.run=run
        with self.assertRaises(asyncio.CancelledError):await self.execute()
        self.assertIsNone(CURRENT.get());self.assertEqual(len(self.runner.calls),1)
    async def test_single_ollama_and_legacy_keep_single(self):
        settings=dict(llm={'backend':'codebuddy_cli'},chat={'dialogue_mode':'planner_replyer'},memory={'enabled':True})
        self.assertEqual(effective_mode(settings),'planner_replyer')
        self.assertEqual(effective_mode(settings|{'llm':{'backend':'ollama_ssh'}}),'single')
        self.assertEqual(effective_mode(settings|{'memory':{'enabled':False}}),'single')
        self.setup_turn(BackendResult('unchanged'));self.owner.dialogue_mode='single';self.runner.native_web=False
        self.source['web_anchor']=None;self.prompt=json.dumps([dict(role='user',content=json.dumps(self.source))])
        self.assertEqual((await self.execute()).text,'unchanged');self.assertEqual(len(self.runner.calls),1)
    async def test_no_expression_after_total_deadline(self):
        self.setup_turn(BackendResult(json.dumps(planned())))
        from types import SimpleNamespace
        from unittest.mock import Mock
        with patch('qqbot_gateway.dialogue.time',SimpleNamespace(monotonic=Mock(side_effect=[0,0,181,181]))):
            with self.assertRaises(GatewayError) as error:await self.execute()
        self.assertEqual(error.exception.code,'MODEL_TIMEOUT');self.assertEqual(len(self.runner.calls),1)
    def test_configuration_defaults_and_reserve(self):
        from test_config import fixture
        from qqbot_gateway.config import normalize_settings
        data=normalize_settings(fixture())
        self.assertEqual(data['chat']['dialogue_mode'],'single');self.assertEqual(data['chat']['replyer_reserve_seconds'],30)
        for reserve in (0,True,180):
            candidate=deepcopy(data);candidate['chat'].update(dialogue_mode='planner_replyer',replyer_reserve_seconds=reserve)
            with self.subTest(reserve=reserve),self.assertRaises(ValueError):normalize_settings(candidate)


if __name__=='__main__':unittest.main()
