# 下一轮medium：跑通当前DeepSeek识图并实际启用

返回[PROGRESS](../../../../PROGRESS.md) / [42交接](HANDOFF.md) / [闭环详规](VISION_CLOSURE_PLAN.md) / [官方接口与输入合同](CLI_PROMPT_CONTRACT.md)。

用户在设置中选择gpt-6.1-sol/medium，再发送下面整段。当前会话只有规划；此段在用户下一轮发送时才授予列明的实施/真实范围。不要重复旧VISION_MEDIUM_START或整轮42整合。

```text
在 E:/CodexWS/QQbot_Snowluma、codex/lap-40-snowluma，用用户已选的gpt-6.1-sol/medium实际完成LAP-42识图闭环并符合条件后启用。不要派代理/切模型，不要再只交计划或固定missing。只续42视觉，不并领28/21或其他功能。

先重新核对根、HEAD、实时远端、工作区/归属与受管状态。规划基线355f7eec2971946595efd057ea3f2a5790afa6f3，文档交付在其后；不reset/强推/覆盖并行修改。按PROGRESS→AGENTS→工作线HANDOFF/TASKS→tasks/LAP-42/HANDOFF.md→VISION_CLOSURE_PLAN.md→CLI_PROMPT_CONTRACT.md→本VISION_CLOSURE_MEDIUM_START.md→docs/BOT_USAGE_COMPARISON.md读。旧PLAN/MEDIUM_START/VISION_FINISH_PLAN/VISION_MEDIUM_START只作历史，不整轮重跑。

上轮四项hosted外层修复已交付，88单元/39框架场景通过，0生成握手确认当前DeepSeek支持图片与low；真实JPEG入站decoded有效可复用，normalizer未变。真实IQ=0/6、群图=0/2、vision=false，尚未真实理解。当前剩余：CLI完整system仍固定拒绝、六例未跑、观察只导出observation而无安全生产激活入口。上轮stopped/disconnected只是当时记录，本轮重查。记忆/学习/关注/成员/受控@已开，B站已退役，不重做；7图/7条pending不激活、不迁历史。

用户明确当前deepseek-v4.1-flash支持视觉。本轮保留CodeBuddy/model/low/账号/credits、全部local/persona/原预算/free/web/memes/冷却0/0。用同一CLI单次原生图片，不换提供方、Ollama/家庭SSH，不加API Key/付费API/caption/OCR/embedding模型，不改Snow/QQ/CLI发行包/SDK全局对象或高度封装内部。

修改前登记session、Asia/Shanghai时间、精确文件及唯一运行/原生验证执行归属，写后重读；保存保护原字节/SHA。最小归属依新PLAN：项目adapters/codebuddy_vision_guard三份插件资产，runner/hosted_cli_budget/vision_capabilities/vision及必要接点，当前定向验证/测试、probe和activate helper、能力记录/新来源与实际报告、进度/交接/使用对照。其他依赖先登记，不重构已交付业务。

必须按已核实的官方Mod方案做：
1. 项目所有插件通过本次CLI的--plugin-dir装载，不安装市场插件或改全局配置。锁定CLI 2.168.0的ownInstructions完成渲染/产品追加之后，模块9443的prompt.compose才返回最终system；源码偏移/类型hash在CLI_PROMPT_CONTRACT。插件返回一项session section，其text为最终传入CLIRunner的完整原system，逐字节一致。不能只拿persona.md、丢掉项目策略，也不能仍让双大括号被CLI替换。
2. prompt.context同时清blocks和instructionFiles：CLI/SDK两个路径读不同字段。只移除CLI自身附加上下文，项目在原prompt里的记忆/成员/网页/群材料保留；不删真实记忆数据。仅当前NativeImage走新插件，普通文字不加载。
3. 每次在既有runtime/requests私有目录复制并核验资产，用manifest options传本请求system/长度hash、model/low/预算、nonce、probe/live和私有回执。静态源码包hash与每次manifest hash分开，不做自引用。通过engine.create就绪回执和原get_available_models握手，在首条user前核验装载/来源/身份/容量；缺插件/回执不符时0 user退出。仅视觉子进程启用函数hook开关及兼容别名，并避免继承库模式禁止值；不改全局env、HOST或鉴权来源。
4. turn.step检查已投影、本次nonce、主turn第0步、当前model/low、无工具与预算；probe始终在此短路，live合格才next一次。必须按锁定TurnStepResult返回形状及Registration.catch语义处理异常/超时；只throw会透传，不能当拒绝。未next失败不透传，已next只重放/保留原结果，不二次生成。回执失败也不放行。父进程把短路/探针标记视为本机结果/项目错误，绝不冒充AI回答发群。
5. 原deny/dontAsk/strict MCP空配置、无续接/持久化、禁自动记忆/compact及图片cap/TTL/尺寸/字节上限保持。新code-owned kind例如hosted_codebuddy_deepseek_v41_mod_v2，只替换所选组合单条partial记录，严格绑定模型/low/bundle/node/插件资产及来源；不并列两个同组合记录，不开放force/pluginPath等配置。
6. 实现完整T+F+V+O≤C：T为原system+prompt UTF-8保守界，F为投影与双上下文清空后逐项审阅的有限框架，V=1024，O=max(项目预留,当次实际CLI输出上界)，C取当前CLI有效容量与模型契约较小者。原30000/2048/2048、视觉reserve4096和窗口null全部不改；已知模板219字节只是部分，不能直接填0/219/2048冒充完整F。剩余固定文字在同一方案内核算，不裁persona/抬预算。fitter/IQ/runner使用同一kind，不简单把diagnostic改return []。

按下列顺序实际执行：
A. 实现插件/runner准入、预算、真实CLI probe、候选激活/回滚和全部必要定向验证。新增脚本probe_lap42_vision_contract及activate_lap42_vision；现有verify_lap42_vision继续生成固定当前offline，绑定新插件/helper/source/test。新closure-sources/closure-result保留旧实际报告/旧28 writer；不跑全库/旧全矩阵/A4。源码、资产、规则、审阅及激活工具全部在IQ前冻结，不能六例后再改绑定源码使其失效。
B. 操作者能配合真实阶段后，按已有受管身份停止本项目组件；已停则只核对。这属于主要停机激活恢复周期，原IQ要求require_stopped；不持配置锁跨runner I/O。外部/手工QQ/Snow不接管，不按进程名批量杀。
C. 用真实CLI进程做本机正向probe（自造图，system包含中英emoji/双大括号，投影原样且step短路）和反向缺插件/错回执0 user验证。正向有本地user但0远端生成，不称0 user或真实IQ；不能只拿替身/自填metadata/模型自述/cost=0判生效。装载/接口问题在本方案内修复后再有变化重验。若出现真实生成迹象立即停止并实记次数，不装作probe后再额外跑满六次。
D. 静态规则/预算、实际probe、当前能力与冻结offline通过后，创建一个现有IQ-01..06持久批次，总最多6次当前DeepSeek/low，每case一次。真值不入prompt；失败/取消/unknown耗次并停，不换trace/batch洗过、不删台账或重试。probe不以前置IQ/production eligible为条件，IQ检查probe，生产最后回查全套，不能循环。
E. 六例每例人工审阅无虚构/事实正确/注入安全。提前确认人在线；操作者可TTY直接输，或本会话明确逐例反馈后agent仅忠实转录到现有回调，保留来源/时间/case/回答hash。不得代判/预填yes/以未回答为通过，已有模型结果等待人工时不重新生成。
F. 必须实际完成生产启用事务。旧observer只导出observation，旧lap42_rollout apply不负责视觉，禁止整轮运行旧apply。新activate工具prepare从规则/runtime/当前offline与probe/六例台账/有效decoded派生候选，共享完整生产校验，不手编passed/eligible，不临时写active试校验。activate在配置锁/停止/双摘要和binding不漂移下备份；先原子保存已验证active，再只补features的vision.enabled=true，最后重读load_production。失败按拥有摘要恢复，不覆盖他人变更。给出实际命令和结果，不只交未运行的新脚本。
G. 正常受管加载一次，读实际生效vision=true及原模型/low/free/其他开关。明确受测授权群/操作者且告知已就绪后，由操作者手工发最多2条真实@自造图，每条最多一次模型生成/原事件投递；第一张PNG/JPEG清晰图文，第二张优先GIF自定义表情，判断首帧。agent不代发群测试。核对实际图片内容理解、同trace/request_key/原事件ACK及操作者客户端显示，分别留证。@只用于确定性验收，不改变生产free。纯face ID/无像素类型明确不可见。
H. 复用既有decoded，不回拉旧URL。只有成功记录确实失效才条件补一次120秒/1新图的0模型入站检查，先取得操作者就绪，超时不自动续窗；两条群图各自仍使用当前新消息。自然free流量与受控6+2分开记录。

本消息在用户发送后明确授权上述外部代码/项目插件/私有候选备份、必要零生成控制与probe、固定最多6次原生、最多2次群图片生成、符合条件的active及仅vision.enabled字段变更、主要受管停机激活恢复周期；仅旧decoded失效时另有一次诊断/恢复周期。正常free恢复可能自然调用原模型答群，不能称全程0调用。若需扫码/密码/安装交操作者，不自动登录/重装。受测对象优先复用忽略记录并核对，不输出ID、不随意挑群。

不授权改第三方内部、旧E/旧C/家庭SSH、模型/后端/账号/额度切换、新付费服务、额外模型、任意媒体/历史读取、无限重启/原生重试或旁路裸发。B/C停止，A4代码/产物/证据原样不读不验，不把旧Snow资格/proof/probe或长稳变成前置；本机CLI检查仅限验证这次新扩展。其他local/persona/记忆key/库/purge/图库/21 pending/参数/触发选择保持，不模板覆盖。

普通加载/接线/预算/回执/激活/测试问题在合同内修好继续，不能再以固定missing交付替代本方案。只有实际锁定版本或强制策略不允许此官方接点、必须改内部/换路径/放宽预算、真实质量未过/unknown未清等具体外部阻断才交最小事实，vision保持false；不伪造“已跑通”。缺人/对象只等待相应真实环节，不默认同意或假审阅。

回滚停机锁/摘要下只撤本任务vision.enabled/配对active/代码；保留旧active档案、IQ失败/unknown、其他local/persona与并行修改、记忆key/库/purge、ACK/清理台账/锁/图库/pending。不reset/clean、删台账洗批或重建key。普通文字不依赖新插件。

交付实际closure-result，明确代码/离线/实际CLI契约/六例真实模型/人工质量/配置保存/运行加载/原群ACK/客户端显示，不能写“完成”同时IQ=0/6。更新PROGRESS、工作线HANDOFF/TASKS、42交接和使用对照。只提交本任务检查过的代码/测试/公开摘要/脱敏报告/文档，真实消息/图片/名册/秘密/local/persona/options/nonce/观察工件不提交。沿用长期Git授权commit/push原分支，核对完整远端SHA并报告保留差异，释放归属停止，不自动激活表情或推进下一项。
```
