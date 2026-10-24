# LAP-40 SnowLuma替换试运行计划

返回[项目入口](../../../../PROGRESS.md) / [任务交接](HANDOFF.md) / [实施指引](IMPLEMENTATION_GUIDE.md) / [任务台账](../../TASKS.md)。

2026-10-24，Asia/Shanghai。基线`66eea49623b76766e0569614207c80c78e57115f`，规划分支`codex/lap-40-snowluma-trial`。用户授权使用branch；随后明确规划完成后由本会话逐步调用`gpt-6.1-sol / medium`实施，由根agent复核。此计划本身不代表已安装、已切换或长稳通过。

## 1. 目标、边界与交付判断

目标是将SnowLuma作为可显式选择的QQ传输端，在本机专用QQ上试运行，优先解决长期运行中“进程/WS/online仍在但真实@无响应”的可发现性与有界恢复。既有链路保持为“专用QQ → SnowLuma → 项目gate → AstrBot/qq_router → 操作者已选模型”。NapCat保留为显式回滚项，不自动双开或自动切回。

先交付能独立完成的代码、离线验证、操作入口和阻断报告；只有所有真实前置成立才切换。不能因为操作者睡觉而代替其扫码、读取日常QQ登录资料或接受未授权的新增许可条件。真实运行前置缺失时，不停原bot，不修改本机provider，记录精确缺口，继续完成其余实施阶段。

非目标：更换QQ账号/授权群/黑名单；开启私聊；扩大真实@或free范围；更换CodeBuddy/Ollama/模型/额度来源；新增付费API；迁移到家庭主机、Linux、WSL、Docker；恢复已放弃的Startup；改人设或历史预算；新增定时主动群发、探活生成、任意媒体/MCP/SDK工具。LAP-18/24/28/29/31B等旧差额全部保留。

验收状态必须分开记录：①详细规划；②项目集成已实现/离线通过；③私有运行适配已核验；④本机真实接入通过；⑤72小时初筛；⑥固定环境7天长期验收。前一项不能替代后一项。

## 2. 当前证据与设计依据

已读根AGENTS/PROGRESS、工作线HANDOFF/TASKS和[LAP-39评估](../LAP-39/SNOWLUMA_ASSESSMENT.md)。本轮是静态核对，没有重新探活；00:36:41等故障时间均是39历史证据。

| 证据位置 | 已确认事实 | 设计要求 |
| --- | --- | --- |
| `scripts/manage.py`、`scripts/process_host.py` | 组件、6099、安装路径和登录观察硬编码NapCat；已有PID/创建时间登记、启动快照、stop marker和受管子进程回收 | 引入provider描述，沿用身份与快照，不按进程名结束；加载实例的provider决定停止行为 |
| `src/qqbot_gateway/onebot_gate.py` | 当前observe_online只消费online；严格Bearer/X-Self-ID/Universal；入口/发送/RPC已有授权和最终栅栏 | SnowLuma额外消费good和独立证明；统一检查所有入站、上下文和发送通道 |
| `config_files.py`、`config.py` | 五文件布局、schema1/2/3→3、snapshot原始SHA与规范化semantic_digest双校验 | 新字段缺省时不能向旧规范化数据插默认值，否则旧快照摘要失配 |
| `lifecycle.py`、`reply_delivery.py`、`plugins/qq_router/main.py` | 实例停机标志、连接代际、未知/部分发送与ACK后历史、停言票据 | 不重放未知发送，不跨旧连接释放模型结果，不绕过最终输出栅栏 |
| 本机项目QQ `resources/app/package.json` | main为`./napcat/napcat.mjs` | 此QQ不是干净QQ，不可再注入SnowLuma作对照 |
| LAP-24原生数据范围 | 原生QQ数据位置、免扫码连续性尚无完整证明 | 不能以安装目录、环境变量或猜测参数冒充数据隔离 |
| 本机Node只读检查 | v24.22.0 | SnowLuma实际构建/运行需自带合格Node，不改全局或WorkBuddy Node |

