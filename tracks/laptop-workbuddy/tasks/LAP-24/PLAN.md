# LAP-24：NapCat登录持久化与自然分条修正计划

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [本任务HANDOFF](HANDOFF.md)。继承[AGENTS](../../../../AGENTS.md)、[LAP-14分条合同](../LAP-14/PLAN.md)、[LAP-19群聊/表情合同](../LAP-19/GROUP_CHAT_PLAN.md)与[LAP-12生命周期](../LAP-12/HANDOFF.md)。

更新：2026-10-18（Asia/Shanghai），max职责复审版。用户明确本会话详细规划，之后由其安排gpt-6.1-sol/medium实施。本次仅只读核对/文档，未实施、未部署，未使用用户提供的密码；不自行检测或切换会话设置。medium可直接执行的步骤见[IMPLEMENTATION_GUIDE](IMPLEMENTATION_GUIDE.md)。

## 1. 需求与非目标

1. 项目NapCat尽量复用目标bot账号已完成验证的登录状态，减少重复扫码；遇到QQ要求的新设备/验证码验证时如实提示，不能承诺永久免扫码。
2. free/adaptive配置“最多3条”须成为真正的上限。先确定需要说什么，再按内容和群聊语气选择1、2或3条；简单应声或调侃通常1条足够，第二/第三条须有必要内容。认真回答保留完整性并合成1条。
3. 2026-10-17排查时保存配置只读确认：ollama_ssh、free、adaptive、max_bubbles=3、casual_max_chars=80、bubble_max_chars=40、web=true、memes=true。每条间隔800—5000ms。以上为历史保存配置快照，不证明当前运行进程已加载或用户此后未改配置；本轮未探活bot。

不改变授权群、真实@必答/普通新消息可沉默、黑名单入口、私聊关闭、后端/模型/额度或工具隔离；不增加付费服务、另一套QQ客户端、自动换模型、定时发言或第二次模型分类/润色。不中途改变正在发送的回复，不读取原始私密群消息定位风格问题。

## 2. 当前代码与排查证据

| 证据 | 可确认结论 / 限制 |
| --- | --- |
| `scripts/manage.py:20,300—303` | 固定项目NapCat bundle、固定CWD，启动NapCatWinBootMain.exe时已传入配置bot.qq；不是每次漏传账号。但没有证明底层实际QQ数据目录在项目内。 |
| 安装包napcat.quick.bat及ReadMe.txt | 传账号可快速登录；说明要求至少登录过一次。项目当前入口已具备这一启动形式，无需再改一个bat声称解决。 |
| 安装v4.18.38的napcat.mjs:82872—82881、83263 | QQ data root由原生getNTUserDataInfoConfig取得，无结果才回退用户主目录的.config/QQ；Windows global目录为data root/nt_qq/global。固定安装目录不能推导固定/独立登录数据。 |
| 同包napcat.mjs:49270—49364 | Windows设备GUID存于上述global/nt_data/msf/Registry20，使用CurrentUser DPAPI保护；跨Windows身份复制不保证可用。设备重置API会删除该文件。 |
| 同包napcat.mjs:82978—83165 | 有历史账号时先quickLogin；失败或无历史可使用NAPCAT_QUICK_PASSWORD或NAPCAT_QUICK_PASSWORD_MD5回退。密码回退也可能返回needCaptcha/needNewDevice并等待人工。 |
| 同包napcat.mjs:83324—83353、83535—83560 | 掉线恢复可重启Worker；createWorker复制process.env。原生密码环境变量会跟随Worker重启继续存在，不能靠父进程删变量保证整个项目实例只回退一次。 |
| 同包napcat.mjs:41716—41740、49210—49246、62019—62045、67244—67249、70934 | WebUI接口统一code=0/-1包络、data字段；认证POST /api/auth/login接收SHA256(token+'.napcat')，返回data.Credential；其他接口用Authorization: Bearer。不需要伪造JWT签名。 |
| 同包napcat.mjs:49781—49810、49823—49833、50118—50125 | 已有CheckLoginStatus/GetQQLoginInfo/GetQuickLoginList/PasswordLogin接口；PasswordLogin请求uin/passwordMd5，挑战通过needCaptcha/needNewDevice返回。这里是管理端登录接口，不是OneBot账号工具。 |
| `scripts/manage.py:295—312` / `scripts/process_host.py` | 目前共用子进程环境，没有本项目独立登录凭据注入；NapCat原始输出被丢弃，不能从现有项目日志证明每次扫码的完整错误链。 |
| `src/qqbot_gateway/persona.py:33—39` | free专用提示词只要求闲聊至多N条，没有普通adaptive分支的“不凑条数”；开启memes时还提示每轮至多1图，未强调不必发图。 |
| `config/persona.md` | 闲聊目标含1—3短句、15—60字；容易被当作需要达到的篇幅，和一句即可的应声存在张力。是静态线索，尚非模型根因复现。 |
| `group_protocol.py:54`、`media_protocol.py:29—40`、`reply_plan.py:107—131` | 保留模型给出的合法文字数组；超限合成单条，图片仅模型选择有效meme_id时追加。不存在按max_bubbles补空句或补图的逻辑。 |
| `reply_delivery.py:99` | 遍历plan.parts发送，间隔只影响速度，不决定数量。已有已处理标记/ACK保护保持。 |
| 本轮8项test_reply_plan既有单元通过；额外3项合成group_plan输入 | 模型数组1/2/3条分别保留1/2/3条，证明协议层没有强制凑满；不证明真实模型会自然选条数，也不是实际QQ发送验证。 |

