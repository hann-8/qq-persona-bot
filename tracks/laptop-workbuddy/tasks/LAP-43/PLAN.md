# LAP-43详细规划：Snow表情、时效搜索、群参与与唯一操作者

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [本任务交接](HANDOFF.md) / [medium指令](MEDIUM_START.md)。

日期：2026-10-27，Asia/Shanghai。session：`LAP-43-snow-memes-web-attention-plan`。本轮是用户指定的sol/max规划轮；模型/推理档位由用户会话设置选择，未自动检测或切换、未派代理。

## 0. 2026-10-28更新：一次落地，用户自行实测

用户最新要求：个人自用、尽快可用，QQ群体验由本人实测；原功能合同已经足够，下一轮给medium一个直接落地prompt。本节及更新后的第5/10/11节、MEDIUM_START覆盖旧A/B/C/D分轮停止、固定公共质量批次和重新人工打分后才上线的要求。2026-10-28本轮只改文档；用户下一轮提交统一prompt后，才授权其中实现、当前配置启用、受管停机/启动及部署。

目标是同一session把四项做成可实际试用的运行版本，不在代码/离线报告完成后等第二次授权。保留与本次改动直接相关的基本检查：代码/配置可加载、本人控制权、空@/叫名正反例、表情路径/hash/停机锁，以及现有预算、工具隔离、unknown/清理和受管身份边界；不将第11节完整矩阵、旧功能全量回归、额外报告数量或历史差额作为上线清单。

搜索和识图的质量状态均可明确为“已启用、待用户实测”，不能伪写已通过。搜索改为显式search_enabled及每次真实材料校验，不再被旧全局质量常量硬挡；识图增加第10.2节当前版本的操作者试用模式，保留全部技术运行约束及旧真实接受事实，免去新IQ质量生成/人工打分的上线前置。agent不主动调用真实模型或群发验收，用户正常聊天/发图自行试用；只对确实妨碍启动、权限或数据/预算边界的错误当轮修复或配对回滚。ASR、家庭后端、完整旧验收与新框架路线不扩入。

## 1. 授权、目标和非目标

用户本次累计五项意图：①既有表情包真正落地；②搜索最新消息，补模型知识时效；③修正“我在，目前只接通文字聊天。”及free明显叫名漏答；④把已有Snow分支合并主线；⑤bot行为控制有且仅操作者本人能执行。最后一项虽口头编号为6，按第五项统一记录。

2026-10-27原规划轮只读核对、写详细规划与medium指令，**只有第④项实际执行Git整合**；2026-10-28续修同样仅文档。不改业务代码/local/persona/图库/pending，不启停、安装、登录、调用真实模型/QQ/群/SSH。本文字段和流程仍是待实现合同；下一轮用户提交统一prompt才授权部署，不能把文档完成当功能已落地。

实施目标是复用官方Snow → OneBot gate → AstrBot/router → 共用gateway及当前CodeBuddy runner；家庭5070路线保留，网络材料仍由同一外层提供。当前DeepSeek/low、账号和credits来源、文字政策48000字节、overhead/output各2048、视觉reserve4096保持，不自动切模型、换后端或提额度。

非目标：重新迁移全部图片/聊天历史，任意图片URL/文件输出，视频/语音理解，恢复B站字幕，定时主动聊天，增加第二次分类/修复模型，自建/私改Snow框架，QQ内远程shell/配置/运维，付费搜索API、新账号或搜索服务部署。私聊关闭、授权群、入口过滤及既有发送/unknown/清理边界不扩展。旧C/A4和原NapCat根不读验或修改。

## 2. 本轮核对的实际基线

开始HEAD与实时远端Snow分支均为`4616186e1e26990837503b8f43195ddf04e53241`，工作区干净。远端默认HEAD为`main`，当时main=`66eea49623b76766e0569614207c80c78e57115f`，`origin/main...HEAD`独立提交数为0/65；main未被其他worktree占用。7份文档归属已先写TASKS并重读。

| 核对对象 | 当前证据 | 不能据此声称 |
| --- | --- | --- |
| 表情数据 | 当前根active catalog不存在；pending version=1、7条，base对应空catalog；7张引用资产hash均匹配，5 GIF+2 JPEG、4,100,086字节。library另有`.gitkeep`，不是第8张表情 | 已激活、运行已加载、Snow图片ACK/客户端显示/GIF动画通过 |
| 当前保存配置 | free、attention/silence/web/memes/vision/memory/members均开启；aliases为既有6项，focus TTL=60秒、intervening=0；web trigger=auto/provider=bing_rss；未保存selection_policy/resolver时按代码coverage/system默认 | 本轮查过当前进程、运行状态或重做42验收 |
| 操作者身份 | `access.admin_users`当前恰为1项，与用户本次明确身份一致，仅输出了比较结果 | 已修复全部控制入口；真实号码允许进入文档/Git |
| 识图 | [42最终结果](../../../../reports/lap-42-vision-closure-result.md)记载已启用、IQ-01/IQ-05及一条原群图获用户缩减验收；本轮只读确认vision保存为true | 原六例全通过、后续任意源码改动后旧凭证仍有效 |
| 搜索 | [web_policy](../../../../src/qqbot_gateway/web_policy.py)第11行`SEARCH_QUALITY_PASSED=False`；[retrieval](../../../../src/qqbot_gateway/web_retrieval.py)第160行在发搜索请求前返回不可用 | web.enabled=true代表搜索可用，或旧DNS失败就是当前网络状态 |
| 空@文案 | [router](../../../../plugins/qq_router/main.py)545—585：无有效文字/图片时在本地发出用户所述文案；并非必须经过模型生成 | 已证明用户某条具体事件携带视频；本轮没有读取原始私密群消息/追踪 |
| 叫名 | [attention.called](../../../../src/qqbot_gateway/attention.py)24—36只认若干开头/末尾/动词模式；同文件84—115分类，router640—642将DIRECT写成must_reply | 所有漏答来自模型选择silent；模型可以覆盖真实@的必答位 |
| 控制 | [gate](../../../../src/qqbot_gateway/onebot_gate.py)398—425未按admin验证停言；[GroupSilence.control](../../../../src/qqbot_gateway/group_silence.py)以任何mention恢复；router已有admin检查的重置入口 | 当前普通群友没有状态控制权 |
| 框架内置控制 | [configure_astrbot](../../../../scripts/configure_astrbot.py)65—78拒绝未知项目插件，并将两组内置命令插件设为禁用；manage把admins_id设成项目admin_users | 本轮已检查实际数据库/插件运行态，或内置控制路径可以不做组合回归 |

