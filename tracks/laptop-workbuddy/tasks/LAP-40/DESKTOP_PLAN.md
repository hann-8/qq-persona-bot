# LAP-40：补齐SnowLuma日常启动入口

返回[项目入口](../../../../PROGRESS.md) / [交接](HANDOFF.md) / [medium实施指令](DESKTOP_MEDIUM_START.md) / [原OneBot计划](PLAN.md)。2026-10-25，Asia/Shanghai。

## 需求与范围

用户指出“不知道怎么用Snow，也没有让medium落地和NapCat一样的启动脚本”。上一交付只完成协议接入和环境材料，普通用户仍需自己启动QQ/Snow、手填OneBot/token并辨认状态，未达到日常可用入口。本计划补齐这一项，随后交medium实施，不以再读TRYOUT或手工命令代替。

目标用户操作：双击本根`启动机器人.cmd`，脚本按已选provider启动必要组件、准备目标账号OneBot连接、打开官方管理页；首次只需用户在官方页面选择专用QQ进程、确认官方条款并登录/扫码。日常使用同一`查看状态.cmd`和`关闭机器人.cmd`，不要求用户输入命令、JSON或复制token。登录持久性以QQ实际行为为准，不保证以后免扫码。

这是对旧“QQ/Snow全部由操作者手动启动停止”约束的具体补充：**用户启动脚本可以创建官方QQ/Snow，并停止该脚本有创建身份依据的实例；手工已运行的外部实例不接管、不终止。** 官方包/原生接入方式保持原版，手选QQ/登录仍由用户操作。

本轮只规划，未实施或启停。非目标：修改Snow内部、私有控制/健康/资格/proof/probe、自动注入所有QQ、密码自动登录、开机自启、自动重启/回退、其他功能或长稳。旧B/C停止，A4不复核、不重跑、不修改。

## 当前代码与现场证据

工作根`E:/CodexWS/QQbot_Snowluma`，分支`codex/lap-40-snowluma`，起点本地/远端均`47342ac3691ce49c0b190949c0f7bb726d199e0f`、工作区干净。session `LAP-40-desktop-launcher-plan`于11:18登记并重读。

