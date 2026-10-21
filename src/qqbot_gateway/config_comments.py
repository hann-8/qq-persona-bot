"""Fixed Chinese vocabulary; defaults describe new installs, never migration values."""
DESCRIPTIONS = {
    'bot.yaml': '机器人身份、授权群、管理员与前置黑名单',
    'models.yaml': '当前后端与独立双profile；连接/队列为高级项，无失败自动切换',
    'chat.yaml': '群参与、关注续聊、回复与历史；只由授权群新消息驱动',
    'features.yaml': '联网、表情、记忆、视觉与成员；视觉生产拒启，成员生产暂停，搜索门槛关闭',
    'runtime.yaml': '高级连接、版本与秘密引用；layout_version=1独立于内部schema3',
    'qq': '机器人个人QQ，必填正整数字符串，占位不能启动',
    'allowed_groups': '授权群，必填非空正整数列表，不自动加群',
    'admin_users': '管理员，必填非空正整数列表，不豁免黑名单',
    'blocked_users': '全群前置屏蔽QQ列表，不进入框架/模型/新增记忆',
    'private_enabled': '私聊固定false，不能手工开启',
    'backend': '显式选择codebuddy_cli或ollama_ssh，不自动换模型/账号/额度',
    'model': 'CLI模型ID或已安装本地精确tag，不自动下载，不保证免费',
    'reasoning_effort': 'auto/minimal/low/medium/high/xhigh/max，受已有模型能力元数据约束',
    'context_window_tokens': 'CLI原生窗口仅null/auto口径，实际窗口未证',
    'expected_digest': '本地模型SHA256，启用ollama_ssh前须明确核对，不能填已验证标记',
    'access_file': '仅项目secrets内连接资料引用，不内联凭据',
    'num_ctx': '本地请求上下文4096..32768，不保证精确token上界',
    'think': '本地请求固定false；不映射CLI推理档位',
    'num_predict': '本地输出上限128..4096，须不大于输出预算预留',
    'keep_alive_seconds': '本地模型保温秒数0..1800',
    'temperature': '本地采样温度0..2', 'top_p': '本地采样累计概率(0,1]', 'top_k': '本地采样候选数1..100',
    'run_timeout_seconds': '单次运行期限秒；排队+所选运行期限+25秒不得超过180秒',
    'context_input_limit_tokens': '可见UTF-8字节保守输入预算，非精确token/积分',
    'context_overhead_reserve_tokens': '输入开销预留，保守计数，非精确token',
    'output_reserve_tokens': '输出预留；本地输入加输出不超过num_ctx，预留不少于num_predict',
    'host': '高级监听地址固定127.0.0.1', 'port': '高级回环端口1..65535',
    'max_concurrency': '高级模型并发固定1，单次尝试不保证CLI上游只请求一次',
    'queue_limit': '高级模型排队数0..100', 'queue_wait_seconds': '高级排队等待秒1..3600，受180秒总预算限制',
    'cleanup_seconds': '高级清理等待秒1..60，原unknown/清理门槛保持',
    'history_turns': '历史轮数1..64，保留旧历史并受预算裁剪',
    'user_cooldown_seconds': '同人冷却秒0..3600', 'session_queue_limit': '会话排队数0..100',
    'session_queue_timeout_seconds': '会话排队超时秒1..3600',
    'mode': 'participation可选mentions/free；output固定plain_chat',
    'enabled': '显式布尔开关；true不等于能力已验证，关注仅free有效',
    'learning_enabled': '记忆学习开关，必须同时开启记忆读取，不新增推理调用',
    'mentions_enabled': '受控成员@开关，仍受成员生产暂停门槛限制',
    'silence': '每群RAM临时停言；真实@恢复，gate重启复位，重连保持；默认enabled=true',
    'aliases': '关注别名1..16个，每名1..16字符，不当作真实@',
    'focus_ttl_seconds': '焦点保持秒15..180', 'max_intervening_messages': '允许插入条数固定0',
    'direct_queue_limit': '关注直接队列数1..8',
    'focus_candidate_evaluations_per_minute': '焦点候选每分钟评估次数1..8',
    'debounce_seconds': '新群消息合批等待秒', 'max_batch_wait_seconds': '合批最长等待秒',
    'min_evaluation_interval_seconds': '候选评估最小间隔秒',
    'max_evaluations_per_minute': '每分钟候选评估次数上限',
    'unsolicited_cooldown_seconds': '自发回应冷却秒，真实@绕过自发沉默/冷却',
    'max_unsolicited_per_minute': '每分钟自发回应轮数上限',
    'context_messages': 'RAM窗口消息条数上限', 'context_ttl_seconds': 'RAM窗口有效秒数',
    'context_max_bytes': 'RAM窗口UTF-8字节上限', 'message_max_chars': '单条消息字符上限',
    'mention_queue_limit': '真实@排队条数', 'max_ambient_age_seconds': '普通候选最大年龄秒',
    'allow_ambient_web': '普通候选可用联网，还必须开启web；不上传历史',
    'quote_reply': '固定false，直接群发', 'max_reply_chars': '正文字符上限200..8000',
    'delivery_mode': 'single/adaptive，adaptive自然分条，不强制凑条',
    'max_bubbles': '最多气泡1..3，认真问题仍单条', 'casual_max_chars': '闲聊总字符20..120',
    'bubble_max_chars': '单气泡字符10..60，不超过闲聊总长',
    'bubble_delay_min_ms': '分条间隔下限毫秒0..5000', 'bubble_delay_max_ms': '分条间隔上限毫秒0..5000，不小于下限',
    'trigger': '联网触发auto/explicit', 'provider': '搜索提供方固定bing_rss，当前搜索质量门槛关闭',
    'max_searches': '搜索最多1次', 'max_results': '搜索结果1..5条', 'max_pages': '正文1..2页',
    'timeout_seconds': '联网总超时秒5..15', 'max_redirects': '重定向0..2次',
    'max_response_bytes': '响应上限65536..1048576字节', 'max_page_text_bytes': '单页正文1000..8000字节',
    'max_evidence_bytes': '联网材料1000..12000字节', 'max_sources': '来源1..2项',
    'inbox_dir': '固定项目assets/memes/inbox，本机素材不提交',
    'library_dir': '固定项目assets/memes/library', 'catalog_file': '固定config/memes.local.yaml，是图库数据而非发送开关',
    'max_candidates': '表情候选数1..32', 'catalog_prompt_max_bytes': '表情提示500..4000字节',
    'max_images_per_turn': '单轮固定最多1图', 'cooldown_seconds': '表情冷却秒0..600',
    'same_meme_cooldown_seconds': '同图冷却秒0..3600', 'allow_meme_only': '允许仅发送已登记表情，不开放任意媒体',
    'max_file_bytes': '表情单文件1048576..8388608字节', 'import_count': '显式导入数量1..48',
    'max_records': '每群记忆记录数上限', 'max_fact_bytes': '每群记忆事实总字节上限',
    'max_group_file_bytes': '单群记忆文件字节上限', 'max_groups': '可持久化群数上限',
    'max_total_bytes': '记忆总字节上限', 'max_prompt_records': '单次记忆提示记录数上限',
    'max_prompt_bytes': '记忆/成员提示UTF-8字节上限', 'max_proposals_per_turn': '单轮学习提议数上限',
    'max_record_bytes': '单条记忆UTF-8字节上限',
    'input_reserve_tokens': '视觉预留4096仅假设，容量/上界未证，true仍拒启动',
    'ingress_diagnostics': '仅准入后封闭图片元数据日志；不下载、不保存原事件或身份，默认关闭',
    'roster_member_count_lt': '人数必须小于50；未知/过期暂停，不以收到时间假冒观测时间',
    'count_ttl_seconds': '人数有效秒数', 'roster_ttl_seconds': '名册有效秒数', 'max_prompt_entries': '成员提示条目上限',
    'layout_version': '磁盘布局版本固定1，组装时移除', 'schema_version': '内部配置版本固定3',
    'upstream': '固定回环WS /ws端点，不允许认证信息/查询/片段',
    'secrets_file': '项目secrets内token文件引用，check不读凭据',
    'legacy_extensions': '仅迁移保留的未知顶层字段，不保证功能，不得冲突已知字段',
}
COMMENT_KEYS = frozenset(DESCRIPTIONS) | frozenset(('bot','access','llm','profiles','codebuddy_cli','ollama_ssh','input_budget','chat','participation','attention','output','web','memes','memory','vision','members','onebot'))


