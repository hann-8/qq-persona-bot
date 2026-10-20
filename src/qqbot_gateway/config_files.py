"""Fixed five-file layout, read-only discovery, and instance-bound configuration.

No credentials, transports, catalogues or memory stores are opened by this module.
"""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import uuid

import yaml

LAYOUT = {
    'bot.yaml': ('bot', 'access'),
    'models.yaml': ('llm',),
    'chat.yaml': ('chat', 'participation', 'output'),
    'features.yaml': ('web', 'memes', 'memory', 'vision', 'members'),
    'runtime.yaml': ('layout_version', 'schema_version', 'onebot', 'secrets_file', 'legacy_extensions'),
}
KNOWN = frozenset(k for keys in LAYOUT.values() for k in keys)
FILE_LIMIT = 128 * 1024
TOTAL_LIMIT = 512 * 1024


class ConfigError(ValueError):
    """Only pre-approved labels/locations, never parser exception text."""


def error(filename, field='根映射', mark=None, reason='配置无效'):
    location = f'，行{mark.line + 1}列{mark.column + 1}' if mark is not None else ''
    return ConfigError(f'config/local/{filename}：字段 {field}{location}：{reason}')


def exists(path):
    return os.path.lexists(path)


def plain_path(root, path, *, directory=False):
    """Check every component, including Windows junction/reparse points."""
    root = Path(root).resolve()
    path = Path(path).absolute()
    if not path.is_relative_to(root):raise ConfigError('配置路径越界')
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        info = current.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ConfigError('配置路径不能使用链接或重解析点')
    info = path.stat()
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise ConfigError('配置路径类型无效')
    if not path.resolve().is_relative_to(root):raise ConfigError('配置路径越界')
    return path


def safe_mkdir(root, path):
    """Create only checked project directories, never follow an existing junction."""
    root = Path(root).resolve()
    path = Path(path).absolute()
    if not path.is_relative_to(root):raise ConfigError('目录路径越界')
    # Cleanup ledgers use explicit, fresh per-test/per-request roots as well.
    # Preserve configuration_lock's existing ability to create that root.
    root.mkdir(parents=True, exist_ok=True)
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        if not exists(current):current.mkdir()
        plain_path(root, current, directory=True)
    return path


def parse(content, filename):
    # Inspect events first: SafeLoader alone permits aliases, merges and duplicate keys.
    try:
        text = content.decode('utf-8-sig')
        for event in yaml.parse(text, Loader=yaml.SafeLoader):
            if isinstance(event, yaml.AliasEvent) or getattr(event, 'anchor', None):
                raise error(filename, mark=event.start_mark, reason='不允许锚点或别名')
            if getattr(event, 'tag', None):
                raise error(filename, mark=event.start_mark, reason='不允许显式标签')
        node = yaml.compose(text, Loader=yaml.SafeLoader)
        def inspect(node, field='根映射'):
            if isinstance(node, yaml.MappingNode):
                seen = set()
                for key, value in node.value:
                    if not isinstance(key, yaml.ScalarNode) or key.tag != 'tag:yaml.org,2002:str':
                        raise error(filename, field, key.start_mark, '键必须为字符串')
                    if key.value == '<<' or key.value in seen:
                        raise error(filename, field, key.start_mark, '重复键或合并键')
                    seen.add(key.value)
                    # Never echo unknown user-controlled keys as diagnostic labels.
                    child = key.value if field == '根映射' and key.value in LAYOUT[filename] else field
                    inspect(value, child)
            elif isinstance(node, yaml.SequenceNode):
                for value in node.value:inspect(value, field)
        if not isinstance(node, yaml.MappingNode):raise error(filename)
        inspect(node)
        data = yaml.safe_load(text)
        if any(k not in LAYOUT[filename] for k in data):
            raise error(filename, reason='未知根字段或字段归属错误')
        return data
    except ConfigError:raise
    except (yaml.YAMLError, UnicodeError, RecursionError, ValueError, TypeError) as exc:
        raise error(filename, mark=getattr(exc, 'problem_mark', None)) from None


