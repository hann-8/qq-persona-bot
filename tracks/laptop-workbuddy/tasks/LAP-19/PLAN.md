# LAP-19：双后端、联网、自由群聊与表情包总体计划

返回[PROGRESS](../../../../PROGRESS.md) / [本任务HANDOFF](HANDOFF.md) / [TASKS](../../TASKS.md) / [PC交接](../../../local-5070/HANDOFF.md)。追加需求合同见[GROUP_CHAT_PLAN](GROUP_CHAT_PLAN.md)，medium顺序/复制指令见[IMPLEMENTATION_GUIDE](IMPLEMENTATION_GUIDE.md)。

2026-10-17，Asia/Shanghai。状态：**仅规划；只读能力核对完成，功能未实施**。规划/后续实施模型与档位按[AGENTS](../../../../AGENTS.md)由用户在会话设置选择；不声称自动检测或切换。后续medium会话按用户指令依次领取LAP-17→LAP-18→LAP-20→LAP-21，一个会话一项。

本文件第2—7节主要是17/18合同；用户后来追加自由参与/真实@必答/直接群发和表情包，20/21详见GROUP_CHAT_PLAN。早期“仅@/本人历史/纯文本唯一部件”是当前实现或17/18兼容基线，未来free与表情发送以追加合同覆盖，不得据旧限制拒绝用户已要求的规划。

## 1. 需求、决定和非目标

用户已在家庭PC配置Qwen3.5 9B Q4_K_M，明确两条路线都推进：CodeBuddy效果与credits消耗可接受就用CodeBuddy，否则由操作者切到本地。两条路线共用联网搜索；用户已选择“按需自动：明确搜索请求、时效问题，或要求读取网页时联网”，普通闲聊不联网。

本计划确定：

1. 笔记本继续运行唯一NapCat→gate→AstrBot→模型网关入口。PC仅提供已有Ollama；CodeBuddy路线独立于PC在线状态。
2. “配置机器人.cmd”增加后端选择与共用联网设置；分别保留两套模型/预算参数。**手动停机、修改配置、重新启动生效**；保存不调用模型或自动重启。切换开启该群该用户的新当前上下文，旧历史保留。
3. 本地使用原生`/api/chat`，通过已核对的SSH direct-tcpip通道访问PC回环11434；不开放PC Ollama的局域网/公网监听，不复制QQ或CodeBuddy登录资料。
4. 共用检索层位于模型网关，先取得有界材料，再调用当前后端生成一次。CLI全部工具、MCP、AstrBot原生联网继续关闭；第一版自动触发由确定性规则完成，**不增加一次模型调用来判断是否搜索**。这提供按需联网问答，不承诺模型任意多步自主检索。
5. 先LAP-17本地后端/切换，再LAP-18共用联网，再LAP-20自由群聊与直接群发、LAP-21表情包，最后按指定范围比较质量/成本。四项分别交付/回滚，用户自行观察额度，不加自动节流选模策略。

非目标：无新群消息的定时冷场/主动任务、私聊、视频/ASR/收到图片的理解、账号迁移、自动按额度或失败切后端、模型下载/升级、Ollama重装/全局修改、付费搜索/模型API、未经证据的完整验收承诺。LAP-17原“群聊参与”分支因用户追加明确拆为LAP-20详细规划，不删除旧需求，也不在17中顺手启用。

## 2. 当前证据与能力限制

### 2.1 代码证据（基线main `391be0f`）

