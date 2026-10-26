# LAP-42：Snow既有功能整合与B站退役

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [AGENTS](../../../../AGENTS.md)。当前[真实闭环详规](VISION_CLOSURE_PLAN.md) / [官方输入合同](CLI_PROMPT_CONTRACT.md) / [本次medium指令](VISION_CLOSURE_MEDIUM_START.md)。旧[收尾详规](VISION_FINISH_PLAN.md)/[旧视觉指令](VISION_MEDIUM_START.md)和[整合PLAN](PLAN.md)/[旧整合指令](MEDIUM_START.md)均为历史，不整轮再跑。

## 当前检查点：真实契约通过、源码冻结、固定六例待人工审阅

2026-10-26T20:42:55.248901+08:00（Asia/Shanghai）：用户明确授权总上限7次（原意外请求1已耗+六例6），群图最多2；未授权换模型/后端/额度。原失败/隔离/known-zero协议失败和授权账目全保留，不改写成质量通过。当前停止/保护已核对，无运行配置变更。

97单元/39框架通过，当前实际CLI正向1本地user/0 next/0远端；两项反向0 user。修复native-only系统规则注入、公共toApiMessages丢图片造成的误判；原生stdin帧父子双重核验。prompt.context纯函数无I/O，避免host操作再次准备context导致递归；回执移到请求内的插件兄弟目录且分阶段独立保存，防止并发覆盖。CLI及SDK内部/全局配置未改。

**代码、插件、规则、来源、helper及测试已冻结，不能在IQ后改动。** 私有`state/lap42-vision-closure/frozen-before-iq.json`保存binding/adapter/offline/probe摘要；固定batch仍`lap42-vision-closure-v2`、spec在私有iq-fixtures-lap42-v2。六例真实答案只在TTY临时显示，逐例等待本会话人工反馈并忠实转录，source=conversation_explicit_feedback，未回复不得通过，不重新生成已有答案。模型/low/free/预算保持，vision=false。

当前报告[closure-result](../../../../reports/lap-42-vision-closure-result.md)优先于以下历史停止记录；IQ/启用/群图未完成。源码检查点提交后继续同一任务，保持唯一运行与验证归属，不领取21。待审TTY会话及台账应在每次等待点登记。

## 历史：probe意外发生1次真实请求并停止

2026-10-26T20:00:31.695386+08:00（Asia/Shanghai），同session `LAP-42-vision-closure-implementation`按用户“我可以配合了”恢复。开始本地/实时远端`84da0e9d6ff0029c317dba5829634a78d69b53b9`、工作区干净；TASKS已登记重读同23路径和唯一真实执行归属，停止/配置/冻结证据重核通过。

[本轮实际结果](../../../../reports/lap-42-vision-closure-result.md) / [来源](../../../../reports/lap-42-vision-closure-sources.json)。实际21条probe尝试记录、7条本地user；1次真实DeepSeek请求/SSE（19:51:03异常后、19:51:05收到首块）后停止，无后续模型调用。该次不是成功零生成probe，也不是IQ；完成/质量未验证。IQ=0/6、群图=0/2、vision=false，无active/正常加载/群发。用户尚不需发图。

真实装载发现Node imports禁止、crypto全局不可用、直接loader用manifest.options；已改纯JS UTF-8/SHA-256和公开fs API、请求私有回执协调。prompt.compose为注册工具65，公共catalog为83；SDK工具过滤来源与空--tools、strict空MCP、deny及父进程init空工具检查保留。不能把catalog当实际SDK工具。上述实际发现均写来源审阅。

此次直接失败是turn.step块形状断言抛出后宿主继续模型路径；外层catch未成功封闭异常。已修普通校验/I/O内部try/catch、仅nonce匹配且next_calls=1/stage next与host next.called共同成立才重放。96定向单元/39框架通过，包含缺块、host读取失败、宿主called但本请求未准入、next后回执失败，以及隔离在CLI启动前拒绝。**此修复没有再次真实CLI验证**，未将离线通过晋升实际安全通过。

