# LAP-32 清理台账故障调试与目录说明

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md)。继承AGENTS。

2026-10-18 23:52（Asia/Shanghai）领取；session `LAP-32-cleanup-ledger-debug`。用户明确本轮为sol high调试/修复，目录文档为附带工作，不另做功能规划。一个任务覆盖本次故障排查、已有LAP-31合同内的修复和目录说明。

范围：`src/qqbot_gateway/cleanup_identity.py`、`scripts/process_host.py`、`tests/test_lap32.py`、根`项目目录与日志说明.md`、本交接；共享PROGRESS/TASKS/工作线HANDOFF仅追加本任务登记，保留LAP-29内容。开始存在LAP-29的代码/配置/README/报告及共享台账改动，全部不归本任务、不覆盖、不夹带。

现场只读证据：用户附件NapCat日志含提示文本及连接事件，不含CLI清理诊断；`logs/model.log`在2026-10-18 23:00:52记录trace `87c0968601`、generation=success、outcome=observed_empty、coverage=observed_only、reason=ledger_error、count=41、elapsed_ms=30；之后重复CLEANUP_FAILED。`manage.py cleanup status`返回blocked=true；未决账本仍在，当前reason为identity_changed/observation_incomplete。初次具体文件操作/OS错误未记录，不能把后续被动检查结果当原始原因。

当前检查点：2026-10-18 23:58（Asia/Shanghai），修复已实现/95项相关离线回归通过，目录说明已完成；真实bot未恢复、初次OS错误仍无法追溯，31B差额保留。

已完成：
- 自造临时文件原生复现Windows读句柄冲突：atomic replace得到PermissionError/winerror=5，unlink得到winerror=32；没有操作真实台账。此为与现场相符的可复现路径，不能倒推初次ledger_error一定由它引起。
- cleanup台账写未决/轮换摘要/写摘要/删除未决对Windows 5/32/33错误最多尝试3次，10ms/20ms等待受当前清理deadline和单操作60ms重试窗口约束；睡眠超出剩余窗口不再尝试。永久权限/磁盘/数据失败仍阻断，不清unknown、不额外模型尝试。底层OS调用无法强制中断，原单task/总deadline接管保护保留；到期后只允许原有阻断元数据保存路径的一次尝试。
- 新CLI_CLEANUP_IO只记录随机trace、固定operation/error和1..3次序；process_host只放行封闭字段，不输出异常正文、文件路径、argv、凭据或进程身份。
- 相关回归首次93项中旧31摘要轮换测试出现31≠32，确认系统time_ns重复+相同trace可覆盖摘要；增加随机文件名后缀，固定time_ns的36次写入确定性回归通过，32份上限保留。
- 根[项目目录与日志说明](../../../../项目目录与日志说明.md)说明完整一级目录、主要下层、源码分工、4日志、只读状态命令和本次故障/恢复限制。

验证：专项命令`.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_lap32.py -v`；最终聚合通过test_lap32（10项）、test_lap31、test_cli_runner、test_model_gateway、test_lifecycle、test_process_host、test_local_backend，共95项、0失败/0错误。聚合方式为同一unittest.TestSuite装载上述7个模块；控制台详细结果在忽略的`state/lap32-regression.log`。包括原生Windows句柄、临时失败后下个假runner请求成功、永久失败后重启0模型尝试、PID复用、取消/关闭接管和总deadline回归。没有运行旧verify主入口/覆盖旧报告。源码/文档差异、链接与隐私检查另在Git交付前核对。

下一步：交付本任务8文件并核对origin/main SHA；正常加载新代码后可处理已复现的临时I/O冲突、保留更精确诊断。现有真实未决台账仍blocked，不能靠重启、删除文件或observed_only自动恢复；若继续处理现场恢复，须在LAP-31B合同下补完整退出证据，不把本轮标为真实恢复通过。

边界：不读取凭据/聊天正文，不启停或登录真实bot，不调用真实CLI/Ollama/QQ，不删除或改写真实未决台账，不用observed_only解锁。31B完整退出证明缺口仍保留。
