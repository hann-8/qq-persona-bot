# QQ 人设聊天 Bot：项目入口

更新时间：2026-10-17 16:44（Asia/Shanghai）。本文件是唯一项目进度入口，不另建根HANDOFF。

## 当前阶段与授权

[LAP-20自由群聊与直接群发](tracks/laptop-workbuddy/tasks/LAP-20/HANDOFF.md)已实现/离线通过，见[报告](reports/lap-20-2026-10-17.md)：显式mentions/free、RAM窗口/合批、一次说/不说、真实@优先、全模式直发、群ACK/未知隔离与恢复。187单元、两真实runner底层替身+实际框架108组群聊用例（含完整build_main_agent），26网页与90原路径回归通过。默认mentions，本机未切free；0启停/登录/真实模型/群发，运行状态未探测。仅20，21待新指令。以下17/18是继承的历史证据；18搜索缺口与旧真人差额保留。Git交付核对见20交接。

2026-10-17 16:15：[LAP-18共用联网](tracks/laptop-workbuddy/tasks/LAP-18/HANDOFF.md)独立部分已实现/离线通过：安全公共网页读取、配置、两后端共用预算/来源/取消/原问题历史ACK；164单元、26网页框架合成与90原路径回归通过，见[报告](reports/lap-18-2026-10-17.md)。最终三类公共搜索查询均被非全局DNS地址检查拦截，质量门槛未通过，搜索未完成且代码门槛关闭，须回规划；不绕过网络检查或改提供方。真实公共正文/两后端联网生成/群验收未通过或未做，不能标联网可用。未改本机settings/人设、未启停/登录bot、0真实模型/群发；不自动开始20/21。Git交付核对记录见任务HANDOFF。

LAP-17已独立实现，146项单元、两后端实际runner+AstrBot合成90组及入口/ACK/恢复通过，见[报告](reports/lap-17-2026-10-17.md) / [任务HANDOFF](tracks/laptop-workbuddy/tasks/LAP-17/HANDOFF.md)。schema3与两profile、旧配置保留迁移、配置cmd停机手动切换、固定指纹SSH原生Ollama/零推理预检、未知结果持久阻断已落地。真实生成/QQ/完整验收未做，不能标双路线真实可用。

2026-10-17 15:51（Asia/Shanghai）内容提交`34f62843b29c99d746a944216cab74f85eb8e932`已推送origin/main，git ls-remote核对完整SHA一致，内容交付检查点工作区干净；随后仅同步本交付记录。本轮没有修改本机settings/persona或初始化长期运行连接JSON，没有启停/登录bot、真实CLI/Ollama生成/群发、PC下载/全局参数/服务修改。当前bot状态未知。PC最终零推理元数据15:44通过，digest一致；最新ps未加载所选模型，不沿用早期16K加载状态。证据见[PC交接](tracks/local-5070/HANDOFF.md)。

[LAP-19总体计划](tracks/laptop-workbuddy/tasks/LAP-19/PLAN.md)、[自由群聊/表情包合同](tracks/laptop-workbuddy/tasks/LAP-19/GROUP_CHAT_PLAN.md)与[实施指引](tracks/laptop-workbuddy/tasks/LAP-19/IMPLEMENTATION_GUIDE.md)仍是17/18/20/21合同。17已交付；18独立部分交付、搜索缺口回规划；20已实现/离线通过且未启用free，21待后续指令。CLI/AstrBot工具隔离不变，QQ正文仍纯文字。

原[LAP-15人设](tracks/laptop-workbuddy/tasks/LAP-15/HANDOFF.md)、[LAP-16有限分条](tracks/laptop-workbuddy/tasks/LAP-16/HANDOFF.md)及旧真人验收差额保留，缺省single，adaptive未实际启用。Git交付不等于部署或真实验收。

## 已确认的全局需求

