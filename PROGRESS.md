# QQ bot项目入口：SnowLuma主线

本文件是唯一项目进度入口，不另建根HANDOFF。更新：2026-10-25（Asia/Shanghai）。

## 当前结论

QQ以后以 `E:/CodexWS/QQbot_Snowluma` 的官方原版SnowLuma路线为主线。用户已确认Snow可运行、bot在QQ群中可回复；LAP-40最小文字首试按用户现场确认通过。接入与日常启动脚本已实现/离线通过，未把用户反馈扩写成免扫码、停止或长稳完整验收。

LAP-41工作区整理与使用对照已完成：uv报告清除38,269个缓存文件约626.1MiB，5份临时网页快照和退役自启提示入口已删除，四份旧入口说明归档。约1.25MiB字节码缓存因自动审批拒绝删除而保留。25份运行保护文件摘要相同，未改生产代码、模型/人设/触发或其他业务配置，未启停bot。

## 从哪里继续

1. 使用bot：[日常操作](SnowLuma使用说明.md) / [与旧NapCat bot的使用对照](docs/BOT_USAGE_COMPARISON.md)。
2. 项目接续：本文件 → [AGENTS](AGENTS.md) → [QQ主线HANDOFF](tracks/laptop-workbuddy/HANDOFF.md)和[TASKS](tracks/laptop-workbuddy/TASKS.md) → 当前[LAP-41交接](tracks/laptop-workbuddy/tasks/LAP-41/HANDOFF.md)。
3. 故障找文件：[目录与日志](项目目录与日志说明.md)。只按实际问题检索，不从历史清单自动展开新任务。

## 路线和边界

- 当前链路：官方原版SnowLuma → OneBot gate → AstrBot/router → gateway/CodeBuddy CLI。聊天大脑和共用业务模块继续复用；不维护Snow私有分支。
- NapCat旧根 `E:/CodexWS/QQbot` 保留，本轮不修改或启停；本根的NapCat兼容代码/测试暂留，不能删除仍被导入的模块。主线调整不等于改变代码中的兼容默认值或切换现有local。
- local/persona、秘密、图库、登录资料、会话/任务/清理台账和日志保留；不通过删state、lock或uv.lock解决运行问题。
- 私聊关闭、授权群、当前触发/额度/模型/人设、单次尝试、工具隔离不变。账号屏蔽按用户决定由QQ客户端拉黑；不新增内部零日志/存储证明系统。
- 只停止有创建身份依据的本项目进程；禁止按QQ/Node/Python进程名批量结束。QQ/Snow外部手工实例不接管。
- 新功能先规划，按AGENTS由用户选择medium实施；模型/推理档位不自动切换，不派代理。维护在当前授权范围完成。
- 旧私有B/C停止；A4代码、产物、证据原样保留，不复核、不重跑。资格/proof/probe、原生数据证明、72h/7天不作当前使用前置。
- Git沿用长期授权：只提交归属且已检查的修改，push后核对远端；Git交付不代表真实验收。

## 工作线索引

| 工作线 | 状态/最新依据 | 接续入口 |
| --- | --- | --- |
| QQ主线：SnowLuma及共用bot业务 | active，日常使用；LAP-40用户文字首试成功，LAP-41整理/对照完成 | [HANDOFF](tracks/laptop-workbuddy/HANDOFF.md) / [TASKS](tracks/laptop-workbuddy/TASKS.md) / [LAP-41](tracks/laptop-workbuddy/tasks/LAP-41/HANDOFF.md) / [LAP-40](tracks/laptop-workbuddy/tasks/LAP-40/HANDOFF.md) |
| 家庭5070备用模型路线 | 历史记录为接入已实现/离线及元数据通过、真实生成未验；本轮未重查，不自动切换后端 | [HANDOFF](tracks/local-5070/HANDOFF.md) / [既有选型](tracks/local-5070/MODEL_SELECTION.md) |

`tracks/laptop-workbuddy` 是保留的历史目录名，当前承担QQ主线和共用网关交接，不表示仍以NapCat或WorkBuddy界面为主路线。所有旧任务的状态/验收差额在TASKS与各任务HANDOFF保留，不重命名整棵目录。

## 当前使用快照与未验证范围

本轮只读比较两边磁盘设置与最近启动快照：共同使用deepseek-v4.1-flash/low、free、adaptive最多3条、16轮历史，persona内容相同。Snow新根的表情登记为0条，旧NapCat为7条；没有在本轮迁移。详细值与来源见[使用对照](docs/BOT_USAGE_COMPARISON.md)。

网页材料读取开着，搜索质量门槛仍未通过；看图、B站字幕、成员增强、长期群记忆、关注增强目前关着。旧18/28/29/31B等验收差额继续按各自任务保存，既不晋升为通过，也不自动转成当前待办。微信是独立 `E:/CodexWS/WeChatbot` 项目，本次不推进。

## 历史与检查点

- 接入实现：89b7dfae；桌面入口实现：1aabe532。
- 用户确认文字成功：3d3361e，仅指用户现场说明，未独立读取原始模型/发送ACK追踪。
- LAP-41整理前基线：3d3361eaecae1e342bb05412c6af3ccdf6b4417b。
- [整理清单/实际结果与回滚](tracks/laptop-workbuddy/tasks/LAP-41/CLEANUP.md)。
- [旧全量进度快照](docs/archive/pre-snow-mainline-2026-10-25/PROGRESS.md) / [旧工作线交接](docs/archive/pre-snow-mainline-2026-10-25/LAPTOP_HANDOFF.md) / [旧README](docs/archive/pre-snow-mainline-2026-10-25/README.md)。

历史页面可能记载当时“缺环境/真实未验/旧私改待实施”，只能按记录日期理解；当前状态以本入口及活动交接为准。