本轮对`called`函数做了独立、无I/O的AST提取计算：`鱼鱼在吗`、`鱼鱼帮我看看`、`鲸鱼娘，今天有什么新闻？`为true；`鱼鱼查查最新消息`、`鱼鱼这个怎么看`、`我想问鱼鱼一个问题`为false；转述`他说“鱼鱼在吗”`为false。这只是词法函数现状，不是整条路由/模型/QQ测试。

17项保护快照覆盖5份local、persona、旧settings存在状态、active/pending及library文件。只哈希或输出必要metadata，不读取群消息/长期记忆事实/秘密。旧任务[18](../LAP-18/HANDOFF.md)、[21](../LAP-21/HANDOFF.md)、[27](../LAP-27/HANDOFF.md)、[35](../LAP-35/HANDOFF.md)、[42](../LAP-42/HANDOFF.md)的实现与差额保留；本次新增合同覆盖冲突的未来行为，不能改写历史证据。

## 3. 共用行为顺序

平台实际self/group/sender验证及去重 → 唯一操作者控制命令 → 暂停状态/发送代际栅栏 → 当前消息类型归一化 → 本地直接指向分类 → 有界排队/冻结target → 必要公共检索/图片准备 → 一次模型生成 → 协议及来源校验 → 既有原事件投递/ACK。

所有身份、控制权、must_reply及输入类型由项目入口决定，模型只产生已允许的正文、受控表情选择和普通ambient的speak/silent。引用、显示名、网页、人设与模型输出都不具备控制权。暂停期间不得通过空@提示、错误提示或表情发送绕过哑巴栅栏。

## 4. 表情包：补激活，不重做迁移

### 4.1 缺口和落地

当前缺口是active登记未生成，不是图片没有复制。保持7条的id/name/context/tags/enabled/file/sha256/media_type和顺序，保留已审阅标签，不扩库、不重新收藏/下载、不转码。沿用[MemeCatalog](../../../../src/qqbot_gateway/meme_catalog.py)的preview/resolve、候选预算、`activate_pending`和发送账本；memes.enabled=true与0/0冷却保持。

旧忽略脚本`state/meme-migration/LAP-21-snow-memes-data-migration/verify.py`仍核对迁移时两根的完整配置摘要及源数据。LAP-42后配置已经变化，不能直接重放该脚本、篡改旧manifest或重新访问旧根来满足旧断言。未来编写当前根专用的`activate_lap43_memes.py`：默认inspect；激活需显式参数和expected配置/active/pending摘要，所有数据基线来自当前Snow根。

### 4.2 停机激活事务

1. 唯一执行session先登记精确忽略数据及受管实例归属。默认只读确认当前active/pending/7条资产、路径/reparse、格式/大小/尺寸/帧数、hash、候选16项/2000字节总上限；上轮1134字节只作历史，必须重新计算。
2. 在本根忽略批次目录保存原字节、原不存在标记和manifest；不覆盖旧迁移证据。发现新active、不同pending或同ID不同内容则停止该事务，保留他人更改，不重迁/覆盖。
3. 用户后续明确授权运行后，正常停止有创建身份依据的项目进程，确认停止；调用`activate_pending`，由其内部获取既有配置锁、执行`require_stopped`，用config_guard在锁内重查摘要。不在helper外持同一非重入锁再调用该方法。
4. 重读active=预期7条、pending按既有事务删除，资产字节不变；这不是误删state。实际配置/其他字段不动。正常启动并确认加载、候选可用及vision仍有效，不通过热改绕过加载。
5. 启用并正常加载后交用户自行尝试JPEG/GIF，不安排agent主动群发、不等两种图片都测完才交付。实际发生时可按用户反馈及原事件ACK记录显示/动画效果；只收到文字就记未选图，未尝试则记待用户实测。每次沿既有单次生成/发送，不自动重试，无需全库7张逐一发出。

表情仍每轮最多1张，普通直接提问必须有文字，明确索要表情可仅图；认真answer/联网来源答复不带图；最多3个部件及single兼容按既有合同。图库标签只作材料，模型只能返回候选ID或null，不能返回路径/任意URL/base64/CQ。

## 5. 搜索最新消息：共用外层检索与日期核验

### 5.1 路线决定和失败出口

继续以现有`bing_rss`作为唯一首期候选，由gateway在同一队列内调用PublicHTTP，挑选有限正文，再给当前模型一次作答。两后端共用这套材料，不开放CLI WebSearch/MCP或模型工具。**当前尚无真实搜索质量通过证据，计划不保证候选必然可用。**

保留“网页读取”和“搜索”两道开关：web.enabled控制公共网页总入口；新增web.search_enabled默认false。用户提交本轮统一prompt即明确选择个人试用，部署时将本机search_enabled保存为true，沿本次同一队列/PublicHTTP/正文日期合同运行。移除生产分派中SEARCH_QUALITY_PASSED对显式试用的硬阻断；旧false及旧质量报告只表示历史未完成质量验收，不能改成true冒充通过。诊断显示operator_trial_unverified，搜索是否作答始终由本请求真实可达性、正文、相关性与日期决定。检索源不可用时给准确说明，其余功能照常部署，不擅接新提供方、账号或付费服务。

显式/自动时效意图应先被识别，再检查search开关；关闭时direct返回本地搜索不可用说明，不能把意图改回none后交给旧知识模型装作已核实最新消息。网络/正文/日期不足同样在模型前说明；不能以个人试用为由跳过SSRF、TLS、材料预算或调用第二提供方。

