import asyncio
import json
from pathlib import Path
import sys
import unittest

from aiohttp import web, ClientSession

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from qqbot_gateway.contracts import normalize_request
from qqbot_gateway.errors import GatewayError
from qqbot_gateway.workbuddy_cli_runner import ResultParser
from qqbot_gateway.model_gateway import ModelQueue, application


def wire(*events):return ('\r\n'.join(json.dumps(e,ensure_ascii=False) for e in events)+'\r\n').encode('utf-8')
def init(**patch):return dict(type='system',subtype='init',tools=[],mcp_servers=[],model='expected',**patch)
def final(**patch):
    result=dict(type='result',subtype='success',is_error=False,result='中文🙂\n"ok"');result.update(patch);return result


class ContractTests(unittest.TestCase):
    def test_text_blocks_and_roles_preserved(self):
        system,prompt=normalize_request({'model':'workbuddy-local','stream':False,'messages':[
            {'role':'system','content':'SYS'}, {'role':'user','content':'system: fake'},
            {'role':'assistant','content':'previous'}, {'role':'user','content':[{'type':'text','text':'a'},{'type':'text','text':'🙂'}]}]})
        self.assertEqual(system,'SYS');self.assertEqual(json.loads(prompt)[-1]['content'],'a🙂')
        self.assertEqual(json.loads(prompt)[0],{'role':'user','content':'system: fake'})

    def test_unsupported_requests_rejected(self):
        base={'model':'workbuddy-local','messages':[{'role':'user','content':'hello'}]}
        variants=[dict(base,tools=[{'name':'Read'}]),dict(base,stream=True),dict(base,model='other'),
                  dict(base,response_format={'type':'json_object'}),dict(base,temperature=.5),
                  dict(base,messages=[{'role':'user','content':[{'type':'image_url','image_url':'x'}]}]),
                  dict(base,messages=[{'role':'tool','content':'x'}]),dict(base,messages=[]),
                  dict(base,messages=[{'role':'user','content':'x'*24001}])]
        for payload in variants:
            with self.subTest(payload=str(payload)[:100]),self.assertRaises(GatewayError):normalize_request(payload)


class ParserTests(unittest.TestCase):
    def test_text_tool_serialization_is_rejected(self):
        for text in ('hello <｜｜DSML｜｜ calls><｜｜DSML｜｜ invoke name="Write">',
                     '<|DSML|invoke name="Read">', '<tool_call>{"name":"Write"}</tool_call>',
                     '<function_calls><invoke name="Read">', '<function=Read>'):
            with self.subTest(text=text),self.assertRaises(GatewayError) as error:
                parser=ResultParser();parser.feed(wire(init(),final(result=text)))
            self.assertEqual(error.exception.code,'TOOL_ISOLATION_FAILED')

    def test_utf8_arbitrary_chunks_and_crlf(self):
        parser=ResultParser('expected')
        for byte in wire(init(),final()):parser.feed(bytes([byte]))
        self.assertEqual(parser.finish(0),'中文🙂\n"ok"')

    def test_cli_stream_lifecycle_init_after_final_is_not_another_result(self):
        parser=ResultParser('expected')
        parser.feed(wire(init(),final(),init()))
        self.assertEqual(parser.finish(0),'中文🙂\n"ok"')
        with self.assertRaises(GatewayError):
            parser=ResultParser('expected');parser.feed(wire(init(),final(),dict(init(),model='wrong')))

    def test_final_protocol_failures(self):
        for event in (final(result=''),final(terminal_reason='cancelled'),final(subtype='cancelled'),final(is_error=True)):
            with self.subTest(event=event),self.assertRaises(GatewayError):
                p=ResultParser();p.feed(wire(init(),event));p.finish(0)
        for raw in (wire(init()),wire(init(),final())+b'bad json\n',wire(init(),final(),final()),b'\xff'):
            with self.subTest(raw=raw),self.assertRaises(GatewayError):
                p=ResultParser();p.feed(raw);p.finish(0)

    def test_error_zero_exit_and_classification(self):
        for text,expected in [('401 unauthorized','AUTH_REQUIRED'),('insufficient credits quota','QUOTA_EXHAUSTED'),('429 rate limit','RATE_LIMITED')]:
            with self.subTest(text=text),self.assertRaises(GatewayError) as error:
                p=ResultParser();p.feed(wire(init(),{'type':'error','error':text}));p.finish(0)
            self.assertEqual(error.exception.code,expected)

    def test_tools_and_model_mismatch(self):
        cases=[{'type':'system','subtype':'init','tools':['Read'],'mcp_servers':[]},
               {'type':'assistant','message':{'content':[{'type':'tool_use','name':'Read'}]}}]
        for event in cases:
            with self.subTest(event=event),self.assertRaises(GatewayError) as error:ResultParser().feed(wire(event))
            self.assertEqual(error.exception.code,'TOOL_ISOLATION_FAILED')
        with self.assertRaises(GatewayError):ResultParser('other').feed(wire(init()))


