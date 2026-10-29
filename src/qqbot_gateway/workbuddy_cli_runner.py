import asyncio
import codecs
import hashlib
import json
import logging
import os
import re
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


def failure_summary(trace, code, parser, guard_state):
    """Only bounded metadata; never subprocess text, queries, URLs or messages."""
    from .errors import MESSAGES
    tags={'unavailable','none','tool_identity_replay_or_limit','tool_validation_or_io','tool_hook_failure',
        'native_step_validation','native_result_validation','step_validation_or_io','identity_projection_or_step',
        'tool_envelope','tool_private','fetch_input','search_input','search_domains','search_url',
        'tool_total_bytes','non_text_resource','result_private','tool_result_bytes','tool_io_or_invalid_json',
        'previous_failure','tool_subagent','tool_wrong_name','tool_id','tool_plan_missing','tool_plan_mismatch',
        'tool_replayed','tool_limit','tool_deadline','native_ready','native_step_identity','native_turn',
        'native_rows','native_first','native_blocks','native_answer_history','native_call_history',
        'native_result_history','native_history_type','native_history_complete','native_prefix','native_mcp',
        'native_tool_definitions','native_step_budget','server_tool','native_planned_limit','native_returned_tool','native_io'}
    safe_tag=lambda value: value if isinstance(value,str) and value in tags else 'suppressed'
    return dict(schema=1,trace=trace if isinstance(trace,str) and re.fullmatch('[a-f0-9]{10}',trace) else '0000000000',
        code=code if code in MESSAGES else 'BACKEND_UNAVAILABLE',initialized=parser.initialized,
        tool_calls=len(parser.tool_calls),tool_results=len(parser.tool_results),
        reason=safe_tag(guard_state.get('reason','unavailable')),
        guard_reason=safe_tag(guard_state.get('guard_reason','unavailable')),
        refusals=[{k:safe_tag(row.get(k,'unavailable')) for k in ('reason','guard_reason')}
            for row in guard_state.get('refusals',[])[:8] if isinstance(row,dict)])


class _MetadataReady(Exception):
    pass


class _ProbeReady(Exception):
    pass


class ResultParser:
    def __init__(self, expected_model=None, allowed_tools=(), max_calls=3, visible_limit=16384):
        self.frame_limit=max(512*1024,visible_limit*8)
        self.stream_limit=max(2*1024*1024,self.frame_limit*4)
        self.expected_model = expected_model
        self.allowed_tools=set(allowed_tools);self.max_calls=max_calls;self.tool_calls={};self.tool_results=set()
        self.decoder = codecs.getincrementaldecoder('utf-8')('strict')
        self.buffer = ''
        self.bytes = 0
        self.initialized = False
        self.result = None
        self.usage = {}
        self.events = []

    def feed(self, chunk, final=False):
        self.bytes += len(chunk)
        if self.bytes > self.stream_limit:
            raise GatewayError('PROTOCOL_ERROR')
        try:
            self.buffer += self.decoder.decode(chunk, final=final)
        except UnicodeError:
            raise GatewayError('PROTOCOL_ERROR') from None
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            self.line(line.rstrip('\r'))
        if len(self.buffer.encode('utf-8')) > self.frame_limit:
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
            tools=event.get('tools')
            if not isinstance(tools,list) or len(tools)!=len(self.allowed_tools) or set(tools)!=self.allowed_tools or event.get('mcp_servers') != []:
                raise GatewayError('TOOL_ISOLATION_FAILED')
            if self.expected_model is not None and event.get('model') != self.expected_model:
                raise GatewayError('PROTOCOL_ERROR')
            self.initialized = True
        content = event.get('message', {}).get('content', []) if isinstance(event.get('message'), dict) else []
        for b in content if isinstance(content,list) else []:
            if not isinstance(b,dict):raise GatewayError('PROTOCOL_ERROR')
            if b.get('type') in ('tool_use','tool_call'):
                ident=b.get('id');name=b.get('name')
                if (not self.initialized or name not in self.allowed_tools or not isinstance(ident,str) or
                        ident in self.tool_calls or len(self.tool_calls)>=self.max_calls):
                    raise GatewayError('TOOL_ISOLATION_FAILED')
                self.tool_calls[ident]=name
            elif b.get('type')=='tool_result':
                ident=b.get('tool_use_id')
                if ident not in self.tool_calls or ident in self.tool_results:raise GatewayError('PROTOCOL_ERROR')
                self.tool_results.add(ident)
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
        if self.tool_results!=set(self.tool_calls):raise GatewayError('PROTOCOL_ERROR')
        return self.result


