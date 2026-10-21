# LAP-24续作：保存QQ登录状态与开机自动启动

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [本任务交接](HANDOFF.md) / [实施指引](AUTOSTART_IMPLEMENTATION_GUIDE.md)。继承[AGENTS](../../../../AGENTS.md)。旧[PLAN](PLAN.md)的自然分条和既有单次密码回退合同保留；本文件补齐自动登录研究、诊断和部署顺序，冲突处以本续作的登录合同为准，不重做自然分条。

日期：2026-10-21（Asia/Shanghai）。用户指定sol/max承担详细规划，后续由用户设置gpt-6.1-sol/medium并另行下达实施指令；没有自动检测/切换会话设置。本轮仅只读核对和文档，未实施、部署或登录。

## 1. 结论、需求与完成口径

推荐顺序是：**查明快登失败分支 → 让QQ保留且复用自己的原生登录状态 → 验证多次免人工重启 → 最后安装当前Windows用户的Startup快捷方式。** 保存密码不是前置条件。已有快登入口不能算问题已解决，也不能把“脚本运行了/端口开了”算成QQ上线。

目标是在操作者已登录Windows、原网络/所选模型路线可用的正常条件下，双击项目cmd或由`shell:startup`触发后，无需输入QQ账号密码、点击快登或扫码，自动到达目标QQ在线和项目通道就绪。先完成一次由操作者参与的初始化验证可以接受；不能接受每次正常重启都要求“新设备”扫码。

| 状态 | 判据 |
| --- | --- |
| 已规划 | 本文件及实施指引、证据与失败出口明确；本轮仅到此 |
| 已实现/离线通过 | 诊断、状态判定、启动包装器通过替身验证；尚不能声称免扫码 |
| 登录恢复真实通过 | 同一环境两次正常关闭/启动及一次Windows重启后登录，均无需人工且账号/通道匹配 |
| Startup真实通过 | 上项先通过，再真实Windows登录时由唯一入口自动恢复；没有人工补点 |
| 观察通过 | 后续3个实际使用日正常恢复均无重复验证，记录次数和失败；不承诺永久有效 |
| 独立数据归属通过 | 另有原生路径和可强制绑定的专属目录证据；与上两项分别记录 |

非目标：绕过QQ服务端验证、自动代扫手机、伪造/重置设备、抓取网页Cookie冒充QQ会话、读取/复制日常QQ票据、改变QQ账号/模型/订阅额度、安装新的推理后端、无新消息主动群发、系统账户服务、未登录Windows就开机运行、自动启用Windows免密码登录。LAP-10/18/31B及旧真人差额不以本任务补齐。

## 2. 当前证据与限制

### 2.1 本会话前段的运行只读观察

以下是本会话前段已经完成的检查，规划阶段不重启/重新登录以复现；它们不保证未来时刻状态。真实账号、进程完整参数、路径中的个人部分、GUID、票据和群正文均不写本文。

| 观察 | 结论与不能推出的结论 |
| --- | --- |
| 项目进程账本PID+创建时间匹配；原生QQ为其后代 | 检查限定于本项目创建身份，不按QQ.exe进程名选目标 |
| gate健康的connected/online/self_id_verified为true，stopping=false | 当时bot已在线；不证明这次上线经过免人工快登 |
| 项目原生QQ主进程参数含`-q`，账号与磁盘配置相等 | 排除该次主进程完全漏传快登账号；不证明Worker实际分支成功 |
| 原生QQ后代打开的`nt_qq`数据文件位于项目目录外 | 确认“程序在项目内”不等于“原生资料也在项目内”；不能直接断言与日常QQ共用或已独立 |
| 对已观察路径仅stat设备文件：Registry20大小290字节，创建/修改时间为2025-09-19 | 没看到文件每次被重建的迹象；未读/解密内容，不证明DPAPI成功、原生实际采用的GUID相同或服务端信任 |
| 登录凭据文件、身份记录、尝试目录均不存在 | 此现场未启用LAP-24项目密码回退；未读取真实密码 |
| `logs/napcat.log`最近一段只有HOST_START；其中“没有-q”来自10月16日旧段 | 不能拿旧段归因10月20日的新实例；目前缺完整快登结果 |

### 2.2 代码与锁定安装包