第一次本地user的skipRun/无响应错误伴随清理阻断，已核对登记owner/11身份退出，经原工具归档恢复（observed_only，不声称完整后代覆盖）；原归档和当时零生成事实保留。随后实际远端请求的隔离标记完整保留，历史skipRun日志不能再自动清除此标记。后续probe/IQ工具在该标记存在时0进程拒绝；不删台账/换batch/忽略标记来继续。

15份保护文件原字节/SHA保持，独立记忆/key/库、图库/21 pending、local/persona及模型/low/free未改；服务一直stopped/disconnected，外部QQ保留。未发生项目启停或群发送；只有一次既有cleanup recover归档，不读验A4/旧根/家庭SSH。

下一步先向用户交代已耗1次真实请求、原六例未开始及停止条款；继续实际probe/六例必须明确后续次数预算与新检查点。不能在原范围内装作probe零生成后另跑满六次。当前23份归属文件按长期授权检查commit/push并核对远端后释放运行/验证归属，不自行恢复free/推进21。

## 历史规划：官方投影与真实启用闭环

session LAP-42-vision-prompt-closure-plan，2026-10-26 00:00登记7文档并重读，18:34按用户“继续”恢复。开始/恢复本地与实时远端均355f7eec2971946595efd057ea3f2a5790afa6f3，codex/lap-40-snowluma；初始干净，恢复时仅本session TASKS领取段有差异。只续42，不新ID、不领21/其他功能，不派代理或切模型。

已只读核实：当前CLI完整agent文字组装之后调用官方prompt.compose，可用项目所有的当次Mod原样提供完整CLIRunner system，并通过双字段prompt.context限制CLI附加材料；正常启动在dispatch前装载，能建立首条user前检查。关键hook异常默认可能透传，需catch/step短路和父进程回执，不是仅throw。详见新输入合同，尚未实际装载插件/检查CLI。

本次计划明确补齐此前未有的active候选/停机激活入口；与实际CLI零生成检查、固定六例人工质量、vision保存/正常加载和最多两条原群图像理解/ACK/显示一起执行。源码/资产/激活代码在IQ前冻结，不再六例后改源码使binding失效；不能仅代码/离线或0/6就称完成。当前模型/low/账号/额度、预算、人设/free及其他增强保留，Snow/QQ/CLI内部不动。

独占7文档：PROGRESS、工作线HANDOFF/TASKS、本HANDOFF、新CLI_PROMPT_CONTRACT/VISION_CLOSURE_PLAN/VISION_CLOSURE_MEDIUM_START。恢复后22项保护状态新基线涵盖local/persona/图库/pending、key/目录存在及vision active/ledger摘要；不声称跨暂停状态不变，不读取真实记忆事实。本轮不改运行代码/配置，不启停/安装/登录/真实模型/QQ/群/SSH，不读验A4或其他根。完成文档检查及本任务commit/push/远端核对后释放归属停止。

2026-10-26 18:46（Asia/Shanghai）交付检查点：7份Markdown、226个本地链接、2行围栏、UTF-8/占位符/归属与git diff --check通过；锁定CLI及类型来源摘要已复核。恢复后重新取得的22项保护状态前后相同，涵盖配置/persona/图库/pending及vision active/ledger摘要和key/目录存在状态；不声称运行中记忆事实或跨暂停时段不变。已重读本任务修改，未运行代码测试/CLI/真实模型/QQ/群/启停/安装/登录/SSH，生产代码和运行配置0修改。仅提交本任务7文档；完整本地/远端SHA以最终回执为准，核对后释放规划归属并停止，不自动实施。

## 上轮视觉续作实际检查点（不是本轮真实验证）

session `LAP-42-hosted-vision-implementation`，2026-10-25 22:47:38（Asia/Shanghai）在TASKS登记精确文件与唯一受管/真实验证归属并重读。起点本地/实时远端1660f3e6c026390909caa37480ca08493305c242，分支codex/lap-40-snowluma，Git干净。不新领28/21/已开增强。

[实际结果](../../../../reports/lap-42-vision-result.md) / [当前offline](../../../../reports/lap-42-vision-offline.json) / [实际公开资源与CLI符号来源](../../../../reports/lap-42-vision-sources.json)。已实现字节/token分账、hosted null窗口/锁定容量函数、三字段身份严格kind、新固定offline和最终安全能力握手；88单元/3组39场景通过。真实0生成get_available_models确认当前supportsImages=true、low/1M输入/128000输出；已保存安全能力快照，不含rawModels/URL/Key。

