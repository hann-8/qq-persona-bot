# QQ 人设文字 Bot（笔记本测试版）

LAP-28 已交付原生图片适配与离线验证，**生产仍不可启用**；见[交接](tracks/laptop-workbuddy/tasks/LAP-28/HANDOFF.md)和[报告](reports/lap-28-2026-10-18.md)。没有执行真实识图、群图下载、QQ/模型调用或bot启停。

`vision.enabled=false`为默认值；`vision.input_reserve_tokens=4096`仅为待验证假设。菜单7→20查看/关闭desired及设置1..65536的reserve；没有可编辑status，申请启用会被拒绝。手改true同样在gate/router/gateway启动前拒绝。保存不启停，正常重启加载；本次未改本机配置。

图片入口仅在准入/黑名单后给当前新消息第一张图签发cap，原URL/路径/附件从送往框架的事件剥离，框架不自动下载。gate在现有loopback端口提供固定`/context/vision/bind`、`/context/vision/resolve`，独立`context_service_token`只从项目忽略的`secrets/context-service.local.json`读取（随机至少32字节的64位hex；不复用其他token），当前不创建凭据。provider只转sideband，gateway绑定request/target/source/epoch后一次兑换；失败/并发/重放/过期均不能再下载。重连、失联清理cap；运行配置变更须停机重启。ambient合并会同时替换目标与其cap，不读取承载event的旧图。

只接受当前事件已有的HTTPS `gchat.qpic.cn` / `multimedia.nt.qq.com.cn`来源，逐跳检查DNS/实际连接地址、拒绝私网/代理/cookie/auth。JPEG/PNG/WebP及GIF首帧，原图≤8MiB/16M像素；去元数据、保留全图等比缩至≤1024边长/1M像素，规范化PNG≤512KiB。全RAM材料≤8MiB/TTL60秒，单任务解码、完成释放；图片不写请求文件/历史/普通日志，也不发回处理图。CLI走同一次stream-json image content，SSH Ollama走同一次原生images；均保留工具隔离、现有模型/参数和单次尝试，不做caption、不换后端，不接视频音频。图中文字仍是不可信材料。

最终按原profile扣除视觉reserve检查完整文字/政策/目标/窗口/网页及表情候选，base64另算完整wire≤2MiB；local额外满足文字+视觉+输出≤num_ctx。图片与网页共用原15秒准备预算。看不到图时direct只给一次准确本地说明，ambient静默，失败不换图/重试。

证明分为`unverified / offline_passed / native_observed / production_eligible`，绑定代码/库版本、后端、CLI bundle/Node或Ollama运行版本/model digest、normalizer和上下文/推理/输出/reserve。适配器离线通过不代表本机组合真实通过。当前两路线均无可靠模板/视觉token或patch上界及原生容量证明；production_eligible没有放行来源，不能用一次样图或调低reserve解锁，补证需回规划。31B及既有真实验收差额保留。

独立离线入口：`.venv/Scripts/python.exe -X utf8 scripts/verify_lap28.py`，仅写`reports/lap-28-*`。真实观察命令为`scripts/observe_lap28.py`，本次只检查`--help`。后续必须由用户明确现有选定后端、样图、用例和整轮调用总上限，再在停机状态先运行`--backend <已选后端> --inspect`取得本机binding（纯本机、零网络/推理）；单用例须同时提供`--sample <文件> --case known_content|screenshot|max_normalized --expected-visible-text <已知可见内容> --expected-binding <摘要> --max-calls 1 --authorize-native ONE_NATIVE_IMAGE_CALL`。命令不切后端，每次最多一个原生生成且无重试，另保持用户整轮预算；先写一次尝试账本，失败/未知也保留。仅记录脱敏版本/尺寸/hash/观察结果到忽略的`state/vision-evidence/`，不记录样图/回答/路径，不自动启用。最大尺寸用例需规范化≥990000像素；预期内容匹配只形成观察值，不能证明4096上界。

LAP-27新增free关注/指代与自然续聊，默认关闭，尚未真实验收或自动加载。配置机器人.cmd → 7 群聊参与与活跃度 → 18 关注与续聊：仅`participation.mode=free`且`attention.enabled=true`生效，停机保存、正常重启加载；mentions仍仅真实@并沿用原群+用户历史。所有新能力关闭时保留原v1协议、工具隔离及single/adaptive、web/memes行为。

