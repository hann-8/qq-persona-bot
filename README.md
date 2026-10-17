# QQ 人设文字 Bot（笔记本测试版）

项目进度从 [PROGRESS.md](PROGRESS.md) 开始。当前支持指定群的真实 @ 文字聊天，默认使用已登录、同账号同站点的 CodeBuddy CLI 和指定模型；新增家庭SSH原生Ollama后端已实现/离线通过，尚未真实生成或启用；群单条和多轮记忆已验证，隔离已通过离线集成检查；真实多人和长期运行仍在验收。视频、音频和网页正文尚未接入。

日常操作：

1. 双击根目录“启动机器人.cmd”。提示等待登录时，在本机 `http://127.0.0.1:6099` 完成NapCat登录，再双击“查看状态.cmd”；只有显示QQ已连接、可接收群消息后才在授权群真实@试用。
2. 用完双击“关闭机器人.cmd”。关闭启动窗口不会关闭后台bot；操作结束按键关闭结果窗口。

重复启动不会另开实例，重复关闭也可直接使用；部分组件存活时先关闭再启动。只管理项目记录的PID+创建身份及当前子进程，不按QQ进程名关闭日常软件。LAP-12交付时曾关闭后台；后续由你自行启动/关闭。LAP-13仅更新菜单和提示，没有探测或改变你试用后的运行状态，登录恢复/群聊完整验收仍待补。

“查看状态.cmd”分别报告项目组件、QQ通道、模型及任务状态。模型not_probed表示本次未推理；健康检查不调用模型。QQ online缺失/过期显示未知；未登录时保持服务并提示本机登录地址，不反复重启。模型当前错误与后来已恢复的历史错误分别显示，send_unknown等任务状态单列。

高级/脚本用法（原PowerShell入口保留）：

```powershell
.\scripts\Start-Bot.ps1
.\scripts\Show-BotStatus.ps1
.\scripts\Stop-Bot.ps1
.\scripts\Test-Bot.ps1
.\.venv\Scripts\python.exe scripts/manage.py status --json
.\启动机器人.cmd --no-pause
.\关闭机器人.cmd --no-pause
```

cmd入口定位自身目录，支持外部工作目录及中文/空格路径，不依赖Codex注入PATH，不修改执行策略；不带`--no-pause`时保留按键阅读窗口。`Start-Bot.ps1 -ChannelOnly`仅用于无模型通道诊断。启动/停止/配置写操作共用OS锁，同时操作会提示已有操作进行中。停止先暂停新任务并短暂等待，再清理受管树；未完成任务记unknown，不自动重放/重发。清理失败保留身份，不能据state文件存在/空就猜运行状态。

需要扫码时使用本项目NapCat本机界面。AstrBot管理页为 `http://127.0.0.1:6185`，NapCat为 `http://127.0.0.1:6099`；密码/令牌在被忽略的 `secrets` 目录，勿外传。人工操作同一个bot账号时建议先关闭bot，完成后重新启动并确认NapCat登录；平台同号顶号/风控不能由脚本保证避免。本次启停前后15个外部QQ/WorkBuddy进程身份仍存活，未代替你验收QQ界面基本操作，详见[LAP-12报告](reports/lap-12-2026-10-16.md)。

仅指定群且消息含QQ真实 @bot 时处理；普通文字、私聊、仅@全体、仅引用旧消息和手打“@昵称”不会触发。每个用户至少间隔5秒；收到回复后再问下一句。历史按群和用户隔离，最多保留8轮短文字上下文。管理员在真实@后发送“重置会话”，只重置其本人在当前群的会话。

人设在 `config/persona.md`，已按LAP-15整理为“大肥鱼/鱼鱼”鲸鱼娘唯一精简正文，日常通常1—3短句、总体15—60字为表达目标，认真问题按需要答清楚；single发一条QQ纯文本，可显式启用下文LAP-16有限分条。原文完整备份仅在本机忽略的state/persona-backups，新版本组合3618 UTF-8字节，见[LAP-15报告](reports/lap-15-2026-10-17.md)。本轮仅离线验证，未加载真实实例，风格/P01待接受；固定访问/能力政策由代码优先组合，角色正文不能扩大触发权限。修改后停止并重新启动，新的设定版本会在下次请求建立新会话。本机账号、群、模型及队列参数在被忽略的 `config/settings.local.yaml`，格式参考 `config/settings.example.yaml`。已确定的账号、模型、额度来源及触发规则应保持原决定，禁止自动切换模型或另接收费API。

