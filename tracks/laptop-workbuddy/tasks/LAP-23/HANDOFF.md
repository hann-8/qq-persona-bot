# LAP-23 WebSocket断线后持续409修复

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md)。继承AGENTS和现有连接/权限合同；既有功能内故障修复，不新增后端或触发行为。

2026-10-17 18:47（Asia/Shanghai）领取；session `LAP-23-gate-reconnect` / “WebSocket断线持续409修复”。起点2a6b119，工作区干净。归属：onebot_gate、process_host及对应测试、本任务报告/交接/PROGRESS/TASKS/工作线；本session独占。不启停/登录/调用真实模型/群发，不改运行配置/人设。

用户日志显示已有send_group_msg后断开并持续409；入口409为active未释放。只读当前6200/8765健康不可达、项目五端口无监听，未自动启动。日志没有保留gate具体异常，不能断言现场完整根因。

代码证据：handle finally先publish_connection再self.active=None；publish抛出会跳过释放。Windows临时目录实测持有gate-connection.json读取句柄时publish_connection抛PermissionError(winerror=5)，与router读该文件存在竞争可能；不是用户现场异常的直接证明。

计划：离线连接注入状态文件失败复现占用泄漏；状态写入做有界共享冲突重试，清理保证释放并失效online；只保留固定错误类别元数据以便后续诊断；验证重连/健康/重复连接拒绝/权限/去重，保留unknown发送不重放。需要文件永久不可写时仍明确失败，不放开准入或抢占存活连接。

验收：失败后不永久409、旧状态不继续标online、真实存活连接仍拒绝第二连接；0真实外发。剩余：复现/修复/离线回归/文档/Git。用户现场真实稳定性仍待验。

2026-10-17 18:50（Asia/Shanghai）检查点：已实现/离线通过，未加载/启停真实bot。修复前真实WebSocket合成故障注入复现active泄漏；修复后212全单元、18最终入口、实际AstrBot准入/ACK框架通过。真实Windows持有读句柄的断线/重连也通过。报告见[证据](../../../../reports/lap-23-2026-10-17.md)。

改动：清理释放与状态失效先于文件I/O；replace仅Windows指定共享错误最多3次/20ms；永久失败关闭通道，socket清理不被metadata异常跳过；固定错误类别经process_host安全保留。真实现场首个异常仍未知，不伪称根因完整取证。未改变模型、触发或权限。

文件归属：src/qqbot_gateway/onebot_gate.py、scripts/process_host.py、tests/test_onebot_gate.py、tests/test_process_host.py、reports/lap-23-2026-10-17.md及本交接/PROGRESS/TASKS/工作线。只有本任务修改；框架导入产生的4个data模板移到忽略state，原运行文件/凭据未改。

剩余：用户启动后真实稳定性观察；若新日志有错误类别再针对取证。0真实生成/群发/启停；旧验收差额保留。Git：2026-10-17 18:50（Asia/Shanghai），内容提交`1bd9a9fb0e244b3833b5e50f7b63f14a6d7be47f`已推送origin/main，rev-parse/ls-remote完整SHA一致；检查点工作区干净。差异/编译/链接检查通过。保留的本机配置、secrets和state验证工件继续忽略；本段随后独立同步。Git不代表已启动或真实验收。