**尚未完成视觉目标**：renderDefaultAgentInstructions在system覆盖后仍渲染，ownInstructions随后追加产品agent.appendInstructions；模型握手不含该文本，完整F来源界未获证。新hosted规则是partial review，准确返回CLI_POST_OVERRIDE_TEMPLATE_UNBOUNDED；不伪造模板=2048/0或写eligible。IQ静态前置未过，未建批次、0/6真实IQ、0/2群图、无人工代审；vision保持false。既有observed/decoded成功结构/下载1次/bytes已复核，normalizer相关AST未变，复用有效；不补采样或重拉旧URL。

15份保护文件（local/persona/图库/21 pending）原字节与SHA不变，私有备份/采样复核/控制结果/失败及定向日志在state/lap42-vision-finish。现场约23:00为stopped/disconnected；未启停、未改vision或其他local、未正常加载新代码。其他开关磁盘保留true，不能声称当前运行ready。自然free未追溯统计；受控0生成单列。旧E/C、家庭SSH、Snow/QQ/CLI内部、A4未触及。

验证命令：`$env:PYTHONUTF8='1'; .\.venv\Scripts\python.exe scripts/verify_lap42_vision.py`，其框架子过程使用既有AstrBot环境；offline_valid已独立复查true。新fixed offline不覆盖旧writer/报告。首次0生成辅助调用因外锁嵌套在spawn前失败（0进程/控制/user），日志保留；释放辅助外锁后唯一实际握手成功并清理无阻断。其他测试失败已修或调整为本任务必要传输组合，末次88/39全过，详见实际结果。

归属：PROGRESS、工作线HANDOFF/TASKS、本HANDOFF、使用对照；vision_capabilities/vision/token_budget/cli_control/workbuddy_cli_runner/新hosted_cli_budget；observe_lap28、新verify_lap42_vision/test_lap42_vision；code-owned两份能力JSON与reports/lap-42-vision-*。local/观察工件不提交。按长期Git授权检查/commit/push、核对本地/远端完整SHA后释放归属并停止。下一步仅处理实际CLI追加/渲染内容的有限来源合同或经确认的外层隔离方案；不自动重试IQ/启用或推进21。

历史规划合同继续保留：[详规](VISION_FINISH_PLAN.md) / [当时来源](HOSTED_CLI_BUDGET_EVIDENCE.md) / [本轮用户已发送的实施指令](VISION_MEDIUM_START.md)。本轮不是再交新计划；已完成独立代码/报告，具体未解缺口按合同交付。

## 上轮实际状态（本轮未重做）

**可用部分已实施/离线通过/配置保存/运行加载；视觉按具体缺口交付，未称完整验收。** 记忆读取/学习、关注、成员与受控@已启用，字幕退役，最终OneBot就绪；vision仍false。[实际报告](../../../../reports/lap-42-2026-10-25.md)为完整结果。只领取42，未改Snow/QQ/CLI内部、模型/后端/账号/额度。Git交付核对后释放唯一执行归属并停止。

S5交付检查：224个本地文档链接、围栏/UTF-8替换字符/私人目标ID与git diff --check均通过；原字节/候选与16项保护摘要已复核。仅交付本任务跟踪文件，真实对象/观察工件与local/persona/图库/key/记忆/pending全部忽略保留。最终提交/实时完整远端SHA一致性见本轮回执；不自引用提交号。旧规划MEDIUM_START仅作历史授权文本，不能不经新指令再次运行整轮。

| 能力 | 本轮状态 | 未验差额 |
| --- | --- | --- |
| 记忆/关注 | 读取/学习/attention已保存加载；独立HMAC key已建；164定向单元及组合回环通过 | 真实新事实持久化与清RAM回忆、叫名/引用/续聊效果未独立验收 |
| 成员/受控@ | Snow固定强刷typed观察、effective一致及独立context token已接通并加载；1..49/双TTL/单cap/最多1@保留 | 实际群名册/受控@生成/ACK/客户端未独立验收；大群/来源无效退化为普通文字 |
| 视觉 | 追加授权的新图真实JPEG下载/解码成功：1260×709→1024×576，421ms；0模型/0输出 | 视觉token/模板上界、组合原生容量未证，真实IQ与图片群生成未执行，vision=false |
| 字幕 | 运行服务、认证抓取、专用vendor/能力提示/新模板入口退役；旧false兼容、true拒启 | 旧报告保留，纯材料schema/选择函数不删；普通web不变 |