本轮复核安装`napcat.mjs` SHA256仍为`f80e4be3e8640369d23846cf3e8bcfd2a5b6dc5920f50d7ad733d7cca18179e6`，与旧24一致；QQ包路径为`runtime/napcat/installer/NapCat.52230.Shell/versions/9.9.33-52230/resources/app/napcat/`。以下行号是本轮读取时定位，后续用符号复核，不能机械依赖旧PLAN行号。

| 文件/符号 | 证据 |
| --- | --- |
| `scripts/manage.py`，`_start_channel` | 固定bundle/CWD、传`gate.bot_qq`，生命周期锁与幂等启动已有；本地组件就绪后phase=running，不等于QQ已登录 |
| `scripts/manage.py`，logging字典 | 启动写`fileLog=false`、`consoleLog=true`、级别warn |
| `scripts/process_host.py`，`safe_line` | gate/model有固定输出白名单，napcat没有登录事件分类；其原始stdout被丢弃，一般错误也只保留details_suppressed |
| `启动机器人.cmd` | 已传透参数，有`--no-pause`；目前只在首参数是它时跳过pause。自动启动包装器直接调用固定Python管理入口，不依赖改变参数顺序后的偶然行为 |
| `napcat_login.py:data_scope` | 无`native_report`就返回unverified；当前生产调用未接可信报告，手写身份JSON不能解除门槛 |
| `napcat_login_client.py:startup_fallback` | 仍要求project_only，先核已有通道；只在新实例可尝试一次。当前未达到启用条件，不等于保存密码即可工作 |
| bundle `qAe/getDataPaths`约82908行、原生初始化约83298行 | 原生目录来自`getNTUserDataInfoConfig`，无值才回退用户主目录`.config/QQ`；Windows global在`nt_qq/global`，再初始化engine/loginService |
| bundle `getLoginList`约83310行、快登分支及约83206行 | 从原生历史列表启动快登；WebUI快登列表会过滤`isQuickLogin`，是缓存列表，不等于完整历史/已验证可复用的票据 |
| bundle `CheckLoginStatus`约49810行 | 已有loginPhase/loginError/在线布尔；响应也含二维码URL，诊断须丢弃，不整包打印 |
| bundle logger约24867行、`initCore`约32916行 | 文件日志初始关闭；console级别的配置在Core初始化后应用。不能断言warn一定挡住登录前所有info；仅改warn→info也不能解决stdout被丢弃/管道重定向问题 |
| bundle `NAPCAT_WORKDIR`/`getNTUserDataInfoConfig` | 前者只控制NapCat自身config/cache/log等；未查到`QQ_DATA`配置或`setNTUserDataInfoConfig`调用，尚无本包可直接使用的Windows原生路径覆盖开关 |

外部只采用项目官方源码/文档与微软文档，见第12节。没有查到可以保证消除本账号反复验证的公开开关或实测例证；源码支持某能力不等于本机能力已验收。

## 3. “类似Cookie”的保存状态究竟是什么

存在三个不同层次，不能混用：

1. **WebUI管理凭据**：浏览器访问NapCat管理页面的授权。记住它只能省掉管理页面验证，不能使QQ在线。
2. **QQ原生登录资料/会话**：由QQ原生内核在实际资料目录维护，本包快登通过原生历史账号与`quickLoginWithUin`使用。正确方向是保留这套原生资料，让内核自行恢复；不是导出某一个网页Cookie再导入。
3. **设备信任/服务端策略**：设备文件保留、同一账号/机器/Windows身份只是连续性的条件，不能保证服务端永不再次要求验证。Registry20单文件、旧时间戳或目录存在都不能证明信任已建立。

“保存登录状态”可行，NapCat已有原生入口，但本项目尚未证明正常重启可复用。QQ资料不能当成跨机器通用Cookie。Windows相关密文采用CurrentUser DPAPI；换Windows身份/系统、只复制一个文件或还原过期票据都不能保证恢复。不能通过复制日常QQ数据解决本任务。

## 4. 路线比较与选择

