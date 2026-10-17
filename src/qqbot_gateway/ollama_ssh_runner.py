"""One native generation attempt; uncertain remote work requires explicit clearance."""
import asyncio
import json
import os
from pathlib import Path
import time

from .backends import BackendResult, numeric_usage
from .errors import GatewayError
from .ssh_transport import SSHTransport
from .text_safety import has_tool_markup


def native_payload(cfg,system,prompt):
    return dict(model=cfg['model'],messages=[{'role':'system','content':system}]+json.loads(prompt),
        stream=False,think=False,keep_alive=cfg['keep_alive_seconds'],
        options={k:cfg[k] for k in ('num_ctx','num_predict','temperature','top_p','top_k')})


class OllamaSSHRunner:
    backend = 'ollama_ssh'

    def __init__(self,root,profile,budget,output=None,transport_factory=SSHTransport):
        self.root,self.profile,self.budget = Path(root),profile,budget
        self.factory = transport_factory
        self.transport = None
        self.attempts = self.post_attempts = 0
        self.last_parameters = {k:profile[k] for k in ('model','num_ctx','think','num_predict','keep_alive_seconds','temperature','top_p','top_k')}
        self.metadata = {'state':'not_probed','real_generation_verified':False}
        self.marker = self.root/'state/ollama-remote-result-unknown.json'

    def new_transport(self):
        return self.factory(self.root,self.profile['access_file'])

    async def call(self, function, timeout):
        # close() also interrupts blocking SSH I/O; await thread before releasing concurrency.
        task = asyncio.create_task(asyncio.to_thread(function))
        try:return await asyncio.wait_for(asyncio.shield(task),timeout)
        except (asyncio.CancelledError,TimeoutError):
            self.transport.close()
            await asyncio.gather(task,return_exceptions=True)
            raise

    async def preflight(self,require_digest=True):
        self.transport = self.new_transport()
        deadline = time.monotonic()+25
        def inspect():
            request = self.transport.request
            version = request('GET','/api/version',deadline=deadline)
            tags = request('GET','/api/tags',deadline=deadline)
            if not isinstance(version.get('version'),str) or not isinstance(tags.get('models'),list):raise GatewayError('PROTOCOL_ERROR')
            model = next((m for m in tags.get('models',[]) if isinstance(m,dict) and m.get('name')==self.profile['model']),None)
            if model is None:raise GatewayError('OLLAMA_MODEL_MISMATCH')
            expected = self.profile['expected_digest']
            if (require_digest and not expected) or (expected is not None and model.get('digest') != expected):raise GatewayError('OLLAMA_DIGEST_MISMATCH')
            show = request('POST','/api/show',{'model':self.profile['model'],'verbose':False},deadline=deadline)
            if any(show.get(k) or model.get(k) for k in ('remote_host','remote_model')):raise GatewayError('OLLAMA_PARAMETERS_UNSUPPORTED')
            capabilities = show.get('capabilities',[])
            thinking = show.get('thinking',{})
            allowed = thinking.get('values',[]) if isinstance(thinking,dict) else []
            # Observed Ollama metadata: {values:[false,true],default:true}.
            if 'completion' not in capabilities or 'thinking' not in capabilities or not any(v is False for v in allowed):raise GatewayError('OLLAMA_PARAMETERS_UNSUPPORTED')
            info = show.get('model_info',{})
            if not isinstance(info,dict):raise GatewayError('PROTOCOL_ERROR')
            windows = [v for k,v in info.items() if k.endswith('.context_length') and type(v) is int]
            if not windows or self.profile['num_ctx']>max(windows):raise GatewayError('OLLAMA_PARAMETERS_UNSUPPORTED')
            loaded = request('GET','/api/ps',deadline=deadline)
            observed = [{k:m.get(k) for k in ('name','digest','context_length','size_vram')} for m in loaded.get('models',[]) if isinstance(m,dict) and m.get('name')==self.profile['model']]
            return {'state':'metadata_ready','version':version.get('version'),'digest':model['digest'],
                'digest_confirmed':bool(expected),
                'declared_context_max':max(windows),'think_false_supported':True,'loaded_observation':observed,
                'checked_at':time.time(),'real_generation_verified':False}
        try:
            self.metadata = await self.call(inspect,25)
            return self.metadata
        except TimeoutError:raise GatewayError('SSH_UNAVAILABLE') from None
        except GatewayError:raise
        except Exception:raise GatewayError('PROTOCOL_ERROR') from None
        finally:self.transport.close();self.transport=None

    def pending(self,request_id):
        self.marker.parent.mkdir(parents=True,exist_ok=True)
        try:
            with self.marker.open('x',encoding='utf-8') as stream:
                json.dump({'code':'REMOTE_RESULT_UNKNOWN','request_id':request_id,'backend':self.backend,'time':time.time()},stream)
                stream.flush();os.fsync(stream.fileno())
        except FileExistsError:raise GatewayError('REMOTE_RESULT_UNKNOWN') from None
        self.attempts += 1;self.post_attempts += 1

    async def run(self,system,prompt,request_id):
        if self.marker.exists():raise GatewayError('REMOTE_RESULT_UNKNOWN')
        self.budget.check(system,prompt)
        cfg = self.profile
        payload = native_payload(cfg,system,prompt)
        self.transport = self.new_transport()
        deadline = time.monotonic()+cfg['run_timeout_seconds']
        sent = False
        def before_send():
            nonlocal sent
            self.pending(request_id);sent=True
        def generate():
            tags = self.transport.request('GET','/api/tags',deadline=deadline)
            if not isinstance(tags.get('models'),list):raise GatewayError('PROTOCOL_ERROR')
            model = next((m for m in tags.get('models',[]) if isinstance(m,dict) and m.get('name')==cfg['model']),None)
            if model is None:raise GatewayError('OLLAMA_MODEL_MISMATCH')
            if model.get('digest') != cfg['expected_digest']:raise GatewayError('OLLAMA_DIGEST_MISMATCH')
            return self.transport.request('POST','/api/chat',payload,deadline=deadline,before_send=before_send)
        try:
            result = await self.call(generate,cfg['run_timeout_seconds'])
            # A valid terminal response confirms completion even if content is rejected below.
            if result.get('done') is not True:raise GatewayError('PROTOCOL_ERROR')
            self.marker.unlink(missing_ok=True);sent=False
            message = result.get('message',{})
            if (result.get('model') != cfg['model'] or result.get('error') or not isinstance(message,dict) or
                message.get('role') != 'assistant' or message.get('thinking') or message.get('tool_calls')):
                raise GatewayError('PROTOCOL_ERROR')
            text = message.get('content')
            if not isinstance(text,str) or not text.strip() or len(text.encode('utf-8'))>512*1024:raise GatewayError('PROTOCOL_ERROR')
            if has_tool_markup(text):raise GatewayError('TOOL_ISOLATION_FAILED')
            if result.get('done_reason') not in ('stop','length'):raise GatewayError('PROTOCOL_ERROR')
            return BackendResult(text,numeric_usage(result),self.last_parameters,result['done_reason'])
        except BaseException:
            if sent:raise GatewayError('REMOTE_RESULT_UNKNOWN') from None
            raise
        finally:self.transport.close();self.transport=None


def clear_unknown(root,confirmed):
    from .config import configuration_lock,require_stopped
    if confirmed != 'REMOTE_CHECKED_STOPPED':raise ValueError('Explicit remote completion confirmation required')
    with configuration_lock(root):
        require_stopped(root)
        (Path(root)/'state/ollama-remote-result-unknown.json').unlink(missing_ok=True)
