# LAP-42续作：识图真实闭环与启用计划

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [42交接](HANDOFF.md)。[输入合同与来源](CLI_PROMPT_CONTRACT.md) / [完整medium指令](VISION_CLOSURE_MEDIUM_START.md)。

session `LAP-42-vision-prompt-closure-plan`，2026-10-26 00:00登记并重读，18:34按用户“继续”恢复，同步重核HEAD/远端与归属。基线355f7eec2971946595efd057ea3f2a5790afa6f3、codex/lap-40-snowluma；恢复时仅本session TASKS段落有差异。只续42，7份Markdown，不新建ID，不实施/启用/启停/真实模型/QQ。

## 1. 目标、证据与完成出口

目标是实际跑通“当前QQ图片→当前DeepSeek理解→原群答复”。已交付真实JPEG下载/解码、CLI原生图片封套、88单元/39框架场景与模型图片支持/low元数据；不重复接入、首试或四项外层修复。IQ=0/6、群图=0/2、vision=false为上轮实录；stopped/disconnected也只是当时现场，下一轮重查。

还差三件具体事：完整输入合同仍固定拒绝；真实六例未跑；观察脚本只导出observation，缺安全生产激活入口。本方案采用官方后组装投影Mod、实际CLI零生成契约检查、原六例、停机激活与两条人工群图闭环。架构已选定，按来源文档实现，不让medium继续泛泛研究F。

完成必须分别有：代码/来源与定向通过；实际CLI契约检查且0远端生成；六例真实模型和人工质量通过；active与vision.enabled保存/正常加载；原群两图理解、同链ACK和操作者显示确认。代码/标记/offline.passed/开关true均不能独立称识图完成。

非目标：改Snow/QQ/CLI核心、换模型/后端/提供方/账号/额度、新API Key/付费接口/其他caption或OCR模型、21激活、旧历史迁移、重做记忆/关注/成员、B站恢复、A4/B/C/家庭SSH/长稳。CLI本机契约检查只验证本次新扩展的必要接线，不复活旧Snow资格/proof/probe体系。只处理当前第一张有像素的PNG/JPEG/WebP/GIF，GIF首帧；纯face ID/无像素表情不假装看见，既有free及授权群合同保持。

## 2. 行为、配置与最小文件范围

沿用现有gate/AstrBot/router/gateway/CLIRunner、图片cap/TTL/尺寸/字节边界。仅当前NativeImage请求加载项目所有的官方Mod，把CLIRunner最终system原样投影到SDK前的公开组装点；原prompt/图片不变，普通文字不加载插件。四个事件、父进程首条user前回执、失败关闭、probe短路按CLI_PROMPT_CONTRACT。

新code-owned种类可用hosted_codebuddy_deepseek_v41_mod_v2，绑定当前backend/model/low/bundle/node/插件资产/有限框架与来源。替换当前组合的单条partial记录，不并列两行造成歧义，旧报告/来源保留。kind不是用户配置，不能只return []或手填eligible。

T/F/V/O/C使用来源公式，fitter、IQ、runner分派一致；完整system包含persona和项目策略，双大括号也须字节不变。预算数字30000/2048/2048、4096及CLI窗口null不改，当前DeepSeek/low、账号/credits/free不改。新装vision仍false，没有force/pluginPath等用户开关；实际配置只拥有vision.enabled。

实施方登记后最小拥有：

- 新adapters/codebuddy_vision_guard/.codebuddy-plugin/plugin.json、hooks/hooks.json、hooks/register.ts及必要README；本项目资产，不是第三方源码。
- src/qqbot_gateway/workbuddy_cli_runner.py、hosted_cli_budget.py、vision_capabilities.py、vision.py；cli_control/token_budget/config_files仅确需接点才改，不重构其他业务。
- scripts/observe_lap28.py、verify_lap42_vision.py、tests/test_lap42_vision.py及新guard测试；新增scripts/probe_lap42_vision_contract.py与activate_lap42_vision.py。
- 当前能力JSON、固定reports/lap-42-vision-offline.json重新定向生成；新lap-42-vision-closure-sources.json/closure-result.md，旧28报告及上轮实际结果保留。
- 进度/交接/使用对照；忽略的请求options/nonce/回执、观察/激活候选和备份。local/persona/记忆key/库/图库/21 pending均保留。

插件、helper、验证器、来源须纳入实际adapter_signature/offline_valid绑定。**激活/回滚代码也在IQ前实现、离线验证、冻结**；否则六例后再改源码会使整批失效。IQ后只写文档/结果与私有台账，不修改绑定材料或来源报告。

## 3. 实施顺序与真实验证

P0重新核对根/HEAD/实时远端/差异/负责人及受管状态；登记唯一真实执行归属、保护摘要/原字节。原VISION_MEDIUM_START和lap42_rollout apply不整轮重跑，不清台账/锁解决准入。

P1完成Mod、父进程准入、完整预算/新kind、候选激活/回滚和定向测试。静态规则不要求已production eligible，probe不要求IQ，IQ才回查当前probe，生产最后检查全套。

P2先明确操作者能配合真实阶段。若项目运行，用既有管理器停止有创建身份依据的本项目组件；若已停只核对。原IQ要求require_stopped，这次停机归随后激活恢复的主要维护周期；不接管外部/手工QQ/Snow，不持configuration_lock跨CLI I/O。