末次164单元0失败、两组AstrBot原事件/实际runner底层替身共19场景通过；末次成员8场景再通过。首120秒采样在线超时，用户后来发图未回拉；用户明确追加一次120秒/1条新图及恢复后，发图提示就绪、操作者重发确认、采样decoded成功。共两次诊断启动/两次正常加载，第二组有追加授权。原生IQ=0/6、群图片生成=0/2，未写eligible；不把入站/模拟ACK当成远端理解成功。

现场保护：仅features.yaml与chat.yaml的5个布尔值改变，16项保护摘要中persona/图库/21 pending及其他local相同。原字节/候选/双摘要、临时框架工件归档和受测对象在忽略state/lap42-rollout；真实对象ID/名册/图像/事实/秘密不提交。当前persona组合28581/30000，无提预算。末次快照free/原CodeBuddy/DeepSeek/low、web/memes及冷却0/0不变，memory/learning/attention/members/mentions=true，vision=false，无pending_restart。

自然业务单列：开始到首次停机旧实例脱敏日志可见4次真实CLI_START；停机前累计72。两次新实例检查CLI/user_messages均0；任务累计completed102、failed1，未查原消息或推定原因，保留。样本0调用不表示全轮0真实调用。真实记忆/成员/图片群ACK等旧差额保留，后续需用户指定继续，不能自动洗批/重试。

回滚按报告的停机锁/摘要/拥有字段与配对代码执行；key/库、purge、ACK/pending/unknown/清理台账、锁及21 pending保留。未回滚、未重建key、无reset/clean、未访问其他根/A4或推进其他任务。

## 规划轮领取和归属（以下为16:52之前历史）

session `LAP-42-snow-feature-rollout-plan`，2026-10-25 16:24开始只读复核，16:32（Asia/Shanghai）登记TASKS并重读。开始HEAD/实时远端均为`9bb1b58270dbcaa3c5e40c53f804d5e50c54449b`，分支`codex/lap-40-snowluma`，无非忽略差异。

42已查空闲；它负责原27/28/29/30在Snow下的组合适配、统一配置加载和06退役，旧26/38未覆盖该组合发布。不是四项从零重做；旧各任务历史/真实差额保留，medium只领42，不同时重领旧任务。

本规划仅归属7份Markdown：PROGRESS、工作线HANDOFF/TASKS、本HANDOFF、PLAN、MEDIUM_START、BOT_USAGE_COMPARISON。不改代码/local/persona/图库/历史/秘密，不安装、启停、登录/扫码、真实模型/QQ/群/SSH；不改Snow/QQ/CLI内部，不访问旧C/旧NapCat运行数据，不读验A4，不派代理或切模型。20项本机配置/persona/图库/pending及记忆key/目录/context token存在状态纳入保护。

## 核对结论

- 记忆30与关注27已有离线实现，当前关闭；新根无记忆key/目录，不迁旧聊天或HMAC key。
- 成员29硬编码生产暂停，不能只改开关。官方Snow v2.1.1只读强刷路径可供项目外部适配：get_group_info(no_cache=true)等待FetchGroupList网络结果、失败不回旧缓存；名单no_cache=true走force。1..49、双TTL与受控@门槛保留。
- 图片获取/规范化/CLI原生图片封套/原群ACK骨架已存在，GIF目前首帧。用户确认模型支持；重点验证真实像素是否进入当前CLI并由同次模型返回。生产视觉记录表为空不等于模型不支持；必要预算/质量差额仍须诚实保留。
- 旧真实intake管理路径固定拉NapCat，Snow采样要在项目外部manage/observer适配，不能照搬运行。
- B站必须从运行服务/配置入口/能力提示撤下，旧false节兼容；仅再写一遍false不算退役。
- 21交接仍为7图/7条pending准备完成，active不存在。用户“图片完成”不扩写为真实发图验收；42不动其pending，也不将这个尾项作为前置。