| 路线 | 能解决什么 | 对每次新设备验证的作用 | 本轮选择 |
| --- | --- | --- | --- |
| A 保留现有QQ原生会话并快登 | 正常启动不输密码、不扫码；改动最少 | 若根因为读错目录、资料未保存、历史不可用等，针对修复后可能解决；须实测 | **首选**；先诊断，再修有证据的分支 |
| B 原生快登失败后自动密码回退 | 省掉手输密码 | 仍会收到needNewDevice/needCaptcha，不能独立满足目标 | 仅可选兜底，沿旧24单次/DPAPI合同；本轮不解除门槛 |
| C 给NapCat独立、固定的运行环境和持久资料 | 让资料归属及保存边界更明确 | 可排除混用/重建环境，但首次登录与服务端验证仍存在 | 备用；见下，不自动切换 |
| D 保持NapCat常驻，其他组件更新时尽量不重登 | 减少登录次数 | 不解决电脑真正重启后的恢复 | 可另行优化，不算完成本目标 |
| E 浏览器Cookie、记住WebUI密码、模拟点登录 | 省部分界面操作 | 不恢复QQ内核信任；挑战仍在 | 不采用 |
| F 更换QQ协议端/无头客户端，或任意改GUID | 需要新的兼容性与账号风险评估 | 无本机证据支持一定免验证 | 不采用，不由medium临场换框架 |

C的候选按成本分开：

- **Windows原生专属目录**：若以后找到该锁定包真正支持的进程内路径绑定，必须以原生实际路径证据及重启复核证明。`--user-data-dir`只能证明Chromium资料配置，不足以证明QQ内核路径；不改全局注册表/日常QQ设置，不猜开关。
- **专用Windows用户/虚拟机**：隔离NapCat可能更清晰，但用户配置、DPAPI、交互会话、启动方式都变化；CodeBuddy与模型网关仍留原有账号环境，不能连订阅账号一起迁移。需要独立规划/用户新指令，不能以普通修复直接创建用户或切换执行身份。
- **Linux容器/WSL中的NapCat**：官方Docker示例明确把QQ原生资料和NapCat配置分别做持久卷，是“保留状态”的公开例子。可只迁NapCat，保留现有模型路线；但Windows网关回环访问、reverse_ws认证、端口归属、容器自身设备信息及Docker启动依赖均待验证。不能照抄正向WS示例放宽入口，也不能直接复制Windows票据到Linux。它是备用部署路线，不是免扫码保证或本次默认实施项。

## 5. 第一阶段：取得可解释的诊断，不扩大日志采集

### 5.1 两个独立观测来源

**来源一：受管启动stdout的固定事件分类。** 在现有process_host中识别锁定包的登录生命周期，原始输入仅RAM有界处理；输出由程序重建，不能把原始行脱敏后整行落盘。只保留事件枚举和白名单结果码，忽略账号/昵称/二维码/签名URL/票据/群消息。必须先证明本启动器的登录输出确实经过该通道；named pipe/Worker可能改变输出去向，不能把“没有事件”当作没有尝试。

**来源二：可选只读WebUI观察器。** 使用本机操作者另行录入的WebUI管理token，先验证6099监听属于本实例PID+创建身份/受管后代，再在固定loopback读取状态、快登缓存与目标在线信息。它不接收QQ密码，不调用任何QQ登录/刷新/重启/设备/群接口。通过管理端认证只创建管理会话，不发起QQ登录。数据归属未核实时仍可做这个受限观察；这不能给密码回退或目录迁移解锁。

两者都没有证据时输出`telemetry_unavailable`。不启用完整NapCat文件日志，不采集原始HTTP响应，不更改全局日志级别来碰碰运气。现有包不兼容时先记录协议缺口，不能偷偷加第三条认证/登录路线。

### 5.2 观察器协议和上限（拟新增，尚未实现）

固定`127.0.0.1:6099`，禁代理/重定向，单请求3秒、JSON≤64KiB、全程≤120秒，总请求≤16：认证1次，状态至多12次，快登缓存至多2次，在线信息至多1次。状态轮询间隔不少于5秒；取消/实例更换/身份不明立即停止。持续活跃观察器不跟随Worker循环重连。HTTP200还须code=0及严格类型。

允许路由只有：`POST /api/auth/login`、`POST /api/QQLogin/CheckLoginStatus`、`GET /api/QQLogin/GetQuickLoginList`、`POST /api/QQLogin/GetQQLoginInfo`。认证SHA256协议沿既有WebUI实现，Bearer只在内存。2FA要求直接返回`management_verification_required`；不获取种子、不绕过2FA。没有token时仍能使用stdout和gate元数据，不阻断原生快登。

