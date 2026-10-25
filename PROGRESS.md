# QQ bot项目入口：SnowLuma主线

本文件是唯一项目进度入口，不另建根HANDOFF。更新：2026-10-25（Asia/Shanghai）。

## 当前结论

QQ以后以 `E:/CodexWS/QQbot_Snowluma` 的官方原版SnowLuma路线为主线。用户已确认Snow可运行、bot在QQ群中可回复；LAP-40最小文字首试按用户现场确认通过。接入与日常启动脚本已实现/离线通过，未把用户反馈扩写成免扫码、停止或长稳完整验收。

LAP-41工作区整理与使用对照已完成：uv报告清除38,269个缓存文件约626.1MiB，5份临时网页快照和退役自启提示入口已删除，四份旧入口说明归档。约1.25MiB字节码缓存因自动审批拒绝删除而保留。25份运行保护文件摘要相同，未改生产代码、模型/人设/触发或其他业务配置，未启停bot。

当前接续为**LAP-42 Snow既有功能整合**：[详细计划](tracks/laptop-workbuddy/tasks/LAP-42/PLAN.md)与[完整medium指令](tracks/laptop-workbuddy/tasks/LAP-42/MEDIUM_START.md)已完成，仅规划。用户要求记忆、关注、成员增强落地，图片识别也尝试，B站字幕撤下；并确认当前deepseek-v4.1-flash支持视觉。下一轮复用现有业务，在项目外部适配和加载，不改官方Snow/QQ/CLI内部、不换模型/后端。按单项记录实现/离线/配置/加载/真实差别，某项缺口不拖住其他项。

上轮LAP-21[实际数据准备](tracks/laptop-workbuddy/tasks/LAP-21/SNOW_MIGRATION_RESULT.md)已交付：7图复制、7条暂存，运行中未激活/加载/真实验收。用户说图片完成，不据此扩写为图片ACK/客户端显示已通过；42不复做图库、不动21 pending，也不拿该尾项作前置。

## 从哪里继续

1. 使用bot：[日常操作](SnowLuma使用说明.md) / [与旧NapCat bot的使用对照](docs/BOT_USAGE_COMPARISON.md)。
2. 项目接续：本文件 → [AGENTS](AGENTS.md) → [QQ主线HANDOFF](tracks/laptop-workbuddy/HANDOFF.md)和[TASKS](tracks/laptop-workbuddy/TASKS.md) → 当前[LAP-42交接](tracks/laptop-workbuddy/tasks/LAP-42/HANDOFF.md)、[PLAN](tracks/laptop-workbuddy/tasks/LAP-42/PLAN.md)、[medium指令](tracks/laptop-workbuddy/tasks/LAP-42/MEDIUM_START.md) → [使用对照](docs/BOT_USAGE_COMPARISON.md)。旧功能合同只按42所需补读；表情上轮结果见[LAP-21](tracks/laptop-workbuddy/tasks/LAP-21/SNOW_MIGRATION_RESULT.md)。
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
| QQ主线：SnowLuma及共用bot业务 | active；42整合详规完成，待medium实际记忆/关注/成员/识图及B站退役；本轮未启用 | [HANDOFF](tracks/laptop-workbuddy/HANDOFF.md) / [TASKS](tracks/laptop-workbuddy/TASKS.md) / [LAP-42](tracks/laptop-workbuddy/tasks/LAP-42/HANDOFF.md) / [medium指令](tracks/laptop-workbuddy/tasks/LAP-42/MEDIUM_START.md) |
| 家庭5070备用模型路线 | 历史记录为接入已实现/离线及元数据通过、真实生成未验；本轮未重查，不自动切换后端 | [HANDOFF](tracks/local-5070/HANDOFF.md) / [既有选型](tracks/local-5070/MODEL_SELECTION.md) |

`tracks/laptop-workbuddy` 是保留的历史目录名，当前承担QQ主线和共用网关交接，不表示仍以NapCat或WorkBuddy界面为主路线。所有旧任务的状态/验收差额在TASKS与各任务HANDOFF保留，不重命名整棵目录。

## 当前使用快照与未验证范围

LAP-41历史比较共同使用deepseek-v4.1-flash/low、free、adaptive最多3条、16轮历史，persona内容相同。上轮LAP-21配置/persona保护摘要不变；memes=true、冷却0/0保持，目标7图/7条pending已准备。42只读确认active仍不存在、pending存在，未查当前运行态。详见[实际迁移结果](tracks/laptop-workbuddy/tasks/LAP-21/SNOW_MIGRATION_RESULT.md)；保存数据不等于加载/真实通过。

网页材料读取开着，搜索质量门槛仍未通过；视觉、B站字幕、成员、记忆/学习、关注当前都关闭。记忆/关注已有离线实现；成员需补Snow强刷观察外部适配，不能只改开关。模型视觉支持由用户确认，CLI实际像素输入/预算/质量/QQ闭环待验证。42下一轮实际整合这些功能并撤下B站运行链，当前只交付计划，未改代码或本机选择。旧差额保留，不把全部资格/proof/probe/长稳变成前置；微信不推进。

## 历史与检查点

- 本轮规划session LAP-42-snow-feature-rollout-plan，16:32登记7份文档并重读，起点HEAD/实时远端9bb1b58270dbcaa3c5e40c53f804d5e50c54449b，开始无非忽略差异；只读与文档，不改local/persona/图库/运行代码，不启停/模型/群/SSH。交付后停止，最终SHA见回执。
- 本次实际迁移session `LAP-21-snow-memes-data-migration`，16:07登记重读；起点HEAD/实时远端dc79796642371ee72945457b0a4c1bcd94164801，开始Git干净。7图复制/7条暂存完成，20项合成回归及独立数据/保护复核通过；运行中未激活。只交付6份文档，源只读、旧C/A4未访问。

- 本次规划起点本地HEAD/实时远端：e2d9a0c082f3400904d8a4032eb01b4290ef08a8；无非忽略Git差异。session `LAP-21-snow-controlled-memes-plan`，15:49登记7份文档并重读；只有规划交付，不迁数据/历史、不动运行设置或其他根。最终Git号及SHA一致性见当轮交付回执。
- 接入实现：89b7dfae；桌面入口实现：1aabe532。
- 用户确认文字成功：3d3361e，仅指用户现场说明，未独立读取原始模型/发送ACK追踪。
- LAP-41整理前基线：3d3361eaecae1e342bb05412c6af3ccdf6b4417b。
- [整理清单/实际结果与回滚](tracks/laptop-workbuddy/tasks/LAP-41/CLEANUP.md)。
- [旧全量进度快照](docs/archive/pre-snow-mainline-2026-10-25/PROGRESS.md) / [旧工作线交接](docs/archive/pre-snow-mainline-2026-10-25/LAPTOP_HANDOFF.md) / [旧README](docs/archive/pre-snow-mainline-2026-10-25/README.md)。

历史页面可能记载当时“缺环境/真实未验/旧私改待实施”，只能按记录日期理解；当前状态以本入口及活动交接为准。
