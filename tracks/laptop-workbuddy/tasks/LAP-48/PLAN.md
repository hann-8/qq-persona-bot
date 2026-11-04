# LAP-48 最终设计：QQ号整块记忆、联网薄适配与历史人设

返回 [PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)，继承 [AGENTS](../../../../AGENTS.md)。[REVIEW](REVIEW.md) 为简练评审，[MEDIUM_START](MEDIUM_START.md) 为手动实施入口，状态见 [HANDOFF](HANDOFF.md)。

状态：planned / ready_for_medium，2026-11-04（Asia/Shanghai）。用户要求本次修订完成直接提供指令，由其手动交medium；本轮仅文档和非运行人设备稿，不自动实施。首稿mN/rN、逐条编辑、439字候选及严格历史/步骤限制由本稿替代。

## 1. 范围与完成标准

在现有Planner→Replyer一次完成：
1. QQ号唯一标识QQ群友，name展示；记忆为无编号数组，按成员/本群整块更新，不另建精确删除某一条的接口。
2. 全群全文仍交Planner，模型自主增改删/整理/遗忘，程序保证可靠保存和实际结果；不恢复关键词、候选或小注入限额。
3. 联网复用官方工具和公开事件，去掉第二份计划、完整历史重演、阶段齐全及固定10步等额外拒绝；单页或预算提示交模型处理。
4. 保存成功或无变化不改变自然回复；明确要求记忆但失败才反馈。
5. 两阶段使用ff2e348删第十三节的完整人设，Replyer通用风格限制不覆盖它。

不新增模型/账号/后端/收费API、业务阶段、整项自动重试、并行任务或无新消息的主动发言。当前模型/low/额度来源、Planner思考开和Replyer关、触发/权限/表情/识图保持。独立E:/CodexWS/WeChatbot不在范围。

本根WX-Akasha共用MemoryStore，已显式配对的微信成员关联同QQ号；未配对微信身份保留wechat:前缀的平台ID，不冒充QQ号、不猜配对或共享namespace。

## 2. 当前证据及边界

| 来源 | 已确认事实 |
| --- | --- |
| [group_memory.py](../../../../src/qqbot_gateway/group_memory.py) TOP/prepare/POLICY/_write | schema2平铺随机记录键，正文重复长成员标记；模型还收generation/base_revision/actors，磁盘单行。元数据有宿主保存用途，不是模型记忆内容 |
| 首次结构采样 | 当时3文件44条，记录键1,408、正文成员标记2,376个ASCII字符；这是历史采样，不得覆盖运行中自然更新或用户后续配置 |
| 本次只读QQ关联核对 | 用本机已有数字候选与旧算法匹配，仅输出计数；一个群5/5，另一群2/3，有实际暂未关联成员。HMAC不能反推，不能声称全部已有QQ |
| [dialogue.py](../../../../src/qqbot_gateway/dialogue.py)、[runner](../../../../src/qqbot_gateway/workbuddy_cli_runner.py) | 当前120秒共享，表达预留30、每阶段清理5，Planner约85秒；实际provider source timeout=180 |
| [config.py](../../../../src/qqbot_gateway/config.py)、[configure_astrbot.py](../../../../scripts/configure_astrbot.py) | queue_wait＋run_timeout＋25固定不得超180；旧Python web.timeout_seconds=15不是原生CLI整项期限 |
| 忽略日志/投递台账 | 19:27:03天气问题，19:27:12 CLI trace 7c84eda6a5：BACKEND_UNAVAILABLE、initialized=true、2 calls/2 results，先tool_plan_missing后native_ready。首个失败说明已发送；19:27:17新消息触发不同任务，19:27:39发送天气答案 |
| [register.ts](../../../../adapters/codebuddy_vision_guard/hooks/register.ts)与锁定CLI dispatchModsToolCall | 已有真实tool.call，还要另找planned/session快照计划；缺失就拒绝并令后续native_ready失败。现有摘要不足以判定具体流式/并行/内嵌时序，不声称原始竞态已复现 |
| receipt_plan / [router](../../../../plugins/qq_router/main.py) | 宿主可追加保存/无变更固定句并截正文、改kind，需要取消成功收尾的这种改写 |
| [persona.py](../../../../src/qqbot_gateway/persona.py)、dialogue.replyer_system | 两阶段人设均已接线。用户反馈拆分更拟人但角色变淡；指定版本已提取，备稿8,896字符/17,575字节 |

