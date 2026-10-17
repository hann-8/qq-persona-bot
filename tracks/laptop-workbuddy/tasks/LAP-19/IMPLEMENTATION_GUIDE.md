# LAP-19：gpt-6.1-sol/medium执行指引

返回[PROGRESS](../../../../PROGRESS.md) / [PLAN](PLAN.md) / [自由群聊/表情包合同](GROUP_CHAT_PLAN.md) / [HANDOFF](HANDOFF.md) / [TASKS](../../TASKS.md)。本文件为后续实施指令模板，本轮仅规划。

## 1. 顺序和共同范围

用户在会话设置手动选择gpt-6.1-sol、medium；项目文件不会自动检测或切换。建议依次开4个新会话，每个只领取一个任务，交接/提交推送后再开始下一项，不重做LAP-15/16。

| 顺序 | 任务 | 完成出口 |
| --- | --- | --- |
| 1 | LAP-17本地后端/配置cmd切换 | schema3与两profile、无损迁移、固定指纹SSH原生Ollama、零推理连接检查/状态、取消/回滚、离线/框架回归 |
| 2 | LAP-18两后端共用联网 | 候选质量门槛、受控搜索/网页、预算/来源/失败、一次生成、历史/ACK一致 |
| 3 | LAP-20自由群聊/直接群发 | mentions/free、RAM群窗口/合批、一次生成决定说/不说、真实@必答优先、无引用/自动@、ACK/停止/恢复 |
| 4 | LAP-21表情包 | 本地入口/受控图库、QQ收藏只读导入功能、标签/meme_id、类型化图片投递/ACK，两后端适用 |

以上四条默认授权代码、离线测试、实际框架合成回环、文档和Git交付。**不自动改本机settings启用新模式，不启停/登录真实bot，不调用真实模型，不发群消息，不读真实QQ收藏或下载用户表情。** 17可做计划内家庭SSH只读元数据/通道检查；18可做无隐私公共接口质量探测，均不改PC服务/账号。

LAP-18若搜索候选不过门槛，先完成安全读取/配置/稳定检索接口并明确“搜索未完成”；20/21可在其可用独立接口上继续，不把联网涂绿。改变提供方/账号/部署或额外模型调用须回规划，不由medium临时切付费API/注册Ollama账号/部署SearXNG。

## 2. 每个会话必须执行

1. AGENTS→PROGRESS→活动HANDOFF/TASKS→本目录两份计划/本指引；检查git status/diff，保留用户/其他session改动。
2. 只领取对应任务、登记session标题/开始时间/文件归属，建该任务HANDOFF并登记PROGRESS/TASKS，写后重读；不同时领取或操作同一bot。
3. 一般实现细节自行完成；缺口区分已实现/离线/真实未验，做完独立部分。不得扩大群、账号/额度、模型调用次数或用旁路群发绕过ACK。
4. 运行适用单元和实际框架合成验证，保留黑名单前置、私聊拒绝、单并发/单次模型尝试、CLI工具隔离、旧LAP-16回执恢复及用户配置数值；不为旧trace重复真实推理。
5. 同步任务HANDOFF/TASKS/PROGRESS/相关README，保留旧真人验收差额；审阅任务所属差异后commit/push，排除凭据、本机settings、群原文、用户表情。核对本地SHA与对应远端分支一致，报告提交号、保留差异、未验能力和下一步。

## 3. 四条可直接复制的命令

每条分别给一个已选好gpt-6.1-sol/medium的新会话；路径均以 E:\CodexWS\QQbot 为项目根。

### 第1个会话

```text
阅读 E:\CodexWS\QQbot\AGENTS.md 和 PROGRESS.md，按 tracks\laptop-workbuddy\tasks\LAP-19\IMPLEMENTATION_GUIDE.md 的共同规则与边界，只领取并实施LAP-17；先读该目录PLAN.md、GROUP_CHAT_PLAN.md和活动HANDOFF/TASKS。
实现两套后端profile、旧配置无损迁移、配置机器人.cmd手动切换、固定既有指纹的家庭SSH原生Ollama、零推理元数据检查/状态和失败/回滚。PC已有qwen3.5:9b-q4_K_M，不重装/下载、不改全局参数。
先登记/建任务HANDOFF，完成代码、离线/实际框架合成回归、文档和commit/push并核对远端SHA。不调用真实模型、不启停/登录bot、不改本机settings启用后端、不发群消息；真实能力未验如实交接，不自动开始下一任务。
```

