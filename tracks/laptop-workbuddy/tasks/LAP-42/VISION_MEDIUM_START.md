# 下一轮medium：完成当前DeepSeek识图闭环

返回[PROGRESS](../../../../PROGRESS.md) / [42交接](HANDOFF.md) / [识图收尾详规](VISION_FINISH_PLAN.md) / [只读来源与推导](HOSTED_CLI_BUDGET_EVIDENCE.md)。

用户在会话设置中选择gpt-6.1-sol/medium，再复制发送下面整段。此页的规划交付没有执行真实操作；用户下一轮发送这段才授予以下有界实施与验证范围。旧MEDIUM_START是上一轮历史授权，不再整轮重跑。

```text
在 E:/CodexWS/QQbot_Snowluma、分支 codex/lap-40-snowluma，用用户已选的gpt-6.1-sol/medium实际完成LAP-42的当前DeepSeek识图收尾。不要派代理、自动切模型或只交新计划。本session只续42视觉缺口，不新领旧28或21，不重做已启用的记忆/关注/成员，不推进其他功能。

先重新核对Git根、HEAD、实时远端和工作区归属。规划只读基线48f66bc192548184e4f88e23de6a357962bff85e，文档交付在其后；这是历史参考，不能reset到它，不强推、不覆盖他人差异。按PROGRESS→AGENTS→工作线HANDOFF/TASKS→tasks/LAP-42/HANDOFF.md→VISION_FINISH_PLAN.md→HOSTED_CLI_BUDGET_EVIDENCE.md→本VISION_MEDIUM_START.md→docs/BOT_USAGE_COMPARISON.md读。原PLAN/旧MEDIUM_START和旧28合同只查需要的接点，不重复接入/首次文字试用或上一轮采样。

最新事实：memory/learning/attention/members/受控@已字段级保存并加载，字幕运行服务已退役，web/free/DeepSeek/low保留。上轮QQ JPEG已真实下载并decoded，样本0模型/输出，首窗口超时保留；CLI像素输入只有实际runner底层替身通过，真实IQ=0/6、群图生成=0/2、vision=false。重新核对当前状态，不将这些历史记录当成新运行状态。7图/7条pending已准备但未激活，本session不动它们。

用户已明确deepseek-v4.1-flash支持视觉。目标是当前QQ消息第一图真实像素→现有CodeBuddy CLI单次原生输入→同一DeepSeek理解→原router/原群返回。保持当前backend/model/low/账号/credits、全部local/persona和预算参数，不转Ollama/家庭SSH，不加付费API/Key或caption/OCR/embedding模型；不改Snow/QQ/CLI发行包、SDK或高度封装内部。

修改前在TASKS登记session、Asia/Shanghai时间、精确文件和唯一受管实例/真实验证执行归属，写后重读，保存原字节/配置/persona/图库/pending保护摘要。优先拥有vision_capabilities.py、vision.py、token_budget.py、cli_control.py、workbuddy_cli_runner.py、observe_lap28.py、对应定向验证/测试和code-owned能力记录；确需小型hosted预算模块可登记后新增。其他文件依详规登记依赖；不重构已有业务。

必须完成以下具体修复，不能只再报告“缺预算”：
1. 当前CLI配置要求context_window_tokens=null，而production_diagnostics又要求num_ctx/context_window非null；按托管CLI的实际能力规则修项目判断，不能手填1000000或改CLI原生窗口配置。
2. 当前text_budget把视觉reserve=4096原生token从30000 UTF-8字节里扣除为25904；当前persona纯组合空prompt的usage=25997已被挡。保留30000字节政策、2048开销、2048输出预留和4096视觉预留的数值；hosted文字预算不再扣token，独立校验原生总容量。不能裁persona、抬预算或只修最终gate、让早期fitter/IQ仍被旧减法拦住。
3. reviewed目前要求8个GGUF运行字段，实际CLI runtime只有version/artifact_sha256/node_sha256；managed_cli_input_review固定缺3项且permits_native_iq=false。增加code-owned的明确hosted规则种类和严格分派，精确绑定当前backend/model/low/CLI+node身份；旧本地合同保留，不造云端processor/projector/model_digest，也不开放用户强制eligible开关。
4. load_production与IQ main固定回查旧lap-28-C-offline.json。hosted使用本任务新建的固定reports/lap-42-vision-offline.json及定向验证器/当前源码与规则绑定；旧分支和历史报告保持，不重跑覆盖旧writer、A4或全部历史矩阵。静态容量/输入合格可先做IQ，不能要求生产已eligible造成循环；生产仍回查六例真实持久台账和已decoded入站。

来源与预算依详规/证据落地：
- DeepSeek官方视觉文档给单图最多1024 tokens；固定官方tokenizer/encoder revision、SHA及锁定CLI符号已列在HOSTED_CLI_BUDGET_EVIDENCE.md。复核适用当前路径；普通文本上界用UTF-8字节，模板/role/思考/图片占位及CLI额外文字另计，不按base64字符数算视觉token。不加载权重或执行远程代码，优先小型有限结构/字节上界实现，无须安装tokenizers/transformers。
- 令T=全部实际可见文本的保守token上界，F=有来源的有限CLI+模型模板上界，V=1024（第一图），O=max(项目输出预留, 当次CLI生效最大输出上界)，C=当前CLI有效容量与官方所选模型契约的较小者，要求T+F+V+O≤C。F须从实际有限结构算，不把字节开销2048当已证明的模板值，不增加2048模板硬门槛。当前能力快照1M输入/128000输出仅为基线，不将输出预留2048伪称max_tokens已下发。
- C复用锁定CLI的resolveEffectiveContextBudget真实语义：有效session override→defaultLength→多档中的较小档→maxInputTokens，并核对本项目无其他override的实际命令。输出按ModelUtils实际最大输出选择/仅min覆盖语义审阅；不改模型参数。
- 扩展cli_control白名单只取supportsImages、contextWindow.defaultLength/supportedLengths及已有安全容量字段，保留legacy兼容。最终可见文本/原生payload确定后，复用现有0生成get_available_models握手，在第一条user发送前重查所选model/low/容量/支持；失败必须0 user。不落rawModels/URL/Key，不加HTTP/ACP服务或暖机。
- 来源记录的hash必须来自实际公开资源或锁定本机bundle，不把自写说明的hash冒充原文。不用其他提供方同名catalog证明本次CodeBuddy。未知模型/身份/结构/元数据变化仍拒绝，说明准确原因。

实施及验证顺序：
A. 完成上述代码/规则、拟合/IQ/runner一致分派与新固定offline接点。定向验证字节与token反例、当前persona（不输出正文）、中英emoji/特殊字串/模板、容量defaultLength/小档/输出/身份变化、0user拒绝、记录/报告绑定及既有第一图/GIF首帧/坏图/注入/停言/群隔离/ACK。用实际AstrBot原事件与runner底层替身验证当前memory/attention/members/web/memes组合，不手填成功metadata，不跑全库/旧全矩阵。无关历史差额不作前置。
B. 代码/来源/报告冻结且静态前置通过后，做现有0生成模型元数据核对；能力字段不足时先完善同一已审阅范围内的实现。通过后只运行一个IQ-01..06固定原生批次，总最多6次、每case一次，仍用当前模型/low。真值不入prompt，失败/取消/unknown耗次且停止，不换批号/trace、删台账或重复生成洗过。人工审阅必须由人操作；agent不代填yes或用自评冒充人工。缺人工时完成独立代码/报告，真实项待验。
C. 优先验证并复用42已成功的decoded记录。当前load_production回查成功结构/状态/下载1次/bytes，不因只有文本预算文件变更就强制重采样或重拉旧URL；normalizer等确变或旧记录确无效才补。仅此条件下授权一次120秒、指定授权群/操作者的1条新自造图，0模型/0bot输出；先告知准备并取得“已就绪”，再启动窗口，超时不自动重复。
D. 当前规则/元数据/固定offline/六例真实质量/有效decoded记录及原清理状态均通过后，经既有审核路径激活候选；仅拥有本机vision.enabled false→true这一字段，原字节备份、双摘要、停机配置锁、字段级原子保存和正常受管加载。其他已开记忆/学习/关注/成员/受控@不动，新装模板仍false。不热改或重建整个features。
E. 明确受测对象后，由操作者在原授权群手工发最多2条自造真实@图片请求，每条最多一次当前模型生成/原链投递，agent不代发群测试消息。核对模型确实描述图片内容、同trace/request_key/原事件发送ACK和客户端实际显示，分别记录；face ID/文件名不是像素，GIF首帧不等于理解完整动画。未获操作者显示反馈不得写完整验收通过。

本消息在下一轮发送时明确授权：
- 上述项目外部代码、公开来源核对/小型公开来源缓存、离线测试/新定向报告、私有备份/候选/真实IQ与观察台账，以及仅符合全部条件时的vision.enabled字段变更。原始图片/群消息/事实/名册/账号/秘密/local/persona和观察工件不提交。
- 复用现有runner的0生成能力握手；一个固定六例原生批次最多6次；明确对象的群图片闭环最多2次。B/C停止，A4不读不验。正常free自然流量单列，不用受控样本0调用冒充恢复后全程0调用。
- 一次主要受管加载周期；仅C的旧入站记录确无效需要补样时，再允许一次有界诊断/恢复周期。只用本根既有管理器处理有创建身份依据的项目组件，不按QQ/Node/Python名字批杀，不接管外部/手工QQ/Snow。不扫码/登录/安装/读日常密码，不删state/lock/清理台账强启。
- 受测对象优先复用上轮忽略记录并核对当前授权，ID不输出；多个群且对象未明不随意选群。缺对象/就绪/人工审阅只留对应真实步待验，继续独立工作；不能把缺少答复当授权或替人发消息。
- 不授权旧E/旧C根、Snow/QQ/CLI/全局WorkBuddy内部、家庭SSH、新API/后端/账号/额度、额外模型或任意媒体；不激活21 pending，不并领已开功能的独立群验收，不增加历史资格/proof/probe/长稳前置。

遇到普通实现问题就在合同内修好继续；只有确需改内部、换后端/额度、改预算参数或扩大访问等方案变化，才把已完成独立部分和具体缺口交回用户，不以再写一段泛泛“不支持/缺证据”代替已规划修复。来源/模板确无法有界、当次模型能力与计划不符、质量未过或unknown未清时保持vision=false，已加载其他功能继续；不手写eligible或隐去失败。

回滚只撤本任务拥有的vision.enabled/配对hosted代码与active记录，停机锁/摘要核对；保留其他local/persona和并行修改、记忆key/库/purge、IQ失败/unknown、ACK/清理台账/锁、图库与21 pending。不重建key，不reset/clean、不删台账续跑。

更新实际reports/lap-42-vision-*、PROGRESS、工作线HANDOFF/TASKS、42 HANDOFF和必要使用对照，逐项区分代码/离线/实际原生IQ/配置保存/加载/原群ACK/客户端显示。沿用长期Git授权，只commit/push本任务已检查文件到原分支，核对完整本地/实时远端SHA并报告保留差异。完成本视觉续作或具体缺口交付后释放归属并停止，不自动激活表情或推进下一项。
```
