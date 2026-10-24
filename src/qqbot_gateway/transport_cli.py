"""Stopped, finite provider transactions. No runtime qualification is created here."""
import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import secrets
import re
import uuid
import yaml

from .config import configuration_lock, require_stopped
from .config_files import read_project, validate, sha, safe_mkdir, plain_path, parse, LAYOUT, KNOWN
from .lifecycle import atomic_json
from .qq_transport import resolve_transport, checked_path, inspect_transport
from .transport_owner import require_runtime, read_json
from .transport_supervisor import RecoveryLedger

AREA = 'state/qq-transport/'


def _yaml(content):
    """Strict transaction/backup parser: no snippets, aliases, tags or duplicate keys."""
    try:
        text=content.decode('utf-8-sig')
        for event in yaml.parse(text,Loader=yaml.SafeLoader):
            if isinstance(event,yaml.AliasEvent) or getattr(event,'anchor',None) or getattr(event,'tag',None):raise ValueError()
        node=yaml.compose(text,Loader=yaml.SafeLoader)
        def check(value):
            if isinstance(value,yaml.MappingNode):
                seen=set()
                for key,child in value.value:
                    if not isinstance(key,yaml.ScalarNode) or key.tag!='tag:yaml.org,2002:str' or key.value in seen or key.value=='<<':raise ValueError()
                    seen.add(key.value);check(child)
            elif isinstance(value,yaml.SequenceNode):
                for child in value.value:check(child)
        if not isinstance(node,yaml.MappingNode):raise ValueError()
        check(node)
        return yaml.safe_load(text)
    except (yaml.YAMLError,UnicodeError,ValueError,TypeError,RecursionError):raise ValueError('TRANSACTION_YAML_INVALID') from None


def _new(path, content):
    with path.open('xb') as stream:
        stream.write(content);stream.flush();os.fsync(stream.fileno())


def prepare(root):
    root=Path(root).resolve()
    with configuration_lock(root) as lease:
        require_stopped(root);config=read_project(root)
        base=safe_mkdir(root,root/AREA)
        intent=base/'prepare-intent.local.json'
        if intent.exists() or (base/'candidate.local.json').exists():raise ValueError('PREPARE_ALREADY_STARTED')
        keypath=checked_path(root,resolve_transport(config.settings)['snowluma']['control_secret_file'],'secrets')
        if keypath.exists():raise ValueError('CONTROL_SECRET_EXISTS')
        # Intent is deliberately never removed on failure: retry cannot wash budgets.
        _new(intent,b'{"format":"qqbot-prepare-intent-v1"}')
        RecoveryLedger(root).initialize(lease)
        safe_mkdir(root,keypath.parent)
        _new(keypath,json.dumps(dict(schema=1,key=secrets.token_hex(32))).encode())
        source=Path(__file__).resolve().parents[2]/'adapters/snowluma/project_policy.mjs'
        policy=source.read_bytes()
        _new(base/'project_policy.mjs',policy)
        atomic_json(base/'candidate.local.json',dict(format='qqbot-candidate-v1',source_digest=config.source_digest,
            policy_sha256=sha(policy),runtime_qualified=False))
        return dict(prepared=True,runtime_qualified=False,channel_ready=False)


def _provider(content, value, *, remove_empty=False):
    """Edit one scalar via source marks; all unrelated bytes/comments survive."""
    _yaml(content)
    text=content.decode('utf-8-sig');bom=b'\xef\xbb\xbf' if content.startswith(b'\xef\xbb\xbf') else b''
    node=yaml.compose(text,Loader=yaml.SafeLoader)
    sections=[(k,v) for k,v in node.value if k.value=='qq_transport']
    newline='\r\n' if '\r\n' in text else '\n'
    if not sections:
        if value is None:return content
        return bom+(text+('' if not text or text.endswith('\n') else newline)+'qq_transport:'+newline+'  provider: '+value+newline).encode()
    key,section=sections[0]
    if not isinstance(section,yaml.MappingNode) or section.flow_style:raise ValueError('CONFIG_EDIT_UNSUPPORTED')
    fields=[(k,v) for k,v in section.value if k.value=='provider']
    if fields:
        k,v=fields[0]
        if value is not None:text=text[:v.start_mark.index]+value+text[v.end_mark.index:]
        else:
            start=text.rfind('\n',0,k.start_mark.index)+1
            end=text.find('\n',v.end_mark.index);end=len(text) if end<0 else end+1
            if remove_empty and len(section.value)==1:start=text.rfind('\n',0,key.start_mark.index)+1
            text=text[:start]+text[end:]
    elif value is not None:
        at=section.start_mark.index
        # Insert before the first child, preserving its leading indentation.
        start=text.rfind('\n',0,at)+1
        text=text[:start]+' '*section.start_mark.column+'provider: '+value+newline+text[start:]
    return bom+text.encode()


def _target(root,config):
    return plain_path(root,root/('config/local/runtime.yaml' if config.layout=='split' else 'config/settings.local.yaml'))


