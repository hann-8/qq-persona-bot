2026-10-29 LAP-44当前合同：群长期记忆采用schema2全文快照＋同次回复memory_updates增改删，模型决定内容/整理/遗忘；旧候选、句式、关键词和240字节/3条/8条/1536字节小限制停用，旧配置字段兼容但忽略。每群初始50000 Unicode字符、文件1048576字节、总8388608字节；所选CodeBuddy输入政策524288可见UTF-8字节，均可配置扩大并受真实C/F/V/O限制。保存后在投递台账前生成实际回执，重置只清短期上下文。模型/账号/low、thinking=false、free/owner、识图/表情和两工具3调用/4步骤/90秒/8000/12000保持。部署及验证结果以[LAP-44交接](tracks/laptop-workbuddy/tasks/LAP-44/HANDOFF.md)为准，QQ群效果待用户实测。

# QQ bot项目入口：SnowLuma主线

## 当前交接：LAP-44 已部署，待用户群测

2026-10-29 LAP-44已实现、启用并部署main：schema2群记忆全文/模型增改删/实际保存回执已加载，33项定向组合及真实锁定CLI零生成正反配对通过。当前running/connected/can_receive/router_ready，current_error=null、pending_restart=false；memory读写true，3文件0条0字符。初始50000 Unicode字符/1048576文件字节/8388608总字节，所选CLI524288字节政策。容量预算可扩大，100000字符/786432政策合成检查通过，真实C/F/V/O边界仍保留。最新main/df46056联网修复完整合入；其他模型/账号/low、thinking=false、free/owner、识图/表情和工具限额保持。QQ群效果由用户实测，未由离线或加载晋升真实验收。 [交接](tracks/laptop-workbuddy/tasks/LAP-44/HANDOFF.md) / [实际报告](reports/lap-44-memory-result.md) / [使用说明](SnowLuma使用说明.md)。

2026-10-29群测故障修复已合入并部署main：修复CLI工具参数封套及HTTP(S)被误判成本机路径；当前21项定向检查、真实CLI零生成正反接线通过。实际running/connected/can_receive/router_ready，配置无待重启、当前错误为空；识图与记忆保持。详见[43交接](tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md)及[排查报告](reports/lap-43-native-web-debug.md)。真实联网及群答复由用户自行实测。

## 已部署基础：LAP-43联网修复（预算以顶部LAP-44为准）

2026-10-29，main已部署CLI原生WebSearch/WebFetch，由模型按需决定联网，router和WebRunner不再用旧关键词/RSS/HTML预筛当前CodeBuddy请求。每任务最多3次工具调用、4个主步骤、90秒，单结果8000/合计12000字节，每步48000可见政策；其他工具/MCP保持关闭，未自动切换模型/账号或回退Python。CodeBuddy CLI思考显式关闭，DeepSeek/low配置及额度来源不变。

当前实际复核：组件running、OneBot connected、can_receive=true、router_ready=true，磁盘与加载快照一致；原聊天、识图、7表情、唯一操作者、free保持；群长期记忆和学习均true。21项当前定向检查及最终真实CLI零生成正反接线通过，未代用户调用实际WebSearch/WebFetch服务或群发验收，实际联网质量待群测。识图继续完整配对的lap43_operator_trial，未改写旧IQ/质量结论。实现提交651336f/7aa24fb/820a77a，完整运行/Git/回滚见[43交接](tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md)；使用见[日常说明](SnowLuma使用说明.md)。

## 已部署基础：LAP-43四项与原Python联网

2026-10-28，session `LAP-43-rollout`完成统一prompt的四项：7张原表情激活（候选1134字节）；空@/真实媒体提示/直接叫名及同人短续聊修复；仅唯一本机操作者可暂停/明确恢复和执行已有重置；bing_rss时效搜索显式开启，逐请求正文/日期筛选并附来源。原聊天、识图、记忆/学习、关注、成员、free、persona、CodeBuddy/deepseek-v4.1-flash/low、48000政策/4096视觉reserve保留。

生产根已配对保存并正常启动，最近复核：组件running、OneBot connected、授权群消息can_receive=true、router_ready=true，配置快照与磁盘一致；识图完整新绑定`lap43_operator_trial`及搜索`operator_trial_unverified`已加载，质量待用户实测。40定向检查/实际配置预算/真实CLI正反零生成通过；agent主动真实模型/QQ输出为0，不代用户群测。一次公共查询取得RSS及2页响应，但正文提取失败，正确本地说明无法核实，不作为搜索质量通过。用户追加授权从本机npm缓存恢复项目专用2.168.0，原bundle摘要相同，不改已升级的全局2.177.1。

运行及Git证据、精确保护差异、备份和剩余范围见[43交接](tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md)；直接使用见[日常说明](SnowLuma使用说明.md)。原18/21/27/35/42验收差额保留，当前质量由用户群测后反馈，不再等待重复激活/部署授权。

## 上一轮指令准备（历史）


