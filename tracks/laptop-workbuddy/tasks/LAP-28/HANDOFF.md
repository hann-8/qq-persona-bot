# LAP-28 当前消息原生图片理解

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

下一步：等待用户后续指定真实观察/规划补证或其他独立任务，不自动开始29/30。Git交付只含本任务检查过文件，提交/远端完整SHA核对记录随后补入或见最终回执。
