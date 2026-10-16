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

    def __post_init__(self):
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
    if type(version) is not int or version not in (1, 2):
        raise ValueError('Unsupported schema_version')
    data['schema_version'] = 2
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
    if llm.get('backend') != 'codebuddy_cli' or llm.get('host') != '127.0.0.1' or type(llm.get('max_concurrency')) is not int or llm['max_concurrency'] != 1:
        raise ValueError('Restricted local CLI configuration required')
    if not isinstance(llm.get('model'), str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}', llm['model']):
        raise ValueError('Invalid llm.model')
    llm.setdefault('reasoning_effort', 'auto')
    llm.setdefault('context_window_tokens', None)
    if llm['reasoning_effort'] not in ('auto', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max'):
        raise ValueError('Invalid reasoning_effort')
    chat, output = data['chat'], data['output']
    for key, value in {'history_turns': 8, 'context_input_limit_tokens': 16384,
                       'context_overhead_reserve_tokens': 2048, 'output_reserve_tokens': 2048,
                       'user_cooldown_seconds': 5, 'session_queue_limit': 2,
                       'session_queue_timeout_seconds': 600}.items():
        chat.setdefault(key, value)
    output.setdefault('mode', 'plain_chat')
    output.setdefault('max_reply_chars', 1200)
    if output['mode'] != 'plain_chat':
        raise ValueError('Only plain_chat output is planned')
    for section, key, lower, upper in (
        (onebot, 'port', 1, 65535), (llm, 'port', 1, 65535),
        (llm, 'queue_limit', 0, 100), (llm, 'queue_wait_seconds', 1, 3600),
        (llm, 'run_timeout_seconds', 1, 3600), (llm, 'cleanup_seconds', 1, 60),
        (chat, 'history_turns', 1, 64), (chat, 'context_input_limit_tokens', 1024, 1048576),
        (chat, 'context_overhead_reserve_tokens', 0, 65536), (chat, 'output_reserve_tokens', 0, 65536),
        (chat, 'user_cooldown_seconds', 0, 3600), (chat, 'session_queue_limit', 0, 100),
        (chat, 'session_queue_timeout_seconds', 1, 3600), (output, 'max_reply_chars', 200, 8000)):
        value = section.get(key)
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError(f'Invalid {key}; expected integer {lower}..{upper}')
    if output['max_reply_chars'] != 1200:
        raise ValueError('Nondefault output controls require LAP-11 implementation')
    from .token_budget import validate_model_settings
    validate_model_settings(data)
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
            raise ValueError('Configuration/start operation already in progress') from None
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
