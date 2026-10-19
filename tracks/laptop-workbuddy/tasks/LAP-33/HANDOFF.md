# LAP-33 旧清理故障的人工恢复

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承AGENTS。

2026-10-19 20:06（Asia/Shanghai）领取；session `LAP-33-manual-cleanup-recovery`。用户持续要求排查/清除报错，明确不希望轻微错误永久停用bot，并已自行关闭bot。本轮仅执行一次保留完整备份的人工状态恢复；不实现新的自动恢复策略，不声称指定规划/实施模型已核实或切换。

开始工作区干净。归属：本交接、PROGRESS、工作线HANDOFF/TASKS；本机忽略的state清理记录归档。bot启停仍归用户，本session不启停、不登录、不生成、不发群消息。

执行前合同：持项目configuration_lock，确认受管身份全部退出、台账owner和41个登记身份均明确exited、五端口不监听、原trace匹配且记录未被并发改动，才将原始字节完整备份并移出活动路径；不kill、不重放/补发、不动任务/历史/ACK/REMOTE_RESULT_UNKNOWN。任何检查失败则不归档。备份保留SHA256及人工恢复说明；恢复说明明确coverage仍为observed_only。

用户最新要求下，接受已观察集合全部退出的一次人工恢复，调整旧31/32对现场持续阻断的处理；这不是job_complete/所有后代完整退出证明，旧31B缺口保留，不能称完整自动恢复验收通过。原始ledger_error具体文件操作仍未知。

验收：只读cleanup status在归档后blocked=false；受管进程/五端口仍停止；归档原始字节SHA256一致；不消耗模型额度。若用户正常启动后仍报错，按新trace/CLI_CLEANUP_IO重新排查，不自动清除新记录。

当前状态：2026-10-19 20:06:54（Asia/Shanghai）旧记录已人工归档，随后独立只读状态确认blocked=false；不等于长期代码修复或真实生成验收。

现场结果：20:04:58/20:05:02/20:05:07的三次拒单均没有CLI_START，仍对应旧trace 87c0968601。用户再次关闭后，锁内确认managed身份为0、旧owner与41个身份全部exited，6185/6199/6200/6099/8765全部关闭。原始记录完整备份及重命名归档到本机忽略目录 `state/cli-cleanup-manual-archive/LAP-33-20261019-200654-87c0968601/`，含unresolved.backup.json、unresolved.archived.json及manual-recovery.json；两份原始字节SHA256一致，恢复说明明确不是完整后代覆盖证明。未删除原始证据、不改原记录内容。

验证命令：`.venv/Scripts/python.exe -X utf8 scripts/manage.py cleanup status`输出blocked=false/observed_empty/observed_only/reasons=[]；`... scripts/manage.py status --json`输出stopped、四组件为0，任务计数493/52/send_unknown=1前后一致。现场脚本持configuration_lock完成身份/端口/原始字节核验、备份与归档后再读取CleanupOwner.status；没有运行模型。没有代码变更，未为一次状态维护新增代码测试。实际启动及真实群效果由用户后续验证，尚未验收。

回滚：保持bot停止并持配置锁，只有没有新的活动unresolved.json时，才能以归档原始字节恢复原路径；有新记录则禁止覆盖。回滚会恢复旧阻断，不回滚数据库或其他状态。

下一步：交付本任务4份文档并核对远端；用户可自行正常启动验证。如新请求再次失败，只核查新trace/文件操作诊断，不自动归档新记录。长期故障分级/自动恢复仍需后续规划与实施；31B缺口及旧真实验收差额保留。