def _validate_bytes(root,config,content,expected):
    if config.layout=='legacy':raw=_yaml(content)
    else:
        raw={}
        for name in LAYOUT:
            raw.update(parse(content if name=='runtime.yaml' else (root/'config/local'/name).read_bytes(),name))
        if raw.pop('layout_version',None)!=1:raise ValueError('CONFIG_EDIT_UNSUPPORTED')
        extensions=raw.pop('legacy_extensions',{})
        if any(k in KNOWN for k in extensions):raise ValueError('CONFIG_EDIT_UNSUPPORTED')
        raw.update(extensions)
    if validate(root,raw)!=validate(root,expected):raise ValueError('CONFIG_EDIT_SEMANTICS_CHANGED')


def activate(root, *, qualify=require_runtime, before_publish=lambda:None):
    root=Path(root).resolve()
    with configuration_lock(root):
        require_stopped(root);config=read_project(root)
        qualify(root,config.settings)  # production always refuses before any transaction/state write
        RecoveryLedger(root).read()
        candidate=read_json(root,AREA+'candidate.local.json','state')
        if (set(candidate)!={'format','source_digest','policy_sha256','runtime_qualified'} or
            candidate['format']!='qqbot-candidate-v1' or candidate['runtime_qualified'] is not False or
            candidate['source_digest']!=config.source_digest or
            sha(plain_path(root,root/(AREA+'project_policy.mjs')).read_bytes())!=candidate['policy_sha256']):raise ValueError('CANDIDATE_SOURCE_CHANGED')
        path=_target(root,config);original=path.read_bytes()
        if len(original)>128*1024:raise ValueError('CONFIG_EDIT_UNSUPPORTED')
        raw=_yaml(original);prior=raw.get('qq_transport',{})
        before=prior.get('provider');section_present='qq_transport' in raw
        if before=='snowluma':raise ValueError('PROVIDER_ALREADY_SELECTED')
        changed=_provider(original,'snowluma')
        proposed=deepcopy(config.settings);proposed.setdefault('qq_transport',{})['provider']='snowluma';validate(root,proposed)
        _validate_bytes(root,config,changed,proposed)
        ledgerpath=root/(AREA+'activation.local.json')
        if ledgerpath.exists():raise ValueError('ACTIVATION_EXISTS')
        ledger=dict(format='qqbot-activation-v1',phase='prepared',path=str(path.relative_to(root)).replace('\\','/'),
            source_digest=config.source_digest,original=base64.b64encode(original).decode(),before=before,
            section_present=section_present,applied_sha256=sha(changed))
        atomic_json(ledgerpath,ledger)
        before_publish();require_stopped(root)
        if read_project(root).source_digest!=config.source_digest or path.read_bytes()!=original:raise ValueError('CONFIG_SOURCE_CHANGED')
        temp=path.with_name('.transport-'+uuid.uuid4().hex+'.tmp')
        try:_new(temp,changed);os.replace(temp,path)
        finally:temp.unlink(missing_ok=True)
        ledger['phase']='applied';atomic_json(ledgerpath,ledger)
        return dict(activated=True,restarted=False)


def rollback(root,*,stop=None):
    root=Path(root).resolve()
    # Only an activation owned by this task plus a completed trial instance can
    # request the existing manual management stop. Unknown/partial records cannot.
    with configuration_lock(root):
        activation=read_json(root,AREA+'activation.local.json','state',limit=256*1024)
        if activation.get('format')!='qqbot-activation-v1' or activation.get('phase')!='applied':raise ValueError('ROLLBACK_UNKNOWN')
        marker=root/(AREA+'trial-request.local.json')
        request=read_json(root,AREA+'trial-request.local.json','state') if marker.exists() else None
        if request is not None:
            if (set(request)!={'format','source_digest','instance_id'} or request['format']!='qqbot-trial-request-v1' or
                not isinstance(request['instance_id'],str) or not re.fullmatch('[a-f0-9]{32}',request['instance_id'])):raise ValueError('TRIAL_STOP_UNKNOWN')
    if request is not None:
        if stop is None:
            from scripts import manage
            if root!=manage.ROOT:raise ValueError('TRIAL_MANAGEMENT_ROOT_UNKNOWN')
            stop=manage.stop_project
        stop(expected_instance=request['instance_id'])
    with configuration_lock(root):
        require_stopped(root);config=read_project(root)
        ledger=read_json(root,AREA+'activation.local.json','state',limit=256*1024)
        if set(ledger)!={'format','phase','path','source_digest','original','before','section_present','applied_sha256'} or ledger['format']!='qqbot-activation-v1' or ledger['phase']!='applied':raise ValueError('ROLLBACK_UNKNOWN')
        path=_target(root,config)
        if str(path.relative_to(root)).replace('\\','/')!=ledger['path']:raise ValueError('ROLLBACK_LAYOUT_CHANGED')
        content=path.read_bytes();raw=_yaml(content)
        if raw.get('qq_transport',{}).get('provider')!='snowluma':raise ValueError('ROLLBACK_OWNED_FIELD_CHANGED')
        if ledger['before'] not in (None,'napcat') or type(ledger['section_present']) is not bool:raise ValueError('ROLLBACK_UNKNOWN')
        original=base64.b64decode(ledger['original'],validate=True)
        original_raw=_yaml(original)
        if (not isinstance(original_raw,dict) or ('qq_transport' in original_raw)!=ledger['section_present'] or
            original_raw.get('qq_transport',{}).get('provider')!=ledger['before'] or
            sha(_provider(original,'snowluma'))!=ledger['applied_sha256']):raise ValueError('ROLLBACK_UNKNOWN')
        changed=original if sha(content)==ledger['applied_sha256'] else _provider(content,ledger['before'],remove_empty=not ledger['section_present'])
        proposed=deepcopy(config.settings)
        if ledger['before'] is None:
            proposed['qq_transport'].pop('provider',None)
            if not ledger['section_present'] and not proposed['qq_transport']:proposed.pop('qq_transport')
        else:proposed['qq_transport']['provider']=ledger['before']
        validate(root,proposed)
        _validate_bytes(root,config,changed,proposed)
        if read_project(root).source_digest!=config.source_digest:raise ValueError('CONFIG_SOURCE_CHANGED')
        temp=path.with_name('.transport-'+uuid.uuid4().hex+'.tmp')
        try:_new(temp,changed);os.replace(temp,path)
        finally:temp.unlink(missing_ok=True)
        ledger['phase']='rolled_back';atomic_json(root/(AREA+'activation.local.json'),ledger)
        return dict(rolled_back=True,restarted=False)