状态响应中的`loginError`只匹配本包已知错误类别/严格结果码，丢弃原文；`qrcodeurl`直接丢弃。快登列表仅内存比较目标账号，输出present/missing/unknown和`source=cached_webui`，不输出列表或人数；缓存的missing不能单独判为“原生没有历史”。登录信息仅输出account_matches布尔。未知字段不输出，未知状态不视为就绪。

首版结果码白名单固定为`0/140022008/140022010/140022011`，分别仅表达请求成功/验证码/新设备或异常设备要求；其他数字一律归other而非原样抄出。stdout事件仅是观测线索，不能作为重新认证、发密码、重启或宣告在线的授权；群消息中伪造日志头也不能改变登录动作。所有online结论仍由受管gate及实例身份确认。

### 5.3 原生目录与设备连续性

沿此前方法，从有创建身份的项目QQ后代所持文件路径取得“此时正在用哪个原生根目录”的观察，仅保存项目内相对路径或私有映射；公开报告只有project/external/unknown、是否与前次相同、设备文件是否存在及元数据连续性。失败/权限不足就unknown，不扫描全盘/所有用户资料来猜。

句柄路径证明“打开过”，不证明可强制绑定下一次启动、完整资料集合、专属所有权或原生采用的有效GUID。**外部目录继续按unverified处理**，不伪标project_only；不读取其中账号库/Registry20内容，不复制或重置。不用mtime相同宣称DPAPI已解密成功。只有以后取得可信原生报告和进程级强制路径控制，才可按旧24合同补专属身份提供器；没有现成报告接口，本阶段不伪造。

跨重启的路径比较仅在忽略的观察state中保留规范化路径的SHA256及scope，不保存外部绝对路径、不对外展示路径摘要。该摘要只比较路径，不能证明GUID或票据连续性。不能向外部原生根写测试文件来检查可写性；由原生自身写入结果或已证明专属目录的安全夹具补证。

## 6. 第二阶段：按证据修复与验证保存状态

| 实际分支 | 允许处理及退出条件 |
| --- | --- |
| 该次未传/Worker未收到目标账号 | 修本项目参数传递，验证主进程与Worker证据一致；不再加第二次SetQuickLogin补试；当前主进程观察已排除完全漏传 |
| 显式原生日志确认没有目标历史/不可快登 | 先查原生路径在成功登录前后及重启后是否一致、是否持久可写。由操作者在受控验收时完成一次正常QQ扫码登录；下一轮必须自行恢复，不能把每轮人工扫码算通过 |
| 路径每次变化、资料被项目清理、退出时未保存 | 仅修有证据的项目路径/清理/关闭缺陷；资料不删除。已有源码未发现项目主动删除Registry20，不能为凑根因虚构该修复 |
| 历史存在但快速登录返回失败码 | 先按该码定位；错账号/账号已在线/过期/认证挑战分别记录。不得直接猜为密码错误、顶号或GUID变化；禁止无限重试和自动换协议端 |
| 身份/路径稳定仍每次needNewDevice | 说明现路线未达目标。保留原始会话文件不操作，核对本包支持/版本已知问题后回规划；选择C须新指令，不将密码自动填入当修好 |
| 快登成功而gate未就绪 | 分开诊断反向WS/认证/目标账号校验；不重新登录QQ；无群发/模型探测 |
| WebUI缓存/状态不足、stdout被管道截走 | 标证据不足，允许交付独立诊断代码；下一步仅能规划有界本地观测接入，不直接修改vendor或开启原始群日志 |
| 外部数据归属仍不明 | 可继续观察现有自然快登、验证它是否可恢复；不操作外部资料/启用自动密码回退/宣称独立保存。若需要主动修目录，转C规划 |

先一次人工建立可用会话，再有两次正常退出/重启和一次真实Windows重启后的免人工恢复；确认资料正常保存、退出不会清空、Windows SID相同，QQ/bundle/启动目标固定。任何一次又需扫码就记失败，停止当前验收批次并回到分支诊断，不通过多次碰运气刷成功数。

