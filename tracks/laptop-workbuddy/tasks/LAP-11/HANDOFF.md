# LAP-11：纯文本输出与人设 v2

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md)。合同：[UX_PLAN](../../UX_PLAN.md)第6节，U01—03、U13—14；继承AGENTS边界。

状态：已实现/离线通过；未部署，真实QQ ACK/最终人设接受待验。2026-10-16 23:30（Asia/Shanghai）领取，session标题“LAP-11纯文本与人设v2实施”。用户授权实现、验证、提交与推送；开始时main工作区干净。不声称自动检测或切换会话模型档位。

范围/文件归属：新增src/qqbot_gateway/chat_text.py及角色固定政策模块；model_gateway.py、config.py、plugins/qq_router/main.py、scripts/configure_astrbot.py、config/persona.md、pyproject.toml、相关测试/框架离线验证及必要文档。本session独占这些变更及进度台账写入；不启停现有实例、不发群消息，不修改本机运行配置。LAP-10能力缺口和旧真人验收差额保留。

顺序：锁定markdown-it-py 4.2.0并核对token API；网关唯一转换/工具污染前置拒绝/自然边界截短；固定政策优先组合人设并统一版本hash；落地计划v2草案；离线单元与实际框架保存/发送回归；同步报告和交接后提交推送。

验收：U01/02混合格式保留语义与代码；U03保存发送同一内容单次答复；U14入口反例仍静默；U13固定边界和离线样例不冒充真实模型风格接受。真实QQ ACK、P01最终人设接受需要用户参与，另行明确记录。

兼容/回滚：旧人设正文与hash备份至本机state/persona-backups；新版本使下次请求新建当前会话，旧历史保留，已提前告知用户。不改原Obsidian参考。回滚仅还原本任务文件并停止后重新部署，不删除数据库或覆盖其他变更。

最后安全检查点（2026-10-16 23:41 Asia/Shanghai）：实现及验证完成，结果见[报告](../../../../reports/lap-11-2026-10-16.md)与[结构化离线证据](../../../../reports/lap-11-offline-2026-10-16.json)。82项单元测试通过；5组实际AstrBot回环provider/runner/保存/装饰/OneBot发送一致，各一次模拟ACK；无@喊名、引用内At、冷场、黑名单入口及版本迁移回归通过。修复CommonMark星号跨位置误配，以及框架provider对代码空白/think/JSON原文的改写；固定政策与角色正文统一版本hash。未运行部署脚本或改本机配置、未登录/启停/真实推理/群发；运行实例尚未加载，当前运行状态未重新探测。

修改文件：src/qqbot_gateway/{chat_text,persona,model_gateway,config,errors}.py，plugins/qq_router/main.py，scripts/{configure_astrbot,verify_lap11,verify_g4_routing}.py，config/persona.md、pyproject.toml，tests/{test_chat_text,test_config,test_model_gateway}.py，README、reports/lap-11*、UX_PLAN、ACCEPTANCE、PROGRESS/TASKS/工作线及本交接。新增依赖只在项目.venv安装，框架已同版；原persona v1以hash备份到忽略目录。首次根CWD框架测试产生的默认data已保存到忽略state/lap11-framework-scratch，未丢其他改动。

验证命令：项目Python执行`-m unittest discover -s tests -q`（82通过）；框架Python执行scripts/verify_lap11.py（5例通过）；从runtime/astrbot执行绝对路径scripts/verify_g4_routing.py（入口/隔离/预算/版本迁移通过）。99个本地文档链接及git diff --check通过；提交/推送按本轮用户明确授权执行，提交不代表部署或完整验收。

剩余/下一步：当前不需要用户登录。后续真实QQ ACK与U14群回归、人设3组各2次/P01最终接受需用户在NapCat按需登录并参与；报告仅有人为拟定风格预期，不冒充真实模型输出。LAP-10强制压缩/内部恢复及原生窗口缺口先回规划，LAP-12及旧LAP-02/03/04/05差额保留，不自动扩大本session任务。原Obsidian参考、账号/额度来源、实际settings.local和日常QQ/WorkBuddy配置未改。

交付：实现提交`d00d11f`已成功推送origin/main；99个本地文档链接、工作区/暂存差异格式检查通过。本记录随后仅文档提交同步。真实模型/QQ消息次数均为0，运行实例未部署，不改变未验结论。
