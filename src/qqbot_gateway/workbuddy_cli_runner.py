import asyncio
import codecs
import hashlib
import json
import logging
import os
from pathlib import Path
import subprocess
import tempfile

import psutil

from .backends import BackendResult, numeric_usage
from .errors import GatewayError, classify_error
from .text_safety import has_tool_markup
from .cli_control import ControlExchange, model_metadata
from .token_budget import InputBudget, known_models, user_message

LOG = logging.getLogger(__name__)


class ResultParser:
    def __init__(self, expected_model=None):
        self.expected_model = expected_model
        self.decoder = codecs.getincrementaldecoder('utf-8')('strict')
        self.buffer = ''
        self.bytes = 0
        self.initialized = False
        self.result = None
        self.usage = {}
        self.events = []

    def feed(self, chunk, final=False):
        self.bytes += len(chunk)
        if self.bytes > 2 * 1024 * 1024:
            raise GatewayError('PROTOCOL_ERROR')
        try:
            self.buffer += self.decoder.decode(chunk, final=final)
        except UnicodeError:
            raise GatewayError('PROTOCOL_ERROR') from None
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            self.line(line.rstrip('\r'))
        if len(self.buffer) > 512 * 1024:
            raise GatewayError('PROTOCOL_ERROR')
        if final and self.buffer:
            self.line(self.buffer.rstrip('\r'))
            self.buffer = ''

    def line(self, line):
        if not line.strip():
            return
        try:
            event = json.loads(line)
        except ValueError:
            raise GatewayError('PROTOCOL_ERROR') from None
        if not isinstance(event, dict):
            raise GatewayError('PROTOCOL_ERROR')
        kind = event.get('type')
        if len(self.events) >= 128:
            raise GatewayError('PROTOCOL_ERROR')
        self.events.append({'type': kind, 'subtype': event.get('subtype'), 'keys': sorted(event)})
        if kind in ('control_response','control_request'):
            raise GatewayError('PROTOCOL_ERROR')
        if kind == 'error' or event.get('is_error') or event.get('errors'):
            raise GatewayError(classify_error({k:event.get(k) for k in ('error','errors','message','result')}))
        if kind == 'system' and event.get('subtype') == 'init':
            if event.get('tools') != [] or event.get('mcp_servers') != []:
                raise GatewayError('TOOL_ISOLATION_FAILED')
            if self.expected_model is not None and event.get('model') != self.expected_model:
                raise GatewayError('PROTOCOL_ERROR')
            self.initialized = True
        content = event.get('message', {}).get('content', []) if isinstance(event.get('message'), dict) else []
        if isinstance(content, list) and any(isinstance(b, dict) and b.get('type') in ('tool_use', 'tool_call') for b in content):
            raise GatewayError('TOOL_ISOLATION_FAILED')
        if kind == 'result':
            if self.result is not None or not self.initialized:
                raise GatewayError('PROTOCOL_ERROR')
            if (event.get('subtype') != 'success' or event.get('is_error') is not False or
                    event.get('terminal_reason') not in (None, 'end_turn', 'stop', 'completed', 'success') or
                    not isinstance(event.get('result'), str) or not event['result'].strip()):
                raise GatewayError('PROTOCOL_ERROR')
            if has_tool_markup(event['result']):
                raise GatewayError('TOOL_ISOLATION_FAILED')
            self.result = event['result']
            self.usage = numeric_usage(event.get('usage',{}))
            model_usage = event.get('modelUsage',{})
            if isinstance(model_usage,dict):self.usage.update(numeric_usage(model_usage.get(self.expected_model,{})))

    def finish(self, exit_code):
        self.feed(b'', final=True)
        if exit_code != 0:
            raise GatewayError('BACKEND_UNAVAILABLE')
        if not self.initialized or self.result is None:
            raise GatewayError('PROTOCOL_ERROR')
        return self.result


