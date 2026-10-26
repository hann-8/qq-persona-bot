# QQ主线交接：SnowLuma与共用bot业务

返回[项目入口](../../PROGRESS.md) / [AGENTS](../../AGENTS.md) / [任务台账](TASKS.md)。2026-10-26，Asia/Shanghai。保留原目录名以兼容已有链接；此处今后以SnowLuma为主线。

## 当前状态

**当前是42识图实际闭环详规，未实施**：[新计划](tasks/LAP-42/VISION_CLOSURE_PLAN.md) / [CLI输入合同](tasks/LAP-42/CLI_PROMPT_CONTRACT.md) / [新medium指令](tasks/LAP-42/VISION_CLOSURE_MEDIUM_START.md)。锁定CLI在产品追加之后调用官方prompt.compose，可经项目所有的当次Mod原样提供完整system；无须修改第三方内部。计划明确真实CLI零生成检查、固定6原生/人工质量、安全active/vision事务、实际加载及最多2群图ACK/显示，不再仅交固定缺项。其余功能/21未领取，最新运行态本轮未探测。

**LAP-42视觉续作代码/定向验证已交付，真实识图未完成**：[本轮实际结果](../../reports/lap-42-vision-result.md)。已修hosted字节/原生分账、null窗口/容量语义、三字段身份与固定新报告；88单元/39原事件框架场景通过，0生成握手确认当前模型supportsImages/low/1M输入/128000输出。完整CLI模板F仍因自定义system后渲染与产品agent追加文字未能界定，未开IQ/启用/群图；vision=false。旧decoded结构有效且normalizer未变，无需新采样。现场stopped/disconnected，未启停/加载，local/persona/图库/21 pending不变。session LAP-42-hosted-vision-implementation交付后释放唯一归属，停止于42具体缺口。

**LAP-42已实际交付可用部分**：[交接](tasks/LAP-42/HANDOFF.md) / [实际报告](../../reports/lap-42-2026-10-25.md)。记忆读取/学习、关注、成员与受控@已字段级保存并加载；字幕运行服务和入口已撤下。164单元、19项AstrBot原事件/实际runner底层替身场景通过，官方Snow强刷观察、独立token和失败退化接通。真实单图下载/解码成功，原生视觉预算/质量与图片群闭环仍未证，vision=false。模型/额度/free/web/memes及冷却0/0保留，未修改Snow/QQ/CLI内部，旧27/28/29/30差额保留。只领取42，交付后释放归属并停止。

当前**LAP-21 Snow受控表情迁移准备已完成**，见[实际结果](tasks/LAP-21/SNOW_MIGRATION_RESULT.md)。7图已复制、7条原登记已锁内暂存；5 GIF+2 JPEG共4,100,086字节，候选7项/1134字节。目标既有停机检查为运行中，未激活/加载，活动catalog仍不存在；真实图片ACK/客户端显示/GIF均未验。生产代码修改0，local/persona及当前开关/冷却保持。20项合成回归及源稳定性/目标hash/幂等合并保护复核通过，Git交付后释放归属并停止。

LAP-40官方接入与日常入口已实现/离线通过，用户已现场确认Snow可运行、QQ群可回复，最小文字首试成功。来源是用户说明，未据此认定停止/免扫码/其他功能/长稳完整验收。

LAP-41已完成新根整理：uv报告清除38,269缓存文件约626.1MiB、5份网页快照和退役提示cmd已删除，4份旧入口说明归档；少量字节码缓存因自动审批拒绝删除而保留。当前入口以Snow主线压缩整理，使用对照已交付。起点本地/远端3d3361ea、工作区原先干净，session `LAP-41-snow-mainline-cleanup-comparison`；25份保护文件摘要相同，未改生产代码/配置或启停bot。清单、限制和验证见[41 HANDOFF](tasks/LAP-41/HANDOFF.md)/[CLEANUP](tasks/LAP-41/CLEANUP.md)。

## 当前需要读的文件

- 当前：[42 HANDOFF](tasks/LAP-42/HANDOFF.md) → [闭环详规](tasks/LAP-42/VISION_CLOSURE_PLAN.md) / [输入合同](tasks/LAP-42/CLI_PROMPT_CONTRACT.md) / [本次medium指令](tasks/LAP-42/VISION_CLOSURE_MEDIUM_START.md)，再读使用对照；旧42整合及VISION_MEDIUM_START仅历史，不重跑接入、首试或已加载功能。
- 上轮：[21实际数据准备](tasks/LAP-21/SNOW_MIGRATION_RESULT.md)保留；active未激活/真实未验不阻塞42，42不动其pending。
- 日常使用：[SnowLuma使用说明](../../SnowLuma使用说明.md)。
- 旧NapCat用户：[实际bot使用对照](../../docs/BOT_USAGE_COMPARISON.md)。
- 接入/日常入口事实：[40 HANDOFF](tasks/LAP-40/HANDOFF.md)，按需要查其PLAN/桌面入口合同。
- 模型、聊天和功能配置：[config/README](../../config/README.md)，不输出本机配置原文或秘密。
- 原有所有任务及验收差额：[TASKS](TASKS.md)。其他任务仍保留，不自动展开。

## 主线合同

官方Snow只是QQ接入，gate/AstrBot/router/gateway/CodeBuddy仍承担共用bot业务。两根配置/persona前后保护摘要未变；新根7张图片及7条pending已准备，活动目录未激活，不会自动继承旧聊天历史。