2026-10-28，用户明确个人自用、尽快可用、QQ群自行实测。本轮仅修订AGENTS及43执行合同；功能方案沿用已有详规，下一轮提交[统一medium prompt](tracks/laptop-workbuddy/tasks/LAP-43/MEDIUM_START.md)后，在同轮实现、启用并部署表情、空@/叫名、唯一操作者和时效搜索，不再分A/B/C轮流等待授权。只保留必要检查；搜索取消固定质量批次作为个人试用前置，识图增加真实标记为待用户实测的当前版本试用模式，保持预算/工具隔离/完整绑定及unknown边界。旧测试/接受事实不改写，不自动调用真实模型或群发验收。当前功能与运行状态未改；本轮归属、检查和Git回执见[43交接](tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md)。

2026-10-27，LAP-43详细规划与分阶段medium指令已交付，包含表情激活、时效搜索、空@/free漏答及唯一操作者控制。用户明确授权的Snow分支快进main已完成，规划提交`2986667cf88c85db39947871941a81a0014acba4`在两条远端分支核对一致，本根已切main、切换文件树无变化。7份文档登记重读、232本地链接和17项保护检查通过；本轮仅文档与Git，不实施功能、不改local/persona/图库/pending，不启停/模型/QQ。[43交接](tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md) / [详规](tracks/laptop-workbuddy/tasks/LAP-43/PLAN.md) / [medium指令](tracks/laptop-workbuddy/tasks/LAP-43/MEDIUM_START.md)。回执交付后停止，后续从main按用户选中的阶段接续。

当前只读核实：7张表情资产/7条pending有效，active未激活；搜索代码质量门槛false；保存的free/attention/web/vision等开关为true。唯一admin已与用户本人一致，但旧停言入口仍允许普通成员控制、任意真实@恢复，owner-only是本次规划合同，**尚未实施**。真实号码仅留本机忽略配置。

## 2026-10-26 识图已启用并完成用户指定的缩减验收

识图已保存并运行加载为true，用户已确认真实授权群中收到正确识图回复，原事件任务completed、投递sent且有消息ACK。按用户决定只完成IQ-01和1000×1000大图IQ-05，两张真实理解均获人工通过；其余四例豁免，旧六例账本与首张评分记录异常保留，不称六例全通过。104单元/39框架、当前真实CLI零生成契约通过。双图片/成员凭证兼容已修；随后用户明确允许提高输入预算，仅将所选CodeBuddy文字政策30000→48000字节，overhead/output各2048、视觉reserve4096、模型/low/free/账号不变。15项保护中仅features与models的这两个授权标量改变，人设/图库/21 pending等保持。详见本轮closure-result；不续其他验收。

## 当前结论

QQ以后以 `E:/CodexWS/QQbot_Snowluma` 的官方原版SnowLuma路线为主线。用户已确认Snow可运行、bot在QQ群中可回复；LAP-40最小文字首试按用户现场确认通过。接入与日常启动脚本已实现/离线通过，未把用户反馈扩写成免扫码、停止或长稳完整验收。

LAP-41工作区整理与使用对照已完成：uv报告清除38,269个缓存文件约626.1MiB，5份临时网页快照和退役自启提示入口已删除，四份旧入口说明归档。约1.25MiB字节码缓存因自动审批拒绝删除而保留。25份运行保护文件摘要相同，未改生产代码、模型/人设/触发或其他业务配置，未启停bot。

**LAP-42已实际实施并加载可用部分**：[实际报告](reports/lap-42-2026-10-25.md) / [交接](tracks/laptop-workbuddy/tasks/LAP-42/HANDOFF.md)。长期群记忆读取/学习、关注、成员与受控@已保存并加载；B站字幕运行服务/入口已退役，普通web保留。164项定向单元、19项AstrBot原事件组合回环通过。新根独立记忆key/context token已初始化，人设/图库/21 pending未变，CodeBuddy/DeepSeek/low/free及原预算保留。

以下42阶段记录为历史，已被顶部2026-10-26识图缩减验收结论覆盖的状态不能当作当前。上轮追加单图采样真实下载并解码JPEG（1260×709→1024×576），该样本0模型/0bot输出，首窗口超时保留；当时CLI原生图片封套/像素hash仅替身验证、vision=false、IQ/群图未执行。记忆/成员真实效果仍不能据加载晋升通过，实施期间自然CLI尝试单列。完整差额见42结果，不重跑旧阶段。

上轮LAP-21[实际数据准备](tracks/laptop-workbuddy/tasks/LAP-21/SNOW_MIGRATION_RESULT.md)已交付：7图复制、7条暂存，运行中未激活/加载/真实验收。用户说图片完成，不据此扩写为图片ACK/客户端显示已通过；42不复做图库、不动21 pending，也不拿该尾项作前置。

