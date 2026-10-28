import argparse
import os
import asyncio
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import secrets
import time
import uuid
import re
import psutil
import aiohttp

from aiohttp import web
from .config import load_settings

from .contracts import normalize_request, contract_shape
from .errors import GatewayError, MESSAGES
from .backends import BackendResult, create_runner
from .token_budget import InputBudget, validate_model_settings
from .chat_text import prepare_reply
from .reply_plan import make_reply_plan, DEFAULTS
from .lifecycle import stopping

LOG = logging.getLogger(__name__)
TRACE = web.RequestKey('qqbot_trace',str)
GROUP_REQUEST = web.RequestKey('qqbot_group_request',dict)
V2_SOURCE = web.RequestKey('qqbot_v2_source',dict)
V2_EFFECTIVE = web.RequestKey('qqbot_v2_effective',dict)
VISION_LEASE = web.RequestKey('qqbot_vision_lease',object)


@dataclass
class Job:
    system: str
    prompt: str
    request_id: str
    deadline: float
    future: asyncio.Future
    group_request: dict | None = None
    vision: object = None
    prepare_deadline: float | None = None
    requested_at: float = field(default_factory=time.time)
    started: asyncio.Event = field(default_factory=asyncio.Event)
    cancelled: asyncio.Event = field(default_factory=asyncio.Event)


