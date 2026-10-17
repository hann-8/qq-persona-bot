# LAP-16：一次生成与有限分条发送

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md)。继承[AGENTS](../../../../AGENTS.md)，按[LAP-14 PLAN](../LAP-14/PLAN.md)及[实施指引](../LAP-14/IMPLEMENTATION_GUIDE.md)第4—6节。

状态：已实现 / 离线通过，未实际启用/真实验收；2026-10-17 11:16（Asia/Shanghai）领取，session：LAP-16-adaptive-delivery / LAP-16一次生成与有限分条。用户明确继续实施本任务，工作区开始干净、HEAD 7d2f34e。仅本任务，不领取LAP-17/18，不启停/登录/真实推理/群发，不操作PC。

文件归属：src/qqbot_gateway/config.py、persona.py、model_gateway.py、task_store.py、新reply_plan.py/reply_delivery.py；plugins/qq_router/main.py；scripts/configure_astrbot.py、configure_bot.py、新verify_lap16.py；config/settings.example.yaml；相关tests；README、PROGRESS、活动线HANDOFF/TASKS/UX_PLAN/ACCEPTANCE、本HANDOFF和lap-16报告。保持当前人设、CLI/模型/账号/预算、真实@、工具隔离；本机settings不写，缺项single，adaptive仅显式配置。

顺序：配置/纯函数→网关与模式提示词→实际SDK元数据回环→账本/历史识别→事件作用域ACK受控发送→队列/停止/恢复→全框架故障矩阵→文档及commit/push。成功出口：合同C03—09有离线证据，真实/人工接受独立列。若元数据/ACK/锁无法可靠证明，按既定失败分支保持single、记录能力缺口，不绕框架或自动扩大方案。

当前检查点（2026-10-17 11:31）：配置/模式提示词、纯函数协议、网关可信metadata、delivery/part原子账本、事件bot包装器ACK、每群有界整轮锁/停止、收尾/启动历史修复均已实现。single默认及现有人设保持；本机settings未改。实际框架存在发送早于保存路径，修复放在原生成器最终收尾，lease覆盖，兼容两种顺序；这是已规划失败/顺序适配的实现细节。

40组实际SDK/runner/保存/装饰hook/原事件发送回环通过，含首/中/末失败、超时、缺失/重复ACK、metadata缺失/改写、重入/无默认补发；每组只一次合成runner。新增后续请求在前轮修复前等待，之后仅取确认前缀。另5组实际aiocqhttp反向WS API+原gate合成回包、同群两事件不交叉、短本地模型错误、startup在ready前修复均通过。报告结构结果在reports/lap-16-offline-2026-10-17.json，全为合成数据。原single框架5组及入口/历史/版本迁移回归通过。

测试迭代曾发现：fixture缺有效ID、SQLite fixture连接未关闭导致Windows清理失败，以及30ms合成ACK期限过紧；均修正测试设置，未改运行SDK/框架。一次停止/ACK竞争修正为保留已经捕获的成功ACK并终止后续。SDK回执测试必须走原gate过滤重复/未知echo，不用绕过gate的合成输入冒充现行路线。默认data副作用全部在scratch，禁用该验证子进程metrics；未接触真实runtime配置/聊天库。

最终检查点（2026-10-17 11:35）：[实施报告](../../../../reports/lap-16-2026-10-17.md)及[结构结果](../../../../reports/lap-16-offline-2026-10-17.json)已写，项目README/PROGRESS/活动线HANDOFF/TASKS/UX_PLAN/ACCEPTANCE同步。最终124项单元通过；40组框架回环、5组原SDK/gate、并发/本地错误/启动恢复/7项adaptive准入及single回归均通过。两compose实际调用逐字一致：single3618字节/原版本ead23a5d4d15278e，adaptive4563字节/bc6a7fd6a794f9be；均≤6000，现有人设正文hash保持LAP-15。

修改文件：src/qqbot_gateway/{config,persona,model_gateway,task_store,reply_plan,reply_delivery}.py，plugins/qq_router/main.py，scripts/{configure_astrbot,configure_bot,verify_lap16}.py，config/settings.example.yaml，tests/{test_model_gateway,test_configure_menu,test_reply_plan,test_reply_delivery}.py，reports/lap-16-{2026-10-17.md,offline-2026-10-17.json}，README/PROGRESS、活动线HANDOFF/TASKS/UX_PLAN/ACCEPTANCE及本HANDOFF。仅本任务归属；开始工作区干净，未改persona正文或本机配置/其他session内容。离线命令/结果及回滚步骤见报告；源代码差异和新文件已审阅。

剩余：commit/push及最终远端核对；真实范围须用户指定，由唯一实例负责人启用adaptive/协调加载并做真实QQ ACK/多人/停止/风格接受。当前真实bot状态未知，未启停/登录/推理/群发，未SSH或PC操作；真实启用/adaptive设置保存和群ACK/P01/人工接受未验。旧LAP-10及真人差额保留。会话设置由用户选择，未自动核验/切换。
