"""Original transport configuration and read-only local evidence inspection.

No process/network/secret access. Static evidence never grants runtime admission.
Defaults belong at consumption, not in the legacy normalized snapshot.
"""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import stat
from urllib.parse import urlparse

RELEASE = 'v2.1.1'
TAG_SHA = 'f8cb15c27bca3d2d1bd044a921e55bfc44bb5e60'
BUNDLE_NAME = 'SnowLuma-v2.1.1-win-x64.zip'
BUNDLE_SIZE = 42694125
BUNDLE_SHA256 = 'c739171f95c27706767e69ba36099707c222fcec639b46f4d59689997b527772'
PROOF_FORMAT = 'qqbot-snowluma-static-proof-v1'
POLICY_VERSION = 'qqbot-snowluma-policy-v1'
DEFAULTS = dict(provider='napcat', snowluma=dict(
    runtime_root='runtime/snowluma/v2.1.1', qq_executable='runtime/qq-snowluma/QQ.exe',
    proof_file='state/qq-transport/proof.local.json', control_secret_file='secrets/snowluma-control.local.json',
    control_port=5098, health_poll_seconds=5, health_ttl_seconds=15, ready_timeout_seconds=180),
    recovery=dict(enabled=False, allow_qq_restart=False, down_grace_seconds=30, drain_seconds=150,
                  cooldown_seconds=1800, max_snowluma_per_24h=2, max_qq_per_24h=1),
    trial=dict(sample_seconds=60, initial_hours=72, total_hours=168))


@dataclass(frozen=True)
class Provider:
    name: str
    components: tuple
    independent_health: bool


PROVIDERS = {'napcat': Provider('napcat', ('napcat',), False),
             'snowluma': Provider('snowluma', ('qq_client', 'snowluma', 'transport_watch'), True)}


def _mapping(value, keys):
    if not isinstance(value, dict) or any(k not in keys for k in value):
        raise ValueError('Invalid qq_transport mapping or unknown field')


def _relative(value, area):
    if (not isinstance(value, str) or not value or '\\' in value or ':' in value or
        PureWindowsPath(value).is_absolute() or value.startswith('/') or
        any(p in ('', '.', '..') or p.endswith((' ', '.')) or
            re.fullmatch(r'(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', p) or
            any(ord(c) < 32 or c in '<>"|?*' for c in p) for p in value.split('/')) or
        value.split('/')[0] != area):
        raise ValueError('Invalid qq_transport project path')
    return value


def checked_path(root, value, area):
    """Validate missing paths too, checking every existing ancestor for reparse points."""
    _relative(value, area)
    root = Path(root).resolve()
    current = root
    for part in value.split('/'):
        current /= part
        try:info = current.lstat()
        except FileNotFoundError:continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Invalid qq_transport linked path')
    if not current.resolve().is_relative_to(root):raise ValueError('Invalid qq_transport path scope')
    return current