- 使用闲置个人QQ，不能替换成QQ官方机器人；仅指定授权群，私聊关闭。默认mentions；free已实现但需显式启用后自然参与非@聊天，真实@绕过自发沉默/冷却进入回应流程。黑名单在入口先过滤，不进入框架/群窗口/模型/新增历史。
- 笔记本沿用同账号同站点CodeBuddy CLI订阅/免费额度，默认保留deepseek-v4.1-flash，不增付费API；不保证免费。真实credits缺少证据就标未知，不把token或占位0当积分。
- 家庭RTX5070上的Qwen3.5 9B Q4_K_M由用户安装；两路线均保留，比较效果和消耗后由操作者选择，不自动换模型/账号/后端/额度来源。不重装Ollama或执行旧周末全套迁移预案。
- 配置cmd将提供后端切换/共用联网设置，分别保留参数。原生上下文/思考与保守输入字节预算口径分开；schema3迁移/只读检查/回滚详见LAP-19，LAP-17已实现并离线通过，本机仍未切换。
- QQ正文自然纯文本，有限气泡仅显式adaptive；后续21允许已登记表情图，20已实现所有模式直接群发、无引用/自动@。角色为鲸鱼娘/鱼片和口语，认真问题完整回答，不靠人设扩大能力。自由参与已由20实现/离线通过，尚未启用，不使用概率/关键词唯一触发；无新消息的定时冷场发言未规划。
- 两后端共用按需联网，来源可追溯，调用/页数/大小/超时有界，网页材料与指令隔离；升级默认web关闭，真实启用另执行。候选搜索质量不足回规划，不临时增加付费API或放开CLI全部工具。
- mentions连续聊天按群/用户隔离；free已实现每群/epoch独立RAM窗口，不把旧个人历史公开到群上下文。B站/ASR低优先级，不以标题代替视频正文；发送表情不代表接入收到图片/视频的理解。
- 启停只操作有创建身份的项目进程和受管子进程，不按QQ/Node/Python进程名批量结束，不改日常QQ/WorkBuddy全局配置。健康检查不生成模型内容。
- 家庭地址/账号/凭据只放项目忽略secrets，本机使用、不输出/提交、不进入全局记忆、不复用于工作环境；原始私密群消息和本机运行配置继续排除。
- 新功能先由AGENTS指定模型/max及以上规划，再由指定模型/medium按后续指令实施。会话设置由用户选择，不声称自动检测或切换；一个session一个任务。

## 当前技术结论

共用底座NapCat + 严格反向WS入口 + AstrBot，默认后端为官方CodeBuddy CLI2.168.0，新增固定指纹SSH原生Ollama由操作者显式切换。MCP可调用不等于QQ入站自动唤醒；CLI账号调用/隔离/历史有旧真实证据，精确积分与完整无人值守仍未核验。LAP-10的原生窗口/强制压缩/内部恢复缺口保留，一次CLI启动不等于严格一次上游API。

LAP-17已有SSH原生runner/schema3/切换及统一结果/版本；LAP-18安全读取/共用联网政策已离线通过，搜索未完成。PC元数据/通道、公共网页、模型生成/人设/群验收是不同阶段。

## 阅读顺序与下一步

1. [AGENTS](AGENTS.md)→本入口→[笔记本HANDOFF](tracks/laptop-workbuddy/HANDOFF.md)与[TASKS](tracks/laptop-workbuddy/TASKS.md)。
2. 新需求读[LAP-19 HANDOFF](tracks/laptop-workbuddy/tasks/LAP-19/HANDOFF.md)、[PLAN](tracks/laptop-workbuddy/tasks/LAP-19/PLAN.md)、[GROUP_CHAT_PLAN](tracks/laptop-workbuddy/tasks/LAP-19/GROUP_CHAT_PLAN.md)与[复制指令](tracks/laptop-workbuddy/tasks/LAP-19/IMPLEMENTATION_GUIDE.md)，本地再读[PC交接](tracks/local-5070/HANDOFF.md)。20已离线交付；18搜索缺口从[交接](tracks/laptop-workbuddy/tasks/LAP-18/HANDOFF.md)恢复，后续21及真实启用须新指令，不自动推进。
3. 涉及已有输出/ACK路径再查[LAP-16交接](tracks/laptop-workbuddy/tasks/LAP-16/HANDOFF.md)、[LAP-15交接](tracks/laptop-workbuddy/tasks/LAP-15/HANDOFF.md)及[LAP-14原合同](tracks/laptop-workbuddy/tasks/LAP-14/PLAN.md)/[实施指引](tracks/laptop-workbuddy/tasks/LAP-14/IMPLEMENTATION_GUIDE.md)，不重新领取已交付任务。全局背景见[需求](docs/REQUIREMENTS.md)/[调研](docs/RESEARCH.md)。
4. 不重复硬件盘点/安装、旧trace推理或全部真人基线；受影响路径按新任务回归。当前bot状态未知，真实模型/群验收和启停须登记执行归属。

## 工作线索引

| 工作线 | 状态 | 最近更新 | 下一步 | 交接入口 |
| --- | --- | --- | --- | --- |
| 笔记本 WorkBuddy / 共用网关 | active；20离线交付未启用；18搜索未完成 | 2026-10-17 16:44 | 18搜索缺口回规划；21及真实启用待指令 | [HANDOFF](tracks/laptop-workbuddy/HANDOFF.md) / [TASKS](tracks/laptop-workbuddy/TASKS.md) / [20交接](tracks/laptop-workbuddy/tasks/LAP-20/HANDOFF.md) |
| 家庭5070 PC本地模型 | active；17接入已实现/离线与元数据通过，真实生成未验 | 2026-10-17 15:52 | 17待真实范围；保留0生成/未改本机后端 | [HANDOFF](tracks/local-5070/HANDOFF.md) / [选型历史/最新快照](tracks/local-5070/MODEL_SELECTION.md) |

