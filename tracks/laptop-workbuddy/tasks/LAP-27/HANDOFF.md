# LAP-27 关注、指代与自然续聊

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承AGENTS；合同为[LAP-26 PLAN](../LAP-26/PLAN.md)3/4/8—11与[SPEC](../LAP-26/IMPLEMENTATION_SPEC.md)2—4/9/10。

2026-10-18 18:37（Asia/Shanghai）领取；session `LAP-27-attention-v2`。用户说明设置为gpt-6.1-sol/medium，不检测/切换。起点main工作区干净，单session独占本任务代码与共享台账，无真实实例执行归属。

目标：可信本机身份、封闭v2/source/effective manifest，router全局优先dispatcher（Q/R保留槽、冻结target/依赖、单活动直至ACK），叫名/引用/60秒焦点/每群滚动候选额度与对象归因、随机脱敏trace；attention默认false、mentions与全关v1保持；兼容导出与配置菜单同步。

归属：src/qqbot_gateway/{participation,group_protocol,contracts,model_gateway,turn_budget,persona,web_retrieval,config}.py及本任务新增identity/attention/v2辅助，plugins/qq_router/{main,provider}.py，scripts/{configure_bot,verify_lap27}.py，config/settings.example.yaml，tests/test_lap27.py及必要受影响测试，README、reports/lap-27-*、本文件、PROGRESS、工作线HANDOFF/TASKS。

验收：ATT-01—12独立测试与verify_lap27；实际run_agent、两实际runner底层替身、原event及ACK；旧受影响路径回归。只用自造夹具，不覆盖旧报告。未来材料固定空字段，不实现下载/成员RPC/@/持久记忆。

边界：不改忽略本机配置/凭据，不启停/登录/探活真实bot，不调用真实模型/QQ/群发，不读重放私密附件。31A已交付、31B完整覆盖/恢复未交付和unknown阻断不变；不推进28/29/30。

当前检查点：2026-10-18，**已实现/离线通过，真实/完整验收未做**。起点main/`e4aead1`干净；所有当前修改均归本任务，未发现用户或其他session差异。完整ATT-01—12与合同、配置/回滚见[报告](../../../../reports/lap-27-2026-10-18.md)。

完成：可信本机(bot/group/user/message)映射及每票随机ref；封闭v2、source/effective digest/manifest与完整plan hash；router全局Q/R优先dispatcher、同级FIFO/单活动直到ACK、32KiB单票/256KiB待处理、独立direct不合并/冻结target和必要ACK依赖；可靠叫名、Reply、入站60秒/零插话焦点、滚动candidate额度与silent、对象归因；typed文本provider和随机trace贯通；配置菜单/示例/旧schema3审阅副本、停机锁/双摘要显式激活，不自动启用。v2未来材料保持空，不实现28/29/30。

验证：`.venv/Scripts/python.exe -X utf8 scripts/verify_lap27.py`退出0，301单元（18新增ATT专项）及28组合732实际框架通过；16种v2 web/memes组合348例、12种旧路径组合384例。真实build_main_agent/run_agent/provider、两实际runner底层替身、原event逐条ACK，没有手工补成功metadata。收口后全301单元再次通过；小RAM窗口不吞target及真实@同时引用bot依赖有专项边界证据。最后调用同一verify函数对CLI/single/web关闭/memes关闭补验22例，包含纯媒体占位零生成，退出0；[矩阵](../../../../reports/lap-27-framework-offline.json)/[汇总](../../../../reports/lap-27-offline.json)/[补验](../../../../reports/lap-27-edge-framework-offline.json)。当前独立verify也已纳入此新边界，后续全矩阵计数会增加；732矩阵+22复验分别记录，不冒称754种独立能力。没有运行旧verify main或覆盖旧报告。忽略控制台工件为state/lap27-*.log。

实际框架发现的typed text归一化、随机trace专用HTTP hook接入，以及自造CLI stdin UTF-8捕获/随机ref数字子串测试均已收口；没有方案级能力缺口。所有单次尝试、CLI工具/MCP隔离、SSH模型/digest/未知解除、黑名单前置与私聊关闭保持。mentions仍仅真实@、原群+用户历史；attention默认false，本机未开启。当前真实bot状态/加载版本未知，0本机忽略配置/凭据/人设/启停/探活/登录/真实模型/QQ/群发/私密附件操作。

修改：src/qqbot_gateway/{attention.py,turn_v2.py,participation.py,group_protocol.py,contracts.py,model_gateway.py,backends.py,web_retrieval.py,persona.py,config.py,onebot_gate.py}；plugins/qq_router/{main.py,provider.py}；scripts/{configure_bot.py,verify_lap27.py}；config/settings.example.yaml；tests/{test_lap27.py,test_participation.py}；README；reports/lap-27-*；本HANDOFF、PROGRESS、工作线HANDOFF/TASKS。未改本机配置、config/persona.md或其他任务文件。

生效/回滚：仅操作者在free下显式开启attention，停机保存、正常重启加载；全关仍v1，mentions填写attention也不扩大触发。回旧代码前审阅导出的旧schema3副本，显式确认和双摘要复核后才能激活；保留历史/图库/ACK/pending/unknown和CLI清理台账，旧版不能尊重未决清理时保持停机。具体CLI动作见README/报告，本轮只在临时根测试，没有对本机执行。

剩余：真实语义效果/别名接受/排队和QQ ACK待用户另定唯一执行范围；31B完整覆盖/恢复、18搜索、24登录及旧真人差额保留。下一步等待用户后续指令，不自动开始28/29/30，不部署。

Git交付：内容提交`e115774291daee499cd0edda4d25f078d3898309`已推送origin/main，`git rev-parse HEAD`和`git ls-remote origin refs/heads/main`完整SHA一致；内容检查点已跟踪工作区干净。恰27份上述本任务文件，240本地链接/围栏、Python AST、JSON解析及暂存diff --check通过；旧报告/本机配置/凭据/私密附件未夹带。忽略的state/lap27测试日志保留，没有用户未提交修改需要纳入。此记录另提交/推送并再次核对远端，最终记录SHA见会话回执。Git不等于部署或真实/完整验收。