| 文件/位置 | 当前实现 | 设计影响 |
| --- | --- | --- |
| `src/qqbot_gateway/config.py:normalize_settings` | schema1/2，backend只允许codebuddy_cli，停机校验/OS锁/hash复核/原子保存 | 增加schema3与后端profile，保留所有写入保护 |
| `src/qqbot_gateway/model_gateway.py:main/application/ModelQueue` | 固定CLIRunner；入口别名workbuddy-local；有界单并发；统一输出处理 | 选择runner并接共用检索包装；保留别名和回执元数据合同 |
| `src/qqbot_gateway/token_budget.py` | 可见UTF-8字节+序列化封套+预留，非精确token；CLI原生窗口拒绝显式值 | CLI限制保留；本地原生num_ctx另设且不得混称 |
| `plugins/qq_router/main.py:on_group` | 群/真实@/黑名单检查后，遇任意HTTP链接直接拒绝；本人历史；tool_set=None | 联网启用时只移除该能力拒绝分支，严格准入/去重仍在检索之前 |
| `src/qqbot_gateway/persona.py`、`scripts/configure_astrbot.py` | 固定政策写无联网；共用compose；工具/skills和AstrBot搜索关闭 | 政策按配置说明受控材料能力；两个compose调用方同步，不改persona角色正文 |
| `scripts/configure_bot.py`、`配置机器人.cmd` | 分组菜单、每项输入说明、当前只编辑一组模型参数 | 增加后端/当前profile编辑/联网与只读检查入口 |
| `scripts/manage.py` | 创建身份管理、启停锁、失败回收、本机网关模型状态；model启动等待10秒 | 本地模式需有界SSH/元数据预检和独立就绪状态，不影响CLI启动 |
| `workbuddy_cli_runner.py:ResultParser` | 接受result正文，未保留usage数值；工具事件拒绝 | 使用结果对象承载受限数值元数据，兼容输出/发送账本 |

锁定CLI2.168.0的静态包中，result构造含`usage`和`modelUsage`；`buildModelUsage`有inputTokens/outputTokens/cacheReadInputTokens/cacheCreationInputTokens。`total_cost_usd:0`为静态占位。另有ACP credit通路，但**不是本项目stream-json必然返回真实credit的证据**；不为取积分切ACP、不把token或占位0换算成真实积分。没有新增真实CLI请求。

### 2.2 本轮PC只读观测

2026-10-17 **14:53:59 +08:00**，本机忽略证据`state/lap19-pc-metadata.local.json`：

| 项目 | 观测 |
| --- | --- |
| 服务 | Ollama0.40.5，回环11434元数据API可用；监听分类仅loopback |
| 已安装 | 唯一tag `qwen3.5:9b-q4_K_M`，9.0B，GGUF，Q4_K_M，大小6550825550字节 |
| digest | `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90` |
| 元数据能力 | completion/vision/tools/thinking；thinking允许false/true、默认true；模型卡窗口262144 |
| 当前已加载 | 同一digest，context_length=16384，size_vram=6147423600字节；整卡显存7019/12227MiB |
| 连接 | SSH direct-tcpip到PC127.0.0.1:11434并GET /api/version返回200；未建立持久监听 |

这证明安装、元数据与通道可行；**不证明项目推理、速度、非思考、结构化输出、实际窗口限制或人设质量已通过**。已加载16K是用户现有会话的观测，不是本项目写入参数。10:50空模型列表为旧快照，已被新观测更新；硬件不重复盘点。

本机known_hosts为空，首次严格策略在主机密钥检查阶段拒绝；随后在进程内以旧盘点留存的SHA256指纹做固定比对，成功后才使用家庭SSH凭据。未接受新指纹、未改known_hosts或PC文件；凭据未打印/提交。临时Paramiko5.0.0仅在uv隔离环境使用，未加入项目依赖。远程修改/安装/下载/启停/模型生成均为0。

### 2.3 联网提供方选择与真实限制

首版候选为笔记本进程内的`bing_rss`适配器，固定`https://cn.bing.com/search`的RSS响应，不新增账号/API付费或搜索服务。网页正文由同一受控HTTP客户端读取。**这是候选网页接口，不是微软承诺稳定的商业API。**

本机直接HTTP探测（非模型/非群消息）：www.bing.com的HTML/RSS均302；cn.bing.com RSS为200、10条记录；HTML为200但当前解析未取得结果；DuckDuckGo HTML为202且含验证码。RSS探针的`site:docs.ollama.com`返回前5域名均非该站，说明高级过滤/相关性不能凭HTTP200假定成立。尚未验收检索质量、时效与来源正文读取。

因此LAP-18先设检索质量门槛，未过不能标“联网可用”。DDGS的auto会选择/轮询多个引擎，不能当一次受控搜索直接放入；本版不引入DDGS自动聚合或其不受控extract。SearXNG需要额外实例运维，保留为后续替代方案，不在medium中临时安装Docker/WSL。Ollama官方搜索是独立云端API，要求Ollama账号/API key；打开本机Ollama不会自动赋予搜索，本轮不接该账号/额度来源。

## 3. 配置、迁移和配置cmd交互

### 3.1 schema3合同