def blocked_runtime(root):
    config=read_project(root);require_runtime(root,config.settings)
    raise ValueError('PRIVATE_RUNTIME_ENTRY_UNAVAILABLE')


def offline(root):
    """Original pure fixtures, with production qualifications separately reported."""
    from .transport_health import HealthBinding, HealthProducer, HealthVerifier
    binding=HealthBinding('a'*32,'b'*64,'c'*64,'d'*64,'e'*64,1,1000,2,1001,5098)
    key=bytes(range(32));clock=lambda:10.0
    producer=HealthProducer(binding,key)
    verifier=HealthVerifier(binding,key,lambda _:True,clock=clock)
    nonce=verifier.challenge()
    observation=dict(phase='ready',rx_watch_armed=True,pipe_connected=True,logged_in=True,account_match=True,
        receive_healthy=True,outbound_healthy=True,last_rx_age_ms=0)
    response=producer.response(nonce,observation)
    if not verifier.accept(response) or not verifier.ready():raise ValueError('OFFLINE_FIXTURE_FAILED')
    verifier.challenge()
    if verifier.accept(response):raise ValueError('OFFLINE_FIXTURE_FAILED')
    nonce=verifier.challenge();forged=bytearray(producer.response(nonce,observation));forged[-3]^=1
    if verifier.accept(bytes(forged)):raise ValueError('OFFLINE_FIXTURE_FAILED')
    nonce=verifier.challenge()
    if not verifier.accept(producer.response(nonce,observation)):raise ValueError('OFFLINE_FIXTURE_FAILED')
    verifier.clock=lambda:26.0
    if verifier.ready():raise ValueError('OFFLINE_FIXTURE_FAILED')
    result=inspect_transport(root,read_project(root).settings)
    return dict(offline_passed=True,fixtures=4,private_wiring_verified=False,real_verified=False,
        channel_ready=False,evidence=result)


def trial_start(root,*,qualify=require_runtime,start=None):
    root=Path(root).resolve()
    with configuration_lock(root):
        require_stopped(root);config=read_project(root)
        if resolve_transport(config.settings)['provider']!='snowluma':raise ValueError('TRIAL_PROVIDER_NOT_SELECTED')
        qualify(root,config.settings)
        RecoveryLedger(root).read()
        marker=root/(AREA+'trial-request.local.json')
        if marker.exists():raise ValueError('TRIAL_ALREADY_REQUESTED')
        request=dict(format='qqbot-trial-request-v1',source_digest=config.source_digest,instance_id=None)
        atomic_json(marker,request)
    # Existing management acquires its own lock; never wait for gate startup while holding ours.
    if start is None:
        from scripts import manage
        if root!=manage.ROOT:raise ValueError('TRIAL_MANAGEMENT_ROOT_UNKNOWN')
        start=manage.start_channel
    result=start(full=True,expected_source_digest=config.source_digest)
    if (not isinstance(result,dict) or result.get('provider')!='snowluma' or not isinstance(result.get('instance_id'),str) or
        not re.fullmatch('[a-f0-9]{32}',result['instance_id'])):raise ValueError('TRIAL_START_UNKNOWN')
    with configuration_lock(root):
        if read_json(root,AREA+'trial-request.local.json','state')!=request:raise ValueError('TRIAL_START_UNKNOWN')
        request['instance_id']=result['instance_id'];atomic_json(marker,request)
    return dict(requested=True,channel_ready=False,real_verified=False)