def comment(key, value=None):
    return DESCRIPTIONS.get(key, '配置节，子字段见下方；保留既有校验约束')


PATH_DESCRIPTIONS = {
    ('access', 'admin_users'): 'bot管理员QQ，通常填你自己的QQ，非QQ群管理员；可真实@重置上下文，不豁免授权群/黑名单',
    ('participation', 'mode'): 'mentions只回应真实@；free可参与授权群新消息，仍受黑名单和频率约束',
    ('participation', 'attention', 'enabled'): 'free中的叫名/指代与自然续聊开关，mentions不生效',
    ('participation', 'silence', 'enabled'): '临时停言开关；明确停言后本群静默，新真实@恢复，gate重启复位',
    ('output', 'mode'): 'QQ正文固定plain_chat自然纯文本',
    ('web', 'enabled'): '共用网页读取开关；搜索质量门槛仍关闭，不代表完整搜索可用',
    ('memes', 'enabled'): '发送已登记表情图片的开关，不开放任意媒体',
    ('memory', 'enabled'): '读取本群长期记忆的开关，不等于开启学习',
    ('vision', 'enabled'): '原生识图desired开关；生产能力未验证，true仍拒绝启动',
    ('members', 'enabled'): '小群成员desired开关；人数新鲜度未证，生产仍暂停',
}