class CLIRunner:
    backend = 'codebuddy_cli'
    def __init__(self, root, model, timeout=90, cleanup_seconds=5, reasoning_effort='auto', budget=None):
        self.root = Path(root)
        lock = json.loads((self.root/'config/versions.lock.json').read_text(encoding='utf-8'))
        self.node = Path(lock['node']['path'])
        self.entry = Path(lock['cli']['entry'])
        self.model = model
        self.timeout = timeout
        self.cleanup_seconds = cleanup_seconds
        self.attempts = 0
        self.last_protocol = []
        self.reasoning_effort = reasoning_effort
        self.budget = budget or InputBudget()
        self.control_attempts = 0
        self.user_messages_sent = 0
        self.last_parameters = {}
        self.control_timeout = 10
        if reasoning_effort != 'auto' and reasoning_effort not in known_models().get(model, {}).get('reasoning', {}).get('supportedEfforts', []):
            raise GatewayError('MODEL_CONFIG_UNSUPPORTED')
        self.denied = json.loads((self.root/'config/cli-tools-denied.json').read_text(encoding='utf-8'))
        bundle = self.entry.parent.parent/'dist/codebuddy-headless.js'
        if not self.node.is_file() or hashlib.sha256(bundle.read_bytes()).hexdigest() != lock['cli']['headless_sha256']:
            raise GatewayError('BACKEND_UNAVAILABLE')

    async def run(self, system, prompt, request_id):
        self.budget.check(system, prompt)
        parent = self.root/'runtime/requests'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=request_id+'-', dir=parent) as directory:
            work = Path(directory)
            if not work.resolve().is_relative_to(parent.resolve()):
                raise GatewayError('BACKEND_UNAVAILABLE')
            system_file = work/'system.txt'
            system_file.write_text(system, encoding='utf-8')
            args = [str(self.node),str(self.entry),'-p','--output-format','stream-json',
                    '--tools','','--strict-mcp-config','--mcp-config',str(self.root/'config/mcp-empty.json'),
                    '--permission-mode','dontAsk','--no-session-persistence','--max-turns','2',
                    '--model',self.model,'--system-prompt-file',str(system_file),
                    '--setting-sources','none','--disallowedTools',*self.denied]
            local_settings={'autoCompactEnabled':False}
            if self.reasoning_effort != 'auto':local_settings['alwaysThinkingEnabled']=True
            args += ['--settings',json.dumps(local_settings)]
            if self.reasoning_effort != 'auto':
                args += ['--effort',self.reasoning_effort,'--input-format','stream-json']
            env = os.environ.copy()
            env.pop('MAX_THINKING_TOKENS',None)
            for key in list(env):
                if any(term in key.upper() for term in ('API_KEY','AUTH_TOKEN','ACCESS_TOKEN','BASE_URL')):
                    env.pop(key)
            # --tools/--setting-sources do not suppress CLI memory interceptors.
            # These process-local flags disable their prompts and background helpers
            # without changing the user's CLI settings or logged-in account.
            env.update({
                'CODEBUDDY_DISABLE_AUTO_MEMORY':'1',
                'CODEBUDDY_CODE_DISABLE_AUTO_MEMORY':'1',
                'CODEBUDDY_MEMORY_ENABLED':'false',
                'CODEBUDDY_TEAM_MEMORY_ENABLED':'false',
                'CODEBUDDY_MEMORY_EXTRACTION_DISABLED':'1',
                'CODEBUDDY_MEMORY_RELEVANCE_DISABLED':'1',
            })
            self.attempts += 1
            LOG.info('CLI_START request_id=%s attempt=1',request_id)
            try:
                process = await asyncio.create_subprocess_exec(*args,cwd=work,env=env,
                    stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,
                    limit=512*1024,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            except OSError:
                raise GatewayError('BACKEND_UNAVAILABLE') from None
            parser = ResultParser(self.model)
            self.last_parameters = {'model':self.model,'effort_requested':self.reasoning_effort,
                                    'effort_effective':None,'auto_compact_setting':False,
                                    'forced_compact_exclusion_verified':False,'native_window':'unverified'}
            self.last_parameters['effort_evidence']='auto_default' if self.reasoning_effort=='auto' else 'awaiting_current_capabilities'
            exchange = ControlExchange('get_available_models') if self.reasoning_effort != 'auto' else None
            acknowledged = asyncio.Event()
            tracked = {}
            try:
                owned_root = psutil.Process(process.pid)
                owned_root.create_time()
            except psutil.NoSuchProcess:
                owned_root = None

            def capture():
                try:
                    if owned_root is None or not owned_root.is_running():return
                    for child in owned_root.children(recursive=True):
                        tracked[(child.pid,child.create_time())] = child
                except psutil.NoSuchProcess:
                    pass

            async def monitor():
                while True:
                    capture()
                    await asyncio.sleep(.05)

            async def read_stdout():
                if exchange is not None:
                    while line := await process.stdout.readline():
                        try:event = json.loads(line)
                        except (ValueError,UnicodeError):raise GatewayError('PROTOCOL_ERROR') from None
                        if not isinstance(event,dict):raise GatewayError('PROTOCOL_ERROR')
                        if event.get('type') == 'control_response':
                            response = exchange.accept(event)
                            models = {m['id']:m for m in model_metadata(response)}
                            model = models.get(self.model, {})
                            if self.reasoning_effort not in model.get('reasoning',{}).get('supportedEfforts',[]):
                                raise GatewayError('MODEL_CONFIG_UNSUPPORTED')
                            maximum = model.get('maxInputTokens')
                            if isinstance(maximum,int) and self.budget.limit > maximum:
                                raise GatewayError('MODEL_CONFIG_UNSUPPORTED')
                            self.last_parameters['effort_effective'] = self.reasoning_effort
                            self.last_parameters['effort_evidence']='current_supportedEfforts_and_cli_flag'
                            acknowledged.set()
                            break
                        # No model response may precede the only user message.
                        if event.get('type') in ('result','assistant','user'):
                            raise GatewayError('PROTOCOL_ERROR')
                        parser.line(line.decode('utf-8'))
                    else:
                        raise GatewayError('PROTOCOL_ERROR')
                while chunk := await process.stdout.read(8192):
                    parser.feed(chunk)

            async def read_stderr():
                count = 0
                while chunk := await process.stderr.read(8192):
                    count += len(chunk)
                    if count > 65536:
                        raise GatewayError('PROTOCOL_ERROR')

            async def write_stdin():
                if exchange is not None:
                    self.control_attempts += 1
                    process.stdin.write((json.dumps(exchange.request())+'\n').encode('utf-8'))
                    await process.stdin.drain()
                    try:
                        await asyncio.wait_for(acknowledged.wait(), min(self.control_timeout,self.timeout))
                    except TimeoutError:
                        raise GatewayError('PROTOCOL_ERROR') from None
                    payload = (json.dumps(user_message(prompt),ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
                else:
                    payload = prompt.encode('utf-8')
                self.user_messages_sent += 1
                process.stdin.write(payload)
                await process.stdin.drain()
                process.stdin.close()

            watcher = asyncio.create_task(monitor())
            io = [asyncio.create_task(coro()) for coro in (read_stdout,read_stderr,write_stdin)]
            try:
                async with asyncio.timeout(self.timeout):
                    await asyncio.gather(*io,process.wait())
                return BackendResult(parser.finish(process.returncode),parser.usage,self.last_parameters,'stop')
            except TimeoutError:
                raise GatewayError('MODEL_TIMEOUT') from None
            except (ValueError,UnicodeError,BrokenPipeError,ConnectionResetError):
                raise GatewayError('PROTOCOL_ERROR') from None
            finally:
                capture()
                watcher.cancel()
                await asyncio.gather(watcher,return_exceptions=True)
                for task in io:task.cancel()
                await asyncio.gather(*io,return_exceptions=True)
                self.last_protocol = parser.events
                def cleanup():
                    if owned_root is not None:
                        tracked[(owned_root.pid,owned_root.create_time())] = owned_root
                    for child in reversed(list(tracked.values())):
                        try:
                            if child.is_running():child.kill()
                        except psutil.NoSuchProcess:pass
                        except psutil.AccessDenied:return False
                    _,alive = psutil.wait_procs(list(tracked.values()),timeout=max(.1,self.cleanup_seconds-1))
                    return not alive
                clean = await asyncio.shield(asyncio.to_thread(cleanup))
                if not clean:raise GatewayError('CLEANUP_FAILED')
                await asyncio.wait_for(process.wait(),timeout=1)
