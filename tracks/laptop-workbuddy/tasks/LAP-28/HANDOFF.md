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
