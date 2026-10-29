"""Stopped configuration writes and explicit metadata-only connection checks."""
import argparse
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
from qqbot_gateway.config import (save_settings, qq_id,
                                  configuration_lock, require_stopped)
from qqbot_gateway.config_files import (read_management as read_settings, management_root, reject_legacy_write, ConfigError)
from qqbot_gateway.token_budget import known_models
from qqbot_gateway.backends import resolve_backend
from qqbot_gateway.errors import GatewayError, MESSAGES
from scripts.console_ui import Console

OUTPUT_FIELDS = {
    'delivery-mode': ('delivery_mode', '回复方式', 'single / adaptive；single兼容单条，adaptive闲聊最多3条/80字、认真问题单条'),
    'max-bubbles': ('max_bubbles', '最多条数', '整数1—3条，不凑条数，超限合并'),
    'casual-max-chars': ('casual_max_chars', '闲聊总长', '整数20—120字符，默认80；超限合并，不强切'),
    'bubble-max-chars': ('bubble_max_chars', '每条上限', '整数10—60字符，且不大于闲聊总长'),
    'delay-min-ms': ('bubble_delay_min_ms', '间隔下限', '整数0—5000毫秒；不大于间隔上限'),
    'delay-max-ms': ('bubble_delay_max_ms', '间隔上限', '整数0—5000毫秒；不小于间隔下限'),
}


def budget_view(settings):
    return settings['chat'] | resolve_backend(settings)['input_budget']


def show(settings):
    access = settings['access']
    print(f"配置版本：{settings['schema_version']}；授权群 {len(access['allowed_groups'])} 个；黑名单 {len(access['blocked_users'])} 人")
    print('私聊关闭；管理员不豁免授权群或黑名单。完整ID仅在 groups/blacklist list 中显示。')
    print('修改前请关闭机器人；保存后下次启动生效。手工修改运行中的YAML也只在下次启动生效。')
    llm, chat = resolve_backend(settings), budget_view(settings)
    print('当前后端：'+llm['backend'])
    if llm['backend']=='ollama_ssh':
        print('请求参数：'+str({k:llm[k] for k in ('num_ctx','think','num_predict','keep_alive_seconds')}))
        print('元数据须显式只读检查；实际生效/生成质量未验。标称最大窗口不是实际窗口。')
    print(f"模型：{llm['model']}；推理强度：{llm.get('reasoning_effort','关闭思考')}；输入预算：{chat['context_input_limit_tokens']}（可见UTF-8字节保守估算，非精确token）")
    print(f"开销预留：{chat['context_overhead_reserve_tokens']}；输出/推理预留：{chat['output_reserve_tokens']}；轮数：{chat['history_turns']}")
    if llm['backend']=='codebuddy_cli':
        print('原生窗口：未证实支持，仅auto可用；模型容量/支持强度按能力元数据核对，不承诺实际计费或未知模型容量。')
        print('下次启动将关闭常规自动压缩；CLI强制压缩/内部恢复仍有能力缺口，大上下文的严格单次推理合同未验收。')
        supported=known_models().get(llm['model'],{}).get('reasoning',{}).get('supportedEfforts',[])
        print('当前模型可显式选强度：'+('/'.join(supported) or '未知，仅auto'))
    print(f"回复方式：{settings['output']['delivery_mode']}；闲聊最多{settings['output']['max_bubbles']}条/{settings['output']['casual_max_chars']}字符，认真问题单条；切换后新上下文，旧历史保留。")
    print(f"共用网页：{settings.get('web',{}).get('enabled',False)}；搜索候选未通过质量门槛，仅受控公共URL读取；不上传历史。")
    from qqbot_gateway.members import suspend_unverified
    effective=suspend_unverified(settings)
    print(f"小群成员：desired={settings['members']['enabled']}；effective={effective['enabled']}；受控@={effective['mentions_enabled']}；仅官方Snow v2.1.1强刷人数1..49，失败暂停增强。")
    print(f"原生识图：desired={settings['vision']['enabled']}；生产不可启用（模板/视觉token上界与原生容量未验证）；reserve={settings['vision']['input_reserve_tokens']}仅假设。")
    print(f"本群长期记忆：{settings['memory']['enabled']}；学习：{settings['memory']['learning_enabled']}；默认关闭，本机管理见7→22。")


def parameter(settings, section, value):
    if section in OUTPUT_FIELDS:
        key = OUTPUT_FIELDS[section][0]
        if section != 'delivery-mode':
            if not isinstance(value, str) or len(value)>10 or not re.fullmatch(r'[0-9]+',value):
                raise ValueError('Output value must be a decimal integer')
            value = int(value)
        settings['output'][key] = value
    elif section == 'backend':settings['llm']['backend'] = value
    elif section == 'model': settings['llm']['profiles'][settings['llm']['backend']]['model'] = value
    elif section == 'effort':
        if settings['llm']['backend']!='codebuddy_cli':raise ValueError('Local backend supports only think:false')
        settings['llm']['profiles']['codebuddy_cli']['reasoning_effort'] = value
    elif section == 'context-window':
        if value != 'auto':
            raise ValueError('原生窗口未取得有效预算证据；当前只支持auto，请调整context输入预算')
        if settings['llm']['backend']!='codebuddy_cli':raise ValueError('Use local num_ctx')
        settings['llm']['profiles']['codebuddy_cli']['context_window_tokens'] = None
    else:
        key={'context':'context_input_limit_tokens','history':'history_turns',
             'overhead':'context_overhead_reserve_tokens','output-reserve':'output_reserve_tokens'}[section]
        target = settings['chat'] if section == 'history' else settings['llm']['profiles'][settings['llm']['backend']]['input_budget']
        try:target[key] = int(value)
        except (ValueError,TypeError):raise ValueError('预算或轮数必须为整数') from None


