"""Explicit stopped/locked layout operations. Never called by configuration reads."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid
import sys

import yaml

from .config import configuration_lock, require_stopped, read_settings
from .config_files import (LAYOUT, KNOWN, ConfigError, canonical, exists, plain_path,
                           read_project, read_split, sha, safe_mkdir, dump_settings)


def partition(data):
    values = {name: {key: deepcopy(data[key]) for key in keys if key in data}
              for name, keys in LAYOUT.items()}
    values['runtime.yaml']['layout_version'] = 1
    values['runtime.yaml']['legacy_extensions'] = {k: deepcopy(v) for k, v in data.items() if k not in KNOWN}
    if 'llm' in values['models.yaml']:
        model = values['models.yaml']['llm']
        values['models.yaml']['llm'] = {k: model[k] for k in ('backend', 'profiles') if k in model} | {
            k: v for k, v in model.items() if k not in ('backend', 'profiles')}
    return values


def render(name, data):
    """Safe serialization, fixed field comments; never interpolate values as YAML."""
    from .config_comments import comment
    lines = [f'# {name}：{comment(name)}',
             '# 同目录五文件共同组成配置；其他文件见config/README.md。',
             '# 本机config/local不提交；保存后下次正常启动生效，不热更新。']
    def walk(value, prefix=()):
        if isinstance(value, dict):
            for key, item in value.items():
                # Comments derive only from fixed vocabulary, never unknown values.
                if key not in COMMENT_KEYS:continue
                lines.append('# ' + '.'.join(prefix + (key,)) + '：' + comment(key, item))
                if key != 'legacy_extensions':walk(item, prefix + (key,))
    from .config_comments import COMMENT_KEYS
    walk(data)
    return '\n'.join(lines) + '\n' + dump_settings(data)


def backup_dir(root, action):
    base = root / 'state/config-backups'
    safe_mkdir(root, base)
    target = base / (action + '-' + uuid.uuid4().hex)
    target.mkdir()
    return target


def write_new(path, content):
    with path.open('xb') as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def record(directory, **fields):
    # Each stage is append-only evidence and has an unambiguous completion name.
    write_new(directory / (fields['stage'] + '.json'), canonical(fields))


def publish_directory(source, target):
    """Atomic no-replace directory rename, including empty concurrent targets."""
    if os.name == 'nt':
        os.rename(source, target)
        return
    import ctypes
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform.startswith('linux') and hasattr(libc, 'renameat2'):
        result = libc.renameat2(-100, os.fsencode(source), -100, os.fsencode(target), 1)
    elif sys.platform == 'darwin' and hasattr(libc, 'renamex_np'):
        result = libc.renamex_np(os.fsencode(source), os.fsencode(target), 4)
    else:raise ConfigError('此平台缺少不可覆盖的目录发布能力，未发布')
    if result:
        code = ctypes.get_errno()
        raise OSError(code, 'Directory publication failed')


def initialize(root, *, migrate=False, examples=None):
    root = Path(root).resolve()
    local = root / 'config/local'
    legacy = root / 'config/settings.local.yaml'
    plain_path(root, root / 'config', directory=True)
    safe_mkdir(root, root / 'state')
    with configuration_lock(root):
        require_stopped(root)
        if exists(local):raise ConfigError('config/local已存在；拒绝覆盖，请运行check')
        if not migrate and exists(legacy):raise ConfigError('旧配置已存在，请使用migrate')
        original = None
        if migrate:
            plain_path(root, legacy)
            original = legacy.read_bytes()
            data, digest = read_settings(legacy, root=root)
            try:canonical(data)
            except (ValueError, TypeError, RecursionError):
                raise ConfigError('旧文件扩展无法无损表示为分层配置，未发布；请核对字段类型') from None
            if sha(original) != digest:raise ConfigError('旧配置读取期间改变')
            directory = backup_dir(root, 'migrate')
            write_new(directory / 'settings.original.yaml', original)
            record(directory, stage='prepared', source_digest=digest)
        else:
            directory = None
            examples = Path(examples) if examples is not None else Path(__file__).resolve().parents[2] / 'config/examples'
        temporary = Path(tempfile.mkdtemp(prefix='.local-', dir=root / 'config'))
        published = False
        try:
            if migrate:
                for name, value in partition(data).items():write_new(temporary / name, render(name, value).encode('utf-8'))
                candidate = read_split(root, temporary)
                if candidate.settings != data:raise ConfigError('迁移语义不相等，未发布')
                # Session identity is a semantic function; exact normalized equality
                # also preserves unknown extensions and unselected model profiles.
            else:
                for name in LAYOUT:write_new(temporary / name, (examples / name).read_bytes())
            require_stopped(root)
            if migrate and sha(legacy.read_bytes()) != digest:raise ConfigError('旧配置改变，未发布')
            if not migrate and exists(legacy):raise ConfigError('旧配置已在别处创建，未发布')
            if exists(local):raise ConfigError('目标已在别处创建，未发布')
            publish_directory(temporary, local)
            published = True
            if directory:record(directory, stage='published', source_digest=digest)
            return dict(layout='split', published=True, backup=str(directory) if directory else None)
        except BaseException as exc:
            if published:
                raise ConfigError('config/local已完整发布，后续记录失败；保留目录，请运行check') from None
            raise
        finally:
            if not published and temporary.exists():
                plain_path(root, temporary, directory=True)
                shutil.rmtree(temporary)


def export_legacy(root):
    root = Path(root).resolve()
    safe_mkdir(root, root / 'state')
    with configuration_lock(root):
        require_stopped(root)
        config = read_project(root)
        if config.layout != 'split':raise ConfigError('此操作要求config/local分层布局')
        directory = backup_dir(root, 'export')
        content = dump_settings(config.settings).encode('utf-8')
        path = directory / 'settings.export.yaml'
        write_new(path, content)
        require_stopped(root)
        if read_project(root).source_digest != config.source_digest or sha(path.read_bytes()) != sha(content):
            raise ConfigError('配置或导出改变，未激活')
        result = dict(stage='exported', source_digest=config.source_digest, export_digest=sha(content),
                      export=str(path), activated=False)
        record(directory, **result)
        return result


def rollback_layout(root, export, source_digest, export_digest, confirmation):
    root = Path(root).resolve()
    export = Path(export).absolute()
    if confirmation != '已核对':raise ConfigError('请先核对导出与两个摘要')
    if not export.is_relative_to(root / 'state/config-backups'):raise ConfigError('导出必须在项目备份目录')
    plain_path(root, export)
    safe_mkdir(root, root / 'state')
    with configuration_lock(root):
        require_stopped(root)
        config = read_project(root)
        if config.layout != 'split' or config.source_digest != source_digest:raise ConfigError('源配置改变')
        content = export.read_bytes()
        if sha(content) != export_digest:raise ConfigError('导出摘要不匹配')
        from .config_files import validate
        try:exported = validate(root, yaml.safe_load(content.decode('utf-8-sig')))
        except (yaml.YAMLError, ValueError, TypeError, AttributeError, KeyError):
            raise ConfigError('导出文件：字段 根映射：格式、类型或安全约束无效') from None
        if exported != config.settings:
            raise ConfigError('导出与当前完整配置不相等')
        directory = backup_dir(root, 'rollback')
        legacy = root / 'config/settings.local.yaml'
        if exists(legacy):
            plain_path(root, legacy)
            original = legacy.read_bytes()
            write_new(directory / 'settings.original.yaml', original)
        else:original = None
        saved = directory / 'split-backup'
        saved.mkdir()
        for name in LAYOUT:write_new(saved / name, (root / 'config/local' / name).read_bytes())
        # Extra files are preserved by archiving the complete directory last.
        record(directory, stage='prepared', source_digest=source_digest, export_digest=export_digest,
               previous_digest=sha(original) if original is not None else None)
        temporary = legacy.with_name('.rollback-' + uuid.uuid4().hex + '.tmp')
        legacy_written = archived = False
        def unchanged():
            require_stopped(root)
            if read_project(root).source_digest != source_digest or sha(export.read_bytes()) != export_digest:
                raise ConfigError('配置或导出改变，布局回滚未完成；config/local仍优先')
        try:
            write_new(temporary, content)
            unchanged()
            if (legacy.read_bytes() if exists(legacy) else None) != original:raise ConfigError('旧文件被其他操作者改变')
            os.replace(temporary, legacy)
            legacy_written = True
            record(directory, stage='legacy-written', source_digest=source_digest, export_digest=export_digest)
            unchanged()
            if legacy.read_bytes() != content:raise ConfigError('已写旧文件再次改变；分层入口保留')
            archive = directory / 'local-archived'
            if exists(archive):raise ConfigError('归档目标已存在')
            plain_path(root, directory, directory=True)
            publish_directory(root / 'config/local', archive)
            archived = True
            record(directory, stage='completed', source_digest=source_digest, export_digest=export_digest)
            return dict(layout='legacy', completed=True, backup=str(directory), restarted=False)
        except ConfigError:raise
        except (OSError, ValueError):
            if archived:
                raise ConfigError('布局已转换为最新单文件且local已归档；完成记录失败，请运行check核对，不要重复覆盖') from None
            if legacy_written:
                raise ConfigError('布局回滚未完成：最新单文件已写入，config/local仍优先；保留阶段备份，可修复后重试') from None
            raise
        finally:temporary.unlink(missing_ok=True)