不把实际QQ号、私密事实、原始消息、配置、密钥或CLI捕获写入Git。不把此样例扩大为全部联网失败的唯一原因。已有bot自然写入和用户本机改动必须保留。

## 3. schema3：一个文件，按QQ号整块整理

### 3.1 磁盘与模型视图

沿用state/group-memory/<现有namespace>/memory.json和key，不搬群目录。顶层schema_version=3、group、members、unassigned、_meta；磁盘UTF-8中文原文、两空格缩进和末尾换行，仍用现有锁/临时文件/fsync/replace，不新增双文件同步。

- group为可读字符串数组，没有段落ID。
- members为QQ号字符串→{name:显示名,memory:字符串数组}。不用mN；QQ改名只刷新name，同名不同QQ分开。名字未知可空，不为找名字卡住使用。
- unassigned为暂不能关联QQ的旧内容数组；明确历史身份未确定，不造QQ号。
- _meta集中保留namespace_hmac、generation、revision、last_request_key和必要legacy_links。没有next_record_id、next_member_id、rN索引或每段内容hash；不为正常QQ成员再造随机身份。

name/当前身份来自source.messages与identities；不按昵称相似度合并账号。模型可记当前明确提供QQ的被提及者，但不能把昵称猜成QQ。记忆里的身份不授予管理员、真实@或运维权。明确微信配对沿用，其余微信ID带wechat:前缀，隔群合同保持。

多人关系/约定可放group一份，正文用姓名与必要QQ号说明，不强制固定栏目。保持可配置50,000正文Unicode字符、单文件1MiB、总8MiB及当前输入政策；正文计语义字符，结构、身份和缩进计实际字节。

模型收到group/members/unassigned全文及actors:{当前p_ref:QQ号或既有微信身份}，不收_meta/版本/请求键/程序生成长HMAC；磁盘缩进不进入模型。QQ号用于记忆是用户明确选择，不顺手把它们或群记忆加进搜索查询。Replyer仍只收必要事实，不重复全量记忆。

### 3.2 更新合同

沿用memory_updates，改为选择性整块替换：

~~~json
{
  "memory_updates": {
    "members": {
      "123456789": [
        "希望被叫小青。",
        "以前喜欢甜饮，最近改喝清茶。"
      ]
    },
    "group": ["联机改到周六晚上。"]
  },
  "memory_receipt": false
}
~~~

块/成员未出现即不改，出现则以完整数组替换；空数组清空该块，空对象无变化。unassigned同样整块替换。不保留new_1、r2、逐条null删除、下标编辑，不能用另一套每段指纹恢复逐条定位。模型想忘记某句话时，回写数组时不再包含它，程序不需要识别该句话。

成员名沿用真实已知name，新QQ未知名字可空，更新对象只提交memory数组；不为它增加改账号能力。仅回写变化成员，不重抄整群；整块整理日常即可使用，不限于容量满时。

全量source_digest/context保持绑定；宿主版本和last_request去重保留，防止旧快照覆盖新保存。valid_memory、auxiliary、validate_updates、提示和manifest适配整块结构；v2若保留fact_refs则置空，不暗造逐记录引用。内部manifest仍可用完整投影核对，不把保存元数据回塞模型。

本机manage/export按成员/群整块查看、替换、清空；去掉当前记录ID菜单，不扩建旧ID映射。保留全群清空、按成员清空和导出；迁移能读旧ID，但不写进新数据/协议。

### 3.3 重复判断

保存本次提交数组时，可在同一块内对首尾空白归一后完全相同文字保留首项，顺序不变；不跨成员去重，不把时间、数字或不确定程度不同的文本当相同。未提交块不额外扫描。

