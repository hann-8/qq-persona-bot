# QQ bot：SnowLuma主线

当前活动工作根是 `E:/CodexWS/QQbot_Snowluma`。官方原版SnowLuma负责QQ接入，既有AstrBot/router、gate和CodeBuddy网关继续负责这只bot的聊天逻辑。用户已确认Snow可运行、QQ群内可回复。

项目进度只从[PROGRESS](PROGRESS.md)进入；日常操作见[SnowLuma使用说明](SnowLuma使用说明.md)，旧NapCat用户先读[两套bot的实际使用对照](docs/BOT_USAGE_COMPARISON.md)。

## 日常入口

| 要做什么 | 双击 |
| --- | --- |
| 启动bot、专用QQ/Snow并打开管理页 | 启动机器人.cmd |
| 看项目组件、QQ通道和模型状态 | 查看状态.cmd |
| 打开Snow管理页 | 打开SnowLuma管理页.cmd |
| 在本机查看官方启动日志/初始管理密码 | 查看Snow本机日志.cmd |
| 停止本根项目及脚本创建的QQ/Snow | 关闭机器人.cmd |
| 遇到“模型进程清理未确认完成”后人工恢复 | 先按提示关闭，再使用清理模型阻断.cmd；详见[目录与日志](项目目录与日志说明.md) |

首次在官方页面选择本根专用QQ并完成登录/扫码；脚本会准备本项目OneBot连接，无需手填JSON/token。关闭启动窗口不会停止后台bot。手工启动或归属不清的QQ/Snow会被保留，需从对应窗口正常退出。

## 你熟悉的聊天习惯

当前两套配置的非秘密业务值一致：CodeBuddy CLI / deepseek-v4.1-flash、free参与、真实@进入原回应流程、自然分条最多3条、16轮历史上限、私聊关闭；人设文件内容也一致。换QQ接入不自动换模型、额度来源或人设。

当前已开启网页材料读取与表情选择；但新根图库尚无登记，暂时没有可选受控表情。B站字幕、看图、成员/@增强、群长期记忆和关注增强未开启。开关与已验证程度请以[实际对照](docs/BOT_USAGE_COMPARISON.md)为准，不把Snow本身支持的协议能力当作这只bot已接入的能力。

## 配置与数据

配置入口见[配置索引](config/README.md)，人设位于独立的 `config/persona.md`。本机配置/token、QQ登录资料、图库、聊天库、任务台账和日志继续忽略，不提交Git；本次整理没有改动或迁移它们。

新旧两个工作根各自保存会话/状态，不会因为模型和人设相同就自动继承旧聊天。需要迁移时再明确选择数据与范围；当前不复制旧state或QQ登录数据。

## 开发与历史

QQ的新工作默认围绕Snow主线；NapCat仅保留旧工作根、兼容代码和历史参考，不在本次整理中重装或启动。代码中provider的兼容默认值保留，实际使用由现有local显式选Snow，不因文档整理改运行行为。

- [主线交接与任务台账](tracks/laptop-workbuddy/HANDOFF.md)
- [LAP-40接入/日常入口与用户文字成功](tracks/laptop-workbuddy/tasks/LAP-40/HANDOFF.md)
- [LAP-41整理与删除清单](tracks/laptop-workbuddy/tasks/LAP-41/HANDOFF.md)
- [整理前的README与其他入口快照](docs/archive/pre-snow-mainline-2026-10-25/README.md)

旧任务、报告、A4代码/产物/证据均保留；旧B/C私改路线停止。它们不是当前部署步骤，不再作为首次试用的前置要求。开机自启已弃用，退役提示入口已列入清理；日常手动启动。

本次用户确认覆盖“Snow可运行、QQ群可回复”，不自动代表免扫码、停止、多功能或长稳完整验收。后续按实际使用反馈处理，不新增无故障的补证任务。
