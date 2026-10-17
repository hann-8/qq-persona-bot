# LAP-22 free真实框架发送故障修复

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md)。继承AGENTS与LAP-19/20/21既有合同；已规划范围内修复。

2026-10-17 18:01（Asia/Shanghai）领取。session `LAP-22-free-framework-delivery`，标题“free模式兜底回复故障修复”。初始git status干净；归属：router main、verify_lap20及必要新增回归、任务交接/台账/PROGRESS/工作线。不开新功能，不修改本机settings/persona，不启停/登录/调用真实模型/群发。

目标：复现free生成完成却进入本地兜底的问题，修复实际框架结果装饰/发送链，以合成runner验证；保留silent/@、ACK、黑名单和工具隔离。

已核对：用户报告free每次兜底；只读本机选择ollama_ssh/free/web开启/memes关闭。健康页ready、两次生成（mention和ambient各一次）、last_error为空。此为已有运行元数据，不是本session生成；未读取群正文/凭据。

2026-10-17 18:05（Asia/Shanghai）完成代码修复及离线验证，真实QQ/运行加载待验。根因与修复见[报告](../../../../reports/lap-22-2026-10-17.md)：空result_chain使实际框架跳过发送装饰，原测试手动补链掩盖问题。保留可信canonical载体，silent/invalid完成钩子收尾，ACK/guard不变。

验证：修复前新增实际run_agent用例失败（speak/ambient/0发送）；修复后207单元、132群框架（含24实际run_agent生命周期）、136媒体回归通过。命令/日志/安全JSON见报告。只读现场元数据是用户已有运行证据，不作完整真实验收；附日志409为既有连接冲突，重复客户端/旧连接原因未证实。

修改文件：plugins/qq_router/main.py、scripts/verify_lap20.py、新scripts/verify_lap22.py、reports/lap-22-2026-10-17.md与两份安全JSON、本HANDOFF、TASKS、PROGRESS、工作线HANDOFF。旧报告未覆盖。单一session归属，未夹带本机资料。

剩余：用户按项目关闭/启动入口重启加载后验证free/@回复；本session不启停/登录/真实模型/群发，不改配置/人设。若仍有409须另核对受管连接身份，不能按进程名批量终止。保留18搜索/旧真人差额。

Git交付：2026-10-17 18:06（Asia/Shanghai），内容提交`a1c19e248fac6ceaf45f44e454fa88954b1148f7`已推送origin/main，rev-parse与ls-remote完整SHA一致，交付检查点工作区干净。链接/报告合成标记/compileall/提交差异检查通过；本段随后独立同步。保留本机忽略配置、secrets和state日志，无其他任务差异。回滚无schema迁移，沿用pending/unknown保护；回退空链修复会恢复故障。
