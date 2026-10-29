# SnowLuma 日常使用

当前QQ以本工作根为主线；进度见[PROGRESS](PROGRESS.md)，从旧bot迁来的使用差异见[实际对照](docs/BOT_USAGE_COMPARISON.md)。

1. 双击本文件旁的 **启动机器人.cmd**。脚本自动准备连接并启动缺少的组件、专用QQ和官方Snow，打开本机管理页。再次双击会复用已有实例。
2. 首次在官方页面阅读并确认条款，登录管理页。管理账号/初始密码请双击 **查看Snow本机日志.cmd** 在本机查看，不要把日志或密码发给别人。
3. 在页面选择本根 `runtime/qq-snowluma/QQ.exe` 对应的专用QQ进程，按官方页面操作加载，然后亲自扫码登录。不要选择日常QQ。无需填写JSON或复制连接token；以后是否需要扫码以QQ实际提示为准。
4. 双击 **查看状态.cmd**。“组件在运行”和“管理页端口可达”只说明程序在运行；OneBot就绪、QQ通道连接且群消息可接收，才表示通道已接通。连接后，新群消息可能按原有设置触发模型回复，脚本不改触发模式。
5. 需要回到页面时双击 **打开SnowLuma管理页.cmd**。页面未打开时可访问 [本机Snow管理页](http://127.0.0.1:5099)。启动失败时双击日志按钮查看本机信息。
6. 结束使用请双击 **关闭机器人.cmd**。先停止本根入口、模型和框架，再停止脚本创建且身份仍匹配的Snow、专用QQ及其已识别子进程。关闭启动窗口不会停止后台机器人。手工启动或身份未确认的实例会保留，请在对应窗口正常退出。

如果提示“Snow已运行，目标OneBot连接需同步”，请先在Snow窗口/管理页正常退出Snow，QQ可保留，再双击启动；脚本会备份旧配置并自动同步。不要为此关闭仍在运行的项目组件。5099端口冲突时按提示正常退出冲突程序，不要批量结束QQ/Node进程。

用户已确认SnowLuma能运行、bot可在QQ群回复，最小文字首试按用户现场确认成功。日常继续使用现有环境；具体停止、登录持久性及其他功能不因该反馈自动记为完整验收，不需要重新跑首试或重装。local/persona和登录资料保持原样。

## LAP-43日常用法（2026-10-28）

四项已实现并加载，识图/记忆/关注/成员及原有free配置保留；搜索和当前版本识图质量待你群内实测。

- 空@会本地短应声“我在～”，不调用模型。直接叫名如“鱼鱼查查Python最新消息”“鱼鱼这个怎么看？”进入必答；同人已收到回复后可说“那怎么办”“再详细点”“继续”。有人插话或焦点超时后不强行续聊。
- 唯一操作者可发真实@加“暂停发言”或“恢复发言”。暂停时不发确认，普通@和空@不能解除；恢复只处理后续新消息。真实@加“重置本群上下文”（兼容“重置会话”“/重置”）仅操作者可执行，不清长期记忆。
- 7张原有表情已激活。可正常闲聊，或说“鱼鱼发个开心的表情”；模型只从登记候选选图，每轮最多1张，认真回答/搜索来源答复不附图。尚未代你群发测试。
- 原生联网已部署：可问“鱼鱼，明天杭州下雨吗”“鱼鱼，查查今天的航天新闻”，或直接贴公共网页链接。由CLI自行选择WebSearch/WebFetch，不再受旧关键词、近7天或Python正文提取前置限制。说“不要联网”会关闭本轮工具。来源至多2条，只取本次实际工具材料；失败会说明未核实。联网答复单条文字、不附表情、不写长期网页记忆。实际服务效果待你群测。
- 群长期记忆与学习已开启；普通群内事实仍按原学习和管理规则处理，重置本群上下文不清长期记忆。CodeBuddy CLI思考关闭；聊天、识图、受控表情与唯一操作者控制保留。

本轮组件、配置及图库已加载，最新检查OneBot已连接、群消息可接收，可以直接群测。Snow管理页已打开；以后如需登录/扫码由你亲自操作。可双击“查看状态.cmd”检查通道。外部QQ未接管或结束。

项目当前使用`runtime/codebuddy-2.168.0/package`内的缓存旧版CLI，避开全局CLI升级对已审阅识图接线的影响。无需修改全局CLI；模型仍为deepseek-v4.1-flash/low及原账号额度。若以后升级项目专用CLI，需同步接线/预算与识图记录，不能只改hash。


## LAP-44 群长期记忆

当前群每次模型调用都会收到本群现有记忆全文；模型自行新增、概括、更新、合并和遗忘。不会跨群，网页不是群友自述，也不应把群记忆上传联网查询。空库存可首次学习。明确要求记住/更新/忘记时，宿主保存后给实际回执；如果模型未提出动作，会显示“本轮长期记忆未变更”，不能把口头答应当作保存证明。普通聊天可静默学习；保存失败保留原文件。重置上下文不删除长期记忆。

用户可在授权群依次测试：“以后叫我小青，请记住”→看到“已保存到本群长期记忆”→由唯一操作者发送“重置本群上下文”→再问“你记得该怎么称呼我吗”。这是用户真实效果测试，离线/加载检查不保证模型每次都合理学习。

初始配置为 `config/local/features.yaml` 的 `memory.max_chars_per_group: 50000`、`max_group_file_bytes: 1048576`、`max_total_bytes: 8388608`；字符按Unicode code point计数，不是字节。所选 `config/local/models.yaml` 的 `llm.profiles.codebuddy_cli.input_budget.context_input_limit_tokens: 524288` 在此CLI路径实际是可见UTF-8字节政策，不代表实际token消耗。默认值均可扩大；例如100000字符、2097152文件字节、33554432总字节和786432输入政策已作合成验证。超模型真实容量或最终输入仍会明确拒绝，不裁半本记忆、不自动压缩调用或切模型。旧max_records/max_fact_bytes/max_prompt_records/max_prompt_bytes/max_proposals_per_turn/max_record_bytes仅兼容，不再生效。

扩大时先用项目 `.venv/Scripts/python.exe scripts/manage.py stop` 正常停机，备份上述两个local及 `state/group-memory`、当前active/技术记录，再只改所需字段。沿当前完整配对流程执行：

```powershell
.venv/Scripts/python.exe -B scripts/revalidate_lap43_native_web.py check
# 下两项的实际摘要由scripts/activate_lap42_vision.current和当前active文件SHA取得，不手填旧值
.venv/Scripts/python.exe -B scripts/revalidate_lap43_native_web.py probe --expected-binding <当前binding>
.venv/Scripts/python.exe -B scripts/revalidate_lap43_native_web.py activate --authorize-operator-trial --expected-binding <当前binding> --expected-active <当前active文件SHA256>
.venv/Scripts/python.exe -B scripts/manage.py start-desktop
.venv/Scripts/python.exe -B scripts/manage.py status --json
```

取得当前摘要的只读命令（项目根运行）：

```powershell
.venv/Scripts/python.exe -B -c "import sys;from pathlib import Path;sys.path[:0]=['src','.'];from scripts.activate_lap42_vision import current;from qqbot_gateway.vision_trial import sha;r=Path.cwd();print('binding='+current(r)[2]);print('active='+sha(r/'state/vision-evidence/active.json'))"
```

health的memory显示实际加载配额，status的memory显示条数/字符/文件字节及最近保存状态，configuration.pending_restart须false。配置保存不等于已加载。当前固定模型容量不足时先降低额度，不改代码或能力登记伪造容量。该配对probe是CLI零生成技术检查，不调用真实模型生成或联网服务。

本机停机管理用 `scripts/configure_bot.py memory-admin`，支持查看计数、只读导出、自由文本新增/纠正/删除、按稳定成员标记删除或清空群；schema2无确认/固定/到期机制。自由文本若未包含某成员稳定标记，不能保证按成员删除能找全所有间接关系；需要明确条目删除。群聊模型没有清namespace/key或改配置的权限。
