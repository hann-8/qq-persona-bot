# LAP-24自动登录续作：medium实施指引

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [HANDOFF](HANDOFF.md) / [AUTOSTART_PLAN](AUTOSTART_PLAN.md)。本指引仅约束登录/开机启动续作；旧自然分条已交付，不重做，不改用户persona。

2026-10-21：用户要求本会话完成sol/max规划。由用户后续设置gpt-6.1-sol/medium并发出实施指令；文档不会检测或切换模型，也不自动创建聊天/子agent。

## 1. 先读和登记

AGENTS→PROGRESS→工作线HANDOFF/TASKS→24 HANDOFF→AUTOSTART_PLAN→本指引。检查Git和相关diff；一个session只续领LAP-24，写明session/时间/归属并重读。保留用户persona及其他session文件，不重做旧自然分条，不重新宣称旧测试是本轮通过。

默认实施仅P1/P3代码、离线验证、必要文档及commit/push。**不启停/登录/认证真实bot，不写本机秘密或身份记录，不安装真实Startup，不重启Windows，不调用真实模型/SSH/QQ群。** 真实操作须用户日后另行指定范围、唯一负责人和最终运行状态。

## 2. 实施顺序及验收门槛

### S1 登录诊断独立交付

1. 核对安装bundle SHA及符号，不能拿main替代锁定包或自动升级。现有`-q`传递已经有主进程证据，别只新增quick.bat宣称修复。
2. 在process_host增加固定登录事件分类：由程序重建短枚举/白名单码。只处理受管napcat组件；不扩充gate/model输出，不输出原始行或任意异常文本。输入缓冲/事件频率、ANSI/超长行碎片规则按PLAN第8节。找不到日志不能判定未尝试。
3. 新观察器与密码客户端分开：只允许PLAN第5节四条固定管理/只读路由，≤120秒/16请求、≤3秒/64KiB、无代理/重定向。先验证本实例受管监听PID+创建时间/受管后代；PID复用、Worker换代、实例变化即停止。
4. 管理token独立CurrentUser DPAPI，只由未来操作者getpass录入，schema/位置/锁/取消/原子保存按PLAN。没有QQ密码需求；不从旧秘密/浏览器/聊天自动取密。observer-status零认证，真实保存/认证不是离线测试。
5. 响应只输出状态枚举、目标匹配/缓存资格布尔及白名单码；丢弃二维码URL、昵称、完整列表、loginError原文。缓存missing不是原生历史缺失证据。管理2FA直接提示人工，不调用后续挑战接口。
6. 独立采集本项目原生后代文件句柄的路径元数据；仅能证明观察的根，不能证明独立/强制绑定。外部根继续unverified，不读账号库/Registry20内容、不迁移、不重置，不能让此观察给旧密码回退解锁。

另加`start-channel --login-check-only`受控验收入口，默认false且不能用于start-text，复用既有paused=True停止转发、不启动模型。观察器在此模式仍可工作；connected/online/self_id_verified只标qq_session_ready，停止准入时不能标正常qq_ready。先用替身证明入站阻断，再由用户日后安排真实QQ诊断。

不得为了诊断打开全量原生日志或持久原始HTTP包。若stdout不经过process_host，使用受限观察器或记录telemetry_unavailable；不要临时改vendor、hook登录或增加任意HTTP/OneBot工具。

### S2 自动启动包装器独立交付

1. 新`autostart.py`/`开机启动机器人.cmd`复用现有manage入口，固定解释器/脚本/工作目录；路径和参数安全引用。默认30秒延迟/120秒网络接口等待，然后一次start-text，最多120秒QQ就绪等待，观察器共用这120秒；状态和超时按PLAN第7/8节。盘符不可用不保证可启动。
2. manage增加`--login-diagnostics`和`--wait-login-seconds`，默认false/0，保持旧无参启动行为；新等待状态与组件phase分开，gate目标在线才qq_ready。不能改变启动时模型选择、访问控制或既有锁顺序。

   等待/观察在原有配置锁释放后执行；锁内固定instance/快照，锁外按该身份观察。请求/状态原子写前后复核实例，不在网络等待中持锁，停止可立即进入。stdout只是线索，不能触发登录/密码/重启或替代gate在线证据；数字白名单仅0/140022008/140022010/140022011。
3. 已运行幂等，不重复尝试登录；partial/端口冲突/cleanup未决保持阻断，不清账本/自动kill。timeout不自动停止/重启已有bot。status不触发管理认证或模型调用。
4. 注册器install/status/remove严格当前用户单一自有`.lnk`和归属台账；参数不含秘密。重复install幂等、非本项目同名拒绝覆盖，remove不能删除无关链接。测试只用临时Startup路径/替身Windows快捷方式接口；真实注册默认不执行。
5. 包装器无pause/TTY/自动浏览器/后台循环。若需要PowerShell辅助，固定脚本参数且隐藏执行，不拼接命令、不改全局ExecutionPolicy/注册表/服务。任务计划程序是可选替代而非叠加，不默认SYSTEM/密码存储。

