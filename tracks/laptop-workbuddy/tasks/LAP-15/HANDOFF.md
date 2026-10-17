# LAP-15：精简人设与场景表达

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md)。继承[AGENTS](../../../../AGENTS.md)，按[LAP-14 PLAN](../LAP-14/PLAN.md)第4/9/10节和[实施指引](../LAP-14/IMPLEMENTATION_GUIDE.md)第3节执行。

状态：已实现 / 离线通过，真实加载与P01未验。领取记录：in_progress，2026-10-17 11:06（Asia/Shanghai）领取；session标识/标题：LAP-15-persona-implementation / LAP-15精简人设与场景表达。用户只授权本任务实施，不领取LAP-16/17/18。会话模型/档位由用户设置，未自动检测或切换。

目标：备份当前完整人设，整理唯一角色正文/场景表达；保留固定能力政策和单条纯文本，组合目标≤6000 UTF-8字节。router/configure共用compose_persona已存在，保留并离线核对一致。验证纯文本字面量、版本迁移、工具隔离及本人历史预算，实际框架合成回环；不启停真实bot、登录、真实推理或群发，不操作PC。

开始main仅config/persona.md有用户245行增量；原文SHA256：c55c51db10a0d9c3d147638763ffa10e16c0be9daffa4ec80bfd4037417120b7，15984字节，与LAP-14记录一致。已核对完整备份：忽略的state/persona-backups/c55c51db10a0d9c3d147638763ffa10e16c0be9daffa4ec80bfd4037417120b7.md，完整字节核对后才整理。提交只包含本任务整理后正文，不提交原始材料/备份。

初始预计文件范围：config/persona.md、src/qqbot_gateway/persona.py及必要人设验证；reports/lap-15-2026-10-17.md；本HANDOFF、PROGRESS.md、tracks/laptop-workbuddy/HANDOFF.md及TASKS.md，以及确有合同变化的README/UX_PLAN/ACCEPTANCE。既有router/configure共用路径无需为改动而改动。其他任务/运行配置不修改。

已完成：原文完整备份/hash/忽略核对；40行唯一角色正文、9个人工场景例；固定政策及router/configure共用实现原样保留，实际表达式逐字组合一致。新角色2753字节，固定政策865，组合3618（目标≤6000）；persona版本fatfish-chat-ead23a5d4d15278e。完整原文diff仅在本机state/persona-backups/lap15-original-to-current.diff，可审阅且不提交旧用户材料。

验证：108项单元通过；verify_lap11.py实际框架5组合成保存/发送回环通过；verify_g4_routing.py实际框架入口/本人历史/隔离/版本新会话且旧历史保留通过。新真实prompt预算/模板排查及两调用路径一致性通过。结果及准确命令见[报告](../../../../reports/lap-15-2026-10-17.md) / [结构数据](../../../../reports/lap-15-offline-2026-10-17.json)。本轮未真实bot启停/探活/登录、模型或群发，未SSH/PC操作；框架测试默认data副作用已移入忽略state。当前真实bot状态未知。

最终修改：config/persona.md、README.md、PROGRESS.md、活动线HANDOFF/TASKS/UX_PLAN/ACCEPTANCE、本HANDOFF和两份lap-15报告；未改运行配置、模型/预算、代码或发送路径。开始仅persona用户增量，已按用户授权整理且原文完整备份，不夹带其他session修改。

剩余：真实加载版本核对、P01三类各2次模型观察及用户接受/真实QQ；不写完整验收通过。模型/账号/预算、真实@、单条、工具隔离保持；LAP-10/13和原真人差额保留。下一步由用户指定LAP-16或协调LAP-15真实范围；不得自动重启/推理或领取其他任务。加载后下一请求会开始新上下文、旧历史保留。回滚步骤见报告。

Git：本任务10份文件已完成归属/diff/129个本地链接/hash/忽略检查；git diff --check通过。按长期授权提交/推送，交付结果随后记录。