canonical配置保留`llm.backend`与共用host/port/max_concurrency/queue/cleanup字段；新增`llm.profiles.codebuddy_cli`和`llm.profiles.ollama_ssh`。模型、强度、原生窗口、生成超时和输入预算仅归相应profile，不保留可写的顶层model影子。`resolve_backend(settings)`提供明确active视图；所有调用方改读该视图，不能让活动后端错用另一套参数。

| 字段 | 缺省/初始值 | 生效/校验 |
| --- | --- | --- |
| `schema_version` | 新配置3 | 兼容读取1/2，保存才迁移；不在读取时改本机文件 |
| `llm.backend` | `codebuddy_cli` | 仅codebuddy_cli/ollama_ssh；手动选择、停机保存、重启生效 |
| `llm.host/port/max_concurrency` | 127.0.0.1/8765/1 | 网关继续只监听回环；不提供QQ命令切换 |
| `llm.profiles.codebuddy_cli.model/reasoning_effort/context_window_tokens` | 新装deepseek-v4.1-flash/auto/null | 旧配置逐值保留；原生窗口仍只允许null；强度按CLI能力表与当前ACK |
| `llm.profiles.codebuddy_cli.run_timeout_seconds` | 新装90 | 旧llm值原样迁入，不回默认 |
| `llm.profiles.<backend>.input_budget` | 见下 | 包含原chat的context_input_limit_tokens/context_overhead_reserve_tokens/output_reserve_tokens；口径不改为精确token |
| CLI的`input_budget` | 新装16384/2048/2048 | 旧chat三值原样迁入；不扩大现有预算 |
| `llm.profiles.ollama_ssh.model` | `qwen3.5:9b-q4_K_M` | 只选已安装本地tag；元数据digest变化要求本机重新确认，不pull/latest/cloud映射 |
| `.ollama_ssh.expected_digest` | 初始未配置；本机确认后固定上述digest | 不在示例内绑定私有机器；缺失时只影响本地profile启用 |
| `.ollama_ssh.access_file` | `secrets/home-5070-runtime.local.json` | 仅项目secrets内本机忽略文件；CLI活动时不读取或认证PC |
| `.ollama_ssh.num_ctx` | 16384 | 初始采用已加载16K作为试验起点；整数4096..32768且不超元数据上限；每次原生请求options.num_ctx，不改Ollama全局环境 |
| `.ollama_ssh.think` | false | 首版仅false；菜单解释“关闭思考”，不能映射CLI high/max；元数据允许false才通过预检，真实效果待测 |
| `.ollama_ssh.num_predict` | 1024 | 整数128..4096；原生options.num_predict；生成token上限不等于QQ字符上限 |
| `.ollama_ssh.keep_alive_seconds` | 300 | 整数0..1800；请求级keep_alive；不预加载、不自动卸载/停止用户Ollama |
| `.ollama_ssh.temperature/top_p/top_k` | 0.7/0.8/20 | 首版高级profile固定候选，范围0..2、0..1且大于0、1..100；效果未验，不加presence_penalty或自动调参 |
| `.ollama_ssh.run_timeout_seconds` | 120 | 单次原生生成期限；超时不重发、不换后端 |
| 本地`input_budget` | 12288/2048/2048 | 保守字节预算；显式校验输入预算+输出预留<=num_ctx，输出预留>=num_predict；不声称是精确分词保证 |
| `chat.history_turns`及冷却/队列 | 继承原值 | 两后端共用用户选择；新装8轮；实际投喂按当前profile裁剪完整旧轮次 |
| `output.*` | 保留原值；缺省single | 不随切后端开启adaptive；人设正文、发送ACK/账本合同复用 |

本地访问文件由后续LAP-17本机初始化生成：host/port/user、DPAPI保护密码或显式指定的项目专用密钥、固定主机SHA256指纹；不把本轮Markdown访问说明直接当长期运行配置解析。只在明确的本地profile初始化中读取已有家庭资料并转换，保留旧文件；不读日常QQ/WorkBuddy密码，不写全局SSH配置或保存明文密码。凭据只给固定家庭主机的SSH连接，不给模型/检索客户端。

schema1/2迁移：后台读取只做内存归一化；旧CLI的model/effort/window/timeout和chat预算逐值迁入CLI profile，旧历史轮数/输出/群/黑名单和未知扩展保留；新增本地profile为未配置，web关闭。保存仍经过停机检查、OS锁、旧hash复核、完整备份、校验和原子替换；有新旧冲突值拒绝并说明，不猜测覆盖。一次保存后schema3旧程序不可直接读取，回滚必须先还原配对备份。

