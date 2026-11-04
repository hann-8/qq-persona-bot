# LAP-47 统一 medium 实施指令

返回 [PROGRESS](../../../../PROGRESS.md) / [HANDOFF](HANDOFF.md) / [完整计划](PLAN.md) / [TASKS](../../TASKS.md)。

将下面整段交给 `gpt-6.1-sol / medium`。用户提交本指令后，授权其中的实现、两个 local 字段启用、精简人设、必要零生成技术配对、受管部署和 Git 交付；本规划会话不执行这些动作。用户自行实测，agent 不主动发测试消息或调用真实模型做质量验收。

```text
阅读 E:\CodexWS\QQbot_Snowluma\AGENTS.md、PROGRESS.md，按活动任务进入 tracks/laptop-workbuddy/tasks/LAP-47/HANDOFF.md 和 PLAN.md，核对工作线 HANDOFF/TASKS 后，只实施 LAP-47。

严格遵守：严禁过度防御性编码，严禁过度测试，严禁让整个设计落地流程分太多步骤。AGENTS 只放长期准则，不再追加进度流水账。不要派代理或切模型。

我批准 PLAN.md 的整体方案，请本轮一次完成实现、必要检查、启用、受管部署、文档和 commit/push，不停在“代码写完待授权”。真实 QQ/微信效果由我随后实测；你不主动发送测试消息，也不调用真实模型/搜索服务跑质量样本。已有技术配对所需的本地 CLI 零生成检查可以执行。

实现要点：
- 当前 SnowLuma 根的 CodeBuddy v2 群聊增加 Planner → Replyer。Planner 负责语义理解、对象/发言决策、事实、工具/当前图片、表情和记忆更新；Replyer 读取冻结的真实聊天及 reply_reference，只写正文。silent 一次、speak 最多两次业务阶段，无第三次修复/分类/评审调用。复用既有 AstrBot/gateway/runner，不接入整个 MaiBot 或新 agent 框架。
- 同一队列任务、同一模型账号、同一个 120 秒总期限；表达预留默认 30 秒，阶段按剩余时间运行。Replyer 的思考、工具、图片关闭，局部参数不污染共享 runner；Planner 保持当前 low/思考及既有两 web 工具预算。
- 新中间包不能被现有 v2/web 正文恢复当作群消息。最终组装回原 v2 协议，保留 Planner 的来源/身份/记忆回执，记忆动作只处理一次，Replyer 不扩权。原 owner/muted/@/free、识图、受控表情、memory 和 ACK 边界保持；原能力不能为过检查被关掉。
- 精简 config/persona.md，保留大肥鱼的身份性格，去掉开发者说明、重复模板、颜文字配额、固定反应顺序等机械表演要求。原文件先备份，不另造第二个人设配置入口。认真回答仍完整，普通闲聊顺着上下文说。
- 仅增加 chat.dialogue_mode（缺省 single，本次 local 保存 planner_replyer）和 chat.replyer_reserve_seconds（默认 30），正常启动生效。Ollama 和旧接口保留 single；health 如实显示实际模式。阶段 usage 如实合并，不把两次记成一次，不建常驻原文日志。

执行保持三个连续工作块：整体实现 → 必要检查和当前技术配对/部署 → Git 交付。使用本根短期分支，部署前只按创建身份操作项目受管进程；不新增长期 worktree、不操作旧 QQbot 空目录、不修改独立 WeChatbot。

只补少量有意义的阶段/能力/期限回归，按受影响接点运行已有用例与必要 revalidate/probe/activate，一次完成，不重做历史大矩阵或六例 IQ，不增加质量审批轮。一般实现细节自行处理，只有确实改变方案的能力缺口才说明。

先核对用户和其他 session 的差异、TASKS 归属与精确恢复材料。规划时已有未跟踪 启动机器人_workbuddyDeepseek.bat，保留、不执行、不提交。当前源码、配置若较规划变化则按真实状态接续，不覆盖未知修改。配置只改本计划字段，秘密、群号、私密消息和 state 备份不提交。

最终回到 main，核对 ready/connected、实际加载的双阶段和原能力、无待重启；同步本任务结果/HANDOFF 与 PROGRESS/TASKS，commit/push 并核对远端一致，清理已合入的临时分支。交付说明写清做了什么、必要验证结果、提交号、剩余用户差异和“真实自然感/延迟待用户实测”，不要把离线或零生成说成群聊验收通过。
```
