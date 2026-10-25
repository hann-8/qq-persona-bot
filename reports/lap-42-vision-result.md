# LAP-42 当前 DeepSeek 视觉续作实际结果

返回[PROGRESS](../PROGRESS.md) / [42交接](../tracks/laptop-workbuddy/tasks/LAP-42/HANDOFF.md)。2026-10-25，Asia/Shanghai。

## 交付结论

已实施项目外层的单位、null窗口、hosted身份和新报告接点修复；88项定向单元、3组39个原事件/实际runner底层替身场景通过。当前模型0生成握手确认supportsImages=true、支持low、maxInputTokens=1000000、maxOutputTokens=128000。**识图尚未完成：完整CLI模板F没有来源上界，IQ=0/6、群图片生成=0/2、vision=false。** 未将公开支持或离线通过写成真实理解。

基线/实时远端1660f3e6c026390909caa37480ca08493305c242；根E:/CodexWS/QQbot_Snowluma，分支codex/lap-40-snowluma。session LAP-42-hosted-vision-implementation于22:47:38登记精确归属并重读，只续42，不派代理、不切模型、不领取28/21/其他功能。最终Git回执见会话；提交不代表部署。

## 已实施的四项修复

1. InputBudget附带内部vision_kind，当前CLI/DeepSeek/low走hosted分支。text_budget保留30000 UTF-8字节，不再扣4096原生token；早期fitter、IQ-05构造及最终runner使用同一分派。2048开销、2048项目输出预留、4096视觉预留均未变，人设未裁。旧本地reserve分支保留。
2. hosted容量实现锁定resolveEffectiveContextBudget的实际语义：先过滤合法长度/去重；仅至少两个长度时，合法override/defaultLength才能生效，否则小档或maxInputTokens。模型契约容量仍取min，不把1M写进local窗口；null合法。原生O取max(项目预留,CLI所选最大输出)，128000不伪称2048已下发。
3. code-owned hosted_codebuddy_deepseek_v41_v1严格绑定backend/model/low、CLI bundle及node三字段身份；精确记录相等、未知kind/额外eligible/改身份拒绝。旧GGUF合同不改，不编造processor/projector/model_digest。managed_cli_input_review不再固定三缺项，而依据所选规则、当前安全能力和来源给具体诊断。
4. hosted固定reports/lap-42-vision-offline.json；load_production与IQ前置统一回查当前adapter signature、rule hash、verifier/test/source-audit hash。旧分支仍读旧报告，未运行旧writer或覆盖旧报告。IQ静态检查不依赖生产eligible；生产的六例持久台账/有效decoded/unknown条件保留。IQ主命令也修正了持有外层配置锁跨runner I/O的旧问题：只在快照/每例准入时持锁，并重查本机binding；独立锁回归在首例故意失败，确认只耗一次且不重试。最终payload确定后的现有get_available_models响应再次核对模型/low/能力/容量/身份，失败0 user；新增独立inspect_models复用相同隔离与清理。

## 来源与尚未解决的具体缺口

[实际来源审阅](lap-42-vision-sources.json)记录实际公开响应/固定资源SHA、锁定bundle符号位置和审阅片段hash。三份HF revision 314113f8a7dadb388215396ba5fbee2c610a04d6资源SHA与详规一致；普通UTF-8字节界、单图1024、官方role/思考/图片占位和CLI user_query字面量已复核。Tokenizers v0.22.2原文added_tokens为0，未将postprocessor.add_prefix_space误当增加内容。资源缓存在忽略state/lap42-vision-finish/sources，无权重、安装或远程代码执行。audit自身hash仅绑定审阅报告，不冒充上游原文hash。

**CLI_POST_OVERRIDE_TEMPLATE_UNBOUNDED**：锁定bundle的renderDefaultAgentInstructions在getCliSystemPromptOverride之后仍调用promptRenderer.render；ownInstructions随后通过appendInstructions追加所选agent内容。buildAgentsFromProductConfiguration的agents来自产品配置，当前get_available_models只返回models，不返回已渲染system/追加文字，也未找到适用该分支的有限长度合同。system文件覆盖因此不能证明全部额外文字消失。已编码官方有限模板部分，但它只是F的一部分，不能把它或2048字节政策开销当完整F。

所以当前只可检验必要项T+F_known+1024+max(2048,128000)，不可证明T+F_complete+V+O≤C。新规则明确是partial review，最终原生检查拒绝；不把未界定的CLI附加内容填成0，不增加“模板≤2048”硬门槛。本轮在允许的项目外层、公开来源和现有模型控制内未解决该来源缺口，不能继续消耗真实IQ。后续需要能覆盖**本次实际CLI追加/渲染内容**的有限契约或可验证的外层隔离方案；不能以改模型/预算/内部包或写eligible替代。