### 3.2 配置cmd界面

主菜单显示“当前后端 + 模型”，增加“后端与连接”和“联网搜索”。后端子页可选1 CodeBuddy/2 家庭PC本地，展示待切换profile、影响与保存结果；编辑当前模型/预算时明确归属，不把qwen填进CLI模型ID。两套值来回切换不丢失。

本地页提供“初始化家庭连接资料”“只读检查连接/已装模型”“原生上下文/输出上限/保温”；只读检查为显式动作，最多一次SSH认证和有界元数据请求，无`/chat`、`/generate`、预加载、pull或端口开放。失败区分SSH不通、主机指纹不符、Ollama未运行、模型/digest不符、参数元数据不支持。运行中可查看/只读检查，但所有配置保存仍拒绝；不替用户关闭正在运行的实例。

切换提示：当前机器人须先关闭；保存后重新启动；切后端/模型/digest/原生生成参数会开启本人当前群的新上下文，旧历史保留。非活动profile编辑不改变活动会话版本。联网设置变化只在重启后生效，普通请求的检索时间/内容不参与会话版本hash。

## 4. 本地后端请求、状态和失败合同

网关和AstrBot仍使用`workbuddy-local`别名与本地bearer token；远端真实模型由profile指定，不让群消息/请求字段改host、tag、think或options。backend工厂产生CLIRunner或OllamaSSHRunner，二者返回`BackendResult(text, usage, parameters, finish_reason)`；共用输出处理不另开旁路发送。

SSH连接归模型网关进程管理，严格固定主机指纹，在认证前核对；禁止AutoAddPolicy。原生HTTP仅通过direct-tcpip到固定127.0.0.1:11434，避免新增本地转发监听与外部ssh进程。通道建立/连接重建失败不重复提交POST；下一条独立请求可以在状态允许时新建连接，同一请求不能重发。

本地启动在QQ准入前对所选profile做有界SSH/版本/tags/show预检（show是元数据POST，不是生成）；最多一次认证，单项连接/读取有期限，总计<=25秒。model组件等待上限从10秒按所选后端调整到30秒；失败按现有创建身份回收本次已启动组件，不改PC服务。CLI模式不进行PC预检、不读取家庭凭据，PC关机仍可正常启动CLI路线。

单个已准入请求只POST一次`/api/chat`，携带完整system与本人裁剪历史、当前问题、stream:false、think:false、keep_alive和上述options；不提供tools、远端system覆盖、任意URL、图片或MCP。adaptive可传与LAP-16一致的JSON schema，但须先实测兼容；single不加JSON format。解析只接收对应模型的assistant文本、done=true；拒绝tool_calls、非空thinking（与本profile冲突）、不完整/超限/错误响应。JSON格式失败按原LAP-16合同本地降级或拒绝，不调用模型修复。

参数页显示“请求值/元数据支持/真实观测”三种证据；元数据标称262144不能显示为本次有效上下文。实际num_ctx与think效果需结合本次生成响应、`/api/ps`和资源观测验证；ps读取不消耗生成额度，也不能单独证明某条请求或忙闲状态。

网关队列仍单并发。超时/取消关闭本请求HTTP/SSH通道；不发送远程进程终止命令。Ollama是否及时停止计算尚未验证；无法确认请求完成时记`REMOTE_RESULT_UNKNOWN`，阻止自动重复或后续生成，须本机操作者核对/显式解除，不能仅以ps显示模型已加载判为完成。关闭机器人只释放本项目资源，不关闭用户Ollama，不按Python/Node/QQ进程名批量结束。

状态页分别显示本地组件、QQ、当前backend与模型、SSH/Ollama元数据检查、最近真实生成、排队/错误和历史错误时间。`cli_attempts`仅计CLI，新增`backend_attempts`及本地POST计数；连接200不得标真实推理通过。真实接口响应大小、连接/读超时都有上限。provider超时须满足排队30+检索15+本地生成120+安全余量10=175秒；沿用当前180秒须校验关系，修改任一上限超出即拒绝保存。

## 5. 共用联网的行为合同

### 5.1 触发、查询与调度

联网发生在群/黑名单/真实@/消息去重/本人队列/停止标记检查之后，进入全局模型队列后执行，使检索和生成共用排队与取消。未准入消息不产生HTTP请求，不进入新增历史。

