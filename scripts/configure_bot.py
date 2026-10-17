"""Local configuration editor. No network calls or service lifecycle operations."""
import argparse
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
from qqbot_gateway.config import (read_settings, save_settings, qq_id,
                                  configuration_lock, require_stopped)
from qqbot_gateway.token_budget import known_models
from scripts.console_ui import Console

OUTPUT_FIELDS = {
    'delivery-mode': ('delivery_mode', '回复方式', 'single / adaptive；single兼容单条，adaptive闲聊最多3条/80字、认真问题单条'),
    'max-bubbles': ('max_bubbles', '最多条数', '整数1—3条，不凑条数，超限合并'),
    'casual-max-chars': ('casual_max_chars', '闲聊总长', '整数20—120字符，默认80；超限合并，不强切'),
    'bubble-max-chars': ('bubble_max_chars', '每条上限', '整数10—60字符，且不大于闲聊总长'),
    'delay-min-ms': ('bubble_delay_min_ms', '间隔下限', '整数0—5000毫秒；不大于间隔上限'),
    'delay-max-ms': ('bubble_delay_max_ms', '间隔上限', '整数0—5000毫秒；不小于间隔下限'),
}


def show(settings):
    access = settings['access']
    print(f"配置版本：{settings['schema_version']}；授权群 {len(access['allowed_groups'])} 个；黑名单 {len(access['blocked_users'])} 人")
    print('私聊关闭；管理员不豁免授权群或黑名单。完整ID仅在 groups/blacklist list 中显示。')
    print('修改前请关闭机器人；保存后下次启动生效。手工修改运行中的YAML也只在下次启动生效。')
    llm, chat = settings['llm'], settings['chat']
    print(f"模型：{llm['model']}；推理强度：{llm['reasoning_effort']}；输入预算：{chat['context_input_limit_tokens']}（可见UTF-8字节保守估算，非精确token）")
    print(f"开销预留：{chat['context_overhead_reserve_tokens']}；输出/推理预留：{chat['output_reserve_tokens']}；轮数：{chat['history_turns']}")
    print('原生窗口：未证实支持，仅auto可用；模型容量/支持强度按能力元数据核对，不承诺实际计费或未知模型容量。')
    print('下次启动将关闭常规自动压缩；CLI强制压缩/内部恢复仍有能力缺口，大上下文的严格单次推理合同未验收。')
    supported=known_models().get(llm['model'],{}).get('reasoning',{}).get('supportedEfforts',[])
    print('当前模型可显式选强度：'+('/'.join(supported) or '未知，仅auto'))
    print(f"回复方式：{settings['output']['delivery_mode']}；闲聊最多{settings['output']['max_bubbles']}条/{settings['output']['casual_max_chars']}字符，认真问题单条；切换后新上下文，旧历史保留。")


def parameter(settings, section, value):
    if section in OUTPUT_FIELDS:
        key = OUTPUT_FIELDS[section][0]
        if section != 'delivery-mode':
            if not isinstance(value, str) or len(value)>10 or not re.fullmatch(r'[0-9]+',value):
                raise ValueError('Output value must be a decimal integer')
            value = int(value)
        settings['output'][key] = value
    elif section == 'model': settings['llm']['model'] = value
    elif section == 'effort': settings['llm']['reasoning_effort'] = value
    elif section == 'context-window':
        if value != 'auto':
            raise ValueError('原生窗口未取得有效预算证据；当前只支持auto，请调整context输入预算')
        settings['llm']['context_window_tokens'] = None
    else:
        key={'context':'context_input_limit_tokens','history':'history_turns',
             'overhead':'context_overhead_reserve_tokens','output-reserve':'output_reserve_tokens'}[section]
        try:settings['chat'][key] = int(value)
        except (ValueError,TypeError):raise ValueError('预算或轮数必须为整数') from None


