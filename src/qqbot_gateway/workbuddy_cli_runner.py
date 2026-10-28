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

from .cleanup_identity import CleanupOwner
from .backends import BackendResult, numeric_usage
from .errors import GatewayError, classify_error
from .text_safety import has_tool_markup
from .cli_control import ControlExchange, model_metadata
from .token_budget import InputBudget, known_models, user_message

LOG = logging.getLogger(__name__)


class _MetadataReady(Exception):
    pass


class _ProbeReady(Exception):
    pass


class ResultParser:
    def __init__(self, expected_model=None, allowed_tools=()):
        if not set(allowed_tools) <= {'WebFetch', 'WebSearch'}:
            raise ValueError('Read-only native web tools required')
        self.allowed_tools = frozenset(allowed_tools)
        self.tool_calls = {}
        self.completed_tools = set()
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
            tools = event.get('tools')
            if (not isinstance(tools,list) or any(not isinstance(t,str) for t in tools) or
                    set(tools) != self.allowed_tools or len(tools) != len(set(tools)) or
                    event.get('mcp_servers') != [] or event.get('mcp_servers_unavailable')):
                raise GatewayError('TOOL_ISOLATION_FAILED')
            if self.initialized:raise GatewayError('PROTOCOL_ERROR')
            if self.expected_model is not None and event.get('model') != self.expected_model:
                raise GatewayError('PROTOCOL_ERROR')
            self.initialized = True
        content = event.get('message', {}).get('content', []) if isinstance(event.get('message'), dict) else []
        # Only the installed CLI's complete assistant tool_use / user tool_result
        # envelopes are accepted. Never promote intermediate text to the answer.
        if kind in ('tool_use','tool_call','tool_result'):
            raise GatewayError('TOOL_ISOLATION_FAILED')
        for block in content if isinstance(content,list) else []:
            if not isinstance(block,dict):continue
            if block.get('type') in ('tool_use','tool_call'):
                name,call_id=block.get('name'),block.get('id')
                if (not self.initialized or self.result is not None or kind!='assistant' or
                        not isinstance(name,str) or name not in self.allowed_tools or not isinstance(call_id,str) or not call_id or
                        call_id in self.tool_calls):raise GatewayError('TOOL_ISOLATION_FAILED')
                self.tool_calls[call_id]=name
            elif block.get('type')=='tool_result':
                call_id=block.get('tool_use_id')
                if (kind!='user' or self.result is not None or not isinstance(call_id,str) or
                        call_id not in self.tool_calls or call_id in self.completed_tools):
                    raise GatewayError('TOOL_ISOLATION_FAILED')
                self.completed_tools.add(call_id)
        if kind == 'result':
            if self.result is not None or not self.initialized or set(self.tool_calls)!=self.completed_tools:
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

    def cleanup_owner(self):
        owner = getattr(self, '_cleanup_owner', None)
        # Offline harnesses replace root after construction; initialize lazily.
        if owner is None:
            owner = self._cleanup_owner = CleanupOwner(self.root)
        return owner

    def cleanup_status(self):
        return self.cleanup_owner().status()

    async def cleanup_check(self):
        return await self.cleanup_owner().check()

    async def cleanup_close(self):
        owner = self.cleanup_owner()
        if owner.task is not None:
            await owner.join()

    async def inspect_models(self, request_id):
        """Same isolated controls and cleanup, with no user or model generation."""
        return await self._execute('', '', request_id, control_only=True)

    async def run(self, system, prompt, request_id, *, group_request=None):
        return await self._execute(system, prompt, request_id,group_request=group_request)

    async def run_group(self, system, prompt, request_id, request):
        return await self.run(system,prompt,request_id,group_request=request)

    async def probe_image_contract(self, system, prompt, request_id, *, fault=None):
        """Local single-user turn.step short circuit; never a business answer."""
        if fault not in (None,'missing_plugin','wrong_receipt'):raise ValueError('INVALID_PROBE_FAULT')
        return await self._execute(system,prompt,request_id,probe=True,probe_fault=fault)

    async def _execute(self, system, prompt, request_id, *, control_only=False,probe=False,probe_fault=None,group_request=None):
        from .vision import CURRENT,text_budget,cli_message,wire_check,production_budget
        from .lifecycle import stopping
        if stopping(self.root):raise GatewayError('SHUTTING_DOWN')
        from .web_policy import native_tools, current_question
        tools=native_tools(getattr(self,'web_settings',{}),current_question(prompt,group_request),
            image=bool(CURRENT.get()),disabled=control_only or probe or bool(group_request and
                not group_request.get('must_reply') and not getattr(self,'allow_ambient_web',True)))
        denied=[name for name in self.denied if name not in tools]
        if getattr(self,'web_settings',None) and not control_only and not CURRENT.get():
            system+='\n本次会话只读联网工具：'+('、'.join(tools) if tools else '无')+'。未列出的工具不可用；没有实际工具结果不得声称已联网。图片会话不联网，图+URL不代表已读网页。\n'
        if control_only and CURRENT.get():raise GatewayError('PROTOCOL_ERROR')
        if not control_only:production_budget(self.root,getattr(self,'vision_settings',{}),self.budget,system,prompt)
        text_budget(self.budget).check(system, prompt)
        image_message=cli_message(prompt)
        wire_check(dict(system=system,input=image_message))
        parent = self.root/'runtime/requests'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=request_id+'-', dir=parent) as directory:
            work = Path(directory)
            if not work.resolve().is_relative_to(parent.resolve()):
                raise GatewayError('BACKEND_UNAVAILABLE')
            system_file = work/'system.txt'
            system_file.write_text(system, encoding='utf-8')
            args = [str(self.node),str(self.entry),'-p','--output-format','stream-json',
                    '--tools',','.join(tools),'--strict-mcp-config','--mcp-config',str(self.root/'config/mcp-empty.json'),
                    '--permission-mode','dontAsk','--no-session-persistence','--max-turns','8' if tools else '2',
                    '--model',self.model,'--system-prompt-file',str(system_file),
                    '--setting-sources','none','--disallowedTools',*denied]
            if tools:args += ['--allowedTools',*tools]
            local_settings={'autoCompactEnabled':False}
            if self.reasoning_effort != 'auto':local_settings['alwaysThinkingEnabled']=True
            args += ['--settings',json.dumps(local_settings)]
            guard=None
            from .hosted_cli_budget import KIND, final_budget
            if CURRENT.get() and self.budget.vision_kind==KIND:
                from .vision_mod_guard import Guard
                from .vision_capabilities import selected_record
                try:
                    terms=final_budget(selected_record(self.vision_settings),self.budget,system,prompt,
                        CURRENT.get().blob.width,CURRENT.get().blob.height,known_models().get(self.model,{}))
                    guard=Guard(work,system,prompt,CURRENT.get().blob,terms,mode='probe' if probe else 'live',denied_tools=self.denied,wire_message=image_message)
                except (OSError,ValueError,KeyError,TypeError):
                    raise GatewayError('MODEL_CONFIG_UNSUPPORTED') from None
                if probe_fault!='missing_plugin':args += ['--plugin-dir',str(guard.root)]
            elif probe:
                raise GatewayError('MODEL_CONFIG_UNSUPPORTED')
            if self.reasoning_effort != 'auto':
                args += ['--effort',self.reasoning_effort,'--input-format','stream-json']
            elif CURRENT.get():args += ['--input-format','stream-json']
            env = os.environ.copy()
            if guard:
                env.update(CBC_ENABLE_FUNCTION_HOOKS='1',CLAUDE_CODE_ENABLE_FUNCTION_HOOKS='1')
                env['CODEBUDDY_DISABLE_SYSTEM_REMINDER_MD']='1'
                env.pop('CODEBUDDY_LIBRARY_RUNTIME',None)
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
            owner = self.cleanup_owner()
            owner.reserve(request_id)
            self.attempts += 1
            LOG.info('CLI_START request_id=%s attempt=1',request_id)
            try:
                process = await asyncio.create_subprocess_exec(*args,cwd=work,env=env,
                    stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,
                    limit=512*1024,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            except BaseException as error:
                # A cancelled spawn has no provable root identity: retain unknown.
                if not isinstance(error, OSError):owner.reason('observation_incomplete')
                empty = asyncio.create_task(asyncio.sleep(0))
                owner.begin(None, [], empty, None,
                            'cancelled' if isinstance(error, asyncio.CancelledError) else 'BACKEND_UNAVAILABLE', self.cleanup_seconds)
                clean = await owner.join()
                if not clean:raise GatewayError('CLEANUP_FAILED') from None
                raise GatewayError('BACKEND_UNAVAILABLE') from None
            parser = ResultParser(self.model,tools)
            self.last_parameters = {'model':self.model,'effort_requested':self.reasoning_effort,
                                    'native_web_tools':list(tools),'cli_max_turns':8 if tools else 2,
                                    'effort_effective':None,'auto_compact_setting':False,
                                    'forced_compact_exclusion_verified':False,'native_window':'unverified'}
            self.last_parameters['effort_evidence']='auto_default' if self.reasoning_effort=='auto' else 'awaiting_current_capabilities'
            exchange = ControlExchange('get_available_models') if control_only or self.reasoning_effort != 'auto' else None
            acknowledged = asyncio.Event()
            owned_root = None
            try:
                owned_root = psutil.Process(process.pid)
                owner.add(owned_root, root=True)
            except psutil.NoSuchProcess:
                pass
            except psutil.Error:
                owner.reason('observation_incomplete')

            def capture():
                owner.observe(owned_root)

            async def monitor():
                while True:
                    capture()
                    await asyncio.sleep(.05)

            async def read_stdout():
                if exchange is not None:
                    while line := await process.stdout.readline():
                        try:event = json.loads(line)
                        except (ValueError,UnicodeError):
                            if probe:
                                self.last_probe_nonjson=getattr(self,'last_probe_nonjson',b'')+line
                            raise GatewayError('PROTOCOL_ERROR') from None
                        if not isinstance(event,dict):raise GatewayError('PROTOCOL_ERROR')
                        if event.get('type') == 'control_response':
                            response = exchange.accept(event)
                            safe_models=model_metadata(response)
                            ids=[m['id'] for m in safe_models]
                            if len(set(ids))!=len(ids):raise GatewayError('PROTOCOL_ERROR')
                            models = {m['id']:m for m in safe_models}
                            self.last_models=safe_models
                            model = models.get(self.model, {})
                            if self.reasoning_effort != 'auto' and self.reasoning_effort not in model.get('reasoning',{}).get('supportedEfforts',[]):
                                raise GatewayError('MODEL_CONFIG_UNSUPPORTED')
                            maximum = model.get('maxInputTokens')
                            if isinstance(maximum,int) and self.budget.limit > maximum:
                                raise GatewayError('MODEL_CONFIG_UNSUPPORTED')
                            self.last_parameters['effort_effective'] = self.reasoning_effort
                            self.last_parameters['effort_evidence']='current_supportedEfforts_and_cli_flag'
                            acknowledged.set()
                            if control_only:raise _MetadataReady()
                            break
                        # No model response may precede the only user message.
                        if event.get('type') in ('result','assistant','user'):
                            raise GatewayError('PROTOCOL_ERROR')
                        parser.line(line.decode('utf-8'))
                    else:
                        raise GatewayError('PROTOCOL_ERROR')
                if guard and probe:
                    while line := await process.stdout.readline():
                        event=json.loads(line)
                        if event.get('type')=='assistant':
                            self.last_parameters['vision_probe_failure']='generation_unknown'
                            raise GatewayError('PROTOCOL_ERROR')
                        if event.get('type')=='result':
                            observed=guard.read()
                            self.last_parameters['vision_guard_observed']=observed
                            if 'refused' in observed.get('stages',[]) and observed.get('next_calls')==0:
                                raise GatewayError('MODEL_CONFIG_UNSUPPORTED')
                            proof=guard.finish()
                            if not parser.initialized:raise GatewayError('PROTOCOL_ERROR')
                            # An empty Mod short circuit produces the CLI's local
                            # no-response terminal on this locked build. The
                            # independently verified probe receipt is the proof.
                            self.last_parameters['probe_terminal_subtype']=event.get('subtype')
                            self.last_parameters['vision_guard']=proof
                            raise _ProbeReady()
                        parser.line(line.decode('utf-8'))
                else:
                    while chunk := await process.stdout.read(8192):
                        parser.feed(chunk)

            async def read_stderr():
                count = 0
                if probe:self.last_probe_stderr=bytearray()
                while chunk := await process.stderr.read(8192):
                    count += len(chunk)
                    if count > 65536:
                        raise GatewayError('PROTOCOL_ERROR')
                    if probe:self.last_probe_stderr.extend(chunk)

            async def write_stdin():
                if exchange is not None:
                    self.control_attempts += 1
                    process.stdin.write((json.dumps(exchange.request())+'\n').encode('utf-8'))
                    await process.stdin.drain()
                    try:
                        await asyncio.wait_for(acknowledged.wait(), min(self.control_timeout,self.timeout))
                    except TimeoutError:
                        raise GatewayError('PROTOCOL_ERROR') from None
                    if control_only:return
                    if CURRENT.get():
                        text_budget(self.budget).check(system,prompt)
                        self._native_metadata_check(system,prompt)
                        if guard:
                            try:
                                ready_proof=await guard.ready(min(self.control_timeout,self.timeout))
                                if probe:self.last_parameters['vision_guard_ready']=ready_proof
                                if probe_fault=='wrong_receipt':
                                    # Deliberately invalidate the expected identity after
                                    # real engine readiness; the parent must withhold user.
                                    guard.request['nonce']='0'*64
                                    guard.read()
                            except (OSError,ValueError,TimeoutError) as error:
                                self.last_parameters['vision_rejection']='VISION_PLUGIN_NOT_READY_OR_MISMATCH'
                                if probe:self.last_parameters['vision_guard_error']=type(error).__name__
                                if probe:self.last_parameters['vision_guard_reason']=str(error)
                                raise GatewayError('MODEL_CONFIG_UNSUPPORTED') from None
                    payload = (json.dumps(image_message,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
                elif CURRENT.get():
                    text_budget(self.budget).check(system,prompt)
                    payload = (json.dumps(image_message,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
                else:
                    payload = prompt.encode('utf-8')
                # Identity/ledger overflow must fail before the only user input.
                if owner.record['reasons'] or owner.io_failed:
                    raise GatewayError('CLEANUP_FAILED')
                if guard:
                    if hashlib.sha256(payload).hexdigest()!=guard.request['wire_sha256']:
                        raise GatewayError('MODEL_CONFIG_UNSUPPORTED')
                self.user_messages_sent += 1
                process.stdin.write(payload)
                await process.stdin.drain()
                process.stdin.close()

            watcher = asyncio.create_task(monitor())
            async def watch_shutdown():
                while process.returncode is None:
                    if stopping(self.root):raise GatewayError('SHUTTING_DOWN')
                    await asyncio.sleep(.05)
            io = [asyncio.create_task(coro()) for coro in (read_stdout,read_stderr,write_stdin,watch_shutdown)]
            generation = 'pending'
            try:
                async with asyncio.timeout(self.timeout):
                    await asyncio.gather(*io,process.wait())
                if guard:
                    try:self.last_parameters['vision_guard']=guard.finish()
                    except (OSError,ValueError):raise GatewayError('MODEL_CONFIG_UNSUPPORTED') from None
                if stopping(self.root):raise GatewayError('SHUTTING_DOWN')
                result = BackendResult(parser.finish(process.returncode),parser.usage,self.last_parameters,'stop')
                generation = 'success'
                return result
            except _MetadataReady:
                # Intentional end after control; no generation was started.
                generation='cancelled'
                return self.last_models
            except _ProbeReady:
                generation='cancelled'
                return {'local_probe':True,'user_messages':self.user_messages_sent,
                    'guard':self.last_parameters['vision_guard']}
            except TimeoutError:
                generation = 'MODEL_TIMEOUT'
                raise GatewayError('MODEL_TIMEOUT') from None
            except GatewayError as error:
                generation = error.code
                raise
            except asyncio.CancelledError:
                generation = 'cancelled'
                raise
            except (ValueError,UnicodeError,BrokenPipeError,ConnectionResetError):
                generation = 'PROTOCOL_ERROR'
                raise GatewayError('PROTOCOL_ERROR') from None
            except Exception:
                generation = 'BACKEND_UNAVAILABLE'
                raise GatewayError('BACKEND_UNAVAILABLE') from None
            finally:
                if probe and guard:
                    try:self.last_parameters['vision_guard_observed']=guard.read()
                    except (OSError,ValueError) as error:self.last_parameters['vision_guard_read_error']=str(error)
                    try:
                        from .vision_regression import PROBE_BASE
                        destination=PROBE_BASE.get() or self.root/'state/lap42-vision-closure/probe-request-evidence'
                        self.last_parameters['probe_evidence']=guard.preserve_probe(destination/work.name)
                    except (OSError,ValueError):self.last_parameters['probe_evidence_error']=True
                self.last_protocol = parser.events
                owner.begin(process, io, watcher, owned_root, generation, self.cleanup_seconds)
                clean = await owner.join()
                if not clean:
                    # Keep original generation metadata; withhold any late answer.
                    raise GatewayError('CLEANUP_FAILED')
                if asyncio.current_task().cancelling():
                    raise asyncio.CancelledError

    def _native_metadata_check(self, system, prompt):
        from .vision import CURRENT
        from .hosted_cli_budget import KIND, RUNTIME, final_budget
        if self.budget.vision_kind != KIND:
            # Legacy local/transport-only fixtures keep their existing contract.
            # A real hosted observation is always constructed with from_settings.
            return
        from .vision_capabilities import selected_record, runtime_identity
        settings=getattr(self,'vision_settings',{})
        try:
            record=selected_record(settings)
            if runtime_identity(self.root,settings)!=RUNTIME:raise ValueError('HOSTED_RUNTIME_MISMATCH')
            model=next((m for m in self.last_models if m['id']==self.model),{})
            expected=known_models().get(self.model,{})
            keys=('id','supportsImages','maxInputTokens','maxOutputTokens','contextWindow','reasoning')
            if {k:model.get(k) for k in keys}!={k:expected.get(k) for k in keys}:
                raise ValueError('HOSTED_CURRENT_CAPABILITIES_CHANGED')
            image=CURRENT.get().blob.checked()
            terms=final_budget(record,self.budget,system,prompt,image.width,image.height,model)
            self.last_parameters['native_budget']=terms
        except (ValueError,KeyError,TypeError,StopIteration) as error:
            self.last_parameters['vision_rejection']=str(error)
            raise GatewayError('MODEL_CONFIG_UNSUPPORTED') from None
