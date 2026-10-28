from dataclasses import dataclass
from pathlib import Path
import json
import re
from urllib.parse import urlparse
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import os
import tempfile
import time
import uuid
import threading

import yaml
import psutil


def export_legacy_config(path):
    """Stopped, locked review artifact only. Never activates or restarts anything.

    Return both digests so a later operator can detect edits to either snapshot.
    Unknown extensions and all legacy settings are preserved verbatim in meaning.
    """
    from .config_files import reject_legacy_write
    path=Path(path);root=reject_legacy_write(path)
    with configuration_lock(root):
        reject_legacy_write(path)
        require_stopped(root)
        value,source_digest=read_settings(path)
        original=path.read_bytes()
        if hashlib.sha256(original).hexdigest()!=source_digest:raise ValueError('Configuration changed')
        if isinstance(value.get('participation'),dict):
            value['participation'].pop('attention',None)
            value['participation'].pop('silence',None)
        value.pop('vision',None)
        value.pop('members',None)
        value.pop('memory',None)
        value.pop('bilibili',None)
        content=yaml.safe_dump(value,allow_unicode=True,sort_keys=False).encode('utf-8')
        directory=root/'state/config-exports';directory.mkdir(parents=True,exist_ok=True)
        tag=uuid.uuid4().hex
        backup=directory/(tag+'.original.yaml');review=directory/(tag+'.legacy.yaml')
        with backup.open('xb') as f:f.write(original)
        with review.open('xb') as f:f.write(content)
        copy_digest=hashlib.sha256(content).hexdigest()
        if (hashlib.sha256(path.read_bytes()).hexdigest()!=source_digest or
            hashlib.sha256(review.read_bytes()).hexdigest()!=copy_digest):raise ValueError('Export changed')
        return dict(source_digest=source_digest,legacy_digest=copy_digest,backup=str(backup),review=str(review),activated=False)


def activate_legacy_config(path,review,source_digest,legacy_digest,confirmation):
    """Explicit operator-confirmed activation, stopped + lock + both digests.

    Does not roll back code, erase unresolved markers, or start any service.
    """
    from .config_files import reject_legacy_write
    path=Path(path);root=reject_legacy_write(path);review=Path(review).resolve()
    if confirmation!='已核对' or review.parent!=(root/'state/config-exports').resolve():raise ValueError('Review required')
    if not all(isinstance(v,str) and re.fullmatch('[a-f0-9]{64}',v) for v in (source_digest,legacy_digest)):raise ValueError('Both digests required')
    with configuration_lock(root):
        reject_legacy_write(path)
        require_stopped(root)
        original=path.read_bytes();content=review.read_bytes()
        if hashlib.sha256(original).hexdigest()!=source_digest or hashlib.sha256(content).hexdigest()!=legacy_digest:raise ValueError('Configuration changed')
        data=yaml.safe_load(content);normalize_settings(data)
        if 'silence' in data.get('participation',{}) or 'attention' in data.get('participation',{}) or 'vision' in data or 'members' in data or 'memory' in data or 'bilibili' in data:raise ValueError('Not legacy compatible')
        backup=review.with_name(review.stem+'.activation-original.yaml')
        with backup.open('xb') as f:f.write(original)
        temporary=path.with_name(path.name+'.legacy-'+uuid.uuid4().hex+'.tmp')
        try:
            with temporary.open('xb') as f:f.write(content)
            if (hashlib.sha256(path.read_bytes()).hexdigest()!=source_digest or
                hashlib.sha256(review.read_bytes()).hexdigest()!=legacy_digest):raise ValueError('Configuration changed')
            os.replace(temporary,path)
        finally:
            if temporary.exists():temporary.unlink()
        return dict(activated=True,legacy_digest=legacy_digest,restarted=False)


