# LAP-40 / 3R-B：资格与单次DROP探针精确合同

返回[项目入口](../../../../PROGRESS.md) / [任务交接](HANDOFF.md) / [续作计划](STAGE3_CONTINUATION_PLAN.md) / [总计划](PLAN.md)。2026-10-24，Asia/Shanghai；`LAP-40-max-realentry-next`。本文件是A1实施期间独立细化的B规划，**尚未实施，不授予真实启动资格**；实际B领取须等待A1/A2根审。

## 目的和不可改变的边界

解决现有capability-probe直接调用生产总拒、无法收集自身所需证据的问题。生产资格不能依靠自填布尔/匹配几个文件hash；仍由完整受审私有构建、G0/G1执行证据及当前实时owner/health逐层判定。旧1/2/4/5不重做，旧NapCat/快照/配置事务兼容；账号/群/黑名单/模型/额度/恢复默认值不变。

当前Windows原生数据机制未证。不能为了让以下合同有成功路径而猜参数、修改共享UserDataInfo.ini/HOME/APPDATA/日常QQ或创建系统用户/VM。实现可以用独立测试依赖验证成功分支；生产支持表没有已证机制时必须拒绝真实probe和启动。未写代码与缺真实机制分别诊断。

## 三层入口及调用顺序

| 入口 | 必须成立 | 可以产生的副作用 | 不依赖 |
| --- | --- | --- | --- |
| 材料/资格inspect | 只读限定路径，严格格式/大小/摘要/来源/支持表 | 无端口/进程/秘密读取/配置写入 | provider激活、QQ在线、probe成功 |
| `require_probe_candidate` | G0原件/接受/原位置native；已根审的完整私有构建与合成；可信干净QQ候选；已审Windows数据机制与限定元数据观察器；明确本次人工授权/唯一执行归属；停机和无未决身份 | 只准一次DROP probe计划；尚未创建任何进程 | probe自己的结果、生产资格、已登录/armed、provider=snowluma |
| `require_runtime` | 固定完整构建受审profile、严格G0/G1/probe记录语义、原件/私有产物/QQ/配置仍匹配；未决/stop/预算条件正常 | 只允许准入关闭的受管正常启动，随后独立实时owner/health才准入 | 旧probe的PID继续存活、旧health或某个ready=true字段 |

`activate`仍停机有限字段事务，先完整`require_runtime`再写候选provider；`trial-start`仍明确single-shot。`capability-probe --authorize-owned-qq --timeout 1..240`改用probe前置层，不调用生产资格、不启用正常forward。无明确本次probe授权，仅执行inspect/离线验证；条款接受/解压确认不被当作probe授权。

## 可信构建profile和本机材料（待实现schema）

新增公开原创代码中的固定profile表，初始为空。只有A1/A2实际私有源/完整产物/执行证据经根审，才在专属Git检查点登记精确profile摘要；public仅摘要/版本/封闭能力，不含修改源或patch。不能从local配置动态添加profile，不接受`approved/valid/managed=true`；不能从操作者自填manifest派生一个“已审”profile。

profile固定字段为`profile_id/upstream_commit/builder_version/input_inventory_sha256/output_inventory_sha256/synthetic_report_sha256/policy_version/control_version`。上述值由实际文件/构建/执行证据计算，profile_id为本项目代码固定枚举，commit固定f8cb15c；输入/输出inventory均是规范JSON的相对路径、字节数与SHA256精确集合。private entry、所有JS依赖/资源、构建配置/锁、原创policy/control及使用的转换器必须纳入，禁任意额外运行import/插件/测试依赖。生产逐文件检查完整集合及目录/符号链接边界，不仅验证入口文件；任一变化均失效。

忽略`state/qq-transport/qualification-candidate.local.json`格式`qqbot-snowluma-candidate-v1`，精确键为下表。既有`candidate.local.json`属于4B2的prepare/activate停机事务（qqbot-candidate-v1），保留其格式/来源冻结/未决语义，不覆写或静默升级；B的新资格材料引用独立，不能替代原事务校验。

| 键 | 必须验证的语义 |
| --- | --- |
| `format/profile_id/release/tag_sha` | 固定格式/已审profile/2.1.1/f8cb15c，无额外键 |
| `bundle` | 相对runtime内的固定ZIP路径/42,694,125字节/固定SHA256；Downloads核验作为材料报告，不放宽现有运行路径边界 |
| `official_inventory` | 固定原包71成员的inventory引用和摘要，逐项校验原位置；额外保留的原ZIP单列，无原版文件覆盖 |
| `acceptance` | 两原文精确SHA256、明确本会话操作者已接受的受限记录引用；缺失/单份/旧原文拒绝。不生成官方consent.json，不代表书面扩展部署许可 |
| `native_deployment` | 仅`operator_prepared_original_bundle`或已另外根审的范围匹配书面授权引用；不能靠一段声明自动复制/安装组件 |
| `clean_qq` | 由原始腾讯安装包/可信专用入口来源证据派生；安装包与exe的各自hash/签名/安装或提取来源分开。某exe文件存在/文件版本不能单独证明干净 |
| `data_mechanism` | 生产已审机制枚举、可信出处摘要、固定候选启动参数/数据允许根和观察器版本引用；源码/文档解释与实际元数据probe两者都需成立 |
| `configuration` | `base_source_digest/qualification_effective_digest`及本次候选引用；前者冻结材料/probe时原源，后者对当前完整resolved配置仅将provider规范化为snowluma后，使用现有canonical/hash算法计算。账号/群/黑名单/模型/其他传输参数不省略，不记录原始凭据 |

