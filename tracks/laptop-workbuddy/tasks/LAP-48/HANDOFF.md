# LAP-48 记忆、联网早失败与大肥鱼角色表达

返回 [PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承根 [AGENTS](../../../../AGENTS.md)。

状态：planned / awaiting_review，2026-11-04 19:54（Asia/Shanghai）。[独立评审稿](REVIEW.md) / [详细设计](PLAN.md) 已完成。用户只授权本轮规划；当前会话是唯一文档写入者，无代理。用户反馈后修订，确认后提供 medium 指令；不自动实施，也未创建 MEDIUM_START。

目标：按成员组织记忆并减少无意义模型输入；修复联网早失败并贯通三分钟运行预算；用户追加“成功保存不在聊天说出来”和“恢复大肥鱼人设，保留拆分后自然感”均已纳入。

基线：main / `31945062e726b4b98a8b6717d4315063537581d0`，开始实时 origin/main 相同。仅有用户未跟踪 `启动机器人_workbuddyDeepseek.bat`，保留、不执行、不提交。旧 QQbot 是空 cwd；实际工作根为 QQbot_Snowluma，独立 WeChatbot 不在本次范围。

决定：一个 schema3 memory.json 按“成员名 · mN”分层、rN 精确改删，元数据/长身份映射集中 _meta 且不入模型，全文范围不缩减；成功/无变化不追加回执。信任锁定 SDK 官方 tool.call，去掉第二份计划匹配前提；180 秒两阶段共享、表达预留30、清理5，Planner约145秒，provider由30+180+25推导为235秒。角色候选见 REVIEW，恢复具体性格/称呼/米与水池设定并明确 Replyer 表达职责，不增加固定台词/配额。

证据：19:27:03天气问题、19:27:12失败，CLI trace 7c84eda6a5 记录 tool_plan_missing → native_ready，不是 MODEL_TIMEOUT；首次失败投递与19:27:39天气答复属于两项任务。具体 SDK 原始顺序未留在摘要，不能确定并行/流式/内嵌哪一种；不把本例推及所有故障。两阶段人设都已接线，原 9,585 字压为514字；日志有角色口吻和重复颜文字，用户报告拆分更拟人、角色变淡。候选439字（未计标题），具体表达效果待用户 review/群测。

本轮归属仅 PROGRESS、工作线 HANDOFF/TASKS 和本目录 HANDOFF/REVIEW/PLAN。只读当前源码、锁定 CLI 源码/随包官方文档、必要忽略日志/只读任务台账、health和记忆结构统计；不改运行配置/人设/实际记忆，不启停，不调用真实模型/搜索或发送消息。共用 WX-Akasha actor_links/namespace_override 在实施兼容范围内，独立 WeChatbot 不操作。当前 bot 自然运行写入不归本轮改动。

验证：归属六文档的281个本地链接均存在、两处JSON示例可解析、双向入口和review先行边界通过；git diff --check通过。源码/运行配置/实际人设/记忆均未由本会话修改，不跑实现测试，不把只读health当成功验收。候选角色正文439字已独立计算，未声称一定增加或减少总模型费用。

Git交付仅六份归属Markdown，提交说明 `docs: plan LAP-48 memory, web reliability and persona improvements`；最终SHA以本轮回执/git log为准。commit/push并核对main远端一致后释放文档归属；用户未跟踪bat继续保留，不提交。

下一步：用户 review REVIEW；有反馈修改两稿。确认后给与最终方案一致的一份 medium 指令，用户手动交接；实施按 PLAN 一次落地/必要检查/启用部署/Git，不追加历史大矩阵或真实测试样本。