def resolve_transport(settings):
    """Return a detached effective value; never add defaults to settings."""
    raw = settings.get('qq_transport', {})
    _mapping(raw, DEFAULTS)
    result = deepcopy(DEFAULTS)
    for key, value in raw.items():
        if key == 'provider':result[key] = value
        else:
            _mapping(value, DEFAULTS[key])
            result[key].update(deepcopy(value))
    if not isinstance(result['provider'], str) or result['provider'] not in PROVIDERS:raise ValueError('Invalid qq_transport provider')
    snow, recovery, trial = (result[k] for k in ('snowluma', 'recovery', 'trial'))
    for key, area in (('runtime_root', 'runtime'), ('qq_executable', 'runtime'),
                      ('proof_file', 'state'), ('control_secret_file', 'secrets')):
        _relative(snow[key], area)
    paths = [snow[k].casefold() for k in ('runtime_root', 'qq_executable', 'proof_file', 'control_secret_file')]
    if (len(set(paths)) != len(paths) or paths[1].startswith(paths[0] + '/') or
        paths[0].startswith(paths[1] + '/')):
        raise ValueError('Invalid qq_transport path collision')
    other_secrets = [settings.get('secrets_file'),
        settings.get('llm', {}).get('profiles', {}).get('ollama_ssh', {}).get('access_file'),
        'secrets/bilibili-session.local.json']
    if 'qq_transport' in settings and paths[3] in [p.replace('\\', '/').casefold() for p in other_secrets if isinstance(p, str)]:
        raise ValueError('Invalid qq_transport reused control_secret_file')
    ranges = ((snow, 'control_port', 1, 65535), (snow, 'health_poll_seconds', 5, 10),
              (snow, 'health_ttl_seconds', 15, 30), (snow, 'ready_timeout_seconds', 60, 240),
              (recovery, 'down_grace_seconds', 30, 30), (recovery, 'drain_seconds', 150, 150),
              (recovery, 'cooldown_seconds', 1800, 2147483647), (recovery, 'max_snowluma_per_24h', 0, 2),
              (recovery, 'max_qq_per_24h', 0, 1), (trial, 'sample_seconds', 60, 60),
              (trial, 'initial_hours', 72, 72), (trial, 'total_hours', 168, 168))
    for obj, key, lo, hi in ranges:
        if type(obj[key]) is not int or not lo <= obj[key] <= hi:raise ValueError('Invalid qq_transport ' + key)
    if snow['health_ttl_seconds'] < 3 * snow['health_poll_seconds']:raise ValueError('Invalid qq_transport health_ttl_seconds')
    for key in ('enabled', 'allow_qq_restart'):
        if type(recovery[key]) is not bool:raise ValueError('Invalid qq_transport recovery flag')
    # QQ restart also needs runtime 3/3 evidence, enforced by the later supervisor.
    ports = {6099, 3000, 3001, 6185, 6199, 6200, 8765}
    for section in ('onebot', 'llm'):
        config = settings.get(section, {})
        port = config.get('port')
        if type(port) is int:ports.add(port)
    try:
        port = urlparse(settings.get('onebot', {}).get('upstream', '')).port
        if port:ports.add(port)
    except ValueError:raise ValueError('Invalid qq_transport upstream port') from None
    if 'qq_transport' in settings and snow['control_port'] in ports:raise ValueError('Invalid qq_transport control_port collision')
    return result


def validate_transport(settings, root=None):
    if 'qq_transport' in settings:
        effective = resolve_transport(settings)
        if root is not None:
            snow = effective['snowluma']
            for key, area in (('runtime_root', 'runtime'), ('qq_executable', 'runtime'),
                              ('proof_file', 'state'), ('control_secret_file', 'secrets')):
                checked_path(root, snow[key], area)


def provider_description(settings):
    return PROVIDERS[resolve_transport(settings)['provider']]


def _exact(value, keys):
    _mapping(value, keys)
    if set(value) != set(keys):raise ValueError('Invalid static proof fields')


def _digest(value):
    if not isinstance(value, str) or re.fullmatch('[a-f0-9]{64}', value) is None:
        raise ValueError('Invalid static proof digest')


def _json(content):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:raise ValueError('Duplicate static proof field')
            result[key] = value
        return result
    return json.loads(content, object_pairs_hook=pairs)


def validate_static_proof(value):
    """Strict evidence references, no booleans/valid switches or arbitrary capabilities."""
    _exact(value, ('format', 'release', 'tag_sha', 'bundle', 'native_deployment', 'clean_qq', 'data_scope', 'private_build'))
    if (value['format'], value['release'], value['tag_sha']) != (PROOF_FORMAT, RELEASE, TAG_SHA):
        raise ValueError('Invalid static proof version')
    bundle = value['bundle']
    _exact(bundle, ('file', 'sha256', 'size'))
    _relative(bundle['file'], 'runtime')
    if (Path(bundle['file']).name != BUNDLE_NAME or bundle['sha256'] != BUNDLE_SHA256 or
        type(bundle['size']) is not int or bundle['size'] != BUNDLE_SIZE):raise ValueError('Invalid fixed official bundle')
    for key in ('native_deployment', 'clean_qq', 'data_scope', 'private_build'):
        record = value[key]
        extra = {'clean_qq': ('executable_sha256',), 'private_build': ('build_file', 'build_sha256', 'policy_file', 'policy_sha256', 'policy_version')}.get(key, ())
        _exact(record, ('evidence_file', 'evidence_sha256') + extra)
        _relative(record['evidence_file'], 'state')
        if not record['evidence_file'].startswith('state/qq-transport/'):
            raise ValueError('Invalid static proof evidence scope')
        for field in record:
            if field.endswith('sha256'):_digest(record[field])
        if key == 'private_build':
            _relative(record['build_file'], 'runtime')
            _relative(record['policy_file'], 'runtime')
            if (not record['build_file'].startswith('runtime/snowluma-private/') or
                not record['policy_file'].startswith('runtime/snowluma-private/') or record['policy_version'] != POLICY_VERSION):
                raise ValueError('Invalid private build proof')
    return deepcopy(value)


