# LAP-40：Sol medium最小接入指引

返回[项目入口](../../../../PROGRESS.md) / [当前计划](PLAN.md) / [当前交接](HANDOFF.md) / [可复制指令](SOL_MEDIUM_START.md)。2026-10-25，Asia/Shanghai。

原分阶段私有改造实施指引已被用户最新决定整体取代。旧B/C、A4复核、私有过滤/资格/proof/probe及长稳前置均停止；历史实现和证据保留，不继续补齐。

用户另开`gpt-6.1-sol/medium`后发送[SOL_MEDIUM_START](SOL_MEDIUM_START.md)，只实施官方原版SnowLuma的OneBot外部接入：解除现有Snow provider对私有入口/健康的依赖，复用gate/AstrBot/gateway/CodeBuddy CLI文字链，完成必要针对性验证及明确的首次试用步骤。无需另建阶段或新任务编号。

优先涉及`scripts/manage.py`、`src/qqbot_gateway/qq_transport.py`、`onebot_gate.py`、`config.py`，仅因实际阻断再查其他调用点及配置说明。保留默认NapCat；本根显式Snow选择才走官方接入。A4及`runtime/snowluma-private/`不修改、不导入新路径。

当前仅文档，没有实施授权被自动执行；后续代码/合成验证可按用户发送的指令推进，真实安装/启停/登录/模型/群操作仍由用户明确授权或亲自进行。原运行根、local和persona不动。只提交本任务归属修改并push，核远端SHA；完成后停止，不自动恢复其他功能或旧B/C。
