# LAP-28 当前交接：阶段C代码/离线交付，真实与可信上界仍缺

2026-10-22最新规划：[LAP-38 QQ合同](../LAP-38/QQ_VISION_WEB_PLAN.md)补Windows/GGUF实际路径固定源码链、零生成收集器/尺寸域上界/激活工件与分批验收；[medium指令](../LAP-38/IMPLEMENTATION_GUIDE.md)第2段用于后续R代码/离线任务。仅规划，不改本任务已实现/真实未验结论，不启用vision/自动换后端。[38交接](../LAP-38/HANDOFF.md)。

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [I4/I5](../LAP-36/IMAGE_PLAN.md)。继承AGENTS，保留以下A及18日历史交接/全部旧差额。

2026-10-22，session `LAP-28-C-quality-capacity`，19:59:05+08:00领取/重读；起点工作区干净，本session独占本轮文件，无真实实例操作归属。详细[报告](../../../../reports/lap-28-C-2026-10-22.md)与[汇总](../../../../reports/lap-28-C-offline.json)。

已完成：公开初始空审阅表与缺项、固定最大视觉/模板/字节转换来源校验、完整条件派生/固定私有台账和入站/离线回查、两runner最终预算/原生hash审计；固定六例/spec绑定/SQLite FULL逐例原子预占与失败不可重试、精确结构化评分+人工审阅、自造六PNG。保留gate唯一材料/一次cap/第一图/sideband/TTL/租约/隔离，复用18最终传输未重写网络。门槛纯合成正例可达，初始生产组合仍不合格。

证据分级：已实现/离线通过；真实入站ingress_unverified，native_observed/真实质量/容量/群ACK/完整验收未过，production_eligible=false。真实模型/家庭SSH/QQ/群图/登录/启停/本机配置修改均0；默认vision=false，本机配置/人设/家庭凭据未动，不部署/不进入06。272单元通过（最终签名一致）；12组138实际框架底层替身、7专项（与全套重叠，不累加）、12条两原生编码/预算指标均单列。新增依赖0；旧用户人设23393字节预算差额保留。

剩余/回规划：现有API的version/digest/vision不能独立证明Windows/NVIDIA GGUF实际processor/projector/二进制路径；观察器只用真实观测事实，不从审阅表反填路径。所选路径可信观测、视觉/模板上界与bytes→tokens保守证明/原生窗口需sol/max规划；CLI视觉未知/无支持不换模型。审阅表初始无可用记录，不能手写eligible/缩reserve/搬Mac MLX公式来开图。A真实入站、18公网/TLS/搜索、24登录/原生归属、31B完整覆盖/恢复、07ASR及所有旧差额保留。

下一步：用户后续明确规划指令才补所选路径与上界；明确选定后端和总6次授权后才运行一个固定IQ批次，失败/取消/unknown消耗，同case不换trace重试；群同链ACK另批。脚本只导出观察，不写active或vision=true。真正启用须所选组合材料/质量/可信预算全部通过，由操作者停机审阅配置后正常启动；保持未知状态台账，不自动清理重试。

归属：vision/vision_capabilities/vision_quality、公开能力JSON、backends/两runner、config/model_gateway/router main固定root门槛、manage/configure_astrbot/configure_bot必要root/缺项接点、observe_lap28/verify_lap28_quality、test_lap28_capability/tests/fixtures/lap28-C、C报告JSON/Markdown、本交接与PROGRESS/工作线HANDOFF/TASKS。旧报告未覆盖，未改18安全传输实现。测试命令/资源/回滚见报告；临时替身进程及测试日志state保持忽略。

Git收口：33份本阶段归属文件内容提交`eb5278bcac0ce08059fcaf31d945217c48fb26a2`已推送origin/main，git rev-parse HEAD与git ls-remote完整SHA一致，核对时git status --short为空。272单元25.047秒、12组138框架22.828秒；15Python AST/7JSON解析、340本地链接/围栏、uv lock --check（29包）、暂存/工作区diff检查通过；最终离线签名172925876f03e9f5eda8da4beddbd49eb198dde4ec0a7d938426d5a6687931af一致。无非忽略本机差异，local/secrets/state保持忽略。随后仅本交接/TASKS/报告同步交付记录另提交推送，最终SHA见回执；下方旧SHA仅历史，Git不等于启用或真实验收。

---
LAP-28阶段C领取记录（现已代码/离线交付）：session `LAP-28-C-quality-capacity`，开始2026-10-22T19:59:05+08:00；本session唯一写入。归属：src/qqbot_gateway/vision.py、新vision_capabilities.py/vision_quality.py、config/vision-capabilities.json、scripts/observe_lap28.py及新verify_lap28_quality.py、tests/test_lap28_capability.py/自造夹具生成器及tests/fixtures/lap28-C六例、必要runner预算接点（backends/两runner）、config/model_gateway/router/main与manage/configure_astrbot/configure_bot仅固定root门槛/诊断接点、reports/lap-28-C-*、28 HANDOFF/PROGRESS/工作线HANDOFF/TASKS。仅I4/I5代码、审阅来源、自造夹具与底层替身；0真实模型/SSH/QQ/群图/启停/登录/本机配置修改。默认vision=false，可信上界或真实质量缺失继续拒启；旧31B/18/24等差额保留，不推进06。