授权群和全局用户黑名单可双击根目录 `配置机器人.cmd` 维护。首页按“群与黑名单”“模型与对话”“详细设置与能力说明”分组，切页清屏；列表/保存结果按回车后返回。每项编辑页会说明格式、范围和用途，空回车取消；首页0退出、子菜单0返回。推理强度可输入页面编号或英文值，编号只用于选择，保存的仍是auto/low/high/max等支持值；未知模型能力只允许auto。菜单读取当前值，不把你已保存的预算或轮数重置为默认。

启动/重复启动始终显示 `NapCat 登录/管理：http://127.0.0.1:6099`；启动失败时也给地址并提示可能暂不可访问，不自动打开浏览器。直接脚本命令和重定向输出不清屏、不额外暂停，原命令仍可使用：

```powershell
.\.venv\Scripts\python.exe scripts/configure_bot.py show
.\.venv\Scripts\python.exe scripts/configure_bot.py groups list
.\.venv\Scripts\python.exe scripts/configure_bot.py groups add <群号>
.\.venv\Scripts\python.exe scripts/configure_bot.py groups remove <群号>
.\.venv\Scripts\python.exe scripts/configure_bot.py blacklist list
.\.venv\Scripts\python.exe scripts/configure_bot.py blacklist add <QQ号>
.\.venv\Scripts\python.exe scripts/configure_bot.py blacklist remove <QQ号>
```

`show`仅显示数量和边界；`list`会在本机显示完整列表，勿将其作为公开诊断分享。读取可在运行中进行；添加/移除前先关闭机器人，保存后重启生效。工具保留未知配置字段，拒绝空授权群和非法ID，写前自动备份到被忽略的 `state/config-backups/`，并以独占锁、摘要校验和原子替换防止冲突或失败损坏旧文件。手工编辑运行中的YAML也只在下次启动生效。旧配置缺少版本/黑名单时仍可读，启动只在内存补默认值；首次工具保存才迁移为schema3（两套独立profile），不重生成令牌、不清空历史。

管理员同样受授权群和黑名单约束。被屏蔽发送者的新消息在转发给AstrBot前静默拒绝；直接到达插件也不进入任务、冷却、模型或新会话。拉黑不删除旧历史，解除后可继续原会话；仍需真实@才触发。配置授权群后，账号是否入群需由你手工确认，工具不会自动加群。LAP-11纯文本/人设v2已实现并通过离线验证，已在本次暂停准入启动中加载验证，最终已关闭。

LAP-10已增加参数菜单及下列命令。LAP-12曾暂停准入加载验证并关闭，这是历史检查点，当前运行状态未探测；原生窗口和CLI强制恢复能力缺口尚未解决，整体未完成验收，不据本机启动结果宣称能力缺口已解决：

```powershell
.\.venv\Scripts\python.exe scripts/configure_bot.py model set <模型ID>
.\.venv\Scripts\python.exe scripts/configure_bot.py context set <输入预算>
.\.venv\Scripts\python.exe scripts/configure_bot.py effort set auto
.\.venv\Scripts\python.exe scripts/configure_bot.py history set <记忆轮数>
.\.venv\Scripts\python.exe scripts/configure_bot.py context-window set auto
```

输入预算范围1024—1048576，默认16384；计数为可见system、序列化对话与已知信封的UTF-8字节保守估算，加内部开销预留2048，**不是精确token或计费上限**。保留system和当前问题，历史从最旧完整轮次移除；只有system和当前问题仍超预算时拒绝，不截断问题、不调用摘要模型。`history`为包含当前轮的总轮数（1—64，默认8）。`overhead set`、`output-reserve set`可设置0—65536的开销和输出/推理预留；原生总窗口未知时，输出预留不能作为已验证的模型容量约束，也不是模型输出token参数。

当前默认模型仍deepseek-v4.1-flash；同站点零推理能力元数据确认它支持low/high/max。`effort set high`等显式设置会在每次唯一user消息之前核对当前模型支持列表，再以CLI参数传递；不支持时拒绝，未知模型仅允许auto。auto不覆盖强度。换模型如与旧强度冲突，请先设auto；不改账号/站点，不自动fallback。模型可用性依当前账号/站点，不承诺免费。能力快照绑定当前锁定CLI，不等于永久服务承诺。

