2026-10-24 12:38：LAP-40新会话`LAP-40-max-realentry-next`已领取材料核验与阶段3续作规划；根独占PROGRESS、工作线HANDOFF、TASKS及40交接/规划，旧根/medium已释放。先读[精简交接](tasks/LAP-40/HANDOFF.md)/[最小接续入口](tasks/LAP-40/MAX_START.md)，按缺口检索，不加载全部历史。

独立项目集成1/2/4A/4B及离线根审已交付（代码0250f54、总审144b968）；真实阶段3私有接线/probe/资格缺失、生产总拒、未切换，72h/7天未开始。用户已提供两包路径并接受EULA/PRIVACY、手工解压Snow；ZIP固定SHA256匹配，解压后Node v24.22.1及原生摘要通过，QQ安装包腾讯签名Valid。[阶段3续作计划](tasks/LAP-40/STAGE3_CONTINUATION_PLAN.md)/[材料报告](../../reports/lap-40-stage3-materials-2026-10-24.md)区分代码缺项与原生数据前置；先A0私有入口/JS-only，QQ安装/真实probe仍待可信数据机制。实际工作C:/Users/yutha/.codex/worktrees/lap-40-snowluma-impl/QQbot、codex/lap-40-snowluma-impl，基线f2bdb0c已核对远端；原运行E:/CodexWS/QQbot不动。07:10一次性唤醒已删除，不重建。

2026-10-24 00:53（Asia/Shanghai）：LAP-39续作SnowLuma替换可行性调研，session `LAP-39-SnowLuma-longrun-assessment`；现调研完成，未实施。用户强调NapCat/SnowLuma最重要的是长期运行。仅官方源码/发布/故障记录与本项目兼容面只读核对，独占PROGRESS、工作线HANDOFF/TASKS、39 HANDOFF/RESEARCH与新SNOWLUMA_ASSESSMENT.md共6份文档；不安装、不启停/注入/登录、不改代码/运行配置、不调用模型/群/SSH。开始main/3ecd9a0、工作区干净；上一现场状态只作历史，不在本轮重新探活。原版补历史/存储/内置答复在gate前，须先解决再规划72h/7天试验，见[评估](tasks/LAP-39/SNOWLUMA_ASSESSMENT.md)。

2026-10-24 00:27（Asia/Shanghai）：LAP-39续领只读复发诊断与上游调研，session `LAP-39-max-recurrence-research`；现调研完成、故障未恢复。用户要求读背景并联网找办法，期间报告再次真实@无响应；本session仅诊断/调研及文档，独占本台账、PROGRESS、工作线HANDOFF、39 HANDOFF与新RESEARCH.md；不改代码/运行配置/人设，不启停/QQ登录/模型生成/群发。开始main/04aff7b、工作区干净。22:29后无新准入、自身状态失败/资料刷新超时；全局o3试验、诊断修复与接入替换均只是候选，见[调研](tasks/LAP-39/RESEARCH.md) / [交接](tasks/LAP-39/HANDOFF.md)。

2026-10-23：LAP-18阶段C已实现/离线通过，session `LAP-18-C-body-selection-diagnostics`（00:01:00领取）。语义主体/代码表格、coverage默认及question相关整段、封闭PUBLIC_MATERIAL/default inspect交付；290单元/28组合346框架/20组合460关闭兼容、末次39专项通过。0真实公共取样/模型/QQ/SSH/启停/登录，本机配置/人设未改；搜索false。38部分公网成功且仍超时为历史，原页真实质量/旧差额保留，不自动28R/微信。 [18交接](tasks/LAP-18/HANDOFF.md)。

2026-10-22：LAP-37容量阻断修复/手动恢复完成，session `LAP-37-cleanup-capacity-recovery`（21:20领取）。128条累计身份超限已定位；容量满时仅回收系统确认退出条目，105项回归通过。21:21:50停机核验/完整备份归档后独立blocked=false，任务计数不变，bot保持停止；根清理cmd交付。用户放弃自启，项目Startup status/remove均not_installed，旧入口退役；以后手动启动24h运行。0真实模型/QQ/启停/登录，31B/真实稳定及旧差额保留。 [37交接](tasks/LAP-37/HANDOFF.md)。

LAP-28阶段C领取记录（现已代码/离线交付）：session `LAP-28-C-quality-capacity`，开始2026-10-22T19:59:05+08:00；本session唯一写入。归属：src/qqbot_gateway/vision.py、新vision_capabilities.py/vision_quality.py、config/vision-capabilities.json、scripts/observe_lap28.py及新verify_lap28_quality.py、tests/test_lap28_capability.py/自造夹具生成器及tests/fixtures/lap28-C六例、必要runner预算接点（backends/两runner）、config/model_gateway/router/main与manage/configure_astrbot/configure_bot仅固定root门槛/诊断接点、reports/lap-28-C-*、28 HANDOFF/PROGRESS/工作线HANDOFF/TASKS。仅I4/I5代码、审阅来源、自造夹具与底层替身；0真实模型/SSH/QQ/群图/启停/登录/本机配置修改。默认vision=false，可信上界或真实质量缺失继续拒启；旧31B/18/24等差额保留，不推进06。

2026-10-21（Asia/Shanghai）：LAP-18B安全公共网络/轻量正文已实现、离线与合成提取质量通过，session `LAP-18-B-public-body`（20:38领取）。232受影响单元、16组164实际框架替身及末次定向回归通过；5依赖约10.97MiB、单页<2秒/256MiB、取消/超时自有worker回收。真实七域DNS全非公网，DoH TLS verify_code=20，0可用公开正文，仍network_unverified；搜索质量false、真实生成/QQ/完整验收未过。web.enabled保存值true不变，未正常启动加载/未部署；0模型/QQ/SSH/真实bot启停/登录，24/28/人设和旧差额保留，不推进28C/06。 [报告](../../reports/lap-18-B-2026-10-21.md) / [18交接](tasks/LAP-18/HANDOFF.md)。