def execute(path, section, action, identifier=None, *, expected_digest=None):
    settings, digest = read_settings(path)
    if expected_digest is not None and digest != expected_digest:
        raise ValueError('Configuration changed; reload before saving')
    if section == 'napcat-login' and action in ('set-observer-token','clear-observer-token','observer-status'):
        import json
        from qqbot_gateway.napcat_login_observer import configure_token
        print(json.dumps(configure_token(path,action),ensure_ascii=False));return
    if section == 'napcat-login':
        import json
        from qqbot_gateway.napcat_login import configure_credentials
        print(json.dumps(configure_credentials(path,action),ensure_ascii=False))
        return
    if section in ('connection-check','connection-init','clear-remote-unknown'):
        root=management_root(path)
        def unchanged():
            if read_settings(path)[1]!=digest:raise ValueError('Configuration changed')
        local=resolve_backend(settings,'ollama_ssh')
        if section=='connection-init':
            from qqbot_gateway.ssh_transport import initialize_access
            initialize_access(root,local['access_file'],config_guard=unchanged)
            print('已初始化项目内DPAPI连接资料，未切换后端。')
        elif section=='clear-remote-unknown':
            from qqbot_gateway.ollama_ssh_runner import clear_unknown
            clear_unknown(root,identifier,config_guard=unchanged);print('已按操作者确认解除；未推理/重启。')
        else:
            import asyncio,json
            from qqbot_gateway.ollama_ssh_runner import OllamaSSHRunner
            from qqbot_gateway.token_budget import InputBudget
            unchanged()
            print(json.dumps(asyncio.run(OllamaSSHRunner(root,local,InputBudget()).preflight(require_digest=False)),ensure_ascii=False))
        return
    if section == 'export-legacy-config':
        reject_legacy_write(path)
        from qqbot_gateway.config import export_legacy_config
        import json
        print(json.dumps(export_legacy_config(path),ensure_ascii=False))
        return
    if section == 'show':
        show(settings)
        return
    if section in OUTPUT_FIELDS or section in ('backend','model','context','context-window','effort','history','overhead','output-reserve'):
        reject_legacy_write(path)
        parameter(settings,section,identifier)
        save_settings(path,settings,digest)
        print('参数已校验保存，下次启动生效；账号/站点不变。')
        return
    key = {'groups': 'allowed_groups', 'blacklist': 'blocked_users'}[section]
    values = settings['access'][key]
    if action == 'list':
        print('本机列表：' + ('、'.join(values) or '空'))
        return
    reject_legacy_write(path)
    identifier = qq_id(identifier)
    if identifier is None:
        raise ValueError('群号/QQ号必须是规范的正整数')
    # Even no-op writes are rejected while the project is running.
    if action == 'add':
        if identifier in values:
            with configuration_lock(management_root(path)):
                require_stopped(management_root(path))
            print('该ID已存在，无需重复保存。')
            return
        values.append(identifier)
    elif action == 'remove':
        if identifier not in values:
            raise ValueError('该ID不在列表中')
        values.remove(identifier)
    save_settings(path, settings, digest)
    print('已校验并保存；旧配置备份位于 state/config-backups/。下次启动生效。')


_MEMORY_MANAGER=None

def memory_action(path,group,action,*,config_digest=None,**fields):
    """Stopped + config digest + memory digest; same OS/JSON locks as runtime."""
    from qqbot_gateway.group_memory import MemoryStore
    global _MEMORY_MANAGER
    with configuration_lock(management_root(path)):
        require_stopped(management_root(path))
        settings,current=read_settings(path)
        if config_digest is not None and config_digest!=current:raise ValueError('Configuration changed')
        if group not in settings['access']['allowed_groups']:raise ValueError('Unauthorized group')
        if not settings['memory']['enabled']:raise ValueError('Enable memory explicitly first')
        identity=(str(path.resolve()),current)
        # One stopped management session shares one recovered store. Repeating
        # startup blacklist purge between inspect and confirm would otherwise
        # rotate generation and invalidate every reviewed memory digest.
        if _MEMORY_MANAGER is None or _MEMORY_MANAGER[0]!=identity:
            _MEMORY_MANAGER=(identity,MemoryStore(management_root(path),settings['bot']['qq'],settings['access']['allowed_groups'],settings['access']['blocked_users'],settings['access']['admin_users'],settings['memory']))
        store=_MEMORY_MANAGER[1]
        return store.manage(group,action,**fields)


EFFORT_NAMES = {'auto':'自动', 'minimal':'最低', 'low':'低', 'medium':'中',
                'high':'高', 'xhigh':'更高', 'max':'最大'}