- 根`启动机器人.cmd`只调用`manage.py start-text`；`Start-Bot.ps1`同样调用start-text/start-channel。`manage.py:_snow_framework_specs`只包含AstrBot/gateway/gate，证实没有官方桌面端启动入口。
- `manage.py:_start_channel`在三个项目组件已运行时直接返回。新入口必须仍能补启QQ/Snow，不能重复打印“已运行”后漏掉外部端。
- `manage.py:show_status`把waiting_login统一显示为“等待NapCat登录”，Snow未就绪末尾仍提示“私有运行前置”，与官方路径和用户实际动作不符，须修正。
- 11:18只读status：provider=snowluma、text、项目running、gateway/router就绪，gate waiting_login/connected=false/channel_ready=false，cli_attempts=0，pending_restart=false。waiting_login在这里仅说明未收到OneBot连接，不能判定QQ登录实际状态。
- 专用`runtime/qq-snowluma/QQ.exe`、Snow bundled node/launcher、完整local和token均存在；`config_files.py check`在上轮只读接续已通过。旧MATERIALS的“QQ/local缺失”是10:49历史，不再要求重复安装或覆盖。未读取token正文、QQ登录资料或私密群内容。
- 本机原版`runtime/snowluma/v2.1.1/launcher.bat`依次调用`node check-node-version.cjs`、`node index.mjs`，最后pause；完整包自带node.exe。包装器可用**包内node绝对路径、包根cwd、原版入口**运行，避免PATH选错或隐藏批处理pause。
- 官方包`index.mjs`的`loadOneBotConfig/saveOneBotConfig`（5035/5086行）、snapshot标记（4981行）与[官方配置说明](https://snowluma.github.io/zh/docs/guide/configuration)支持目标账号`config/onebot_<uin>.json`及`networks.wsClients`。不需要新增转换器。正常运行入口含官方父/子Node进程，登记时须覆盖自己创建的进程及其可识别子进程。

## 用户行为合同

| 入口/场景 | 预期行为 |
| --- | --- |
| 双击启动，provider=napcat | 沿用原start-text/NapCat行为，不启动Snow/专用QQ，不改变默认provider |
| 双击启动，provider=snowluma | 复用或启动项目组件；准备本项目目标账号连接；启动缺少的专用QQ和官方Snow；打开本机管理页，显示简短首次步骤和本机日志入口 |
| 项目已运行但Snow未启动 | 保留现有项目实例、快照和队列；只补缺少的官方端，不能先stop重建 |
| 再次双击 | 不重复起QQ/Snow/三个项目组件。对有创建身份记录的实例复用；无法确认归属的现存实例只报告/打开管理页，不强行接管或结束 |
| 首次登录/协议页面 | 用户亲自在官方页面阅读并确认条款、登录管理页、选择专用QQ、完成扫码；脚本不设置自动接受协议的环境变量，不读取/填写QQ密码 |
| 查看状态 | 分开显示项目组件、官方管理页/进程、OneBot连接和模型空闲/活动；等待时说明“打开Snow管理页，选择专用QQ并登录”，不显示NapCat或私有前置要求 |
| 关闭机器人 | 先撤销群入口并停止本根模型/框架，再停止本脚本有创建身份依据的Snow/专用QQ及其已识别子进程；外部手动实例保留并提示用户正常关闭 |

接通后按原业务合同处理新消息。保留free时其他新消息也可能触发模型；启动脚本不发送测试消息、不调用生成接口、不自动改mentions/free。部署/真实启动不是本轮或medium离线实施的自动步骤。

## 最小实现接口

1. 在`manage.py`增加`start-desktop`动作作为日常统一入口：读取现有provider，NapCat委托原start-text；Snow完成上表外部启动编排。原start-text/start-channel保留为高级项目组件入口，不悄悄扩大它们的既有语义。`Start-Bot.ps1 -ChannelOnly`继续无模型，可经start-desktop的`--channel-only`显式支持相同外部便利入口；该选项只适用于新动作。
2. 根`启动机器人.cmd`和普通Start-Bot.ps1调用新动作；`查看状态.cmd/关闭机器人.cmd`继续使用统一status/stop并扩充官方端结果。保留引号、任意cwd、退出码和`--no-pause`，中文cmd使用UTF-8和CRLF。所有路径从脚本根/既有配置推导，不硬编码旧工作根。
3. 新增小型`src/qqbot_gateway/official_snowluma.py`处理包路径、目标OneBot文件和官方进程创建；通过manage已有配置锁、PID/创建时间登记与停止机制衔接。可以为普通官方组件使用`official_snow`、`official_qq`名称，避免误入旧私有snowluma/qq_client控制分支。不新增另一套supervisor、私有owner/proof或健康服务。
4. Node以包内`node.exe`运行官方`check-node-version.cjs`（短进程）及`index.mjs`（后台进程），cwd为包根。后台隐藏窗口；专用QQ是用户需要看到和扫码的交互窗口。官方输出只保留忽略的`logs/snowluma-startup.local.log`或等价本根日志，不通过process_host的过滤丢掉初始管理密码；统一终端/status/agent报告不回显密码或token。
5. 根增加`打开SnowLuma管理页.cmd`和`查看Snow本机日志.cmd`，分别打开固定本机官方管理页和本机日志文件；不登录、不生成、不另启模型或QQ。主启动成功后自动打开管理页一次；首次说明明确账号/初始管理密码在本机官方日志中查看。不自动把token拼进URL或命令行。
6. 新增根`SnowLuma使用说明.md`，面向用户只写“双击哪个文件→首次网页如何选择专用QQ/登录→怎么看连上→怎么关闭”，提供管理页/本机日志按钮的名称。明确“组件运行”与“QQ通道已连接”的区别；用户无需理解gate、Universal、JSON或token。不要把实现字段写进普通操作步骤。

进程归属仅用于安全启停：创建后立即记PID/创建时间和组件，沿用本根忽略状态；只有可识别为本次创建子进程的成员才登记。QQ启动器若交给现存实例，不把现存实例当新建；身份不清时保留并给人工退出提示，不按进程名扫描终止。5099等端口被不明进程占用时定位冲突并保留现场，不强占端口或杀其他根。部分失败只回收本次新建且有身份的组件，保留原本已运行组件；不为普通失败新建恢复系统。

## 配置、默认值及生效

不新增用户业务YAML字段；`qq_transport.provider`默认napcat和现有`runtime_root/qq_executable`路径不变。CLI的`start-desktop`是操作者显式动作，新开机任务保持关闭。脚本不得修改local/persona、模型/额度来源或版本锁。

Snow端连接配置可由新启动入口正常准备，目标仅实际bot账号文件`runtime_root/config/onebot_<bot>.json`：

- 本项目条目名`qqbot-gate`，enabled=true，url取当前gate回环地址并加`/ws`（现值6200），role=Universal，messageFormat=array，reportSelfMessage=false，reconnectIntervalMs=5000，accessToken在进程内读取现有onebot_inbound。
- 缺文件时按官方snapshot结构创建，其他三类networks置空，只加这一条反向WS；不暴露默认HTTP/正向WS作额外接入。已有文件保留无关字段、其他条目和mode；同名本项目条目已一致则零写入，需要同步时先原字节备份再仅更新该条并原子发布。重复点击不累加条目，不删其他账号或全局设置，不重生成token。
- 初始化/同步发生在本次新建Snow之前。Snow已外部运行时不通过猜测接口提交认证修改；只给本项目目标连接的正常配置说明/可明确执行的同步动作，保留外部实例。不得因为这种兼容分支回退为所有用户都手抄JSON的交付。
- WebUI默认5099，启动子环境可用官方已支持的SNOWLUMA_WEBUI_HOST=127.0.0.1、SNOWLUMA_WEBUI_PORT=5099约束本机入口；不修改全局环境或其他实例。不启hookAutoLoad，不设置SNOWLUMA_HOOK_AUTOLOAD_ALL，不让官方自动加载所有日常QQ；首次手选专用进程。
- 不预设扫码后一定免扫码，不复制登录数据；已有账号连接正常配置保持可用。官方首次条款/管理密码由用户在本机处理，包装器不自动接受、不捕获日常密码或管理cookie。

## 文件与任务顺序

medium归属候选：`scripts/manage.py`、`src/qqbot_gateway/official_snowluma.py`、根三个既有cmd、两个新增Snow辅助cmd、`scripts/Start-Bot.ps1`（必要时Stop/Status PS入口）、根使用说明、必要专项测试及LAP-40交接/TRYOUT/PROGRESS/工作线台账。登记后再改，未涉及的文件不为凑列表修改。不改gate/router业务、A4、官方包源码、local/persona或原E根/旧C根。

顺序：登记与新现场只读核对 → 实现统一入口/目标连接的幂等准备 → 官方进程创建/复用/安全停止 → 中文状态与两辅助入口/简短说明 → 必要离线检查 → 同步交接并commit/push。不得只写新的操作文档而不落实脚本。

必要验证使用临时根、伪造账号/token、模拟Popen/浏览器/文件打开，不运行真实QQ/Snow/模型：

1. 从任意cwd/带空格项目路径进入，绑定正确包内node/官方入口与cwd；NapCat仍委托旧入口。
2. 已运行项目但未启动桌面端时只补缺项；两次点击无重复组件或重复WS条目。
3. 新建/一致/需更新的目标连接，仅改本项目条目；无关字段/账号、旧字节备份和token不回显。
4. 只停止有PID/创建时间依据的本次实例；外部同路径实例、PID复用和其他QQ均保留；部分启动失败只回收本次新增。
5. 缺包、端口冲突、配置错误给具体中文动作，退出码有效，不自动安装/回退；状态不再错误提示NapCat/私有资格，模型0生成。
6. 管理页/本机日志入口与首次说明准确可用；浏览器/文件打开失败给路径，不重复创建服务。cmd编码/换行及既有生命周期必要相关用例检查。

不跑A4、全量回归或长稳。只有上述离线检查通过，才记“启动入口已实现/离线通过”；真实双击、QQ选择/登录、目标群一次真实@及可见回复必须用户后续授权/亲自操作后另记。medium本次实施不启停当前running实例、不写实际Snow账号配置、不打开真实登录页，实际配置准备由未来用户点击新入口触发。

## 兼容、回滚与缺口出口

当前正在运行的三个组件保持原状；改脚本不会热替换实例。回滚可在本分支撤销本项启动入口提交，原start-text/start-channel仍可用；仅恢复本项曾修改的目标Snow配置备份，先确认该实例已停止，保留其他runtime和用户数据。不能自动启动原根NapCat或删除QQ登录材料。

未验证：官方桌面端实际拉起/进程交接、网页首次引导、QQ扫码与会话保留、真实OneBot/模型/群ACK；没有把这些写成已通过。一般Windows启动细节和已列失败分支由medium处理。若官方QQ启动器交接不明，先完成脚本和可识别部分、保留外部QQ让用户退出，不以“必须证明所有原生数据”冻结交付。只有实际基本接入被Snow内部阻断，携具体外部尝试结果交用户决定；不得重启私有路线。