class CLIRunner:
    backend = 'codebuddy_cli'
    def __init__(self, root, model, timeout=90, cleanup_seconds=5, reasoning_effort='auto', budget=None):
        self.root = Path(root)
        lock = json.loads((self.root/'config/versions.lock.json').read_text(encoding='utf-8'))
        self.node = Path(lock['node']['path'])
        self.entry = Path(lock['cli']['entry'])
        if not self.entry.is_absolute():self.entry=self.root/self.entry
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

    async def run(self, system, prompt, request_id):
        return await self._execute(system, prompt, request_id)

    async def probe_image_contract(self, system, prompt, request_id, *, fault=None):
        """Local single-user turn.step short circuit; never a business answer."""
        if fault not in (None,'missing_plugin','wrong_receipt'):raise ValueError('INVALID_PROBE_FAULT')
        return await self._execute(system,prompt,request_id,probe=True,probe_fault=fault)

    async def _execute(self, system, prompt, request_id, *, control_only=False,probe=False,probe_fault=None):
        from .vision import CURRENT,text_budget,cli_message,wire_check,production_budget
        from .cli_web_policy import native_contract, SCOPE, current_question
        web=getattr(self,'web_config',{})
        native=bool(getattr(self,'native_web',False) and not control_only)
        scope=SCOPE.get()
        policy=native_contract(web,getattr(self,'web_private_ids',()),text_budget(self.budget),scope[1] or current_question(prompt)) if native else None
        if policy and not scope[0]:policy['allowed_tools']=[]
        allowed=policy['allowed_tools'] if policy else []
        denied=[t for t in self.denied if t not in allowed]
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
                    '--tools',','.join('NoDefer('+t+')' for t in allowed),'--strict-mcp-config','--mcp-config',str(self.root/'config/mcp-empty.json'),
                    '--permission-mode','dontAsk','--no-session-persistence','--max-turns',str(policy['max_turns'] if policy else 2),
                    '--model',self.model,'--system-prompt-file',str(system_file),
                    '--setting-sources','none','--disallowedTools',*denied]
            if allowed:args+=['--allowedTools',*allowed]
            local_settings={'autoCompactEnabled':False,'alwaysThinkingEnabled':False}
            args += ['--settings',json.dumps(local_settings)]
            guard=None
            from .hosted_cli_budget import KIND, final_budget, framework_upper, model_terms
            if native or CURRENT.get() and self.budget.vision_kind==KIND:
                from .vision_mod_guard import Guard
                from .vision_capabilities import selected_record
                try:
                    image=CURRENT.get().blob if CURRENT.get() else None
                    terms=final_budget(selected_record(self.vision_settings),self.budget,system,prompt,
                        image.width,image.height,known_models().get(self.model,{})) if image else dict(T=len((system+prompt).encode()),F=framework_upper(),V=0,
                            O=model_terms(known_models().get(self.model,{}),self.budget.output)[1],C=1000000)
                    guard=Guard(work,system,prompt,image,terms,mode='probe' if probe else 'live',denied_tools=denied,wire_message=image_message,native_web=policy)
                except (OSError,ValueError,KeyError,TypeError):
                    raise GatewayError('MODEL_CONFIG_UNSUPPORTED') from None
                if probe_fault!='missing_plugin':args += ['--plugin-dir',str(guard.root)]
            elif probe:
                raise GatewayError('MODEL_CONFIG_UNSUPPORTED')
            if self.reasoning_effort != 'auto':
                args += ['--effort',self.reasoning_effort,'--input-format','stream-json']
            elif CURRENT.get() or native:args += ['--input-format','stream-json']
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
                    limit=max(512*1024,self.budget.limit*8) if self.budget else 512*1024,
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
            parser = ResultParser(self.model,allowed,policy['max_calls'] if policy else 3,self.budget.limit if self.budget else 16384)
            self.last_parameters = {'model':self.model,'effort_requested':self.reasoning_effort,
                                    'effort_effective':None,'thinking_enabled':False,'allowed_tools':allowed,'auto_compact_setting':False,
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
                elif CURRENT.get() or native:
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
            io = [asyncio.create_task(coro()) for coro in (read_stdout,read_stderr,write_stdin)]
            generation = 'pending'
            try:
                async with asyncio.timeout(self.timeout):
                    await asyncio.gather(*io,process.wait())
                if guard:
                    try:self.last_parameters['vision_guard']=guard.finish()
                    except (OSError,ValueError):raise GatewayError('MODEL_CONFIG_UNSUPPORTED') from None
                    if policy:self.last_parameters['native_web']=self.last_parameters['vision_guard'].get('native_web',{})
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
                if generation not in ('pending','success','cancelled'):
                    try:
                        from .lifecycle import atomic_json
                        try:observed=guard.read() if guard else {}
                        except (OSError,ValueError):observed={}
                        summary=failure_summary(owner.record.get('trace'),generation,parser,observed)
                        self.last_parameters['failure_summary']=summary
                        atomic_json(self.root/'state/cli-last-failure.json',summary)
                    except OSError:pass
                if probe and guard:
                    try:self.last_parameters['vision_guard_observed']=guard.read()
                    except (OSError,ValueError) as error:self.last_parameters['vision_guard_read_error']=str(error)
                    try:
                        self.last_parameters['probe_evidence']=guard.preserve_probe(
                            self.root/'state/lap42-vision-closure/probe-request-evidence'/work.name)
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