def validate(root, raw):
    from .config import normalize_settings
    from .ssh_transport import secrets_path
    data = normalize_settings(raw)
    try:secrets_path(root, data['llm']['profiles']['ollama_ssh']['access_file'])
    except ValueError:raise error('models.yaml', 'llm.profiles.ollama_ssh.access_file', reason='秘密引用必须位于项目secrets内') from None
    try:secrets_path(root, data['secrets_file'])
    except ValueError:raise error('runtime.yaml', 'secrets_file', reason='秘密引用必须位于项目secrets内') from None
    return data


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(content):
    return hashlib.sha256(content).hexdigest()


class _NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):return True


def dump_settings(data):
    return yaml.dump(data, Dumper=_NoAliasDumper, allow_unicode=True, sort_keys=False)


@dataclass(frozen=True)
class ProjectConfig:
    root: Path
    settings: dict
    layout: str
    source_digest: str
    semantic_digest: str
    files: dict
    unloaded: tuple = ()
    extensions: int = 0


def read_project(root):
    """No writes, network, secret contents, fallback on malformed split, or retries."""
    root = Path(root).resolve()
    local = root / 'config/local'
    if not exists(local):
        from .config import read_settings
        try:data, digest = read_settings(root / 'config/settings.local.yaml')
        except (ValueError, OSError, TypeError, KeyError, AttributeError):
            raise ConfigError('config/settings.local.yaml：字段 整体校验：文件缺失、格式或安全约束无效') from None
        try:semantic = sha(canonical(data))
        except (TypeError, ValueError):raise ConfigError('config/settings.local.yaml：扩展字段不能表示为规范化配置') from None
        return ProjectConfig(root, data, 'legacy', digest, semantic,
                             {'config/settings.local.yaml': digest}, extensions=sum(k not in KNOWN for k in data))
    return read_split(root, local)


def read_split(root, local):
    root = Path(root).resolve()
    contents = {}
    for name in LAYOUT:
        try:
            path = plain_path(root, local / name)
            if path.stat().st_size > FILE_LIMIT:raise error(name, reason='文件超过128KiB')
            with path.open('rb') as stream:content = stream.read(FILE_LIMIT + 1)
            if len(content) > FILE_LIMIT:raise error(name, reason='文件超过128KiB')
            contents[name] = content
        except (OSError, ConfigError):
            raise error(name, reason='文件缺失、路径不安全或超过128KiB') from None
    if sum(map(len, contents.values())) > TOTAL_LIMIT:raise error('runtime.yaml', reason='总大小超过512KiB')
    assembled = {}
    for name, content in contents.items():assembled.update(parse(content, name))
    if type(assembled.get('layout_version')) is not int or assembled.pop('layout_version') != 1:
        raise error('runtime.yaml', 'layout_version', reason='仅支持布局版本1')
    if type(assembled.get('schema_version')) is not int or assembled['schema_version'] != 3:
        raise error('runtime.yaml', 'schema_version', reason='分层内部版本必须为3')
    ext = assembled.pop('legacy_extensions', {})
    if not isinstance(ext, dict) or any(not isinstance(k, str) or k in KNOWN for k in ext):
        raise error('runtime.yaml', 'legacy_extensions', reason='扩展字段冲突或类型错误')
    assembled.update(ext)
    try:
        data = validate(root, assembled)
        semantic = sha(canonical(data))
    except ConfigError:raise
    except (ValueError, TypeError, AttributeError, KeyError, OverflowError, RecursionError) as failure:
        # Identify the failing section using existing validator against a valid
        # synthetic baseline. Diagnostics never copy a validator's arbitrary text.
        field = '整体校验'
        filename = 'runtime.yaml'
        from .config import normalize_settings
        # Diagnostic scaffolding only, never read examples/legacy as a fallback.
        baseline = normalize_settings(dict(schema_version=3, bot=dict(qq='222'),
            access=dict(allowed_groups=['111'], admin_users=['333'], private_enabled=False),
            onebot=dict(host='127.0.0.1', port=6200, upstream='ws://127.0.0.1:6199/ws'),
            llm=dict(backend='codebuddy_cli', host='127.0.0.1', port=8765, max_concurrency=1,
                     queue_limit=5, queue_wait_seconds=30, cleanup_seconds=5),
            secrets_file='secrets/local-tokens.json'))
        for name, sections in LAYOUT.items():
            for section in sections:
                if section not in assembled:continue
                candidate = deepcopy(baseline)
                candidate[section] = assembled[section]
                try:validate(root, candidate)
                except (ValueError, TypeError, AttributeError, KeyError, OverflowError):
                    field, filename = section, name
                    break
            if field != '整体校验':break
        # A known schema key can refine a section diagnostic. Never echo the
        # exception, unknown keys or values; retain a safe YAML node location.
        node = yaml.compose(contents[filename].decode('utf-8-sig'), Loader=yaml.SafeLoader)
        mark = node.start_mark
        section_node = next((value for key, value in node.value if key.value == field), None)
        if section_node is not None:
            mark = section_node.start_mark
            from .config_comments import COMMENT_KEYS
            matches = []
            def locate(value, path):
                if not isinstance(value, yaml.MappingNode):return
                for key, child in value.value:
                    if key.value in COMMENT_KEYS and re.search(r'(?<![A-Za-z0-9_])' + re.escape(key.value) + r'(?![A-Za-z0-9_])', str(failure)):
                        matches.append(('.'.join(path + (key.value,)), child.start_mark))
                    locate(child, path + (key.value,)) if key.value in COMMENT_KEYS else None
            locate(section_node, (field,))
            if len(matches) == 1:field, mark = matches[0]
        raise error(filename, field, mark, reason='类型、范围、组合或安全约束不满足') from None
    files = {f'config/local/{name}': sha(content) for name, content in contents.items()}
    for name, content in contents.items():
        try:
            path = plain_path(root, local / name)
            with path.open('rb') as stream:current = stream.read(FILE_LIMIT + 1)
            if current != content:raise ValueError()
        except (OSError, ValueError):raise error(name, reason='读取期间文件改变，请保存完后再试') from None
    digest = sha(canonical({'layout_version': 1, 'files': files}))
    unloaded = tuple(sorted(p.name for p in local.iterdir() if p.name not in LAYOUT and p.suffix.lower() in ('.yaml', '.yml')))
    return ProjectConfig(root, data, 'split', digest, semantic, files, unloaded, len(ext))