CLI的`context-window`当前仅接受auto（YAML为null）。设置收到ACK不代表有效原生预算；本版本没有证实原生窗口，不能冒充提高容量。常规自动压缩由进程内settings关闭，但已发现CLI的强制压缩/内部恢复可绕过，尚未证明严格无额外推理；1次CLI、1条user消息不等于上游模型API严格1次。该缺口需按AGENTS回到规划，详见[LAP-10报告](reports/lap-10-2026-10-16.md)。不建议据本次实现直接放大实际运行预算。

状态页查看队列、累计CLI尝试、最近错误和router_ready，不会调用模型。`backend_state=not_probed`表示本次启动尚未真实推理，不能据此判定登录失败。认证/配额故障后暂停请求；在官方界面处理后再重启，不反复尝试登录。进程运行不等于文本链路通过，验收证据见 `reports`。

`runtime`、`state`、`cache`、`logs`及`secrets`为本机数据；会话数据库可能含聊天内容，分享项目时不要附带这些目录。暂未配置开机自启；电脑睡眠时不承诺在线。

LAP-11由网关一次将模型最终Markdown转为聊天纯文本：保留正文、可见链接、代码字面量和缩进，表格改成字段/值。single缺省仍为单条消息；可显式选adaptive，具体行为见下段，超长明确提示未展示完；格式转换后为空则本次失败，不自动重试。`output.mode`仅支持`plain_chat`，`output.max_reply_chars`可在停止后手工编辑本机YAML为200—8000，默认1200，下次完整启动生效；原max_reply_chars仍可手工设置；配置菜单已新增回复方式分组。新部署会因组合政策/人设版本变化使下一次请求开启新上下文，旧历史保留。LAP-12已暂停准入启动验证后关闭；真实QQ ACK和P01人设接受仍待用户参与，见[LAP-11报告](reports/lap-11-2026-10-16.md)。

## 有限分条（LAP-16，需显式启用）

缺项仍是single；本轮只实现/离线验证，没有改本机配置或加载真实bot。协调关闭当前实例后，双击“配置机器人.cmd”，进入“4 回复方式”，将delivery-mode设为adaptive，再按既有入口启动；具体实例启用与真实试用须由当前负责人协调。也可运行`.venv/Scripts/python.exe scripts/configure_bot.py delivery-mode set adaptive`，仍受停止身份守卫限制。切回single使用同一菜单或命令。

adaptive在一次生成内决定日常chat和认真answer。闲聊最多3条、合计80字符、每条40字符，首条后间隔800—1600毫秒；不凑条数，不按标点硬拆。认真问题、代码/字面量保守合成一条；超闲聊限额合成一条且保留尾段，原max_reply_chars总上限和未展示完提示仍有效。进阶项可调整条数/字符/间隔，页面标明范围与单位；保存后下次启动生效。模式/生成限额改变会建立新当前上下文，间隔调整不改人设版本，旧会话保留。

只有确认ACK的内容会进入下一次可用历史；任一条回执不明就终止后续，不自动重发/补调模型。部分发送显示send_unknown，不能当成全部送达。启动仅恢复本地确认历史，不补发。若某会话提示发送历史需要本机核对，先保留账本并核对；管理员重置只建立新的本人当前会话，不删除原异常历史。回切旧代码前先处理pending历史，保留state/tasks.sqlite。

工具隔离、授权群真实@、黑名单/私聊和当前CLI/账号/预算保持。真实QQ ACK、多人/关闭中发送及用户风格接受仍待验，见[LAP-16报告](reports/lap-16-2026-10-17.md)。


## LAP-17：手动选择后端与家庭连接

已实现、离线及实际框架合成回归通过；真实本地生成、think:false效果、实际窗口/显存/速度、adaptive遵循和远端取消后停止均未验证。既有仅真实@、黑名单前置、私聊关闭和LAP-16发送账本继续保留。联网/free/表情包仍须后续任务，本次不启用。

配置机器人.cmd → 5 后端与连接，手动选择CodeBuddy或家庭PC；模型与对话页编辑当前profile，本地参数页可在CLI仍活动时预先编辑本地profile。两套模型、强度/原生选项、超时和输入预算各自保留，历史轮数共用。所有保存须先关闭机器人，下次启动生效；保存不生成、不重启、不自动fallback。本轮没有修改本机settings或初始化长期运行连接文件。

