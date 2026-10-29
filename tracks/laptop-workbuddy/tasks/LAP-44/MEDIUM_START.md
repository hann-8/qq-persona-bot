# LAP-44：交给 gpt-6.1-sol / medium 的实施 prompt

返回 [PROGRESS](../../../../PROGRESS.md) / [详细规划](PLAN.md) / [HANDOFF](HANDOFF.md) / [TASKS](../../TASKS.md)。

用户已 review 总体方向，2026-10-29 要求补齐详细规划后由 sol/medium 落地。以下整段可以作为下一轮用户指令；会话模型/档位由用户选择，不自动切换。

```text
请实施 LAP-44 群长期记忆改造，不再重新规划。使用 gpt-6.1-sol / medium；模型/档位由我在会话设置中选择，不要声称自动检测或切换。我要尽快用起来，本轮完成实现、必要检查、启用、受管部署及 Git 交付，不要停在代码或离线报告，不按阶段反复找我确认；QQ群体验由我自己实测。

生产根是 E:/CodexWS/QQbot_Snowluma，原 E:/CodexWS/QQbot/NapCat 根不要修改或启停。
先读生产根 PROGRESS.md、AGENTS.md、活动 HANDOFF/TASKS 和 LAP-43 最新交接；再完整读取：
E:/CodexWS/QQbot_LAP44_plan/tracks/laptop-workbuddy/tasks/LAP-44/PLAN.md
E:/CodexWS/QQbot_LAP44_plan/tracks/laptop-workbuddy/tasks/LAP-44/HANDOFF.md

设计在 codex/lap-44-full-memory-plan，已包含既有 main/b0b4573 的联网修复。先核对最新 main、工作区和任务归属，登记 LAP-44 本轮唯一实施/部署归属并重读；在隔离分支 codex/lap-44-full-memory 实现，保留生产与其他会话修改。不要覆盖 b0b4573 的 SDK/流式工具计划同步、URL 和诊断修复。生产运行期间不先切分支或替换源码；部署时正常 stop 后再快进 main。

实现合同：
1. 每次模型调用提供本群记忆全文，不跨群，不做 Python 关键词检索、相关性排序、摘要分层、按成员过滤或单轮2000/3000字符限额。
2. 是否记忆、记什么、如何概括/合并/更新/遗忘都交当前模型。使用 PLAN 的 system prompt 和合成例子，移除旧句式、类型槽、原句包含、关键词、候选/置信度/TTL/固定等语义门槛；不改我的 persona.md。
3. 每群正文初始 max_chars_per_group=50000，按 Unicode code point 计数，约为5万普通汉字，不是5万字节。只在同一次回复附轻量 memory_updates 增改删和可选 memory_receipt，不让模型每次重写全文，不另调模型或新增记忆工具/后端。
4. 容量和预算必须可配置扩大。50000、524288、1MiB是初始配置，不是代码上限。去掉 memory.validate_config 以 DEFAULTS[k] 封顶和 TS native_policy 的 visible_limit<=48000；不能换成 <=524288。schema、store、fit、manifest、gateway、CLI 每步校验使用同一加载配置，保留当前模型真实 C/F/V/O 容量边界。
5. 本机所选 CodeBuddy 输入政策初始提高到524288可见UTF-8字节，旧 memory 文件字节限额明确提升到1048576；memory 的旧240/3/8/1536等小限制停用且兼容旧字段。初始 enabled/learning_enabled 保持true，其他后端/profile和模型/账号不变。后续修改字符/磁盘配额和输入预算应只需改配置及正常应用/技术配对，不需要再改代码。
6. 贯通正常v2、联网有/无工具、prepared_plan、识图和router提交路径。不能因用过WebSearch/WebFetch就清空对本群人类消息的记忆更新；不把网页当群友自述，不上传群记忆。重置短期上下文、正常重启后仍能读回长期记忆。
7. 先保存再给实际回执：原子批量变更、版本冲突不覆盖、hook重入不重复写、失败保留旧文件。回执在投递台账建立前生成最终合法ReplyPlan，正确记录最终hash/ACK；不绕过已有发送栅栏。日志区分无动作/协议/容量/冲突/存储失败，只记计数/状态，不输出正文或凭据。

本次指令授权此任务必要的：停机前核对/备份、项目受管正常stop、schema1到2迁移、本机memory/所选CodeBuddy输入预算调整、当前完整vision/native-web技术检查和配对activate、正常start及health/加载快照核对、main快进/commit/push。以上同轮完成，不必重复询问。数据或真实模型能力出现具体阻断时保留现场并说明；一般实现细节自行解决，不把旧验收差额当上线门槛。

必要检查按PLAN做少量有意义的定向单元和现有AstrBot/锁定CLI替身组合。特别验证：首次写入→清RAM/重置→读回；50000字符全文；配置扩大到100000字符、file=2097152、total=33554432、CLI政策=786432后读写/全文/原生guard合法接线仍通过，同时超真实容量会被拒绝。该扩容是合成检查，生产仍按50000/524288初始配置部署。可以运行既有CLI零生成metadata/契约probe，不主动真实模型生成、WebSearch/WebFetch服务调用或QQ发消息，不新增全项目大型矩阵或循环额度试验。

保持唯一操作者、暂停/恢复、free、当前DeepSeek/low配置和CLI thinking=false、账号/credits、两工具白名单/3调用/4步骤/90秒/单结果8000/总12000、识图、受控表情及其他边界。只操作有创建身份依据的项目进程，不按进程名批量结束。原始群消息、配置/密钥/备份留本机忽略区，不能提交。

交付时说明：改了什么，必要检查结果，实际是否已加载部署、当前memory字数/条数和配置值，用户如何测试“记住称呼→重置→询问”及以后如何扩大配置；报告提交/远端一致及保留差异。同步 PLAN/HANDOFF/PROGRESS/TASKS、AGENTS和使用说明的当前合同。真实效果待我群测，不把离线/加载通过写成真实记忆验收。
```

当前只有文档准备完成，尚未实施、启用新协议或调整生产预算；只有用户将上述 prompt 作为实施指令提交后才执行其中部署动作。无需再为该轮授权动作逐项申请批准。