2026-10-17排查时组合prompt为5134 UTF-8字节，含free/web/memes规则且没有“不凑条数”。这是未修改prompt的历史尺寸快照，不是额度/有效上下文实测。2026-10-18复核安装napcat.mjs的SHA256为`f80e4be3e8640369d23846cf3e8bcfd2a5b6dc5920f50d7ad733d7cca18179e6`；后续若安装包变动，先复核相关接口，不升级/替换bundle来迎合计划。

用户报告“经常新设备”和“每次三条”作为现场现象保留。本轮未从本机读取口令、登录票据或原始群消息；未发现足以认定设备GUID被每次重建、密码错误、同号顶号或某条模型输出结构的直接证据，不把这些猜测写成根因。

外部核对只用官方资料：[Shell快速登录文档](https://napneko.github.io/guide/boot/Shell)；[v4.18.38新设备验证代码](https://github.com/NapNeko/NapCatQQ/blob/v4.18.38/packages/napcat-framework/napcat.ts)。前者说明快速登录入口，后者明确密码登录仍可能需新设备扫码；本机Shell细节以上述安装包证据为准，不用最新main替代锁定版本。

## 3. A：登录持久化行为合同

### A1. 先确认数据归属，再谈保存/迁移

- 保留当前目标bot.qq、bundle、Windows操作者与CWD。先只读核对受管NapCat进程的PID+创建身份、实际使用的QQ data root和历史账号是否包含目标，输出仅固定状态或布尔值；不列出其他账号/昵称，不打印票据、GUID或路径中的无关个人资料。
- Native QQ data root与NapCat自身config/cache目录分开核验。NAPCAT_WORKDIR控制后者，不能当作已隔离QQ登录数据的开关；不能仅设置Electron user-data-dir就声称原生登录目录已改变。
- 当前没有已验证的Windows原生data root覆盖方式。实施方先查锁定启动器/原生配置的可验证能力；若只能找到日常QQ共享目录，不读取其中账号库/Registry20内容、不改全局注册表/日常QQ设置、不复制其票据，记录能力缺口回规划。可先独立交付分条修正和密码回退，不伪称已实现登录数据隔离。
- 若确认当前已使用本项目专属、可持续写入的数据目录，则沿用并在忽略的本机身份记录中固定。普通关闭/重启不得清理该目录、Registry20或历史登录记录；不调用ResetDeviceID/SetDeviceGUID，不生成或冒用另一设备GUID。
- 数据目录确需迁移时，仅在已证实的项目目录之间进行，先停本项目受管实例并保留原副本；实际源/目标归属、路径覆盖方式和DPAPI可用性须有证据。不能在能力未证实时照计划猜路径搬动。

### A2. 登录顺序与失败行为（本版取代原生密码环境注入方案）

1. 普通启动继续让NapCat使用目标bot.qq进行原生历史快速登录。已有gate确认目标账号在线时直接完成启动，不为检查密码额外认证。
2. **选择固定WebUI单次回退，不向常驻进程环境注入密码。** 仅操作者已保存并启用本项目回退、A1项目数据归属有可信证据、受管NapCat身份与6099监听归属均核验通过时，项目启动控制器才可用现有WebUI PasswordLogin尝试一次。不上原生NAPCAT_QUICK_PASSWORD/MD5路线；因此Worker恢复不会因本功能重新继承密码。
3. 原生登录尚在initializing/reconnecting、二维码已扫描/已接受、QQ已登录其他账号或状态不明时，不提交密码，不登出其他账号。只有确定未登录、稳定进入waiting_qrcode且未接受扫码时才允许回退；已有人工操作优先。状态检查和提交间若发生扫码竞争，以接口拒绝/后续匹配在线为准，不重试。
4. 提交前以当前service-mode.instance_id和目标账号摘要写一次性尝试账本，先占位再POST。写失败不发请求；有记录/损坏记录均不再尝试。请求超时、取消或响应丢失为unknown，同一实例禁止再试；重跑启动命令/Worker重启不会重置账本。用户明确关闭并新启动是新的实例，可重新按设置尝试一次。
5. needCaptcha、needNewDevice、WebUI认证要求2FA、账号不匹配、错误密码或协议错误均停止自动流程，显示固定原因，保留普通WebUI二维码人工登录。不自动跟进验证码/新设备接口，不声称浏览器一定能续接脚本内存中的挑战；挑战URL/signature不保存。未启用、数据归属未证实或解密失败时也保持原快登/扫码，不让可选回退失败导致整套bot反复启停。
6. 仅普通start的本次新建实例执行这个可选有界流程；幂等start、status、健康检查、connection-check、模型请求和后台定时任务都不触发密码尝试。无自动重放/额外登录守护进程，不修改NapCat原有Worker恢复机制。
7. PasswordLogin成功包络只证明请求被接受；成功显示仍须核对GetQQLoginInfo的uin匹配和现有gate self_id校验/QQ在线状态。限时内只确认登录而通道未就绪时显示channel_waiting，不再认证。整个登录流程不触发模型、不发群消息。

### A3. 固定管理接口、预算与状态

固定访问`http://127.0.0.1:6099/api`，不接受任意URL/端口/路由配置、不使用代理、不跟重定向；每次敏感提交前复核监听PID仍是本实例有创建身份的NapCat进程/受管子进程。认证失败、监听被替换、停止标记或实例切换即退出。

| 接口 | 严格用途/数据 | 次数上界 |
| --- | --- | --- |
| POST /auth/login | hash=SHA256(WebUI token+'.napcat')；只取data.Credential，不保存。require2FA直接停止，不读TOTP种子/不关闭2FA | 1 |
| POST /QQLogin/CheckLoginStatus | 仅取布尔isLogin/isOffline/qrLoginAccepted/coreReady和已知loginPhase；qrcodeurl/loginError不输出/持久化 | 合计最多4，含提交后的确认 |
| POST /QQLogin/GetQQLoginInfo | 仅在已登录/可确认时取uin核对目标；不记录昵称、头像或其他字段 | 1 |
| GET /QQLogin/GetQuickLoginList | 可选，仅计算目标账号是否存在；不列出/保存其他账号 | 1 |
| POST /QQLogin/PasswordLogin | uin来自当前bot.qq，passwordMd5仅在内存计算；响应只取code及needCaptcha/needNewDevice等允许字段 | **1** |

单次可选流程总期限20秒、单HTTP请求至多3秒且受剩余总期限约束；响应正文上限64KiB。状态检查之间至多等待2秒，受停止/实例失效取消；最多8个HTTP请求，不自动重新认证或重试POST。没有确认到可回退状态时标waiting_login/unknown，交给人工，不扩大时间/调用上限。认证凭证不能放URL参数或日志。

“稳定未登录”具体为至少连续两次CheckLoginStatus均明确isLogin=false、qrLoginAccepted=false、coreReady=false、loginPhase=waiting_qrcode，期间实例/监听身份不变；缺失字段或未知阶段不满足。使用同一最多4次状态预算，不另加隐藏轮询。

`state/napcat-login-attempts/<instance_id>.json`是忽略的本机账本，实例ID必须匹配当前service-mode的32位小写hex值并解析在该项目目录内。字段为schema_version=1、instance_id、bot_account_sha256、state、updated_at，以及可选固定枚举reason；state仅attempting/accepted/verification_required/failed/unknown/confirmed，不含口令/MD5/token/挑战/原始错误。在已有启动锁保护下原子占位，先于密码POST；相同实例的既有/损坏文件不能当作“从未尝试”。新实例另用新文件，保留旧unknown记录，不自动清理。状态只供本机启动/状态页，模型和OneBot均没有调用入口。

### A4. 本机凭据与配置合同

| 字段/文件 | 缺省与保存方式 | 生效方式 |
| --- | --- | --- |
| 既有bot.qq | 保留操作者选择；不新增第二套目标账号字段 | 正常启动继续传目标账号 |
| `secrets/napcat-login.local.json` | 新可选忽略文件；缺失即不启用密码回退。精确字段schema_version=1、bot_qq、fallback_enabled、credentials_dpapi_b64 | 明确保存后下次启动读取，不热改运行实例 |
| fallback_enabled | false；仅布尔。保存密码并选择启用才变true | 仅影响NapCat快速登录失败分支 |
| credentials_dpapi_b64 | CurrentUser DPAPI密文，解密后JSON恰含qq_password、webui_token；二者均不保存明文/摘要，不进入settings、argv、环境、日志、报告或Git | 启动控制器仅在实际需要时解密并在内存计算协议摘要；不声明Python能可靠擦除所有副本 |
| 本机身份记录`state/napcat-login-identity.json` | 可选schema1：data_scope、qq_data_root、bundle_path、windows_user_sid_sha256、evidence_method；scope为project_only/shared/unverified，只有原生路径报告或已验证启动器原生配置可支撑project_only | 启动复核路径/身份；没有可信来源即unverified，不能只凭目录存在或用户说明标实证；只控制可选密码回退，不阻断既有快登/人工扫码 |

配置入口在`configure_bot.py`增加`napcat-login status / set-password / clear-password`，连接页新增“NapCat登录”子项，原1—6编号保留。set-password通过本机getpass分别无回显录入QQ密码、项目NapCat WebUI token；不从其他账号/旧材料搜集。回车取消/EOF/Ctrl+C不改旧文件；不strip有效口令、不将其转大写/归一化。不要求用户在新聊天再次粘贴密码。

保存前沿用受管运行身份检查/独占锁、配置及旧凭据摘要冲突检查、临时文件flush/fsync与原子替换。新文件上限16KiB，秘密单项UTF-8字节上限4096；这是资源界限，不推断QQ口令规则。密文只存secrets，备份如需保留也仅secrets内；不把通用settings备份逻辑套到口令文件。未核实数据归属时允许保存但不启用，启动仍须再次核验。clear-password只移除本项目回退凭据，不登出QQ、不删设备记录/一次性账本；status仅显示有无/启用/账号匹配/固定状态，不解密探测密码有效性。

所有受管子进程环境均移除继承的NAPCAT_QUICK_PASSWORD/NAPCAT_QUICK_PASSWORD_MD5/NAPCAT_QUICK_ACCOUNT，NapCat也不接收这些变量；目标账号仅沿用已有启动参数，秘密仅启动控制器内存可见。不得setx、写全局环境或修改第三方bundle。DPAPI使用CurrentUser/禁止交互UI，经stdlib ctypes调用Windows API并释放结果缓冲；路径必须解析在本项目secrets内。安全保存/解密不可用时不回退明文，不改变Windows用户来试密码。

登录状态优先复用现有QQ层级状态；新增辅助状态由客户端已验证包络/布尔字段或本地固定原因生成，不解析或放行NapCat自由格式日志。`process_host.safe_line`继续丢弃原始上游错误、验证URL和聊天内容，无需为本功能扩大白名单。不能从一个“需扫码”提示猜成凭据失效。

## 4. B：按实际内容自然选择条数

### B1. 一次生成中的表达规则

在compose_persona中用同一份短规则覆盖free、mentions/adaptive及受控表情协议，避免提前return导致规则遗漏；保留single最终合并与认真回答合同。建议规则语义：

> 先决定必要正文，再选择自然的消息段数。最多N条只是上限，能一条说清就一条；需要独立补充才第二条，确实有第三段必要内容才第三条。不凑条数、不凑字数、不把一个短句拆开发。简单应声/调侃通常一句即可。认真回答用answer完整一条，不为缩短省要点。表情可不发，没有必要就meme_id=null，不用图片填满额度。

删除人设“15—60字”这类最低篇幅暗示，保留角色性格与简短应声例子。正文以“通常一句或一两句就够，按实际内容补充”为方向，不改成每轮必须单条。人设只作为内容材料；group/free/web/表情的实际能力和触发仍由固定规则控制。

添加少量人工场景示意：应声/感谢1条，确有补充的闲聊2条，内容较丰富且自然分开的闲聊3条；认真问题1条完整。1条示例应覆盖最常见短场景，不能所有JSON样例都恰好塞满当前上限；这些是提示样例，不是模型实测结果。

实现选择：共享规则由persona.py中的一个短构造函数/常量产生，放入各协议分支之前；不再分别手抄三套表达规则。single的有效文字条数为1，adaptive为1..max_bubbles；表情部件上限仍按LAP-21独立核验。仅当实际模式/上限允许时才展示2/3条示例，max=1不得收到“需要时三条”的矛盾指令。普通single且memes关闭仍输出纯文本，不因风格修正强制新JSON协议。

| 人工场景 | 表达方向（非真实模型结果） | 验收关注点 |
| --- | --- | --- |
| 仅叫名字、表示收到或感谢 | “嗯？咋啦”“那就好～”这类一次自然接话即可 | 1条足够；可短于15字，不附固定追问/告别/图片 |
| 闲聊中有一个确实需要独立补充的点 | 先接住当前话，再补一句有用内容 | 可1或2条，不能为了测试凑第二条 |
| 较丰富的闲聊有三处独立且自然的内容 | 按语义安排，必要时3条 | 3条仍合法，不对模型结果随机删尾；也不要求每个此类问题必发3条 |
| 简单事实/认真解释/代码/网页材料 | 需要多少说明多少，完整放在answer | 1条完整，不能为角色短促而遗漏关键条件 |
| 普通闲聊且表情库可用 | 文字足够就meme_id=null；有必要时选本次候选 | 不预留表情位置，文字+图片总量不能超出上限 |

人设末段如需同步，改为“依据系统交给你的本次对话材料，权限/能力/输出按固定政策”，避免继续把free描述为只有本人历史；不增加新能力或触发范围。最终prompt只放少量短示例，完整场景矩阵留在测试/文档，避免为了强调简短反而膨胀系统输入。

### B2. 下游不代替模型凑段数

- 保留现有严格协议、一次生成、1..max_bubbles准入、超限保留全文合并、工具污染过滤、可信metadata、逐条ACK及失败即停。不随机抽取1/2/3，不按固定字数或标点切段，不丢掉第三段来制造“自然”。
- 文本段落与QQ消息数量分开：一个消息可含两个相关短句；无需把每句单独发。80字总长/40字单条仍是分条准入上限，不是目标或最低字数。
- 当前memes=true必须覆盖：图片计入3条总限额、最多1图，不预留图片名额；一句文字已经够就可只发一句，meme_id=null。认真answer/网页来源仍无图且1条。既有明确索要表情/ambient仅图分支保持。
- 不新增条数/概率/短句长度配置，不改schema3或操作者的现有输出限额/间隔。max_bubbles=1/2/3均有同一语义，不能把“通常1—2条”写成绕过max=1的指令。
- 如果补强提示后真实所选模型仍习惯性三条，先记录脱敏计数与场景接受差额回规划；不能擅自添加截断合并阈值、第二次润色或换模型。

## 5. 涉及文件与实施顺序

建议一个后续实施任务沿用LAP-24交接，依次完成下列阶段；若另拆session领取，先明确TASKS/文件归属，不让两个session同时修改共享菜单或索引。

1. **自然分条独立修正：**`src/qqbot_gateway/persona.py`、`config/persona.md`；扩充必要的现有reply_plan/group/media框架场景，核对两个compose使用点`configure_astrbot.py`与`plugins/qq_router/main.py`输出一致。原则上不改解析/发送/历史实现。
2. **登录只读归属核验：**`scripts/manage.py`现有创建身份、锁定NapCat源码/启动器与项目本机路径元数据。先确认A1能力缺口，原始本机路径/设备资料只在忽略文件，不写公开报告。不触碰日常QQ数据。
3. **最小密码回退：**新增`src/qqbot_gateway/napcat_login.py`负责严格本机凭据/DPAPI/身份与一次性账本，必要时拆`napcat_login_client.py`承载固定WebUI客户端；`scripts/manage.py`清理子进程环境并在新建实例启动阶段接入单次流程；`scripts/configure_bot.py`添加无回显入口/状态显示。复用已有锁/创建身份，不重入启动锁；私密文件原子保存单独实现，不安装新依赖、不改第三方bundle或扩大process_host日志。
4. **离线与框架验收：**相关tests、新scripts/verify_lap24.py复用verify_lap20/21的verify函数并加入受影响用例；失败先修受影响路径，不扩大到无关功能。旧脚本main会写旧reports，不直接用来覆盖历史结果；本任务脚本只写新lap-24报告，底层调用维持合成。
5. **文档/Git交付：**README配置/实际效果/登录限制；本任务HANDOFF/报告及PROGRESS、工作线HANDOFF/TASKS。只提交本任务已检查内容，按长期授权push并对比完整SHA；忽略文件继续排除。
6. **运行加载/真人验收：**另由明确的实例负责人按用户指定范围执行；保持待处理ACK/unknown保护。规划和Git交付都不构成启停、登录或真实模型/群发授权。

遇到登录数据目录缺口，仍完成第1项与可证实的独立部分并交付；不能将整项标为完整验收。当前会话仅完成计划，未执行以上实施阶段。

## 6. 验证与验收出口

| 层次 | 验证内容 | 通过标准与不能替代的证据 |
| --- | --- | --- |
| 本次排查基线 | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_reply_plan.py` | 8项既有单元通过；3项合成group输入1/2/3保持相同数量。只验证当前协议不填满。 |
| 提示词/配置离线 | free/mentions × single/adaptive × memes开关 × max=1/2/3共24个基本组合，另核web认真回答；两个生产compose调用点 | 所有适用分支有上限非目标/短场景规则，无模式政策冲突；prompt尺寸进入现有输入预算，不能随意扩大预算或删除隔离政策腾空间。不能靠断言某几个字存在就宣称自然程度通过。 |
| 实际框架合成 | 两后端真实runner底层替身，1/2/3条chat、answer、silent、文本+表情、重复hook/失败/取消 | 精确发送预期条数、不补发，ACK/历史只认成功前缀；沿用LAP-22真实run_agent生命周期，禁止手动补链掩盖装饰链问题。 |
| 登录离线 | 凭据缺失/关闭/损坏、错账号、DPAPI错误、原子保存失败/冲突/运行中拒写、带空格中文的合成秘密、环境分配 | 不做真实认证；任何失败不暴露秘密/改全局，所有子组件含NapCat都无密码回退变量，命令行无秘密；快登和人工扫码仍可用。 |
| 固定WebUI/尝试账本离线 | 假管理服务包络、2FA/验证要求、HTTP200但code=-1、错账号、非受管PID、扫描竞争、超时/中断/重复调用/Worker重启/损坏账本 | 正确认证哈希/不把WebUI token当QQ密码；先记账再POST，同一instance+目标至多1次PasswordLogin；unknown不重放，状态页不认证。每项均为合成服务/秘密，不连6099。 |
| 受控本机无推理 | 只在用户后续指定范围和实例归属后，按创建身份暂停准入启停；首次人工验证后同一身份/同一目录正常重启两次 | 核对目标账号、在线和项目数据未清理；记录是否每次要求扫码。不能从磁盘文件存在推出登录可复用。不得接收群验收造成模型消费，不能测试日常QQ密码。 |
| 真实表达接受 | 用户后续明确授权小批真实模型/群场景；应声、感谢、调侃、两段必要补充、三段自然闲聊、认真问答 | 短应声/感谢1条；两段、三段场景按真实内容接受，认真问题1条完整。无需人为凑齐统计分布；如有抽样，记录场景/次数/条数与用户接受，不存原始私密正文，不拿合成文本冒充模型输出。 |

实施时先运行受影响单元，再运行LAP-20/21/22受影响框架回归；若改登录生命周期再运行test_lifecycle/test_process_host及身份归属/环境隔离测试。仅提示词/文档变化不新增镜像实现的无意义测试；选择能发现分支遗漏、固定条数或凭据泄漏的用例。

分别记录“已规划”“已实现”“离线通过”“受控本机登录通过”“真实表达/QQ通过”“完整验收通过”。QQ服务端仍可能要求再验证，因此“持久化通过”只能表述为记录条件下复用了状态，不是长期永久免扫保证。旧LAP-10/18及其余真人差额保留。

## 7. 兼容迁移、分支与回滚

- 首轮main开始干净，基线`5024879ad06446ae7f12cf8a2e908d44a0cc5b79`；2026-10-18续作基线`cf69570a1a4c129f17c9d13750890ca41a04edb1`且干净。规划文档可沿用main交付；实施先重新核对status/归属；需分支时使用codex/前缀，不覆盖其他session修改，不强推。
- 现有schema3及本机输出/后端选择保持，不自动降低max_bubbles、不改睡眠/SSH/Ollama或日常QQ/WorkBuddy设置。新登录凭据文件缺失时完全兼容既有快登/扫码；明文旧密码不会自动扫描导入。
- 自然分条提示改变会通过现有session_version建立新当前上下文，旧个人历史保留；free RAM按既有重启/epoch机制更新，不迁入个人持久历史、不回拉QQ群历史。
- 回滚分条修正时，只回退本任务提示词/人设变更，在协调加载后生效；不删除pending/unknown账本、历史或图库，不通过重放群消息验证。
- 回滚密码回退时，先停本项目受管实例，禁用专属回退设置并移除本任务WebUI调用接入；保留一次性/unknown账本及既有QQ设备/登录目录。不能通过删除账本重试不明结果。密文解密失败不降级明文，变更Windows用户不自动搬迁DPAPI资料。
- 需要数据迁移而路径控制尚未验证、新设备仍反复出现、或新提示风格仍不接受时：记录独立交付与未验部分，回到本计划补证据；不通过重置GUID、清空QQ数据、再登录循环或换客户端规避。

## 8. 本轮交付状态

2026-10-17首轮完成规则/源码/白名单配置核对、官方资料核对、8项既有单元与3项合成协议基线。2026-10-18续作只读补核Worker/认证/固定登录接口，明确本版单次WebUI方案、配置和失败分支，并新增[medium实施指引](IMPLEMENTATION_GUIDE.md)；没有重新运行单元/框架或进行认证。两轮只写本任务文档及索引，未改代码、人设或运行配置，未操作服务/QQ登录、密码认证、SSH、真实模型或群消息。Git提交/推送记录见[HANDOFF](HANDOFF.md)。
