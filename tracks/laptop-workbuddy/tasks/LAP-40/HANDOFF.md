# LAP-40 SnowLuma替换试运行详细规划

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承AGENTS。

状态：详细[PLAN](PLAN.md)与[分阶段实施指引](IMPLEMENTATION_GUIDE.md)已完成，尚未实施。用户要求SnowLuma替换试运行，长期运行优先，允许branch；随后授权根agent逐步调用`gpt-6.1-sol / medium`实施复核。规划阶段仅只读源码/元数据与6份文档，0代码/配置/安装/依赖/注入/启停/登录/模型/群/SSH操作。

session `LAP-40-SnowLuma-trial-plan`，2026-10-24 01:19（Asia/Shanghai）开始；基线main/66eea49623b76766e0569614207c80c78e57115f，工作区干净。已按用户授权新建`codex/lap-40-snowluma-trial`；本轮仅该分支规划，保留main和原运行状态，不声称自动检测或切换会话模型/档位。

规划归属：本HANDOFF、PLAN.md/IMPLEMENTATION_GUIDE.md，PROGRESS、工作线HANDOFF/TASKS，共6份Markdown。一个session仅推进LAP-40，LAP-39已完成调研作为证据来源，不抹掉其故障、o3候选及旧验收差额。实施时根agent独占3个共享入口，medium在隔离worktree按阶段领取代码/测试/40交接和报告，不并行覆写。

当前依据：[LAP-39长期运行评估](../LAP-39/SNOWLUMA_ASSESSMENT.md)；固定SnowLuma v2.1.1/f8cb15c，已有good/接收停滞及Windows管道重接，但原版在gate前答复/补历史/存储，当前项目硬编码NapCat且忽略good。干净QQ/原生数据归属和发行协议的原生组件部署限制是前置门槛，不能用安装成功或静态源码代替证明。

计划包括：可选provider及旧快照兼容；原创策略/私有早期过滤、禁#sl/补史/原始日志/磁盘消息store；固定版本/原生部署许可/干净QQ数据证明；独立armed健康与gate统一栅栏；有界身份恢复、CLI/有限字段回滚与72h/7天分级。public只交付原创代码，私有上游修改/native不入Git。无真实前置时完成独立实现离线验证，不动原bot。

2026-10-24 01:58（Asia/Shanghai）规划完成；下一步文档校验→commit/push核对远端→调用medium阶段1，串行复核再推进2—5，只有真实前置齐全才6。不得把用户睡觉当成放宽登录/数据/许可条件的授权。阶段6需人工扫码则waiting_operator，不循环登录。

额度约束：用户明确5小时剩余<=5%时，无论规划或medium执行都交接并等待北京时间2026-10-24 07:10恢复；根agent负责heartbeat。01:50实际300分钟used=2%，remaining=98%，未触发等待；不得使用reset credit/购买额度。每阶段及长步骤之间检查，medium约15分钟核对。

规划验证：6份Markdown本地链接/代码围栏检查通过；git diff --check通过。差异仅上述6文档，未运行代码测试或上游测试，没有把静态阅读当本机通过。规划Git交付后由根agent记录精确提交/远端SHA并开始阶段1。

## 2026-10-24 02:03 实施准备

规划内容提交`09ad5a43c3be57d8cc736029357dcc710d7a4368`已推送origin/codex/lap-40-snowluma-trial，git ls-remote核对完整SHA一致，规划checkout干净。

受管worktree `C:\Users\yutha\.codex\worktrees\lap-40-snowluma-impl\QQbot`，分支`codex/lap-40-snowluma-impl`从精确规划提交创建；不含原runtime/state/secrets/local，不复制认证/私改。原`E:\CodexWS\QQbot`仍为规划分支，运行代码/状态未动。可借原`.venv/Scripts/python.exe`作为只读解释器，测试工作目录/PYTHONPATH必须指向隔离worktree，禁止写原运行目录。

阶段1登记：`LAP-40-medium-stage1-config`，开始02:03，待根agent调用gpt-6.1-sol/medium。归属qq_transport/provider、config.py/config_files.py/config_comments.py/必要布局操作、scripts/transport.py只读inspect、模板/配置说明、对应测试及本任务交接/报告。共享3入口只由根agent写。完成后交根agent审阅，不自行越级启动真实阶段。