启用关注后：真实@ > 可靠叫名/引用已ACK的bot文字 > 同人60秒且无插话的第二人称续聊 > 无主语续聊候选 > ambient。同级FIFO，不打断活动生成；不同direct消息各自排队，目标与必要引用冻结到投递/ACK结束。候选每群滚动60秒默认最多4次，同次模型可判断结束确认应沉默。只有已确认的正常模型文字ACK建立焦点，按真实回应对象归因，unknown/图片/本地错误不建焦点。队列/生成/ACK均可能增加等待，不承诺固定时延；新增随机trace关联固定类别日志，不含正文或QQ/群号。

旧代码回滚前，先停止受管实例并保留所有pending/unknown/清理台账。菜单7→19或`.venv/Scripts/python.exe scripts/configure_bot.py export-legacy-config`生成`state/config-exports/`忽略目录内的原配置备份、移除attention与vision section的旧schema3审阅副本及两个摘要；保留其他扩展字段。**只导出不激活**。本机审阅后可显式运行`activate-legacy-config <review路径> <source_digest> <legacy_digest> 已核对`，同配置锁下复核停机与双摘要后原子激活，不重启；任一副本有变化须重新导出。旧版本不认识未决清理台账时保持停机，不能靠回旧代码抹掉unknown。

独立离线验证：`.venv/Scripts/python.exe -X utf8 scripts/verify_lap27.py`，只写`reports/lap-27-*`；实际run_agent/provider/原event ACK与两runner底层替身、自造群/图片夹具，不调用真实模型/QQ。上述27交付时图片/名册/记忆字段仅预留；28图片进展见本文顶部，29/30未实施，31B完整覆盖/恢复仍未交付。见[LAP-27交接](tracks/laptop-workbuddy/tasks/LAP-27/HANDOFF.md)。

LAP-24已实现/离线通过，尚未重启加载或真实验收：闲聊“最多三条”仅为上限，能一句接住就一句，有必要补充才两三条；认真回答完整单条，表情可不发、不占位凑数。single仍保留单条文字规则，不改操作者已有条数/间隔设置。真实模型的表达与QQ效果仍待另行验证。

新增“配置机器人.cmd → 5 后端与连接 → 7 NapCat登录”，原1—6编号保留。也可用项目Python运行`scripts/configure_bot.py napcat-login status / set-password / clear-password`（三选一动作）。status只读本机状态，不解密或认证；set-password须停机并在本机TTY通过两次无回显输入分别录入QQ密码和项目WebUI token，回车/取消保留原凭据；不支持命令行密码或重定向输入。密文仅存忽略的`secrets/napcat-login.local.json`，CurrentUser DPAPI绑定当前Windows身份，清除只移除本项目回退凭据，不登出或删除设备/尝试账本。

**登录目录能力仍未证实，当前保存入口只能保存为关闭，不能据此保证免扫码。** 固定安装目录不等于QQ数据隔离；缺少原生数据根目录证据时保留快登/人工扫码，不迁移日常QQ、不重置GUID。单次回退客户端与实例账本已离线实现，但生产入口保持unverified，手写project_only记录也不会启用。未来补齐可信原生路径读取后，才可按明确授权接入并验证：新实例、目标匹配、受管6099监听、连续两次稳定未登录、先记账再密码POST；同实例最多一次，超时/中断unknown不重放，Worker重启不带密码环境。状态/健康/幂等启动不会认证。详见[LAP-24报告](reports/lap-24-2026-10-18.md)及[剩余差额](tracks/laptop-workbuddy/tasks/LAP-24/HANDOFF.md)。

项目进度从 [PROGRESS.md](PROGRESS.md) 开始。当前支持指定群的真实 @ 文字聊天，默认使用已登录、同账号同站点的 CodeBuddy CLI 和指定模型；家庭SSH原生Ollama后端已实现/离线通过，尚未真实生成或启用；群单条和多轮记忆有旧真实证据，隔离通过离线集成检查；真实多人和长期运行仍在验收。LAP-18公共网页读取已实现/离线通过，默认关闭；搜索质量门槛未通过，搜索未完成。视频、音频未接入。

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

