# LAP-10：模型、上下文、推理强度

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md)。继承全局边界；实施合同：[UX_PLAN](../../UX_PLAN.md)第3/5节，U08—12。

状态：**部分完成，独立实现/离线通过；high组合本机真实通过；原生窗口及强制压缩排除能力缺口待规划，未部署/未完整验收。** 2026-10-16 23:08（Asia/Shanghai）领取，23:22交接。当前会话由已交付LAP-09转入LAP-10，用户明确授权继续已有计划，沿用自主commit/push授权。基线9d8f64c，开始时工作区干净；未声称自动切换/检测模型档位。

范围：先零推理验证CLI 2.168.0控制/effort/autoCompact读取链，后共享配置参数、预算模块、router历史整轮裁剪、gateway复核、AstrBot框架限制对齐、配置菜单与离线/必要单次真实provider验证。原生窗口无法满足合同时按已规划分支明确不支持，不换后端或写用户全局设置。

文件归属：src/qqbot_gateway/{config,contracts,token_budget,workbuddy_cli_runner,model_gateway,errors}.py，plugins/qq_router/main.py，scripts/{configure_bot,configure_astrbot,verify_lap10}.py及必要新增探针/控制模块，settings.example、tests、README和进度/验收/本交接。当前session拥有这些任务文件和必要共享文档写入；真实验证使用独立临时请求/回环provider，不启停既有bot或发群消息，不读取登录凭据。

完成标准：U08—12分别记录离线、零推理控制、真实验证证据；上下文输入预算为UTF-8字节保守估算并说明限制，保持system/最新问题，历史按完整轮次裁剪；过大输入0CLI；无工具/记忆/压缩/自动fallback与一次CLI尝试边界不变。LAP-09真实验收差额继续保留。

最终证据、命令、统计口径和回滚见[验证报告](../../../../reports/lap-10-2026-10-16.md)。70项单元测试及实际框架路由预算回归通过；零推理控制通过；首次真实解析失败和修复后成功均保留证据。以下保留关键检查点，不用静态源码或配置回显冒充真实有效窗口。

零推理能力检查点：ControlExchange错ID/错误/部分/重复ACK离线3项通过；实际CLI在不发送user、不initialize账户的情况下get_available_models及set_config成功，2控制/0推理，进程树确认清理。元数据只保留能力字段，见reports/lap-10-control-2026-10-16.json。DeepSeek支持low/high/max、默认high、maxInputTokens=1000000；无原生窗口档位或effective session budget证据。contextWindow只ACK不判通过，按计划分支本任务不支持显式原生窗口。继续实现独立预算和effort；不新增后端、不改全局settings、不创造空白模型轮次。

后续检查点：已实现独立预算/历史裁剪/网关复核、模型effort菜单与当前能力前置核对，70项单元测试及扩展实际AstrBot router离线通过。真实provider首次因result后额外init被新增检查误拒，保留first报告；修复并补回归后第二次准确回忆，1CLI/1控制/1user消息。两次累计2条真实user请求，无自动重试/群消息，未启停实例或改实际配置。

新增能力缺口（需回规划）：locked bundle的compactWithResultOwned仅在force=false时服从autoCompactEnabled=false；checkAutoCompact/scheduleEmergencyCompact/PTL恢复调用force=true。不能保证大上下文下无额外压缩/内部重试，不能把1次CLI/1条user当作上游API严格1次。独立实现可保留，完整U09/U10/U12/大上下文单次推理合同未通过，保持未部署；不自行替换CLI/后端、修改bundle或发明禁用环境变量。后续由符合AGENTS要求的规划会话处理该缺口，未验原生窗口继续显式拒绝。

修改文件：上述范围及新增cli_control.py、config/cli-capabilities.json、tests/test_cli_control.py/test_cli_runner.py/test_token_budget.py、原test_config/test_model_gateway和verify_g4_routing回归；reports/lap-10*.json/md、README、UX_PLAN、ACCEPTANCE、PROGRESS/TASKS/工作线交接同步。没有修改settings.local.yaml、persona或运行实例；未读取认证文件/群正文。真实CLI3次启动（含零推理1次）、控制4次、user2条；上游API内部尝试次数未知，已将代码计数改名user_messages_sent。

下一步：先由符合AGENTS模型档位要求的规划会话处理强制压缩/内部恢复边界，不把它与原生窗口ACK混为已通过。LAP-10未完成差额不删除；LAP-09真实验收/原文本收尾任务继续保留。无需用户本轮登录；未自动领取LAP-11/12。提交/推送不等于部署。