2026-10-21（Asia/Shanghai）：LAP-28阶段A入站诊断已实现/离线通过，session `LAP-28-A-ingress-diagnostics`（19:57:04领取）。默认inspect/内存合成可重现有段无像素、URL字节解码、文本占位；封闭日志与另行授权的受管intake-only交付，真实模式未运行。213单元/16组158实际框架替身通过，用户人设既有23,393字节预算失败单列保留。真实样本/群图/模型/QQ/SSH/启停/登录均0，仍ingress_unverified、vision=false/生产拒启；不自动推进18/真实验收。 [报告](../../reports/lap-28-A-2026-10-21.md) / [交接](tasks/LAP-28/HANDOFF.md)。

2026-10-21 19:40（Asia/Shanghai）：LAP-24 P1/P3已实现/离线通过；session `LAP-24-autostart-independent-implementation`（19:21:05领取）。固定脱敏登录事件/只读WebUI与独立DPAPI token、受控login-check-only、锁外QQ等待和一次Startup包装器/自有链接注册交付；171项受影响回归通过（30.121秒），新观察器27/Startup12项包含其中。0真实bot启停/认证/登录/6099/凭据/Startup/SSH/模型/QQ操作；原生路径/完整句柄/设备连续性及真实免扫码仍未证，data_scope=unverified。保留persona及并行LAP-36，真实D/R/部署待后续指令。 [交接](tasks/LAP-24/HANDOFF.md)/[报告](../../reports/lap-24-autostart-2026-10-21.md)。

LAP-24 P1/P3实施进行中：session `LAP-24-autostart-independent-implementation` / “自动登录观测与Startup独立代码”，开始2026-10-21T19:21:05+08:00，基线main/b23d961。唯一写入负责人为本session；文件归属：scripts/process_host.py、manage.py、configure_bot.py、新autostart.py/必要固定快捷方式辅助、开机启动机器人.cmd、src/qqbot_gateway/napcat_login_observer.py、相关observer/autostart/process_host/lifecycle测试、README/config/README、reports/lap-24-autostart-2026-10-21.md、本台账/工作线HANDOFF/24 HANDOFF/PROGRESS。按AUTOSTART_PLAN与新指引仅代码和离线夹具，0真实启停/认证/登录/6099/Startup/SSH/模型/QQ；保留用户persona差异，不动旧自然分条、runner/vendor/data_scope。

2026-10-20 22:31（Asia/Shanghai）：LAP-34旁注续作已完成，session LAP-34-inline-comments-followup（22:19领取）；6份模板/生成器改为逐参数同行注释，68项配置相关回归通过。按用户后续明确授权为已有local补旁注，并保留手改项、定向恢复旧源未改项与纠正已确认误填；原字节备份/源摘要/候选整体校验/原子写入通过，旧源不改。未运行迁移或启停/登录/探活/SSH/模型/QQ，不触及凭据/图库/记忆/人设；本机解析通过不等于进程已加载。仅归属代码/模板/文档提交，local/备份忽略，persona差异保留。 [续作报告](../../reports/lap-34-inline-comments-2026-10-20.md)；Git见34交接。

2026-10-20 20:25（Asia/Shanghai）：[LAP-34分层配置](tasks/LAP-34/HANDOFF.md)已实现/离线通过，session LAP-34-config-files-implementation；五文件/中文注释索引、安全loader/双摘要、无损迁移回滚、统一实例快照与管理动作保留、配置cmd退役完成。426单元、20组合460实际框架合成及末次30项补验通过；[报告](../../reports/lap-34-2026-10-20.md)。本机未迁移/加载，0真实bot/登录/SSH/模型/群及真实凭据/图库/记忆操作；persona差异保留不提交，人设测试用已提交基线，真实/完整未验，旧差额保留，不推进35。Git见任务交接。

2026-10-19 20:06（Asia/Shanghai）：[LAP-33人工恢复](tasks/LAP-33/HANDOFF.md)已完成一次现场状态维护，session LAP-33-manual-cleanup-recovery；用户要求降低轻微故障影响并自行关闭bot，锁内核验owner/41登记身份全退出、五端口关闭后完整备份并归档旧记录，独立cleanup status确认blocked=false。仅observed_only人工判断，不是31B完整退出证明；0代码/配置/真实模型/群操作，bot保持停止。长期分级/自动恢复未实现，真实启动效果待用户验证；归属4份文档，原记录/说明留本机忽略目录。

2026-10-19（Asia/Shanghai）：[LAP-30](tasks/LAP-30/HANDOFF.md)已实现/离线通过，session LAP-30-group-memory；396单元、68组合926实际框架（含31专项及成员/视觉+记忆组合）。稳定有界群记忆/同轮协议/文字ACK/持久purge与菜单7→22交付；默认读取/学习均关闭。0本机配置/凭据/真实记忆或真实bot/模型/QQ操作，真实/完整未验，旧差额保留；Git检查点见交接。

2026-10-18 23:58（Asia/Shanghai）：[LAP-32清理台账调试](tasks/LAP-32/HANDOFF.md)已修复已复现的临时I/O冲突与摘要文件名覆盖，95项相关离线回归通过；新增根[目录与日志说明](../../项目目录与日志说明.md)。现场23:00:52生成success但ledger_error，原OS错误未留存；真实未决仍blocked、未恢复，31B完整退出证据差额保留。0真实启停/模型/QQ/台账修改；保留LAP-29全部差异，Git交付以32交接为准。

2026-10-18 23:50（Asia/Shanghai）：[LAP-29](tasks/LAP-29/HANDOFF.md)已实现/离线通过：gate固定成员服务、双TTL/1..49、受限候选、RPC防旁路、v3 typed@/一次许可/同链ACK及失效同次剥@交付。355单元/52组合790实际框架（成员32组合288例）及32专项末次补验通过；人数新鲜度未证，生产capability_unverified、拒激活。0本机配置/凭据/真实bot/模型/QQ操作，28/31B与旧差额保留，不开始30。见[报告](../../reports/lap-29-2026-10-18.md)。

# 笔记本任务台账

2026-10-18 18:34（Asia/Shanghai）：[LAP-31](tasks/LAP-31/HANDOFF.md)的31A独立实现/离线通过，283单元、12组合384实际框架用例及旧生命周期/ModelQueue回归通过；原结果/清理状态分离、单task接管、总deadline/有界台账/零推理检查与脱敏诊断落地。31B强化探针发现breakaway请求被接受且目标成员证据不足，完整覆盖门槛未过；生产Job/完整恢复未交付、unknown继续阻断。0本机配置/真实bot/模型/QQ操作；仅31，不自动推进27—30。见[报告](../../reports/lap-31-2026-10-18.md)。

