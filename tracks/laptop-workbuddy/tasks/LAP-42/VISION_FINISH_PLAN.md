# LAP-42续作：当前DeepSeek CLI识图收尾

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [42交接](HANDOFF.md)。[证据与推导](HOSTED_CLI_BUDGET_EVIDENCE.md) / [完整medium指令](VISION_MEDIUM_START.md)。

2026-10-25 22:19（Asia/Shanghai）登记并重读，session `LAP-42-hosted-vision-finish-plan`。起点本地/实时远端`48f66bc192548184e4f88e23de6a357962bff85e`，codex/lap-40-snowluma，开始无非忽略差异。只续42视觉缺口，不新建ID，不重跑上轮整合。

## 1. 目标、事实和非目标

目标是让当前deepseek-v4.1-flash/CodeBuddy CLI/low走通“当前QQ图片真实像素→同次原生理解→原群答复”，完成项目外部预算修复、定向离线、固定六例和受控群闭环。模型支持用户已确认，本轮又取得官方视觉1024 token上限及固定编码器/tokenizer依据，详见证据；不换模型/提供方/账号/额度，不改Snow/QQ/CLI内部。

上轮已启用记忆/学习/关注/成员/受控@，字幕已退役，真实QQ JPEG下载/解码已过；这些不重做。vision=false、六例0/6、群图生成0/2是上轮交付记录，下一轮必须重查。7条表情仍pending未激活；该维护和已启用功能的群内验收分开列在第10节，不并领、不作为识图前置。

非目标：直连DeepSeek付费API或新API Key、新caption/OCR/embedding模型、Ollama/家庭SSH、改变人格或预算数字、放宽媒体/身份/群范围、读取QQ缓存/旧历史、整轮42重启、A4/B/C或旧资格/proof/probe/长稳。保持第一图、GIF首帧、单次尝试、工具隔离、停言/原群ACK。

## 2. 必须解决的当前问题

详细来源/数值见[证据](HOSTED_CLI_BUDGET_EVIDENCE.md)：CLI窗口必须null与当前gate要求非null互斥；4096原生token被从30000字节里扣除，当前空prompt即25997>25904；CLI本机runtime只有3字段但review要求8个GGUF字段；诊断固定缺项和旧offline报告路径妨碍新规则。不能只改其中一个、再以剩下的同类错误结束为“模型不支持”。

本次是按托管CLI真实契约实现原有安全目标，不取消预算/来源/质量校验。没有所选路径来源、观察或质量结果时仍拒绝；不设置假processor/window/eligible。

## 3. hosted专用规则与两套预算

1. 在项目代码所有视觉表增加明确kind（例如hosted_codebuddy_deepseek_v41_v1），只适用于当前backend/model/low/锁定CLI与node身份。旧记录/本地路径保留，不用新分支给任意模型放行。未知kind、重复记录或hash不符拒绝。
2. hosted runtime采用runtime_identity实际可观测的version/artifact/node hash，模型是提供方托管alias及所选能力快照；不伪造云端权重/processor/projector/runner路径，不改变公开context_window_tokens=null合同。
3. 代码审阅依据固定tokenizer/encoder及CLI符号；普通文本上界每UTF-8字节至多1 token，模板/额外文字另计，一图V≤1024，容量使用CLI实际有效值。先核对CLI将单图交所选DeepSeek的有限转换契约，不拿其他provider catalog作证据。
4. 模板只覆盖当前“自定义system、单user、单图、无tools/MCP/会话续接”的有限结构。把全部实际CLI额外文字和官方role/思考/图片占位计入F；普通文本和F不得漏计或凭平均字数估算。F由有限结构/来源计算，不能把原字节开销2048冒充原生模板上界，也不另设无来源的2048模板硬门槛；不适用的结构拒绝，不缩persona掩盖。
5. 保留现有30000 UTF-8可见政策、2048开销、2048输出预留和4096视觉预留及全部本机参数。hosted的text_budget不再从字节limit中减token reserve；图像/模板/输出在独立原生账本核算。旧本地分支保持原合同。
6. 原生检查用证据中的T+F+V+O≤C；O使用当前CLI实际最大输出上界，至少覆盖项目输出预留，不将2048假装为已下发max_tokens。现有ModelUtils的输出覆盖仅取min可用于证明上界；缺明确上界则暂停图像生成，不改输出参数。
7. C复用锁定CLI的resolveEffectiveContextBudget语义：有效override/defaultLength/受支持较小档/maxInputTokens；再与官方所选模型容量契约取min。无session override才可用相应默认，不直接把1M最大值写成本机设置。保留原CLI原生窗口null，修项目判断而非更改CLI设置。
8. 在最后文字拟合/原生payload确定后和第一条user发出前，复用现有0生成get_available_models握手核验所选模型/低档/安全能力字段/有效限制，失败0 user输入。扩展cli_control的白名单仅限supportsImages、contextWindow.defaultLength/supportedLengths及现有容量字段，不落rawModels或凭据。source/model/限制变化时拒绝并显示具体原因。
9. 图像/请求字节限额、尺寸域、解码及一次cap/TTL不改；base64只是wire大小，不按字符算视觉token。两套预算在材料拟合、IQ构造、最终runner边界采用同一显式内部规则种类，不能只在最终校验改单位，前面仍提前拒绝。