def effort_options(settings):
    supported = known_models().get(resolve_backend(settings)['model'], {}).get('reasoning', {}).get('supportedEfforts', [])
    return ['auto'] + list(dict.fromkeys(value for value in supported if value in EFFORT_NAMES and value != 'auto'))


def operation_error(error):
    """Translate known validation categories, never display arbitrary exception payloads."""
    if isinstance(error,ConfigError):return str(error)
    if isinstance(error,GatewayError):return MESSAGES[error.code]
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
        if 'Catalog changed' in text:
            return '表情目录已在别处更新，请返回列表重新选择，避免覆盖。'
        if text == 'Confirm name and tags before enabling':
            return '启用图片必须填写名称和至少一个标签；使用语境不能代替标签。'
        if text == 'Invalid meme tags':
            return '标签最多8个；请用逗号分隔，启用时至少填写一个。'
        if text == 'Invalid meme label':
            return '名称、语境及每个标签最多80字符，不能包含换行、URL、file或base64内容。'
        if 'Requested effort' in text:
            return '该模型与推理强度不兼容。先将推理强度设为自动（auto），再修改模型。'
        if 'exceeds known model capacity' in text:
            return '输入预算超过当前已知模型容量，请重新进入本项设置较小的值。'
        if 'Confirm local model digest' in text:
            return '先在后端与连接页只读检查模型，再把核对的digest填入本地profile；本次未切换。'
        if 'Provider timeout' in text:
            return '排队等待+当前后端生成期限+25秒预留超过provider的180秒，请减小期限。'
        if 'Conflicting legacy/profile' in text:
            return '新旧配置字段冲突，请对照备份核对；本次未覆盖任何值。'
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
        self.path = Path(path)
        self.root = management_root(self.path)
        self.ui = console or Console()

    def run(self):
        while True:
            settings, _ = read_settings(self.path)
            access, llm, chat = settings['access'], resolve_backend(settings), budget_view(settings)
            self.ui.page('机器人配置')
            self.ui.write(f"当前后端：{llm['backend']}；模型：{llm['model']}")
            self.ui.write(f"推理强度：{EFFORT_NAMES.get(llm.get('reasoning_effort','关闭思考'), llm.get('reasoning_effort','关闭思考'))}（{llm.get('reasoning_effort','关闭思考')}）")
            self.ui.write(f"授权群：{len(access['allowed_groups'])} 个    黑名单：{len(access['blocked_users'])} 人    记忆：{chat['history_turns']} 轮")
            self.ui.write(f"输入预算：{chat['context_input_limit_tokens']:,}（可见内容保守计数）")
            self.ui.write('\n1  群与黑名单\n2  模型与对话\n3  详细设置与能力说明\n4  回复方式\n5  后端与连接\n6  联网搜索\n0  退出')
            self.ui.write('\n修改前请先关闭机器人；保存后，下次启动生效')
            self.ui.write('7  群聊参与与活跃度\n8  表情包')
            choice = self.ui.choose({'0','1','2','3','4','5','6','7','8'})
            if choice == '0':return
            if choice == '8':self.memes_group()
            elif choice == '7':self.participation_group()
            elif choice == '6':self.web_group()
            elif choice == '5':self.backend_group()
            elif choice == '4':self.output_group()
            elif choice == '3':
                self.ui.page('详细设置与能力说明')
                content = StringIO()
                with redirect_stdout(content):show(settings)
                self.ui.write(content.getvalue().rstrip())
                self.ui.pause()
            else:self.group(choice)

    def memes_group(self, *, admin_only=False):
        from qqbot_gateway.meme_catalog import MemeCatalog,DEFAULTS,controlled_path
        from qqbot_gateway.meme_import import favorites,admin_token
        import asyncio,os,aiohttp
        root=self.root
        while True:
            settings,digest=read_settings(self.path)
            self.ui.page('表情包')
            self.ui.write('默认关闭；扫描/标签/激活须停机，重启生效。收藏仅在现有机器人连接可用时显式读取，绝不启动或登录。导入暂存后须停机激活并确认标签。真实收藏/显示未验。')
            self.ui.write('1 打开本地inbox / 2 扫描本地表情 / 3 初始化独立管理token / 4 从机器人QQ收藏详情导入 / 5 基础接口导入（仅显式选择） / 6 停机激活暂存 / 7 看图填写标签 / 0 返回'+('' if admin_only else ' / 8 表情参数'))
            if admin_only:self.ui.write('维护模式：参数请编辑config/local/features.yaml；8不可用。')
            choice=self.ui.choose({str(i) for i in range(8 if admin_only else 9)})
            if choice=='0':return
            try:
                guard=self.config_guard(digest)
                catalog=MemeCatalog(root,settings['memes'],config_guard=guard)
                if choice=='1':
                    folder=controlled_path(root,settings['memes']['inbox_dir']);folder.mkdir(parents=True,exist_ok=True);os.startfile(folder)
                elif choice=='2':self.ui.write('扫描接收/拒绝数量：'+str(catalog.scan()))
                elif choice=='3':
                    admin_token(root,create=True);self.ui.write('独立管理token已准备在项目secrets内；下次正常启动gate时加载。未显示token、未启停。')
                elif choice in ('4','5'):
                    result=asyncio.run(favorites(root,settings['memes'],settings['onebot']['port'],basic=choice=='5',config_guard=guard))
                    self.ui.write('暂存接收/失败数量：'+str(result)+'；停机激活后再填写标签，未启用memes。')
                elif choice=='6':catalog.activate_pending();self.ui.write('已停机激活；请确认名称/标签后重启。')
                elif choice=='7':
                    self.label_memes(settings['memes'],config_digest=digest)
                elif choice=='8':
                    keys=list(DEFAULTS)
                    for i,key in enumerate(keys,1):self.ui.write(f'{i} {key}: {settings["memes"][key]}')
                    self.ui.write('enabled/allow_meme_only: true或false；候选1..32/字节500..4000；单轮图片固定1；冷却0..600秒/同图0..3600秒；文件1048576..8388608字节；导入1..48；路径固定项目忽略位置。')
                    value=self.ui.read('参数序号（回车取消）：').strip()
                    if not value:continue
                    key=keys[int(value)-1];value=self.ui.read('新值：').strip()
                    if type(DEFAULTS[key]) is bool:
                        if value not in ('true','false'):raise ValueError()
                        value=value=='true'
                    elif type(DEFAULTS[key]) is int:value=int(value)
                    settings['memes'][key]=value;save_settings(self.path,settings,digest)
                    self.ui.write('配置已保存，须重启生效；未启停或发图。')
            except (ValueError,OSError,IndexError,TimeoutError,aiohttp.ClientError):self.ui.write('操作未完成：检查连接、停机状态、目录、标签和参数；未自动重试/登录/扩域。')
            self.ui.pause()

    def config_guard(self,digest):
        def unchanged():
            if read_settings(self.path)[1]!=digest:raise ValueError('Configuration changed')
        return unchanged

    def label_memes(self,cfg,*,config_digest=None):
        from qqbot_gateway.meme_catalog import MemeCatalog
        import os
        while True:
            catalog=MemeCatalog(self.root,cfg,config_guard=self.config_guard(config_digest) if config_digest is not None else None)
            if not catalog.rows:
                self.ui.write('图库为空，请先扫描本地图片或激活收藏导入暂存。');return
            self.ui.page('看图填写表情标签')
            for i,row in enumerate(catalog.rows,1):
                self.ui.write(f'{i}  {row["name"] or "未命名"}  {Path(row["file"]).suffix[1:].upper()}  '+('已启用' if row['enabled'] else '未启用'))
            self.ui.write('P 打开带编号的图片预览总览；输入编号打开该张原图，再决定是否编辑。预览不启用/发送图片，不修改目录。')
            value=self.ui.read('输入 P 或图片编号（回车返回）：').strip()
            if not value:return
            try:
                if value.lower()=='p':
                    page=catalog.preview_page();os.startfile(page)
                    self.ui.write('编号预览页已打开；看图后回到这里选择相同编号。');continue
                if not value.isdecimal() or not 1<=int(value)<=len(catalog.rows):
                    self.ui.write('请输入列表中的图片编号，或输入 P 看全部图片。');continue
                row=catalog.rows[int(value)-1]
                image,_=catalog.preview(row['id']);os.startfile(image)
            except (ValueError,OSError):
                self.ui.write('图片预览失败：请检查图片完整性或系统默认打开方式；尚未修改标签或保存目录。')
                self.ui.pause()
                continue
            self.ui.write(f'已打开第{value}张图片：{row["name"] or "未命名"}')
            if self.ui.read('确认是这张？输入 E 编辑名称/标签，回车重选：').strip().lower()!='e':continue
            for key,title in (('name','简短名称'),('context','简短使用语境')):
                row[key]=self.ui.read(f'{title}（当前：{row[key] or "未填写"}；回车保留）：').strip() or row[key]
            value=self.ui.read('标签（首次启用至少填1个，逗号分隔；已有标签回车保留）：').strip()
            if value:row['tags']=[x.strip() for x in value.replace('，',',').split(',') if x.strip()]
            row['enabled']=self.ui.read('确认登记并启用此图？输入 YES，其余禁用：').strip()=='YES'
            cancelled=False
            while row['enabled'] and (not row['name'].strip() or not row['tags']):
                missing='name' if not row['name'].strip() else 'tags'
                self.ui.write('尚未保存：启用图片必须有名称和至少一个标签。已填写的名称/语境保留；使用语境不能代替标签。')
                value=self.ui.read(('补填名称' if missing=='name' else '补填至少一个标签（逗号分隔）')+'，输入0取消编辑：').strip()
                if value=='0':cancelled=True;break
                if missing=='name':row['name']=value
                else:row['tags']=[x.strip() for x in value.replace('，',',').split(',') if x.strip()]
            if not cancelled:self.save_meme_draft(catalog,row)

    def save_meme_draft(self,catalog,row):
        while True:
            try:
                catalog.validate_row(row)
                catalog.save()
            except (ValueError,OSError) as error:
                self.ui.write('表情目录未保存：'+operation_error(error))
                if self.ui.read('已填写内容暂时保留；输入 R 重试保存，回车返回列表且不保存：').strip().lower()!='r':return
            else:
                self.ui.write('目录已保存，下次启动生效；未调用模型或发图。')
                self.ui.pause();return

    def participation_group(self):
        from qqbot_gateway.participation import DEFAULTS,RANGES
        while True:
            settings,digest=read_settings(self.path)
            self.ui.page('群聊参与与活跃度')
            self.ui.write('free会读取授权群启动后的新消息，即使沉默也可能消耗模型额度。真实@优先；无新消息不生成。保存须停机，重启生效；全模式直接群发，无引用/自动@。')
            self.ui.write('seconds单位为秒，per_minute为每分钟轮次；context_messages为条数，context_max_bytes为UTF-8字节，message_max_chars为字符；mention_queue_limit为每群等待数。')
            keys=list(DEFAULTS)
            for index,key in enumerate(keys,1):
                bounds=f'{RANGES[key][0]}..{RANGES[key][1]}' if key in RANGES else ('mentions/free' if key=='mode' else 'true/false')
                self.ui.write(f'{index} {key}: {settings["participation"][key]} ({bounds})')
            self.ui.write('17 核对后解除本群未知发送隔离 / 18 关注与续聊 / 19 导出旧版配置审阅副本 / 20 原生识图 / 21 小群成员与受控@ / 22 本群长期记忆 / 0 返回')
            choice=self.ui.choose({'0','17','18','19','20','21','22'}|{str(i) for i in range(1,len(keys)+1)})
            if choice=='0':return
            if choice=='22':
                self.memory_group();continue
            if choice=='21':
                self.members_group();continue
            if choice=='20':
                self.vision_group();continue
            if choice=='19':
                try:execute(self.path,'export-legacy-config',None)
                except (ValueError,OSError) as error:self.ui.write(operation_error(error))
                self.ui.pause();continue
            if choice=='18':
                self.attention_group();continue
            if choice=='17':
                from qqbot_gateway.task_store import TaskStore
                group=self.ui.read('已在QQ核对发送结果的授权群号：').strip()
                if group not in settings['access']['allowed_groups']:
                    self.ui.write('必须选择授权群。');self.ui.pause();continue
                if self.ui.read('不会重发任何旧内容；输入“已核对”继续：').strip()!='已核对':continue
                try:
                    with configuration_lock(self.root):
                        require_stopped(self.root)
                        store=TaskStore(self.root/'state/tasks.sqlite')
                        try:store.review_group(group)
                        finally:store.close()
                    self.ui.write('已解除；原未知ACK证据保留，没有重发。')
                except (ValueError,OSError,RuntimeError) as error:self.ui.write(operation_error(error))
                self.ui.pause();continue
            key=keys[int(choice)-1];value=self.ui.read('新值（回车保留）：').strip()
            if not value:continue
            try:
                if key=='allow_ambient_web':
                    if value not in ('true','false'):raise ValueError('Expected true/false')
                    value=value=='true'
                elif key in ('debounce_seconds','max_batch_wait_seconds'):value=float(value)
                elif key in RANGES:value=int(value)
                settings['participation'][key]=value
                save_settings(self.path,settings,digest)
                self.ui.write('已保存，下次启动生效。没有启停/读取群消息/调用模型。')
            except (ValueError,OSError) as error:self.ui.write(operation_error(error)+' 请核对页面范围。')
            self.ui.pause()

    def memory_group(self, *, admin_only=False):
        settings,digest=read_settings(self.path)
        self.ui.page('本群长期记忆（默认关闭）')
        self.ui.write('有限JSON主库/MD只读视图；学习不增加模型调用。保存/管理须停机，下次启动加载。删除同时净化副本；失败不代表删除完成。')
        self.ui.write('3 本机查看与管理 / 0 返回' if admin_only else f"1 enabled={settings['memory']['enabled']} / 2 learning_enabled={settings['memory']['learning_enabled']} / 3 本机查看与管理 / 0 返回")
        if admin_only:self.ui.write('维护模式：开关请编辑config/local/features.yaml；仅3和0可用。')
        choice=self.ui.choose({'0','3'} if admin_only else {'0','1','2','3'})
        if choice=='0':return
        try:
            if choice in ('1','2'):
                value=self.ui.read('新值 true/false（回车保留）：').strip()
                if not value:return
                if value not in ('true','false'):raise ValueError('Boolean required')
                settings['memory']['enabled' if choice=='1' else 'learning_enabled']=value=='true'
                if choice=='1' and value=='false':settings['memory']['learning_enabled']=False
                save_settings(self.path,settings,digest);self.ui.write('已保存；未启停/调用模型。')
            else:
                group=self.ui.read('授权群号：').strip()
                info=memory_action(self.path,group,'inspect',config_digest=digest)
                self.ui.write(f"记录{info['records']}条 / {info['chars']}字符 / JSON {info['bytes']}字节 / revision {info['revision']}")
                self.ui.write('1 只读导出（含事实与record ID）/ 2 新增 / 5 纠正 / 6 删除记录 / 7 删除成员 / 8 清空群 / 0 返回')
                selected=self.ui.choose({'0','1','2','5','6','7','8'})
                if selected=='0':return
                action={'1':'export','2':'add','3':'confirm','4':'pin','5':'correct','6':'delete','7':'delete-member','8':'clear'}[selected]
                fields=dict(expected=info['digest'])
                if action in ('confirm','pin','correct','delete'):fields['record_id']=self.ui.read('record ID（从本机导出查看）：').strip()
                if action in ('add','delete-member'):fields['user']=self.ui.read('成员QQ（新增群背景时留空）：').strip() or None
                if action in ('add','correct'):fields['fact']=self.ui.read('自由记忆文本（受本群总字符配额限制）：').strip()
                if self.ui.read('核对本次操作，输入“已核对”：').strip()!='已核对':return
                result=memory_action(self.path,group,action,config_digest=digest,**fields)
                self.ui.write('已完成：'+str(result))
        except (ValueError,OSError) as error:self.ui.write('未完成：'+operation_error(error))
        self.ui.pause()

    def members_group(self):
        from qqbot_gateway.members import DEFAULTS,validate_config,require_production
        settings,digest=read_settings(self.path)
        self.ui.page('小群成员与受控@')
        self.ui.write('仅已审阅的官方Snow v2.1.1可用强刷观察；NapCat/未知版本继续暂停增强，文字继续。普通received_at不能证明新鲜度。')
        from qqbot_gateway.members import snow_source
        if not snow_source(settings):self.ui.write('capability_unverified：当前来源暂停成员增强。')
        self.ui.write('仅1..49可取名单；50/未知/过期不取。人数60秒/名单300秒同时有效；最多8人/768字节候选，禁止任意QQ/@all/CQ。正常重启加载，不自动启停或查询QQ。')
        keys=list(DEFAULTS)
        for i,key in enumerate(keys,1):self.ui.write(f'{i} {key}: {settings["members"][key]}')
        choice=self.ui.choose({'0'}|{str(i) for i in range(1,len(keys)+1)})
        if choice=='0':return
        key=keys[int(choice)-1];value=self.ui.read('新值（回车保留）：').strip()
        if not value:return
        try:
            if key in ('enabled','mentions_enabled'):
                if value not in ('true','false'):raise ValueError('true/false required')
                value=value=='true'
            else:value=int(value)
            settings['members'][key]=value
            if key=='enabled' and value is False:settings['members']['mentions_enabled']=False
            settings['members']=validate_config(settings['members']);require_production(settings)
            save_settings(self.path,settings,digest)
            self.ui.write('已保存，下次正常启动加载；没有查询人数/名单或发送。')
        except (ValueError,OSError) as error:self.ui.write('未保存：'+operation_error(error))
        self.ui.pause()

    def vision_group(self):
        from qqbot_gateway.vision import validate_config,require_production
        settings,digest=read_settings(self.path)
        self.ui.page('原生识图（证据派生门槛）')
        from qqbot_gateway.vision_capabilities import load_production
        _,missing=load_production(settings,self.root)
        self.ui.write('生产缺项：'+(','.join(missing) if missing else '无；仍须操作者停机审阅后启用'))
        self.ui.write('4096仅reserve政策，样图成功不能解锁；状态由证据派生，不可手写status。')
        self.ui.write('验证入口 scripts/observe_lap28.py --help；明确授权固定六例/合计6次，每例一次，不自动启用，不改后端。只处理当前第一张图，无编辑/视频音频。')
        self.ui.write(str(settings['vision']))
        self.ui.write('1 设置reserve（1..65536） / 2 关闭desired / 3 请求启用（须通过证明门槛） / 0 返回')
        choice=self.ui.choose({'0','1','2','3'})
        if choice=='0':return
        try:
            if choice=='1':settings['vision']['input_reserve_tokens']=int(self.ui.read('reserve：').strip())
            else:settings['vision']['enabled']=choice=='3'
            settings['vision']=validate_config(settings['vision'])
            require_production(settings,root=self.root)
            save_settings(self.path,settings,digest)
            self.ui.write('已保存，重启生效；没有启停、下载或模型调用。')
        except (ValueError,OSError):self.ui.write('未保存：缺可靠上界/原生容量证明不能启用；reserve必须1..65536。')
        self.ui.pause()

    def attention_group(self):
        from qqbot_gateway.participation import ATTENTION_DEFAULTS
        keys=list(ATTENTION_DEFAULTS)
        while True:
            settings,digest=read_settings(self.path)
            self.ui.page('关注与自然续聊（默认关闭）')
            self.ui.write('仅free且enabled=true生效；mentions仍仅真实@。重启加载，不自动启停。焦点默认60秒/零插话；候选可沉默。')
            self.ui.write('enabled: true/false；aliases: 逗号分隔1..16个/每名1..16字符；focus_ttl_seconds:15..180；max_intervening_messages:固定0；direct_queue_limit及focus_candidate_evaluations_per_minute:1..8。')
            for i,key in enumerate(keys,1):self.ui.write(f'{i} {key}: {settings["participation"]["attention"][key]}')
            choice=self.ui.choose({'0'}|{str(i) for i in range(1,len(keys)+1)})
            if choice=='0':return
            key=keys[int(choice)-1];value=self.ui.read('新值（回车保留）：').strip()
            if not value:continue
            try:
                if key=='enabled':
                    if value not in ('true','false'):raise ValueError('Expected true/false')
                    value=value=='true'
                elif key=='aliases':value=[v.strip() for v in re.split('[,，]',value)]
                else:value=int(value)
                settings['participation']['attention'][key]=value
                save_settings(self.path,settings,digest)
                self.ui.write('已校验保存，下次启动生效；没有真实调用。')
            except (ValueError,OSError) as error:self.ui.write(operation_error(error))
            self.ui.pause()

    def web_group(self):
        from qqbot_gateway.web_policy import DEFAULTS
        while True:
            settings,digest=read_settings(self.path)
            self.ui.page('联网搜索')
            self.ui.write('搜索候选未通过质量门槛，目前仅明确URL可读取。公共查询会外发；不上传历史。保存须停机，重启生效；不自动重启或探测。')
            self.ui.write('enabled: true/false；trigger: auto/explicit；provider仅bing_rss；搜索固定1次；结果1..5、页1..2、总时限5..15秒、跳转0..2、响应65536..1048576字节、每页1000..8000字节、材料1000..12000字节、来源1..2。')
            keys=list(DEFAULTS)
            for index,key in enumerate(keys,1):self.ui.write(f'{index} {key}: {settings["web"][key]}')
            self.ui.write('0 返回')
            choice=self.ui.choose({'0'}|{str(i) for i in range(1,len(keys)+1)})
            if choice=='0':return
            key=keys[int(choice)-1];value=self.ui.read('新值（回车保留）：').strip()
            if not value:continue
            try:
                if key=='enabled':
                    if value not in ('true','false'):raise ValueError('Expected true/false')
                    value=value=='true'
                elif type(DEFAULTS[key]) is int:value=int(value)
                settings['web'][key]=value
                save_settings(self.path,settings,digest)
                self.ui.write('已保存，重启生效；没有执行联网或模型探测。')
            except (ValueError,OSError) as error:self.ui.write(operation_error(error)+' 请核对页面范围。')
            self.ui.pause()

    def backend_group(self):
        while True:
            settings,digest=read_settings(self.path)
            self.ui.page('后端与连接')
            self.ui.write('当前后端：'+settings['llm']['backend'])
            self.ui.write('分别保留两套参数；须先停机，保存后重新启动。切换会开启新上下文，旧历史保留。失败不自动切换。')
            self.ui.write('1 CodeBuddy CLI / 2 家庭PC本地 / 3 初始化家庭连接资料 / 4 零推理元数据检查 / 5 本地profile参数 / 6 解除远端结果未知 / 7 NapCat登录 / 0 返回')
            choice=self.ui.choose({'0','1','2','3','4','5','6','7'})
            if choice=='0':return
            try:
                if choice in ('1','2'):
                    execute(self.path,'backend','set','codebuddy_cli' if choice=='1' else 'ollama_ssh',expected_digest=digest)
                elif choice=='3':execute(self.path,'connection-init',None)
                elif choice=='4':execute(self.path,'connection-check',None)
                elif choice=='7':
                    self.ui.write('仅配置下次启动的可选单次回退；数据归属未核实不能启用。不会在此认证/登录。')
                    execute(self.path,'napcat-login','status')
                    command=self.ui.read('1 无回显保存密码（默认关闭） / 2 清除回退凭据 / 回车返回：')
                    if command in ('1','2'):execute(self.path,'napcat-login','set-password' if command=='1' else 'clear-password')
                elif choice=='6':
                    self.ui.write('仅在操作者独立确认远端请求已停止后输入 REMOTE_CHECKED_STOPPED；已加载/ps成功不能证明结束。')
                    execute(self.path,'clear-remote-unknown',None,self.ui.read('确认文字（回车取消）：').strip())
                else:
                    local=settings['llm']['profiles']['ollama_ssh']
                    keys=['expected_digest','model','num_ctx','num_predict','keep_alive_seconds','run_timeout_seconds','temperature','top_p','top_k','context_input_limit_tokens','context_overhead_reserve_tokens','output_reserve_tokens','access_file']
                    for i,key in enumerate(keys,1):self.ui.write(f"{i} {key}: {local.get(key,local['input_budget'].get(key))}")
                    self.ui.write('请求级num_ctx 4096..32768、num_predict 128..4096、保温0..1800秒、超时受provider180秒约束；think固定false。输入预算为UTF-8字节保守估算，输入+输出预留<=num_ctx且预留>=num_predict。temperature 0..2、top_p (0,1]、top_k 1..100。只选已安装tag，不下载；digest需本机核对固定。')
                    entry=self.ui.choose({'0'}|{str(i) for i in range(1,len(keys)+1)})
                    if entry=='0':continue
                    key=keys[int(entry)-1];value=self.ui.read('新值（回车保留）：').strip()
                    if not value:continue
                    if key in ('temperature','top_p'):value=float(value)
                    elif key not in ('model','expected_digest','access_file'):value=int(value)
                    if key in local['input_budget']:local['input_budget'][key]=value
                    else:local[key]=value
                    save_settings(self.path,settings,digest)
                    self.ui.write('本地profile已保存，活动后端未自动切换；重启后生效。')
            except GatewayError as error:self.ui.write(MESSAGES[error.code])
            except (ValueError,OSError) as error:self.ui.write(operation_error(error)+' 请检查digest、连接资料和参数关系。')
            self.ui.pause()

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
                llm, chat = resolve_backend(settings), budget_view(settings)
                self.ui.write('编辑当前profile：'+llm['backend'])
                self.ui.write(f"1  模型ID      {llm['model']}\n2  输入预算    {chat['context_input_limit_tokens']:,}\n3  推理强度    {llm.get('reasoning_effort','关闭思考')}\n4  记忆轮数    {chat['history_turns']} 轮")
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
            self.ui.write('当前profile：'+settings['llm']['backend'])
            if section=='effort' and settings['llm']['backend']=='ollama_ssh':
                self.ui.write('本地profile固定请求think:false（关闭思考），不映射CLI强度；真实效果尚未验证。')
                self.ui.pause();return
            if section == 'model':
                current = resolve_backend(settings)['model']
                self.ui.write('填写已安装的本地tag，例如qwen3.5:9b-q4_K_M；随后需核对digest，不自动下载。' if settings['llm']['backend']=='ollama_ssh' else '填写站点使用的字符串模型ID，不是菜单编号或展示名。示例：deepseek-v4.1-flash')
                self.ui.write('以字母或数字开头，可含 . _ : / -，最多128个字符。')
                self.ui.write('不保证账号可用或免费；若与现有强度冲突，先返回将强度设为auto。')
            elif section == 'context':
                current = budget_view(settings)['context_input_limit_tokens']
                self.ui.write('限制送入模型的固定设定、当前问题、历史与开销。范围：1024—1048576；默认16384仅作参考。')
                self.ui.write('内部按可见UTF-8字节保守计数，非精确token、模型原生窗口或计费上限。')
                self.ui.write('本地输入+输出预留不能超过请求num_ctx；原生窗口不是精确分词保证。' if settings['llm']['backend']=='ollama_ssh' else '较大预算不代表模型支持同样大的窗口；CLI内部强制压缩/恢复问题尚未解决。')
                self.ui.write('输入不带单位的十进制整数，例如32768；已知模型容量限制可能更小。')
            elif section == 'history':
                current = settings['chat']['history_turns']
                self.ui.write('范围：1—64轮；默认8轮仅作参考，包含当前这轮。1代表不携带旧轮次。')
                self.ui.write('不会删除存储历史；输入预算仍会裁剪旧轮次。请填整数，例如8。')
            else:
                current = resolve_backend(settings).get('reasoning_effort','关闭思考')
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
    commands.add_parser('memes-admin',help='图库导入、预览、标签与目录激活（不编辑参数）')
    commands.add_parser('memory-admin',help='授权群记忆查看、导出与确认CRUD（不编辑开关）')
    commands.add_parser('export-legacy-config',help='停机功能兼容审阅导出：剥除silence/attention/vision/members/memory；不同于完整布局导出')
    commands.add_parser('connection-init')
    commands.add_parser('connection-check')
    commands.add_parser('clear-remote-unknown').add_argument('identifier')
    login=commands.add_parser('napcat-login').add_subparsers(dest='action',required=True)
    for action in ('status','set-password','clear-password','set-observer-token','clear-observer-token','observer-status'):login.add_parser(action)
    for section in (*OUTPUT_FIELDS,'backend','model','context','context-window','effort','history','overhead','output-reserve'):
        actions=commands.add_parser(section).add_subparsers(dest='action',required=True)
        actions.add_parser('set').add_argument('identifier')
    for section in ('groups', 'blacklist'):
        actions = commands.add_parser(section).add_subparsers(dest='action', required=True)
        actions.add_parser('list')
        for action in ('add', 'remove'):
            actions.add_parser(action).add_argument('identifier')
    legacy=commands.add_parser('activate-legacy-config')
    legacy.add_argument('review');legacy.add_argument('source_digest');legacy.add_argument('legacy_digest');legacy.add_argument('confirmation',choices=['已核对'])
    args = parser.parse_args()
    path = ROOT / 'config/settings.local.yaml'
    try:
        if args.section=='activate-legacy-config':
            from qqbot_gateway.config import activate_legacy_config
            import json
            print(json.dumps(activate_legacy_config(path,args.review,args.source_digest,args.legacy_digest,args.confirmation)))
        elif args.section is None:
            print('日常配置：config/README.md；config/local/bot.yaml、models.yaml、chat.yaml、features.yaml、runtime.yaml。')
            print('关闭→编辑→正常启动；旧单文件未迁移时仍兼容。角色正文：config/persona.md。')
            print('管理动作：memes-admin / memory-admin / napcat-login / connection-init / connection-check / clear-remote-unknown；见--help。')
        elif args.section=='memes-admin':ConfigMenu(path).memes_group(admin_only=True)
        elif args.section=='memory-admin':ConfigMenu(path).memory_group(admin_only=True)
        else:
            execute(path, args.section, getattr(args, 'action', None), getattr(args, 'identifier', None))
    except (ValueError, OSError, GatewayError) as error:
        # Parser errors may contain secrets or user supplied YAML; never print them.
        print('配置操作失败：'+operation_error(error),file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print('\n已退出。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