Native内部行为不完全受项目控制：本包有Worker恢复/掉线快登链，不能因为项目只调用一次start就声称严格一次底层登录。诊断须区分project instance和原生Worker代次；不主动重启Worker、不额外补试。若发现内部登录重复/循环造成问题，记录能力缺口，不为压制它临时改vendor/全局环境。

## 7. 第三阶段：接入shell:startup（前两阶段真实门槛通过后）

### 7.1 默认选择与状态合同

默认当前用户Startup快捷方式，指向项目新增的`开机启动机器人.cmd`，再调用固定项目Python包装器。它复用现有manage/start-text及其生命周期锁、配置快照/访问控制，不另起一套NapCat，不改现有模型/账号/额度选择；参数绝不含QQ密码、WebUI token或家庭凭据。普通人工cmd入口继续可用。

1. Windows当前用户登录后触发，延迟30秒；最多120秒等待本机网络接口基础可用。接口有地址不代表互联网/家庭PC/模型已可用；没有地址到期输出dependency_timeout，不发起登录。项目所在E盘须在登录前已可访问；脚本本身在不可用盘上时无法自救，不自动解锁/挂载磁盘。
2. 只调用一次现有受管start入口。已运行返回现状、不重复启动；partial_running/端口冲突/cleanup未决按现有保护退出，不清台账、不自动kill/restart或自动改后端。启动前网络/家庭PC不可达只报告对应失败，不生成模型探测或自动换CLI。
3. 限时等待QQ就绪，最多120秒。只有本实例gate的connected、online、self_id_verified为true且非stopping，才记`qq_ready`。观察器与此等待共用120秒预算，不串行再加一轮等待。模型网关自身就绪另列；0真实生成，不能把元数据预检说成模型真实可用。
4. 验证要求记`verification_required`；账号不匹配记`account_mismatch`；证据不足记`waiting_login/telemetry_unavailable`。不自动输入密码/点挑战/刷新二维码。到期状态保留，包装器退出，已运行组件保持现状；后续操作者完成验证可由正常健康状态显示恢复，包装器不常驻循环。
5. 快捷方式运行可最小化；包装器无pause、无TTY输入、无自动开网页。失败详情限固定状态，保存在项目state并由“查看状态”显示。无人可见的窗口不等于启动成功。

登录状态单独建字段，不替换现有组件phase；建议`qq_login_state=starting/qq_ready/verification_required/waiting_login/account_mismatch/transport_unavailable/telemetry_unavailable`。状态查询始终只读，不能触发管理认证、QQ登录、模型推理或启动。

当前健康和创建身份优先于保存的观察：旧qq_ready不能覆盖实时离线/身份失效，旧verification_required也不能覆盖已由操作者恢复的有效在线。无新证据的历史原因明确标历史/未知，不让status为了刷新它自动认证。

新就绪等待和观察器必须在原有configuration_lock释放后进行；不把120秒轮询追加到持锁的`_start_channel`内阻塞关闭/配置动作。锁内只固定本次instance_id/快照与创建身份，锁外使用这份固定身份做观测；每次请求/原子写前后复核当前实例，旧实例不得覆盖新状态。状态写入只做短临界区，网络等待不持配置锁；用户停止后立即取消等待，不自动拉起。

### 7.2 注册、重复和撤销

拟提供`autostart install/status/remove`及`run`，install/remove仅在用户日后明确允许部署时执行；代码实现/测试绝不触碰真实Startup。默认只处理当前用户一个带项目身份标记的`.lnk`，记录根路径、固定目标/参数摘要及所有权。已有同名非本项目快捷方式拒绝覆盖；重复install幂等，remove须核对完整归属，不删其他启动项、不改common startup/注册表。

若后来需要任务计划程序，只能替代Startup而非同时启用，选择相同Windows身份的“用户登录时/仅用户登录时运行”，可利用延迟和不重复实例设置。不能默认SYSTEM、存Windows密码、改开机登录策略或启用全局服务。“开机未登录Windows也自动运行”是另一部署目标，本计划不声称达到。

## 8. 配置、默认值与生效方式（全部为拟新增）

避免为启动包装器把新未知字段硬塞进LAP-34五文件配置。本阶段不改变layout/schema，也不恢复已退役配置cmd；新管理动作加入现有`scripts/configure_bot.py`命令行接口。QQ账号及模型继续从既有统一配置快照读取。