| 当前问题 | enabled=true且trigger=auto | 次数 |
| --- | --- | --- |
| 明确“搜索/搜一下/联网查/帮我查”等事实查找 | 搜索；“查一下你记不记得口令/看看我的代码”等会话内任务排除 | 至多1个查询 |
| “现在/今天/最新/最近/目前”结合新闻/版本/价格/天气/赛程/在任等事实问题 | 搜索；“你今天开心吗/现在陪我聊聊”排除 | 至多1个查询 |
| 带HTTP(S) URL并要求读/总结/解释/核对网页 | 直接读取所给公共页面；本请求不再补搜索 | 至多2页 |
| 仅有公共URL | 按读取该链接处理；B站等视频仍提示内容能力未接入 | 至多2页 |
| 普通闲聊、旧知识解释、提到网站名称但无时效/查找要求 | 不检索 | 0 |
| 当前明确“不要联网/只根据这段文字/只凭记忆” | 禁止本次检索；回答不能声称实时核验 | 0 |
| “刚才那个最新多少”且本条缺少明确对象 | 请求补充对象，不把整段历史上传搜索服务 | 0 |

否定/仅据提供文字的本次限制优先于时效词。规则带本地可测试的中文短语/意图组合，禁止只匹配“今天/查”单字；第一版误判/漏判通过样本修正规则，不让medium悄悄增加模型分类调用。群友可说“联网查……”显式触发，也可限制本条不联网。

外发仅当前请求中必要的短查询（最多240字符）：去真实@、配置内账号/群号、明确QQ标识、凭据/本机路径；不上传人设、system、整段历史或原始群事件。查询过长/敏感或缺主体不能安全形成时，要求用户改写简短查询；不声称规则能识别一切隐私。搜索无Cookie/个人登录态/全局代理继承，不调用工作环境账号。显式请求已有公共URL不为它自动做站外搜索。

### 5.2 联网配置与预算

| `web.*`字段 | 默认/有效范围 | 说明 |
| --- | --- | --- |
| `enabled` | false | 保证升级默认行为；后续LAP-18验收后由操作者在配置cmd显式开启 |
| `trigger` | auto；可选explicit | 本次用户选择auto，开启时默认采用；explicit只接受明确查找/读链接 |
| `provider` | bing_rss | 首版唯一实现候选；固定站点/路径，无账号/付费；未过质量门槛不得宣传已可用 |
| `max_searches` | 1，首版固定 | 同一请求不翻页、不重写查询重试、不并发多引擎 |
| `max_results` | 5，1..5 | 上游即使返10条也只接前5条有效去重候选 |
| `max_pages` | 2，1..2 | 搜索后读前2个不同有效页面；直接URL请求也共用上限 |
| `timeout_seconds` | 15，5..15 | 整次检索硬期限；单次网络连接<=3秒/读取<=6秒且受总期限约束 |
| `max_redirects` | 2，0..2 | 每跳校验目标；上游302也计入网络请求审计 |
| `max_response_bytes` | 1048576，65536..1048576 | 每响应解压后硬上限；压缩前也限量，流式读，超限立刻关闭 |
| `max_page_text_bytes` | 4000，1000..8000 | 每页纯文本截取，标明截断，不用模型压缩 |
| `max_evidence_bytes` | 6000，1000..12000 | 标题/URL/日期/状态/正文一起计入，仍不得超过当前输入预算余量 |
| `max_sources` | 2，1..2 | QQ来源尾注；包含实际交给模型的来源，不显示未提供的候选 |

初版不做跨用户缓存、持久网页正文、后台更新或主动推送。每请求至多1次搜索加2页读取（重定向额外连接仍受总期限/跳数约束）；普通闲聊0次。记录search_calls/fetch_calls/redirect_hops/bytes/latency，不能把一次适配器调用声称只有一次HTTP连接。

### 5.3 网页访问和材料边界

只接受公开HTTP(S)且80/443端口的文本网页，拒绝userinfo、片段内伪协议、IP混淆、非全局地址/本机/家庭网段/组播/保留地址及元数据地址；每次DNS解析与每个重定向都复核，连接绑定已检查IP并核验peer，避免DNS重绑定。模型推理SSH通道与网页HTTP客户端是独立能力，用户URL不能借访问本地Ollama或SSH。