微软官方已说明旧Bing Search APIs于2025-08-11退役，[公告](https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement)。这与当前网页`format=rss`候选不是同一个接口，不能据此断言RSS已退役或受商业API可用性保证。Brave/Tavily等需新账号/费用来源，公共SearXNG实例或自部署、Azure Grounding等均不在本轮实现授权中；只有当前路线的缺口确实改变方案时才回规划，不能自动切换。

### 5.2 触发和查询合同

- 显式：搜索/搜一下/查查/联网查/帮我查等。自动时效：今天/现在/最新/最近/本周/近N天与新闻/消息/动态/公告/更新/版本/发布/价格/天气/赛程/汇率/股价等组合。补充“最新消息/有什么新动态”等当前漏覆盖；单独“你现在怎么样”“我最近很累”不联网。
- 用户本轮明确“不要联网/只根据这段文字”优先；有明确公共URL仍沿read路线，视频/音频不伪装正文搜索。`web.trigger=explicit`只允许显式查询。
- 只选当前冻结target的一条明确公共问题；ambient沿当前allow_ambient_web和评估频控，不能拿整段RAM、历史、记忆/名册或先前别人的问题拼搜索词。模糊“查一下那个”本地要求补对象，不调用额外模型改写。
- 去掉已识别的称呼/请求前缀，保留公共实体、版本号、关键词、site限制及用户时间窗；查询240字符上限、敏感信息/账号/路径拦截沿用，不通过“自动脱敏”猜测放行。年份、日期用确定性结构解析后允许，例如ISO日期先识别再做长数字拦截，不能把全部5位以上数字放开。文本“QQ号”等个人标识继续拦截。
- `requested_at`冻结在事件到达时；用户“今天”按Asia/Shanghai自然日，“最近/最新”未给范围默认近7天；明确“过去24小时”是滚动24小时。“最新发布版本”按当前官方发布/版本正文核对，可早于7天，表述为“截至本次查询看到的官方版本”，不把版本发布时间改成今天。价格/天气等网页只能称带时间的资料，不能保证实时行情/分钟级精度。
- 查询词可附绝对日期/时间提示来提升召回，**不能把加日期当成检索已按日期过滤**；最终必须本地核对正文日期。相同问题不跨轮缓存为“最新”，每轮受1次搜索上限独立处理。

### 5.3 日期、正文和排序合同