2026-10-18 13:57（Asia/Shanghai）：LAP-26完整实施合同复审完成，13:47续领/基线4cb970d干净；7份文档包含新增[精确SPEC](tasks/LAP-26/IMPLEMENTATION_SPEC.md)与五份独立复制指令。根agent独占写入、子任务只读复核；链接/围栏/diff检查通过。仍仅规划，31/27—30未领取，不操作真实bot/模型/群或本机配置。

2026-10-18 13:35（Asia/Shanghai）：LAP-26详细规划完成/未实施，session `LAP-26-group-understanding-plan`，13:14领取；6份文档/193本地链接检查及子任务只读复核。三份附件仅脱敏诊断，原始内容不入库；31清理可靠性前置，再27/28/29/30，均已规划未领取，见[26交接](tasks/LAP-26/HANDOFF.md)。不操作bot/模型/群或本机配置。

2026-10-18 00:55（Asia/Shanghai）：LAP-25已实现/离线通过，session `LAP-25-chat-reliability-fix`，00:44领取、00:55交接；260单元/384框架合成通过，文件/方案/报告见[25交接](tasks/LAP-25/HANDOFF.md)。无真实运行操作，待用户重启加载及试用。

返回[全局入口](../../PROGRESS.md) / [工作线交接](HANDOFF.md)。继承[AGENTS](../../AGENTS.md)；本轮体验增量合同见[UX_PLAN](UX_PLAN.md)，原规格见[实施计划](IMPLEMENTATION_PLAN.md)，通过标准见[验收矩阵](ACCEPTANCE.md)。

2026-10-18 00:35历史检查点：24自然分条与登录独立代码已实现/248单元/324框架合成通过；原生目录与报告读取能力缺口保留，生产回退不可启用；真实加载/登录/表达接受未验。21/22/23离线交付、18搜索及旧真人差额保留。该轮无本机凭据/settings/身份记录修改、无真实认证/启停/模型/远程修改/群发，以下旧状态与测试按对应时间理解。

LAP-12的97项离线/本机启停及16c6fd6/0d9d309推送为历史检查点；上次交接时停机，本轮未探测当前运行状态，不假定用户试用后仍停止。旧LAP-10与真人验收差额全部保留。

LAP-13实现提交`ee7f2d4`已成功推送origin/main；随后仅同步交付检查点。108项全套及末次菜单10项通过，117个链接/差异检查通过；未操作真实bot，用户persona仍保持原有未提交改动。

## 当前任务

2026-10-21 19:48（Asia/Shanghai）：LAP-36图片与轻量网页/B站详细规划完成，未实施；session `LAP-36-image-web-video-plan`，19:20领取。起点main/b23d961，24并行实现现已738ca0a独立交付并明确留下36归属段落；保留用户persona。归属六份36规划文档、PROGRESS/工作线HANDOFF/本台账与18/28旧HANDOFF指针，共11份；0代码/运行配置/启停/登录/真实模型/QQ/SSH。分级证据/配置/限额/失败/验收/回滚及四阶段[medium指引](tasks/LAP-36/IMPLEMENTATION_GUIDE.md)完成，检查/Git见[36交接](tasks/LAP-36/HANDOFF.md)。28A→18B→28C→06D分别等待后续实施指令，不合并旧差额。

2026-10-21 19:15（Asia/Shanghai）：LAP-24自动登录/开机启动详细规划续作完成，未实施；session `LAP-24-autostart-login-plan` / “保存登录状态与开机自动登录规划”，18:56领取并重读。基线`main/3e4122b4e9046f154ff9fa82d2be317413e69056`，保留用户persona差异。归属8份文档：PROGRESS、本台账、工作线HANDOFF、24 HANDOFF、旧PLAN/IMPLEMENTATION_GUIDE入口、新[AUTOSTART_PLAN](tasks/LAP-24/AUTOSTART_PLAN.md)/[medium指引](tasks/LAP-24/AUTOSTART_IMPLEMENTATION_GUIDE.md)。原生会话优先/双观测/受控验收/Startup及失败转独立环境分支完成；0代码/本机配置/启停/登录/模型/QQ操作。检查/Git见24交接；P1/P3实施等待新指令，旧24真实差额保留。

2026-10-20 20:58（Asia/Shanghai）：[LAP-35群临时停言](tasks/LAP-35/HANDOFF.md)已实现/离线通过，session LAP-35-group-silence-implementation；本地明确停言/真实@恢复、gate唯一RAM状态与签名群代际票、全输出最终栅栏/ACK、router提交边界与重启复位交付。440单元、44组合918实际框架及20组合460关闭兼容通过；[报告](../../reports/lap-35-2026-10-20.md)。本机配置/人设未改、未加载；0真实bot启停/登录/SSH/模型/QQ，真实/完整未验，旧差额保留。Git见任务交接。

文件归属见35交接；20:35登记后重读，结束20:58；用户persona保留。

LAP-35历史规划（实施状态以上段为准）：session `LAP-35-group-silence-plan` / “群临时停言/真实@恢复规划”，2026-10-20 19:18（Asia/Shanghai）领取、19:26交接；起点`main/29f75ff`，保留用户persona差异。本轮归属本台账/PROGRESS/工作线HANDOFF及[35交接](tasks/LAP-35/HANDOFF.md)/[PLAN](tasks/LAP-35/PLAN.md)/[IMPLEMENTATION_GUIDE](tasks/LAP-35/IMPLEMENTATION_GUIDE.md)共6份文档；状态/识别/全输出代际/重启重连/回滚/5步骤12验收项已定，文档检查/Git见交接。34规划不改；0代码/配置/启停/模型/群操作。两项待用户medium分别实施34→35。