class ModelQueue:
    @staticmethod
    def release_image(job):
        if job.vision and job.vision.lease:job.vision.lease.release()
        job.vision=None

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
        self.last_usage={}
        self.group_usage={}
        self.close_task=None
        if self.cleanup_status().get('blocked'):
            self.state='CLEANUP_FAILED'

    def cleanup_status(self):
        method=getattr(self.runner,'cleanup_status',None)
        return method() if method else {}

    async def cleanup_admission(self):
        if self.state=='CLEANUP_FAILED' or not self.active and self.cleanup_status().get('blocked'):
            check=getattr(self.runner,'cleanup_check',None)
            status=await check() if check else {'blocked':True}
            self.state='CLEANUP_FAILED' if status.get('blocked',True) else 'not_probed'

    async def start(self):
        self.worker=asyncio.create_task(self._work())

    async def close(self):
        if self.close_task is None:
            self.close_task=asyncio.create_task(self._close())
        await asyncio.shield(self.close_task)

    async def _close(self):
        if self.worker:
            self.worker.cancel()
            await asyncio.gather(self.worker,return_exceptions=True)
        close=getattr(self.runner,'cleanup_close',None)
        if close:await close()
        if self.cleanup_status().get('blocked'):self.state='CLEANUP_FAILED'
        while not self.queue.empty():
            job=self.queue.get_nowait()
            self.release_image(job)
            if not job.future.done():job.future.set_exception(GatewayError('BACKEND_UNAVAILABLE'))

    async def submit(self,system,prompt,request_id,group_request=None,vision=None,prepare_deadline=None):
        if self.close_task is not None:raise GatewayError('SHUTTING_DOWN')
        await self.cleanup_admission()
        if self.state in ('AUTH_REQUIRED','QUOTA_EXHAUSTED','CLEANUP_FAILED','REMOTE_RESULT_UNKNOWN'):
            raise GatewayError(self.state)
        if self.queue.qsize()>=self.limit+(0 if self.active else 1):raise GatewayError('QUEUE_FULL')
        job=Job(system,prompt,request_id,time.monotonic()+self.wait,asyncio.get_running_loop().create_future())
        job.group_request=group_request
        job.vision=vision
        job.prepare_deadline=prepare_deadline
        if group_request and group_request.get('version')==2:
            try:
                snapshot=json.loads(json.loads(prompt)[-1]['content'])
                target=next(r for r in snapshot['messages'] if r['seq']==snapshot['target_seq'])
                age=target['age_ms']
                if type(age) is int and 0<=age<=900000:job.requested_at-=age/1000
            except (ValueError,TypeError,KeyError,IndexError,StopIteration):pass
        try:self.queue.put_nowait(job)
        except asyncio.QueueFull:raise GatewayError('QUEUE_FULL') from None
        if vision and vision.lease:vision.lease.owned=True
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
            if job.future.cancelled() or job.cancelled.is_set():self.release_image(job);continue
            if time.monotonic()>job.deadline:
                job.future.set_exception(GatewayError('QUEUE_TIMEOUT'));self.release_image(job);continue
            await self.cleanup_admission()
            if self.state in ('AUTH_REQUIRED','QUOTA_EXHAUSTED','CLEANUP_FAILED','REMOTE_RESULT_UNKNOWN'):
                job.future.set_exception(GatewayError(self.state));self.release_image(job);continue
            self.active=True
            if job.group_request and job.group_request.get('kind') in ('group_turn','member_turn') and hasattr(self.runner,'run_group'):
                call=self.runner.run_group(job.system,job.prompt,job.request_id,job.group_request)
            elif job.group_request=={'version':1,'kind':'media_turn'} and hasattr(self.runner,'run_media'):
                call=self.runner.run_media(job.system,job.prompt,job.request_id)
            else:call=self.runner.run(job.system,job.prompt,job.request_id)
            from .vision import CURRENT
            image_token=CURRENT.set(job.vision)
            from .members import PREPARE_DEADLINE
            prep_token=PREPARE_DEADLINE.set(job.prepare_deadline)
            from .web_retrieval import REQUESTED_AT
            from datetime import datetime,timezone
            web_token=REQUESTED_AT.set(datetime.fromtimestamp(job.requested_at,timezone.utc))
            try:task=asyncio.create_task(call)
            finally:
                CURRENT.reset(image_token);PREPARE_DEADLINE.reset(prep_token);REQUESTED_AT.reset(web_token)
            cancel=asyncio.create_task(job.cancelled.wait())
            try:
                done,_=await asyncio.wait((task,cancel),return_when=asyncio.FIRST_COMPLETED)
                if cancel in done and job.cancelled.is_set():
                    task.cancel()
                    outcomes=await asyncio.gather(task,return_exceptions=True)
                    if any(isinstance(e,GatewayError) and e.code in ('CLEANUP_FAILED','REMOTE_RESULT_UNKNOWN') for e in outcomes):self.state=next(e.code for e in outcomes if isinstance(e,GatewayError) and e.code in ('CLEANUP_FAILED','REMOTE_RESULT_UNKNOWN'))
                    continue
                result=await task
                if self.cleanup_status().get('blocked'):raise GatewayError('CLEANUP_FAILED')
                self.state='ready'
                if not isinstance(result,BackendResult) or result.generation_performed:
                    self.last_success=time.time()
                    if self.last_error:self.last_error['historical']=True
                if isinstance(result,BackendResult):self.last_usage=result.usage
                if not job.future.done():job.future.set_result(result)
            except GatewayError as error:
                self.state=error.code
                if not job.future.done():job.future.set_exception(error)
            except asyncio.CancelledError:
                task.cancel();await asyncio.gather(task,return_exceptions=True)
                if self.cleanup_status().get('blocked'):self.state='CLEANUP_FAILED'
                if not job.future.done():job.future.cancel()
                raise
            except Exception:
                self.state='BACKEND_UNAVAILABLE'
                if not job.future.done():job.future.set_exception(GatewayError('BACKEND_UNAVAILABLE'))
            finally:
                cancel.cancel();await asyncio.gather(cancel,return_exceptions=True)
                self.release_image(job);task=None;call=None;done=None
                self.active=False