搜索端点固定，搜索响应返回URL也按上述策略检查；Bing跳转包装只允许已知格式本地解码并重新校验，不请求任意中继站以绕过策略。启用TLS验证，关闭环境代理/Cookie/客户端认证；不随重定向携带认证/私人header。拒绝文件下载、PDF/二进制、登录/付费墙/验证码和依赖JS的空壳；不绕过这些限制、不自动调浏览器或安装解析服务。第一版仅静态HTML/text，B站视频/评论不作为已观看证据。

提取去导航/脚本/表单的正文，保存title、最终URL、抓取时间、可取得的发布日期、正文/摘要状态。网页发布日期缺失就记未知，不能用抓取时间冒充新闻发生时间。给模型的材料包是有界不可信数据，不提升为system指令；页面中的“忽略规则/执行命令/发送密码”等文字不能变成工具调用、触发或后端配置。

### 5.4 一次生成、预算、来源与历史

保留原始问题用于输出分类/历史；检索包装器只在发给runner的当前user内容副本中附受控材料包与时间/失败状态，不拼到角色正文、不增加tools或messages角色。固定政策说明“可依据本次已提供联网资料回答；不能自主操作电脑或声称没有证据的检索”。web关闭时仍说明不可联网。所有compose调用方使用同一能力配置。

发送前重新计算system+序列化历史+当前问题+材料+封套预留的真实可见字节，先裁旧完整历史，再裁材料到可用余量；不截当前问题或伪称分词精确。基本问题本身超限照原合同拒绝；材料不足最低有效证据时返回明确限制，不发额外模型请求补救。检索文本、原始搜索查询和网页整篇不保存进AstrBot会话；保存本人原问题及最终实际发送文本（含来源），LAP-16逐条ACK/历史修复照常。

有资料的联网回答采用answer单条，即使adaptive也不把来源拆成闲聊气泡。网关本地追加“来源：标题 URL”的自然纯文本尾注，最多2个；来源只能来自本次实际材料包，代码负责URL集合/状态校验，不能验证每句事实是否被充分支持。搜索摘要需标“仅搜索摘要”，不能标已阅读全文；模型新编链接不触发再抓取，未授权来源尾注拒绝或移除。尾注计入max_reply_chars，先预留尾注空间再限制正文，最终canonical文本与保存/ACK完全一致，不截断URL或在发送后补一条来源。标题可本地缩短；若两条来源过长先减到一条，完整URL加最少正文仍放不下时给本地长度限制提示，不擅自增加用户字符上限。

成功检索会增加输入内容；CodeBuddy credits可能因此增加。本地模型生成没有CodeBuddy调用，但查询仍发送到选定公共搜索站点；不宣传“本地路线完全不出网”。

### 5.5 失败分支

- enabled=false：文字照旧；带URL的读取请求给本地未开启提示，不假装读过页面。
- 全部查询/读取失败、CAPTCHA/429、无相关结果：本地短提示“这次没查到可核对的资料，请稍后再试/换个链接”，**0次模型生成**；不凭模型记忆输出最新事实，不换付费API或引擎。
- 两页仅一页成功：仅使用该页，并明确材料范围；不重试失败页。
- 只有搜索摘要：一般事实可明确按摘要回答；要求精确原文/完整网页内容/高风险时效结论时说明证据不足，不能冒充正文或完整核验。
- URL被拦截/登录/视频/JS空壳：说明对应限制，不扩大工具能力。页内注入不改变准入/配置。
- 停止/用户任务取消/已过检索期限：取消HTTP，禁止继续开始模型或发送；已有后端请求按第4节未知结果合同处理。
- 模型协议/输出/ACK失败：复用既有单次尝试与逐条账本，不为补来源/换措辞再次生成。框架不得额外fallback或开启内建search。

## 6. 文件范围和实施顺序

