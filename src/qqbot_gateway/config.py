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

import yaml
import psutil


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

    def __post_init__(self):
        if self.participation_mode not in ('mentions','free'):raise ValueError('Invalid participation mode')
        if not qq_id(self.bot_qq) or not self.allowed_groups or not self.admin_users:
            raise ValueError('Bot, allowed groups and admins must be nonempty')
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
    from .web_policy import validate_web
    data['web'] = validate_web(data.get('web', {}))
    from .participation import validate_participation
    data['participation']=validate_participation(data.get('participation',{}))
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
    return data


def read_settings(path):
    path = Path(path).resolve()
    content = path.read_bytes()
    try:
        raw = yaml.safe_load(content.decode('utf-8-sig'))
    except (yaml.YAMLError, UnicodeError):
        raise ValueError('Invalid UTF-8 YAML configuration') from None
    data = normalize_settings(raw)
    root = path.parent.parent
    from .ssh_transport import secrets_path
    secrets_path(root,data['llm']['profiles']['ollama_ssh']['access_file'])
    if not (root / data['secrets_file']).resolve().is_relative_to(root / 'secrets'):
        raise ValueError('Secrets file must remain in project secrets directory')
    return data, hashlib.sha256(content).hexdigest()


def load_settings(path):
    return read_settings(path)[0]


def load_gate_config(path):
    path = Path(path).resolve()
    root = path.parent.parent
    data = load_settings(path)
    token_path = (root / data['secrets_file']).resolve()
    if not token_path.is_relative_to(root / 'secrets'):
        raise ValueError('Secrets file must remain in project secrets directory')
    tokens = json.loads(token_path.read_text(encoding='utf-8'))
    if data['access'].get('private_enabled') is not False:
        raise ValueError('Private messages must be disabled')
    groups, admins = data['access']['allowed_groups'], data['access']['admin_users']
    if not isinstance(groups, list) or not isinstance(admins, list):
        raise ValueError('Groups/admins must be explicit lists')
    return GateConfig(
        bot_qq=data['bot']['qq'], allowed_groups=frozenset(groups), admin_users=frozenset(admins),
        inbound_token=tokens['onebot_inbound'], upstream_token=tokens['onebot_upstream'],
        database=root / 'state/gate.sqlite', upstream=data['onebot']['upstream'],
        host=data['onebot']['host'], port=data['onebot']['port'],
        blocked_users=frozenset(data['access']['blocked_users']),
        participation_mode=data['participation']['mode'],
    )


@contextmanager
def configuration_lock(root):
    """OS lock shared by configuration writes and project startup; crashes release it."""
    lock = Path(root) / 'state/configuration.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
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
        try:
            yield
        finally:
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
    path = Path(path).resolve()
    root = path.parent.parent
    with configuration_lock(root):
        require_stopped(root)
        _, digest = read_settings(path)
        if digest != expected_digest:
            raise ValueError('Configuration changed; reload before saving')
        normalized = normalize_settings(data)
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
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected_digest:
                raise ValueError('Configuration changed; reload before saving')
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
