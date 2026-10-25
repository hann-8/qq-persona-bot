# QQ bot项目入口：SnowLuma主线

本文件是唯一项目进度入口，不另建根HANDOFF。更新：2026-10-25（Asia/Shanghai）。

## 当前结论

QQ以后以 `E:/CodexWS/QQbot_Snowluma` 的官方原版SnowLuma路线为主线。用户已确认Snow可运行、bot在QQ群中可回复；LAP-40最小文字首试按用户现场确认通过。接入与日常启动脚本已实现/离线通过，未把用户反馈扩写成免扫码、停止或长稳完整验收。

LAP-41工作区整理与使用对照已完成：uv报告清除38,269个缓存文件约626.1MiB，5份临时网页快照和退役自启提示入口已删除，四份旧入口说明归档。约1.25MiB字节码缓存因自动审批拒绝删除而保留。25份运行保护文件摘要相同，未改生产代码、模型/人设/触发或其他业务配置，未启停bot。

**LAP-42已实际实施并加载可用部分**：[实际报告](reports/lap-42-2026-10-25.md) / [交接](tracks/laptop-workbuddy/tasks/LAP-42/HANDOFF.md)。长期群记忆读取/学习、关注、成员与受控@已保存并加载；B站字幕运行服务/入口已退役，普通web保留。164项定向单元、19项AstrBot原事件组合回环通过。新根独立记忆key/context token已初始化，人设/图库/21 pending未变，CodeBuddy/DeepSeek/low/free及原预算保留。

用户配合的追加单图采样已真实下载并解码JPEG（1260×709→1024×576），该样本0模型/0bot输出；首窗口超时保留，不抹失败。当前CLI原生图片封套与四种格式像素hash已用实际runner底层替身验证；模型支持由用户确认，但视觉token/模板上界与组合原生容量未获证，六例IQ/群图片生成未执行，vision仍false。记忆持久学习、成员/受控@群内真实效果与客户端显示均未据加载晋升通过。最终OneBot就绪；本轮实施期间旧实例有4次可见自然CLI尝试，不能称全程0调用。只完成42，不续其他任务。

上轮LAP-21[实际数据准备](tracks/laptop-workbuddy/tasks/LAP-21/SNOW_MIGRATION_RESULT.md)已交付：7图复制、7条暂存，运行中未激活/加载/真实验收。用户说图片完成，不据此扩写为图片ACK/客户端显示已通过；42不复做图库、不动21 pending，也不拿该尾项作前置。

**下一项只续LAP-42当前DeepSeek识图收尾，已详细规划、未实施**：[详规](tracks/laptop-workbuddy/tasks/LAP-42/VISION_FINISH_PLAN.md) / [来源与推导](tracks/laptop-workbuddy/tasks/LAP-42/HOSTED_CLI_BUDGET_EVIDENCE.md) / [可复制medium指令](tracks/laptop-workbuddy/tasks/LAP-42/VISION_MEDIUM_START.md)。本轮只读核对取得官方单图1024 token规则和固定编码器来源；发现项目hosted校验的null窗口互斥、字节/token混扣、GGUF身份要求及旧报告接点阻断。按当前CLI真实契约修项目外层，不改模型/人设/预算数字或Snow内部，不等于已通过原生质量/启用。然后才分别收尾21表情激活与已开增强的人工验收；本轮不同时领取。

## 从哪里继续

1. 使用bot：[日常操作](SnowLuma使用说明.md) / [与旧NapCat bot的使用对照](docs/BOT_USAGE_COMPARISON.md)。
2. 项目接续：本文件 → [AGENTS](AGENTS.md) → [QQ主线HANDOFF](tracks/laptop-workbuddy/HANDOFF.md)和[TASKS](tracks/laptop-workbuddy/TASKS.md) → 当前[LAP-42交接](tracks/laptop-workbuddy/tasks/LAP-42/HANDOFF.md)、[识图详规](tracks/laptop-workbuddy/tasks/LAP-42/VISION_FINISH_PLAN.md)、[预算来源](tracks/laptop-workbuddy/tasks/LAP-42/HOSTED_CLI_BUDGET_EVIDENCE.md)、[新medium指令](tracks/laptop-workbuddy/tasks/LAP-42/VISION_MEDIUM_START.md) → [使用对照](docs/BOT_USAGE_COMPARISON.md)。原42 PLAN/MEDIUM_START为上一轮合同，不整轮再跑；旧功能合同只按具体接点补读，表情上轮结果见[LAP-21](tracks/laptop-workbuddy/tasks/LAP-21/SNOW_MIGRATION_RESULT.md)。
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
| QQ主线：SnowLuma及共用bot业务 | active；42可用功能已加载；视觉真实入站通过、原生预算/质量未验且仍关闭；hosted预算修复/识图收尾详规已交付未实施 | [HANDOFF](tracks/laptop-workbuddy/HANDOFF.md) / [TASKS](tracks/laptop-workbuddy/TASKS.md) / [LAP-42](tracks/laptop-workbuddy/tasks/LAP-42/HANDOFF.md) / [识图medium](tracks/laptop-workbuddy/tasks/LAP-42/VISION_MEDIUM_START.md) |
| 家庭5070备用模型路线 | 历史记录为接入已实现/离线及元数据通过、真实生成未验；本轮未重查，不自动切换后端 | [HANDOFF](tracks/local-5070/HANDOFF.md) / [既有选型](tracks/local-5070/MODEL_SELECTION.md) |

