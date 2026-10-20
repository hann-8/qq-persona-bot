"""Explicit file-layout maintenance; ordinary use is edit then normal startup."""
import argparse
import json
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main(argv=None):
    from qqbot_gateway.config_files import read_project, ConfigError
    from qqbot_gateway.config_layout_ops import initialize, export_legacy, rollback_layout
    parser = argparse.ArgumentParser(description='分层配置文件工具；日常关闭→编辑→正常启动，check可选')
    parser.add_argument('--root', type=Path, default=ROOT, help='显式项目根目录')
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('check', 'init', 'migrate', 'export-legacy'):commands.add_parser(command)
    rollback = commands.add_parser('rollback-layout')
    rollback.add_argument('export', type=Path)
    rollback.add_argument('source_digest')
    rollback.add_argument('export_digest')
    rollback.add_argument('confirmation', choices=['已核对'])
    args = parser.parse_args(argv)
    try:
        if args.command == 'check':
            config = read_project(args.root)
            # Only known filenames/digests and unloaded filenames, no configuration values.
            result = dict(layout=config.layout, source_digest=config.source_digest,
                          semantic_digest=config.semantic_digest, files=config.files,
                          unloaded=list(config.unloaded), preserved_extensions=config.extensions,
                          extension_note='旧扩展仅保留，不保证有功能', effective='下次正常启动加载；本命令未更改运行实例')
        elif args.command in ('init', 'migrate'):
            result = initialize(args.root, migrate=args.command == 'migrate')
        elif args.command == 'export-legacy':result = export_legacy(args.root)
        else:result = rollback_layout(args.root, args.export, args.source_digest, args.export_digest, args.confirmation)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ConfigError as exc:print(str(exc), file=sys.stderr)
    except (ValueError, OSError, TypeError, yaml.YAMLError):
        print('配置操作失败：请检查文件格式、停机证明、配置锁或文件权限；未启停机器人。', file=sys.stderr)
    return 1


if __name__ == '__main__':raise SystemExit(main())