def management_root(path, root=None):
    """Only the known shallow legacy entry may supply an implicit root."""
    path = Path(path).absolute()
    if root is not None:return Path(root).resolve()
    if path.parent.name != 'config' or path.name != 'settings.local.yaml':
        raise ConfigError('此入口必须显式传递项目root；不能从深层配置路径猜根')
    return path.parent.parent.resolve()


def read_management(path, *, root=None):
    config = read_project(management_root(path, root))
    return deepcopy(config.settings), config.source_digest


def reject_legacy_write(path):
    root = management_root(path)
    if exists(root / 'config/local'):
        raise ConfigError('分层配置禁止旧入口写入；请按config/README.md编辑config/local对应文件')
    return root


def create_snapshot(config, instance_id):
    if not re.fullmatch('[a-f0-9]{32}', instance_id):raise ConfigError('配置实例标识无效')
    directory = config.root / 'state/config-runtime' / instance_id
    safe_mkdir(config.root, config.root / 'state/config-runtime')
    directory.mkdir(parents=True, exist_ok=False)
    content = dump_settings(config.settings).encode('utf-8')
    path = directory / 'settings.yaml'
    with path.open('xb') as stream:stream.write(content)
    metadata = dict(format='qqbot-config-snapshot-v1', instance_id=instance_id, layout=config.layout, files=config.files,
                    source_digest=config.source_digest, semantic_digest=config.semantic_digest, snapshot_digest=sha(content),
                    legacy_extension_count=config.extensions)
    with (directory / 'source.json').open('x', encoding='utf-8') as stream:json.dump(metadata, stream)
    return path, metadata


def snapshot_environment(root, path, metadata):
    return dict(QQBOT_ROOT=str(root), QQBOT_CONFIG_SNAPSHOT=str(path),
                QQBOT_CONFIG_DIGEST=metadata['snapshot_digest'], QQBOT_INSTANCE_ID=metadata['instance_id'],
                QQBOT_CONFIG_REQUIRED='1')