已建立任务交接：[LAP-08规划](tracks/laptop-workbuddy/tasks/LAP-08/HANDOFF.md)、[09配置/准入](tracks/laptop-workbuddy/tasks/LAP-09/HANDOFF.md)、[10预算/参数](tracks/laptop-workbuddy/tasks/LAP-10/HANDOFF.md)、[11纯文本/人设](tracks/laptop-workbuddy/tasks/LAP-11/HANDOFF.md)、[12启停/状态](tracks/laptop-workbuddy/tasks/LAP-12/HANDOFF.md)、[13配置控制台](tracks/laptop-workbuddy/tasks/LAP-13/HANDOFF.md)、[14人设/分条规划](tracks/laptop-workbuddy/tasks/LAP-14/HANDOFF.md)、[15精简人设](tracks/laptop-workbuddy/tasks/LAP-15/HANDOFF.md)、[16一次生成/分条](tracks/laptop-workbuddy/tasks/LAP-16/HANDOFF.md)、[19双后端/联网规划](tracks/laptop-workbuddy/tasks/LAP-19/HANDOFF.md)、[17本地接入/配置切换](tracks/laptop-workbuddy/tasks/LAP-17/HANDOFF.md)、[18共用联网独立部分/搜索缺口](tracks/laptop-workbuddy/tasks/LAP-18/HANDOFF.md)；[LAP-20已实现/离线通过](tracks/laptop-workbuddy/tasks/LAP-20/HANDOFF.md)，未启用free；21未领取。

## 必须保留的验收差额

- LAP-10部分完成：选定DeepSeek/high有真实证据，原生窗口未证实，CLI force压缩/内部恢复未排除；不改写为严格一次上游推理，见[报告](reports/lap-10-2026-10-16.md)。
- LAP-09授权群/黑名单真实缺项、LAP-11/15最终P01风格接受、LAP-13终端视觉接受、LAP-16真实QQ ACK/多人/关闭中发送和adaptive启用均未由本轮补齐。
- LAP-02/03/04/05真人交错/隔离/三轮记忆/重置/长稳/完整文本交付保留。旧G4仅单条/无@/两轮口令有证据，两小时混合文本/视频完整验收不以离线代替；见[TASKS验收差额](tracks/laptop-workbuddy/TASKS.md#验收差额)。
- LAP-12最后全停/端口关闭是历史检查点，不能推断用户试用后状态；当前未探活bot。旧失败trace上游根因缺完整证据，不为旧错误循环消费额度。
- LAP-06/07视频/ASR延期；原LAP-17未@分支由LAP-20实现/离线通过，尚未启用。17已有离线/元数据证据；新后端/联网/free/表情包仍无真实生成/群验收，PC已加载或NapCat静态API存在不等于真实验收通过。

## 多session与Git交付

PROGRESS保存全局结论，工作线HANDOFF保存当前检查点，TASKS登记唯一任务/负责人/文件归属。领取后建任务HANDOFF并双向链接，结束前更新完成、剩余、文件和验证，区分已规划/已实现/离线通过/真实通过/完整验收。Markdown台账无锁，同文件不明修改、真实模型/群操作和bot启停先协调，不覆盖其他session。

长期授权允许在可审阅检查点自行commit/push，规划也须Git交付。只提交本任务检查过的文件，推送后核对完整SHA与对应远端分支、报告保留差异；凭据/本机配置/原始私密消息排除，详细以AGENTS为准。

## 最近里程碑

- LAP-17两profile/迁移/菜单/SSH原生runner/预检/未知阻断已实现，146单元、90框架合成和SSH零推理元数据通过；真实启用另行授权。

- LAP-19四项详细设计/medium复制指令落盘；PC/SSH有只读证据，黑名单直接过滤与收藏API静态核对，0生成/群发/运行修改；联网候选/QQ表情均未真实功能验收。
- LAP-16一次生成/有限气泡、事件回执/历史修复/启动恢复实现并离线通过；缺省single，adaptive未启用。
- LAP-15角色正文整理完成，组合3618字节；原文hash备份本机忽略，真实风格接受未验。
- LAP-12一键生命周期本机无推理验证有历史证据；LAP-13配置交互实现/离线通过，真实终端接受待验。
- G0—G4和LAP-09—11技术/群文本基线可从工作线及各任务恢复，不等同完整第一版文本/视频交付。

当前交付：[LAP-20自由群聊与直接群发](tracks/laptop-workbuddy/tasks/LAP-20/HANDOFF.md)，session LAP-20-group-participation；实现/离线通过，真实未验，仅20；下一步等用户指令，不启停或改本机settings。
