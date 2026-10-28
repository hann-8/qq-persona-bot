# LAP-43：原生联网仅两工具，给medium的落地prompt

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [HANDOFF](HANDOFF.md) / [当前原生联网合同](CLI_WEB_PLAN.md)。

旧四项统一prompt已完成，其代码和证据保留。本文件现在仅续用户已选定的CLI WebSearch/WebFetch，按既定分工交下一轮medium；本次规划不实施、不启停。用户无需重新授权同一范围。

```text
你是gpt-6.1-sol/medium。在 E:/CodexWS/QQbot_Snowluma 从已核对的main接续LAP-43原生联网。
先读PROGRESS、AGENTS、工作线HANDOFF/TASKS、43 HANDOFF及CLI_WEB_PLAN.md和本MEDIUM_START。以CLI_WEB_PLAN覆盖旧PLAN中当前CodeBuddy的Python联网前置和全工具禁用假设；旧表情、owner、输入等已交付，不重做。

用户已确认第一批仅开放WebSearch、WebFetch，并由CLI自行判断何时联网；请这一轮完成实现、启用和部署供用户QQ群自行实测，不再只交计划或离线分支。

按CLI_WEB_PLAN实现：
- web.engine新增gateway/codebuddy_cli兼容字段，本机改codebuddy_cli；native模式绕开Python关键词/RSS/HTML/日期预筛，不丢失WebRunner承担的取消/stop、图片成员上下文及最终v2处理。
- 固定工具白名单只有WebSearch/WebFetch，显式许可配合dontAsk，保持MCP空和其他工具禁用；必要时用NoDefer两项直接暴露，不能带ToolSearch/DeferExecuteTool、Read、命令或Agent。当前web两开关true保持。
- 同步StreamParser与SDK tool.call/turn.step：合法中间工具过程留在CLI内部、只发送最终JSON；每任务最多3个工具调用/4主步骤，维持90秒总deadline，单结果8000/合计12000 UTF-8字节及每步48000可见政策，真实字段/定义/结果入账。不自动重启、换模型或增加预算。
- 修正代码生成能力政策，允许模型按需联网、用户明确不联网优先；只引用实际工具结果URL，不把失败装成功。用过web时单条answer、不夹表情、不写长期网页记忆；普通聊天/原图/表情和唯一操作者继续可用。
- 复用现有lap43_operator_trial配对当前完整binding及native工具策略，适配图像+有限工具往返，更新必要收据/预算接点；不伪改旧active/报告、不缩小签名、不静默关识图、不新开IQ/评分项目。

先在TASKS登记当前唯一实现/部署session及精确路径后重读，在适用隔离工作树/codex分支实现，保留正在运行的生产根。基本检查只覆盖两工具白名单/第三工具拒绝、计数并发/重放、每步预算和中间事件隔离、图片上下文及原暂停发送栅栏；复用现有边界替身和当前CLI零生成接线，不跑全库/旧六例或agent主动真实模型/群发测试。

用户已授权本项必要的当前Snow受管停启、main合入、本机engine及上限保存、当前识图试用记录配对更新；检查后同轮部署并正常启动，确认实际工具/配置加载及通道，交用户自己试。只有本项目创建身份可证的进程可操作；不安装/登录、不改全局CLI/旧根/家庭主机，不碰persona、图库或记忆内容。

保持DeepSeek/low、当前账号credits来源、48000/其他预算、free和群权限，不新增提供方/付费API，不自动回退Python或另一模型。实际CLI工具服务不可用时报告具体错误并交付独立成果，不把本地失败提示说成联网已成功；能修就当轮修，技术回滚按本任务配对旧代码/config/active，不删unknown或覆盖后续改动。

同步必要交接/配置说明，按长期授权只提交已检查本任务修改、push main并核对实时SHA。最后简要说是否已部署、实际允许哪些工具、用户怎么试及具体未验/阻断。不要重开规划或重复索取本项部署授权。
```
