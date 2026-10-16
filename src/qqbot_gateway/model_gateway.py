import argparse
import asyncio
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import secrets
import time
import uuid
import psutil

from aiohttp import web
from .config import load_settings

from .contracts import normalize_request, contract_shape
from .errors import GatewayError, MESSAGES
from .workbuddy_cli_runner import CLIRunner
from .token_budget import InputBudget, validate_model_settings
from .chat_text import prepare_reply

LOG = logging.getLogger(__name__)
TRACE = web.RequestKey('qqbot_trace',str)


@dataclass
class Job:
    system: str
    prompt: str
    request_id: str
    deadline: float
    future: asyncio.Future
    started: asyncio.Event = field(default_factory=asyncio.Event)
    cancelled: asyncio.Event = field(default_factory=asyncio.Event)


class ModelQueue:
    def __init__(self,runner,limit=5,wait=30):
        if type(limit) is not int or limit<0 or wait<=0:raise ValueError('Bounded queue configuration required')
        self.runner=runner
        self.limit=limit
        self.queue=asyncio.Queue(maxsize=limit+1)
        self.wait=wait
        self.worker=None
        self.active=False
        self.state='not_probed'
        self.last_success=None
        self.last_shape=None
        self.last_error=None

    async def start(self):
        self.worker=asyncio.create_task(self._work())

    async def close(self):
        self.worker.cancel()
        await asyncio.gather(self.worker,return_exceptions=True)
        while not self.queue.empty():
            job=self.queue.get_nowait()
            if not job.future.done():job.future.set_exception(GatewayError('BACKEND_UNAVAILABLE'))

    async def submit(self,system,prompt,request_id):
        if self.state in ('AUTH_REQUIRED','QUOTA_EXHAUSTED','CLEANUP_FAILED'):
            raise GatewayError(self.state)
        if self.queue.qsize()>=self.limit+(0 if self.active else 1):raise GatewayError('QUEUE_FULL')
        job=Job(system,prompt,request_id,time.monotonic()+self.wait,asyncio.get_running_loop().create_future())
        try:self.queue.put_nowait(job)
        except asyncio.QueueFull:raise GatewayError('QUEUE_FULL') from None
        try:
            try:await asyncio.wait_for(job.started.wait(),timeout=self.wait)
            except TimeoutError:raise GatewayError('QUEUE_TIMEOUT') from None
            return await asyncio.shield(job.future)
        finally:
            if not job.future.done():
                job.cancelled.set();job.future.cancel()
            elif not job.future.cancelled():
                job.future.exception()  # Consume exceptions even on a queue timeout race.

    async def _work(self):
        while True:
            job=await self.queue.get()
            job.started.set()
            if job.future.cancelled() or job.cancelled.is_set():continue
            if time.monotonic()>job.deadline:
                job.future.set_exception(GatewayError('QUEUE_TIMEOUT'));continue
            if self.state in ('AUTH_REQUIRED','QUOTA_EXHAUSTED','CLEANUP_FAILED'):
                job.future.set_exception(GatewayError(self.state));continue
            self.active=True
            task=asyncio.create_task(self.runner.run(job.system,job.prompt,job.request_id))
            cancel=asyncio.create_task(job.cancelled.wait())
            try:
                done,_=await asyncio.wait((task,cancel),return_when=asyncio.FIRST_COMPLETED)
                if cancel in done and job.cancelled.is_set():
                    task.cancel()
                    outcomes=await asyncio.gather(task,return_exceptions=True)
                    if any(isinstance(e,GatewayError) and e.code=='CLEANUP_FAILED' for e in outcomes):self.state='CLEANUP_FAILED'
                    continue
                result=await task
                self.state='ready';self.last_success=time.time()
                if not job.future.done():job.future.set_result(result)
            except GatewayError as error:
                self.state=error.code
                if not job.future.done():job.future.set_exception(error)
            except asyncio.CancelledError:
                task.cancel();await asyncio.gather(task,return_exceptions=True)
                if not job.future.done():job.future.cancel()
                raise
            except Exception:
                self.state='BACKEND_UNAVAILABLE'
                if not job.future.done():job.future.set_exception(GatewayError('BACKEND_UNAVAILABLE'))
            finally:
                cancel.cancel();await asyncio.gather(cancel,return_exceptions=True)
                self.active=False