## 验证与真实状态

| 项目 | 实际证据 |
| --- | --- |
| 定向单元 | 88项，0失败/错误；字节反例、当前19256字节persona组合、IQ-05拟合、容量defaultLength/小档/override、O、身份/能力变化、未知kind和新报告绑定等 |
| 原事件组合 | 3组合/39场景；CodeBuddy/adaptive/free，image+memory/attention/web/memes，members+memory/attention/web/memes，silence+memory/members/attention/web/memes；原AstrBot/provider/run_agent、实际runner底层替身及原事件ACK。组合间分开验证，不声称当前hosted图片生成已通过 |
| 视觉原有边界 | 第一图/GIF首帧/坏图/超限/注入/群隔离/重放/停言/ACK/unknown由上述定向模块及框架场景验证；GIF不代表完整动画理解 |
| 原persona预算 | 新hosted字节分派已在当前persona/可选成员与记忆fitter通过；正文未输出、未改文件或抬预算 |
| 当前0生成能力握手 | 1次get_available_models，1个CLI进程调用、0 user、0真实生成；supportsImages=true、low受支持、1M输入/128000输出；无contextWindow多档字段，按锁定函数回退maxInputTokens；cleanup observed_empty、blocked=false、observed_only |
| 六例IQ/质量 | 未建新批次、未消耗用例、未人工代填；0/6，静态模板前置未满足 |
| 真实入站复用 | 既有一条observed/decoded/none、download=1、104666原bytes/316276规范bytes、1260×709→1024×576；normalize/Blob/Materials/fetch/URL节点与本轮原字节备份一致。未新下载、未回拉旧URL、未开120秒窗口 |
| 激活/保存/加载 | 未创建active、未改vision.enabled、未启停或加载；其他local/persona/图库/7条pending原字节保持 |
| 原群理解/ACK/显示 | 0/2；操作者图片与客户端反馈未进入本轮；不写完整验收 |

验证命令：`$env:PYTHONUTF8='1'; .\.venv\Scripts\python.exe scripts/verify_lap42_vision.py`。单元用既有gateway环境，框架用既有runtime/astrbot-tool/astrbot/Scripts/python.exe，输出在本任务忽略目录，不安装依赖。框架网页组合使用合成材料传输；一次额外选择body_reader=true因AstrBot环境缺提取依赖失败，未改生产提取器或把全套网页矩阵加入本轮前置。末次report.passed与offline_valid=true仅表示定向回归通过，native_iq_eligible和production_eligible均false。

0生成检查首次辅助调用在外层持有configuration_lock时遇到runner自身锁，spawn前CLEANUP_FAILED（0进程/0控制/0 user），记录保留。已修辅助调用锁范围：快照检查后释放外锁再调用runner，随后上述唯一实际握手成功，清理台账未删改或强清。最终原生握手失败/能力变化的0 user由实际runner替身验证，包括control_only竞争路径。

首次现场只读状态（约23:00）为stopped/disconnected，最终维持；与上轮ready是不同时间的事实。磁盘CodeBuddy/DeepSeek/low/free/web/memes、memory/learning/attention/members/mentions=true、vision=false。没有受管启停/群发/真实生成；未追溯本轮最初只读状态之前的自然free流量，不用受控0调用宣称整个时段自然流量0。

## 保护、回滚与交接

15份配置/persona/图库/pending文件的原字节私有备份与SHA保护清单前后相同；未改账号/群、key/记忆库、运行预算、Snow/QQ/CLI发行包或全局配置，旧E/C根和A4未访问。只记录允许的公开能力/脱敏结构，local/图/群消息/事实/名册/观察工件不提交。

本轮没有配置激活可回滚。将来撤本轮配对代码/规则时继续保留vision=false、其他local/persona/记忆key/库/purge/台账/锁/图库与21 pending；不reset/clean、不洗IQ或删unknown。旧28/21及已开增强的真实差额保留，不自动推进。代码/定向报告/本实际结果按长期Git授权交付后释放唯一执行归属；视觉目标因上面的具体来源缺口尚未完成。

2026-10-25T23:11:40+08:00（Asia/Shanghai）：最终交付检查：88单元/39框架场景、当前offline binding、19份归属文件编译/UTF-8/隐私ID检查、230个Markdown本地链接与围栏、git diff --check通过；15份保护原字节/SHA不变。唯一实际模型控制1次、0 user/0生成，清理无阻断。Git核对后释放本session归属，停止于已记录的完整CLI模板来源缺口。