def comment_for_path(path):
    return PATH_DESCRIPTIONS.get(tuple(path), comment(path[-1]))


def annotate_yaml(text):
    """Move generated notes beside keys without reserializing any YAML value.

    Keep existing user comments, ordering, quoting, BOM and line endings. New
    annotations use only the fixed vocabulary, never configuration values.
    """
    import re
    import yaml

    def nodes(source):
        try:
            for event in yaml.parse(source, Loader=yaml.SafeLoader):
                if isinstance(event, yaml.AliasEvent) or getattr(event, 'anchor', None):
                    raise ValueError('注释更新不接受锚点或别名')
            root = yaml.compose(source, Loader=yaml.SafeLoader)
            if not isinstance(root, yaml.MappingNode):raise ValueError('注释更新要求YAML映射')
            fields = []
            def walk(node, path=()):
                if not isinstance(node, yaml.MappingNode):return
                for key, value in node.value:
                    if not isinstance(key, yaml.ScalarNode) or key.tag != 'tag:yaml.org,2002:str':
                        raise ValueError('注释更新要求字符串字段名')
                    if key.start_mark.line != key.end_mark.line:
                        raise ValueError('注释更新不支持跨行字段名')
                    field = path + (key.value,)
                    fields.append((field, key, value))
                    walk(value, field)
            walk(root)
            return fields
        except (yaml.YAMLError, RecursionError):
            raise ValueError('YAML格式无效，未更新注释') from None

    original_fields = nodes(text)
    paths = {'.'.join(path) for path, _, _ in original_fields}
    notes = {}
    retained = []
    for line in text.splitlines(keepends=True):
        match = re.fullmatch(r'# ([A-Za-z_][A-Za-z0-9_.]*)：([^\r\n]*)(?:\r?\n)?', line)
        if match and match[1] in paths and all(key in COMMENT_KEYS for key in match[1].split('.')):
            path = tuple(match[1].split('.'))
            note = match[2]
            base = comment(path[-1])
            if path in PATH_DESCRIPTIONS and note.startswith(base):
                note = comment_for_path(path) + note[len(base):]
            notes[path] = notes[path] + '；' + note if path in notes else note
        else:retained.append(line)
    source = ''.join(retained)
    fields = nodes(source)
    lines = source.splitlines(keepends=True)
    additions = {}
    for path, key, value in fields:
        line = key.start_mark.line
        if ((isinstance(value, yaml.ScalarNode) and value.style not in ('|', '>') and value.value) or
                getattr(value, 'flow_style', False)) and value.end_mark.line > line:
            line = value.end_mark.line
        line = min(line, len(lines) - 1)
        note = notes.get(path, comment_for_path(path) if path[-1] in COMMENT_KEYS else '兼容扩展字段，保留原值，不保证有运行功能')
        additions.setdefault(line, []).append((path, note))
    # Locate real comments outside scalar tokens; quoted '#' and block content
    # must remain literal values. Block header comments are outside the body.
    scalars = [token for token in yaml.scan(source, Loader=yaml.SafeLoader) if isinstance(token, yaml.ScalarToken)]
    offsets = [];offset = 0
    for line in lines:offsets.append(offset);offset += len(line)
    for index, entries in additions.items():
        original = lines[index]
        body = original.rstrip('\r\n');ending = original[len(body):]
        start_comment = None
        for column, char in enumerate(body):
            if char != '#':continue
            position = offsets[index] + column
            if not any(token.start_mark.index <= position < token.end_mark.index and not
                       (token.style in ('|', '>') and token.start_mark.line == index) for token in scalars):
                start_comment = column;break
        existing = body[start_comment + 1:] if start_comment is not None else ''
        wanted = []
        for path, note in entries:
            if note in existing:continue
            label = '.'.join(path) + '：' if len(entries) > 1 else ''
            wanted.append(label + note)
        if wanted:
            body += ('；' if start_comment is not None else '  # ') + '；'.join(wanted)
        lines[index] = body + ending
    result = ''.join(lines)
    try:
        if yaml.safe_load(text) != yaml.safe_load(result):raise ValueError('注释更新改变了YAML语义，已拒绝')
    except yaml.YAMLError:
        raise ValueError('注释更新无法安全保持YAML语义，已拒绝') from None
    return result
