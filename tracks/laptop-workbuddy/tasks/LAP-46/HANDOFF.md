# LAP-46 联网质量修正规划交接

返回 [PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [计划](PLAN.md)。继承根 AGENTS；用户本轮明确先 review 再实施，并希望全程由当前会话处理、保持简单。

状态：**planned / awaiting_user_review**。2026-11-02，session `LAP-46-web-quality-plan`，无代理。基线 main/2fd1073 与实时 origin/main 相同。尚未实施、配置变更、捕获开关、模型调用、启停或群发。

已完成：读取 AGENTS、项目/工作线交接及台账；定位当日 18:24/18:34 两例收发与 completed/sent 台账；确认来源尾巴为 web_retrieval.source_plan 强制追加；核对 native 提示、工具参数传递、结果裁剪和实际配置。独立公开搜索能找到相关资料，不代表 bot 工具效果。今日完整 query/返回轨迹未保留，检索差的具体根因未证实。

方案只改原生正文和简短搜索指导，复用一次性捕获做两例真实本机前后对照，最多四项业务任务、零主动 QQ 输出；不换后端、不加预算、不建搜索框架。真实调用和部署须等本计划获用户确认。需要换服务/模型/CLI或增加限额时，带证据回到 review。

本轮归属：PROGRESS.md、工作线 HANDOFF/TASKS、本目录 PLAN/HANDOFF 五份文档。用户未跟踪 `启动机器人_workbuddyDeepseek.bat` 保留、不执行、不提交；原始群消息、号码、数据库和捕获材料不进入 Git。旧 LAP-43、44、45、微信任务状态不改写。

验证：五份归属文档检查通过、244 个本地 Markdown 链接无缺失、git diff --check 通过；未改代码或配置。实现与搜索检查尚未执行。Git 交付为规划文档，不是部署；最终提交号以 Git/本次回复为准。

下一步：等待用户 review；同意后按 PLAN 第5节在当前会话一次完成最小实现、必要验证、配对恢复、Git 交付。实施前重新取当前配置/运行/Git基线，不沿用本次现场快照。此次规划 Git 核对后释放文档归属。