规则编译/运行校验需有code-owned来源及摘要。固定HF资源本轮已取得SHA，可复核；官方网页若建来源快照，摘要必须是实际取得内容的摘要，并标抓取日期/提取范围，不能将本证据文档或自己写的结论hash冒充原文。首选小型本项目有限模板/字节界实现，不必安装tokenizers/transformers或复制上游推理代码，绝不下载模型权重。

## 4. 观察、报告与激活接点

reviewed/selected_record/runtime_verified/production_diagnostics/final_budget和managed_cli_input_review均按kind分派，hosted真实3字段与观察一致，诊断不再永久硬编码三缺项。支持声明、规则审阅、当前元数据、IQ、真实入站、已激活、群ACK各有独立状态。

hosted的IQ前置和生产回查使用本轮**固定新报告**（如reports/lap-42-vision-offline.json），由本任务定向验证器生成并绑定当前源码/规则摘要；不能要求覆盖旧lap-28-C报告、重跑整套历史writer。旧后端旧报告入口不改。报告路径由代码选定，不开放任意“passed文件”路径。

IQ仅要求静态规则/当前容量和输入合格，不依赖生产已eligible；生产仍须六例持久台账、真实decoded记录、当前离线/本地身份和unknown清理状态满足。不造通过字段、不洗批。新kind更新观察器与runtime_ok判断，不能再用本地GGUF字段比较CLI身份。

优先复用42已有真实decoded记录：验证原记录结构/成功状态/一次下载与不变normalizer等实际条件，不回拉过期图、不因只有文字预算代码改变就重做QQ采样。现有load_production已能回查该入站记录，medium须确认它与本轮契约仍匹配。仅记录缺失/无效等具体原因才补一次120秒/1新图，先告知操作者准备，收到就绪再开窗口；超时不自动续授权。

全部新代码/规则冻结并生成当前离线报告后，再计算IQ binding。docs提交不改变输入行为；修改source/config/persona/normalizer/规则等确会改变binding的材料须按原规则失效，不能套旧观察。当前原生容量和来源校验前置失败时不要先占/启动一个已知无法运行的批次。

## 5. 文件归属和实施步骤

本规划只改7份Markdown：PROGRESS、工作线HANDOFF/TASKS、42 HANDOFF、VISION_FINISH_PLAN、HOSTED_CLI_BUDGET_EVIDENCE、VISION_MEDIUM_START；不改生产/运行数据。

下一轮登记精确文件后，最小允许：

- src/qqbot_gateway/vision_capabilities.py、vision.py、token_budget.py、cli_control.py、workbuddy_cli_runner.py；必要小型hosted_cli_budget.py，不改CLI发行包。
- scripts/observe_lap28.py的hosted分派、既有quality工具必要兼容、固定新verify入口及对应新定向测试；config/vision-capabilities.json和确有来源的白名单CLI能力快照。
- reports/lap-42-vision-*及42交接/入口/使用对照；旧报告不覆盖。其他模块仅确有接点依赖才先登记，不能重构已交付记忆/成员/关注。
- 忽略state/vision-evidence台账/候选active/本任务备份和必要公开来源缓存；生产配置最多拥有vision.enabled这一布尔字段，其他local/persona/key/token/图库/pending均保留。

P0重核根/分支/实时远端/差异及42归属，读取本合同与来源，保存保护摘要；不重跑旧MEDIUM_START。

P1修上述hosted规则、单位、容量/null窗口、metadata/输出上界以及新offline报告接点，做定向离线与当前persona无正文预算核对；准备可审阅候选，不动运行实例。

P2仅在P1合格后用现有runner 0生成握手检查当前所选能力；不发送user、不暖机、不改账号。冻结源码/规则和当前报告，准备一个固定六例批次。

P3按授权固定IQ-01..06各一次，总最多6次；使用当前CLI/DeepSeek/low，自造图和真值不入prompt，原生hash/返回/预算/人工审阅按既有协议。失败/取消/unknown照耗次数，不能换trace/批号或删台账补跑。人工审阅不得由agent/脚本代填yes，缺少时只留待验。

