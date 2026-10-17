# LAP-25 群聊可靠性修复

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md)。

2026-10-18 00:44（Asia/Shanghai）：LAP-25由session `LAP-25-chat-reliability-fix`领取，用户明确“分析一下，修复一下”。范围：群发送当轮容错、完整输入预算、文字/表情协议恢复与错误分流；先落盘方案后实施/离线验证，不操作真实bot/模型/群或本机配置。

开始main/695a80d，工作区干净。归属：本HANDOFF/PLAN，PROGRESS、工作线HANDOFF/TASKS，task_store/reply_delivery/group_protocol/media_protocol/reply_plan/model_gateway/token_budget及必要新共用辅助模块，qq_router主插件/provider，相关tests、verify_lap20/21的兼容断言和新增verify_lap25，README/本任务报告。按实际变更收敛最终清单；不修改登录、人设、运行配置或原始私密日志。

当前：修复已实现，260单元通过；最终12组合384实际框架合成通过。A两条media_protocol_error；B八条兜底所在时段16次INPUT_TOO_LONG。原始模型输出未保存，具体格式错误未证实。方案见[PLAN](PLAN.md)。

验证：全套unittest 260通过（22.471秒）；命令`.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests`。框架入口`scripts/verify_lap25.py`从runtime/astrbot运行，使用独立临时目录、动态端口假HTTP和两后端实际runner底层替身；最终12组合384用例已核对通过，日志state/lap25-framework-final.log、独立JSON见报告。真实加载/QQ/模型效果未验。会话模型与档位由操作者设置，本任务不声称自动检测或切换。用户本轮明确授权分析及修复，按同任务完成方案与实施。

实现：group_blocked不再以历史unknown锁住新消息，group已发+未尝试区分partial；共享输出恢复器兼容围栏/缺省/单字符串/真实@安全纯文，坏图片保文字且身份哈希严格；入口和网关最终system统一裁剪，保护target与有效web_anchor并预留空候选说明；已验证群请求的业务错误返回绑定原request的error/silent元数据。无新配置/schema，不改模型与额度，不做真实启停。

完成/剩余：方案和代码、单元及实际框架合成完成；[报告](../../../../reports/lap-25-2026-10-18.md) / [合成JSON](../../../../reports/lap-25-framework-offline.json)。真实运行未接管/未加载，不以离线替代真实QQ验收；下一步用户正常关闭/启动后试用，有新失败按固定类别追踪。保持LAP-24及原有历史差额。

最终修改文件：PROGRESS、README、工作线HANDOFF/TASKS、本任务HANDOFF/PLAN；src/qqbot_gateway/{task_store,contracts,group_protocol,media_protocol,model_gateway,output_envelope,turn_budget}.py；plugins/qq_router/main.py；scripts/{verify_lap20,verify_lap21,verify_lap25}.py；tests/{test_memes,test_participation,test_lap25}.py；reports/lap-25-2026-10-18.md与lap-25-framework-offline.json。未修改登录、人设、settings、真实账本或原始日志。旧verify仅改新合同断言/新增可选场景，旧报告保留。

Git：开始与交付前远端main均695a80d6c4a88bc2e43de3a4884c67b595387aed，无其他session差异。提交前核对差异/归属与验证，推送核对后在下方记录内容SHA。

交付前检查：196个相关Markdown本地链接均存在，22份最终归属文件已检查；未发现其他session差异。新增PLAN换行统一为仓库LF后，暂存差异空白检查通过。

Git内容交付：`019700a082118b0350459347fb4e08975aa95c71`已推送origin/main，rev-parse与ls-remote完整SHA一致；内容检查点工作区干净，无保留本机差异。260单元和最终384框架均通过，196本地链接/暂存diff检查通过。本段另作交付记录提交；Git不代表当前运行实例已加载或真实验收通过。