LAP-34分层配置详细规划已完成，未实施：session `LAP-34-config-files-plan` / “分层配置文件规划”，2026-10-20 19:06（Asia/Shanghai）领取、19:12交接；起点`main/003f04e`，保留用户`config/persona.md`未提交差异。本轮归属为PROGRESS、工作线HANDOFF/TASKS、[34交接](tasks/LAP-34/HANDOFF.md)/[PLAN](tasks/LAP-34/PLAN.md)/[IMPLEMENTATION_GUIDE](tasks/LAP-34/IMPLEMENTATION_GUIDE.md)共6份文档；5文件职责/字段/统一快照/迁移回滚与C34/CF合同已定，文档检查通过，Git交付见交接。不改实现/运行配置，不启停/登录/模型/群操作。后续实施需用户新指令。

LAP-24实施续作独立部分已实现/离线通过：session `LAP-24-natural-login-implementation` / “LAP-24自然分条与登录独立部分实施”，2026-10-18 00:20（Asia/Shanghai）领取、00:35交接；开始main/d319811、工作区干净。归属persona.py/persona.md、napcat_login*.py、manage.py/configure_bot.py/verify_lap24.py、相关tests/verify_lap20/21合成场景、README/24报告/24 HANDOFF及进度索引。248单元/324框架用例通过；未证实原生目录/报告能力，生产回退禁用；未操作真实bot/本机配置/凭据/模型/群。详情见[24交接](tasks/LAP-24/HANDOFF.md)。

LAP-24于2026-10-18 00:05续领max详规复审，2026-10-18 00:15交接：用户明确规划/后续medium实施分工；[PLAN](tasks/LAP-24/PLAN.md)与[medium指引/复制命令](tasks/LAP-24/IMPLEMENTATION_GUIDE.md)完成。同一session仅6份文档，基线cf69570且干净。明确Worker环境继承、固定WebUI单次回退/DPAPI/实例账本与数据目录门槛；未实施/认证/启停/真实生成，17日8单元/3合成仅历史基线。

LAP-24于2026-10-17 23:42由`LAP-24-login-natural-replies-plan` / “登录持久化与自然分条排查规划”领取，23:50完成排查/详细[规划](tasks/LAP-24/PLAN.md)，未实施；[HANDOFF](tasks/LAP-24/HANDOFF.md)登记证据与文件归属。仅写本任务HANDOFF/PLAN、PROGRESS、工作线HANDOFF/TASKS；8项既有单元、3项合成协议与文档链接检查通过。后续按用户指令实施，当前无启停/登录/真实模型/群发，密码未用/保存；LAP-21代码/测试/README/报告/交接并行改动不纳入24。

LAP-21 2026-10-17 23:32续作：既有标签流程编号预览修复已实现/215单元通过，由原session独占；涉及菜单/图库校验/自造测试/README与交接索引，详见[21交接](tasks/LAP-21/HANDOFF.md)。本机素材和运行配置不读写，0真实服务操作。

LAP-20已实现/离线通过：`LAP-20-group-participation` / “LAP-20自由群聊与直接群发实施”，2026-10-17 16:19领取、16:44检查点，开始main/109f4ee且工作区干净；[HANDOFF](tasks/LAP-20/HANDOFF.md) / [报告](../../reports/lap-20-2026-10-17.md)登记归属与证据。187单元、108群聊实际框架、26网页/90原路径回归通过。默认mentions、本机未改free，未操作bot/真实模型/群发；不自动开始21。以下18/17为历史检查点，旧真人差额保留。

LAP-18独立部分已实现/离线通过、搜索未完成：`LAP-18-shared-web-implementation` / “LAP-18共用按需联网实施”，2026-10-17 16:05领取，16:15检查点；文件归属/验收见[HANDOFF](tasks/LAP-18/HANDOFF.md) / [报告](../../reports/lap-18-2026-10-17.md)。164单元、26网页实际框架合成、90原路径回归通过；最终三类公共查询均被非全局DNS拦截，候选未达质量门槛，搜索代码门槛关闭，回规划。无真实模型/bot操作/本机settings修改，不自动领取20/21。

LAP-17已实现/离线通过、真实未验：`LAP-17-dual-profile-implementation` / “LAP-17双profile与SSH原生后端实施”，2026-10-17 15:35领取；146单元/90实际框架合成及元数据通过，见[报告](../../reports/lap-17-2026-10-17.md) / [任务HANDOFF](tasks/LAP-17/HANDOFF.md)。仅17，0真实生成/启停/群发；内容提交`34f62843b29c99d746a944216cab74f85eb8e932`已推送origin/main并核对完整SHA一致；随后仅同步交付记录。

以下LAP-19为已完成的历史规划检查点：`LAP-19-dual-backend-web-plan` / “双后端、联网、自由群聊与表情包规划”，2026-10-17 14:49领取，15:01首版落盘，随后按用户追加扩为四项合同；[PLAN](tasks/LAP-19/PLAN.md)、[GROUP_CHAT_PLAN](tasks/LAP-19/GROUP_CHAT_PLAN.md)、[复制指令](tasks/LAP-19/IMPLEMENTATION_GUIDE.md)、[HANDOFF](tasks/LAP-19/HANDOFF.md)记录范围/证据/归属。本轮不实施/改运行配置，不启停/模型生成/群发。

LAP-16内容提交`2a2bb93`已推送origin/main，2026-10-17 11:36（Asia/Shanghai）用ls-remote核对完整SHA一致，已跟踪工作区无剩余差异；随后仅同步本交付记录。state中的备份/测试日志及本机settings保持忽略，未实际启用adaptive或部署/真实验收。

LAP-15内容提交`632fdc5`已推送origin/main，2026-10-17 11:09用ls-remote核对完整SHA一致，已跟踪工作区无剩余差异；原文备份/本机diff/框架scratch工件均忽略保留。随后仅同步本交付记录，未部署或真实验收。

“待领取”是尚无执行session登记；“部分完成”是已有实现/证据但缺验收；“延期”保留需求但不进入当前文本交付。表格登记不具备互斥能力，未登记也不代表其他session没有在工作。

