# LAP-44：群记忆全文方案交接

返回 [PROGRESS](../../../../PROGRESS.md) / [工作线 HANDOFF](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [详细规划 PLAN](PLAN.md) / [medium实施prompt](MEDIUM_START.md)。继承根 AGENTS，用户明确要求尽快落地、避免流程拖延。

## 当前状态

2026-10-29，session `LAP-44-medium-handoff-plan`。用户已review总体方向，要求补齐详细规划后交 sol/medium 落地，并要求容量/预算以后可扩大。PLAN/MEDIUM_START 已准备；**未实施、未改本机配置或运行状态，记忆故障未修复**。下一步由用户提交 MEDIUM_START 给 sol/medium，同轮实现、必要检查、受管部署和 Git 交付，不再追加规划审批或补做旧大批次验收。

核心：本群记忆全文注入，模型决定内容/整理/遗忘；每群正文初始 50,000 Unicode字符，约5万普通汉字，停用旧句式、类型、候选、关键词和小限额。保留最少增改删协议避免全文反复输出，代码只负责本群归属/格式/版本/容量/可靠保存。所选 CodeBuddy 字节政策初始 524,288；所有数值可配置扩大，不把默认值写成最大值。扩容合成检查须接受100000字符/786432字节政策。仍有当前完整 CLI/vision 绑定和同一工具边界。具体数字、prompt、回执、文件、顺序、迁移/回滚见 PLAN。

本轮补充的关键接点：memory.validate_config 当前把 DEFAULTS[k] 当上限；TS adapter native_policy 仍写死 visible_limit<=48000，Python native_contract 则已经来自budget.limit。必须一起改为加载配置/真实容量，不是只换YAML或把48000换成524288。

## 本轮证据及归属

- 起点生产 main/c2346cb，初始工作区干净，LAP-43 部署归属已释放。当前运行状态只引用 43 已记录证据，本轮没有重新启停/探活。
- 本轮重查：三个 schema 1 文件 records/applied_txns 都为 0，仅读取计数，不输出原文。用户先前测试和旧日志支持“口头确认但无保存”，首个丢失点未唯一定位；新方案需逐段计数解决可观测性。
- 源码已核对 group_memory、turn_v2、persona、gateway、WebRunner、router 和预算，PLAN 列出全文可能被二次裁剪及联网清空的接点。
- 本地登记模型输入 1,000,000/输出 128,000，历史 F 上界 8,985 字节；5 万字符中文/emoji/转义封套做了纯本地长度核对，不是真实模型或费用测量。
- 只拥有五份文档：PROGRESS.md、tracks/laptop-workbuddy/HANDOFF.md、TASKS.md、本目录 HANDOFF.md/PLAN.md。登记已写后重读。不改 AGENTS/代码/local/persona/记忆/key/旧报告，不操作其他根，无代理。
- 写作中生产目录出现并行 LAP-43 修改：guard adapter/capabilities、43报告、vision_mod_guard、CLI runner/相关测试及43 HANDOFF。本轮未读取或夹带其私密运行数据，不修改这些文件。五份设计文档已转到 `E:/CodexWS/QQbot_LAP44_plan` 的 `codex/lap-44-full-memory-plan`；生产三个共享入口经逐字核对后只移除本轮内容，新44文档同步搬走，9项并行差异保留。受管 worktree 接口因聊天未登记 Snow 根不可用，普通 Git worktree 已创建；不声称已由 app 附着。
- 前条为初次设计历史；并行43修复现已由其owner提交至main/b0b4573。本轮在独立设计分支用merge提交fec402d保留并同步该既有历史，未改其代码或重做部署。起点设计3642b97，独立树初始干净，当前仅拥有原五文档加MEDIUM_START共六文档。生产main不在本轮修改范围。

## 验证与 Git

前次3642b97已通过5文档/11链接检查并推送。本轮6文档归属/严格UTF-8/围栏、28条本地链接、统一配置/单位/高于默认值的扩容合同及prompt授权一致性检查、git diff --check已通过，b0b4573祖先关系已核对；不运行功能测试或模型/QQ探针。仅提交这六份文档并 push `codex/lap-44-full-memory-plan`，核对本地/实时远端一致后释放归属；最终提交号和远端核对以 Git/本轮交付回执为准。不把规划检查记为实现验证。

## 实施提醒

先完整阅读 PLAN。保留“5万字符全文”决定，不重新设计关键词检索/摘要层/2千或3千字符限额，不把读取预算误当固定消耗。不要用简单删 `_resolve` 或只调一个 local 数字宣称完成：source/fit/manifest/web/prepared_plan/回执都需要贯通。实施按用户选择的模型/档位进行，不能声称自动检测或切换。

schema 1 备份和 schema 2 后续新增内容都要保留；实施时重查数据/分支/并发归属。具体真实效果交用户群测，不因只读/离线/加载通过就记为真实验收。
