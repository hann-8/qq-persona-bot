# LAP-47 群聊理解与自然表达分离

返回 [PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承根 [AGENTS](../../../../AGENTS.md)。

状态：planned / ready_for_medium；方案与统一指令已落盘，文档核对已通过。尚未实现、启用或部署；Git 交付提交见本轮会话回执。

目标：核对 MaiBot 的 Planner / Replyer，给现有 SnowLuma bot 制定一次落地的轻量改造方案，由用户交给 medium 实施，真实群聊由用户实测。同时按用户纠正，将 AGENTS.md 清理为长期项目准则，并原文加入“严禁过度防御性编码，严禁过度测试，严禁让整个设计落地流程分太多步骤。”

本轮 session：LAP-47-maibot-dialogue-plan，2026-11-04 18:30（Asia/Shanghai），当前会话唯一文档写入者；不派代理。

安全检查点：主线 `main`，HEAD / 实时 origin/main 均为 `31e9adc6f41ed5c01c87506400de1aa7264edd0f`。已有用户未跟踪文件 `启动机器人_workbuddyDeepseek.bat` 保留，不执行、不提交。未发现其他已跟踪差异。

归属：根 AGENTS.md、PROGRESS.md、工作线 HANDOFF.md / TASKS.md、本目录 HANDOFF.md / PLAN.md / MEDIUM_START.md。不修改源码、配置、人设、状态或历史交付记录；不启停、不登录、不调用真实模型或发消息。

成果：[完整计划](PLAN.md) / [统一 medium 指令](MEDIUM_START.md)。本轮共七份文档，不改源码、local 或人设内容。

已核对：根准则、PROGRESS、工作线入口、LAP-46 当前交接；MaiBot main 固定参考提交 `c6429547af711555e3d4d1b8d04b413572cb616c`，实际 Planner/reply_reference/真实聊天输入/Replyer 分工与过滤代码已读。当前项目的 persona、v2、WebRunner/CLIRunner/ModelQueue、记忆和技术绑定接点已核对；本机配置仅读取非秘密参数投影。

决定：CodeBuddy v2 同任务内 Planner → Replyer，silent 一阶段、speak 最多两阶段；表达不重复工具/像素/记忆决策。共享现有 120 秒整项运行期限，表达默认预留 30 秒；精简 9,585 字符的人设，保留角色，删除机械配额。只新增 chat.dialogue_mode 与 chat.replyer_reserve_seconds。Ollama/旧接口保留单阶段，独立 WeChatbot 根不动。

AGENTS 已去掉部署/排查流水账，保留长期准则，原文加入用户三条禁止要求；当前与历史任务进度继续由 PROGRESS、任务交接和 Git 承接。本次方案不写成 AGENTS 进度。

实施授权边界：用户提交 MEDIUM_START 后一轮实现、启用两个 local 字段、精简人设、必要离线/零生成配对、受管部署和 Git。agent 不主动真实生成/搜索服务质量测试/QQ或微信测试消息；真实自然感、事实保持和延迟由用户实测。旧大矩阵/六例 IQ 不作本次前置。

验证：七份归属文档的差异与合同已核对，33 个新增/本地引用均可达，git diff --check 通过；AGENTS 原文要求存在、日期流水账已移除。不运行行为测试，不探测模型，不查询当前进程健康，不把前日部署健康当本轮事实。功能与实际两阶段 CLI 延迟均未验证。

下一步：用户将统一指令交给 medium。从 AGENTS/PROGRESS 进入本任务即可；无需重做 MaiBot 全库调研或再拆规划审批。本轮归属在文档提交推送交付后释放，原用户未跟踪 bat 继续保留。
