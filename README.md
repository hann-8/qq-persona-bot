# QQ 人设文字 Bot（笔记本测试版）

项目进度从 [PROGRESS.md](PROGRESS.md) 开始。当前支持指定群的真实 @ 文字聊天，使用已登录、同账号同站点的 CodeBuddy CLI 和指定模型；群单条和多轮记忆已验证，隔离已通过离线集成检查；真实多人和长期运行仍在验收。视频、音频和网页正文尚未接入。

在 `E:\CodexWS\QQbot` 的 PowerShell 中使用：

```powershell
.\scripts\Start-Bot.ps1
.\scripts\Show-BotStatus.ps1
.\scripts\Stop-Bot.ps1
.\scripts\Test-Bot.ps1
```

启动脚本仅管理项目独立实例；已运行时会拒绝重复启动。停止依据项目记录的PID及创建时间，不按QQ进程名停止其他程序。`-ChannelOnly`启动选项仅用于关闭模型的通道诊断。不要同时启动两个实例。

QQ登录正常时可自动恢复；需要扫码时使用本项目NapCat本机界面。AstrBot管理页为 `http://127.0.0.1:6185`，NapCat为 `http://127.0.0.1:6099`；密码/令牌在被忽略的 `secrets` 目录，勿外传。日常QQ安装不属于该实例。

仅指定群且消息含QQ真实 @bot 时处理；普通文字、私聊、仅@全体、仅引用旧消息和手打“@昵称”不会触发。每个用户至少间隔5秒；收到回复后再问下一句。历史按群和用户隔离，最多保留8轮短文字上下文。管理员在真实@后发送“重置会话”，只重置其本人在当前群的会话。

人设在 `config/persona.md`，已采用“大肥鱼/鱼鱼”鲸鱼娘v2；固定访问/能力政策由代码优先组合，角色正文不能扩大触发权限。修改后停止并重新启动，新的设定版本会在下次请求建立新会话。本机账号、群、模型及队列参数在被忽略的 `config/settings.local.yaml`，格式参考 `config/settings.example.yaml`。已确定的账号、模型、额度来源及触发规则应保持原决定，禁止自动切换模型或另接收费API。

授权群和全局用户黑名单可双击根目录 `配置机器人.cmd` 维护，也可执行：

```powershell
.\.venv\Scripts\python.exe scripts/configure_bot.py show
.\.venv\Scripts\python.exe scripts/configure_bot.py groups list
.\.venv\Scripts\python.exe scripts/configure_bot.py groups add <群号>
.\.venv\Scripts\python.exe scripts/configure_bot.py groups remove <群号>
.\.venv\Scripts\python.exe scripts/configure_bot.py blacklist list
.\.venv\Scripts\python.exe scripts/configure_bot.py blacklist add <QQ号>
.\.venv\Scripts\python.exe scripts/configure_bot.py blacklist remove <QQ号>
```

`show`仅显示数量和边界；`list`会在本机显示完整列表，勿将其作为公开诊断分享。读取可在运行中进行；添加/移除前先关闭机器人，保存后重启生效。工具保留未知配置字段，拒绝空授权群和非法ID，写前自动备份到被忽略的 `state/config-backups/`，并以独占锁、摘要校验和原子替换防止冲突或失败损坏旧文件。手工编辑运行中的YAML也只在下次启动生效。旧配置缺少版本/黑名单时仍可读，启动只在内存补默认值；首次工具保存才迁移为v2，不重生成令牌、不清空历史。

管理员同样受授权群和黑名单约束。被屏蔽发送者的新消息在转发给AstrBot前静默拒绝；直接到达插件也不进入任务、冷却、模型或新会话。拉黑不删除旧历史，解除后可继续原会话；仍需真实@才触发。配置授权群后，账号是否入群需由你手工确认，工具不会自动加群。LAP-11纯文本/人设v2已实现并通过离线验证，运行实例未加载。

LAP-10已增加参数菜单及下列命令，但当前bot未重启加载；原生窗口和CLI强制恢复能力缺口尚未解决，整体未完成验收，暂未部署：

```powershell
.\.venv\Scripts\python.exe scripts/configure_bot.py model set <模型ID>
.\.venv\Scripts\python.exe scripts/configure_bot.py context set <输入预算>
.\.venv\Scripts\python.exe scripts/configure_bot.py effort set auto
.\.venv\Scripts\python.exe scripts/configure_bot.py history set <记忆轮数>
.\.venv\Scripts\python.exe scripts/configure_bot.py context-window set auto
```

输入预算范围1024—1048576，默认16384；计数为可见system、序列化对话与已知信封的UTF-8字节保守估算，加内部开销预留2048，**不是精确token或计费上限**。保留system和当前问题，历史从最旧完整轮次移除；只有system和当前问题仍超预算时拒绝，不截断问题、不调用摘要模型。`history`为包含当前轮的总轮数（1—64，默认8）。`overhead set`、`output-reserve set`可设置0—65536的开销和输出/推理预留；原生总窗口未知时，输出预留不能作为已验证的模型容量约束，也不是模型输出token参数。

当前默认模型仍deepseek-v4.1-flash；同站点零推理能力元数据确认它支持low/high/max。`effort set high`等显式设置会在每次唯一user消息之前核对当前模型支持列表，再以CLI参数传递；不支持时拒绝，未知模型仅允许auto。auto不覆盖强度。换模型如与旧强度冲突，请先设auto；不改账号/站点，不自动fallback。模型可用性依当前账号/站点，不承诺免费。能力快照绑定当前锁定CLI，不等于永久服务承诺。

`context-window`当前仅接受auto（YAML为null）。设置收到ACK不代表有效原生预算；本版本没有证实原生窗口，不能冒充提高容量。常规自动压缩由进程内settings关闭，但已发现CLI的强制压缩/内部恢复可绕过，尚未证明严格无额外推理；1次CLI、1条user消息不等于上游模型API严格1次。该缺口需按AGENTS回到规划，详见[LAP-10报告](reports/lap-10-2026-10-16.md)。不建议据本次实现直接放大实际运行预算。

状态页查看队列、累计CLI尝试、最近错误和router_ready，不会调用模型。`backend_state=not_probed`表示本次启动尚未真实推理，不能据此判定登录失败。认证/配额故障后暂停请求；在官方界面处理后再重启，不反复尝试登录。进程运行不等于文本链路通过，验收证据见 `reports`。

`runtime`、`state`、`cache`、`logs`及`secrets`为本机数据；会话数据库可能含聊天内容，分享项目时不要附带这些目录。暂未配置开机自启；电脑睡眠时不承诺在线。

LAP-11由网关一次将模型最终Markdown转为聊天纯文本：保留正文、可见链接、代码字面量和缩进，表格改成字段/值。输出仍为单条消息，超长明确提示未展示完；格式转换后为空则本次失败，不自动重试。`output.mode`仅支持`plain_chat`，`output.max_reply_chars`可在停止后手工编辑本机YAML为200—8000，默认1200，下次完整启动生效；配置菜单没有新增输出项。新部署会因组合政策/人设版本变化使下一次请求开启新上下文，旧历史保留。本轮未部署或要求登录，真实QQ ACK和P01人设接受仍待用户参与，见[LAP-11报告](reports/lap-11-2026-10-16.md)。