### 第2个会话

```text
阅读 E:\CodexWS\QQbot\AGENTS.md 和 PROGRESS.md，按 tracks\laptop-workbuddy\tasks\LAP-19\IMPLEMENTATION_GUIDE.md 的共同规则与边界，只领取并实施LAP-18；先读PLAN.md、GROUP_CHAT_PLAN.md、LAP-17交接和活动TASKS。
实现两后端共用按需联网：候选搜索质量门槛先行，受控公共网页读取、查询/页数/大小/时间预算、来源、失败/取消、一次生成和历史ACK。不开CLI WebSearch/MCP、不增加付费API/账号/部署；候选质量不过则交付独立部分并明确搜索缺口回规划。
完成离线/实际框架合成回归、文档及commit/push并核对SHA。只做无隐私公共探测，不调用真实模型、不启停/登录bot、不改本机settings启用web、不发群消息，不自动开始下一任务。
```

### 第3个会话

```text
阅读 E:\CodexWS\QQbot\AGENTS.md 和 PROGRESS.md，按 tracks\laptop-workbuddy\tasks\LAP-19\IMPLEMENTATION_GUIDE.md 的共同规则与边界，只领取并实施LAP-20；重点读GROUP_CHAT_PLAN.md、PLAN.md、17/18交接和活动TASKS。
实现显式mentions/free、授权群新消息驱动的RAM窗口/多人合批、一次生成内决定说/不说、真实@绕过自发沉默/冷却并优先排队。黑名单在框架/缓存/检索/模型前过滤；不导入旧个人历史或拉QQ历史。所有模式直接群发，single/adaptive都去引用和自动@，不增加分类模型调用或无新消息的主动任务。
先完成实际框架无conversation/silent/异常发送拦截与ACK/恢复/停止合成门槛；完成实现/测试/文档和commit/push并核对SHA。此次不启停/登录、不做真实模型/群发、不改本机settings为free，不关闭旧真人缺项，不自动开始下一任务。
```

### 第4个会话

```text
阅读 E:\CodexWS\QQbot\AGENTS.md 和 PROGRESS.md，按 tracks\laptop-workbuddy\tasks\LAP-19\IMPLEMENTATION_GUIDE.md 的共同规则与边界，只领取并实施LAP-21；重点读GROUP_CHAT_PLAN.md、PLAN.md、LAP-20交接和活动TASKS。
实现assets\memes\inbox入口/受控library/本机目录表，配置cmd支持本地扫描和从机器人QQ收藏只读导入功能，固定管理RPC不开放账号工具。模型仅选已登记meme_id，一次生成至多一张，正文纯文本/直接群发；图片也进入类型化投递、逐条ACK/部分失败/恢复，不裸API旁路发图。用户素材/标签/签名URL忽略，测试只用自造图片。
完成假收藏API/图片与实际框架离线回归、README/交接和commit/push并核对SHA。不读取真实QQ收藏/下载其图片，不登录/启停bot，不调用真实模型/群发，不改本机settings启用memes。用户已收藏2个仅为用户说明，不能写真实可发。
```

## 4. 实施后的试用/真实验收

四项落地后，用户可在配置cmd选择后端，显式开启free/web/memes和活跃度，停机保存后重新启动。PC开机不睡眠、Ollama后台/SSH可达即可作为模型端前提，笔记本继续跑QQ入口。QQ收藏导入需当前机器人连接可用，由用户点击；可准备暂存，停机激活目录表后重启。

如需agent协助真实验收，另开会话明确领取既有LAP-02的本轮集成范围，并给受测授权群/时段/后端/模型调用上限、是否允许读取收藏/下载/发图以及最终启停状态；范围未给出时不得把上述离线指令解释为实时观察群聊/消费额度授权。

顺序：无推理连接→离群合成窗口的真实生成→群内非@发言/沉默和@必答→联网来源→收藏导入/本地图GIF显示→多人/恢复/长稳。每后端单独记录，用户自行据效果/消耗决定长期后端，不自动双发A/B、换模型或增付费方案。