固定上游[SnowLuma v2.1.1](https://github.com/SnowLuma/SnowLuma/releases/tag/v2.1.1)，tag SHA=`f8cb15c27bca3d2d1bd044a921e55bfc44bb5e60`；Windows完整包`SnowLuma-v2.1.1-win-x64.zip`，42,694,125字节，SHA256=`c739171f95c27706767e69ba36099707c222fcec639b46f4d59689997b527772`。包内含Node、不含完整QQ。源码engines为`^24.22.1 || >=26.12.1`、pnpm11.25.0；不得用当前全局24.22.0冒充满足条件。实施时只复核固定版，不自动升级到新发布。

上游关键能力与限制（只读源码证据，不是本机通过）：

- [接收看门狗](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/bridge/src/hook-session.ts)在首次见到`SsoHeartBeat`后才armed，90秒无接收加15秒确认；初始receiveHealthy为true，所以未armed的good不能证明健康。停滞只报告，不自动重登。
- [Windows管道重接](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/bridge/src/hook-manager.ts)可重连仍存在的管道；开启auto-load后Windows并无本项目账号白名单。必须启动前固定auto-load=false，并禁止通用QQ枚举/识别影响其他实例。
- [get_status](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/actions/info.ts)的good包含receiveHealthy；反向WS支持Bearer、X-Self-ID、X-Client-Role=Universal，消息字段名为messageFormat=array。
- [instance.ts](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/instance.ts)在网络分发前存储、记录接收日志并处理默认启用的#sl直接答复；[event-pipeline.ts](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/event-pipeline.ts)先调用backfillReplyTarget。historySync=false不关闭引用补拉。
- [MessageStore](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/message-store.ts)经sqlite-open打开路径，`:memory:`是候选RAM方案，须验证实际SQLite连接及其他store均无磁盘回退。日志文件级别不控制全部console/ring/subscriber；只设warn不足以保证无消息记录。
- [Windows启动器](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/runtime/launcher.bat)不提供整个Node/QQ的守护；#549等旧issue关闭不构成本机长期恢复证明。

## 3. 前置门槛：许可、原生包和干净QQ

### G0 发行与私有适配

本仓库`hann-8/qq-persona-bot`已核对为public。上游[LICENSE](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/LICENSE)允许规定范围的非商业私有修改，公开修改版/衍生版有额外限制；[EULA第5.4条](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/EULA.md)明确限制专有原生组件复制、重打包和自动化脚本部署。本计划据此限定技术交付方式，不作法律适用的扩张判断。

1. public仓库只提交本项目原创的provider适配、策略模块、接口合同、自造测试和文档。不得提交上游修改源码、patch/diff、衍生bundle、原生二进制或带它们的安装器。修改过的上游源码与私有构建仅留忽略的`runtime/snowluma-private/`；实施报告只记路径/摘要/固定能力项。
2. 不写自动下载/解压/复制/重打包原生组件的脚本，不clone整仓后把native blob当普通依赖搬运。原版完整包须由操作者按条款准备在项目忽略目录；或具有范围匹配的书面授权后另记录证据。源码阅读和原创适配/离线测试可继续，不把“可读源代码”当部署原生组件授权。
3. 私有JS适配不得改动原生组件、许可/激活/完整性保护。若官方校验拒绝私有JS构建，记录能力缺口；不关闭校验或修改保护。构建只处理JS/TS；阶段3已确认普通core build与build:all均会检查/复制native，二者都不能直接作为本任务构建方式运行。需另证保留合法同意/保护、只产JS且原生组件原位置/摘要不变的方式。不能证实时真实部署仍阻断，见[固定源码清单](PRIVATE_WIRING_CHECKLIST.md)。
4. 不伪造EULA接受。PRIVACY提及遥测机制但也注明截至其修订时尚未发布；不由文档推断2.1.1实际遥测。私有运行按文档设SNOWLUMA_TELEMETRY=0并关闭通知/webhook/自动更新，不引入外发诊断。

缺少预备包/适用授权是“真实部署前置未满足”，不是阻止阶段1/2/4原创代码与离线测试的理由。也不能把上述门槛改成一个可随意填写true的配置开关。

### G1 专用QQ与数据范围

需要可信的干净NTQQ入口，候选位置`runtime/qq-snowluma/QQ.exe`，不复用已patched的NapCat QQ。操作者准备的原始文件、原生账号数据范围、进程exe/创建时间/父子链和加载组件需形成忽略的本机证据。不得推定某个package.json main值就是原版，不直接覆写原入口。

只加载控制器本次创建并登记的QQ PID；不adopt已存在QQ，不按名称结束/注入，不用Windows全局自动枚举挑选。QQ原生数据路径需可信文档/源参数和有界进程文件访问证据互证；只检查项目已指定根，不遍历日常QQ资料，不读取认证内容。若NTQQ无法隔离到项目归属范围，转为能力缺口，不通过改APPDATA/HOME或臆造--user-data-dir来声称已隔离。

验证数据范围所需的受控QQ探针属于后续真实阶段：全链入站DROP、不启动AstrBot/模型，不发消息；最多一次创建，240秒超时，可能需要操作者在自己的QQ窗口扫码。操作者不在、无预备材料或数据范围无法确认时，留在waiting_operator。不得为了收集证据碰日常QQ或反复登录。

## 4. 真实行为合同

### 4.1 两层入口与私有SnowLuma运行模式

gate仍为项目访问控制和输出的唯一权威。新增原创`adapters/snowluma/project_policy.mjs`可供私有适配调用；必须在QQ事件进入转换、缓存、日志、历史查询前判断：当前受管实例/账号匹配、group新消息、授权群、发送者非黑名单且非self。阶段3确认core BridgeManager raw trace、protocol packet-pipeline的identity enrichment/handleSideEffects/printEvent早于OneBot监听；私有准入须在这些位置之前，以经审计无副作用的最小原生信封投影接`admitEnvelope`，OneBot convert前才过滤不够。私聊、未知/畸形身份、未授权群、黑名单直接丢弃；拒绝事件不得到框架/模型、RAM群窗口、新消息store或原始日志。QQ/原生底层接收本身不被当成新增应用历史许可。parser投影与上述私有接线当前未实现/未验，不能以阶段2原创模块测试替代。

私有模式在正常core启动初始化广域发现、文件logger、通知、WebUI/debug动作之前分支；固定能力如下，不提供可热开启的绕过选项：

- `SNOWLUMA_HOOK_AUTOLOAD=0`；只绑定控制器预登记PID+创建时间，禁用通用账户扫描、自动注入与其他QQ监听。
- 禁止#sl及其他内置自动答复；禁通知/webhook/泛化MCP/SDK入口/自动更新。不启用通用WebUI动作测试台，保留原有不可绕过的合法初始化条件；无法分离则阻断真实模式。
- 仅一条指向既有gate的反向WS；array、reportSelfMessage=false、Universal和现有Bearer。默认HTTP3000/WS3001、其他wsClient/httpPost均关闭，不另开可直接群发的服务。
- 禁登录历史同步、引用/转发补历史、get_msg/群史/私聊史回查；内部RPC也拒绝这些请求，不能只拦外部OneBot action。引用可保留当前事件的引用ID/非展开占位，不补被引内容；无任意转发/图片回拉。
- 对准入后的当前消息，仅允许有界RAM元数据/索引。MessageStore若复用SQLite，必须真实`:memory:`；其message/media/reaction/temp/RKey及发送匹配缓存分别有界，合计默认最多512条/2MiB/300秒，发送关联128条/600秒。纯计数/ID/过期元数据也计上界；超限淘汰，不写磁盘，不下载入站媒体。无法用现有store满足时实现等价RAM适配或停在未完成，禁止磁盘回退。
- 上游message logger及原始异常栈在格式化前关闭所有file/console/ring/subscriber/debug sink；自有诊断仅封闭事件码、布尔、计数、延迟和随机实例ID，禁止正文、QQ号、群号、昵称、URL、token和任意错误字符串。子进程host同样仅转发白名单事件，其他输出丢弃，不落原始stderr。

私有适配需有上游固定tag上的实际接线证据与合成测试；只有原创模块自身测试不算“SnowLuma边界适配完成”。上游源码文件有变则构建摘要变更、旧证明失效；不能只以自报managed=true放行。

### 4.2 业务与输出不变

mentions/free、真实@、停言/恢复、一次模型尝试、工具隔离、人设、黑名单、授权群和私聊关闭全部沿用加载快照。模型profile以当前操作者设置为准，不在此计划中写死切换。没有新消息的健康检查不触发模型或群消息。

OneBot动作沿用当前gate白名单，不扩大历史/转发/媒体。群文字、已有受控表情图片、固定收藏RPC按原合同；fetch_custom_face/detail仅静态兼容，真实收藏导入不随迁移自动执行。当前未通过的视觉/成员能力保持门槛关闭。

接受非零有符号整数或十进制字符串message_id；ACK成功才提交对应文字历史/记忆。unknown/partial/timeout不重新生成、不自动重发，不清空旧账本。连接或健康代际变更时，旧请求和旧模型结果在最终输出栅栏失效；再次健康后只接新事件。

## 5. 配置、快照与生效方式

在五文件布局的runtime.yaml新增可选根节`qq_transport`；旧单文件配置同样识别。schema_version仍3，layout_version仍1，旧用户无该节时原始规范化数据和semantic_digest必须完全不变。新增`resolve_transport(settings)`在消费层给出有效默认值；只校验实际存在的节，不回写缺省字段。旧legacy_extensions中同名字段碰撞需明确报错/人工审阅，不能偷偷解释成新功能。

| 字段（qq_transport下） | 默认/限制 | 用途与生效 |
| --- | --- | --- |
| provider | napcat；枚举napcat/snowluma | 显式选择，停机保存、下次受管启动生效；没有自动fallback |
| snowluma.runtime_root | runtime/snowluma/v2.1.1 | 操作者准备的完整官方包，项目内无链接/重解析点 |
| snowluma.qq_executable | runtime/qq-snowluma/QQ.exe | 可信干净专用QQ；必须匹配本机证据 |
| snowluma.proof_file | state/qq-transport/proof.local.json | 固定版/私有JS构建/数据范围的本机证明，不是自行填true |
| snowluma.control_secret_file | secrets/snowluma-control.local.json | 独立32字节随机密钥引用；不得复用OneBot/模型凭据 |
| snowluma.control_port | 5098，1..65535 | 仅127.0.0.1，不能冲突已有端口；不提供通用动作 |
| snowluma.health_poll_seconds | 5，固定允许5..10 | 独立状态采样周期 |
| snowluma.health_ttl_seconds | 15，>=3×poll且<=30 | 证明过期即不可准入/发送 |
| snowluma.ready_timeout_seconds | 180，60..240 | 启动/恢复等待；超时关准入、转人工，不无限阻塞 |
| recovery.enabled | false | 首次真实手动验证后显式启用；不新增系统自启 |
| recovery.allow_qq_restart | false | 仅数据归属已证且连续3次受控重启免扫码后允许设true |
| recovery.down_grace_seconds | 30，固定 | 先给现有WS/管道自恢复机会 |
| recovery.drain_seconds | 150，固定 | 等待既有请求清理；cleanup未知/超时保持阻断 |
| recovery.cooldown_seconds | 1800，>=1800 | 持久冷却，进程重启不重置 |
| recovery.max_snowluma_per_24h | 2，0..2 | 24小时内最多两次Snow重启；不是每事故重试两次 |
| recovery.max_qq_per_24h | 1，0..1 | QQ重启更严格，需allow_qq_restart已证 |
| trial.sample_seconds | 60，固定 | 仅状态/资源采样，无模型/发群 |
| trial.initial_hours / total_hours | 72 / 168，固定 | 初筛包含在7天内，非额外叠加 |

recovery/trial节也在qq_transport根节内。以上路径均相对当前项目根解析；秘密位于secrets，私有代码/包位于runtime，状态位于state；禁止链接、越界、共享日常QQ或把秘密实际值放环境变量/命令行。release/tag/包摘要、私有策略版本、rx_armed要求为代码合同，不能配置绕过。

更新config示例、中文同行注释与config/README；不重写现有本机五文件或人设。提供停机的显式activate/rollback事务：锁内读取原源摘要、只改provider及本任务新增字段、原字节备份、候选整体校验、原子写入；并发源变化则拒绝，不覆盖操作者新改项。旧运行实例总按启动快照工作，改磁盘值不改变正在运行的provider/停止目标。

## 6. 独立健康证明与统一准入

在私有运行模式内实现仅回环的固定控制面，和上游OneBot good分开。GET health只读；nonce挑战、HMAC-SHA256规范化JSON，单响应<=8KiB、超时3秒。独立控制密钥只由同一受管实例读取。固定字段：schema、instance_id、transport_epoch、policy_digest、build_hash、Node/QQ的PID+创建时间、account_match布尔、phase、pipe_connected、logged_in、rx_watch_armed、receive_healthy、outbound_healthy、last_rx_age_ms、seq、nonce、mac；不包含账号/群/正文。

校验加载快照/策略/构建摘要、受管注册与实际PID创建时间、控制端监听归属、nonce/单调seq/签名/TTL。旧proof文件、旧PID、新进程复用PID、重放包、摘要变化、QQ未知、watchdog未armed均不判绿。磁盘静态“通过”记录不能替代新鲜运行证明。控制面POST只允许对预先登记同一PID的bind、drain、stop；没有任意PID/路径/命令/action/登录接口。

SnowLuma的channel_ready要求：当前受管身份有效、stop marker=false、WS连接当前代际、OneBot online=true且good=true、独立证明新鲜可信、pipe/logged_in/account_match=true且rx_watch_armed/receive_healthy/outbound_healthy=true。good缺失/未armed显示UNKNOWN并保持准入关闭。NapCat缺少新配置时完全保留原行为，不强迫其提供Snow证明。

将ready条件集中为一个helper，覆盖消息入口、free窗口/检索前、成员/视觉/收藏RPC、群发送和最终router输出，不能只改/status。健康由可用变为不可用时立刻轮换连接代际/撤销材料与成员能力；不因恢复自动复活旧消息或模型输出。读status/inspect只读且零推理，不暗中bind/重启。

## 7. 受管生命周期与有界恢复

新增provider描述层，保留现有AstrBot/gate/model组件；Snow增加qq_client和snowluma两个真实进程。2026-10-24 07:16细化：健康monitor及后续有界恢复监督作为gate拥有的任务，不另起transport_watch进程、不制造PID或重复nonce消费者；processes只统计真实进程，monitor另列任务状态。gate本身退出时准入关闭并等待人工恢复，不宣称覆盖其自动恢复；Snow/QQ进程退出仍由gate任务检测。进程注册记录PID+创建时间/启动意图，同一configuration_lock下由唯一管理writer API维护；stop marker先置位后停子进程，监督任务经同一API申请动作，不并行改registry。31B完整退出仍未证，unknown继续阻断，不借迁移解除。

1. 启动前G0/G1与离线适配证明、路径/端口/Node/摘要通过；固定auto-load=false及私有早期模式，先关准入。整个过程只创建一次自己拥有的QQ/Node；读取已存在QQ也不把它adopt。
2. 正常WS/管道断线先给30秒上游重连；期间关准入/旧代际输出。恢复则记录一次短暂中断，不另重启。
3. 未恢复且recovery已显式启用，先drain最多150秒；模型或cleanup未知、活动发送未决则不杀、不重试，转operator_required。现有unknown/partial账本保持。
4. 每事故至多一个恢复动作：Node退出/管道断而QQ身份健康可尝试重启Snow并重绑原受管QQ；已armed接收停滞且管道仍在，只有allow_qq_restart及3/3免扫码证明有效时才可重启该QQ，否则至多一次Snow动作后转人工。禁止“Snow→QQ→重登”的升级重试循环。
5. 动作前write-ahead预占持久预算，失败/结果未知也消耗；24小时滑动窗Snow<=2、QQ<=1，动作间至少1800秒。QQ动作同时创建Node，单次事故动作同时占Snow/QQ两个资源预算，不能额外产生第三次Node创建。账本损坏/时钟回拨不能补额度或清空。watch自身重启不重置预算。
6. 完成动作后180秒等待独立健康/armed；从30秒确认到drain/ready上限合计360秒。失败则停止自动动作、保持gate关闭，记录waiting_operator/原因类别。需扫码时等待人工，不保存密码、不反复快速登录。
7. 手动stop、shutdown、rollback优先，停机标志使所有watch/延迟回调失效，确认自有注册身份退出。管理端退出不丢子进程归属；无证据进程只报告，不按QQ.exe/Node/Python名称批量结束。未收敛身份不得报告停止成功或启动另一provider。

4B按两个可审检查点推进。4B1先实现原锁下持久预算和gate监督状态机，4B2再实现操作CLI、有限配置事务和采样。监督只消费现有monitor的身份/健康结果，不另建nonce消费者；恢复动作通过唯一writer API，在锁内核对停止标志、实例、旧登记与动作意图并预占预算，网络等待移出锁。重新创建后登记新的PID/创建时间与transport_epoch，旧proof/旧连接/旧结果全部失效；同实例换binding只能由该已核验的writer事务执行，普通控制客户端不能自行清零序列或换owner。

预算账本跨管理进程、gate及bot实例保留。初始化必须是明确的首次停机准备动作，曾准备过而账本丢失/损坏不得由watch补成空账；时间回拨、预占或落盘失败、执行结果未知均不能释放额度。持久保存事故是否已动作，watch重启不能把同一事故当作新事故再试。短暂恢复后又掉线可记录新事故，但冷却和24小时预算仍生效。QQ重启的3/3原生数据与免扫码资格目前没有真实证明，生产分支继续拒绝；自造资格只能通过测试依赖注入，不能增加可写true的配置绕过。

自动恢复的drain与人工stop分别遵循既有合同：前者必须证明模型/cleanup及发送均已收敛，未知或150秒到期转人工且不kill；人工stop先置marker，沿既有有界中止和unknown留账执行。状态机至少区分观察、grace、drain、动作已预占、等待就绪和operator_required，回调每次执行前重查stop/实例。不得只交未接调用点的预算helper；用假进程/时钟穿过gate-owned监督、管理writer、重绑定和最终输出失效路径。原生与私有入口资格仍总拒，不为测试解除生产门槛。

不是定时重启，不因内存小幅变化杀进程，不向群发恢复提示，不启动Windows Startup。默认recovery=false时仍能报告健康并阻止坏链路继续入站/输出，恢复由显式管理动作完成。

## 8. 操作入口与预计文件

新增`scripts/transport.py`，复用项目已有配置/锁/生命周期，不增加第三方安装器：

| 命令 | 行为 |
| --- | --- |
| inspect --json | 默认只读本机状态和静态前置；缺少材料给封闭reason，不探测登录/模型 |
| prepare-policy | 停机后只创建本项目原创策略/随机控制密钥/候选清单；不下载、安装、搬运原生组件 |
| verify --offline | 校验策略/源码接线/固定摘要证据，运行自造夹具；缺原生包不造假通过 |
| capability-probe --authorize-owned-qq --timeout 240 | 仅G0已满足后的单次受管QQ探针；全入站DROP、无模型/发群，需人工扫码就waiting_operator |
| activate --provider snowluma | 所有前置通过且停机后，有限字段事务；本命令不自动登录/启动 |
| trial-start | 所有前置通过、旧实例已停止后启动一次已选择provider，附带有界采样；不发送测试群消息 |
| trial-status --json | 只读连续段、未知/中断/恢复/资源计数；不将安静群当故障 |
| rollback | 显式停止试验/核验归属，恢复本任务字段；不自动启动NapCat，不抹旧账本 |

预计新增：`src/qqbot_gateway/qq_transport.py`（provider/有效配置/本机proof）、`transport_health.py`、`transport_supervisor.py`、`transport_trial.py`，`scripts/transport.py`，原创`adapters/snowluma/project_policy.mjs`及README；必要的自造单元/框架/JS测试与`reports/lap-40-*.md`。

预计修改：`scripts/manage.py`、`scripts/process_host.py`、`src/qqbot_gateway/{config.py,config_files.py,config_comments.py,config_layout_ops.py,onebot_gate.py}`、`plugins/qq_router/main.py`中最终ready连接；`config/settings.example.yaml`、`config/examples/runtime.yaml`、`config/README.md`、根README及6份任务入口/规划文档。只有必要时改reply_delivery/lifecycle以复用代际，不能顺手重构旧模型/人设/媒体能力。现有.gitignore已覆盖runtime/state/secrets/logs/local，不反向取消忽略。

私有接线预计涉及固定上游core/index、bridge manager/HookManager/session观测、OneBot event pipeline/instance/message-actions/store/logger；这些文件只在私有忽略区，不能作为public提交。实施方核对实际符号后可选更小的原创独立入口，但同样需要全部前置合同；不能只写一个无真实调用点的策略模块就宣称完成。

## 9. 分阶段实施与停止条件

根agent每阶段只派一个sol medium实施子任务，接收结果后复核差异、测试与能力缺口，再下发下一阶段；不并行写同文件。用户已授权此执行方式，不再把完成规划当结束点。

1. **阶段1：静态准入和配置/provider。** 领取实施session，建立隔离worktree，保存基线；实现有效配置/旧快照兼容、provider描述、inspect和固定本机证据结构，补模板。缺官方包不妨碍完成。不得改真实local或启停。
2. **阶段2：原创策略及健康/准入。** 完成严格早期policy、RAM/无历史/无原始日志的可调用接口和测试；健康签名/身份/代际集中于gate。以虚拟transport跑真实项目入口和最终输出栅栏。不启动真实QQ/Snow/模型。
3. **阶段3：私有Snow接线核验。** 在忽略区只准备许可允许的源码/JS修改和固定版接线测试；核对是否有操作者准备的官方包与原生部署许可条件。无包或保护不允许私有构建，完成可做源码接线核对与报告，标记真实适配未验，不能补一个伪造manifest。此缺口不阻止下一阶段离线部分。
4. **阶段4：生命周期/恢复/试验账本。** 拆为4A身份/健康管理接线（provider-aware管理、唯一writer注册/锁、加载快照、受管PID与固定监听、独立秘密/nonce轮询、原创固定控制面、stop优先、缺真实前置硬拒启）和4B持久预算/有界恢复/CLI事务/资源采样，根agent分别复核再派下一步。健康/恢复由gate拥有的任务负责，物理组件不含虚构watch PID。控制命令序列须跨gate bind与管理drain/stop使用原锁下同一持久预占分配，不能每个客户端从1重置；锁等待不得阻塞gate事件循环或与管理等端口形成死锁。全部先用假进程/假时钟/假端口/假transport测试。不使用真实组件作离线fixture；上游观测接线未做时真实监听/QQ仍不通过，不能伪造资格来跑管理路径。
5. **阶段5：独立集成复核和Git交付。** 受影响回归、原NapCat缺省行为/快照兼容、隐私/旁路扫描、文档/README/任务证据；commit/push并核对远端SHA。若阶段3或G1缺口存在，这一步交付明确“已实现/离线通过、未部署”，不空等或宣称替换完成。
6. **阶段6：受控真实切换。** 只有G0/G1、私有接线、固定构建、干净QQ/数据范围均可证，且无需睡眠中的操作者扫码/确认，才允许按已授权试运行完成一次停止旧实例→activate→单次启动。若条件缺失，保留原运行状态，结束于具体waiting_operator清单。无人工测试消息授权则不自行群发；观察自然新消息亦必须经现有合同。
7. **阶段7：长期资格。** 成功真实启动后由本地采样记录72小时及7天，不让agent空转等待7天，不凭短时结果打长期通过。无用户新要求不创建主动群任务或监控通知automation；额度等待是用户另行明确授权的例外，见第13节。

## 10. 验证与验收

离线证据必须是真实执行，不能把源码存在或测试文件写完当通过。至少覆盖：

- schema1/2/3、五文件/legacy单文件、已有snapshot原始/语义摘要；无qq_transport时规范化对象/semantic_digest/默认NapCat行为不变；新字段非法值/冲突/路径重解析/并发源修改拒绝。
- 私聊/未授权/黑名单/self/畸形消息在任何store/log/backfill/模型callback前被拒绝；含引用/转发仍零历史请求；授权当前新事件可穿过实际gate，#sl不能旁路答复。固定action白名单与关闭的媒体/成员/视觉继续拒绝。
- Bearer/X-Self-ID/Universal/array、self echo/去重、真实@/free/停言/最终栅栏；整数/字符串ACK、unknown/partial、迟到回执；断线/健康失效后的旧模型结果永不发送/学习。
- good=false而online=true、从未armed、过期/伪签/重放/乱序proof、PID复用、监听归属不符、policy/build变化、stop marker冲突均fail closed；NapCat分支不被强迫提供Snow健康。
- 有界缓存真实RAM连接、零消息DB/原始日志、禁历史RPC；超限/TTL/异常路径亦无磁盘回退。测试用自造消息，不带真实QQ号/群内容/凭据。
- 假进程退出/管道断、QQ心跳停滞、一次动作、预算预占/持久化失败/重启/时钟回拨、cooldown、drain未知、stop与watch竞态；不执行真实杀进程/睡眠多分钟/端口启动/模型调用。所有资源采样也用固定fixture验证上界。
- 运行受影响的config/config_files/config_comments/lifecycle/process_host/onebot_gate/participation/group_silence/reply_delivery等单元及实际AstrBot框架替身测试。纯JS模块可用本机Node的node:test，不能因此声称Snow运行时版本合格。以现有测试命令为准，不盲跑含真实服务测试。

已知基线：LAP-24 PersonaMatrix旧8192字节断言与当前23393字节人设不符，上一轮1失败/25通过；不得改人设/预算以让本任务变绿。若复现单列原失败，其余新增失败必须处理或明确真实缺口。不要扩大到无关功能或以全量重跑代替有意义验证。

真实验收另记录：固定QQ/Node/Snow/build/config/策略/原生数据证据；首次armed；实际新消息准入和ACK；短断网/WS/管道重连与一次受管重启。恢复证明先在全链暂停/无模型/无发送下做；3次QQ免扫码测试要独立授权的可用人工窗口，缺少它就保持allow_qq_restart=false，不因此阻止只启用Snow有限恢复的试验。

## 11. 72小时和7天长稳资格

从第一次真实channel_ready开始一个连续段；前72小时为初筛，包含在168小时中。QQ/Node/固定构建/策略/关键配置变化或重新扫码产生新段，旧失败/未知记录保留；有计划故障注入单独标记，不伪装自然故障消失。

每60秒采样受管进程RSS/句柄、接收健康/armed/pipe/online/good、重启/人工介入/ACK计数与延迟、项目日志和数据目录总字节。每条<=512字节，最多16MiB/保留14天，轮换有界；不读消息正文或登录数据库，外部原生文件只取已允许范围的元数据。覆盖缺口记UNKNOWN，安静群不记失败；只见进程或good未armed不计独立健康覆盖。

7天转正要求：无越权输出/黑名单历史泄漏、无无证据重发、无未恢复假活、无非计划反复扫码；中断按合同有界恢复，所有失败和人工恢复如实纳入；自然新消息有完整准入/ACK对照。长期无真实新消息则只能判传输观测通过，不能判实际收发7天通过。不存在“永不掉线”的承诺。

资源以预热后同等负载趋势复核；例如连续8个小时中位RSS增长超过预热基线50%且>=256MiB、句柄增长25%且>=256时提出调查，不借自动重启抹趋势。源码自身缓存上界也要验。健康检查不消耗模型额度；正式试运行的自然群触发仍沿用用户当前模型，不能声称整个7天零模型消耗。

## 12. 分支、兼容迁移和回滚

规划先提交推送`codex/lap-40-snowluma-trial`，核对远端SHA。实施优先使用此分支精确规划提交创建的受管worktree，建议实施分支`codex/lap-40-snowluma-impl`；先list_artifacts复用适合的worktree。不复制runtime/secrets/state/local、人设私改或认证到worktree。无现成依赖时使用已知Python解释器/源码只读依赖或项目局部安装，不能启动真实bot作为测试依赖。

根agent拥有PROGRESS/工作线HANDOFF/TASKS的写入，medium独占其当前阶段代码/测试/任务报告；子任务交接时列文件。阶段串行，提交只包含任务归属检查过的文件。public Git保持私有源码/patch/bundle/native、账号/本机配置/原始消息排除。每个可审阅阶段可commit/push，远端核对SHA；不强推、不合并main、不重写他人提交。真实切换前才把已审实现交付到目标运行checkout，必须停机、干净且只允许快进，不能把运行中插件热加载当部署。

回滚为显式操作：先停Snow试验并确认owned进程退出、stop marker保持、未决发送账本保留；恢复本任务有限provider字段/原始备份，若操作者后来修改同字段则拒绝自动覆写；不删除QQ登录数据、模型历史、记忆或未知结果。此后由操作者显式启动NapCat，不能双开同账号或自动fallback。NapCat原有长期问题仍保留，不标已根治。

## 13. 配额等待与持续交接

用户补充授权：无论规划或medium实施，**5小时窗口剩余<=5%时停止继续消耗，等北京时间2026-10-24 07:10后继续**。检查使用account usage tool的300分钟窗口，remaining=100-usedPercent；缺失值为未知，不当0或100。当前2026-10-24 01:50检查剩余98%，尚未触发等待。

根agent在阶段交接及较长工作步骤之间检查；medium在领取、阶段提交前及约15分钟检查，接近阈值更频繁。阈值触发时保存最小HANDOFF/未完成清单、提交已审可交付内容，停止新模型工作并通知根agent；不自行花费reset credit或购买额度。根agent通过Codex heartbeat工具安排本线程北京时间07:10恢复，并在提示中先检查配额/任务归属再继续，不重复已有步骤；不使用连续sleep或循环轮询耗到早晨。若已过07:10，先核对可用额度，不无限按已过期时间重试。未到阈值则正常逐步实施，不为等待而提前停工。

## 14. 未验证项与改变方案的出口

目前未验证：原生组件预备/部署条件；私有JS模式是否被完整性保护允许；干净QQ原生数据隔离；真实QQ版本能否观测armed；真实WS/收发/表情/收藏ACK；3/3免扫码；Snow/QQ进程完整回收；72h/7天资源与会话。上游版本更新不自动解决这些缺口。

若某项不成立，medium先完成不依赖它的阶段并记录“证据、失败类别、已做部分、未做部分、最小所需人工/上游能力”，根agent回到此计划做有证据的小范围修订。不得换成未经计划的新后端/云服务/自动登录，不关闭黑名单/历史/输出/身份门槛。最终报告必须区分“集成代码可审阅”与“bot已经换成SnowLuma”，不把文件存在和等待状态报成迁移成功。