| 字段/动作 | 默认与约束 | 位置、生效方式 |
| --- | --- | --- |
| `start-text --login-diagnostics` | 默认false；有界诊断，仅新实例启动时 | argv只含布尔；不跟随幂等start重认证 |
| `start-text --wait-login-seconds` | 默认0；整数0..300；自动包装器固定传120 | 只影响等待/状态，不改变触发/账号；0保持现有返回行为 |
| `start-channel --login-check-only` | 默认false；只允许channel入口，不能与start-text组合 | 受控QQ验收复用既有`paused=True`停止准入路径：不启动模型、不向AstrBot转发群消息；只报告qq_session_ready，不报可聊天 |
| `autostart run --delay-seconds` | 默认30；整数0..120 | 包装器参数，值固化在注册的快捷方式，安装后下次登录生效 |
| `autostart run --network-wait-seconds` | 默认120；整数0..300 | 只做无凭据的本机接口基础检查，无网络就绪不调用start |
| `secrets/napcat-observer.local.json` | 默认缺失；schema_version=1、management_token_dpapi_b64为唯一密文；≤16KiB、拒未知键 | 操作者日后通过本机无回显TTY录入，仅含WebUI token，不含QQ密码；CurrentUser DPAPI、不提交 |
| `set-observer-token / clear-observer-token / observer-status` | 不自动导入旧秘密；保存须停机/配置锁/原子替换；status只报告存在/可用元数据 | 既有configure_bot.py增加管理动作；不恢复配置cmd，不把秘密放stdin重定向/argv/env |
| `state/napcat-login-observation.json` | schema1，instance_id、observed_at、source、固定状态、目标匹配布尔、可选白名单数字错误码、native_scope及最多4个native_root_fingerprints | 原子写，单文件≤16KiB；不含账号、根绝对路径、GUID/票据/URL或原始异常。路径摘要仅本机忽略存储，只接受本实例更新 |
| `state/autostart-status.json` | schema1，instance_id、started/finished、phase、reason、qq_ready布尔 | 只由本项目包装器写；旧实例不能覆盖新状态 |
| `state/autostart-registration.json` | 缺失=未登记；固定目标/参数/项目归属及快捷方式位置 | 操作系统注册台账，不是QQ身份记录；只核对/操作自己创建的链接 |
| 旧`fallback_enabled` | 默认false；仍须专属原生归属、无回显录入及单次账本 | 本续作不自动开启、不绕过unverified、不把observer token当QQ密码 |

诊断日志对每次start最多32条事件、每条≤256字节，原始输入缓冲≤16KiB，超长行整条丢弃直至下一个换行；按实例/事件限流，不能把拼接出来的尾部当新事件。state不保存完整观察历史，保留最近实例与既有账本独立；不主动删除旧unknown或清理其他任务日志。管理token是秘密，即使不是QQ密码，也不得输出、写通用备份或注入其他组件环境。

## 9. 涉及文件与执行顺序

**本轮仅8份文档**：PROGRESS、工作线HANDOFF/TASKS、24 HANDOFF、旧PLAN/IMPLEMENTATION_GUIDE的入口，以及本PLAN/新实施指引。用户persona修改完整保留，不纳入Git。

后续实现的预期文件（尚未修改）：

- `scripts/process_host.py`：固定登录事件分类与长度/拼接防护。
- `src/qqbot_gateway/napcat_login_observer.py`（新）：固定只读WebUI、DPAPI管理token配置、脱敏分类/本实例观察；复用可安全复用的底层函数，不扩充密码客户端允许路由。
- `scripts/manage.py`、`scripts/configure_bot.py`：新启动参数、有界就绪等待/状态输出及管理token动作；保留同锁、幂等和配置快照。
- `scripts/autostart.py`、`开机启动机器人.cmd`（新）：单次启动、等待、归属注册/移除；若Windows快捷方式需要PowerShell辅助，只用固定脚本/结构化固定参数，执行隐藏，不改全局策略。
- 相关`tests/test_napcat_login_observer.py`、`tests/test_autostart.py`及受影响生命周期/日志测试、README、config/README的入口说明、本任务报告/交接。不修改persona、群协议、模型runner或vendor bundle。