| 任务 | 预计涉及文件 | 交付顺序 |
| --- | --- | --- |
| LAP-17 本地接入/切换 | `config.py`、`token_budget.py`、`model_gateway.py`、新增`backends.py`/`ollama_ssh_runner.py`/`ssh_transport.py`、`errors.py`；`persona.py`的统一会话版本函数；`plugins/qq_router/main.py`、`configure_astrbot.py`、`configure_bot.py`、`manage.py`；settings.example/pyproject及锁定依赖、相关测试/README/该任务HANDOFF | ①领取/建HANDOFF ②schema3迁移与两profile/菜单 ③backend结果合同与CLI回归 ④固定指纹SSH/原生runner/元数据检查 ⑤会话版本/状态/启停回收 ⑥离线与实际框架合成回归 ⑦有后续授权才离群本地推理/真实启用 |
| LAP-18 共用联网 | 新增`web_retrieval.py`/`web_policy.py`及HTML正文提取；`config.py`/`configure_bot.py`/settings.example；网关包装、`token_budget.py`/`reply_plan.py`/`chat_text.py`的预算/来源处理；`persona.py`、router链接分支、`configure_astrbot.py`共用能力政策；相关测试/README/该任务HANDOFF | ①领取/建HANDOFF ②候选引擎质量门槛 ③独立受控读取/规则/预算与离线测试 ④两runner共用包装 ⑤来源单条与历史/ACK验证 ⑥无模型公共网页验证 ⑦按授权分别做两后端联网生成与群验收 |
| 成本与比较（归两项对应验收） | backend结果/CLI parser、状态与数值统计模块；不读取用户私密会话日志 | 允许的数值指标先离线；真实credit未知就保留未知；不新增自动后台模型/账户探测 |

本轮只修改计划/索引/交接，不创建上述实现文件。新代码包/版本须实施时核对并锁定，不能把临时uv环境直接当部署依赖。原124项离线证据为LAP-16旧基线，本轮没有重跑或把它归为新后端通过。

## 7. 验证与验收出口

### 7.1 LAP-17离线与集成必测

- 旧schema1/2逐值迁移、扩展字段保留、活动/非活动profile、错误枚举/类型/路径与预算关系；停机锁/hash竞争/备份原子保存；原设置不回默认。
- 配置cmd中文空格路径/外部CWD/两profile来回切换；保存与状态检查不POST生成；CLI模式PC离线依然启动、无家庭资料读取。
- 使用假SSH/HTTP服务断言固定主机指纹在认证前核验、固定目的端、只POST一次、参数与序列化正确；tag/digest不符/思考不符/tool_calls/超长/半JSON/超时取消/未知结果阻止后续调用等反例。
- 实际AstrBot合成回环覆盖两runner替身、single/adaptive、字面代码/JSON、切后端新上下文且旧历史保留、ACK/部分交付/启动恢复；不连QQ或真实模型。
- 适用CLI/入口/预算/生命周期回归通过；清理只触及本项目创建身份，不终止PC Ollama/日常QQ/WorkBuddy。新本地API计数与CLI计数分开。

真实阶段需用户后续指定执行归属/范围：先元数据无推理检查；再最多6个离群本地生成样例覆盖冷/热、角色闲聊、严肃问答、single/adaptive/字面代码和两轮本人记忆。一个样例若失败不自动重跑。记录digest/参数、输出协议/质量、首字不可测则明确、总时延/prompt_eval_count/eval_count/显存与offload。未经样例验证不承诺速度或关闭思考效果；离群通过后再单独登记真实QQ范围。

### 7.2 LAP-18检索质量门槛与离线必测

实现开始先用3个无隐私公共查询（中文事实、当日可核对时效、官方站点限定）复核候选适配器。至少2/3有真正相关且可读取来源；站点限定要求在代码中过滤，过滤后无来源必须报告不足；至少1项时效样例能区分发布日期与抓取时间。200/结果数量不是通过标准，不保留完整网页到Git。

若候选接口持续无关/验证码或达不到门槛：可独立完成安全网页读取、配置和离线包装，明确LAP-18搜索未完成并回规划；不能自行换付费API、注册Ollama云账号、部署SearXNG或放开CLI WebSearch。SearXNG/官方key搜索若需替代，要先更新方案并由用户决定相应账号/部署，不把“有来源URL”当质量过关。

离线合成覆盖：触发正反例/本次禁止联网/链接和视频/模糊指代；黑名单与无@零HTTP；SSRF的IPv4/IPv6、DNS重绑定/重定向到内网、异常端口、TLS/压缩炸弹/大小/超时/验证码/非文本；搜索和页数/调用量硬上限；页面指令注入；超预算裁剪；原始材料不入历史；来源存在性/尾注限额/字面代码；两后端都只有一次生成，检索全失败0生成；取消/ACK/恢复无旁路补发。