后续由操作者显式初始化：在后端与连接页选3，只从项目secrets内既有家庭资料复制DPAPI密文及旧盘点固定指纹到`secrets/home-5070-runtime.local.json`，保留原文件，不打印密码，不认证探测密码。运行时只读JSON，不解析旧Markdown，不读全局SSH/QQ/WorkBuddy资料。也支持在该JSON显式设置项目secrets内专用`key_file`替代`password_dpapi`；二者只能选一个，字段为host（既有家庭IPv4/IPv6字面地址，避免DNS超时不受控）/port/user/fingerprint和凭据引用，禁止明文password。既有资料不全时停止，不自动接受网络上新指纹。

然后选4进行零推理检查：每次最多一次SSH认证，只访问固定PC回环11434的version/tags/show/ps，无chat/generate/pull/预加载。检查可在CLI活动时由操作者显式执行，常规CLI启动/健康状态不读取家庭凭据。首次检查允许expected_digest未配置，显示已安装tag的digest与digest_confirmed=false；核对后在5本地profile参数填入expected_digest，才可选择本地后端。指定digest不符即拒绝，不自动换tag/下载。PC须开机不睡眠、已有Ollama后台和SSH可达，不需常开ollama run聊天窗口。

本地请求级初值：num_ctx=16384、think=false、num_predict=1024、keep_alive=300秒、temperature=0.7/top_p=0.8/top_k=20；不改PC全局参数。输入预算12288、开销2048、输出预留2048，完整原生JSON请求纳入UTF-8字节计数；输入预算+输出预留<=num_ctx且输出预留>=num_predict。这是保守预算，不能代替精确分词或有效原生窗口实测。CLI默认仍deepseek-v4.1-flash/auto及原预算；旧schema1/2逐值迁移到CLI profile，未知扩展保留，有冲突拒绝。schema3不再有可写的顶层llm.model或chat预算影子。

网关启动本地后端时先完成<=25秒元数据预检再监听，model等待30秒；失败由既有创建身份回收本次启动组件。每条请求先复核tag/digest，再只POST一次原生chat，复用system、本人裁剪历史和同一输出/ACK路径，不提供tools/MCP/图片。超时、取消、半响应或断线未确认完成时，持久记`state/ollama-remote-result-unknown.json`并返回REMOTE_RESULT_UNKNOWN，已排队和重启后生成都阻断；不远程杀进程、不据ps已加载认定请求已结束。操作者独立确认远端请求结束、停机后，可在菜单6输入REMOTE_CHECKED_STOPPED显式解除；禁止为了重试直接删标记。

可用命令（均不自动启停）：

```powershell
.\.venv\Scripts\python.exe scripts/configure_bot.py connection-init
.\.venv\Scripts\python.exe scripts/configure_bot.py connection-check
.\.venv\Scripts\python.exe scripts/configure_bot.py backend set ollama_ssh
.\.venv\Scripts\python.exe scripts/configure_bot.py backend set codebuddy_cli
.\.venv\Scripts\python.exe scripts/configure_bot.py clear-remote-unknown REMOTE_CHECKED_STOPPED
```

状态区分保存的下次启动profile、当前运行backend/model、元数据检查、最近真实生成、CLI尝试/本地POST/总backend尝试及数值usage；计数为当前网关进程内，credits仍null/unknown，不把token或占位0当积分。连接检查成功不能标真实推理通过。选定后端/模型/digest/原生生成参数/预算进入共用会话版本；非活动profile修改不影响当前版本。首次加载新版本合同或切换会建立新当前上下文，旧会话原样保留，不自动恢复为旧current。

回滚到保留的CLI：停机→后端菜单选CLI→重新启动，不删模型、凭据或历史；远端未知状态仍需独立确认，不因切CLI而宣称远端已停。回退schema2代码前，先停机处理/隔离pending发送账本和远端未知请求，恢复同一检查点的配置备份并保留schema3/新历史备份；旧代码不能直接读schema3。部署依赖由pyproject.toml及uv.lock锁定（Paramiko5.0.0）；仅在项目虚拟环境安装，不修改系统Python。

本轮验证与限制见[LAP-17报告](reports/lap-17-2026-10-17.md) / [任务交接](tracks/laptop-workbuddy/tasks/LAP-17/HANDOFF.md)。