## 下一轮和交付边界

执行顺序：字幕退役与记忆/关注→成员外部适配→当前DeepSeek图片路径/受控尝试→组合加载与报告。某项缺口不拖住独立部分。官方Snow/QQ/CLI及高度封装内部保持原样。

新medium复制指令在用户下一轮发送时，才授予其列明的外部代码/本机开关、独立key/token、至多两次受管加载周期及有条件的受控观察；当前规划没有执行授权。普通free恢复后自然流量可能调用模型并答群，不能误报0。人工群测试不由agent代发；视觉IQ最多6次、群闭环最多2次且前置/对象明确。

文档完成检查与Git交付后释放归属并停止。逐项保留代码/离线/配置/加载/真实差别，最终SHA和保留差异见交付回执，不自引用提交号。

16:52检查点：7份Markdown、231个本地链接、4个围栏行检查通过，git diff --check通过；20项本机配置/persona/图库/pending/记忆与context存在状态前后相同。未运行代码测试，真实模型/QQ/启停操作0。仅7份已登记文档交付；当前DeepSeek视觉支持的用户补充已同步到入口/计划/medium指令。

## 实施归属

2026-10-25T16:57:28+08:00 (Asia/Shanghai): LAP-42-snow-integration-implementation owns LAP-42 only, including the sole managed runtime executor. Baseline HEAD/live remote 0752c7b9bc2c38033d86e957fdfd9d179460aea1; initial tree clean. Exact owned paths: PROGRESS.md; tracks/laptop-workbuddy/{HANDOFF.md,TASKS.md,tasks/LAP-42/HANDOFF.md}; docs/BOT_USAGE_COMPARISON.md; src/qqbot_gateway/{members,onebot_gate,config,web_retrieval,persona,bilibili_policy,bilibili_subtitles,model_gateway,vision_intake_gate,vision_capabilities,vision,workbuddy_cli_runner,config_comments}.py; src/qqbot_gateway/vendor/bilibili_fields.py; scripts/{configure_bot,configure_astrbot,manage,observe_lap28_intake,lap42_rollout}.py; plugins/qq_router/main.py; tests/{test_lap42,test_bilibili}.py; reports/lap-42-2026-10-25.md. Ignored ownership: state/lap42-rollout backups/candidate/digests; specified local flags; independent memory key/context token only when absent. Preserve all other local/persona/library/LAP-21 pending and old evidence. No agents, model switch, A4 access, old-root work.

## S0—S3检查点（加载前）

- 根/分支/本地及实时远端核验通过，规划起点是祖先，初始Git干净。16项本机配置/persona/图库/pending摘要及五份配置原字节保存于忽略的state/lap42-rollout；受测群/操作者仅保存在忽略文件。
- 字幕服务、认证/HTTP实现和专用vendor已撤下；旧材料选择/schema及历史报告脚本保留。旧false兼容、true明确拒启；普通web保留。
- 成员补固定no_cache强刷、gate内部typed请求时间窗/群/连接绑定、已审阅官方v2.1.1包摘要限定；旧NapCat/未知版本仍暂停。effective与独立context token校验已接通。
- 定向163项首次有1项菜单提示断言失败，已修正并32项成员复跑通过；没有产品逻辑失败遗留。当前CodeBuddy/free/adaptive/web/memes的实际AstrBot原事件、实际runner底层替身两组19场景通过。运行目录UTF-8需显式PYTHONUTF8=1，未改旧writer。
- 四种真实像素编码经实际CLI runner替身，同次base64/MIME/hash和返回验证通过；GIF仅首帧。当前人设19256字节，组合system24114字节，最终可见预算28581/30000；原fitter裁剪可选候选/记忆，没有修改正文或抬预算。
- 当前托管CLI 2.168.0/固定bundle支持原生图片封套；已核对DeepSeek元数据1000000输入、128000输出及low，但视觉token/模板上界及组合原生容量尚未获证，不套本地processor/projector门槛。IQ前置不满足，真实六例未调用，vision保留false；单图Snow采样仍独立推进。
- 启停前现场：官方OneBot connected，text/free运行，队列0/active=false，已完成任务102，无unknown；自然历史CLI计数72，只作停机前基线，不能归成本轮受控试验。外部手工Snow/QQ保留。