NapCat旧根和旧C根不修改/启停；保留本根仍被导入的NapCat兼容代码、旧任务/报告和A4代码/产物/证据。B/C停止，不再把旧私有资格/proof/probe/原生数据证明或长稳作为首试前置。模型/账号/额度、local/persona、群历史、登录和图库不因整理自动变化。

上轮21的7图/pending保持；42仅修改计划内项目外部接点及5个本机布尔字段，创建本根独立key/token。两次诊断采样启动、两次正常加载均由本轮唯一session处理受管身份，第二组由用户明确追加120秒/1图及恢复授权；手工QQ不接管、未扫码/登录/安装，旧根/A4未访问。原始图/消息/名册/记忆/local/persona/秘密及观察工件不提交。

## 后续排序与含义

上轮42记忆/关注/成员及字幕退役已实际交付，本轮后续排序：先42当前DeepSeek视觉外层预算/原生质量/群闭环；再独立续21激活既有7图/7条pending；最后少量人工验证已开记忆/关注/成员的真实效果。只展开第一项，其余未领取，不作视觉前置。识图支持由用户确认且本轮有官方来源，保持当前CLI/模型/low/账号/额度，网页读取和搜索质量差额保留。

成员是小群名册候选/受控@，42已补官方只读强刷来源并保留1..49/双TTL/8项768字节/单cap/最多1受控@；缺来源、人数无效/大群只暂停增强。关注是free叫名/引用/短续聊，已加载，无新消息不主动发言。字幕专用网络/认证服务及vendor已删除，纯材料schema/选择函数和旧报告保留；旧专用报告脚本不适用于当前退役版本，不重跑。真实效果按42报告逐项保留，不能用开关/代码替代群验收。

## 本次归属与检查点

2026-10-26 00:00登记、18:34恢复重核，session LAP-42-vision-prompt-closure-plan续42，仅PROGRESS/本工作线HANDOFF/TASKS/42 HANDOFF及新CLI_PROMPT_CONTRACT/VISION_CLOSURE_PLAN/VISION_CLOSURE_MEDIUM_START共7文档。基线/实时远端355f7eec2971946595efd057ea3f2a5790afa6f3；恢复时仅原TASKS领取段有差异。本轮无生产/运行操作，恢复后22项保护状态重新取基线；核对/Git见42交接，交付后释放归属停止。

2026-10-25 22:19（Asia/Shanghai），session `LAP-42-hosted-vision-finish-plan`登记并重读，起点HEAD/实时远端48f66bc192548184e4f88e23de6a357962bff85e，Git无非忽略差异。独占PROGRESS、本工作线HANDOFF/TASKS、42 HANDOFF及新VISION_FINISH_PLAN/HOSTED_CLI_BUDGET_EVIDENCE/VISION_MEDIUM_START共7文档。20项配置/persona/图库/pending及key/目录存在状态保护；不改运行数据/代码，不启停/模型/群，不读验A4或其他根。检查/Git见42交接，交付后释放归属停止。

2026-10-25 16:32（Asia/Shanghai），LAP-42-snow-feature-rollout-plan登记并重读。起点HEAD/实时远端9bb1b58270dbcaa3c5e40c53f804d5e50c54449b，Git干净；7文档归属见42交接。20项本机保护状态纳入核对，当前只读/详规；交付后释放归属并停止。

2026-10-25 16:07（Asia/Shanghai），session `LAP-21-snow-memes-data-migration`，精确归属及起点见21交接；本轮6份文档及忽略的7图/pending/批次备份脚本。7图已复制、7条暂存，目标运行中未激活，20项合成回归与独立数据检查通过；交付后释放归属，不续其他任务。

2026-10-25 15:49（Asia/Shanghai），session `LAP-21-snow-controlled-memes-plan`续LAP-21，仅7份文档：PROGRESS、本工作线HANDOFF/TASKS、21 HANDOFF、新SNOW_MIGRATION_PLAN/SNOW_MEDIUM_START、BOT_USAGE_COMPARISON。15:46开始只读，本地/实时远端均e2d9a0c082f3400904d8a4032eb01b4290ef08a8，开始无非忽略差异；登记已重读。源7条及5 GIF/2 JPEG共4,100,086字节通过现有路径/解码/hash校验，候选7项/1134字节；新根catalog/pending不存在，未据此推断运行状态。代码测试未运行，文档/保护摘要与Git检查见21交接。交付后释放归属并停止。

## 历史接续

需要查历史时打开[整理前完整交接](../../docs/archive/pre-snow-mainline-2026-10-25/LAPTOP_HANDOFF.md)或具体任务，不重读所有历史。

- [LAP-39 NapCat故障观察](tasks/LAP-39/HANDOFF.md)：只作旧根历史，不能推断Snow当前故障。
- [LAP-38后续功能/独立微信规划](tasks/LAP-38/HANDOFF.md)：仅用户指定后推进，不自动启用。
- [LAP-37人工清理恢复](tasks/LAP-37/HANDOFF.md)：保留维护边界，不删除任务台账或依赖锁。
- [家庭5070备用路线](../local-5070/HANDOFF.md)：原有后端保留，未在本轮认证或调用。

## 本轮视觉续作检查点

2026-10-25T23:08:17+08:00（Asia/Shanghai）：起点HEAD/实时远端1660f3e6c026390909caa37480ca08493305c242，TASKS登记重读、15份保护原字节/SHA保存；本轮代码/来源/0生成/定向验证与限制见实际结果。不将此前历史ready当当前状态，其他任务未领取；Git核对后释放归属。