def execute(path, section, action, identifier=None, *, expected_digest=None):
    settings, digest = read_settings(path)
    if expected_digest is not None and digest != expected_digest:
        raise ValueError('Configuration changed; reload before saving')
    if section == 'show':
        show(settings)
        return
    if section in OUTPUT_FIELDS or section in ('model','context','context-window','effort','history','overhead','output-reserve'):
        parameter(settings,section,identifier)
        save_settings(path,settings,digest)
        print('参数已校验保存，下次启动生效；账号/站点不变。')
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


EFFORT_NAMES = {'auto':'自动', 'minimal':'最低', 'low':'低', 'medium':'中',
                'high':'高', 'xhigh':'更高', 'max':'最大'}


def effort_options(settings):
    supported = known_models().get(settings['llm']['model'], {}).get('reasoning', {}).get('supportedEfforts', [])
    return ['auto'] + list(dict.fromkeys(value for value in supported if value in EFFORT_NAMES and value != 'auto'))


def operation_error(error):
    """Translate known validation categories, never display arbitrary exception payloads."""
    if isinstance(error, ValueError):
        text = str(error)
        if 'Stop project processes' in text:
            return '请先关闭机器人，再重新进入本项修改。'
        if 'Cannot verify project is stopped' in text:
            return '无法确认机器人已停止，请先查看项目状态；本次未保存。'
        if 'operation already in progress' in text:
            return '另一项配置或启停操作正在进行，请稍后重新进入本项。'
        if 'Configuration changed' in text:
            return '配置已在别处更新，请重新进入本项读取最新值。'
        if 'Requested effort' in text:
            return '该模型与推理强度不兼容。先将推理强度设为自动（auto），再修改模型。'
        if 'exceeds known model capacity' in text:
            return '输入预算超过当前已知模型容量，请重新进入本项设置较小的值。'
        if 'allowed_groups' in text or 'Groups must' in text:
            return '至少保留一个授权群；移除最后一个群不会放行所有群。'
        if text == '该ID不在列表中':
            return '该完整ID不在当前列表中；请查看列表后重新输入。'
    return '本次未保存，旧配置保持完整。请检查本机文件权限和配置格式后重试。'