P4静态/元数据/IQ及复用入站记录满足后，用既有审核激活路径生成候选active，在停止/配置锁/摘要条件下激活并只改vision.enabled=true，正常加载；最多一次主要受管加载周期。仅确需条件补采样时再允许一次诊断/恢复，未消耗旧授权不能自行延伸成无限窗口。

P5由操作者在明确授权群发送最多2条自造真实@图片请求；agent不代发群消息，每条最多一次原模型生成/原事件投递。验证内容理解、同链ACK和客户端显示，逐项留证，不用合成ACK关闭真实项。更新实际结果/入口，commit/push核对远端后停止。

## 6. 必要验证和通过出口

| 检查 | 要求 |
| --- | --- |
| 字节/token反例 | 自造23895字节system＋空prompt在30000政策下可用；旧减法25904错误被覆盖。R变化不会误改hosted文字字节限；legacy分支维持 |
| 容量与身份 | null本机窗口可在有来源的hosted规则下校验；CLI current defaultLength/较小档/无效值、模型/bundle/node/输出上界变化拒绝；最后握手失败0 user |
| BPE/模板 | 固定tokenizer结构/256字母表/无扩张；中英emoji/特殊字串/JSON/边界输入；模板与全部额外文字计数，未知结构拒绝；不把base64算模型文字 |
| IQ/报告 | 新固定offline路径/源码与规则绑定；不依赖生产先eligible，不覆盖旧writer；旧/错kind/过期signature拒绝，真实台账回查不信总结字段 |
| 原链路 | 当前persona及memory/attention/members/web/memes组合，第一图/GIF首帧/注入/坏图/超限/停言/群隔离/unknown不补发；实际框架替身测试，不手填成功metadata |
| 真实 | 六例原生与人工确认、QQ decoded记录、最多2图理解/ACK/显示分别通过；公开支持或离线拟合不等于真实理解 |

新测试只覆盖本次真实问题和边界，不重跑全库/旧全矩阵/A4。源码编译/当前定向报告及diff、引用、隐私检查完成后，才进入对应真实阶段。现有HTTP/群/历史策略、模型单次尝试和其他已启用功能不变。

## 7. 授权分层与缺口出口

本轮只读/文档/提交推送，不安装、启停、模型/QQ/群/SSH。下一轮用户发送新medium段才授予其列明的代码、0生成能力检查、固定最多6原生、最多2群图、条件最多1入站窗口及受管加载；旧42整轮授权文本不自动复用。普通free正常流量单列，不能称恢复后全局0模型输出。

无需增加付费API、读取日常WorkBuddy/QQ密码或修改全局配置。受测对象优先复用忽略的上轮操作者/群配置并核对当前授权，具体ID不输出；若对象/人工审阅或准备就绪缺失，完成独立部分，保留该真实环节待验，不随意挑群或代发。

通用来源假设不成立、当前CodeBuddy实际model/容量不符、模板中发现未有界文本等，按本计划完善普通实现细节；确需换模型/后端、改Snow/CLI内部、放宽限额或扩大访问时，先完成独立修复并留最小事实交用户决定，不用新的eligible字段自解锁。

## 8. 配置、兼容与回滚

没有新增用户可写的budget kind/proof/强制放行开关；kind属于代码所有审阅记录。保持input_reserve_tokens=4096、输入30000/开销2048/输出预留2048、context_window_tokens=null及现有模型/low不变。只有全部条件满足才拥有vision.enabled false→true，停机字段级补丁、原字节备份/双摘要、原子保存、正常启动，不热改或重建整个features。

active/IQ/source/offline记录按已有忽略路径保留；回滚在停机锁及当轮摘要下只撤vision.enabled和配对hosted代码/记录，不删IQ失败/unknown、不复位批次、不删除key/库/锁/ACK/清理台账/图库或21 pending。其他增强继续保持true。旧实现不识别新kind时保持视觉关闭，不自动尝试其他路径。

## 9. Git与交接

只提交本任务检查过的代码/测试/规则/新报告/文档；local/persona/真实图/群内容/账号/秘密和state观察工件不入Git。原分支codex/lap-40-snowluma，不强推、不reset/clean；远端推进先查明归属并安全协调。推后核对完整SHA，分开记录规则已实现/离线/实际IQ/激活/原群ACK/显示和保留差异。完成当前视觉续作后停止。

## 10. 后续独立收尾，不在本轮领取

- 原LAP-21：7图/7条pending仍在，未来一次身份核验停机维护中按既有备份/锁/摘要激活，再正常加载；不重复制或重标注。本视觉session不擅自激活别的任务pending。
- 记忆/关注/成员：已启用，之后用少量真实新消息检查持久学习/清RAM回忆、叫名/引用、受控@和ACK；不重新开发、不改当前配置、不伪认已验收。
- B站退役保持，其他旧差额保留，不扩微信、家庭后端或长稳。