def application(queue,token,ready_file=None,budget=None,max_reply_chars=1200,root=None,output=None,memes=None,v2=None,materials=None,members=None,vision_status=None):
    budget=budget or InputBudget()
    vision_bytes=0
    output=DEFAULTS | {'max_reply_chars':max_reply_chars} | (output or {})
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
            queue.last_error={'trace':trace,'code':error.code,'time':time.time()}
            if GROUP_REQUEST in request:
                usage_key=request[GROUP_REQUEST].get('addressing',request[GROUP_REQUEST].get('trigger'))+':error'
                queue.group_usage[usage_key]=queue.group_usage.get(usage_key,0)+1
            LOG.warning('REQUEST_FAILED request_id=%s code=%s',trace,error.code)
            if GROUP_REQUEST in request and error.code in MESSAGES and error.code!='UNSUPPORTED_REQUEST':
                from .group_protocol import metadata as group_metadata,SILENT
                from .reply_plan import ReplyPlan
                group=request[GROUP_REQUEST]
                text=MESSAGES[error.code] if group['must_reply'] else SILENT
                plan=ReplyPlan('answer',(text,),text,fallback_reason='gateway_'+error.code.lower()) if group['must_reply'] else None
                response_id='chatcmpl-'+trace
                if group['version']==2:
                    from .turn_v2 import metadata as v2_metadata
                    bound=v2_metadata(group,response_id,'error',plan,request.get(V2_EFFECTIVE,request[V2_SOURCE]))
                else:bound=group_metadata(group,response_id,'error',plan)
                # Keep local errors on the same authenticated result path. No
                # generation/retry, no raw exception text, no missing metadata.
                return web.json_response({'id':response_id,'object':'chat.completion','created':int(time.time()),
                    'model':'workbuddy-local','qqbot_credits':None,'qqbot_gateway_error':error.code,
                    'qqbot_group_plan':bound,
                    'choices':[{'index':0,'message':{'role':'assistant','content':text},'finish_reason':'stop'}]})
            status={'UNSUPPORTED_REQUEST':422,'QUOTA_EXHAUSTED':429,'RATE_LIMITED':429,'QUEUE_FULL':429,
                    'INPUT_TOO_LONG':422,'MODEL_CONFIG_UNSUPPORTED':422,
                    'QUEUE_TIMEOUT':504,'MODEL_TIMEOUT':504,'PROTOCOL_ERROR':502}.get(error.code,503)
            return web.json_response({'error':{'message':MESSAGES[error.code]+'（追踪'+trace+'）','type':'gateway_error','code':error.code}},status=status)

    @web.middleware
    async def ram_release(request,handler):
        try:return await handler(request)
        finally:
            lease=request.get(VISION_LEASE)
            if lease and not lease.owned:lease.release()
    app=web.Application(middlewares=[guard,ram_release],client_max_size=budget.payload_limit)

    async def health(request):
        last_error=dict(queue.last_error) if queue.last_error else None
        if last_error:
            last_error['historical']=bool(last_error.get('historical') or queue.last_success and queue.last_success>last_error.get('time',0))
        current_error=last_error if last_error and not last_error['historical'] else None
        return web.json_response({'alive':True,'backend_state':queue.state,'queue':queue.queue.qsize(),
                                  'stopping':bool(root and stopping(root)),
                                  'current_error':current_error,
                                  'cli_cleanup':queue.cleanup_status(),
                                  'input_budget':budget.limit,'budget_counting':'utf8_visible_bytes_with_envelope',
                                  'overhead_reserve':budget.overhead,'output_reserve':budget.output,
                                  'native_window':'unverified','parameters':getattr(queue.runner,'last_parameters',{}),
                                  'forced_compact_exclusion_verified':False,
                                  'upstream_inference_attempts':'single_native_post' if getattr(queue.runner,'backend',None)=='ollama_ssh' else 'unverified_cli_internal_recovery',
                                  'control_attempts':getattr(queue.runner,'control_attempts',0),
                                  'user_messages_sent':getattr(queue.runner,'user_messages_sent',0),
                                  'backend':getattr(queue.runner,'backend','codebuddy_cli'),
                                  'model':getattr(queue.runner,'model',getattr(queue.runner,'profile',{}).get('model')),
                                  'metadata':getattr(queue.runner,'metadata',{'state':'not_probed'}),
                                  'remote_result_unknown':bool(getattr(queue.runner,'marker',None) and queue.runner.marker.exists()),
                                  'active':queue.active,'cli_attempts':queue.runner.attempts if getattr(queue.runner,'backend','codebuddy_cli')=='codebuddy_cli' else 0,
                                  'backend_attempts':queue.runner.attempts,'local_post_attempts':getattr(queue.runner,'post_attempts',0),
                                  'web_audit':getattr(getattr(queue.runner,'retriever',None),'last_audit',{}),
                                  'web_search_quality_passed':False,
                                  'web_engine':getattr(queue.runner,'web_config',{}).get('engine','gateway'),
                                  'native_web_tools':__import__('qqbot_gateway.cli_web_policy',fromlist=['allowed_tools']).allowed_tools(getattr(queue.runner,'web_config',{})),
                                  'native_web_limits':{k:v for k,v in getattr(queue.runner,'web_config',{}).items() if k.startswith('cli_')},
                                  'thinking_enabled':False,
                                  'memory':{k:settings.get('memory',{}).get(k,False) for k in ('enabled','learning_enabled')},
                                  'vision':vision_status or {'enabled':bool(materials),'quality_state':'unverified'},
                                  'web_search_enabled':getattr(queue.runner,'retriever',None).cfg.get('search_enabled',False) if getattr(queue.runner,'retriever',None) else False,
                                  'web_search_state':'operator_trial_unverified' if getattr(queue.runner,'retriever',None) and queue.runner.retriever.cfg.get('search_enabled') else 'disabled',
                                  'last_usage':queue.last_usage,'credits':None,'credits_state':'unknown',
                                  'group_usage':queue.group_usage,
                                  'last_success':queue.last_success,'real_inference_verified':queue.last_success is not None,
                                  'router_ready':router_ready(),'last_contract':queue.last_shape,'last_error':last_error})

    async def models(request):
        return web.json_response({'object':'list','data':[{'id':'workbuddy-local','object':'model','owned_by':'local'}]})

    async def chat(request):
        nonlocal vision_bytes
        request[TRACE]=uuid.uuid4().hex[:10]
        if root and stopping(root):raise GatewayError('SHUTTING_DOWN')
        try:
            from .reply_plan import _pairs
            payload=json.loads(await request.text(),object_pairs_hook=_pairs)
        except (ValueError,UnicodeError):raise GatewayError('UNSUPPORTED_REQUEST') from None
        from .turn_budget import candidate_instruction
        if isinstance(payload,dict) and isinstance(payload.get('qqbot_request'),dict) and payload['qqbot_request'].get('kind') in ('group_turn','member_turn'):
            from .group_protocol import validate_request
            header=validate_request(payload['qqbot_request'])
            if header['version']==2:
                trace=request.headers.get('X-QQBot-Trace','')
                if not re.fullmatch(r'[a-f0-9]{32}',trace):raise GatewayError('UNSUPPORTED_REQUEST')
                request[TRACE]=trace
                if not v2 or header['mode']!=v2['mode'] or header['config_version']!=v2['config_version']:
                    raise GatewayError('UNSUPPORTED_REQUEST')
                from .turn_v2 import validate_source
                try:
                    content=payload['messages'][-1]['content']
                    if isinstance(content,list):
                        if any(not isinstance(p,dict) or set(p)!={'type','text'} or p['type']!='text' or not isinstance(p['text'],str) for p in content):raise ValueError()
                        content=''.join(p['text'] for p in content)
                    source=validate_source(content,header)
                except (KeyError,IndexError,TypeError,ValueError):raise GatewayError('UNSUPPORTED_REQUEST') from None
                if source['self']['names']!=v2['aliases']:raise GatewayError('UNSUPPORTED_REQUEST')
                if source['memory'] is not None and not v2.get('memory_enabled',False):raise GatewayError('UNSUPPORTED_REQUEST')
                request[V2_SOURCE]=source
            request[GROUP_REQUEST]=header
        suffix=candidate_instruction([]) if memes is not None and memes.cfg['enabled'] else ''
        system,prompt=normalize_request(payload,budget=budget,group_suffix=suffix)
        if payload.get('qqbot_request',{}).get('kind')=='group_turn':request[GROUP_REQUEST]=payload['qqbot_request']
        if not router_ready():raise GatewayError('BACKEND_UNAVAILABLE')
        queue.last_shape=contract_shape(payload)
        LOG.info('REQUEST_ACCEPTED request_id=%s',request[TRACE])
        group_request=payload.get('qqbot_request')
        is_group=bool(group_request and group_request.get('kind') in ('group_turn','member_turn'))
        is_media=group_request=={'version':1,'kind':'media_turn'}
        if is_media and (memes is None or not memes.cfg['enabled']):raise GatewayError('UNSUPPORTED_REQUEST')
        candidates=[]
        native_image=None
        member_receipt=None;prepare_deadline=None
        question=json.loads(prompt)[-1]['content']
        if is_group:
            snapshot=json.loads(question)
            if group_request['version']==2 and len(group_request['resource_caps'])>len(snapshot['images']):
                prepare_deadline=time.monotonic()+15
                try:
                    if members is None:raise ValueError('Member service unavailable')
                    resolved=await members.resolve(group_request,request[V2_SOURCE],prepare_deadline)
                    snapshot['member_candidates']=resolved['candidates']
                    member_receipt=resolved['receipt']
                except (ValueError,TypeError,TimeoutError,OSError,aiohttp.ClientError):
                    snapshot['member_candidates']=[]
                from .members import POLICY as MEMBER_POLICY
                system=system.replace('mention必须null；','')+MEMBER_POLICY
                if not (v2 or {}).get('mentions_enabled',False):system+='本轮受控@关闭，mention必须null。\n'
                from .turn_v2 import fit
                dialog=json.loads(prompt);dialog[-1]['content']=fit(snapshot,group_request,system,budget,suffix,dialog[:-1])
                prompt=json.dumps(dialog,ensure_ascii=False,separators=(',',':'))
                snapshot=json.loads(dialog[-1]['content'])
            if group_request['version']==2 and snapshot['images']:
                from .vision import POLICY,NOTICE,CURRENT,text_budget
                from .turn_v2 import fit
                from .attention import canonical
                deadline=prepare_deadline or time.monotonic()+15
                prepare_deadline=deadline
                try:
                    if materials is None:raise ValueError('MATERIAL_UNAVAILABLE')
                    native_image,descriptor=await asyncio.wait_for(materials.resolve(group_request,snapshot,deadline),max(.001,deadline-time.monotonic()))
                except (ValueError,TypeError,TimeoutError,OSError,aiohttp.ClientError):
                    # No second image or model attempt. Direct produces one
                    # truthful local notice; ambient is silent.
                    from .group_protocol import SILENT
                    from .turn_v2 import metadata as v2_metadata
                    snapshot['images']=[]
                    for row in snapshot['messages']:row['images']=[]
                    request[V2_EFFECTIVE]=snapshot
                    from .reply_plan import ReplyPlan
                    plan=ReplyPlan('answer',(NOTICE,),NOTICE,fallback_reason='local_image_unavailable') if group_request['must_reply'] else None
                    response_id='chatcmpl-'+request[TRACE]
                    text=plan.canonical_text if plan else SILENT
                    meta=v2_metadata(group_request,response_id,'speak' if plan else 'silent',plan,snapshot)
                    return web.json_response(dict(id=response_id,object='chat.completion',created=int(time.time()),model='workbuddy-local',
                        choices=[dict(index=0,message=dict(role='assistant',content=text),finish_reason='stop')],qqbot_group_plan=meta))
                size=len(native_image.blob.data)
                if vision_bytes+size>8*1024*1024:
                    snapshot['images']=[]
                    for row in snapshot['messages']:row['images']=[]
                    request[V2_EFFECTIVE]=snapshot
                    raise GatewayError('INPUT_TOO_LONG')
                from .vision import BlobLease
                from dataclasses import replace
                def release_blob():
                    nonlocal vision_bytes
                    vision_bytes-=size
                lease=BlobLease(release_blob)
                vision_bytes+=size;request[VISION_LEASE]=lease
                native_image=replace(native_image,lease=lease)
                snapshot['images']=[descriptor]
                system=system.replace('当前仅文字聊天','本次可读取当前一张图片并进行文字聊天').replace('、看图','').replace('图片材料/名册/长期记忆尚未接入','名册/长期记忆尚未接入')+POLICY
                image_token=CURRENT.set(native_image)
                try:
                    dialog=json.loads(prompt)
                    dialog[-1]['content']=fit(snapshot,group_request,system,text_budget(budget),suffix,dialog[:-1])
                    prompt=json.dumps(dialog,ensure_ascii=False,separators=(',',':'))
                except GatewayError:
                    snapshot['images']=[]
                    for row in snapshot['messages']:row['images']=[]
                    request[V2_EFFECTIVE]=snapshot
                    raise
                finally:CURRENT.reset(image_token)
                snapshot=json.loads(json.loads(prompt)[-1]['content'])
            if group_request['version']==2:
                from .turn_v2 import fit
                dialog=json.loads(prompt);dialog[-1]['content']=fit(snapshot,group_request,system,budget,suffix,dialog[:-1])
                prompt=json.dumps(dialog,ensure_ascii=False,separators=(',',':'))
                snapshot=json.loads(dialog[-1]['content']);request[V2_EFFECTIVE]=snapshot
            question=next((r['text'] for r in snapshot['messages'] if r['seq']==snapshot.get('target_seq')),snapshot['messages'][-1]['text'])
            if group_request['version']==2:
                from .attention import canonical
                LOG.info('ATTENTION trace=%s stage=snapshot config=%s seq_first=%s seq_last=%s target=%s trimmed_bytes=%s backend=%s model=%s',
                    request[TRACE],group_request['config_version'],snapshot['messages'][0]['seq'],snapshot['messages'][-1]['seq'],snapshot['target_seq'],
                    max(0,len(canonical(request[V2_SOURCE]).encode())-len(json.loads(prompt)[-1]['content'].encode())),
                    getattr(queue.runner,'backend','codebuddy_cli'),getattr(queue.runner,'model',getattr(queue.runner,'profile',{}).get('model','unknown')))
        if memes is not None and memes.cfg['enabled'] and (is_group or is_media):
            candidates=memes.candidates((snapshot.get('meme_question') or '') if is_group and group_request['version']==2 else question)
            while True:
                instruction=candidate_instruction(candidates)
                final_budget=budget
                if native_image:
                    from dataclasses import replace
                    final_budget=replace(budget,limit=budget.limit-native_image.reserve)
                if final_budget.usage(system+instruction,prompt)<=final_budget.limit:break
                if not candidates:raise GatewayError('INPUT_TOO_LONG')
                candidates.pop()
            system+=instruction
        started=time.monotonic()
        result=await queue.submit(system,prompt,request[TRACE],group_request,vision=native_image,prepare_deadline=prepare_deadline)
        backend_result=result if isinstance(result,BackendResult) else BackendResult(result)
        result=backend_result.text
        response_id='chatcmpl-'+request[TRACE]
        metadata={}
        if is_group:
            from .group_protocol import group_plan,metadata as group_metadata,SILENT
            snapshot=json.loads(json.loads(prompt)[-1]['content'])
            question=next((row['text'] for row in snapshot['messages'] if row['seq']==snapshot.get('target_seq')),snapshot['messages'][-1]['text'])
            response_to=None
            memory_proposals=list(backend_result.memory_proposals)
            if backend_result.prepared_plan is not None:
                plan=backend_result.prepared_plan
                response_to=backend_result.response_to_seq
                decision='speak'
            elif backend_result.web_expired:
                decision,plan=group_plan('',output,'',group_request['must_reply'])
            else:
                if group_request['version']==2:
                    from .turn_v2 import plan as v2_plan
                    decision,plan,response_to=v2_plan(result,output,question,group_request,snapshot,memes,candidates,memory_out=memory_proposals)
                elif memes is not None and memes.cfg['enabled']:
                    from .media_protocol import media_plan
                    decision,plan=media_plan(result,output,question,memes,candidates,group=True,must_reply=group_request['must_reply'])
                else:decision,plan=group_plan(result,output,question,group_request['must_reply'])
            result=plan.canonical_text if plan else SILENT
            limited=plan.limited if plan else False
            if group_request['version']==2:
                from .turn_v2 import metadata as v2_metadata
                if plan and not (v2 or {}).get('mentions_enabled',False):
                    from dataclasses import replace
                    plan=replace(plan,prepared_parts=tuple(replace(p,mention_ref=None) for p in plan.parts)) if any(p.mention_ref for p in plan.parts) else plan
                if not (v2 or {}).get('learning_enabled',False) or backend_result.web_evidence:memory_proposals=[]
                metadata['qqbot_group_plan']=v2_metadata(group_request,response_id,decision,plan,snapshot,response_to,member_receipt,memory_proposals,backend_result.web_evidence)
                LOG.info('ATTENTION trace=%s stage=model_done decision=%s elapsed_ms=%s',request[TRACE],decision,int((time.monotonic()-started)*1000))
            else:metadata['qqbot_group_plan']=group_metadata(group_request,response_id,decision,plan)
            queue.last_usage=dict(queue.last_usage,trigger=group_request.get('addressing',group_request.get('trigger')),decision=decision)
            usage_key=group_request.get('addressing',group_request.get('trigger'))+':'+decision
            queue.group_usage[usage_key]=queue.group_usage.get(usage_key,0)+1
            if backend_result.generation_performed:
                generated_key=group_request.get('addressing',group_request.get('trigger'))+':generations'
                queue.group_usage[generated_key]=queue.group_usage.get(generated_key,0)+1
        elif is_media and not backend_result.web_expired:
            from .media_protocol import media_plan
            plan=backend_result.prepared_plan
            if plan is None:_,plan=media_plan(result,output,question,memes,candidates)
            result,limited=plan.canonical_text,plan.limited
            metadata['qqbot_reply_plan']=plan.metadata(response_id)
        elif backend_result.web_expired:
            metadata['qqbot_web_expired']=True
            limited=False
        elif backend_result.prepared_plan is not None:
            plan=backend_result.prepared_plan
            result,limited=plan.canonical_text,plan.limited
            if output['delivery_mode']=='adaptive':metadata['qqbot_reply_plan']=plan.metadata(response_id)
        elif output['delivery_mode']=='adaptive':
            question=json.loads(prompt)[-1]['content']
            plan=make_reply_plan(result,output,question)
            result,limited=plan.canonical_text,plan.limited
            metadata['qqbot_reply_plan']=plan.metadata(response_id)
        else:
            result,limited=prepare_reply(result,max_reply_chars)
        return web.json_response({'id':response_id,'object':'chat.completion','created':int(time.time()),
            'model':'workbuddy-local','qqbot_backend_usage':backend_result.usage,'qqbot_credits':None,'choices':[{'index':0,'message':{'role':'assistant','content':result},
                                               'finish_reason':'length' if limited or backend_result.finish_reason=='length' else 'stop'}],**metadata})

    app.router.add_get('/health',health)
    app.router.add_get('/v1/models',models)
    app.router.add_post('/v1/chat/completions',chat)
    async def start(app):
        if hasattr(queue.runner,'preflight'):await queue.runner.preflight()
        if getattr(queue.runner,'marker',None) and queue.runner.marker.exists():queue.state='REMOTE_RESULT_UNKNOWN'
        await queue.start()
    async def close(app):await queue.close()
    app.on_startup.append(start);app.on_cleanup.append(close)
    return app


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--root');args=parser.parse_args()
    from .config_files import load_consumer,management_root
    path=Path(args.config).absolute();root=management_root(path,args.root or os.environ.get('QQBOT_ROOT'))
    settings=load_consumer(root,path)
    llm=settings['llm']
    if llm['host']!='127.0.0.1' or llm['max_concurrency']!=1:
        raise ValueError('Restricted local CLI configuration required')
    tokens=json.loads((root/settings['secrets_file']).read_text(encoding='utf-8'))
    budget=InputBudget.from_settings(settings,validate_model_settings(settings))
    from .vision import require_production
    require_production(settings,root=root)
    runner=create_runner(root,settings,budget)
    from .web_retrieval import WebRunner, Retriever
    ids=[settings['bot']['qq']]+sum((settings['access'][k] for k in ('allowed_groups','admin_users','blocked_users')),[])
    runner=WebRunner(runner,Retriever(settings['web'],ids,network=settings['public_network'],root=root,bilibili=settings['bilibili'],aliases=settings['participation']['attention']['aliases']),budget,settings['output'],root)
    runner.allow_ambient_web=settings['participation']['allow_ambient_web']
    from .meme_catalog import MemeCatalog
    memes=MemeCatalog(root,settings['memes'])
    runner.memes=memes
    queue=ModelQueue(runner,llm['queue_limit'],llm['queue_wait_seconds'])
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    from .members import suspend_unverified,MemberClient
    settings['members']=suspend_unverified(settings)
    v2=None
    if settings['participation']['mode']=='free' and settings['participation']['attention']['enabled'] or settings['vision']['enabled'] or settings['members']['enabled'] or settings['memory']['enabled'] or settings['bilibili']['enabled']:
        from .persona import compose_persona,session_version
        from .reply_plan import digest
        persona=compose_persona((root/'config/persona.md').read_text(encoding='utf-8'),settings['output'],settings['web'],settings['participation'],settings['memes'],settings.get('vision'),settings['members'],settings['memory'],settings.get('bilibili'))
        persona_id=session_version(persona+('\n'+memes.fingerprint() if memes.cfg['enabled'] else ''),settings)
        v2=dict(mode=settings['participation']['mode'],config_version=digest(persona_id),aliases=settings['participation']['attention']['aliases'],mentions_enabled=settings['members']['mentions_enabled'],memory_enabled=settings['memory']['enabled'],learning_enabled=settings['memory']['learning_enabled'])
    from .vision import MaterialClient,context_token
    materials=MaterialClient(f"http://127.0.0.1:{settings['onebot']['port']}/context/vision/resolve",context_token(root),settings['vision']['input_reserve_tokens']) if settings['vision']['enabled'] else None
    member_client=MemberClient(f"http://127.0.0.1:{settings['onebot']['port']}/context/members",context_token(root)) if settings['members']['enabled'] else None
    vision_status={'enabled':settings['vision']['enabled']}
    if settings['vision']['enabled']:
        from .vision_capabilities import read_json
        active=read_json(root/'state/vision-evidence/active.json')
        vision_status.update(acceptance_mode=active.get('acceptance_mode','fixed_iq'),
            quality_state='pending_user_test' if active.get('acceptance_mode')=='lap43_operator_trial' else 'prior_acceptance')
    web.run_app(application(queue,tokens['model_gateway'],root/'state/router-ready.json',budget,settings['output']['max_reply_chars'],root,settings['output'],memes,v2,materials,member_client,vision_status),host=llm['host'],port=llm['port'],
                access_log=None,handler_cancellation=True)


if __name__ == '__main__':
    from .config_files import ConfigError
    import sys
    try:main()
    except ConfigError as error:
        print(str(error),file=sys.stderr)
        raise SystemExit(1) from None