def qq_id(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    text = str(value)
    return text if re.fullmatch(r'[1-9][0-9]{0,19}', text) else None


@dataclass(frozen=True)
class GateConfig:
    bot_qq: str
    allowed_groups: frozenset[str]
    admin_users: frozenset[str]
    inbound_token: str
    upstream_token: str
    database: Path
    upstream: str = 'ws://127.0.0.1:6199/ws'
    host: str = '127.0.0.1'
    port: int = 6200
    blocked_users: frozenset[str] = frozenset()
    participation_mode: str = 'mentions'
    attention_enabled: bool = False
    media_catalog: object = None
    vision_enabled: bool = False
    ingress_diagnostics: bool = False
    members_enabled: bool = False
    members_config: object = None
    public_network: object = None
    silence_enabled: bool = True
    silence_aliases: tuple = ('肥鱼','大肥鱼','鱼鱼','鲸鱼娘','小鲸鱼','DSH')
    session_queue_timeout_seconds: int = 600
    message_max_chars: int = 2000
    transport_provider: str = 'napcat'
    transport_instance_id: str = ''
    transport_config_digest: str = ''
    transport_control_port: int = 5098
    transport_health_ttl: int = 15
    transport_health_poll: int = 5
    transport_ready_timeout: int = 180

    def __post_init__(self):
        if type(self.transport_ready_timeout) is not int or not 60<=self.transport_ready_timeout<=240:
            raise ValueError('Invalid transport ready timeout')
        if self.transport_provider not in ('napcat','snowluma'):raise ValueError('Invalid transport provider')
        if (type(self.transport_health_poll) is not int or not 5<=self.transport_health_poll<=10 or
            type(self.transport_health_ttl) is not int or not 3*self.transport_health_poll<=self.transport_health_ttl<=30 or
            type(self.transport_control_port) is not int or not 1<=self.transport_control_port<=65535):
            raise ValueError('Invalid transport health configuration')
        if type(self.silence_enabled) is not bool:raise ValueError('Invalid silence enabled')
        if self.participation_mode not in ('mentions','free'):raise ValueError('Invalid participation mode')
        if not qq_id(self.bot_qq) or not self.allowed_groups or not self.admin_users:
            raise ValueError('Bot, allowed groups and admins must be nonempty')
        if len(self.admin_users)!=1 or self.bot_qq in self.admin_users or self.admin_users & self.blocked_users:
            raise ValueError('Exactly one distinct, unblocked operator is required')
        if any(not qq_id(x) for x in self.allowed_groups | self.admin_users | self.blocked_users):
            raise ValueError('Invalid QQ/group ID')
        if self.host != '127.0.0.1' or not 0 < self.port < 65536:
            raise ValueError('Gate must listen on loopback')
        url = urlparse(self.upstream)
        if (url.scheme != 'ws' or url.hostname != '127.0.0.1' or
                url.path != '/ws' or not url.port or url.username or url.password or url.query or url.fragment):
            raise ValueError('Upstream must be a loopback WS /ws endpoint')
        if any(not isinstance(t, str) or len(t) < 32 for t in (self.inbound_token, self.upstream_token)):
            raise ValueError('Missing local transport token')


def normalize_settings(raw):
    """Validate a complete snapshot without rewriting the source or losing extensions."""
    if not isinstance(raw, dict):
        raise ValueError('Configuration must be a mapping')
    data = deepcopy(raw)
    version = data.get('schema_version', 1)
    if type(version) is not int or version not in (1, 2, 3):
        raise ValueError('Unsupported schema_version')
    data['schema_version'] = 3
    from .group_memory import validate_config as validate_memory
    data['memory']=validate_memory(data.get('memory',{}))
    from .members import validate_config as validate_members
    data['members']=validate_members(data.get('members',{}))
    from .vision import validate_config
    data['vision']=validate_config(data.get('vision',{}))
    from .public_network import validate_network
    data['public_network']=validate_network(data.get('public_network',{}))
    from .web_policy import validate_web
    data['web'] = validate_web(data.get('web', {}))
    if data['web']['engine']=='codebuddy_cli' and data.get('llm',{}).get('backend')!='codebuddy_cli':
        raise ValueError('Native web requires codebuddy_cli backend')
    from .bilibili_policy import validate as validate_bilibili
    data['bilibili']=validate_bilibili(data.get('bilibili',{}),data['web'])
    from .participation import validate_participation
    data['participation']=validate_participation(data.get('participation',{}))
    from .meme_catalog import validate_memes
    data['memes']=validate_memes(data.get('memes',{}))
    for section in ('bot', 'access', 'onebot', 'llm', 'chat', 'output'):
        data.setdefault(section, {})
        if not isinstance(data[section], dict):
            raise ValueError(f'{section} must be a mapping')
    bot, access, onebot, llm = (data[k] for k in ('bot', 'access', 'onebot', 'llm'))
    bot['qq'] = qq_id(bot.get('qq'))
    if bot['qq'] is None:
        raise ValueError('Invalid bot.qq')
    for key in ('allowed_groups', 'admin_users', 'blocked_users'):
        values = access.get(key, [] if key == 'blocked_users' else None)
        if not isinstance(values, list) or any(qq_id(v) is None for v in values):
            raise ValueError(f'access.{key} must be a list of numeric IDs')
        access[key] = list(dict.fromkeys(qq_id(v) for v in values))
        if key != 'blocked_users' and not access[key]:
            raise ValueError(f'access.{key} must not be empty')
    if len(access['admin_users'])!=1 or bot['qq'] in access['admin_users'] or set(access['admin_users']) & set(access['blocked_users']):
        raise ValueError('Exactly one distinct, unblocked operator is required')
    if access.get('private_enabled') is not False:
        raise ValueError('Private messages must be disabled')
    if onebot.get('host') != '127.0.0.1':
        raise ValueError('OneBot must listen on loopback')
    try:
        if not isinstance(onebot.get('upstream'), str):
            raise ValueError('Invalid upstream')
        url = urlparse(onebot['upstream'])
        valid = (url.scheme == 'ws' and url.hostname == '127.0.0.1' and url.path == '/ws'
                 and url.port and not (url.username or url.password or url.query or url.fragment))
    except ValueError:
        valid = False
    if not valid:
        raise ValueError('Upstream must be a loopback WS /ws endpoint')
    if llm.get('backend') not in ('codebuddy_cli', 'ollama_ssh') or llm.get('host') != '127.0.0.1' or type(llm.get('max_concurrency')) is not int or llm['max_concurrency'] != 1:
        raise ValueError('Restricted local backend configuration required')
    chat, output = data['chat'], data['output']
    from .backends import CLI_DEFAULTS, OLLAMA_DEFAULTS, BUDGET_DEFAULTS
    profiles = llm.setdefault('profiles', {})
    if not isinstance(profiles, dict):raise ValueError('profiles must be a mapping')
    for name, defaults in (('codebuddy_cli', CLI_DEFAULTS), ('ollama_ssh', OLLAMA_DEFAULTS)):
        profile = profiles.setdefault(name, {})
        if not isinstance(profile, dict):raise ValueError('profile must be a mapping')
        if name == 'codebuddy_cli':
            for key in ('model','reasoning_effort','context_window_tokens','run_timeout_seconds'):
                if key in llm:
                    if version == 3 or (key in profile and profile[key] != llm[key]):
                        raise ValueError('Conflicting legacy/profile value: '+key)
                    profile[key] = llm.pop(key)
        budget = profile.setdefault('input_budget', {})
        if not isinstance(budget, dict):raise ValueError('input_budget must be a mapping')
        if name == 'codebuddy_cli':
            for key in BUDGET_DEFAULTS:
                if key in chat:
                    if version == 3 or (key in budget and budget[key] != chat[key]):
                        raise ValueError('Conflicting legacy/profile budget: '+key)
                    budget[key] = chat.pop(key)
        for key, value in defaults.items():
            if key != 'input_budget':profile.setdefault(key, deepcopy(value))
        for key, value in defaults['input_budget'].items():budget.setdefault(key, value)
        if not isinstance(profile['model'], str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}', profile['model']):
            raise ValueError('Invalid profile model')
        for key, lower, upper in (('context_input_limit_tokens',1024,1048576),('context_overhead_reserve_tokens',0,65536),('output_reserve_tokens',0,65536)):
            if type(budget[key]) is not int or not lower <= budget[key] <= upper:raise ValueError('Invalid input_budget '+key)
        if type(profile['run_timeout_seconds']) is not int or not 1 <= profile['run_timeout_seconds'] <= 3600:raise ValueError('Invalid run timeout')
    cli, local = profiles['codebuddy_cli'], profiles['ollama_ssh']
    if cli['reasoning_effort'] not in ('auto','minimal','low','medium','high','xhigh','max'):raise ValueError('Invalid reasoning_effort')
    for key, lower, upper in (('num_ctx',4096,32768),('num_predict',128,4096),('keep_alive_seconds',0,1800),('top_k',1,100)):
        if type(local[key]) is not int or not lower <= local[key] <= upper:raise ValueError('Invalid local '+key)
    import math
    for key, lower, upper in (('temperature',0,2),('top_p',0,1)):
        if type(local[key]) not in (int,float) or not math.isfinite(local[key]) or not lower <= local[key] <= upper or (key == 'top_p' and local[key] == 0):raise ValueError('Invalid local '+key)
    if local['think'] is not False:raise ValueError('Only think:false supported')
    if local['model'].lower().endswith((':cloud','-cloud')) or ':' not in local['model'] or local['model'].endswith(':latest'):raise ValueError('Explicit installed local model tag required')
    digest = local['expected_digest']
    if digest is not None and (not isinstance(digest,str) or not re.fullmatch(r'[a-f0-9]{64}',digest)):raise ValueError('Invalid expected_digest')
    if llm['backend'] == 'ollama_ssh' and digest is None:raise ValueError('Confirm local model digest before activation')
    access_path = local['access_file']
    if not isinstance(access_path,str) or not access_path.startswith('secrets/') or '..' in Path(access_path).parts or Path(access_path).is_absolute():raise ValueError('Local access_file must remain in project secrets')
    if local['input_budget']['context_input_limit_tokens']+local['input_budget']['output_reserve_tokens'] > local['num_ctx'] or local['input_budget']['output_reserve_tokens'] < local['num_predict']:raise ValueError('Local budget exceeds known model capacity / output reserve')
    for key, value in {'history_turns':8,'user_cooldown_seconds':5,'session_queue_limit':2,'session_queue_timeout_seconds':600}.items():chat.setdefault(key,value)
    output.setdefault('mode', 'plain_chat')
    output.setdefault('quote_reply',False)
    if output['quote_reply'] is not False:raise ValueError('Only direct group replies are supported')
    output.setdefault('max_reply_chars', 1200)
    from .reply_plan import DEFAULTS
    for key, value in DEFAULTS.items():
        output.setdefault(key, value)
    if output['delivery_mode'] not in ('single', 'adaptive'):
        raise ValueError('Invalid delivery_mode')
    for key, lower, upper in (('max_bubbles',1,3), ('casual_max_chars',20,120),
                              ('bubble_max_chars',10,60), ('bubble_delay_min_ms',0,5000),
                              ('bubble_delay_max_ms',0,5000)):
        if type(output[key]) is not int or not lower <= output[key] <= upper:
            raise ValueError(f'Invalid {key}; expected integer {lower}..{upper}')
    if (output['bubble_max_chars'] > output['casual_max_chars'] or
            output['bubble_delay_max_ms'] < output['bubble_delay_min_ms']):
        raise ValueError('Invalid bubble limit/delay relationship')
    if output['mode'] != 'plain_chat':
        raise ValueError('Only plain_chat output is planned')
    for section, key, lower, upper in (
        (onebot, 'port', 1, 65535), (llm, 'port', 1, 65535),
        (llm, 'queue_limit', 0, 100), (llm, 'queue_wait_seconds', 1, 3600),
        (llm, 'cleanup_seconds', 1, 60),
        (chat, 'history_turns', 1, 64),
        (chat, 'user_cooldown_seconds', 0, 3600), (chat, 'session_queue_limit', 0, 100),
        (chat, 'session_queue_timeout_seconds', 1, 3600), (output, 'max_reply_chars', 200, 8000)):
        value = section.get(key)
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError(f'Invalid {key}; expected integer {lower}..{upper}')
    from .token_budget import validate_model_settings
    validate_model_settings(data, backend='codebuddy_cli')
    # 180s provider: reserve 15s retrieval (LAP-18) and 10s delivery margin.
    active = profiles[llm['backend']]
    if llm['queue_wait_seconds'] + active['run_timeout_seconds'] + 25 > 180:raise ValueError('Provider timeout 180 exceeded')
    secret = data.get('secrets_file')
    if not isinstance(secret, str) or not secret:
        raise ValueError('Missing secrets_file')
    from .qq_transport import validate_transport
    if isinstance(data.get('legacy_extensions'), dict) and 'qq_transport' in data['legacy_extensions']:
        raise ValueError('Legacy qq_transport collision requires review')
    validate_transport(data)
    return data


def read_settings(path, *, root=None):
    path = Path(path).resolve()
    content = path.read_bytes()
    try:
        raw = yaml.safe_load(content.decode('utf-8-sig'))
    except (yaml.YAMLError, UnicodeError):
        raise ValueError('Invalid UTF-8 YAML configuration') from None
    data = normalize_settings(raw)
    root = Path(root).resolve() if root is not None else path.parent.parent
    from .qq_transport import validate_transport
    validate_transport(data, root)
    from .ssh_transport import secrets_path
    secrets_path(root,data['llm']['profiles']['ollama_ssh']['access_file'])
    if not (root / data['secrets_file']).resolve().is_relative_to(root / 'secrets'):
        raise ValueError('Secrets file must remain in project secrets directory')
    return data, hashlib.sha256(content).hexdigest()


def load_settings(path):
    return read_settings(path)[0]


def load_gate_config(path=None, *, root=None, settings=None):
    from .config_files import load_consumer, management_root
    root = Path(root).resolve() if root is not None else management_root(path)
    data = deepcopy(settings) if settings is not None else load_consumer(root, path)
    from .vision import require_production
    require_production(data,root=root)
    token_path = (root / data['secrets_file']).resolve()
    if not token_path.is_relative_to(root / 'secrets'):
        raise ValueError('Secrets file must remain in project secrets directory')
    tokens = json.loads(token_path.read_text(encoding='utf-8'))
    from .meme_import import admin_token
    admin=admin_token(root)
    from .vision import context_token
    from .members import suspend_unverified
    effective_members=suspend_unverified(data)
    context=context_token(root) if data['vision']['enabled'] or effective_members['enabled'] else None
    if context and context in list(tokens.values())+[admin]:raise ValueError('Independent context token required')
    if admin and admin in tokens.values():raise ValueError('Independent memes admin token required')
    if data['access'].get('private_enabled') is not False:
        raise ValueError('Private messages must be disabled')
    groups, admins = data['access']['allowed_groups'], data['access']['admin_users']
    if not isinstance(groups, list) or not isinstance(admins, list):
        raise ValueError('Groups/admins must be explicit lists')
    from .meme_catalog import MemeCatalog
    from .members import suspend_unverified
    from .qq_transport import resolve_transport
    from .config_files import canonical, sha
    transport = resolve_transport(data)
    return GateConfig(
        bot_qq=data['bot']['qq'], allowed_groups=frozenset(groups), admin_users=frozenset(admins),
        inbound_token=tokens['onebot_inbound'], upstream_token=tokens['onebot_upstream'],
        database=root / 'state/gate.sqlite', upstream=data['onebot']['upstream'],
        host=data['onebot']['host'], port=data['onebot']['port'],
        blocked_users=frozenset(data['access']['blocked_users']),
        participation_mode=data['participation']['mode'],
        silence_enabled=data['participation']['silence']['enabled'],
        silence_aliases=tuple(data['participation']['attention']['aliases']),
        session_queue_timeout_seconds=data['chat']['session_queue_timeout_seconds'],
        message_max_chars=data['participation']['message_max_chars'],
        vision_enabled=data['vision']['enabled'],
        ingress_diagnostics=data['vision']['ingress_diagnostics'],
        members_enabled=effective_members['enabled'],
        members_config=effective_members,
        public_network=data['public_network'],
        attention_enabled=data['participation']['mode']=='free' and data['participation']['attention']['enabled'],
        media_catalog=MemeCatalog(root,data['memes']) if data['memes']['enabled'] else None,
        transport_provider=transport['provider'], transport_instance_id=os.environ.get('QQBOT_INSTANCE_ID',''),
        transport_config_digest=sha(canonical(data)), transport_control_port=transport['snowluma']['control_port'],
        transport_health_ttl=transport['snowluma']['health_ttl_seconds'], transport_health_poll=transport['snowluma']['health_poll_seconds'],
        transport_ready_timeout=transport['snowluma']['ready_timeout_seconds'],
    )


_configuration_leases = {}


def require_configuration_lease(root, lease):
    """Writer capability is valid only in the current OS-lock scope/thread."""
    key = str(Path(root).resolve())
    if _configuration_leases.get((key, threading.get_ident())) is not lease or lease is None:
        raise ValueError('TRANSPORT_WRITER_LOCK_REQUIRED')


@contextmanager
def configuration_lock(root):
    """OS lock shared by configuration writes and project startup; crashes release it."""
    from .config_files import safe_mkdir, plain_path, exists
    root = Path(root).resolve()
    lock = Path(root) / 'state/configuration.lock'
    safe_mkdir(root, lock.parent)
    if exists(lock):plain_path(root, lock)
    with lock.open('a+b') as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise ValueError('Configuration/start/stop operation already in progress') from None
        lease = object()
        lease_key = (str(root), threading.get_ident())
        _configuration_leases[lease_key] = lease
        try:
            yield lease
        finally:
            _configuration_leases.pop(lease_key, None)
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def require_stopped(root):
    for filename in ('managed-processes.json', 'router-ready.json'):
        path = Path(root) / 'state' / filename
        if not path.exists():
            continue
        try:
            entries = json.loads(path.read_text(encoding='utf-8'))
            if filename == 'router-ready.json':
                entries = [entries]
            if not isinstance(entries, list):
                raise ValueError()
            for entry in entries:
                try:
                    process = psutil.Process(entry['pid'])
                    if process.is_running() and abs(process.create_time() - entry['created']) < .01:
                        raise ValueError('Stop project processes before changing configuration')
                except psutil.NoSuchProcess:
                    continue
        except (OSError, KeyError, TypeError, psutil.AccessDenied, json.JSONDecodeError):
            raise ValueError('Cannot verify project is stopped; inspect local state') from None


def save_settings(path, data, expected_digest):
    from .config_files import reject_legacy_write
    reject_legacy_write(path)
    path = Path(path).resolve()
    root = path.parent.parent
    with configuration_lock(root):
        reject_legacy_write(path)
        require_stopped(root)
        _, digest = read_settings(path)
        if digest != expected_digest:
            raise ValueError('Configuration changed; reload before saving')
        normalized = normalize_settings(data)
        from .members import require_production as require_members
        require_members(normalized)
        from .ssh_transport import secrets_path
        secrets_path(root,normalized['llm']['profiles']['ollama_ssh']['access_file'])
        if not (root / normalized['secrets_file']).resolve().is_relative_to(root / 'secrets'):
            raise ValueError('Secrets file must remain in project secrets directory')
        original = path.read_bytes()
        if hashlib.sha256(original).hexdigest() != expected_digest:
            raise ValueError('Configuration changed; reload before saving')
        backup = root / 'state/config-backups'
        backup.mkdir(parents=True, exist_ok=True)
        (backup / f'{time.time_ns()}-{uuid.uuid4().hex}.yaml').write_bytes(original)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                yaml.safe_dump(normalized, stream, allow_unicode=True, sort_keys=False)
                stream.flush(); os.fsync(stream.fileno())
            require_stopped(root)
            reject_legacy_write(path)
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected_digest:
                raise ValueError('Configuration changed; reload before saving')
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