# LAP-28 当前消息原生图片理解

阶段A当前（2026-10-21）：**代码/离线交付，真实ingress_unverified，生产仍拒启**。详细行为、文件/验证/资源、未验证与B/C解除条件见[阶段A报告](../../../../reports/lap-28-A-2026-10-21.md)；[本轮汇总](../../../../reports/lap-28-A-offline.json)/[实际框架矩阵](../../../../reports/lap-28-A-framework-offline.json)/[资源采样](../../../../reports/lap-28-A-resources.json)。默认inspect及synthetic已执行，真实intake-only未运行；0真实启停/登录/下载/SSH/模型/QQ。213项影响集与16组158实际框架替身通过；用户ff2e348人设既有预算回归23,393>=8,192字节失败独立记录，未修改/替换人设，最终验证器明确排除此一项。历史323/900不作本轮结果。

阶段A Git交付：内容提交`4ccf16851dad30497492be860807882ea650d6dc`已推送origin/main，HEAD与ls-remote完整SHA一致；23份归属文件经差异/暂存区检查、11份Python AST/3份JSON/364本地链接与围栏检查，uv lock --check通过。最终回归213单元/16组158框架替身，总61.188秒；旧人设预算失败单列。内容检查点无非忽略差异，persona与实际配置/凭据未修改；只保留忽略的state/lap28-A测试日志等本机工件。本交付记录另提交/推送并再次核对远端，最终SHA见会话回执；Git不是部署或真实验收。

已完成：第一image URL→一次cap/bind/租约→有界bytes→Pillow实际解码的分级诊断；闭合脱敏schema/process_host行；默认false配置/模板/旁注；独立无转发/发送/RPC的诊断gate和复用24最终管理器的受控intake-only。默认/普通日志观察不下载图。无get_image/路径读取/补拉历史/第二图替代，production与4096边界不动。新增依赖0。代码/测试/文档归属见报告及下方领取段，基线后无其他任务差异。

下一步：用户另指令才续18B安全公共网络/正文；另授权正常bot停机、指定自造群图/发送者与最多1事件、0模型/0群输出，才运行真实入站证明。只有段/URL不够，须同次bytes+decoded；无URL且有安全opaque ID的真实证据出现后才能按I3实施默认关闭fallback。28C另续领质量/可信视觉及模板上界/批次预算与派生门槛；真实生成/群ACK另批授权。保留31B/18/24及旧差额，不自动继续。

阶段A领取：2026-10-21T19:57:04+08:00，session `LAP-28-A-ingress-diagnostics`（图片入站证据与诊断工具）。按用户medium职责执行，不检测/切换模型。基线工作区干净；24 P1/P3已提交，process_host/manage无未提交修改，本轮仅增加必要诊断接口，保留24行为。归属：新增vision_ingress.py/observe_lap28_intake.py与test_lap28_ingress.py、vision/onebot_gate/config及配置模板/注释/导出必要字段、process_host/manage必要入口、适用verify与独立报告、本交接/PROGRESS/工作线HANDOFF/TASKS。先登记后实现；无真实进程操作归属，不运行intake-only，不动persona/本机配置/凭据。

目标与验收：复用准入/第一图/一次cap/租约及安全URL下载；封闭分级元数据、默认inspect与独立受管intake-only；合成证明有段无像素、URL解码、纯文字占位，入口拒绝/去敏/取消超时回收及适用实际AstrBot回归。production拒启及vision=false保持；无get_image真实必要证据，不实施fallback。真实仍ingress_unverified。阶段B/C及真实批次等待后续指令。

以下为2026-10-21历史规划记录（A实施状态以上方当前段为准）：[LAP-36总计划](../LAP-36/PLAN.md)、[图片合同](../LAP-36/IMAGE_PLAN.md)、[medium指引A/C](../LAP-36/IMPLEMENTATION_GUIDE.md)已完成；先真实入站材料，再所选后端质量/可信容量证明/派生生产门槛。现有日志无原始图像证据，本机DNS/TLS另由18B补齐；本轮没有修改28实现/启用或做真实识图。下方18日历史实现/验收差额原样保留，续作待新指令领取。

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承AGENTS及LAP-26 PLAN5、SPEC2/4/5/9/10。

领取：2026-10-18T19:12+08:00，session `LAP-28-native-vision`；用户声明设置gpt-6.1-sol/medium，不检测或切换。起点main工作区干净，27可信身份/v2已交付。本session独占任务修改，无真实实例操作归属。

目标：gate唯一材料服务、独立认证/一次cap、当前目标第一张图、RAM规范化/hash、provider仅sideband、gateway一次兑换、两原生runner同次输入、最终文字/视觉/wire预算及派生证据状态。生产默认关闭，4096仅假设，证明不足拒激活。