`tracks/laptop-workbuddy` 是保留的历史目录名，当前承担QQ主线和共用网关交接，不表示仍以NapCat或WorkBuddy界面为主路线。所有旧任务的状态/验收差额在TASKS与各任务HANDOFF保留，不重命名整棵目录。

## 当前使用快照与未验证范围

LAP-41历史比较共同使用deepseek-v4.1-flash/low、free、adaptive最多3条、16轮历史，persona内容相同。上轮LAP-21配置/persona保护摘要不变；memes=true、冷却0/0保持，目标7图/7条pending已准备。42只读确认active仍不存在、pending存在，未查当前运行态。详见[实际迁移结果](tracks/laptop-workbuddy/tasks/LAP-21/SNOW_MIGRATION_RESULT.md)；保存数据不等于加载/真实通过。

网页材料读取保持开启，搜索质量门槛仍未通过。42后记忆/学习/关注开启，成员/受控@仅已审阅官方Snow强刷来源、1..49人及双TTL有效时增强；NapCat/未知版本继续暂停，大群/失败保留普通文字。B站字幕已退役，旧false节兼容且未改本机原字节，true拒绝恢复服务。视觉仍关闭；真实入站成功不等于模型理解/群ACK成功。旧差额保留，不把资格/proof/probe/长稳变成前置；微信不推进。

## 历史与检查点

- 识图收尾规划session `LAP-42-hosted-vision-finish-plan`，22:19登记7份文档并重读，起点本地/实时远端48f66bc192548184e4f88e23de6a357962bff85e，Git无非忽略差异。只续42，不新建ID；本轮只读代码/公开来源和纯预算计算，不改代码/local/persona/图库/运行状态，不启停/真实模型/QQ/群/SSH。实际检查和Git回执见42交接；规划完成后停止。

- LAP-42实际实施session `LAP-42-snow-integration-implementation`：起点本地/实时远端0752c7b9bc2c38033d86e957fdfd9d179460aea1，初始Git干净；164单元/19框架组合/224文档链接通过，可用功能已保存加载，第二组采样/恢复由用户追加授权。仅拥有两份local的5个布尔字段，图库/persona/21 pending不变。交付后释放唯一执行归属并停止；视觉预算/质量和各项真实效果差额见42报告，不能自动续验。

- 本轮规划session LAP-42-snow-feature-rollout-plan，16:32登记7份文档并重读，起点HEAD/实时远端9bb1b58270dbcaa3c5e40c53f804d5e50c54449b，开始无非忽略差异；只读与文档，不改local/persona/图库/运行代码，不启停/模型/群/SSH。交付后停止，最终SHA见回执。
- 本次实际迁移session `LAP-21-snow-memes-data-migration`，16:07登记重读；起点HEAD/实时远端dc79796642371ee72945457b0a4c1bcd94164801，开始Git干净。7图复制/7条暂存完成，20项合成回归及独立数据/保护复核通过；运行中未激活。只交付6份文档，源只读、旧C/A4未访问。

- 本次规划起点本地HEAD/实时远端：e2d9a0c082f3400904d8a4032eb01b4290ef08a8；无非忽略Git差异。session `LAP-21-snow-controlled-memes-plan`，15:49登记7份文档并重读；只有规划交付，不迁数据/历史、不动运行设置或其他根。最终Git号及SHA一致性见当轮交付回执。
- 接入实现：89b7dfae；桌面入口实现：1aabe532。
- 用户确认文字成功：3d3361e，仅指用户现场说明，未独立读取原始模型/发送ACK追踪。
- LAP-41整理前基线：3d3361eaecae1e342bb05412c6af3ccdf6b4417b。
- [整理清单/实际结果与回滚](tracks/laptop-workbuddy/tasks/LAP-41/CLEANUP.md)。
- [旧全量进度快照](docs/archive/pre-snow-mainline-2026-10-25/PROGRESS.md) / [旧工作线交接](docs/archive/pre-snow-mainline-2026-10-25/LAPTOP_HANDOFF.md) / [旧README](docs/archive/pre-snow-mainline-2026-10-25/README.md)。

历史页面可能记载当时“缺环境/真实未验/旧私改待实施”，只能按记录日期理解；当前状态以本入口及活动交接为准。