引用只能指state/qq-transport内有界严格JSON，runtime文件只能runtime白名单，秘密只能既有secrets约束；候选不引入任意命令/绝对外部路径/PID或code对象。采用现有重复键拒绝/文件上限/checked_path/非symlink规则。准确JSON子结构在B实现前以该表字段落验证器及测试，不得临时接受未知键；任一无法确定的来源维持unverified。

provider规范化仅解决“probe发生在napcat源、activate只改provider后资格就失效”的循环。base_source_digest仅用于prepare/probe冻结，后续activate继续核对原事务的预期before/after源摘要及有限归属字段；实际运行资格重新计算qualification_effective_digest，不能借规范化忽略任何其他配置变化，也不能授权热切换。修改安装根/QQ数据根/profile或相关输入均需新证据，不把worktree内原件/固定路径资格自动搬到旧E运行目录。

## 单次probe状态机和证据

管理器持原configuration_lock/OwnerWriter租约核对停机、marker、未决任务/身份和候选，写前置意图/随机run_id后释放网络等待所需锁；失败/退出未知不能删除意图重试。只创建本次受管QQ与私有Node，不adopt旧QQ、不做全局进程/登录数据发现。probe mode为固定启动枚举，必须在最早原生入口DROP全部消息，绝不调用AstrBot、模型、发送RPC、正常反向WS、内置答复或历史；健康心跳只作封闭观测。

状态固定`prepared → creating → observing → stopping → complete`；另有终态`waiting_operator/failed/unknown`。总deadline最多240秒，从任何进程创建前开始，必须包含退出回收；应预留停止时间，不能先等240秒再无限清理。取消/stop优先，不重登/重启/重试注入。需要扫码由操作者在本次窗口操作，超时不再创建；probe不会自动读取密码或日常QQ会话。

忽略`probe-results/<run_id>.json`格式`qqbot-snowluma-probe-result-v1`，只由实际probe执行器write-ahead/原子追加终态生成。固定键：`format/run_id/candidate_sha256/profile_id/collector_version/started_ms/deadline_ms/finished_ms/phase/created_identities/component_observations/data_observations/side_effect_counts/exit_observations/failure_code`。原始观测只保留指定PID及受管子进程exe/创建时间/父子关系、固定模块路径/摘要、允许范围文件访问元数据，完整细节留忽略证据；CLI不打印账号/路径/任意异常。

执行器实际核对候选固定组件和创建时间，观测pipe/login/account_match/armed/rx/outbound，各布尔须有实际受管观测源，不把无事件初始good当armed。数据观察器必须具有本次完整覆盖/失效/丢事件的判据；只看到一份句柄或“未发现越界”不能证明范围。观察器缺失、不支持或丢事件均unverified，不从安静群/无文件访问推定成功。

生产只接受执行器核验过的complete结果：run唯一、时钟有序且未回拨、candidate/profile/组件/协议/配置及观察器机制匹配、所有必需G0/G1/保护初始化/退出语义成立，所有禁用side_effect计数0；`complete`字符串本身不是通过条件。无真实消息时不要求群发送/模型计数大于0；probe严格0模型/0发送，不能把它称正常收发验收。旧probe PID不被复用为正常运行身份，正常启动重新创建/登记并获得新health。

## 错误、兼容和验证出口

CLI新增封闭错误类按层输出：`candidate_missing/candidate_invalid/unreviewed_private_build/operator_acceptance_missing/native_provenance_unverified/clean_qq_unverified/data_mechanism_unverified/observer_unavailable/probe_authorization_required/probe_already_attempted/probe_waiting_operator/probe_deadline/probe_observation_unverified/probe_exit_unknown/probe_result_invalid/probe_evidence_stale`。不得泄漏原始路径、QQ号、任意错误/堆栈；沿用channel_ready=false。旧static-proof-v1只保留原静态功能，不能升级为新生产证据，不能清旧pending/unknown/预算或quiet地迁移配置。

B验证用temp/fake collector/进程/时钟/FS/network，覆盖缺每项前置创建数0、双启动/并发锁/意图、缺同意、profile/hash/import变化、旧证据/未知键/重复键、PID复用/账号变更、DROP早于所有sink、超时包含回收、操作员缺席、停止优先、丢观测与unknown不重试，正常停机事务/旧NapCat兼容。测试依赖只能显式注入，生产支持表为空时真实命令仍拒绝。之后根审具体实现/源码与fake执行结果；仍不执行C，不以资格代码完成代替真实证据。

回滚为保留原运行provider/配置和失败证据，只撤销本次候选/资格引用，不清空实际创建或退出未知记录。真正允许C前需先解决Windows数据机制和唯一停机/人工窗口，另写可恢复检查点；72h/7天从后续第一次真实channel_ready计，本probe不计时。