归属：src/qqbot_gateway的gate/contracts/turn_v2/两runner/web_retrieval/model_gateway/config及新增vision模块；plugins/qq_router；scripts/configure_bot及verify_lap28/受控验证入口；config/settings.example.yaml；tests/test_lap28及适用回归；README、reports/lap-28-*、本交接/PROGRESS/工作线HANDOFF/TASKS。

验收：VIS-01—04、适用ATT、实际provider/run_agent/两runner底层替身；独立报告不覆盖旧报告。仅自造夹具。0真实下载/模型/QQ/启停/登录，不改忽略配置凭据，不推进29/30；31B与旧差额保留。

当前：2026-10-18 19:52（Asia/Shanghai），**已实现/离线通过；未做真实识图，生产不可启用，完整验收未完成**。起点main/c44c2497干净；所有25个当前变更文件均归本session，无用户/其他session不明差异。详细合同/能力缺口/回滚见[报告](../../../../reports/lap-28-2026-10-18.md)。

完成：gate唯一材料、独立本机token只读、封闭bind/resolve与一次cap；精确HTTPS来源/DNS/peer安全、第一图、原始附件全模式剥离、RAM规范化/双hash/尺寸/TTL与取消释放。provider只传sideband、gateway一次兑换和effective图片manifest；两原生runner同次图片输入、CLI auto/显式effort工具隔离与最终文字/视觉/wire预算、共享15秒准备deadline、8MiB在途RAM租约与清理接管。ambient合并同步目标/cap，无图v2、mentions仍仅真@且旧UMO/本人历史/ACK修复保持，不保存图片/ref/cap。菜单7→20、示例、旧配置导出和README同步。

验证：`.venv/Scripts/python.exe -X utf8 scripts/verify_lap28.py`退出0：323单元、56组合900实际框架用例；28图片组合152例、28旧路径748例。VIS-01—04与适用ATT-01—12映射在报告，均自造图片/身份、实际provider/build_main_agent/run_agent/两runner底层替身/原event ACK，没有手工补成功metadata。收口后RAM真实context引用释放/TTL不延长专项共22项再次退出0；代码/库signature与[汇总](../../../../reports/lap-28-offline.json)一致，[矩阵](../../../../reports/lap-28-framework-offline.json)独立保存，没有运行旧verify main/覆盖旧报告。AST/JSON/本地链接/围栏/diff检查通过。

能力：适配器offline_passed；本机组合未做native_observed，production_eligible没有可信放行来源。4096仅reserve假设，可信模板/视觉token或patch上界及CLI/Ollama原生容量未证明；所有reserve下都拒启生产，不能用成功样图/手写status/减reserve绕过。独立scripts/observe_lap28.py已交付，本次只检查--help，未inspect/真实调用；后续需用户明确现有选定后端、样图和整轮总预算，停机锁/绑定/每用例最多一次、失败台账/unknown保持、不重试/切后端、不保存图或回答、不自动启用。可靠生产证明来源需回规划。

修改：src/qqbot_gateway/{vision,config,model_gateway,onebot_gate,ollama_ssh_runner,workbuddy_cli_runner,persona,turn_v2,web_retrieval}.py；plugins/qq_router/{main,provider}.py；scripts/{configure_bot,observe_lap28,verify_lap28,verify_lap28_framework}.py；tests/test_lap28.py；config/settings.example.yaml；README；reports/lap-28-*；PROGRESS、工作线HANDOFF/TASKS与本交接。contracts/token_budget仅核对与现路径复用，未修改。

边界：没有修改忽略本机settings/凭据或config/persona.md，没有真实下载群图、SSH/模型/QQ调用、登录/启停/探活真实bot或群发。仅本机临时假HTTP、合成图片和假CLI进程；普通测试工件state/lap28-*.log忽略保留。当前真实bot状态/加载版本未知，Git交付不等于部署。31B完整覆盖/恢复、LAP-18搜索、LAP-24登录与所有旧真人差额保留。

生效/回滚：desired默认false，手改true也在gate/router/gateway启动前拒绝；本机配置未开新功能，正常旧文字行为保留。菜单保存不启停。回旧版先停机/保留pending/unknown/清理台账，审阅导出的去attention/vision旧schema3副本并双摘要显式激活；不删历史/图库/未决状态，旧代码无法尊重未知清理时保持停机。

下一步：等待用户后续指定真实观察/规划补证或其他独立任务，不自动开始29/30。Git交付只含本任务检查过文件，见下方检查点；最终记录提交SHA见会话回执。

Git交付：内容提交`27bdec5eaeb6124bbdd60f4d10e52769ccaaa9ec`已推送origin/main，git rev-parse HEAD与git ls-remote origin refs/heads/main完整SHA一致；内容检查点工作区无非忽略差异。25份本任务文件经diff/归属、AST/JSON、238本地链接/围栏检查；旧报告、本机配置/凭据/私密群消息未夹带。仅忽略的state/lap28测试日志/临时测试工件保留。此交付记录另提交并推送，再核对远端；不部署、不补发、不开始29/30。