**LAP-42视觉续作已交付代码与定向验证，识图仍待具体来源缺口**：[实际结果](reports/lap-42-vision-result.md) / [定向报告](reports/lap-42-vision-offline.json) / [来源审阅](reports/lap-42-vision-sources.json)。null窗口、字节/token分账、hosted三字段身份及新offline接点已修；88单元/39框架场景通过。现有0生成握手确认当前DeepSeek支持图片与low（1M输入/128000输出），但CLI自定义system后仍渲染/追加产品agent文字，完整F上界未获证，静态拒绝IQ；IQ=0/6、群图=0/2、vision=false。既有decoded记录有效可复用，未新采样/启停/改local；现场当前stopped/disconnected，不能沿用上轮ready。只交付42并释放归属，未自动推进21或其他验收。

**LAP-42真实CLI接线与当前零生成契约检查已通过，代码冻结，开始固定六例人工审阅。** 用户明确追加授权本机总上限7次（既有意外1+固定六例6），群图仍最多2。新规则/视图/回执问题已修，97单元/39框架通过；当前实际正向1本地user/0 next、缺插件与错回执均0 user，无新增远端生成。双上下文纯函数、仅视觉子进程关闭CLI rules注入，原system/项目材料保留；API文字视图不冒充图片视图，原生帧由子进程与父进程分别校验。回执置于插件目录之外并按阶段独立留证。现有真实耗次1、IQ待逐例、vision=false，尚未激活/群图。实际结果与当前私有frozen-before-iq绑定见[报告](reports/lap-42-vision-closure-result.md)。

## 从哪里继续

1. 使用bot：[日常操作](SnowLuma使用说明.md) / [与旧NapCat bot的使用对照](docs/BOT_USAGE_COMPARISON.md)。
2. 项目接续：本文件 → [AGENTS](AGENTS.md) → [QQ主线HANDOFF](tracks/laptop-workbuddy/HANDOFF.md)和[TASKS](tracks/laptop-workbuddy/TASKS.md) → [LAP-44交接](tracks/laptop-workbuddy/tasks/LAP-44/HANDOFF.md)、[详细规划](tracks/laptop-workbuddy/tasks/LAP-44/PLAN.md)、[medium实施prompt](tracks/laptop-workbuddy/tasks/LAP-44/MEDIUM_START.md)。用户提交prompt后同轮实现部署44。已有联网/识图等基础及最近修复读[43交接](tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md)，保留b0b4573成果，不重做旧六例/接入/首试；真实QQ体验由用户实测。
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
| QQ主线：SnowLuma及共用bot业务 | LAP-44全文群记忆/可扩配置已部署；最新43联网修复保留，群效果待用户实测 | [HANDOFF](tracks/laptop-workbuddy/HANDOFF.md) / [TASKS](tracks/laptop-workbuddy/TASKS.md) / [LAP-43](tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md) |
| 家庭5070备用模型路线 | 历史记录为接入已实现/离线及元数据通过、真实生成未验；本轮未重查，不自动切换后端 | [HANDOFF](tracks/local-5070/HANDOFF.md) / [既有选型](tracks/local-5070/MODEL_SELECTION.md) |

`tracks/laptop-workbuddy` 是保留的历史目录名，当前承担QQ主线和共用网关交接，不表示仍以NapCat或WorkBuddy界面为主路线。所有旧任务的状态/验收差额在TASKS与各任务HANDOFF保留，不重命名整棵目录。

## 早期使用快照与未验证范围（当前以顶部LAP-43为准）

LAP-41历史比较共同使用deepseek-v4.1-flash/low、free、adaptive最多3条、16轮历史，persona内容相同。上轮LAP-21配置/persona保护摘要不变；memes=true、冷却0/0保持，目标7图/7条pending已准备。42只读确认active仍不存在、pending存在，未查当前运行态。详见[实际迁移结果](tracks/laptop-workbuddy/tasks/LAP-21/SNOW_MIGRATION_RESULT.md)；保存数据不等于加载/真实通过。

网页材料读取保存为开启，旧搜索质量门槛仍未通过且本轮未改代码。42后记忆/学习/关注开启，成员/受控@仅已审阅官方Snow强刷来源、1..49人及双TTL有效时增强；NapCat/未知版本继续暂停，大群/失败保留普通文字。B站字幕已退役，旧false节兼容、true拒绝恢复服务。视觉已按顶部2026-10-26缩减验收启用；本轮未查进程或重做真实验收。下一轮按43第0/10节配对更新及明确试用状态，不把待人工实测伪写成质量通过。旧差额保留，不加资格/长稳前置；微信不推进。

## 历史与检查点

- 2026-10-26识图闭环规划session LAP-42-vision-prompt-closure-plan：00:00领取7文档并重读，18:34用户“继续”后重核本地/实时远端仍355f7eec2971946595efd057ea3f2a5790afa6f3，仅已有本session TASKS段落有差异。查明官方后组装投影接口及实际启用事务尾项；只读/文档，不执行插件/模型/启停/QQ。恢复后重取22项保护基线，检查/Git见42交接，交付后停止。

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
