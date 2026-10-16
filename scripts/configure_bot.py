"""Local configuration editor. No network calls or service lifecycle operations."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from qqbot_gateway.config import (read_settings, save_settings, qq_id,
                                  configuration_lock, require_stopped)


def show(settings):
    access = settings['access']
    print(f"配置版本：{settings['schema_version']}；授权群 {len(access['allowed_groups'])} 个；黑名单 {len(access['blocked_users'])} 人")
    print('私聊关闭；管理员不豁免授权群或黑名单。完整ID仅在 groups/blacklist list 中显示。')
    print('修改前请关闭机器人；保存后下次启动生效。手工修改运行中的YAML也只在下次启动生效。')
    print('模型、上下文、推理强度及输出设置入口待后续任务开放。')


def execute(path, section, action, identifier=None):
    settings, digest = read_settings(path)
    if section == 'show':
        show(settings)
        return
    key = {'groups': 'allowed_groups', 'blacklist': 'blocked_users'}[section]
    values = settings['access'][key]
    if action == 'list':
        print('本机列表：' + ('、'.join(values) or '空'))
        return
    identifier = qq_id(identifier)
    if identifier is None:
        raise ValueError('群号/QQ号必须是规范的正整数')
    # Even no-op writes are rejected while the project is running.
    if action == 'add':
        if identifier in values:
            with configuration_lock(path.parent.parent):
                require_stopped(path.parent.parent)
            print('该ID已存在，无需重复保存。')
            return
        values.append(identifier)
    elif action == 'remove':
        if identifier not in values:
            raise ValueError('该ID不在列表中')
        values.remove(identifier)
    save_settings(path, settings, digest)
    print('已校验并保存；旧配置备份位于 state/config-backups/。下次启动生效。')


def menu(path):
    choices = {'1': ('groups', 'list'), '2': ('groups', 'add'), '3': ('groups', 'remove'),
               '4': ('blacklist', 'list'), '5': ('blacklist', 'add'), '6': ('blacklist', 'remove')}
    while True:
        execute(path, 'show', None)
        print('1 查看授权群  2 添加授权群  3 移除授权群\n4 查看黑名单  5 添加黑名单  6 移除黑名单  0 退出')
        choice = input('请选择：').strip()
        if choice == '0':
            return
        if choice not in choices:
            print('请选择菜单中的编号。'); continue
        section, action = choices[choice]
        identifier = input('输入群号/QQ号：').strip() if action != 'list' else None
        try:
            execute(path, section, action, identifier)
        except (ValueError, OSError):
            print('操作失败：请检查ID、非空授权群、停止状态或并发修改；未覆盖旧配置。')


def main():
    parser = argparse.ArgumentParser(description='本机授权群/黑名单配置，停止后保存、下次启动生效')
    commands = parser.add_subparsers(dest='section')
    commands.add_parser('show')
    for section in ('groups', 'blacklist'):
        actions = commands.add_parser(section).add_subparsers(dest='action', required=True)
        actions.add_parser('list')
        for action in ('add', 'remove'):
            actions.add_parser(action).add_argument('identifier')
    args = parser.parse_args()
    path = ROOT / 'config/settings.local.yaml'
    try:
        if args.section is None:
            menu(path)
        else:
            execute(path, args.section, getattr(args, 'action', None), getattr(args, 'identifier', None))
    except (ValueError, OSError):
        # Parser errors may contain secrets or user supplied YAML; never print them.
        print('配置操作失败：检查配置格式、ID、停止状态和并发修改。旧配置保持完整。', file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print('\n已退出。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