语义相近由现有Planner看全文自主合并；提示避免反复新增同一事实、保留变化与时间背景。没有额外模型调用、向量库、相似度门槛、后台清理任务或百分之百准确保证；非上线前置。

### 3.4 迁移与待关联内容

在受管空闲停止点备份当时实际记忆、key、必要配置/技术配对，再转换同路径。schema1沿既有归一化接入，schema2去掉随机记录键、转为文本数组；不用模型，不做语义压缩。初次迁移保留历史事实，完全重复折叠仅针对本次正常整块提交。

旧HMAC只能用已知QQ候选按原算法验证。来源是已有本机真实身份/日志/缓存、授权配置和明确微信配对；仅进程内比较，不输出QQ、正文或密钥，不暴力枚举，不联网查账号，不新增群成员采集或要求先人工补表。

可关联actor归该QQ；涉及多人放group，身份引用换成已知QQ/名字；保留事实、时间和不确定性。无法关联的原内容进入unassigned，投影把长标记表达为“历史群友（QQ待关联）”；_meta.legacy_links只留旧actor与待关联文本来源。以后真实身份匹配、对应待关联文本仍在时再归入QQ。已被模型改写/删除的内容不能按旧备份复活；无法确定改写归属时继续留未关联区。

这是已存在缺口的轻量保留分支，不建匹配服务/评分/审批，不阻塞其它群部署。退役群/未知旧文件保留，不扩大访问名单或删除它们；记录实际转换范围。内存构建并检查全文转换/群归属/容量后原子替换，失败不覆盖原件，重跑不重复迁移。原件在忽略部署目录，不提交、不重复当记忆注入。

## 4. 联网薄适配：删除重复门槛

### 4.1 采用官方执行事件

复用锁定CLI WebSearch/WebFetch、tool.call及next(e)，argsOf仅归一化官方封套。不自建搜索、不升级/修改CLI、不开放其它工具/MCP。

删除而非再补竞态等待：
- native.planned/pendingStep和从session补找同一份计划的执行前提。
- 逐步完整重演assistant/tool历史、固定消息类型、prefix完全相同、调用/结果数量必须立即齐全。
- 阶段必须按固定顺序出现才能继续，以及普通工具失败毒化native.failed→native_ready的联锁。
- 原生联网固定10步上限及按内嵌处理的步骤/turn形态拒绝。

官方事件提供工具名、执行ID和输入，足够做薄适配。保留两工具范围、同一执行ID不重复执行、真实输入容量与原初始wire/图片接线。实际回执如实表示当前检查内容，不为保持旧布尔字段偷偷保留第二计划或完整历史证明；旧证明不伪改，新技术配对走现机制。

资源管理不变成层叠失败：
- 8次真正工具执行保留为可调预算。耗尽给模型普通工具提示，让它尽量用已有材料收尾；第9次意图不当越权。parser/guard按实际执行协调统计，预算提示不再次触发隔离失败。
- cli_max_turns兼容保留但对原生联网忽略，health/说明不再宣称硬执行10步，实际步骤可观察计数。
- 当前单结果65,536/总262,144字节和真实输入窗口沿用；长内容按现有逻辑截取，容量不足给普通工具结果供收尾。
- 网站、重定向、参数或单页读取错误交模型按官方能力处理，计真实执行预算，不抹掉已有材料，不自动重跑整项任务。
- 不新增域名评分、来源凑数、质量门槛、数字/token/secret内容词表、来源尾巴或审查模型。公开网页用途/工具范围沿用。

实现优先删除简化现有多余逻辑，不为了减少防御又搭一套新框架。真实总deadline到达仍停止本项，受管清理不变。

### 4.2 时间和加载