P3用真实CLI进程做正向本机契约probe与反向0 user检查，不用进程替身冒充扩展生效。正向有自造图/本地user但0远端生成；独立code-owned probe分支必须在turn.step不next，标记不进业务回复。加载/事件问题在本方案内修好后有变化地重验，不能无变化循环；若出现真实生成迹象立即停并按实记账，不能装作0生成后再额外跑满六次。

P4源码/资产/规则/报告冻结，静态预算、实际probe、当次模型能力齐全后，创建现有IQ-01..06一个固定持久批次，总最多6次当前模型/low、每例一次。真值不入prompt；失败/取消/unknown耗次且停，不换batch/trace、删台账或重试。前轮未建批次，仍须重查实际台账。

人工逐例审阅无虚构、可见事实正确、注入安全。操作者可本机TTY输入，或本会话明确逐例反馈后由agent忠实转录到现有回调，注明来源/时间/case/回答hash；不得代判、预填yes或把未答复当通过。已得到模型结果后等待人工，不重新生成。不以模型自评替代人工。

## 4. 必须补齐的启用事务

observe_lap28明确仅导出batch-observation.json，不写active；lap42_rollout的旧PATCHES不含视觉，禁止借旧apply开启。新增activate_lap42_vision提供prepare/activate/rollback，复用停机/锁/摘要/原子写，不让用户手编active。

prepare从code-owned规则、实际runtime、固定offline/probe、六例持久台账和既有decoded派生候选。复用有效成功结构/一次下载/不变normalizer，不拉旧URL；通过共享的完整生产校验检查候选，不临时写active试校验，不信候选自称passed/eligible。输出私有候选和审阅摘要，不输出真实对象。

activate持配置锁，确认停止、源配置/persona/规则/binding未变、无unknown，备份features/active与双摘要。**先原子保存已验证active，再只补features的vision.enabled=true**，最后重读配置/load_production；中断在两者之间时vision仍false。失败按本任务拥有摘要恢复，不覆盖他人变更。active和vision字段为此事务明确拥有的两项生产写入。

参数含预期binding/候选摘要等明确审阅值，不接受任意外来“eligible”。prepare/activate/rollback须有help及脱敏结果，实施方实际执行，不只交新脚本。正常启动后读取实际生效vision、模型/low/free和其他开关，连接就绪、实际生成与#sl分开。

## 5. 群图片闭环

受测群/操作者优先复用上轮忽略记录并核对仍授权；缺对象不随意挑群。正常加载后明确就绪，再由操作者发最多2条自造真实@图片请求，每条最多一次模型生成/原事件投递，agent不代发。

第一张自造PNG/JPEG含清晰图形/文字，第二张优先自造GIF自定义表情，按首帧判断。真实@用于确定性验收，不改变生产free。逐项核对一次下载/规范化、原生像素hash、同次模型理解可见内容、原群trace/request_key/事件ACK与操作者客户端显示。纯ID/不可取像素的类型明确不可见，不据此声称所有QQ表情都能看懂。

已有decoded有效则不补采样。仅确实失效时，允许一次120秒/1条新自造图的0模型入站检查，先取得就绪，超时不自动续窗。两条群测试仍用当前新消息，不拿旧样本冒充。恢复free后自然业务可能调用模型，须与受控6+2单列。

## 6. 必要验证和回滚

| 层 | 必须验证 |
| --- | --- |
| 插件/runner | 真装载、首条user前准入；源码/manifest/nonce/hash/路径/TTL；system原样、双上下文清空、无工具；异常/超时/catch不透传/不重复next；probe标记不进业务 |
| 预算/兼容 | 当前persona、中英emoji/模板符号、完整T/F/V/O/C；旧partial/本地分支与新kind分离；普通文字不变；原参数保留 |
| 实际CLI | 正向有本地user且0远端生成、反向0 user；来源/阶段回执/结果一致，不用替身或自填metadata通过 |
| IQ/激活 | 6次持久耗次/人工回调、无资格循环、probe与源码绑定；候选事务、摘要冲突/中断、仅拥有vision字段、回滚 |
| 当前业务/实群 | 定向AstrBot/runner的image与memory/attention/members/web/memes组合、第一图/GIF/坏图/注入/停言/群隔离/ACK；六例及两条原群理解/显示各有实据 |

不跑全库/旧全矩阵/A4。新代码适用检查通过后，真实步骤按上节执行。回滚先停机锁/摘要，只撤vision.enabled及配对active/代码；保留旧active档案、失败IQ/unknown/记忆key/库/purge/ACK/清理台账/锁/图库/pending。不reset/clean、删台账或重建key；普通文字不依赖新插件。

## 7. 授权和停止条件

本轮仅7文档与只读；用户下一轮发送新medium段才授予项目代码/当次官方插件、必要零生成检查、固定最多6原生与最多2群图、条件1次入站和主要受管停机激活恢复周期。仅旧decoded失效时另含一次诊断/恢复周期；不无限重启。

普通插件装载/接线/回执/预算/激活问题在合同内修好，不再交固定missing代替已规划实现。若实际锁定版本/强制策略不支持该官方接点，或必须改内部/后端/额度/预算、真实质量未过或unknown未清，才留下具体最小事实及已完成部分，vision保持false。人未就绪只待相应真实环节，不假审阅。

只提交检查过的本任务代码/测试/公开来源摘要/脱敏报告/文档；local/persona/真实图/名册/群消息/options/nonce/观察工件不入Git。同步PROGRESS、工作线HANDOFF/TASKS、42交接及使用对照，commit/push原分支核对完整远端SHA并报告保留差异。当前视觉闭环或具体外部阻断交付后释放归属停止，不推进21/其他功能。