### S3 测试与交付

覆盖PLAN O1—O4/A1—A5，用自造秘密/账号、临时根、假WebUI和假进程。测试应验证路由没有登录副作用、秘密从未落盘、并发不会多启动、端口打开不误报QQ在线、外部链接不会被删除、login-check-only阻断free转发且观察器仍运行，不能只比对实现返回的枚举常量。

运行受影响单元/生命周期和配置回归；根据真实修改范围选择，不无理由重跑全部群聊框架。没有修改聊天/runner时不调用真实模型，也不执行会覆写旧报告的verify脚本入口。新增本任务离线报告，写清命令和数量，旧248/324仅作历史。

实际文件以PLAN第9节为限；不触及persona/群协议/模型runner/vendor。本机credentials、identity、local配置和Startup未改时明确记录。同步24交接/台账/PROGRESS/README，明确诊断及启动代码交付≠免扫码已修好；只暂存归属文件，长期授权commit/push并核对完整SHA。

## 3. 后续真实诊断与上线（本指引默认不执行）

用户日后指定范围后，只安排一个实例负责人。D/R1/R2用先经离线证明的login-check-only停止转发，只验证QQ会话。R3正常text模式须用户明确允许恢复原授权群运行；free消息可能自然触发，不能承诺全程0推理/群输出。停止/启动仅管理本项目身份及受管后代，保留日常QQ与其他启动项。

| 批次 | 内容 | 失败退出 |
| --- | --- | --- |
| D 诊断 | 本机无回显录入可选管理token；一次受控启动，取得快登结果/目标资格/根路径连续性；必要时操作者完成一次正常QQ初始化验证 | 仍无法取证则记录具体观测缺口；不在同批循环改设置/重登 |
| R1 两次重启 | 固定Windows身份/目标/bundle/原生资料；正常关闭本项目再启动两次 | 任一次要求扫码/输密/点快登即不通过，转PLAN第6节对应分支 |
| R2 系统重启 | 注册Startup前，由用户重启Windows并登录，再用同一cmd | 不能用休眠/旧进程仍活着当跨重启恢复；失败则不安装Startup |
| R3 自动触发 | 明确部署后，注册当前用户唯一链接，再一次Windows登录验收 | 自动到达目标QQ/gate才通过；失败可移除本项目链接，保留登录资料与账本 |

不在群里发“已上线”消息、不生成模型测试；模型网关元数据可单独报告，不能算真实模型验收。生产R3按用户运行范围记录正常触发；若只允许零推理则只做登录层/触发层部分验收，不标生产R3通过。

若需要修复源码，先看第6节是否属于已规划的独立项目缺陷；若必须改变原生目录/执行Windows用户/引入Docker或换QQ框架，交付独立完成部分、记录能力缺口，回到规划。旧data_scope门槛保持；未实现原生报告不能填project_only，更不能以“用户已给密码”跳过。

## 4. 给medium的可复制指令

```text
阅读 E:\CodexWS\QQbot\AGENTS.md 与 PROGRESS.md，再读活动HANDOFF/TASKS、tracks\laptop-workbuddy\tasks\LAP-24\HANDOFF.md、AUTOSTART_PLAN.md 和 AUTOSTART_IMPLEMENTATION_GUIDE.md，只续领LAP-24自动登录续作，登记session/时间/文件归属并重读。旧自然分条已交付，不重做、不改persona。
仅实施P1/P3：先做process_host固定脱敏登录事件和独立只读WebUI观察器、管理token本机DPAPI配置及本实例状态，增加复用既有paused路径的start-channel --login-check-only以阻断未来QQ验收的群转发；后做复用现有锁/生命周期的单次开机启动包装器、QQ就绪等待和当前用户自有快捷方式注册器。严格遵守路由/请求/时间/缓冲上限及状态定义，未知/缓存缺失不得误判为历史不存在或QQ已上线，qq_session_ready不能冒充正常可聊天。
不要改变账号/模型/额度/触发/群协议，不注入QQ密码环境变量，不解除data_scope，不操作外部QQ资料/设备，不修改vendor。禁止把加-q、自动填密码、WebUI记住登录或离线测试当作免扫码已修好。若stdout/原生路径能力不满足，交付独立部分并回规划，不自行切Docker、Windows用户或QQ框架。
用临时根/假WebUI/假进程/临时Startup目录完成有意义的受影响离线回归，新增报告，更新交接和README，按长期授权commit/push并核对远端完整SHA。保留用户及其他session改动。不要读取/保存真实秘密、不认证真实6099、不启停/登录bot、不安装真实Startup、不重启Windows、不调用SSH/真实模型或QQ群；真实D/R批次等用户后续指令。
```

本复制指令授权的是代码与离线交付；不会自动解决服务端反复验证，也不包含真实验收/操作系统部署。登录恢复、Startup及独立资料归属必须分别报告。