| 项目 | 最终值/行为 |
| --- | --- |
| 所选CodeBuddy run_timeout_seconds | 默认及本机120→180秒，Ollama原profile不顺带改 |
| 两阶段 | 同一180秒单调deadline，Replyer预留30，现有每阶段清理5在deadline内；Planner约145秒，提前结束的剩余时间可交Replyer |
| provider timeout | 所选queue_wait＋run_timeout＋25，当前235秒，替换固定180校验/注释和实际接线 |
| 原生工具 | 执行预算8，固定10步停用；当前结果/输入字节保持，旧Python的15秒不是CLI整项期限 |

统一推导用于验证/展示和实际provider_sources，不能只改不再持有timeout的provider条目；正常受管启动加载，唯一业务配置入口仍config/local。正常工作不先发失败提示，确凿连接/账号故障立即说明。超时/取消复用原清理，一项任务只完成一次；后续聊天自然承接不新增限制。

### 4.3 错误与诊断

MODEL_TIMEOUT、AUTH_REQUIRED、QUOTA_EXHAUSTED、RATE_LIMITED、BACKEND_UNAVAILABLE保原含义。普通工具错误不升级为整项后端不可用。真实本地web适配故障用WEB_ADAPTER_ERROR：“这次联网过程出错，没能完成查询。”，只据同请求真实异常/回执分类，不猜内容。

现有failure_summary按需补phase、elapsed_ms、实际期限/工具执行数量/受控原因；不新增常驻原始消息、查询、网页日志或proof流水线。受影响零生成接线一轮即可，不把新日志采样、真实搜索、历史大验收当上线前提。

## 5. 保存成功静默

receipt_plan对saved/unchanged直接返原plan，不追加句、不截正文、不改kind/气泡/表情/@。内部MEMORY_SAVE、memory-last-save和实际revision保留。

memory_receipt保留字段但解释为明确记住/改正/忘记时需要的失败反馈；普通整理false。实际失败且明确要求时一次简短说明；后台失败内部记录，不另发群。模型可自然应声，不提前宣称文件保存成功。提示留程序职责，不为此改写指定人设，也不对正文做删词过滤。

## 6. 精确恢复指定人设

源：ff2e348d236613ab74990edd3386dafb06b149ed的config/persona.md。[PERSONA_RESTORE](PERSONA_RESTORE.md)是交接备稿，不是第二运行入口：
1. 删除第十三节“精简版System Prompt”整个章节。
2. 删除开头指向该节的开发者说明，并顺排剩余说明编号。
3. 第1～12节、角色细节、颜文字规则、情绪反应、few-shot和署名保留，其余正文不改写。

备稿8,896 Unicode字符/17,575字节，SHA256：82a9378d450388a8c08cb30481ee42c8666c3a4b8758293a014d243a75ced430。实施原样写入config/persona.md，两阶段均读该文件；不采用439字候选，不再自动精简。

用户此次选择替代首稿“不得恢复旧颜文字配额/反应顺序”的风格决定。检查persona.py、natural_expression、dialogue.replyer_system，清理会盖掉指定人设的通用表达限制，例如“不强制昵称/颜文字”。人设里的规则交模型表达，不新增程序计数器、随机口头禅池或文本过滤器。

Planner管意思/事实/动作，Replyer按完整人设结合真实聊天表达；answer认真完整且仍可有角色声音，事实/代码/链接不失真。旧人设不授予额外工具、伪造进度/本机操作、提前声明保存或无新消息主动发言的能力；既有真实职责由系统/代码处理，不另改角色稿。

## 7. 文件和同轮实施