## 当前视觉实施归属

2026-10-25T22:47:38+08:00 (Asia/Shanghai): LAP-42-hosted-vision-implementation owns only LAP-42 visual continuation, sole managed instance/native IQ/real verification executor. Baseline HEAD/live remote 1660f3e6c026390909caa37480ca08493305c242, clean initial tree. Exact tracked ownership: PROGRESS.md, tracks/laptop-workbuddy/HANDOFF.md, tracks/laptop-workbuddy/TASKS.md, tracks/laptop-workbuddy/tasks/LAP-42/HANDOFF.md, docs/BOT_USAGE_COMPARISON.md, src/qqbot_gateway/vision_capabilities.py, src/qqbot_gateway/vision.py, src/qqbot_gateway/token_budget.py, src/qqbot_gateway/cli_control.py, src/qqbot_gateway/workbuddy_cli_runner.py, src/qqbot_gateway/hosted_cli_budget.py, scripts/observe_lap28.py, scripts/verify_lap42_vision.py, tests/test_lap42_vision.py, config/vision-capabilities.json, config/cli-capabilities.json, reports/lap-42-vision-offline.json, reports/lap-42-vision-result.md, reports/lap-42-vision-sources.json. Ignored ownership: state/lap42-vision-finish backups/source cache/protection, state/vision-evidence new fixed IQ ledger/candidate; conditionally only vision.enabled false->true under stopped lock. Preserve other local/persona/library/LAP-21 pending, memory and all old evidence. No subagents, A4, old roots, model or budget parameter changes.

P0: root/branch/live remote verified; ownership reread; original bytes and protection manifest saved privately before code edits. Implementation and all real stages pending.

2026-10-25T23:11:40+08:00（Asia/Shanghai）：最终交付检查：88单元/39框架场景、当前offline binding、19份归属文件编译/UTF-8/隐私ID检查、230个Markdown本地链接与围栏、git diff --check通过；15份保护原字节/SHA不变。唯一实际模型控制1次、0 user/0生成，清理无阻断。Git核对后释放本session归属，停止于已记录的完整CLI模板来源缺口。



2026-10-26T18:51:14.069564+08:00 (Asia/Shanghai): session LAP-42-vision-closure-implementation owns LAP-42 only; sole managed stop/start, CLI probe/native IQ and real group verification executor. Baseline HEAD/live remote 61124d583c3fba49c17d38a3ed549ccc6c50856b; initial tracked tree clean. Exact tracked ownership: PROGRESS.md, tracks/laptop-workbuddy/HANDOFF.md, tracks/laptop-workbuddy/TASKS.md, tracks/laptop-workbuddy/tasks/LAP-42/HANDOFF.md, docs/BOT_USAGE_COMPARISON.md, src/qqbot_gateway/workbuddy_cli_runner.py, src/qqbot_gateway/hosted_cli_budget.py, src/qqbot_gateway/vision_capabilities.py, src/qqbot_gateway/vision.py, src/qqbot_gateway/vision_mod_guard.py, scripts/observe_lap28.py, scripts/verify_lap42_vision.py, scripts/probe_lap42_vision_contract.py, scripts/activate_lap42_vision.py, tests/test_lap42_vision.py, tests/test_vision_mod_guard.py, config/vision-capabilities.json, reports/lap-42-vision-offline.json, reports/lap-42-vision-closure-sources.json, reports/lap-42-vision-closure-result.md, adapters/codebuddy_vision_guard/.codebuddy-plugin/plugin.json, adapters/codebuddy_vision_guard/hooks/hooks.json, adapters/codebuddy_vision_guard/hooks/register.ts. Ignored ownership: state/lap42-vision-closure and runtime/requests per-request plugin/options/receipts; state/vision-evidence probe, fixed IQ batch/candidate/paired active backups; conditionally only features vision.enabled. Protection original bytes/SHA saved. No subagents/model switch/other tasks/A4/old roots; source and activation helpers frozen before IQ. Fresh manage status: stopped/disconnected, model/gate/AstrBot=0; external QQ preserved.