缺省mentions仅处理授权群的QQ真实@；普通文字、仅@全体、引用或手打“@昵称”不强制触发。mentions保留每用户5秒冷却、群+用户隔离的最多8轮本人历史与管理员真实@“重置会话”。LAP-20新增显式free，见下文；私聊、未授权群和黑名单仍不处理。

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

已实现、离线及实际框架合成回归通过；真实本地生成、think:false效果、实际窗口/显存/速度、adaptive遵循和远端取消后停止均未验证。黑名单前置、私聊关闭和LAP-16发送账本继续保留。联网独立进展见下节；free已由LAP-20实现但未启用，LAP-21受控表情已实现/离线通过，默认关闭，真实收藏/发图未验。

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

## LAP-20：显式自由群聊（已离线验证，尚未启用）

停机后在“配置机器人.cmd → 7 群聊参与与活跃度”选择participation.mode=free，保存后重启生效；缺省仍mentions。本轮没有改本机配置、启停或真实试用。free只观察授权群启动后的新消息，先过滤黑名单/自身/私聊；不会导入旧个人历史、回拉QQ历史或理解收到的图片/视频。机器人输出在所有模式均为直接群发，single/adaptive都没有引用和自动@，output.quote_reply仅允许false。

free使用每群独立RAM窗口，缺省60条/15分钟/32768 UTF-8字节；重启/断连/模式切换清空，管理员真实@“重置本群上下文”仅重置当前群。普通文字2秒合批，持续发言首条最多等5秒，每群每5秒至多评估一次、每分钟最多12次；一次生成决定说/不说，沉默也可能消耗模型额度。默认自发发言至少间隔15秒、每分钟最多4轮；无新消息不生成，不设定时冷场发言。高级参数的单位/范围显示在菜单，完整合同见[配置表](tracks/laptop-workbuddy/tasks/LAP-19/GROUP_CHAT_PLAN.md#5-lap-20配置默认值与生效)。

真实@独立优先排队，绕过自发沉默/冷却/频率限制。队列满、超时、无文字/能力不支持或后端异常给一次简短状态；不保证故障时模型完整回答或QQ必达，不自动重试/切模型。纯媒体非@只记占位。收到新@时取消未开始的自发任务，已开始生成只完成一次，若有@等待则丢弃自发输出；过期/断连/停止结果不发送。

free的所有模型输出经统一逐条ACK投递，只把确认的bot输出加回RAM，原群快照不入个人conversation或持久发送账本。任一未知ACK会暂停本群继续接龙，真实@只给本机核对提示；操作者在QQ核对后，停机进入菜单7→17解除隔离，未知证据保留，旧内容不会重发。连接元数据监视仅清理失效RAM，不调用模型/搜索或主动发言。

联网复用LAP-18，最多从本批新消息选择一个查找问题/公共URL，其他群聊与旧问题不外发搜索；allow_ambient_web仅与web.enabled同时开启时生效。搜索质量门槛仍未通过，不能称联网已可用。health的group_usage分mention/ambient、speak/silent/error与generations记录数值，credits仍unknown。两后端自然参与、真实QQ/ACK/多人/恢复/关闭中行为与旧真人缺项均未验；[离线报告](reports/lap-20-2026-10-17.md)与[交接](tracks/laptop-workbuddy/tasks/LAP-20/HANDOFF.md)列明证据。回滚先停机设mentions再重启，旧个人历史保留；回退旧代码前核对/隔离pending和unknown账本并保留配对备份。LAP-21后续独立交付见下节，仍不自动启用。

## LAP-18：共用公共网页读取，搜索未完成

两后端共用受控读取、确定性按需规则、预算/来源和原发送路径，已实现并通过离线/实际框架合成回归。本轮未启用或部署，没有真实联网生成或群验收。Bing RSS候选的三类最终公共查询均被非全局DNS地址检查拦截，未满足至少2/3相关且可读、含时效日期核对的门槛；不能判断候选质量合格。搜索有代码内关闭门槛，配置不能绕过；明确搜索/时效问题会给一次本地缺口提示，0次搜索HTTP、0次模型生成。需先回规划处理网络条件/搜索提供方，不能自行改账号、部署服务或开CLI WebSearch/MCP。

后续由操作者停机，在“配置机器人.cmd → 6 联网搜索”显式设置web.enabled=true，保存后重启生效；本轮没有操作这些步骤。默认false，旧配置只在内存补齐，保存沿用锁/hash/备份/原子替换。trigger=auto采用明确查找/时效事实/公共URL规则；explicit仅明确查找或URL。当前可用独立分支为用户直接提供的公共HTTP(S)静态HTML/text，最多2页。当前问题明确“不要联网/只根据这段文字/只凭记忆”优先；闲聊不联网，不外发人设或历史。视频/评论、PDF/文件、登录/付费/验证码/JS空壳不支持。

web预算缺省：max_searches=1（固定，当前搜索关闭）、max_results=5（1..5）、max_pages=2（1..2）、timeout_seconds=15（5..15）、max_redirects=2（0..2）、max_response_bytes=1048576（65536..1048576，压缩前后各限）、max_page_text_bytes=4000（1000..8000）、max_evidence_bytes=6000（1000..12000）、max_sources=2（1..2）。单次连接最多3秒，读取空闲最多6秒，全部读取共用硬期限；只允许80/443，每跳解析/绑定已检查全局IP并核对peer、TLS校验开启，无环境代理/Cookie/登录态。当前系统DNS对测试公共域名给出非全局地址，现实现会拒绝，不能保证当前网络下可实际读取；不调整系统网络或绕过安全门槛。

取得材料后仅调用当前后端一次。输入计入完整可见字节预算，先裁旧完整轮次，再裁材料；保留当前原问题，证据不足则本地说明/0生成。来源由代码从实际投喂材料追加，最多2个完整URL，计入原字符限额；联网答复固定answer单条，adaptive也不拆来源。全部读取失败0生成并本地说明；部分成功只用成功页并标范围。总期限到达不开始模型、不发送或保存内部标记；取消/停止关闭当前HTTP，不继续生成。发送/历史只含原问题与实际确认答复，网页原文不入AstrBot历史；adaptive沿用逐条ACK/未知不重发/启动恢复。单条模式原有ACK验收差额保留。

web设置进入会话版本，重启加载后新建当前上下文，旧历史保留；单次查询/时间/网页内容不参与版本。健康页web_audit和日志仅记录次数、字节和时延，http_calls包含被DNS拦截的连接尝试，不能当作已建立连接次数；本地缺口提示不标真实生成成功。关闭web并停机保存/重启即可回滚，回退旧代码前仍须处理pending账本并保留配置/历史。详情见[报告](reports/lap-18-2026-10-17.md) / [交接](tracks/laptop-workbuddy/tasks/LAP-18/HANDOFF.md)。


## LAP-21：受控表情（已实现/离线通过，默认关闭）

认图与标签：重新打开“配置机器人.cmd → 8 表情包 → 7 看图填写标签”。按 `P` 在默认浏览器打开带编号的本机缩略图总览，回配置窗口选相同编号；输入编号也会用系统图片查看器打开该张原图，确认后输入 `E` 再填写名称/语境/标签，不是目标图片就回车重选。列表显示名称或“未命名”、格式及启用状态，不要求靠哈希认图。空回车保留已有字段；首次启用必须有名称和至少一个标签，使用语境不能代替标签。若标签留空后输入YES，会保留名称/语境并提示补填（0取消编辑），支持中英文逗号分隔；输入YES才确认启用该图。保存失败会单独说明校验/停机等原因，可按R保留当前输入重试，不再统称预览失败。预览不修改目录或启用发送，未启用图片也可预览；保存标签仍须停机、重启后生效。总览仅引用通过路径/格式/hash校验的本机文件，无脚本或外部资源，生成页在忽略的state/meme-preview内；打开失败可检查系统默认图片/HTML关联。

本地入口为`assets/memes/inbox`，支持PNG/JPEG/WEBP/GIF。在“配置机器人.cmd → 8 表情包”打开目录、扫描本地文件，再填写简短名称、使用语境、逗号分隔标签并输入YES确认登记。扫描/标签/目录激活须停止项目，保存后重启生效；菜单不会启停或登录。图片按SHA256去重存入`assets/memes/library`，目录表为`config/memes.local.yaml`；未命名/未确认图片不进入候选。用户图片、标签、QQ来源与临时工件全部忽略；Git仅保留模板和自造测试。目录位置固定为项目预留的忽略路径。

从机器人QQ收藏导入是显式管理操作：先在表情页初始化独立管理token（仅存项目secrets，不显示）；下次正常启动gate时加载。机器人现有连接可用时选择“收藏详情导入”；基础接口仅由操作者显式另选，无自动回退。导入只读取当前机器人账号收藏，不修改QQ收藏、不查询其他账号/凭据或群历史。没有连接就报不可用，不代为登录/启动。运行中下载只准备`state/memes-pending.local.yaml`及受控库，之后由操作者停机激活目录、填写标签并重启；活动目录不会热替换。激活使用配置锁与目录hash复核，竞争时拒绝覆盖。

固定回环`POST /admin/memes/favorites`仅接受count=1..48和detail/basic模式，管理token与模型/OneBot token分离，独立echo关联回执；框架/模型仍不能调用收藏和账号API。下载仅接受该RPC返回的HTTPS媒体地址，精确白名单为本机NapCat源码出现的`gchat.qpic.cn`、`multimedia.nt.qq.com.cn`，逐跳TLS/全局IP/实际连接地址校验，不使用Cookie/代理、任意URL或通配域。真实收藏若返回其他域名会拒绝，须补证据；不自动扩域。单项至多8MiB、总量128MiB、总期限60秒，失败不重试，取消不激活。完整签名URL只在进程内，不入目录表/日志。

`memes.enabled`默认false；升级旧配置只补缺省，不自动启用。表情页参数包括候选16项/2000 UTF-8字节（可调1..32/500..4000）、每轮图片固定1张、普通图片冷却60秒、同图300秒、允许闲聊仅图true、单文件8388608字节与导入48项。图片限制为4096×4096且不超过16M像素、最多120帧/累计128M解码像素，拒绝伪装类型/SVG/HTML/越界/符号链接/junction。验证依赖Pillow12.3.0已锁定。候选只有ID/名称/语境/标签，计入当前后端输入预算；标签仅作材料，不向模型提供图片字节、文件路径或收藏URL，不接入看图模型。

启用后mentions使用认证`media_turn`和严格`qqbot_media_reply`封套，free扩展既有群封套；模型一次生成，只能选本次候选meme_id或null。文字仍经一次纯文本整理，内部封套不发群。single至多一段文字加一图，总部件不超过max_bubbles（为1时文字优先）；认真answer/代码/联网来源不附图。普通@至少有文字；明确索要表情或ambient闲聊可仅图。冷却只抑制图片，不再调用模型换图；明确要图可绕过普通图片冷却一次。

文字和图片都经原event、同群队列及逐条ACK账本直接群发，无引用/自动@。图片在投递前复核hash并冻结在忽略的`state/meme-delivery`，AstrBot转换为base64后，由事件私有回执代理核验字节再映射为冻结file URI，gate再次校验；没有裸API旁路。账本记录类型/hash/受控引用/语义标签与逐条状态。文字确认而图片发送前失效为partial；未知/重复ACK保持unknown且不重发，停止/断连停止余下部件。只有ACK确认图片才记“bot发了表情：名称”到本人历史或当前群RAM；图片only不会额外发送假图片描述。仅图发送前不可用时@给一次本地状态、ambient静默。重启不补发或重新生成，群RAM丢弃；LAP-25起未知群投递保留账本，不再要求核对后才能继续新消息。

[离线报告](reports/lap-21-2026-10-17.md)与[任务交接](tracks/laptop-workbuddy/tasks/LAP-21/HANDOFF.md)记录验证。真实QQ收藏读取、下载域名/图片和GIF客户端显示、真实模型ID遵循/ACK/额度/长稳均未验；用户说明“已有2个收藏”不是已导入或真实可发证据。此次未读真实收藏/下载用户图，未启停/登录/探活bot、真实生成/群发或修改本机settings启用memes。

回滚可停机保存`memes.enabled=false`后重启，图库/旧历史保留。回退typed账本之前的代码，须先停机隔离pending/unknown，备份并恢复同检查点数据库和配置；不可让旧文本修复器处理未知image。LAP-18搜索缺口及旧真人验收差额继续保留。

## LAP-25：群发送容错与“没接住”修复

娱乐群发送中断或ACK未知只结束当轮，不再持续锁住该群；既有unknown也无需删库或人工解除即可处理新的群消息。确认已发部分可进RAM，未确认部分不进上下文，不重发、不补调模型。仅group RAM采用这项宽松策略，个人历史冲突及远端生成是否结束未知的保护仍保留；原“核对后解除”菜单作为旧证据标记入口兼容保留。

群上下文按最终完整system和固定表情候选说明重新核算预算，必要时删除最旧群行，保留当前@目标；候选列表再在剩余预算内裁剪。预算计数仍是UTF-8字节及信封的保守估算，不代表原生token窗口。目标与固定设定本身仍过长时明确显示输入预算原因，限流等业务错误也保留具体固定提示；ambient错误保持沉默，无额外模型调用。

模型输出允许完整JSON围栏、缺省可选字段、单字符串bubbles等偏差；真实@的安全普通文字可降级为单条，坏表情选择不丢弃可用文字。工具标记、重复键、损坏内部JSON、请求/响应身份不匹配仍拒绝。ambient不会因普通文字降级扩大自动发言；只发送登记表情，不开放模型任意图片路径。

本轮未改本机配置或接管运行实例，需正常关闭/启动加载代码。离线验证与已知限制见[修复报告](reports/lap-25-2026-10-18.md)和[任务交接](tracks/laptop-workbuddy/tasks/LAP-25/HANDOFF.md)，真实QQ与模型效果待试用确认。


## LAP-31：CLI 清理诊断与未决保护

31A已实现：原生成结果与清理结果分开记录；每次请求只有一个受持有的cleanup task，取消和关闭接管同一任务。`llm.cleanup_seconds`仍默认5秒、范围1..60，现在表示整次kill、等待及落盘的总deadline。个别身份无权访问不会跳过其他已知身份；PID复用的新进程不操作。超时线程仍在运行时保持阻断，旧答案不迟发、不重试。

零推理本机诊断：在项目目录运行 `.venv/Scripts/python.exe scripts/manage.py cleanup status` 或 `cleanup check`。check只核对已登记的PID+创建身份，不kill、不调用模型、不补发；每5秒最多一次检查、最多等待2秒。`/health`的`cli_cleanup`仅含固定分类、数量、耗时和随机trace。正常legacy成功仍允许下一请求；`observed_empty/observed_only`只证明已知观察集合退出，不能解除已经发生的清理故障阻断。

忽略的`state/cli-cleanup/`保留最多1个未决请求、128个创建身份及32份已解决摘要；单文件不超过32KiB，模块不超过2MiB。坏账本、超限、磁盘失败或覆盖不明均拒绝新CLI；不删除unknown腾位置，不保存argv/env/提示词/群消息。重启重读未决状态，历史`job_complete`标签不能直接解锁。不要通过删台账、切后端或回旧代码绕过阻断。回滚前确认cleanup task结束并保留未决身份；旧版不认识此保护时须保持停机，直到独立确认完整退出。

31B仍有实现/验收差额：Windows自造进程的执行前Job归属、归零、失败回收与句柄关闭有离线证据，但强化试验发现breakaway创建请求仍被接受，尚未证明该子进程是否仍属目标Job；禁止breakaway/完整覆盖门槛未通过。生产CLI仍走原asyncio启动路径，未接入执行前Job容器，也未授权真实CLI组合验证；因此没有完整自动恢复能力，不能称清理问题完整解决。后续需按[LAP-31交接](tracks/laptop-workbuddy/tasks/LAP-31/HANDOFF.md)补生产创建/管道适配和验证；本轮不自动启用。Ollama远端未知解除合同不变。

独立验证入口 `.venv/Scripts/python.exe -X utf8 scripts/verify_lap31.py` 只用替身/自造受管进程，自动使用既有框架Python执行实际run_agent/两runner底层替身回归，只写`reports/lap-31-*`，不运行旧verify主程序。[报告](reports/lap-31-2026-10-18.md)区分31A与31B。本轮没有改本机配置、启停或登录真实bot，也没有真实模型/QQ调用。
