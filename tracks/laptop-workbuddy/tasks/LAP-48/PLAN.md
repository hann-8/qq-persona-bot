# LAP-48 详细设计：成员记忆、联网等待与角色表达

返回 [PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承根 [AGENTS](../../../../AGENTS.md)。先读 [独立评审稿](REVIEW.md)；接续状态见 [HANDOFF](HANDOFF.md)。

状态：planned / awaiting_review，2026-11-04（Asia/Shanghai）。本轮只读与文档；此文不表示功能已实现或部署。用户追加的安静记忆保存和角色恢复已纳入同一方案。用户确认后提供实施指令，不自动派代理或切换模型。

## 1. 目标、范围和完成标准

在 QQbot_Snowluma 当前 main 上一次解决：记忆按人阅读且减少模型无意义输入；修复联网计划匹配早失败并贯通三分钟运行期限；成功保存记忆不追加提示；恢复大肥鱼个性且保持 Planner → Replyer 的自然表达。

完成标准：

1. 人能直接找到成员名下的记忆；改名/同名不混人。全群记忆仍完整交 Planner，Replyer 只接必要事实。
2. 模型不再收到长期记忆的长哈希、存储版本和去重键；精确增改删与可靠保存保留。
3. 合法 SDK 工具事件不因另一快照尚无计划而被拒；三分钟预算从阶段到 provider 一致，失败原因不再全归为后端不可用。
4. 成功或无变化不追加记忆回执；明确记忆要求失败才告知。内部保存证据保留。
5. 两阶段加载同一份具有辨识度的角色材料，认真回答仍能保留角色声音；自然感/人设质量以用户体验为准。

不增加模型/后端/账号、收费 API、业务阶段、整项重试、并行任务、主动定时聊天、关键词记忆筛选或正文内容过滤。模型仍为当前配置，思考仍 Planner low 开、Replyer 关；原触发/唯一操作者/授权群/识图/表情/额度来源保留。

独立 `E:/CodexWS/WeChatbot` 不属于此任务。本根已接入的 WX-Akasha 使用共用 MemoryStore，必须保留已有显式群/成员配对映射；不因本次格式变化重建身份或混群，不扩展微信范围。

## 2. 当前证据与判断边界

| 证据 | 当前事实与含义 |
| --- | --- |
| [group_memory.py](../../../../src/qqbot_gateway/group_memory.py) 的 TOP、prepare、POLICY | 磁盘 schema2 有 namespace_hmac/generation/revision/last_request_key 和平铺 records；模型视图含 generation/base_revision/records/actors。记录键为 32 位随机十六进制，正文反复出现 `u_` 加 64 位成员标识 |
| 同文件 _write | canonical 单行写盘，没有缩进。人读困难并不等于模型不能读；长标识在语义上无帮助，仍有存储身份/并发用途 |
| 本轮首次结构采样 | 三份忽略的实际记忆文件为 8/32/4 条，记录键合计 1,408 ASCII 字符、正文成员标记合计 2,376；仅读结构统计，不复制私密事实。运行中的 bot 后续自然更新不视为本会话改写 |
| [dialogue.py](../../../../src/qqbot_gateway/dialogue.py)、[runner](../../../../src/qqbot_gateway/workbuddy_cli_runner.py) | 总运行 120，Replyer 预留 30，每阶段 runner 再从截止时间扣清理 5 秒；Planner 实际最多约 85 秒，提前完成时 Replyer 可使用更多剩余时间 |
| [config.py](../../../../src/qqbot_gateway/config.py)、[configure_astrbot.py](../../../../scripts/configure_astrbot.py) 及实际 provider_sources | 校验固定 queue_wait + run_timeout + 25 ≤ 180；当前实际源 timeout=180。web.timeout_seconds=15 属旧 Python retrieval，不是当前原生 CLI 搜索的整项期限 |
| 忽略日志/台账 | 2026-11-04 19:27:03 天气问题；19:27:12 CLI trace `7c84eda6a5` BACKEND_UNAVAILABLE，initialized=true、2 tool calls/2 results，先 tool_plan_missing，再 native_ready；19:27:13 第一任务已投递失败说明。19:27:17 后续消息，19:27:39 不同任务已投递天气答复 |
| [register.ts](../../../../adapters/codebuddy_vision_guard/hooks/register.ts) tool.call/nativeStep | 工具事件必须再与 planned 或 session.messages 中的同 id/name/input 匹配；找不到就失败，native.failed 又令后续步骤被 native_ready 拒绝。现有摘要不足以判断具体的流式/并行/内嵌顺序，不宣称已复现原始时序 |
| 当前锁定 CLI 的 dispatchModsToolCall 与随包 Mods 文档 | 官方执行路径产生 tool.call 的 tool/tool_use_id/agentId 和输入，非 flat 路径还检查这些身份不可被改写；公开中间件入口足以执行薄的工具白名单/预算适配，不需要自建第二份计划作为许可 |
| [errors.py](../../../../src/qqbot_gateway/errors.py)、ResultParser | BACKEND_UNAVAILABLE 的正文是“暂时接不上模型”；MODEL_TIMEOUT 单独映射。CLI 错误与本地拒绝可能被前者兜住，这个样例不是总超时证据 |
| group_memory.receipt_plan / [router](../../../../plugins/qq_router/main.py) | aux 请求回执时，宿主追加保存/未变更固定句并重建最终计划，可能把自然聊天变成 answer、截短原正文 |
| [persona.md](../../../../config/persona.md)、[persona.py](../../../../src/qqbot_gateway/persona.py)、dialogue.replyer_system | 两阶段均加载当前角色；实现 78da4ea 将原 9,585 字/442 行压成 514 字/11 行，删掉许多身份细节。近期日志有角色表达，也有同一颜文字连续复用；不据此给所有回复作主观评分 |

原始群消息、实际记忆、配置、CLI 捕获均不提交。诊断仅确认本次触发的本地拒绝原因；不把它扩大为所有联网失败的唯一原因。

## 3. schema3：一个文件，两种展示

### 3.1 磁盘合同

沿用 `state/group-memory/<现有 namespace>/memory.json`，不改群目录和 memory key。文件键按 schema_version、group、members、_meta 顺序写出，UTF-8、不转义普通中文、两空格缩进、末尾换行。原子临时文件/fsync/replace、锁与容量管理继续复用；canonical 仅用于内容摘要/模型紧凑投影，磁盘容量必须计实际落盘字节。

group 是 `rN → 文本`；members 是 `显示名 · mN → {rN: 文本}`，示例见 REVIEW。所有 rN 在本群唯一、递增分配、不因删除复用。mN 是本群稳定成员短编号；显示名只用于展示，真实身份仍由可信来源关联的 actor key 识别。重复名字因 mN 后缀自然区分；改名只换展示键、不新建成员。空名字用“未命名成员 · mN”。

_meta 集中保留：namespace_hmac、generation、revision、last_request_key、next_member_id、next_record_id、member_keys（mN → 现有长 actor key）。文件 schema_version=3 已在顶层，不重复存。必要版本与请求去重只存一份，成员长标识只在 member_keys 中存一次，不再放入每条记忆正文。组装时通过尾部短编号关联展示键，不把昵称当身份或权限。

当前身份算法、namespace_overrides、actor_links、key 文件保持。昵称来自本次 source.messages 与 identities 对应的真实发言；不能用模型猜测的名字合并账号。首次绑定和名字刷新由现有群处理/存储锁内完成，拿到更新后的版本再准备快照；只有文件实际改变才原子保存和更新 revision。它们不是新增长期事实，不产生聊天回执。

涉及多人的关系/共同经历放 group 一份，正文用姓名和 mN 引用；模型自主决定如何组织，不为节省 token 复制到多个人名下，也不强制固定喜好/性格等栏目。成员下可以放多段短文本，不把每句话拆成大量标签字段。

容量仍为可配置的 50,000 正文 Unicode 字符、单文件 1 MiB、总 8 MiB，所选输入政策保持；标识/缩进不计入语义正文字符额度，但计入文件/输入字节。保留完整全文，不加小条数或固定小注入门槛。

### 3.2 模型视图与更新合同

模型视图保留 group、members 的全文和 `actors: {当前 p_ref: mN}`；成员展示键仍含名字和 mN，记录为 rN。**不传 _meta、namespace、generation、base_revision、请求键或长 actor key。** model source 的摘要/绑定及上下文中的存储版本继续由宿主管理，不要求模型回显 CAS 字段。内部 manifest 可携带投影以核对全量材料，不把元数据重新塞回模型提示。

沿用 memory_updates 对象；新格式只增加明确归属：

```json
{
  "memory_updates": {
    "new_1": {"subject": "m1", "text": "现在更喜欢清茶。"},
    "r2": {"subject": "m1", "text": "希望被叫小青，不再用旧昵称。"},
    "r3": null,
    "new_2": {"subject": "group", "text": "周五的联机改到周六。"}
  },
  "memory_receipt": false
}
```

subject 只指本轮已提供的 mN 或 group；宿主据真实身份提供缺少记忆的当前发言者短编号，模型不自行创建账号。已有 rN 允许改归属；null 删除；空对象无变更；新增最终 rN 由宿主分配。未知 rN 不猜测目标。保留实际保存前的 snapshot/CAS/去重，成功后才写结果，重置短期上下文不清长期记忆。

valid_memory、validate_updates、manifest/fact_refs、源摘要、Planner 协议及本机 manage/export 一并适配；fact_refs 从两个层级展平。读取给模型时紧凑编码，磁盘缩进不增加模型输入。single/本根已接入微信同样使用新投影，不保留两套内容真源。

### 3.3 迁移

实施的受管空闲停止点，逐群备份原始 memory.json 和必要 key/配对状态到忽略的本任务部署目录，再迁移同路径文件。schema1 沿既有归一化逻辑接入 schema3，不删除已有备份；schema2 直接转换。不消费模型调用、不自动总结、去重或丢弃事实。

为旧记录分配稳定 rN，为旧正文的历史成员标记分配 mN 并保留长标记对照。恰好一个不同成员标记的记录归该成员；没有或涉及多个标记的记录归 group。正文只把这些历史身份引用替成对应短编号，内容、名字、时间与不确定性均保留，模型可在以后自然整理。历史标记只是既有记忆关联，不提升为管理员、真实 @ 或账号认证证据。无法从可信当前发言获知名字时保留未命名标签，不按昵称相似度猜账号。

在内存构建并校验完整新文件后原子替换；失败保留原文件。核对记录数、文本转换对照、群归属和容量，重跑不重编号、不重复迁移；旧程序不直接读 schema3。备份不计作新的模型记忆，不上传、不提交。

## 4. 联网：用官方事件，贯通时间预算

### 4.1 去掉重复的计划许可

tool.call 以当前锁定 CLI 产生的事件为执行依据，argsOf 继续只负责现有封套归一化。删除 native.planned / pendingStep 作为合法事件的执行前提及 session.messages 补找计划的逻辑；nativeStep 返回的 toolUses 不再作为第二次调用许可或重复计费依据。

在任何 await 前按 tool_use_id 预留一次调用，记录工具名/输入，沿用当前两工具 allowlist、非子代理、每任务 ID 去重、8 次总调用、10 个步骤、截止时间、公开 WebFetch URL 和返回/输入字节预算。其余工具/MCP 仍关闭，不加入内容词表，不扩大权限。tool.call → next(e) → 实际结果沿框架原路径执行，不自己实现搜索或重写 CLI。

nativeStep 仍负责真实模型/思考/输入预算与当前图片接线，需要的历史核对使用已观察到的调用/结果；允许当前正在执行的工具和 WebFetch 内嵌摘要，不要求正在进行中的所有调用已写入另一个快照。只调整本次重叠的调用计划/完成判定，不重做无关 vision 体系或忽略实际越权/容量错误。

普通工具或网站失败作为原生工具错误材料交回同一任务，由模型决定继续查询或用已得材料回答；调用仍累计，不重跑 Planner。中间结果不是最终群回复。本次已知 tool_plan_missing 的前置条件消失，native_ready 的连带拒绝不再由它触发；其他真实故障仍如实结束。

### 4.2 时间配置与生效

| 项目 | 实施值/行为 |
| --- | --- |
| CodeBuddy CLI run_timeout_seconds | 默认及本机所选 profile：120 → 180 秒；Ollama 原 profile 不顺带改值 |
| chat.replyer_reserve_seconds | 保持 30 秒；不是再加在 180 秒之外 |
| 当前 cleanup_seconds | 保持 5 秒；每阶段在共享 deadline 内预留 |
| Planner | deadline=整项 deadline−30；runner 内扣清理后，默认可用约 145 秒，包含该阶段启动、推理、原生工具与处理 |
| Replyer | 用整项剩余时间，至少按前一阶段预留安排；Planner 早完成时可用更多，最终清理仍在总期限内 |
| provider timeout | 从所选 queue_wait_seconds + run_timeout_seconds + 25 统一计算；当前 235 秒，替换写死的 180 及对应校验/注释 |
| 其他现有限额 | 原生工具 8 次/10 步、单结果 65,536/总 262,144 字节及输入政策保持；旧 Python web.timeout_seconds=15 不冒充原生期限 |

同一推导函数用于配置展示/验证和项目 provider 运行接线；当前受管启动把实际 provider source 更新为派生值，不要求用户手改 AstrBot 配置。不能只修改已不持有字段的 provider 条目而漏掉 provider_sources。只使用原 config/local/models.yaml 和 chat.yaml；示例、默认值、配置注释与说明同步。既有可配置范围保留，不新加隐藏短期限。

长等待不等于盲等：确凿账号/额度/协议故障立即结束；正在工作时不给临时失败通知。截止后沿既有取消/受管清理收尾，一项任务只完成一次。队列等待与模型工作时间分别记，不把后续新消息任务误认为第一次的迟到结果。

### 4.3 错误和最小诊断

保留 MODEL_TIMEOUT、AUTH_REQUIRED、QUOTA_EXHAUSTED、RATE_LIMITED、BACKEND_UNAVAILABLE 等真实含义。增加 WEB_ADAPTER_ERROR，正文“这次联网过程出错，没能完成查询。”；仅当同一请求的实际 guard 回执表明本地原生 web 拒绝时映射，不能凭用户问了天气就改错误分类。不要把真实登录、额度错误重映射。

failure_summary 保留现有安全元数据并补 phase、elapsed_ms、期限来源、真实工具/步骤计数、受控 guard 原因，明确总超时和工具自身超时；不加常驻原始消息、网页、查询、凭据日志，不要求重新采集一大套 trace。可复用既有一次性捕获处理实施中出现的具体缺口，不能因此增加真实模型样本。

## 5. 成功保存静默，失败诚实

receipt_plan 对 saved/unchanged 直接返回原计划：不追加固定句、不预留字数、不改 kind/气泡/表情/@，也不截掉正常正文。内部 MEMORY_SAVE、memory-last-save 和保存 revision 保留。

memory_receipt 字段暂保留以缩小协议改动，提示改为“明确要求记住/改正/忘记时需要失败反馈”；日常自主整理为 false。只有请求此反馈且实际失败/拒绝时，沿原一次最终计划收尾追加简短失败说明，不宣称已记住。普通后台失败只留内部状态，避免另一种机械刷屏。

正文政策同步为“后台整理不主动汇报保存”；不写输出正则删句，用户在讨论这句话时正常回答。模型可自然应声，但不能声称宿主尚未完成的写盘成功；用户明确请求失败时由真实保存结果纠正。silent 的普通自动记忆仍不新增发言。

## 6. 角色恢复

当前完整候选稿以 REVIEW 第4节为准，实施时写入唯一 `config/persona.md`，不另造一份运行角色文件。保留身份、自称/称呼、贪吃摸鱼、嘴硬心软、虚拟水池/米的世界观及错了认真的性格；把“认真准确”与“角色口吻”同时说清。

调整 dialogue.replyer_system 的正向职责：以蓝色大肥鱼身份表达，Planner 的 reply_reference 提供意思、必要事实和不确定性，语气由 Replyer 结合真实聊天/关系形成；不把指导当待复述的客服稿。kind=answer 的事实/代码/链接保持，不因此关闭角色。Planner 继续负责理解、事实和动作，不下发每条必须带昵称/表情/固定句尾的命令。

不为颜文字设置计数器、不建立随机口头禅池、不对生成文本按关键词加工、不新加人设评价模型。现有真实聊天快照已经可供 Replyer 避免机械复读，无需多注入完整长期记忆。候选正文 439 个 Unicode 字符（未计标题），比现稿略短，远小于旧 442 行；实际完整阶段字节/输入变化在实施结果据实报告，不设置人为字数硬门槛。

## 7. 涉及文件与一次实施路径

| 文件 | 必要修改 |
| --- | --- |
| src/qqbot_gateway/group_memory.py | schema3 读写/迁移、投影、短编号、更新归属、POLICY、静默成功回执及管理导出 |
| src/qqbot_gateway/turn_v2.py | 新记忆视图校验、展平 fact_refs/manifest、原全量绑定保持 |
| src/qqbot_gateway/persona.py、dialogue.py、config/persona.md | Planner 新记忆协议/静默政策；Replyer 角色职责；确认后的候选人设；既有两阶段期限接点 |
| adapters/codebuddy_vision_guard/hooks/register.ts | 工具事件薄适配，去掉重复计划许可，正确处理进行中的调用 |
| workbuddy_cli_runner.py、errors.py、必要 model_gateway/web_retrieval 接点 | web 适配错误分类、最小阶段/时间诊断，最终来源仍用 Planner 的真实回执 |
| backends.py、config.py、config_comments.py；plugins/qq_router/provider.py 或实际 provider 配置拥有处；scripts/configure_astrbot.py | 180 秒默认、派生 provider 等待、当前 provider_sources 正确接线、替换旧校验/注释，不创建第二日常配置入口 |
| config/examples/models.yaml、config/settings.example.yaml、config/README.md、SnowLuma使用说明.md | 默认/生效方法、新记忆格式、静默保存与等待语义 |
| scripts/configure_bot.py / 原 memory_action 所在接点 | 仅在新短 ID 和管理合同需要时适配，不重做菜单或管理系统 |
| 本任务文档、入口、必要现有测试及配对脚本 | 当前状态与受影响指纹/零生成接线同步；不伪改历史证明 |

实施成功后，把 AGENTS 中长期记忆合同的格式名 schema2 更新为 schema3，保留全文/模型自主增改删/可靠保存语义，并按本方案改为内部保存结果、必要失败反馈；不在规划期改写现行运行合同。

实施方先读当前 main、状态和本方案，保留未跟踪用户 bat；在本根短期 `codex/lap48-memory-web-persona` 分支工作，不建长期 worktree。用户手动提交确认后的实施指令后，同轮在一个受管停止窗口完成精确备份、代码/配置/记忆迁移、必要验证、当前技术配对和正常受管启动，再快进 main、清理已合入临时分支、commit/push 并核对远端。遇到常规已规划失败分支直接修复；只有改变方案的真实能力缺口才回报用户。

本机仅修改所选 CodeBuddy run_timeout_seconds=180；其他模型/账号/low/额度、群/操作者/开关不顺带改。人设和受影响配对以本方案为准。共用 MemoryStore 的现有显式微信配对纳入兼容检查，独立 WeChatbot 不操作。

## 8. 必要验证与未验证范围

不在规划期跑实现测试。实施仅覆盖变化的行为：

- **记忆：** 用少量合成数据验证 schema1/2→3 的全文/数量、同名/改名、无名字、群与成员/多人记录、短 ID 增改删、一次保存/冲突、导出和已有 actor_links。比较模型投影不含 _meta/长成员串且有全文，分别报告磁盘与输入字节；不虚报精确 tokenizer 成本。
- **联网：** 复用当前锁定 SDK dispatch 的离线 harness，覆盖正常事件在计划缺失/尚未进入 session 快照时通过、并行调用和内嵌摘要；保留非允许工具拒绝和真实次数/容量边界。用替身时钟验证 180/30/5 的共享 deadline 和 235 外层等待，不真的等三分钟。
- **回执：** 保存/无变更不改正文和部件；明确请求失败仅一次说明；后台 silent 不额外发言。最终投递台账仍只记录最终正文。
- **角色：** 核对两阶段确实加载同一确认稿、Replyer 含正向角色职责且只输出正文封套；不用某句口头禅或某个颜文字出现作为单元通过标准。真实自然度仅记录用户反馈，不由字符串检查冒充。

按变更跑现有受影响的 test_lap44_memory、test_cli_native_web、test_dialogue、CLI runner/配置/投递相关用例；组合必要技术配对只做一轮，新增失败/改动才重跑相应项。修改单文件无需重跑全库或旧六例/长稳矩阵。

部署前后完成原有真实 CLI **零生成**本地接线和当前绑定更新，再读 health/实际 source timeout/加载配置确认。记忆格式、角色提示/guard 指纹变化必须完成当前配对，不能通过关掉识图规避。不安排 agent 发起真实模型生成、WebSearch/WebFetch 服务查询、QQ群/微信测试消息。用户在自然群聊中验证搜索、角色和延迟，结果与健康/离线结论分开写。

## 9. 风险和回滚

更长任务会占用原唯一模型队列更久，后来的问题可能等待；仍无整项自动重试或新并发。格式迁移需要备份，历史无可靠昵称不会凭空恢复；不会遗漏这些人的事实。短编号与分层可减输入重复，完整阶段提示的调整和更完整的工具往返也会影响用量，不承诺净费用。

回退前受管停止并先保留当前 schema3 文件及后续新增事实。旧代码只认识旧结构，必须配对恢复代码、所选超时、provider 接线、原人设、技术材料和迁移前的记忆原件；若迁移后已产生新记忆，先导出/保留增量再恢复，不能直接用旧备份覆盖丢掉它们。只恢复本任务精确字段，不覆盖用户后来改动，不清会话/图库/登录或独立项目数据。没有后续写入时可直接用部署前精确备份恢复。

评审通过后生成与此稿一致的 MEDIUM_START；当前不创建可误当已授权实施的指令文件。
