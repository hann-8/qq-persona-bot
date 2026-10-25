# QQ主线交接：SnowLuma与共用bot业务

返回[项目入口](../../PROGRESS.md) / [AGENTS](../../AGENTS.md) / [任务台账](TASKS.md)。2026-10-25，Asia/Shanghai。保留原目录名以兼容已有链接；此处今后以SnowLuma为主线。

## 当前状态

当前下一轮为**LAP-42 Snow既有功能整合**：[交接](tasks/LAP-42/HANDOFF.md) / [PLAN](tasks/LAP-42/PLAN.md) / [完整medium指令](tasks/LAP-42/MEDIUM_START.md)。用户追加要求记忆、关注、成员落地，识图尝试、B站撤下；当前DeepSeek支持视觉由用户确认。42统筹组合适配与统一加载，复用旧27/28/29/30，不重写架构、不改Snow/QQ/CLI内部，不同时重领旧任务。本轮仅规划，未改开关或真实操作。

当前**LAP-21 Snow受控表情迁移准备已完成**，见[实际结果](tasks/LAP-21/SNOW_MIGRATION_RESULT.md)。7图已复制、7条原登记已锁内暂存；5 GIF+2 JPEG共4,100,086字节，候选7项/1134字节。目标既有停机检查为运行中，未激活/加载，活动catalog仍不存在；真实图片ACK/客户端显示/GIF均未验。生产代码修改0，local/persona及当前开关/冷却保持。20项合成回归及源稳定性/目标hash/幂等合并保护复核通过，Git交付后释放归属并停止。

LAP-40官方接入与日常入口已实现/离线通过，用户已现场确认Snow可运行、QQ群可回复，最小文字首试成功。来源是用户说明，未据此认定停止/免扫码/其他功能/长稳完整验收。

LAP-41已完成新根整理：uv报告清除38,269缓存文件约626.1MiB、5份网页快照和退役提示cmd已删除，4份旧入口说明归档；少量字节码缓存因自动审批拒绝删除而保留。当前入口以Snow主线压缩整理，使用对照已交付。起点本地/远端3d3361ea、工作区原先干净，session `LAP-41-snow-mainline-cleanup-comparison`；25份保护文件摘要相同，未改生产代码/配置或启停bot。清单、限制和验证见[41 HANDOFF](tasks/LAP-41/HANDOFF.md)/[CLEANUP](tasks/LAP-41/CLEANUP.md)。

## 当前需要读的文件

- 当前：[42 HANDOFF](tasks/LAP-42/HANDOFF.md) → [整合计划](tasks/LAP-42/PLAN.md) / [medium指令](tasks/LAP-42/MEDIUM_START.md)，再读使用对照；原功能合同按需补读，不重跑接入或文字首试。
- 上轮：[21实际数据准备](tasks/LAP-21/SNOW_MIGRATION_RESULT.md)保留；active未激活/真实未验不阻塞42，42不动其pending。
- 日常使用：[SnowLuma使用说明](../../SnowLuma使用说明.md)。
- 旧NapCat用户：[实际bot使用对照](../../docs/BOT_USAGE_COMPARISON.md)。
- 接入/日常入口事实：[40 HANDOFF](tasks/LAP-40/HANDOFF.md)，按需要查其PLAN/桌面入口合同。
- 模型、聊天和功能配置：[config/README](../../config/README.md)，不输出本机配置原文或秘密。
- 原有所有任务及验收差额：[TASKS](TASKS.md)。其他任务仍保留，不自动展开。

## 主线合同

官方Snow只是QQ接入，gate/AstrBot/router/gateway/CodeBuddy仍承担共用bot业务。两根配置/persona前后保护摘要未变；新根7张图片及7条pending已准备，活动目录未激活，不会自动继承旧聊天历史。

NapCat旧根和旧C根不修改/启停；保留本根仍被导入的NapCat兼容代码、旧任务/报告和A4代码/产物/证据。B/C停止，不再把旧私有资格/proof/probe/原生数据证明或长稳作为首试前置。模型/账号/额度、local/persona、群历史、登录和图库不因整理自动变化。

上轮21只在新根忽略目录备份/复制/暂存数据、6文档交付；本轮42只写7份文档，不改代码/local/persona/图库/历史或秘密，不安装、启停、登录、真实模型/QQ/群/SSH，不碰其他根/A4。下轮用户发送42指令时才生效其列明的代码/开关/受管加载及受控试验授权，不从规划文件自行获得真实执行权。

## 后续排序与含义

用户最新范围覆盖旧排序：42先记忆/关注与B站退役，再成员外部适配和当前DeepSeek图片链，最后统一加载；一个能力缺口不拖住可独立部分。记忆无需先开成员/视觉；识图支持由用户确认，重点验证CLI像素输入/预算/质量与原群返回，不自动换后端。网页读取和搜索质量差额保持。

成员是小群名册候选/受控@，现硬暂停，42补官方只读强刷来源而保留1..49/双TTL；关注是free叫名/引用/短续聊，现关闭。B站由“退出近期路线”进一步明确为撤下运行功能和入口，旧配置兼容在42计划中处理；本轮仍不删代码。最新合同以[42计划](tasks/LAP-42/PLAN.md)为准。

## 本次归属与检查点

2026-10-25 16:32（Asia/Shanghai），LAP-42-snow-feature-rollout-plan登记并重读。起点HEAD/实时远端9bb1b58270dbcaa3c5e40c53f804d5e50c54449b，Git干净；7文档归属见42交接。20项本机保护状态纳入核对，当前只读/详规；交付后释放归属并停止。

2026-10-25 16:07（Asia/Shanghai），session `LAP-21-snow-memes-data-migration`，精确归属及起点见21交接；本轮6份文档及忽略的7图/pending/批次备份脚本。7图已复制、7条暂存，目标运行中未激活，20项合成回归与独立数据检查通过；交付后释放归属，不续其他任务。

2026-10-25 15:49（Asia/Shanghai），session `LAP-21-snow-controlled-memes-plan`续LAP-21，仅7份文档：PROGRESS、本工作线HANDOFF/TASKS、21 HANDOFF、新SNOW_MIGRATION_PLAN/SNOW_MEDIUM_START、BOT_USAGE_COMPARISON。15:46开始只读，本地/实时远端均e2d9a0c082f3400904d8a4032eb01b4290ef08a8，开始无非忽略差异；登记已重读。源7条及5 GIF/2 JPEG共4,100,086字节通过现有路径/解码/hash校验，候选7项/1134字节；新根catalog/pending不存在，未据此推断运行状态。代码测试未运行，文档/保护摘要与Git检查见21交接。交付后释放归属并停止。

## 历史接续

需要查历史时打开[整理前完整交接](../../docs/archive/pre-snow-mainline-2026-10-25/LAPTOP_HANDOFF.md)或具体任务，不重读所有历史。

- [LAP-39 NapCat故障观察](tasks/LAP-39/HANDOFF.md)：只作旧根历史，不能推断Snow当前故障。
- [LAP-38后续功能/独立微信规划](tasks/LAP-38/HANDOFF.md)：仅用户指定后推进，不自动启用。
- [LAP-37人工清理恢复](tasks/LAP-37/HANDOFF.md)：保留维护边界，不删除任务台账或依赖锁。
- [家庭5070备用路线](../local-5070/HANDOFF.md)：原有后端保留，未在本轮认证或调用。