| 文件 | 必要修改 |
| --- | --- |
| group_memory.py | schema3、QQ整块更新、投影/迁移/待关联/同块完全重复、静默成功和管理导出 |
| turn_v2.py | 新视图/整块更新与全文绑定；旧fact_refs不作逐条索引 |
| persona.py、dialogue.py、config/persona.md | 新记忆/静默政策、指定备稿、阶段风格冲突；原两阶段保留 |
| adapters/codebuddy_vision_guard/hooks/register.ts | 官方事件薄适配，删计划/完整历史/阶段/步数门槛，实际资源预算友好收尾 |
| workbuddy_cli_runner.py、errors.py、必要model_gateway/web_retrieval接点 | parser/guard协调实际执行/错误/期限/最小诊断，最终来源仍用Planner真实回执 |
| backends.py、config.py、config_comments.py、provider实际拥有处、scripts/configure_astrbot.py | CLI180默认、派生provider等待、兼容停用10步门槛及实际source加载 |
| config/examples/models.yaml、settings.example.yaml、config/README.md、使用说明 | 当前默认/生效、新记忆、旧步数字段忽略、人设输入代价、静默保存 |
| scripts/configure_bot.py / memory_action | 按群/成员整块管理，去掉当前记录ID入口，不重做菜单系统 |
| 受影响测试/配对脚本、AGENTS、入口与任务文档 | 必要回归/当前配对，部署后更新schema3与内部保存/必要失败反馈合同，历史证据保留 |

用户手动提交MEDIUM_START后，在本根短期codex/lap48-memory-web-persona分支一次实现、必要检查、精确备份、空闲点受管停止/迁移/技术配对、启用正常启动和Git交付。不建长期worktree，不分多轮审批；计划内常规适配直接修复。

本机只改所选CLI运行期限180；读取当前真实local，保持用户当前群/操作者/模型/账号/low/开关，不拿规划快照覆盖后续改动。仅操作有创建身份依据的项目进程，不按QQ/Node/Python名称批量结束，不动日常QQ/WorkBuddy全局配置。未跟踪用户启动bat不执行不提交。独立WeChatbot不操作。

## 8. 必要验证

规划不跑实现测试；实施只覆盖受影响行为：
- 记忆：合成迁移/QQ同名改名/整块更新清空/未关联保留与真实身份匹配/已有微信配对；全文无_meta、程序长HMAC或逐记录ID；同块完全重复折叠，时间差异/不同人不误合并。验证实际保存/冲突与字节即可。
- 联网：锁定SDK离线harness覆盖没有第二计划/滞后历史仍执行、并行/内嵌摘要、网站错误不毒化、10步不再拒绝、预算提示正常收尾、非允许工具仍关闭。替身时钟验证180/30/5及235，不真的空等三分钟。
- 回执：成功/无变化不改正文/部件，明确失败一次，后台silent不新增消息。
- 人设：文件与备稿一致、仅删除指定节/失效说明，两个阶段加载且无通用风格覆盖；不把某个口头禅/颜文字出现当自然感单元标准。

跑现有受影响记忆、dialogue、native web、runner/配置/投递用例和必要当前真实CLI零生成技术配对一轮；新失败/改动才补相应用例。不照抄实现扩建测试，不跑旧全库/六例/长稳大矩阵。图片绑定按现机制更新，不关识图绕过、不伪改旧证明。

部署后读health/实际provider source/加载配置，确认期限、人设、记忆与原能力。agent不主动真实模型生成、公共WebSearch/WebFetch服务查询或QQ/微信测试消息；用户自然群测真实角色/质量/延迟，不能把离线/健康晋升此类结论。

## 9. 成本、回退、Git

无新业务阶段或专门去重调用。完整人设单份1,502→17,575字节，两个阶段和Planner工具往返的输入/缓存影响费用；不能声称省掉编号就抵消它或总费固定。180秒占队列更久；去掉额外拒绝可能完成更多正常处理，仍受真实容量和期限约束。

QQ号进入记忆是用户选择，实际资料仍不提交，不自动放进搜索。暂未关联不猜人、不阻塞上线，不加逐条人工审批。

回退先受管停止并保留当前schema3及后续新增事实；旧代码不能直接读新格式，配对恢复代码/期限/provider/人设/技术材料/备份。已有新事实先导出/保留增量，不能旧备份覆盖丢失；只恢复本任务精确变化，不覆盖用户后续配置，不清会话/图库/登录或其它项目。

完成后快进main、清理已合入短期分支；按长期授权仅提交本任务已核对文件并push，核对本地/实时origin/main一致。报告实际验证/部署/提交/待用户群测项/剩余差异。真实能力缺口改变方案才回报，不为常规适配再追加审批。