RSS `pubDate`按规范是可选的条目发布日期，不是正文事实的实时时间；channel更新日不能给每篇文章背书。[RSS 2.0规范](https://www.rssboard.org/rss-2-0-11)支持此区分。页面`datePublished`和`dateModified`分别代表首次发布与修改，[Schema.org发布](https://schema.org/datePublished) / [修改](https://schema.org/dateModified)；页面日期也不是所述事件日期，[Google日期说明](https://developers.google.com/search/docs/appearance/publication-dates)。下面的筛选策略是本项目设计，不是这些规范承诺的搜索准确率。

新增无网络纯函数`web_freshness.py`，规范化并保留：requested_at、fetched_at、published_at、modified_at、date_source、date_precision、freshness_status；事件发生日期只能从正文明确提取或在正文回答中区分，不拿页面更新替代事件发生。日期缺失、冲突、未来日期或日期精度不足以支持小时窗时标unknown/conflict/invalid，不补写当前时间。日期无时区只保留date精度，不伪装精确时刻。

HTML日期提取在受管worker内进行：先取受限article:published_time/modified_time；再取有限JSON-LD的Article/NewsArticle/BlogPosting（最多8个script、合计64KiB、嵌套深度8、遍历节点256），只读取日期/当前页面URL/标题字段，不执行脚本、不拉@context；最后主正文中的time/datetime（最多8个、须与主文关联）。多个文章/推荐栏日期不混用。解析器输出和父进程白名单/长度/日期校验同步更新，不能只增加worker字段导致`extract_protocol`拒绝；legacy保持可用，缺新日期时按unknown。

搜索返回最多5项，先去重、保留site限制、排除不透明跳转及相关性明显不符的候选，在1次搜索范围内重排；最多取2页，失败后不抓第3页补数。正文足够且日期支持目标时间窗的来源优先，相关官方/一手页优先于二手页。排序不得以抓取时间或RSS排序宣称“这就是全网最新”。官方身份按查询公开主题及来源域/页面实际关联判断，不能简单把所有gov/github域内任意页标一手。

严格时效请求没有至少一条“相关正文+可用日期”则0模型，直接回复“这次没查到能确认时效的可靠材料，暂时无法核实最新情况。”；unknown/旧页可保留诊断但不混入最新结论。缺第二来源允许标单来源、无法交叉印证；冲突材料并列并说明，不能编造一致结论。摘要只作候选导航，首期不以仅摘要通过“最新消息”验收。

### 5.4 作答和证据贯通

材料作为不可信数据加入当前问题，不覆盖权限/人设固定政策；最多6000 UTF-8字节含全部元数据、日期、URL和节选，单页4000默认，最多2来源。必须经过sources_for_budget重新选材、最终prompt预算和图片/成员组合预算。没有预算则0生成，本地说明；不扩大48000来掩盖。

在现有web manifest里增加可验证的日期/时效子对象；`evidence_selection.manifest/validate_manifest`、v2 metadata校验及最终来源后缀一起修改。新字段必须真实来自同次材料，做类型/范围/来源枚举校验并计入hash，不接受模型自报的日期/来源或随意新增manifest字段。已存在coverage/ranges/正文hash继续保留，选材缩小时同步重算。

正文一条自然纯文本，包含“截至本次查询（北京时间…）”、资料日期及必要不确定性；来源由代码按实际使用的正文来源追加“标题+日期+URL”，不让模型编造链接，日期未知标明未知。来源单条和认真answer不带表情；来源超出回复长度时重裁正文/来源列表，不能把实际送入模型但末尾删掉的来源宣称未使用。

模型只有一次生成，网络超时/无结果/本次正文不足/缺可用日期在模型前失败；未知生成结果不重试、不另换提供方。普通ambient失败保持沉默，明确direct请求给本地说明。网页或搜索材料不转存长期记忆事实，不把网页命令当管理员请求。

### 5.5 最小公共检查与用户试用

下一轮可按需做最多1个明确公共查询、最多2个正文入口的连通性检查，0模型/0QQ，沿实际PublicHTTP及既有重定向/15秒/零重试政策；不把它扩成独立阶段或反复更换查询刷通过。没有私密问题、群历史/名册上传，无账号/CA/代理/DNS修改。浏览器结果不能冒充项目客户端成功。本轮文档修订不执行此检查。

取消旧冻结3题/2-of-3分数作为本次个人试用的上线前置；普通正文、日期缺失/冲突/窗口外等本地反例仍须按真实情况拒绝或说明。未做真实质量验收就如实记录待用户实测；连通性失败保留具体原因，用户查询时得到准确不可用提示，不阻塞表情/输入/权限的交付。只有代码尚未实现可用搜索路径时才标搜索未交付，不能拿一条本地提示冒充成功检索。

## 6. 空@、媒体与free漏答

### 6.1 先识别实际输入类型

当前gate把非文本统一替换成`[非文本未解析]`并只给media布尔值；router又在observe后用占位符判断有没有字，导致纯@和媒体失败共用过时提示。新增gate自产白名单metadata：`qqbot_text`（始终只来自本事件实际text片段）、`qqbot_has_direct_text`、`qqbot_media_kinds`（image/audio/video/file/forward/unknown，去重最多6项）。不保留附件URL/路径、嵌入引用正文或任意传入qqbot_*字段；原材料cap及真实at/reference绑定保持。

新增`input_policy.py`提供纯归一化/分支函数，mentions/free/attention三条入口共用，先分支再观察群窗口/准备记忆/检索，避免空@占位污染RAM。**不同QQ事件不拼接**：@发一条、问题另发一条时，不延迟猜测视频或自动把下一人的话绑定到空@；后一条仍按叫名/引用/已ACK焦点等既有证据判断。

| 当前事件 | normal状态下的未来行为 | 模型调用 |
| --- | --- | --- |
| 只有真实@，无实际text/媒体 | 走现有受guard的local_notice，短应声“我在，怎么啦？”；既有去重，不建焦点/长期记忆，不声称只能文字 | 0 |
| 只含空格/atAll/表情占位而无对bot直接指向 | 无有效任务，安静结束；atAll不等于真实@ | 0 |
| @或明确叫名+文字 | 冻结target、直接必答；超长在模型前按长度提示 | ≤1 |
| 当前图片且cap可用 | 沿当前识图，支持无caption的图片；不拿历史图/相邻消息补图 | ≤1 |
| 明确含图片但cap/下载/资格失败 | 用当前图片不可读提示，不能说图片未接入；不默默丢图后回答caption | 0，若生成前已失败 |
| 音频/视频/文件/转发或未知媒体，包括有caption | direct时说明本条媒体暂不能读取并请贴文字；ambient静默。不调用模型假装理解媒体 | 0 |
| 字面文字恰为`[非文本未解析]` | 根据gate自产has_direct_text判断，保留为用户实际文字，不能用字符串替换抹掉 | 按正常文字 |

暂停状态先于全部行：普通@、空@、叫名、图片、失败提示均不能发言。真正不支持的媒体类型用事件事实生成提示；不能从“没收到字”推断存在视频。清理router第448/584/725等全部旧文字能力文案及同类POLICY分支，但不改用户config/persona.md；能力提示由当前有效配置/材料路径生成。

local_notice复用现有guard、原event和投递队列；必要时返回有限投递结果给任务层，只有真实ACK才能称发送通过。空@应答不经过模型、不产生群学习或bot_commitment，不能按“调用send了”标ACK成功。静音/断线/过期/停止仍阻断提示。

### 6.2 直接指向由本地提高召回

优先级不变：真实@ > 明确叫名/解析到本bot已ACK消息的引用 > 同一发送者短续聊 > focused_candidate > ambient。前四类DIRECT沿现有must_reply=true，模型返回silent属于协议失败，不能当正常沉默；按既有本地失败说明，无第二次模型补答。

`called`改为明确、可测试的有限语法，不加单纯全句子串命中：NFKC/casefold、长别名优先、忽略代码/引号/转述/URL/以>开头引用行；中文别名在句首可紧接请求/问句、请求句式“我想问<别名>…”，或句末呼语；英文短名必须词边界。句首支持常见“查查/查一下/这个…怎么看/你觉得/能否/给我/帮忙/来…”；别名嵌在第三人称描述如“鱼鱼这个名字不错”“我把鱼鱼的回复转给你”不升级direct，疑义保留ambient。语法清单写成表驱动夹具，不靠不断扩大`.*`。

必须新增的正例：`鱼鱼查查最新消息`、`鱼鱼这个怎么看？`、`我想问鱼鱼一个问题`、`帮我看看这个，鱼鱼`、大小写/全角等价英文呼语。负例：引文/转述/代码/URL中的别名、别人的昵称包含别名、仅第三人称评价、at别人、引用他人消息。真实@始终优先且不受文本转述排除。

短续聊保持focus TTL=60、max_intervening_messages=0和真实ACK前提；只在同一发送者、未插入其他人/at他人/引用他人且焦点有效时，将有限承接问句（“那怎么办”“为什么呢”“再详细点”“继续”“还有呢”）升级focused_followup，避免当前必须出现“你/您”造成漏判。“嗯/好/哈哈/谢谢”不强迫回答；换人/超时/重连/重置立即清焦点。引用未知/过期消息不拉get_msg、不从引用正文认身份。

普通ambient依然由同一次生成决定speak/silent并受原频控；不降低全群冷却来提高直接叫名命中。alias仍只认显式配置的6项，不从人设大段文本/群名片自动采集新名字。

### 6.3 最小诊断

沿现有ATTENTION trace增加有限枚举：input_kind、addressing、must_reply、filtered_reason、queue_result、generation_performed、decision、delivery_state；只记录随机trace/枚举/耗时/计数，不记录QQ/群号/正文/名册/图片/搜索词。用同一个原事件trace区分“没识别叫名”“排队/过期/停言拦截”“协议出错”“发送失败/unknown”，不把所有没回复算模型silent。不开新常驻监视器、不追读历史群消息。

## 7. 唯一操作者控制

### 7.1 身份和配置

复用现有`config/local/bot.yaml → access.admin_users`，当前已经是用户指定本人且单项，不新增owner配置源。字段名保持兼容，但未来规范化和GateConfig校验要求**去重后恰好1个合法QQ**，且不等于bot、不在blocked；`is_owner`只用平台验证过的实际sender精确匹配。0项/多项/冲突时配置失败，提示本机修正；不自动挑第一位、静默删管理员或从QQ群角色填入。

真实号码仅留本机忽略配置，公开示例用既有REQUIRED_ADMIN_QQ占位；本轮不重写当前已正确的值。AstrBot管理名单、router/admin和MemoryStore的“管理员群背景”能力全部来自同一个规范化单项集合，不能维持另一份群角色/全局框架管理员作为并集。项目外部手工AstrBot实例或日常QQ不接管。

已有两组内置命令插件禁用和未知项目插件拒绝保持；在实际隔离AstrBot链确认/reset、人格/模型切换等内置语法不会绕过router。若发现额外命令入口，按“项目内禁用/仅同一owner显式授权”最小收口，不去修改框架源码或日常全局配置，也不借机新增群内管理指令。

### 7.2 控制权限矩阵

| 行为 | 唯一操作者 | 普通授权群成员 | 实施范围 |
| --- | --- | --- | --- |
| 暂停本群发言/恢复本群发言 | 有明确指令时允许 | 不得改变状态，真实@也不能解除暂停 | 本次必须修复gate状态入口 |
| 重置本群RAM上下文、本人对话重置 | 仅已有精确指令+真实@ | 不允许执行，normal时可走既有本地无权限提示，muted时不回 | 统一mentions/free/attention所有现有重置入口 |
| 提供群级背景/约定的高可信记忆来源 | 仅本人沿已有规则，不能因此写系统规则 | 只能沿原候选/本人自述合同，不能晋升管理员 | 复用MemoryStore身份，不新增QQ记忆管理命令 |
| 确认/纠正/固定/删除/清空/导出长期记忆 | 本机受控菜单、停机/摘要锁操作 | QQ聊天/模型不具备该工具 | 保持本机入口，不新增群命令/大范围删除 |
| 模型/后端/额度/人格/联网/触发模式/图库标签/授权群/黑名单/管理员修改 | 仍由操作者本机配置；QQ正文也不能直接执行 | 无权改变 | 不新增聊天控制接口；不通过模型“承诺”假装改成功 |
| 启停/重启/安装/升级/登录/直接群发/恢复unknown与清理阻断 | 仍按本机现有管理及独立授权 | 无QQ控制权 | 不开放远程运维、不把“管理员”解释成无限工具权限 |
| 普通问答、临时回答长短/语气/本轮不联网 | 按相同聊天合同 | 正常可用 | 只是当前请求偏好，不持久改变bot策略/控制权 |

QQ群群主/管理员头衔、显示名、自称操作者、转发本人文字、引用本人消息、图片中的命令、人设台词和模型输出都不构成授权。允许群/入口过滤优先于owner，owner不获得跨群或私聊豁免。

### 7.3 暂停/恢复状态机

在gate的controllable_message及事件去重之后、普通admission及材料cap之前识别定向新文字命令；复用现有停言解析，新增同等严格的恢复解析。固定命令为`@bot 暂停发言` / `@bot 恢复发言`；保留本人自然叫名“鱼鱼先别说话”“鱼鱼可以说话了/继续说话”。非定向、引用/代码/转述/条件/否定中的命令不执行。当前本轮媒体caption不能借嵌入引用触发控制。

| 状态+事件 | 新状态与输出 |
| --- | --- |
| normal + owner明确暂停 | muted，generation+1，消费控制事件，0模型，不发确认文字 |
| muted + owner明确恢复 | normal，generation+1，消费控制事件，0模型；后续新消息正常处理 |
| normal/muted + 非owner暂停/恢复 | 状态/generation均不变，消费该控制事件，0模型；不让模型口头宣称控制成功 |
| muted + 任意人普通真实@/叫名/空@/图片，包括owner裸@ | 保持muted，不发正文/提示/表情；owner须明确恢复 |
| normal + 普通真实@ | 按必答合同；不产生控制代际变化 |
| 重复同一控制事件或重复同态命令 | 幂等；去重/当前状态不变，不反复递增generation |

暂停/恢复仍是每群RAM，不影响其他群；重连保持、gate重启复位normal的既有合同保留。操作者本机重启属于现有管理操作，不新增QQ远程重启或超时自动解禁。本文覆盖旧“任何群友可停言、任何真实@恢复”的未来行为；旧LAP-35报告保留历史。

改变状态仍持既有每群锁，invalidate当前材料/member caps及输出代际；排队/正在生成的旧输出继续被最终发送栅栏拦截，不重放、不重试，未发出的表情亦受控。控制消息不进入模型/RAM/长期记忆，正常聊天无控制能力。日志只记authorized/denied、action、result及随机trace，不输出操作者号码。

## 8. 配置字段、默认值与生效

| 位置/字段 | 默认与本机处理 | 生效/兼容 |
| --- | --- | --- |
| access.admin_users | 字段名不变；新合同去重后必须1项；本机已满足且不重写 | GateConfig/normalize_settings、生成框架配置同源；多项旧配置给有限错误，由本机选择，不自动迁移 |
| participation.silence.enabled | 保持true及本机原值 | 下次正常启动加载新owner-only状态机；false仍关闭停言能力，不提供替代旁路 |
| participation.attention | enabled/aliases/TTL/队列/频控均保持；只改确定性语法 | 按当前配置正常启动；不自动加别名、提高频控或改变free/mentions |
| memes.enabled/catalog/library/冷却 | 不新增字段、不改开关；当前7条pending激活成active | 停机锁内事务，正常启动重载；不热加载 |
| web.enabled/trigger/provider | 保持true/auto/bing_rss，普通read兼容 | 新增search开关不能关闭既有read |
| web.search_enabled（新增） | 新安装默认false；本次用户提交统一prompt后将当前本机保存为true | 停机正常加载；显式试用不受旧全局质量分数阻断，逐请求材料/日期校验保持 |
| web.freshness_days（新增） | 默认7，整数1..30；用户本轮明确时间窗优先，最大30天；更长/无法解析时本地澄清 | 自动时效筛选用；纯read不据此拒绝历史文章 |
| 日期时区 | 固定Asia/Shanghai，UTC保存绝对时刻、显示北京时间；不新增机器全局设置 | 测试用冻结时钟覆盖跨日/UTC/日期精度 |
| web其他硬上限 | 1搜索/5候选/2页/2来源/15秒/2重定向，6000总材料、4000单页默认不变 | 查询日期/来源元数据全部计入同一预算；不增付费/重试 |
| vision.enabled/预算/模型 | 当前true/48000/既有其他数值与模型保持 | 新代码及新web字段影响vision binding，必须按第10节处理，不能只重启赌旧凭证有效 |

新增web字段同步validate_web、config_comments、分层模板/完整示例/导出/快照/语义版本与菜单（若现有入口有对应字段）；模板默认false，本次部署只按明确试用合同保存新增字段。新worker日期协议和web manifest须配对升级，旧报告不重写。人设内容完全保留，只在compose_persona等代码生成政策里准确说明当前材料/直接指向/控制限制。

## 9. 预期实施文件与归属

以下是下一轮领取范围建议，**不是本轮修改清单**。medium先登记实际要动的路径并重读，同文件不明差异先协调；不要照表全量改无关文件。

| 子项 | 主要文件 |
| --- | --- |
| 唯一操作者与停言 | src/qqbot_gateway/config.py、group_silence.py、onebot_gate.py、participation.py；plugins/qq_router/main.py；scripts/manage.py的框架管理名单映射仅必要接点；config_files/config_comments及示例说明 |
| 归一化与attention | 新src/qqbot_gateway/input_policy.py；onebot_gate.py、attention.py、router/main.py、persona.py；turn_v2/group_protocol仅有实际合同缺口才改，不放开must_reply校验 |
| 表情激活 | 新scripts/activate_lap43_memes.py；复用meme_catalog，不重写发送器；忽略的本次manifest/备份、config/memes.local.yaml及既有pending；library只读 |
| 时效搜索 | web_policy.py、web_retrieval.py、html_worker.py、web_extractor.py、evidence_selection.py；新web_freshness.py；model_gateway/turn_v2仅必要metadata接点；公开配置/旁注/操作说明 |
| 必要检查 | tests/test_lap43.py、test_web_freshness.py及现有受影响用例按风险择要；verify_lap43.py/probe_lap43_search.py只在实际需要时最小实现，不为凑报告数量新建检查框架，不覆盖18/21/27/35/42报告 |
| 识图配对兼容 | scripts/revalidate_lap43_vision.py复用现有prepare/activate；vision_capabilities.py、vision.py及probe/激活helper增加固定的明确待用户实测试用模式，必要时调整vision_operator_review.py/vision_mod_guard.py接点；旧路径/常量/批次/失败记录完整保留 |
| 交接 | PROGRESS、工作线HANDOFF/TASKS、43 HANDOFF和相关用户配置说明；后续实际实施报告精确区分已实现/离线/已加载/真实 |

## 10. 实施顺序、识图兼容与运行边界

### 10.1 同轮实现、必要检查和上线

本轮Git整合不改变当前HEAD业务文件内容，不重启bot。未来实施在独立`codex/lap-43-*`分支和隔离工作树中完成，先检查本chat已有适用worktree再创建；不在正在使用的Snow工作根直接改Python，避免现有进程/按次CLI混读新旧代码。隔离根不复制local/persona/秘密/登录/群数据库，只使用自造夹具；需要当前persona预算验证时只在进程内只读原文/长度，不写到Git/测试夹具。Python依赖可使用已存在环境执行，但CWD/QQBOT_ROOT/所有状态目录固定到隔离临时根，禁止拾取生产配置。

顺序为：统一owner及输入/attention → 当前根表情激活包装 → 搜索开关/日期/来源 → 当前版本识图试用兼容 → 必要检查 → 配对配置和main部署 → 交给用户实测。允许在同一session内设代码检查点，不再在“离线已过/待激活”处等待另一轮用户授权。新prompt只授权本任务当前Snow根，不扩大到旧根、家庭SSH、安装/登录或自动群发。遇到能力缺口先收尾独立部分，不能把搜索等单项质量问题变成全部停止的理由。

### 10.2 保留识图可用：明确的当前版本操作者试用

[vision.binding/adapter_signature](../../../../src/qqbot_gateway/vision.py)63—100绑定完整设置及全部gateway Python、router等；新增Python文件也会改变摘要。[vision_operator_review](../../../../src/qqbot_gateway/vision_operator_review.py)的旧兼容指纹同样覆盖全部gateway源码，现有豁免只用于旧材料客户端小修，不能扩大成“与本轮改动都兼容”。更换Git分支名或提交本轮Markdown不会改变这些业务文件。

本轮不生成新凭证。下一轮实现一个最小的代码拥有模式`lap43_operator_trial`，由用户提交统一prompt授权，目的仅为允许当前版本上线供本人实测。它明确区分运行许可与质量已通过，不要求重跑IQ或先等用户给新样本打分；旧operator-review/large-attempt、IQ账本不改写，也不允许只改active.binding或缩小adapter_signature。复用既有prepare/activate及锁机制，避免再建完整资格系统：

1. 固定路径`state/lap43-vision-trial/<binding>/`保存一次明确试用授权、当前技术检查摘要、旧active摘要、候选及回滚备份；字段至少含当前完整binding、runtime/selected-record摘要、authorized_at、authorization_source=operator_submitted_prompt、quality_state=pending_user_test。固定helper须显式`--authorize-operator-trial`及expected binding；HTTP/模型输出/网页/普通群消息不能选择此模式或提供任意证据路径。
2. 原IQ-01/IQ-05及真实群图只保留为旧版本真实接受事实，不能填成当前IQ、人工review或新生成次数。当前试用质量状态始终如实待用户实测，诊断/状态不得把试用许可展示成新版本质量已通过；不自动跑大图、不催用户先打分，也不替用户接受答案。
3. 技术检查只覆盖当前运行兼容所需：完整adapter/settings/runtime/selected record、当前静态/最终预算、工具隔离、已有当前CLI正反零生成接线与真实来源读取。复用现有检查；不把新完整测试矩阵或大量报告当门槛。CLI检查若意外出现真实生成，忠实记录并停止相关调用，不能当作0生成继续；本prompt没有授权agent主动真实模型质量批次。
4. production_diagnostics/validate_production_evidence/load_production/require_production及状态展示对新模式采用同一严格结构和固定路径分派：只免去当前IQ/人工质量分数要求，其他运行约束保持；允许启动与待实测两个状态分别展示。旧模式行为不变；当前技术报告/probe须校验当前版本，不能拿42报告冒充新代码通过。
5. 正常停止后，在最终源码及搜索/表情/配置值确定时一次性prepare/activate配对当前试用记录并保持vision=true，随后启动确认加载。可以用本次现有helper最小扩展完成，不新建per-case attempt/评分/资格流水线。用户随后自行发图实测；若报告真实错误，按普通故障修复，不触发整套重新规划。
6. 未解决的unknown/失败、工具隔离或真实容量错误仍阻断相关启动/生成；不得删标记、伪造摘要或静默关掉识图求上线。技术兼容确实无法保持时先尝试修复，不能解决则恢复本任务配对旧版本供继续使用，并交付独立成果与具体阻断。纯粹缺新质量打分不算技术阻断。

具体接点：当前offline_path/offline_valid/probe_valid固定读42报告与journal；43试用模式需最小配对当前固定检查路径（如reports/lap-43-vision-offline.json及上述私有probe路径），绑定实际使用的helper/test/source摘要，不照搬旧通过标志。生产/prepare/activate使用同一模式，新增helper纳入完整adapter签名，原unknown及授权账本继续检查。核心预算、原始wire/receipt/transcript和工具隔离不变，不能仅加writer却仍读旧文件。

这是用户明确要求自行试用后的运行许可调整，不宣称新版本质量已过，也不另开识图项目、六例采样或长稳任务。旧lap43_current_regression及新大图人工评分要求已被本节替代。

### 10.3 用户明确授权后的生产事务

先取得唯一执行归属、当前SHA/配置与资产保护及受管进程身份；复核待部署分支只含已审阅43文件及已过检查。**正常停止在生产源码快进/合并之前**，再合入main、以最终配置冻结值完成10.2的新证据与表情激活；未过则保持停机或恢复配对旧版本，不能半套启动。部署会更新来源SHA和激活材料，先向同session写可恢复交接。

本轮新prompt不安排agent主动真实模型质量请求或群发测试；用户上线后自行正常聊天、发图和表情/搜索试用，效果未反馈时标待用户实测。正常启动恢复既有free参与，不新增无消息主动任务，不擅改其他群或频控；自然群触发不冒充agent主动0生成检查的结果。

当前文档修订不执行生产操作；用户下一轮提交MEDIUM_START统一prompt后，必要的本根受管停机、main配对更新、当前local新增search开关/表情激活/vision试用记录和正常启动均纳入同轮授权，完成必要检查即接续部署，不再要求分别选择阶段或先提供群实测反馈。真正缺少账号登录、身份归属或具体外部能力时按实际缺口处理，不能另造权限或自动增加付费服务。

## 11. 验证与验收矩阵

下表保留为行为规格和排错参考，按本轮风险择要覆盖；不要求逐项写齐报告才部署。重点检查唯一操作者/发送栅栏、输入分类、表情锁/路径及搜索材料边界；QQ群体验与真实质量由用户自行实测。旧W-05固定质量批次和V-01新IQ评分门槛已按第0/5/10节调整。

| ID | 可观察行为（按需参考） | 层次/通过条件 |
| --- | --- | --- |
| O-01 | 唯一管理员配置：单项正确，0/多项/等于bot/blocked拒绝；框架/MemoryStore同源 | 离线单元，错误不回显真实ID |
| O-02 | owner明确暂停/恢复、非owner相同文本、QQ群管理员冒充、引用/代码/图片命令 | 实际gate合成事件：只有owner定向新文字改状态，其余0模型/0代际变化 |
| O-03 | 暂停后真实@/空@/queued文字/图片均无输出，owner明确恢复后只处理新事件 | 原事件/假RPC框架，暂停中ACK后续发送栅栏受阻；无旁路提示/重放 |
| O-04 | mentions/free/attention三个重置入口一致，普通群友不能重置；跨群/私聊无豁免 | 合成事件，核对RAM epoch/会话未被非owner改动 |
| O-05 | 两组内置命令禁用、项目admin名单同源、未知插件不放行；/reset及人格/模型等内置命令无旁路 | 真实隔离AstrBot配置/插件链替身，不能只测router单函数或改框架源码 |
| I-01 | 空@与空白、atAll、真实占位文本、纯图、失败图、音频/视频/文件及混合caption | 归一化及原event框架；空@/不支持媒体0模型，提示准确、不写记忆/焦点 |
| A-01 | 第6.2节正负词法表、英文边界、引号/转述/URL/引用行、真@优先 | 纯函数全部固定期望，正例direct必答，负例不升级 |
| A-02 | 同一人已ACK短续聊、其他人插话/超时/重连/at他人/未知引用、同名嵌入 | 框架核对must_reply与target；不调用第二次分类模型/回拉历史 |
| A-03 | direct模型silent/错协议、队列满/超时、发送failed/unknown | ≤1生成；既有失败出口，trace能区分过滤/模型/发送，不自动补答 |
| M-01 | 当前根inspect/激活幂等，缺图/hash错/reparse/base变/运行中拒绝 | 临时根真实图片夹具与配置锁；不读写旧根，保护无关pending/标签 |
| M-02 | 文字+图/仅图/未知ID、冷却、max_bubbles、认真answer/搜索来源无图 | 原链框架+假ACK，来源/原图发送失败不转成任意媒体 |
| W-01 | 明确时效/普通闲聊/不要联网/模糊对象/日期vs长数字隐私 | 冻结时钟纯单元，无关键词全量触发和历史上传 |
| W-02 | meta/JSON-LD/time日期、冲突/未来/缺时区/跨日/精度、修改日不等于事件日 | worker真实子进程+父schema，反例严格失败/unknown，资源硬限保留 |
| W-03 | 1搜索/5候选/2页、相关性/时效筛选、过期/未知/部分页/完整要求/最终预算 | PublicHTTP替身+真实提取worker，0或1生成可核对，保留SSRF/TLS/无环境代理 |
| W-04 | 日期与来源贯通manifest/metadata/后缀、链接注入/模型假URL、来源超长 | 两后端真实runner底层替身+实际AstrBot事件，签名/实际材料一致 |
| W-05 | 可选1个公共查询/最多2正文入口 | 0模型/QQ，记真实连通性；不以固定得分挡个人试用，不伪称搜索质量通过 |
| V-01 | 旧证据不冒充新代码；当前试用记录绑定完整、授权明确、状态待用户实测 | 新模式允许未做新IQ的明确试用；预算/工具隔离/unknown/固定路径与旧模式保护保持 |
| C-01 | 当前persona与48000政策下，attention+图片+成员+memory+web+7表情候选组合 | 零模型最终容量/原生预算与元数据往返，单次尝试和工具隔离保持 |
| R-01 | 生产中的空@、owner/非owner控制、叫名/真实@、表情、搜索、图片 | 上线后由用户自行试用；实际反馈/ACK可记录，未出现路径保留待实测，不作为部署前置 |

定向命令以实现后的实际CLI为准，例如项目Python `-B -X utf8 -m unittest discover -s tests -p test_lap43.py`及`test_web_freshness.py`；只覆盖必要风险，不为低影响可逆改动补镜像测试。已有Harness/预算脚本按实际需要复用，不直接调用会覆盖旧报告的18/21/27/35/42入口，不重跑A4。纯文档本轮不运行或宣称功能测试。

## 12. 兼容、迁移和回滚

新增字段省略按默认值规范化；web读取仍可用、search默认关闭。单owner是用户最新行为合同，多管理员旧配置显式失败，不悄悄授予多个人控制权；当前本机无需修改名单。旧自由参与及真实@必答在normal保留，muted按最新owner-only合同覆盖；不继承旧“任何真实@恢复”。

代码/worker协议/新字段/vision active按配对版本部署；只做Git分支整合的本轮不动这些文件。未来回滚先停止受管实例，核对本任务拥有字段和原字节摘要，再恢复配对代码、配置及active/catalog/pending；不能用整份旧local覆盖后来修改。不删除群记忆key/事实、图库原资产、IQ/unknown/ACK/清理账本、锁或uv.lock，不`reset --hard/clean`。

表情激活成功后恢复pending必须核对本批原manifest/active未被他人编辑；资产可原地保留。搜索失败可仅停用本任务新增search_enabled而保留read，但这会改变vision绑定，须配对回滚/校验，不能热改后假定识图仍有效。明确试用模式允许当前质量未验状态上线；不能把缺新IQ/分数当成只能交付离线分支的理由。

## 13. 2026-10-27分支合并与交付（已完成，历史）

用户第④项授权实际整合已有Snow成果。交付前刷新实时远端main与Snow分支，核对无独立main提交且仍是当前分支祖先，审阅本轮7文档差异/保护/链接，再只提交本任务文档并推送Snow分支。保留原Snow分支及其他worktree，不强推、不删分支或改旧根文件。

若仍为祖先关系，采取fast-forward把同一Snow tip纳入main，不制造无必要的冲突/重复提交。**避免先checkout陈旧main导致正在使用目录短暂回到旧代码**：可先普通push `HEAD:main`（远端会拒绝非快进），再无force地fetch `main:main`快进未占用的本地main，确认main=HEAD后switch main；两者同提交，文件树不变。所有依赖步骤顺序执行，推送后核对两条远端分支和本地完整SHA。

若远端变化导致非快进，先保留本轮已提交成果，读取独立差异并按已授权合并处理；不覆盖其他session、不在运行根制造待解决代码冲突。纯文档冲突可审阅合并；业务语义冲突若不能保证保持双方成果，则在隔离树解决并完成必要验证，未能完成时如实报告，不强推。当前并未发现这类分歧。

AGENTS、PROGRESS、工作线HANDOFF/TASKS和43交接把后续起点改为main，并注明“规则已规划，尚未实施”；旧计划中的分支名作为历史保留，不全库替换。第⑤项身份不入Git。记录实际提交/远端核验及保留差异，最终停止；main合并只说明Git主线统一，不代表重新部署、框架完整验收或本轮三项/权限功能已生效。

## 14. 当前未验证与停止点

本轮没有运行项目测试、公共候选probe、bot状态/启停、真实模型或QQ；词法纯计算和本地metadata/hash不代替端到端。当前空@具体事件原因、叫名线上命中率、全部控权路径、表情ACK/GIF、搜索本机网络和时效质量、新代码识图绑定回归均待后续实施/验收。

2026-10-28本轮停止点：7文档同步、检查、commit/push及远端SHA核对，给用户统一prompt；不实施功能。下一轮用户提交prompt后直接同轮实现、启用、部署并交用户实测；缺主观质量反馈不阻塞上线，真正能力/权限/数据或预算阻断按具体问题处理。未验事实继续如实保留，不增加真实次数、费用来源或未计划后端。