| 顺序 | 可交付内容 | 进入下一阶段的门槛 |
| --- | --- | --- |
| P1 | 诊断/管理token独立代码、离线测试和说明 | 未连接真实6099，未改本机秘密；允许先交付 |
| P2 | 一次受控诊断批次与有证据的现路线修复 | 用户另行明确启停/QQ验证范围和唯一负责人；login-check-only先证明入站阻断，再进行无模型/群输出的QQ验收 |
| P3 | 自动启动包装器和注册器代码/离线测试 | 可与P1编码交付，但不安装真实Startup、不把其完成当免扫码 |
| P4 | 正常重启两次+Windows重启登录恢复；再安装并验Startup | 先登录恢复真实通过；操作系统安装/重启仍须用户指令 |
| P5 | 3个实际使用日的后续观察 | 不自动创建定时任务/提醒；只有用户另行要求才设监控 |

P2发现本包原生路径隔离或服务端验证无法解决时，停在明确分支、交付独立P1/P3，回到C路线规划。medium不得偷偷新增容器、Windows用户、付费API、设备修改器、外部代理或另一QQ框架。

## 10. 验证与验收矩阵

| 编号 | 有意义的验证 | 合格条件 |
| --- | --- | --- |
| O1 | 自造登录行夹杂账号/昵称/URL/票据/二维码/群正文、ANSI、长行、无换行碎片、伪造日志头/错误码 | 只出现枚举/白名单码，秘密及正文不进入stdout/state/异常；长行尾不能变合法事件，伪造日志不能触发登录或误报在线 |
| O2 | 假WebUI：2FA、HTTP重定向、code=-1、缺字段/错类型、慢响应/超大正文、缓存空/过期 | 固定类别失败，≤120秒/16请求；无QQ登录/刷新/设备或群API |
| O3 | 6099外部PID、PID复用、父进程退出后同名进程、Worker换代、实例变化 | 不发送管理token；观测取消/unknown，不影响当前bot |
| O4 | 合成管理token DPAPI保存/取消/并发/坏密文、清除及只读status | 无QQ密码需求；秘密只在secrets，锁/原子写/冲突保护有效；status零认证 |
| A1 | 临时根/假进程模拟wrapper并发触发、已运行、partial、端口冲突、网络未ready、等待中停止及实例更换 | 最多一次start，无自动kill/restart/切后端；长等待不占配置锁，停止可进入；旧状态不覆盖新实例，清理未决不被覆盖 |
| A2 | 本地端口打开但QQ未在线、错账号、二维码已扫但Core未ready、后续才连接 | 不能误报qq_ready；到期返回等待且不重登；在线由gate身份确认 |
| A3 | 临时Startup目录/替身快捷方式API：中文空格根、无关CWD、同名外部链接、重复安装/移除 | quoting正确、只管自己一个链接；无真实Startup/全局配置写入 |
| A4 | 既有生命周期、密码单次账本、配置快照/分层配置兼容 | 所有受影响回归通过，不改旧unknown；旧不带新参数的启动保持原行为 |
| A5 | login-check-only下模拟free入站/观察器启动、旧ready后离线、旧验证后恢复在线 | 群事件不转发/无模型和QQ输出；暂停时仅session_ready，观察器不被跳过；状态不受旧文件误导 |
| R1 | 操作者一次初始化后，两次本项目正常关闭/启动 | 每次0输入/0点击/0扫码，目标QQ会话匹配；暂停准入时只报qq_session_ready，失败即未通过 |
| R2 | 一次Windows重启并登录（注册Startup前），再手动cmd | 资料可跨系统重启恢复，仍0人工QQ步骤；非保留旧进程的假重启 |
| R3 | 安装唯一Startup入口后，一次真实Windows登录 | 正常生产模式自动达到qq_ready，无其他入口/人工补点；启动/健康不额外生成模型请求，正常群消息触发按用户运行范围另计 |
| R4 | 三个实际使用日记录 | 每日结果/失败类别清楚；不能宣称永久免扫码或服务端永不撤销 |

离线用临时根、合成账号/密码、临时端口替身；不得直接对真实6099跑测试或对真实Startup做测试。源码规划核对不是测试通过。

