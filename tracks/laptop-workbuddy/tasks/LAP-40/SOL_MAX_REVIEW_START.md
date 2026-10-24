# LAP-40 A4：Sol max复核入口

返回[项目入口](../../../../PROGRESS.md) / [A4交接](STAGE3_A4_HANDOFF.md) / [实施报告](../../../../reports/lap-40-A4-implementation-2026-10-24.md)。本入口只交接复核；当前尚未由Sol max审阅通过。

唯一工作根E:/CodexWS/QQbot_Snowluma，分支codex/lap-40-snowluma。先读PROGRESS、AGENTS、A4交接、A4计划和本次报告。用户已授权只实施A4，完成后交Sol max；**不自动B/C、不正常启动、不扫码、不派实施代理**。模型与推理档位由用户会话设置选择，本文不自动切换。

A4候选已实现并通过最终21命令矩阵；316模块/321语法、channel/control15项、15运行场景共用30项（压力34/pipe31）、正式provider10类、实际框架ACK13项、public兼容14项，不能累加重复用例。120ms helper的合法bind1336ms/窗口内12次helper；HTTP health121ms/1次、压力中238ms。全部I/O为合成，生产入口退出1且qualification=false。

先核Git与文件归属/额度；旧2901迁移文本和27 junction、官方71文件/ZIP已审摘要不变。新A4上游源/产物/测试/闭包仅在忽略runtime/snowluma-private；public只有原创报告和交接，不能仅在GitHub上宣称已看过private。未审早期稿保留a4-draft-archive，不运行旧prepare-a4.py/finish-a4.py/make-a4-check.py覆写候选。

私有入口与证据：src/a4-channel.mjs（异步broker/ALS/取消），src/a4-control.mjs（收到起3秒），src/a4-runtime.mjs，src/a4-actions.ts及a4-work/actions.ts；a4-source-manifest.json/a4-reviewed-overlay（424源/13 overlay）、a4-build-evidence.json（316图）、a4-integrity-evidence.json（完整摘要）、a4-final-evidence.json（21准确argv/退出码）。重放命令见实施报告；prepare-a4-reviewed.py --check只核验，--prepare拒绝覆盖已有目录。独立复核按决定性合同选择重放，不为计数重复全量。

优先检查：

1. helper并发1/2秒/输出限额/实际child PID+自捕获created/parent与完整close；取消kill请求不作退出证明，unknown封闭且不再spawn。短scope100ms与持续逻辑许可不混淆，retained事件转换及取消后回调不越权。
2. bind/health/stop使用原HMAC/seq/nonce；request从收body前计3秒；长期ownerLease不捕获旧scope；失败/取消bind同步quiesce，合法stop ACK不因先关channel误丢。
3. HookSession准入前不复制正文，队列16/256KiB/64KiB且在2MiB预算内；纯投影/黑名单/授权群早于完整协议、store/logger/引用回拉。登录/断连代际清队列/许可，旧项不恢复。
4. gate目标和socket代际固定；RPC16 pending/固定动作/参数冻结。实际injectHookProcess、connectSocket、writeControl取队列和Highway connect/write必须fresh后同turn检查；messageSubmitted紧邻实际write，只提交一次。
5. 长图像跨scope成功与中途撤销、前拒绝/unknown/partial准确ACK；实际gate/CQHTTP/AstrBot/TaskStore/Router/MemoryStore不重发，不晋升未知部分。

复核结论应分已实现/合成通过/max已接受/真实未验。发现合同内缺陷可按既有授权修复并定向验证；改变方案的能力缺口回规划。无论复核结果都停在A4，B资格代码、G1可信机制、干净QQ/真实probe另待用户指令。原C工作根与原E运行根只读，local/persona不改，原31B等差额不抹掉。