| ID | 单一任务 | 状态与已有证据 | 依赖/推荐顺序 | 执行session | 下一步/完成出口 |
| --- | --- | --- | --- | --- | --- |
| LAP-40 | SnowLuma替换试运行 | 独立集成/离线根审完成；0250f54代码、144b968总审；现已核验两包/手工解压/同意/合格Node；[HANDOFF](tasks/LAP-40/HANDOFF.md)/[续作计划](tasks/LAP-40/STAGE3_CONTINUATION_PLAN.md) | 长期运行优先；私有接线/probe/资格缺失，72h/7天未开始，旧差额保留 | LAP-40-max-realentry-next，2026-10-24 12:38领取；根独占共享3入口及40交接/阶段3规划报告；基线f2bdb0c；旧根/medium已释放 | 计划交付后先medium A0私有入口/JS-only；真实QQ数据机制仍缺，未安装/扫码、生产总拒，原运行a798不动 |
| LAP-39 | 夜间不回复、配置保留与SnowLuma长期运行评估 | 既有修复/离线通过；复发诊断/SnowLuma调研完成，迁移未实施；[HANDOFF](tasks/LAP-39/HANDOFF.md) / [评估](tasks/LAP-39/SNOWLUMA_ASSESSMENT.md) | 用户以长期运行为首要标准；原版gate前答复/补历史/存储与干净QQ归属是迁移前置；保留o3候选/QQ诱因与旧差额 | 当前LAP-39-SnowLuma-longrun-assessment，2026-10-24 00:53登记，调研交付；独占6文档，23日归属见历史HANDOFF | 先解决前置能力缺口并详细规划，再72h/7天验证；本轮0安装/注入/启停/登录/模型/群/配置/SSH，不重新探活或默认切换 |
| LAP-38 | 识图/网页补证与个人微信接入详细规划 | completed，仅规划；[HANDOFF](tasks/LAP-38/HANDOFF.md)/[PLAN](tasks/LAP-38/PLAN.md)/[指令](tasks/LAP-38/IMPLEMENTATION_GUIDE.md) | 补18C/28R；微信独立先WX-01，旧36/验收差额保留 | LAP-38-vision-web-wechat-plan，2026-10-22 23:19领取、23:50规划收口；18份文档独占 | 公共网络/正文质量新证据、路径/激活合同与微信七份引导/hash交付；0代码/配置/模型/QQ/微信/SSH/启停，Git见交接 |
| LAP-37 | 清理容量阻断修复/人工恢复与弃用自启 | 已实现/105项离线通过/停机现场恢复通过；[HANDOFF](tasks/LAP-37/HANDOFF.md) | 既有31/33合同修复，不自动解锁unknown | LAP-37-cleanup-capacity-recovery，2026-10-22 21:20；归属见交接 | blocked=false，bot停机；清理cmd可复用；自启弃用，真实运行/31B差额保留 |
| LAP-36 | 图片识别、轻量网页理解与B站总结详细规划 | completed，仅规划；[HANDOFF](tasks/LAP-36/HANDOFF.md)/[PLAN](tasks/LAP-36/PLAN.md)/[指引](tasks/LAP-36/IMPLEMENTATION_GUIDE.md) | 28入站→18网络/正文→28质量/容量→06字幕；07 ASR仍延期 | LAP-36-image-web-video-plan，2026-10-21 19:20领取、19:48规划交接；11份文档 | 配置/有限材料/开源复用/验收和失败出口落盘；不实施/启用，Git见交接 |
| LAP-35 | 群临时停言、真实@恢复与重启复位 | 已实现/离线通过；[HANDOFF](tasks/LAP-35/HANDOFF.md)/[报告](../../reports/lap-35-2026-10-20.md) | 34已实现；原触发/ACK/清理门槛保持 | LAP-35-group-silence-implementation，2026-10-20 20:35领取、20:58交接；文件归属见HANDOFF | S35-01—05/SM-01—12离线完成；440单元/44组合918框架、20组合460关闭兼容；本机未改/未加载，真实/完整未验 |
| LAP-34 | 分层配置文件取代日常配置菜单 | 已交付；旁注续作/本机定向配置修复完成，[HANDOFF](tasks/LAP-34/HANDOFF.md) | schema3与既有能力门槛不变 | LAP-34-inline-comments-followup，2026-10-20 22:19领取；源/模板/自造测试/索引与交接归属，local仅按用户新授权处理 | 68配置回归；local正式解析通过、未启停/正常加载，真实/完整未验，persona保留 |
| LAP-26 | 清理可靠性、图片理解、free关注、成员与群记忆规划 | completed，仅规划；[HANDOFF](tasks/LAP-26/HANDOFF.md) | 24登录暂缓，25加载未知、18搜索/旧真人差额保留 | LAP-26-group-understanding-plan，13:14领取、13:47续审/13:57完成；7份文档 | 精确协议/调度/证明/记忆事务/回滚及五项独立指令完成；31→27—30待用户实施指令 |
| LAP-31 | 请求模型进程清理、阻断诊断与有证据恢复 | 部分完成：31A已实现/离线通过；31B门槛未过，见[交接](tasks/LAP-31/HANDOFF.md)；[合同](tasks/LAP-26/PLAN.md)第13节 | 新反馈反复全局拒单，建议先于27—30 | LAP-31-cleanup-reliability，18:16领取、18:34验证；文件归属见交接 | 31A的283单元/384框架通过；31B breakaway/目标Job成员缺口回规划，生产创建/管道/恢复未交付；unknown不解锁 |
| LAP-27 | free关注/第二人称与脱敏阶段trace | 已实现/离线通过；[HANDOFF](tasks/LAP-27/HANDOFF.md) | ATT-01—12；301单元/732矩阵+22边界复验；[报告](../../reports/lap-27-2026-10-18.md) | LAP-27-attention-v2；2026-10-18 18:37；文件归属见HANDOFF；根session独占 | 31A交付/31B差额保留；无真实操作，不推进28—30 |
| LAP-28 | 当前群图片的原生理解 | 阶段A/C已实现/离线通过；真实材料/质量/可信容量未过，仍拒启；[HANDOFF](tasks/LAP-28/HANDOFF.md) | [36图片合同](tasks/LAP-36/IMAGE_PLAN.md)：I4派生门槛/I5固定六例已交付；实际路径/上界待sol/max规划 | LAP-28-C-quality-capacity，2026-10-22 19:59:05领取；归属见交接；本session唯一写入者 | 仅代码/合成离线，0真实启停/登录/下载/模型/QQ/SSH；不启用vision/进入06，旧差额保留 |
| LAP-29 | 少于50人名册与受控@ | 已实现/离线通过；生产人数门槛未证；[HANDOFF](tasks/LAP-29/HANDOFF.md) | 27/28代码已交付；生产人数新鲜度未证 | LAP-29-members-typed-mention；2026-10-18T23:20+08:00；归属见HANDOFF | 355单元/52组合790框架+32专项末次补验通过；MEMB-01—04离线交付，人数新鲜度未证仍拒激活，0真实操作 |
| LAP-30 | 群独立有界长期记忆 | 已实现/离线通过；[HANDOFF](tasks/LAP-30/HANDOFF.md) / [合同](tasks/LAP-26/PLAN.md) | 27/29身份与typed协议，不要求members/vision启用 | LAP-30-group-memory，2026-10-19 00:00领取；代码/协议/菜单/验证/报告/台账归属见交接 | 396单元/68组合926框架、31专项；HMAC/有限JSON、silent与文字ACK分离、CAS/持久purge/同轮预算；真实/完整未验 |
| LAP-01 | 旧偶发后端失败记录 | 并入LAP-12；用户说明当时未登录NapCat，不再独立阻塞 | 有新独立模型失败再重开调查 | 无独立执行 | 保留旧trace证据限制，补分层状态/登录提示，不重复制造错误 |
| LAP-02 | 群入口与会话验收收尾 | 部分完成；旧真实单条/无@/两轮通过，隔离离线通过 | 新入口/历史实现收敛后，相关回归先做 | 未登记 | 补Q/P缺项、真人交错/隔离/重置，不把旧基线当新代码通过 |
| LAP-03 | 人设风格确认 | 部分完成；LAP-11人设v2已实现/暂停准入加载，当前停机；最终接受待验 | LAP-11实现后 | 未登记 | 按用户v2风格和P01做最终人工接受，不与LAP-11实现重复领任务 |
| LAP-04 | 运行恢复与文本稳定性 | 部分完成；旧脚本存在，完整恢复/长稳待验 | LAP-09—12收敛，最终使用LAP-02/03接受的版本 | 未登记 | 完成适用O项与文本观察，记录锁屏/睡眠及QQ共存边界 |
| LAP-05 | 文本交付收口 | 待领取 | LAP-09—12新U项及原LAP-02/03/04必要项完成 | 未登记 | 汇总报告、README、限制及版本；延期/不支持项不能写完成 |
| LAP-06 | B站字幕总结 | 已实现/离线通过，真实未验；[HANDOFF](tasks/LAP-06/HANDOFF.md) / [报告](../../reports/lap-06-2026-10-22.md) | 36D，18安全传输；07 ASR及完整V11保留 | LAP-06-light-subtitles，2026-10-22 20:37:21领取；归属见交接，本session独占 | 273受影响+末次25材料专项（含20字幕）、8组合88字幕/8组合118关闭兼容；anonymous/auth/真实材料/生成/ACK未验，默认false，未改local/启用 |
| LAP-07 | 无字幕本地ASR | 延期，尚未接入 | LAP-06 | 未登记 | G6及V类音频关键项；基于实际转写，不用标题代替正文 |
| LAP-08 | 试用体验改进详细规划 | completed，仅规划；[任务HANDOFF](tasks/LAP-08/HANDOFF.md) | 本轮用户只授权计划 | 当前试用体验规划会话，22:10完成 | AGENTS、UX_PLAN及索引/验收已同步；9份文档77个本地链接、U01—20一致性核对通过 |
| LAP-09 | 配置基础、授权群和黑名单 | 已实现/离线通过，真实待验；[任务HANDOFF](tasks/LAP-09/HANDOFF.md) | 第一实施任务 | LAP-09配置准入实施，2026-10-16 22:54开始，23:00交接 | 53项测试及实际框架离线通过；U04/05真实群、U07暂停准入重启加载已验证，真实群快照待用户参与；[报告](../../reports/lap-09-2026-10-16.md) |
| LAP-10 | 模型/上下文/推理强度 | 部分完成，独立实现/离线及high真实通过；[任务HANDOFF](tasks/LAP-10/HANDOFF.md) | LAP-09实现/离线通过 | LAP-10历史实施会话，2026-10-16 23:08领取，23:22交接 | 70项离线通过；原生窗口未证实、force压缩可绕过普通关闭开关，U09/10/12完整合同待规划；[报告](../../reports/lap-10-2026-10-16.md) |
| LAP-11 | 纯文本输出和人设v2适配 | 已实现/离线通过，真实待验；[任务HANDOFF](tasks/LAP-11/HANDOFF.md) | LAP-09配置合同，LAP-10后集成；能力缺口保留 | LAP-11纯文本与人设v2实施，2026-10-16 23:30领取，23:41交接 | 82项单元、5组实际框架保存/发送及入口/会话迁移通过；U03真实QQ ACK、U13/P01用户接受、U14真实群待验，暂停准入加载后已停机，真实待验 |
| LAP-12 | 一键启停、登录/状态和QQ共存 | 已实现/离线及本机启停通过，真实差额保留；[任务HANDOFF](tasks/LAP-12/HANDOFF.md) | LAP-09/10配置合同，保留LAP-10缺口 | LAP-12启停状态实施与最终停机，2026-10-16 23:43领取，23:56交接 | 97项测试及本机无推理启停通过，最终受管进程0/五端口关闭/15外部身份保留；真实登录恢复、QQ基本操作与真实请求中停机待验 |
| LAP-13 | 配置控制台与启动提示交互 | 已实现/离线通过，终端视觉待接受；[任务HANDOFF](tasks/LAP-13/HANDOFF.md) / [详细计划](tasks/LAP-13/PLAN.md) | 复用LAP-09/10配置合同、LAP-12入口；旧验收差额保留 | LAP-13配置控制台交互实施，2026-10-17 09:58领取 | 108项测试、实际入口路径通过，10:02交接；用户重新打开配置cmd体验；persona保留，真实bot不操作 |
| LAP-14 | 人设落地与分条对话调研规划 | completed，仅v2规划；[HANDOFF](tasks/LAP-14/HANDOFF.md) / [PLAN](tasks/LAP-14/PLAN.md) / [指引](tasks/LAP-14/IMPLEMENTATION_GUIDE.md) | 用户后续明确先规划、CLI优先；另授权SSH只读配置核对 | 同一LAP-14规划会话，10:31首次、10:45续领、10:57规划交接、11:01 Git交付；本任务文档归属 | `c7d2f27`已推送并核对；medium先15后16，bot新功能未实现，persona/私密资料未提交 |
| LAP-15 | 精简人设与场景表达 | 已实现/离线通过，真实加载/P01未验；[HANDOFF](tasks/LAP-15/HANDOFF.md) / [报告](../../reports/lap-15-2026-10-17.md) | 用户已明确指定；仅本任务，单条保持 | LAP-15-persona-implementation / LAP-15精简人设与场景表达，2026-10-17 11:06领取、11:09离线交接 | 原文完整hash备份；组合3618字节；108单元/5组框架回环及版本迁移通过；用户接受待验 |
| LAP-16 | 一次生成与有限分条发送 | 已实现/离线通过，未实际启用；[HANDOFF](tasks/LAP-16/HANDOFF.md) / [报告](../../reports/lap-16-2026-10-17.md) | 用户明确继续，LAP-15离线通过 | LAP-16-adaptive-delivery / LAP-16一次生成与有限分条，2026-10-17 11:16领取、11:35离线交接 | 124单元/40框架回环/原SDK-gate ACK及恢复并发通过；single兼容，真实启用/接受另列 |
| LAP-17 | 本地后端/配置切换；原群参与分支转LAP-20 | 已由[LAP-19](tasks/LAP-19/PLAN.md)已实现/离线与SSH元数据通过，真实生成/启用未验；[PC资料](../local-5070/HANDOFF.md)有模型/通道只读证据 | 两路线保留；先17→18→20→21；群参与明确拆入20不在17启用 | LAP-17-dual-profile-implementation，2026-10-17 15:35；[HANDOFF](tasks/LAP-17/HANDOFF.md)登记文件归属 | 146单元/90框架合成与SSH零推理元数据通过；内容34f6284已推送/核对；真实能力另按范围验证，不自动开始下一任务 |
| LAP-18 | 两后端共用联网检索/网页读取 | C已实现/离线通过；真实质量/完整未验；[HANDOFF](tasks/LAP-18/HANDOFF.md)/[报告](../../reports/lap-18-C-2026-10-23.md) | [38第3节](tasks/LAP-38/QQ_VISION_WEB_PLAN.md)；18B/06复用，搜索另门槛 | LAP-18-C-body-selection-diagnostics；2026-10-23 00:01:00续领，唯一归属见18交接；已离线交付 | 290单元/28组346框架/20组460关闭兼容/末次39通过；搜索false，0真实公共取样/模型/QQ/启停/SSH/登录，本机未改；旧差额保留 |
| LAP-19 | 双后端/联网/自由群聊/表情包总体详细规划 | completed，仅详细规划；内容91b96d5已推送核对；[HANDOFF](tasks/LAP-19/HANDOFF.md) / [PLAN](tasks/LAP-19/PLAN.md) / [追加合同](tasks/LAP-19/GROUP_CHAT_PLAN.md) / [指令](tasks/LAP-19/IMPLEMENTATION_GUIDE.md) | 用户明确只规划、后由gpt-6.1-sol/medium执行；17/18与追加20/21均在此设计 | LAP-19-dual-backend-web-plan / 四项总体规划，2026-10-17 14:49领取；文件归属见HANDOFF | 10份文档/143链接/21唯一ID/隐私与diff检查通过，内容commit/push及远端SHA一致；后续按指引分别实施，不部署/生成/群发 |
| LAP-20 | 自由参与群聊、@必答与直接群发 | 已实现/离线通过，真实未验；[HANDOFF](tasks/LAP-20/HANDOFF.md) / [报告](../../reports/lap-20-2026-10-17.md) | 17/18共用接口后；原17群参与分支明确拆入，黑名单/群授权保留 | LAP-20-group-participation / LAP-20自由群聊与直接群发实施，2026-10-17 16:19领取；[HANDOFF](tasks/LAP-20/HANDOFF.md)登记文件归属 | 187单元/108群框架/26网页与90原路径回归通过；默认mentions，本机未启用free；旧真人差额保留 |
| LAP-21 | QQ收藏导入/本地表情图库与发送 | 已实现/离线通过，真实未验；[HANDOFF](tasks/LAP-21/HANDOFF.md) / [合同](tasks/LAP-19/GROUP_CHAT_PLAN.md) | 20统一群发送后；收藏静态支持不当本账号已通过 | LAP-21-controlled-memes / LAP-21受控表情实施，2026-10-17 16:49领取；文件归属见交接 | 207单元、136媒体框架与108群/26网页/90旧路径通过；inbox/library/固定只读收藏RPC/meme_id/typed图片ACK与恢复落地；默认关闭、真实收藏/发图未验，见[报告](../../reports/lap-21-2026-10-17.md) |
| LAP-22 | free模式兜底回复故障修复 | 已实现/离线通过，真实待验；[HANDOFF](tasks/LAP-22/HANDOFF.md) | LAP-20/21合同内修复 | LAP-22-free-framework-delivery，2026-10-17 18:01领取 | 空链修复；207单元/132群框架/136媒体回归通过；未重启加载；归属与命令见交接 |
| LAP-23 | WebSocket断开后持续409修复 | 已实现/离线通过，真实待验；[HANDOFF](tasks/LAP-23/HANDOFF.md) | 既有连接/恢复合同内修复 | LAP-23-gate-reconnect，2026-10-17 18:47领取 | 状态写失败不再泄漏连接；212单元/18入口/实际框架门槛通过；未启动，现场首异常未完整取证 |
| LAP-24 | 自然分条/登录独立部分与自动启动续作 | P1/P3已实现/171项离线通过；真实未验；[HANDOFF](tasks/LAP-24/HANDOFF.md) / [新PLAN](tasks/LAP-24/AUTOSTART_PLAN.md) / [报告](../../reports/lap-24-autostart-2026-10-21.md) | LAP-12生命周期、34配置快照；旧自然分条不重做 | LAP-24-autostart-independent-implementation，2026-10-21 19:21:05领取、19:40交接；归属见交接 | 2026-10-22用户放弃自启，P3部署/P4自启验收不再推进；独立登录缺口保留；原生归属/设备连续性未证，密码回退仍unverified不可启用 |
| LAP-25 | 群发送容错、预算与输出解析修复 | 已实现/离线通过，真实待验；[HANDOFF](tasks/LAP-25/HANDOFF.md) / [PLAN](tasks/LAP-25/PLAN.md) | 用户明确要求分析并修复；覆盖20/21旧隔离合同，保留24交付 | LAP-25-chat-reliability-fix，2026-10-18 00:44领取、00:55交接 | 260单元、12组合384框架合成；0真实模型/群/启停，正常重启后试用 |