真实联网验收区分：仅公共搜索/网页读取通过；CodeBuddy真实联网生成；本地真实联网生成；授权群真实@/无@/黑名单与纯文本来源/ACK。四者不能互相替代。调用与费用预算由用户后续明确，默认实施回归0真实CodeBuddy调用，不为追查旧trace消费额度。

### 7.3 质量与credits对比

使用同一人设/输出模式、同一组不含私人消息的样题和相同新上下文，手动分两轮切换；禁止一条QQ消息同时调用两个后端。分别记录风格/事实/记忆/来源遵循、失败数和时延。联网样题注明材料取得时间，必要时用同一离线材料比较生成质量，避免把搜索结果变化归因于模型。

数值统计只保留trace、backend/model、时延、输入可见字节、明确上报的token/cache数与检索计数，不记录原问题/网页正文。CLI credits默认null/unknown；仅有当前stream-json可验证的真实积分字段才显示reported，不把`total_cost_usd:0`、token或ACP能力当实扣。账户余额前后对照可由用户自行提供，并注明同期其他使用无法归因；不读取日常账号密码或为测余额另发模型请求。

不在计划中指定“消耗多少算多”，由用户据实际可用额度与体验判断；始终手动选择。两路线各通过真实质量与联网验收，才能写“双路线可用”；旧P01/多人/完整文本交付等差额继续单列。

## 8. 分支、回滚与交接

开始分支main、HEAD391be0f，工作区干净；LAP-19只有本任务文档，按长期授权在main审阅后提交/推送。LAP-17/18由后续session领取，先检查TASKS与工作区；无冲突可继续main，各自独立审阅检查点。需隔离时用`codex/lap-17-local-backend`、`codex/lap-18-shared-web`，不重置别人的修改或抢同一bot运行归属。

回滚：先停本项目并完成/隔离pending发送账本；关闭web可只保存enabled=false并重启；本地故障可由操作者选回保留的CLI profile并重启。切换不删除历史、原生模型、SSH访问资料或用户Ollama。代码回退到schema2版本时必须恢复同一检查点的配置备份，保留schema3备份与新历史；不让旧程序读新配置硬跑。SSH指纹不符则停止本地连接，不能以自动接受新指纹修复。

未验证能力清单：真实本地生成/显存峰值/取消后远端停止、think:false实际表现、adaptive JSON及质量；共享检索相关性/时效/正文质量与内网阻断实施；stream-json真实credits；两后端联网/真实群/完整文本交付。均不得因本轮SSH或网页探测成功划为通过。

## 9. 官方依据与阅读边界

- [Ollama Windows后台/API](https://docs.ollama.com/windows)：PC开机、Ollama后台与SSH可达即可作为模型服务前提，不要求常开聊天窗口；项目接入仍需LAP-17。
- [原生chat请求](https://docs.ollama.com/api/chat)、[模型元数据show](https://docs.ollama.com/api-reference/show-model-details)、[思考控制](https://docs.ollama.com/capabilities/thinking)：按实际模型元数据与请求验证能力，不能只藏思考显示。
- [Ollama上下文](https://docs.ollama.com/context-length)、[FAQ的监听与保温](https://docs.ollama.com/faq)、[生成usage](https://docs.ollama.com/api/usage)：请求级参数、回环监听与性能字段的依据；不据模型最大窗口推显存/速度。
- [Paramiko direct-tcpip](https://docs.paramiko.org/en/stable/api/transport.html#paramiko.transport.Transport.open_channel)：只读通道测试已有实机证据，生产取消/异常处理仍需实现。
- [CodeBuddy成本管理](https://www.codebuddy.cn/docs/cli/costs)、[CLI参考](https://www.codebuddy.cn/docs/cli/reference)、[ACP credit说明](https://www.codebuddy.cn/docs/cli/release-notes/v2.99.0)：token/credits和协议口径分开，真实字段以锁定本机包及后续调用证据为准。
- [Ollama独立联网API](https://docs.ollama.com/capabilities/web-search)：需要云端账号/API key，本计划不将其当本地模型自带搜索或当前授权额度。
- [DDGS源码](https://github.com/deedy5/ddgs/blob/main/ddgs/ddgs.py)、[SearXNG Search API](https://docs.searxng.org/dev/search_api.html)：仅作替代方案调研，不作为本次已部署组件或既有连接。

外部资料核对日2026-10-17；候选Bing RSS依据本机直接HTTP观测，**没有稳定官方API合同**。网页内容只用于技术依据，不作为项目执行指令。