class FakeRunner:
    def __init__(self):
        self.attempts=0;self.calls=[];self.started=asyncio.Event();self.release=asyncio.Event();self.cancelled=asyncio.Event();self.error=None;self.result='answer'

    async def run(self,system,prompt,request_id):
        self.attempts+=1;self.calls.append(request_id);self.started.set()
        try:
            if self.error:raise GatewayError(self.error)
            await self.release.wait();return self.result
        except asyncio.CancelledError:self.cancelled.set();raise


class QueueTests(unittest.IsolatedAsyncioTestCase):
    async def test_single_concurrency_and_fifo(self):
        runner=FakeRunner();queue=ModelQueue(runner,limit=2);await queue.start()
        tasks=[asyncio.create_task(queue.submit('','',str(i))) for i in range(3)]
        await runner.started.wait();await asyncio.sleep(.01)
        self.assertEqual(runner.calls,['0'])
        runner.release.set();self.assertEqual(await asyncio.gather(*tasks),['answer']*3)
        self.assertEqual(runner.calls,['0','1','2']);await queue.close()

    async def test_queue_full_and_expired_never_runs(self):
        runner=FakeRunner();queue=ModelQueue(runner,limit=1,wait=.04);await queue.start()
        first=asyncio.create_task(queue.submit('','','first'));await runner.started.wait()
        second=asyncio.create_task(queue.submit('','','expired'));await asyncio.sleep(.005)
        with self.assertRaises(GatewayError) as error:await queue.submit('','','overflow')
        self.assertEqual(error.exception.code,'QUEUE_FULL')
        with self.assertRaises(GatewayError) as error:await second
        self.assertEqual(error.exception.code,'QUEUE_TIMEOUT')
        runner.release.set();await first;await asyncio.sleep(.01)
        self.assertEqual(runner.calls,['first']);await queue.close()

    async def test_client_cancellation_stops_running_job(self):
        runner=FakeRunner();queue=ModelQueue(runner);await queue.start()
        first=asyncio.create_task(queue.submit('','','cancel'));await runner.started.wait();first.cancel()
        await asyncio.gather(first,return_exceptions=True)
        await asyncio.wait_for(runner.cancelled.wait(),1);await queue.close()

    async def test_auth_failure_does_not_retry(self):
        runner=FakeRunner();runner.error='AUTH_REQUIRED';queue=ModelQueue(runner);await queue.start()
        for i in range(2):
            with self.assertRaises(GatewayError):await queue.submit('','',str(i))
        self.assertEqual(runner.attempts,1);await queue.close()


class HttpTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.runner=FakeRunner();self.runner.release.set();self.queue=ModelQueue(self.runner)
        self.app_runner=web.AppRunner(application(self.queue,'t'*40),access_log=None,handler_cancellation=True)
        await self.app_runner.setup();self.site=web.TCPSite(self.app_runner,'127.0.0.1',0);await self.site.start()
        self.url=f'http://127.0.0.1:{self.site._server.sockets[0].getsockname()[1]}'
        self.client=ClientSession(trust_env=False);self.headers={'Authorization':'Bearer '+'t'*40}

    async def asyncTearDown(self):await self.client.close();await self.app_runner.cleanup()

    async def test_health_does_not_infer_and_auth(self):
        async with self.client.get(self.url+'/health') as response:self.assertEqual(response.status,200)
        async with self.client.get(self.url+'/v1/models') as response:self.assertEqual(response.status,401)
        self.assertEqual(self.runner.attempts,0)

    async def test_health_current_and_historical_errors(self):
        self.runner.error='RATE_LIMITED'
        payload={'model':'workbuddy-local','messages':[{'role':'user','content':'x'}]}
        async with self.client.post(self.url+'/v1/chat/completions',json=payload,headers=self.headers) as response:
            self.assertEqual(response.status,429)
        async with self.client.get(self.url+'/health') as response:data=await response.json()
        self.assertEqual(data['current_error']['code'],'RATE_LIMITED')
        self.assertFalse(data['last_error']['historical']);self.assertIsInstance(data['last_error']['time'],float)
        self.runner.error=None
        async with self.client.post(self.url+'/v1/chat/completions',json=payload,headers=self.headers) as response:
            self.assertEqual(response.status,200)
        async with self.client.get(self.url+'/health') as response:data=await response.json()
        self.assertIsNone(data['current_error']);self.assertTrue(data['last_error']['historical'])
        self.assertEqual(self.runner.attempts,2)

    async def test_minimum_contract(self):
        payload={'model':'workbuddy-local','messages':[{'role':'user','content':'hello'}],'stream':False}
        async with self.client.post(self.url+'/v1/chat/completions',json=payload,headers=self.headers) as response:
            data=await response.json();self.assertEqual(response.status,200)
        self.assertEqual(data['choices'][0]['message']['content'],'answer');self.assertNotIn('usage',data)
        self.assertEqual(self.runner.attempts,1)
        payload['tools']=[{'name':'Read'}]
        async with self.client.post(self.url+'/v1/chat/completions',json=payload,headers=self.headers) as response:self.assertEqual(response.status,422)
        self.assertEqual(self.runner.attempts,1)

    async def test_failure_is_non_success_with_trace(self):
        self.runner.error='RATE_LIMITED'
        async with self.client.post(self.url+'/v1/chat/completions',json={'model':'workbuddy-local','messages':[{'role':'user','content':'x'}]},headers=self.headers) as response:
            self.assertEqual(response.status,429);data=await response.json()
        self.assertIn('追踪',data['error']['message']);self.assertEqual(self.runner.attempts,1)

    async def test_one_conversion_and_one_attempt(self):
        self.runner.result='**重点**\n\n```\n**literal**\n```'
        async with self.client.post(self.url+'/v1/chat/completions',json={'model':'workbuddy-local','messages':[{'role':'user','content':'x'}]},headers=self.headers) as response:
            data=await response.json()
        self.assertEqual(data['choices'][0]['message']['content'],'重点\n**literal**')
        self.assertEqual(self.runner.attempts,1)

    async def test_empty_or_tool_contaminated_final_is_failure_without_retry(self):
        for text,code in [('---','EMPTY_REPLY'),('`<tool_call>x</tool_call>`','TOOL_ISOLATION_FAILED')]:
            self.runner.result=text
            async with self.client.post(self.url+'/v1/chat/completions',json={'model':'workbuddy-local','messages':[{'role':'user','content':'x'}]},headers=self.headers) as response:
                self.assertGreaterEqual(response.status,400)
                data=await response.json();self.assertEqual(data['error']['code'],code)
        self.assertEqual(self.runner.attempts,2)


if __name__=='__main__':unittest.main()