真实D/R1/R2先用拟新增`start-channel --login-check-only`复用现有`paused=True`：保留QQ反向连接，但gate停止入站转发，不启动模型。先以替身验证该组合；观察器必须能在此模式运行，不能沿旧`if not paused`分支被跳过。此时connected/online/self_id_verified证明`qq_session_ready`，允许stopping=true，因为准入被刻意暂停；不能把它标为正常可聊天的qq_ready。验收结束不自动解除停止标记或升级text模式。若无法证明入站阻断，先补独立能力，不直接启动free实例。

R3是正常text模式的真实部署验收，须用户明确允许恢复原授权群运行；free新消息可能自然触发模型/回复，不能同时承诺全程0推理/群输出。启动/健康不得额外做测试推理或发上线消息，实际正常触发另计。若用户只允许零推理，先保持login-check-only完成登录层/触发层的部分验收，生产R3与完整验收保持未完成，不暗改free或授权群。

## 11. 兼容、迁移、回滚与Git分支

- 旧自然分条/248单元/324框架记录继续按其日期理解，不以本次规划重复宣称通过。现有人设不改；17/18/20/21/27—35及旧真人差额均保留。
- 先不迁移原生资料。若必须移动，只允许已证明专属的项目源/目标、停机冷备且可恢复；不能备份整个日常QQ根或只复制Registry20冒充会话迁移。新Windows身份/系统/容器应重新做一次人工登录，不保证旧密文跨环境可用。
- 禁止日常维护清理native资料；缓存清理与登录资料保留分开。备份是否仍被QQ服务端认可必须实测，不能用“还原文件”反复重试已失效登录。
- 回滚先移除本项目唯一Startup链接/停用wrapper入口，再按身份停止本项目实例并恢复旧代码。保留会话目录、设备资料、QQ历史以及pending/unknown/密码尝试账本；不删除设备以求重新登录。不动其他Startup项/日常QQ/WorkBuddy/全局服务。
- 本次文档在当前main交付，仅暂存8份归属文档，长期授权commit/push；推送后核对完整SHA。后续若使用新分支，默认`codex/`前缀并登记归属；不强推、不覆盖其他session、不把规划当部署授权。
- 若bundle/QQ版本变化，当前源码定位及事件解析能力应标unverified，重新核对锁定版本再实施。不能自动升级QQ/NapCat解决未证根因。

## 12. 官方资料与未验证能力

资料核对日期2026-10-21；动态main文档只作部署示例，不能替代本机锁定包。

- [NapCat v4.18.38 Shell登录实现](https://github.com/NapNeko/NapCatQQ/blob/v4.18.38/packages/napcat-shell/base.ts)：原生资料根、历史快登、密码仍可能要求验证码/新设备确认。具体本地行为以上述bundle为准。
- [同版QQLogin管理API](https://github.com/NapNeko/NapCatQQ/blob/v4.18.38/packages/napcat-webui-backend/src/api/QQLogin.ts)及[路由](https://github.com/NapNeko/NapCatQQ/blob/v4.18.38/packages/napcat-webui-backend/src/router/QQLogin.ts)：只读状态与QQ登录/设备写动作是不同接口，观察器仅取本计划白名单。
- [NapCat官方快速登录示例](https://github.com/NapNeko/NapCatQQ/blob/main/packages/napcat-shell-loader/quickLoginExample.bat)：已有“传账号自动快登”的例子；不能证明本机免验证。
- [NapCat官方Docker示例](https://github.com/NapNeko/NapCat-Docker/blob/main/README.md)：QQ原生资料与NapCat配置分别挂载持久目录；只证明有保留状态的部署方法，不证明Windows票据可跨平台或必然免扫码。
- [微软Startup配置](https://support.microsoft.com/en-US/Windows/Experience/Startup-Boot/configure-startup-applications-in-windows)：当前用户Startup在该用户登录时启动，可通过移除对应快捷方式撤销。
- [微软CryptProtectData](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata)：默认用户相关保护通常要求相同登录凭据与机器；本计划不改为机器级密文来迁就跨用户启动。

仍未验证：本账号快登具体失败码/历史资格、稳定的原生根路径跨重启一致性、原生实际采用的设备身份、设备受信状态、同机日常QQ是否共享该根、Windows进程级原生路径覆盖、登录资料冷备恢复、stdout完整可达性、只读API在该包运行时的兼容性、免人工重启/Startup效果。以上均有分支出口，不作为已实现或已通过。
