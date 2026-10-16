# LAP-12：一键启停、分层状态与QQ共存

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md)。合同：[UX_PLAN](../../UX_PLAN.md)第7节及U15—19；继承AGENTS边界。

状态：已实现/离线及本机无推理启停通过；最终后台已关闭，真实人工差额保留。2026-10-16 23:43（Asia/Shanghai）领取。session“LAP-12启停状态实施与最终停机”；用户授权按已有计划实现，完成后关闭后台bot，由用户自行试用。沿用本会话自动提交/推送授权；基线ef605bf，开始时工作区干净。会话模型档位由用户设置，未声称自动检测或切换。

文件归属：scripts/manage.py、process_host.py、旧ps1兼容入口，根目录启动/关闭/状态cmd；新增src/qqbot_gateway/lifecycle.py（实例停止标记/进程身份）；onebot_gate.py health、model_gateway.py错误历史状态、router停止准入；tests与必要报告/README/进度台账。本session拥有项目实例启停和这些文件写入；不并发操作，不改日常QQ/WorkBuddy配置，不调用真实模型或群发。

顺序：实现OS级start/stop互斥、幂等/失败身份保留/动态后代清理；实例绑定停止准入与5秒有界退出；gate仅元数据健康与隔离echo状态查询；模型当前错误/历史错误；cmd定位/提示、旧入口兼容；离线故障及路径回归；必要本机无推理状态/启停隔离验证；最终明确关闭所有受管进程并核对端口/身份，交还用户。

验收：U15路径和入口、U16并发/幂等/PID复用/冲突/清理失败、U17登录未知与恢复/当前历史错误、U18停止期间准入/后代/不重发、U19仅本项目进程操作。人工扫码、真实QQ基本操作、真实推理/ACK中的停机不冒充离线通过；若需用户参与明确记录。LAP-10原生窗口及CLI内部压缩能力缺口保持，不扩大方案或自动换后端。

回滚：仅本任务文件，停止后恢复旧入口/管理逻辑；不删数据库/runtime，不丢已有未提交变更。旧实例无新停止钩子的兼容限制需记录，不能假装已动态升级。

检查点：已读AGENTS、PROGRESS、工作线/TASKS及UX_PLAN相关合同；完成归属登记后重读，尚未变更实现或启停实例。

实施检查点：统一OS锁、start/stop幂等、启动失败仅回收本次身份、动态后代快照及清理失败保留身份、实例停止准入已落地；gate独立get_status echo/心跳online/过期unknown、模型当前/历史错误、双击cmd已实现。97项离线测试通过；新增测试发现SQLite上下文未主动close造成Windows文件占用，已修复并全套通过。NapCat锁定bundle的heartbeat.status.online字段已只读核对。旧实例仍为未加载新代码版本（gate无health），本机无推理读数为ready、active=false、queue=0、CLI累计7，任务completed=9/failed=1，非新版本验收。

下一步真实无推理验证由本session独占：先按旧身份停止现存bot，再以本次实例绑定停止标记从首个子进程起保持暂停准入启动新版本，核对组件/QQ分层状态、幂等入口、日常外部进程身份，最后关闭新实例并核对受管身份及端口。禁止为验证发送群消息或模型探针；真人QQ操作/实际ACK中停机与登录恢复仍按证据留差额。

最终检查点：2026-10-16 23:56（Asia/Shanghai）。完成文件：manage/process_host、启动/关闭/状态cmd、lifecycle、config锁提示、gate/model health、router停止准入/就绪实例ID、verify_g4_routing与tests/test_lifecycle/test_model_gateway/test_onebot_gate，README/UX_PLAN/ACCEPTANCE/PROGRESS/TASKS/工作线及本交接、reports/lap-12*。97项全套测试通过；末次数据库失败提示收紧后12项生命周期单独通过；实际AstrBot两个离线脚本通过。三cmd中文空格路径/外部CWD调度通过。

真实无推理检查：旧实例按身份停止后五端口全关；新版本从第一子进程起paused=true，实际组件running、router_ready=true、waiting_login、not_probed、cli_attempts=0。重复start实例ID不变。最终通过根关闭cmd停机，旧Stop.ps1重复停机通过；受管身份全0、五端口无监听、外部15身份全存活，任务库仍completed=9/failed=1。参考[报告](../../../../reports/lap-12-2026-10-16.md)和[本机证据](../../../../reports/lap-12-local-2026-10-16.json)。

下一步：用户自行双击启动、在本机NapCat按需登录，再查看状态/授权群真实@；当前无需登录，后台保持关闭。不自动重启或推进其他任务。真实登录后恢复、QQ基本操作、真实推理/ACK中停机、人设P01与旧文本验收待用户参与；LAP-10能力缺口仍先回规划。提交推送按已有授权执行，不能据本机准备/暂停准入加载把完整真实验收写通过。

交付前检查：105个本地文档链接全部存在，git diff --check通过；当前后台仍为stopped，真实模型/群消息均0。提交/推送按本会话已有授权执行，完整真人验收差额不变。