G0可行性、G1环境、G2通道、G3实际provider调用已有证据，见[工作线交接](HANDOFF.md#已验证与重要修复)。这是阶段基线；W02/W10等未真实制造的情形仍按验收矩阵记录，不能据此把完整W/Q/P/O标成通过。G4完整验收归LAP-02/03，G7文本相关部分归LAP-01/04/05。

## 验收差额

- LAP-10：配置/预算与选定DeepSeek/high组合有证据；原生窗口仅ACK未证实，显式值拒绝；CLI force压缩/内部恢复不能保证无额外推理，需按AGENTS回规划。统计只证实3次CLI启动（含零推理1次）、4控制、2真实user消息；不当作上游API精确次数。未部署，不删除本差额或自动改后端。
- LAP-14合同保留；LAP-15/16已实现/离线通过，真实加载/P01/群ACK与多人/停止仍未验。本机adaptive未启用，元数据/逐条回执/历史恢复已有合成离线证据；人工例子/模拟ACK不关闭LAP-03/P01或其他旧差额。
- LAP-01/LAP-12：用户补充NapCat未登录为现场原因；不再为旧错误循环真实推理。模型失败追踪`11aacf9b18`、业务追踪`a0c16673b2`的具体上游原因未留存，日志不能证明跨层因果；该限制保留。按UX_PLAN新增QQ通道/模型分层状态及登录就绪提示。
- LAP-02：P02现有证据明确为两轮口令，合同要求跨3轮；先核对原记录，仅补缺项。P03/P04离线通过不代替真人隔离；P05交错、P06重置、P07权限边界和P08超长输入等按证据逐项收尾。已通过的Q01/Q02不整套重测，除非代码变化触及相关路径。
- LAP-03/LAP-11：仓库config/persona.md已采用v2草案，固定政策优先，旧正文在本机hash备份；本次已暂停准入加载验证，当前停机。U01/02离线通过，U03模拟ACK及保存/发送一致性通过；U13真实模型风格/P01三组各两次、U14真实群仍待用户参与，不以人工拟定样例冒充模型产物。
- LAP-04：O01—O09逐项区分脚本存在、离线验证、实际运行验证；未真实制造的认证/配额失效应保留限制。文本连续观察应记录时长、版本、请求/失败数和资源情况。O10原合同为2小时混合文本/视频；文本观察通过可单列结论，不能将未实现的视频或完整O10标通过。不得仅为等待自动创建定时任务。
- LAP-05：只宣称有证据的文本交付阶段；U04—07已有LAP-09离线证据和真实差额，其余U项仍待实施。完整第一版仍包含G5/G6，不与文本阶段混称完成。基线4560ab6，本轮LAP-09按用户新授权提交/推送，运行实例未更新。

LAP-21由上述session独占实施并离线交付；不操作bot/真实收藏/模型，不启用本机memes。

## 一个session一个任务

1. 先读AGENTS、PROGRESS、HANDOFF和本表，核对git status及负责人。新功能先由AGENTS指定模型/max及以上规划、后由指定模型/medium实施。用户指定任务时按指定任务；未指定时以PROGRESS当前建议为准，不重复领取已交付任务。本轮LAP-14仅规划，不自动开始代码。
2. 在实施前将对应行改为进行中，填写session ID或可辨识标题、开始时间、涉及文件及任务交接链接；写后重读确认。已有负责人或共享文件发生不明修改时，先协调归属，不能覆盖。Markdown登记不提供原子锁，不保证同时领取无冲突。
3. 首次领取时创建`tasks/<任务ID>/HANDOFF.md`，记录目标、范围、验收条件、文件归属、最后检查点、证据和下一步，并链接回本表及根PROGRESS；在本表和PROGRESS登记该任务HANDOFF链接，保持双向可达。未领取任务不批量创建空交接文件。
4. 共用一个工作区和bot实例：不同任务可并行只读核对或处理互不冲突的文件；修改共享实现/配置、真实模型/群验收及启停服务必须先明确执行归属。记录运行实例负责人；其他session不重复启动或擅自重启，不重放旧群消息。
5. 任务有里程碑、发现问题或准备交接时，先更新自己的任务HANDOFF，再更新本表对应行；全局状态或下一建议任务变化时同步PROGRESS和工作线HANDOFF。所有时间写Asia/Shanghai，证据注明离线/真实/未验，不抄原始聊天和凭据。
6. 结束时记录已完成、剩余、修改文件、最后验证命令及结果；真正满足验收条件才标完成。有明确外部依赖时标受阻并写解除条件；主动中断则标暂停。未完成任务继续保留，不因切session归零。

## 本次盘点检查点

2026-10-16 21:35前后，只读健康页为ready、router_ready=true、queue=0、active=false、cli_attempts=7，最后模型成功21:21:24。任务库只读计数completed=9、failed=1，最后completed为21:21:25；该计数是处理状态，不是功能验收通过率。21:02失败后的4次成功来自已有试用记录，本会话没有发起推理或群消息。

上段为21:35历史。LAP-08/09—14保留；15/16离线通过、真实差额保留、adaptive未启用。19统一详细规划17/18/20/21，17/20已实现离线通过，18搜索缺口保留，21已实现/离线通过、真实未验；原17群参与由20实现但尚未启用。不抹旧需求，新任务从LAP-22起编号，不为尚未领取的实施预建空HANDOFF；任务交接与PROGRESS双向可达。