class ConfigMenu:
    ACCESS = {'1':('groups','list'), '2':('groups','add'), '3':('groups','remove'),
              '4':('blacklist','list'), '5':('blacklist','add'), '6':('blacklist','remove')}
    PARAMETERS = {'1':('model','set'), '2':('context','set'), '3':('effort','set'), '4':('history','set')}

    def __init__(self, path, console=None):
        self.path = path
        self.ui = console or Console()

    def run(self):
        while True:
            settings, _ = read_settings(self.path)
            access, llm, chat = settings['access'], settings['llm'], settings['chat']
            self.ui.page('机器人配置')
            self.ui.write(f"模型：{llm['model']}")
            self.ui.write(f"推理强度：{EFFORT_NAMES.get(llm['reasoning_effort'], llm['reasoning_effort'])}（{llm['reasoning_effort']}）")
            self.ui.write(f"授权群：{len(access['allowed_groups'])} 个    黑名单：{len(access['blocked_users'])} 人    记忆：{chat['history_turns']} 轮")
            self.ui.write(f"输入预算：{chat['context_input_limit_tokens']:,}（可见内容保守计数）")
            self.ui.write('\n1  群与黑名单\n2  模型与对话\n3  详细设置与能力说明\n4  回复方式\n0  退出')
            self.ui.write('\n修改前请先关闭机器人；保存后，下次启动生效')
            choice = self.ui.choose({'0','1','2','3','4'})
            if choice == '0':return
            if choice == '4':self.output_group()
            elif choice == '3':
                self.ui.page('详细设置与能力说明')
                content = StringIO()
                with redirect_stdout(content):show(settings)
                self.ui.write(content.getvalue().rstrip())
                self.ui.pause()
            else:self.group(choice)

    def output_group(self):
        fields = list(OUTPUT_FIELDS.items())
        while True:
            settings, digest = read_settings(self.path)
            self.ui.page('回复方式')
            self.ui.write('single保持单条；adaptive一次生成，闲聊最多3条/80字，认真问题单条。')
            self.ui.write('改变提示规则会开始新上下文，旧历史保留；保存后须协调关闭/启动，不热生效。')
            for i, (name,(key,title,help_text)) in enumerate(fields,1):
                self.ui.write(f'{i}  {title}：{settings["output"][key]}；{help_text}')
            self.ui.write('0  返回')
            choice = self.ui.choose({'0'} | {str(i) for i in range(1,len(fields)+1)})
            if choice == '0':return
            name,(key,title,help_text) = fields[int(choice)-1]
            self.ui.page(title)
            self.ui.write(help_text+'；空回车保留；保存后下次启动生效。')
            value = self.ui.read('请输入值：').strip()
            if value:
                try:
                    execute(self.path,name,'set',value,expected_digest=digest)
                    self.ui.write('已保存，下次启动生效。')
                except (ValueError,OSError) as error:
                    self.ui.write(operation_error(error)+' 请核对整数范围及上下限关系。')
            else:self.ui.write('已取消，原值保留。')
            self.ui.pause()

    def group(self, category):
        choices = self.ACCESS if category == '1' else self.PARAMETERS
        while True:
            settings, _ = read_settings(self.path)
            self.ui.page('群与黑名单' if category == '1' else '模型与对话')
            if category == '1':
                self.ui.write(f"授权群：{len(settings['access']['allowed_groups'])} 个；黑名单：{len(settings['access']['blocked_users'])} 人")
                self.ui.write('\n1  查看授权群\n2  添加授权群\n3  移除授权群\n4  查看黑名单\n5  屏蔽用户\n6  解除屏蔽')
            else:
                llm, chat = settings['llm'], settings['chat']
                self.ui.write(f"1  模型ID      {llm['model']}\n2  输入预算    {chat['context_input_limit_tokens']:,}\n3  推理强度    {llm['reasoning_effort']}\n4  记忆轮数    {chat['history_turns']} 轮")
            self.ui.write('\n0  返回')
            choice = self.ui.choose(set(choices) | {'0'})
            if choice == '0':return
            section, action = choices[choice]
            if action == 'list':self.list_page(settings, section)
            else:self.edit(section, action)

    def list_values(self, settings, section):
        key = 'allowed_groups' if section == 'groups' else 'blocked_users'
        values = settings['access'][key]
        for index, value in enumerate(values, 1):self.ui.write(f'  {index}.  {value}')
        if not values:self.ui.write('  当前列表为空。')
        return values

    def list_page(self, settings, section):
        self.ui.page('授权群列表' if section == 'groups' else '黑名单列表')
        self.list_values(settings, section)
        self.ui.write('\n序号仅用于展示；移除时需要输入完整群号或QQ号。')
        self.ui.pause()

    def edit(self, section, action):
        settings, digest = read_settings(self.path)
        choices = None
        if section in ('groups','blacklist'):
            group = section == 'groups'
            noun = '群号' if group else 'QQ号'
            title = ('添加授权群' if action == 'add' else '移除授权群') if group else ('屏蔽用户' if action == 'add' else '解除屏蔽')
            self.ui.page(title)
            self.ui.write('只处理已加入的授权群内真实@，不会自动加群；至少保留一个授权群。' if group else
                          '对所有授权群生效，管理员也不豁免；不会删除旧历史。解除后仍需真实@。')
            values = self.list_values(settings, section)
            if action == 'remove' and not values:self.ui.pause();return
            self.ui.write(f'输入完整{noun}，不是上面的展示序号。格式：正整数；示例：'+('123456789' if group else '234567890'))
            prompt = f'请输入'+('要移除的完整' if action == 'remove' else '')+noun+'（回车取消）：'
        else:
            title = {'model':'模型ID','context':'输入预算','effort':'推理强度','history':'记忆轮数'}[section]
            self.ui.page(title)
            if section == 'model':
                current = settings['llm']['model']
                self.ui.write('填写站点使用的字符串模型ID，不是菜单编号或展示名。示例：deepseek-v4.1-flash')
                self.ui.write('以字母或数字开头，可含 . _ : / -，最多128个字符。')
                self.ui.write('不保证账号可用或免费；若与现有强度冲突，先返回将强度设为auto。')
            elif section == 'context':
                current = settings['chat']['context_input_limit_tokens']
                self.ui.write('限制送入模型的固定设定、当前问题、历史与开销。范围：1024—1048576；默认16384仅作参考。')
                self.ui.write('内部按可见UTF-8字节保守计数，非精确token、模型原生窗口或计费上限。')
                self.ui.write('较大预算不代表模型支持同样大的窗口；CLI内部强制压缩/恢复问题尚未解决。')
                self.ui.write('输入不带单位的十进制整数，例如32768；已知模型容量限制可能更小。')
            elif section == 'history':
                current = settings['chat']['history_turns']
                self.ui.write('范围：1—64轮；默认8轮仅作参考，包含当前这轮。1代表不携带旧轮次。')
                self.ui.write('不会删除存储历史；输入预算仍会裁剪旧轮次。请填整数，例如8。')
            else:
                current = settings['llm']['reasoning_effort']
                choices = effort_options(settings)
                for index, effort in enumerate(choices, 1):
                    description = '跟随模型产品默认，不等于关闭推理' if effort == 'auto' else '当前能力快照支持的档位'
                    self.ui.write(f'{index}  {EFFORT_NAMES[effort]}  {effort}  {description}')
                self.ui.write('数字只是选择编号，不是token数；耗时/消耗依模型实际行为。')
                if choices == ['auto']:self.ui.write('当前模型能力未知，仅允许auto；不会发起模型探测。')
            self.ui.write(f'\n当前{title}：{current}')
            prompt = '请选择编号或英文值（回车保留）：' if choices else f'请输入{title}（回车保留）：'
        self.ui.write('\n保存后下次启动生效；空回车保留原值。')
        while True:
            value = self.ui.read(prompt).strip()
            if not value:
                self.ui.write('已取消，原值保留。');self.ui.pause();return
            if choices:
                value = value.lower()
                if value in {str(i) for i in range(1,len(choices)+1)}:value=choices[int(value)-1]
                if value not in choices:
                    self.ui.write('请选择当前页面支持的编号或英文值：'+', '.join(choices));continue
            elif section in ('groups','blacklist') and qq_id(value) is None:
                self.ui.write(f'请填写一个完整的正整数{noun}，例如'+('123456789。' if group else '234567890。'));continue
            elif section in ('context','history'):
                lower, upper = (1024,1048576) if section == 'context' else (1,64)
                if len(value)>32 or not re.fullmatch(r'[0-9]+',value) or not lower <= int(value) <= upper:
                    self.ui.write(f'{title}必须是{lower}—{upper}范围内、不带单位的整数。');continue
            elif section == 'model' and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}', value):
                self.ui.write('模型ID格式不正确：请填写最多128字符、以字母或数字开头的模型ID。');continue
            content = StringIO()
            try:
                with redirect_stdout(content):execute(self.path,section,action,value,expected_digest=digest)
                self.ui.write(f'\n{title}：'+content.getvalue().strip())
            except (ValueError,OSError) as error:
                self.ui.write('\n'+operation_error(error))
            self.ui.pause()
            return  # Re-entering an edit always reloads the latest snapshot/digest.


def menu(path, console=None):
    ConfigMenu(path, console).run()


def main():
    parser = argparse.ArgumentParser(description='本机授权群/黑名单配置，停止后保存、下次启动生效')
    commands = parser.add_subparsers(dest='section')
    commands.add_parser('show')
    for section in (*OUTPUT_FIELDS,'model','context','context-window','effort','history','overhead','output-reserve'):
        actions=commands.add_parser(section).add_subparsers(dest='action',required=True)
        actions.add_parser('set').add_argument('identifier')
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
    except (ValueError, OSError) as error:
        # Parser errors may contain secrets or user supplied YAML; never print them.
        print('配置操作失败：检查配置格式、ID、停止状态和并发修改。旧配置保持完整。', file=sys.stderr)
        if isinstance(error,ValueError):print(str(error),file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print('\n已退出。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