def _file_digest(root, name, area, limit):
    path = checked_path(root, name, area)
    if not path.is_file() or path.stat().st_size > limit:raise ValueError('Static evidence missing or too large')
    digest = hashlib.sha256()
    count = 0
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            count += len(chunk)
            if count > limit:raise ValueError('Static evidence too large')
            digest.update(chunk)
    return digest.hexdigest(), count


def inspect_transport(root, settings):
    """Closed diagnostics only. Does not open the control secret, sockets or QQ data.

    Evidence bytes are hashed, never parsed as commands or printed. Even a matching
    record needs later private wiring and controlled G0/G1 review; this is not ready.
    """
    effective = resolve_transport(settings)
    result = dict(provider=effective['provider'], static_only=True, channel_ready=False,
                  inspection_scope='snowluma_candidate', static_evidence_checked=False, blockers=[])
    snow = effective['snowluma']
    blockers = result['blockers']
    try:
        for key, area in (('runtime_root', 'runtime'), ('qq_executable', 'runtime'),
                          ('proof_file', 'state'), ('control_secret_file', 'secrets')):
            checked_path(root, snow[key], area)
        bundle = snow['runtime_root'] + '/' + BUNDLE_NAME
        if not checked_path(root, bundle, 'runtime').is_file():blockers.append('official_bundle_missing')
        if not checked_path(root, snow['qq_executable'], 'runtime').is_file():blockers.append('clean_qq_missing')
    except (OSError, ValueError):
        blockers.append('transport_path_unsafe')
        return result
    try:
        path = checked_path(root, snow['proof_file'], 'state')
        if path.stat().st_size > 16384:raise ValueError()
        with path.open('rb') as stream:content = stream.read(16385)
        if len(content) > 16384:raise ValueError()
        proof = validate_static_proof(_json(content))
    except FileNotFoundError:blockers.append('static_proof_missing')
    except (OSError, ValueError, TypeError, RecursionError, UnicodeError):blockers.append('static_proof_invalid')
    else:
        try:
            if proof['bundle']['file'] != bundle:raise ValueError()
            if _file_digest(root, bundle, 'runtime', BUNDLE_SIZE) != (BUNDLE_SHA256, BUNDLE_SIZE):raise ValueError()
            for key in ('native_deployment', 'clean_qq', 'data_scope', 'private_build'):
                record = proof[key]
                if _file_digest(root, record['evidence_file'], 'state', 1024 * 1024)[0] != record['evidence_sha256']:raise ValueError()
            if _file_digest(root, snow['qq_executable'], 'runtime', 512 * 1024 * 1024)[0] != proof['clean_qq']['executable_sha256']:raise ValueError()
            build = proof['private_build']
            if _file_digest(root, build['build_file'], 'runtime', 128 * 1024 * 1024)[0] != build['build_sha256']:raise ValueError()
            if _file_digest(root, build['policy_file'], 'runtime', 1024 * 1024)[0] != build['policy_sha256']:raise ValueError()
            result['static_evidence_checked'] = True
        except (ValueError, OSError):blockers.append('static_evidence_mismatch')
    blockers.extend(('native_deployment_unverified', 'clean_qq_unverified', 'data_scope_unverified',
                     'private_build_unverified', 'operator_scan_required'))
    return result