def load_consumer(root, path=None, *, environ=None):
    """Verify instance snapshot; standalone explicit legacy/project reads stay supported."""
    env = os.environ if environ is None else environ
    root = Path(root).resolve()
    keys = ('QQBOT_CONFIG_SNAPSHOT', 'QQBOT_CONFIG_DIGEST')
    if (env.get('QQBOT_CONFIG_REQUIRED') == '1' or re.fullmatch('[a-f0-9]{32}', env.get('QQBOT_INSTANCE_ID', ''))) and not any(k in env for k in keys):
        raise ConfigError('受管实例缺少配置快照元数据')
    if any(k in env for k in keys):
        try:
            instance = env['QQBOT_INSTANCE_ID']
            if not re.fullmatch('[a-f0-9]{32}', instance):raise ValueError()
            if Path(env.get('QQBOT_ROOT', root)).resolve() != root:raise ValueError()
            expected = root / 'state/config-runtime' / instance / 'settings.yaml'
            supplied = Path(env['QQBOT_CONFIG_SNAPSHOT']).absolute()
            if supplied != expected or (path is not None and Path(path).absolute() != expected):raise ValueError()
            plain_path(root, expected)
            plain_path(root, expected.with_name('source.json'))
            content = expected.read_bytes()
            meta = json.loads(expected.with_name('source.json').read_text(encoding='utf-8'))
            if meta.get('format') != 'qqbot-config-snapshot-v1' or meta['instance_id'] != instance or sha(content) != env['QQBOT_CONFIG_DIGEST'] or meta['snapshot_digest'] != sha(content):raise ValueError()
            data = validate(root, yaml.safe_load(content.decode('utf-8')))
            if sha(canonical(data)) != meta['semantic_digest']:raise ValueError()
            return data
        except (ValueError, OSError, KeyError, TypeError, AttributeError, yaml.YAMLError):
            raise ConfigError('实例配置快照缺失、位置或摘要不匹配') from None
    if path is not None:
        if Path(path).absolute().is_relative_to(root / 'state/config-runtime'):
            raise ConfigError('快照必须携带实例与摘要元数据')
        from .config import read_settings
        try:return read_settings(path, root=root)[0]
        except (ValueError, OSError, TypeError, KeyError, AttributeError):
            raise ConfigError('显式legacy文件：字段 整体校验：文件缺失、格式或安全约束无效') from None
    return deepcopy(read_project(root).settings)


def prune_snapshots(root, keep=3):
    """Only retired, identified snapshots; unknown/live ownership is retained."""
    from .config import require_stopped
    root = Path(root).resolve()
    # Global stopped proof includes router identities. A live/unknown state means
    # nothing is deleted, even if an old snapshot looks stale.
    try:require_stopped(root)
    except (ValueError, OSError):return
    if any(exists(root / name) for name in ('state/cli-cleanup/unresolved.json',
                                           'state/ollama-remote-result-unknown.json')):
        return
    base = root / 'state/config-runtime'
    if not base.exists():return
    protected = set()
    try:
        plain_path(root, base, directory=True)
        mode = root / 'state/service-mode.json'
        if mode.exists():
            value = json.loads(mode.read_text(encoding='utf-8'))
            protected.add(value['instance_id'])
    except (ValueError, OSError, TypeError, KeyError):return
    candidates = []
    for directory in base.iterdir():
        try:
            plain_path(root, directory, directory=True)
            plain_path(root, directory / 'source.json')
            plain_path(root, directory / 'settings.yaml')
            meta = json.loads((directory / 'source.json').read_text(encoding='utf-8'))
            if meta.get('format') != 'qqbot-config-snapshot-v1' or meta.get('instance_id') != directory.name or not re.fullmatch('[a-f0-9]{32}', directory.name):continue
            if sha((directory / 'settings.yaml').read_bytes()) != meta['snapshot_digest']:continue
            if set(p.name for p in directory.iterdir()) != {'settings.yaml', 'source.json'}:continue
            candidates.append(directory)
        except (ValueError, OSError, KeyError, TypeError, AttributeError):continue
    for directory in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[keep:]:
        if directory.name in protected:continue
        plain_path(root, directory, directory=True)
        shutil.rmtree(directory)