def application(queue,token,ready_file=None,budget=None,max_reply_chars=1200):
    budget=budget or InputBudget()
    if not isinstance(token,str) or len(token)<32:raise ValueError('Local bearer token required')
    def router_ready():
        if ready_file is None:return True
        try:
            value=json.loads(ready_file.read_text(encoding='utf-8'))
            process=psutil.Process(value['pid'])
            return process.is_running() and abs(process.create_time()-value['created'])<.01
        except (OSError,ValueError,KeyError,psutil.NoSuchProcess):return False
    @web.middleware
    async def guard(request,handler):
        if request.path.startswith('/v1/') and not secrets.compare_digest(request.headers.get('Authorization',''),'Bearer '+token):
            return web.json_response({'error':{'message':'AUTH_FAILED','type':'authentication_error'}},status=401)
        try:return await handler(request)
        except GatewayError as error:
            trace=request.get(TRACE,'unknown')
            queue.last_error={'trace':trace,'code':error.code}
            LOG.warning('REQUEST_FAILED request_id=%s code=%s',trace,error.code)
            status={'UNSUPPORTED_REQUEST':422,'QUOTA_EXHAUSTED':429,'RATE_LIMITED':429,'QUEUE_FULL':429,
                    'INPUT_TOO_LONG':422,'MODEL_CONFIG_UNSUPPORTED':422,
                    'QUEUE_TIMEOUT':504,'MODEL_TIMEOUT':504,'PROTOCOL_ERROR':502}.get(error.code,503)
            return web.json_response({'error':{'message':MESSAGES[error.code]+'（追踪'+trace+'）','type':'gateway_error','code':error.code}},status=status)

    app=web.Application(middlewares=[guard],client_max_size=budget.payload_limit)

    async def health(request):
        return web.json_response({'alive':True,'backend_state':queue.state,'queue':queue.queue.qsize(),
                                  'input_budget':budget.limit,'budget_counting':'utf8_visible_bytes_with_envelope',
                                  'overhead_reserve':budget.overhead,'output_reserve':budget.output,
                                  'native_window':'unverified','parameters':getattr(queue.runner,'last_parameters',{}),
                                  'forced_compact_exclusion_verified':False,
                                  'upstream_inference_attempts':'unverified_cli_internal_recovery',
                                  'control_attempts':getattr(queue.runner,'control_attempts',0),
                                  'user_messages_sent':getattr(queue.runner,'user_messages_sent',0),
                                  'active':queue.active,'cli_attempts':queue.runner.attempts,
                                  'last_success':queue.last_success,'real_inference_verified':queue.last_success is not None,
                                  'router_ready':router_ready(),'last_contract':queue.last_shape,'last_error':queue.last_error})

    async def models(request):
        return web.json_response({'object':'list','data':[{'id':'workbuddy-local','object':'model','owned_by':'local'}]})

    async def chat(request):
        request[TRACE]=uuid.uuid4().hex[:10]
        try:payload=await request.json()
        except (ValueError,UnicodeError):raise GatewayError('UNSUPPORTED_REQUEST') from None
        system,prompt=normalize_request(payload,budget=budget)
        if not router_ready():raise GatewayError('BACKEND_UNAVAILABLE')
        queue.last_shape=contract_shape(payload)
        LOG.info('REQUEST_ACCEPTED request_id=%s',request[TRACE])
        result=await queue.submit(system,prompt,request[TRACE])
        result,limited=prepare_reply(result,max_reply_chars)
        return web.json_response({'id':'chatcmpl-'+request[TRACE],'object':'chat.completion','created':int(time.time()),
            'model':'workbuddy-local','choices':[{'index':0,'message':{'role':'assistant','content':result},
                                               'finish_reason':'length' if limited else 'stop'}]})

    app.router.add_get('/health',health)
    app.router.add_get('/v1/models',models)
    app.router.add_post('/v1/chat/completions',chat)
    async def start(app):await queue.start()
    async def close(app):await queue.close()
    app.on_startup.append(start);app.on_cleanup.append(close)
    return app


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
    path=Path(args.config).resolve();root=path.parent.parent
    settings=load_settings(path)
    llm=settings['llm']
    if llm['host']!='127.0.0.1' or llm['backend']!='codebuddy_cli' or llm['max_concurrency']!=1:
        raise ValueError('Restricted local CLI configuration required')
    tokens=json.loads((root/settings['secrets_file']).read_text(encoding='utf-8'))
    budget=InputBudget.from_settings(settings,validate_model_settings(settings))
    runner=CLIRunner(root,llm['model'],llm['run_timeout_seconds'],llm['cleanup_seconds'],llm['reasoning_effort'],budget)
    queue=ModelQueue(runner,llm['queue_limit'],llm['queue_wait_seconds'])
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    web.run_app(application(queue,tokens['model_gateway'],root/'state/router-ready.json',budget,settings['output']['max_reply_chars']),host=llm['host'],port=llm['port'],
                access_log=None,handler_cancellation=True)


if __name__=='__main__':main()
