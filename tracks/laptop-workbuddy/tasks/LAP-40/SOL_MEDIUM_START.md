# LAP-40：可直接交给Sol medium的最小接入指令

返回[项目入口](../../../../PROGRESS.md) / [当前交接](HANDOFF.md) / [最小计划](PLAN.md)。2026-10-25，Asia/Shanghai。用户在新会话选择`gpt-6.1-sol / medium`后发送以下文字；当前文档会话不实施。

```text
实施LAP-40官方原版SnowLuma的最小OneBot接入，只做到可交用户启动并试用目标群文字收发。

工作根：E:/CodexWS/QQbot_Snowluma
分支：codex/lap-40-snowluma
先读PROGRESS顶部、AGENTS、工作线HANDOFF顶部/TASKS的LAP-40行，再读tracks/laptop-workbuddy/tasks/LAP-40/HANDOFF.md及PLAN.md；只按实际缺口检索，不重读全部历史。

先核Git状态/分支和文件归属，登记本session、开始时间和涉及文件，写后重读。一个session只做本任务；不要派子代理或切换模型。

最新决定已整体取代旧私有改造规划：使用官方原版SnowLuma现成OneBot连接既有gate/AstrBot/gateway/CodeBuddy CLI。停止旧B/C，不复核/重跑A4，不改A4代码/产物/证据，不修改SnowLuma内部。账号屏蔽由我在QQ客户端拉黑；不要新增内部过滤、零日志/存储、资格/proof/probe或原生数据证明系统。

优先修项目侧已确认阻断：当前Snow启动和gate入口调用无条件拒绝的transport_owner.require_runtime，channel_ready还依赖私有健康合同。复用现有provider选择与业务组件，让显式snowluma走官方反向WS及正常OneBot状态/收发路径，默认napcat保持。不得伪装成NapCat或填写proof=true放行；旧私有控制/健康/构建不应成为新路径依赖。优先查scripts/manage.py及src/qqbot_gateway下qq_transport.py、onebot_gate.py、config.py，只有实际调用阻断才扩到其他文件并登记归属。

先按官方正常说明核对启动方式和OneBot配置，官方端由操作者正常启动，不新增注入/进程接管/自动恢复服务。复用本根gate（例ws://127.0.0.1:6200/ws）、AstrBot上游及现有token/账号/授权群校验。保留私聊关闭、当前触发模式、既有模型/额度/人设和单次尝试。只有握手、事件或发送回执实际不兼容才做外部薄适配；其他旧功能按实际需要恢复，未确认问题不建新任务。

只对必要改动做针对性离线/合成验证，验证文字事件和发送回执能通过现有链路及基本账号/授权群/私聊边界；不跑A4矩阵或完整旧功能/极端竞态/性能/72h/7天。本次不安装、不启停/登录/扫码、不调用真实模型、不发群消息、不改local/persona，不修改E:/CodexWS/QQbot原运行根或旧C工作根。新根材料/依赖/配置只列实际缺项，秘密仍留忽略文件。

完成后给准确的准备项、官方QQ/Snow启动停止方式、项目gate/AstrBot/gateway启动停止命令、一次目标群文字试用步骤和脱敏故障材料位置。若尚不能给出可操作命令，只报告实际阻断，不用未验前提堆新清单。代码/合成通过和真实未验分开；真实安装/启动/登录/模型/群操作由我另行授权或亲自进行。

同步PROGRESS、工作线HANDOFF/TASKS和LAP-40交接。沿用长期Git授权，只提交检查过的本任务修改，commit/push并核对远端SHA，报告剩余本机差异。交付后停止，不自动推进旧B/C或其他功能。只有实际必须修改SnowLuma内部才能继续时，记录具体阻断和外部尝试结果交回我决定，不自行恢复私有分支。
```
