# LAP-43：原生联网与删减自建层的medium指令

返回[43交接](HANDOFF.md) / [当前最小方案](NATIVE_WEB_PLAN.md) / [PROGRESS](../../../../PROGRESS.md)。旧B/R2/R3/C不再自动续跑。以下为用户后续可复制的实施指令，本规划轮不执行。

```text
在C:/Users/yutha/.codex/worktrees/lap-43-stage-a/QQbot、codex/lap-43-stage-a续LAP-43。你是gpt-6.1-sol/medium，先读PROGRESS、AGENTS、工作线HANDOFF/TASKS、43 HANDOFF及NATIVE_WEB_PLAN/NATIVE_WEB_MEDIUM_START。先登记session/时间/精确文件并重读，再修改；本轮只代码、离线、文档和Git，不操作生产main或运行。

按新最小方案复用当前CodeBuddy CLI会话原生WebFetch；核对当前模型/headless是否提供WebSearch，提供才按独立search开关接入。不要继续修自建Bing/提取/gist/日期质量流水线或重跑旧公共批次，也不要接新API/账号/付费后端。

同时修改runner的--tools/--allowedTools/本次deny派生、ResultParser init及工具过程接受规则；只放开明确只读联网工具，其他工具/MCP仍拒绝。保留dontAsk、严格空MCP、无全局设置、原账号/model/low；不启用default全工具或bypassPermissions。中间进度和工具JSON不发QQ，只用最终result走原投递链。允许原生联网会话最多8 CLI轮次，保留原timeout、一次CLI尝试、无自动重试；如实说明内部可有多次模型/Fetch，不能宣称等于一次远端生成。

CodeBuddy使用原生工具时移除外层WebRunner抓取接线，web.provider使用codebuddy_native；web.enabled控制Fetch，search_enabled控制Search，模板默认仍关闭。本轮不写生产local。Ollama聊天保留，不为它重造联网、不自动切模型。图片专用guard先保持现有无工具路径，保留R1自然图片政策，图+URL不伪称完成联网。

按引用审查删减自建联网增量和只为它新增的probe/测试/writer；报告/失败/状态证据留档。无其他活跃引用的worker/date/gist模块可删，有共享引用则最小保留。不得删除图片共用PublicHTTP/public_network、配置/vision校验或owner/暂停/输入/表情/记忆等独立成果，不用整分支reset/revert覆盖别人的工作，不改用户persona或CLI/框架源码。

只做必要定向验证：原生会话参数与工具白名单、init/中间工具消息/最终结果、其他工具拒绝、原无工具/图片兼容、最终发送与暂停/取消。复用既有Harness/底层替身，不实际调用CLI/模型/QQ/SSH/公共probe/启停。新源码影响vision绑定时按现有43配对接线处理，禁止伪改旧active；真实校验等下一轮用户选中运行。

把新增/删除文件、验证结果和未证实能力写入43交接及必要实际报告，同步PROGRESS/工作线HANDOFF/TASKS。只提交本任务已检查归属文件，commit/push隔离分支并核对远端后停止。若仅Fetch可用就交付URL阅读，明确原生Search缺口，不为了搜索再建第二套系统。
```

运行阶段另由用户选定：一次受管停机/配对部署/正常启动，实际bot两题（公共URL、无URL近期信息）；必要的既有1次大图+1条群图片版本回归单列，最多4次受控请求尝试，内部工具步骤另计。当前没有这项运行授权；不重放旧R2或旧C。表情/owner的剩余真实验收另按实际缺项补，不重复已完成动作。
