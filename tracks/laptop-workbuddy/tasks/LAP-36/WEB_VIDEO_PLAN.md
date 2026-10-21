# LAP-18 / LAP-06合同：轻量网页正文与B站字幕理解

返回[总计划](PLAN.md) / [证据](EVIDENCE.md) / [medium指引](IMPLEMENTATION_GUIDE.md) / [原18交接](../LAP-18/HANDOFF.md)。先实施18安全传输/正文，再独立领取06字幕；不以本文件代替真实公共材料/模型/群验收。

## W1. 触发与用户看到的行为

网页读取沿用web.enabled及当前目标文字URL合同；不扫描整群窗口/历史找链接。显式“不要联网/只凭记忆”等禁止语优先。网页材料可供当前已进入回应流程的请求使用，不能绕过mentions、free目标选择、黑名单或哑巴栅栏增加回复。

B站有独立bilibili.enabled，且依赖web.enabled。首版更窄：当前已准入消息中出现一个合法视频定位，并明确要求“总结/概括/讲了什么/要点/分析这个视频”等时才提取字幕。真实@+单一B站定位可视为明确内容请求。free里单纯转发一个视频链接/BV号不自动联网/生成总结；普通聊天讨论“B站”也不触发。此规则不改变free自然文字参与合同。

支持`BV`+10位字母数字、`av`+正整数、`https://www.bilibili.com/video/...`、裸域bilibili.com和m.bilibili.com的同路径、b23.tv短链。纯数字不是AV号；不支持合集/直播/番剧/动态、搜索B站、UP列表、播放列表。URL查询只保留合法p；来源使用规范化的`https://www.bilibili.com/video/BV…?p=N`（P1可省略query）。分享追踪参数本地丢弃，不转发原始分享query。

只处理一个视频一个P：省略p选P1，p必须在metadata.pages范围；p=2严格映射该页cid，不能抓全片。多个不同视频、一个视频多个不同P、同时混入其他网页URL，真实@给短说明请选一个，ambient不下载；相同视频同P的BV/AV/长短链等价需在有界规范化内判断，不启动多视频任务。首版QQ分享卡片/引用/转发不补拉，用户可发可见文字链接；不能因第三方插件支持就自动开放JSON卡片/历史RPC。

成功答复自然纯文本，通常250—500字、一个大意与3—5要点；来源行由程序按真实材料生成，标明网页正文/人工字幕/自动字幕、实际P、完整/节选、规范化链接。QQ里不输出Markdown表格/代码围栏或图片卡片。不做未经来源支持的“看完整个视频/完整画面理解”宣称。

## W2. 共用公共传输与当前网络缺口

从web_retrieval抽出`public_http.py`，保留原public_ip/safe_url/PublicResolver/PublicConnector/PublicHTTP/审计接口兼容导出，供网页、vision和B站调用。新增固定用途策略page/image/bilibili_api/subtitle/doh/search，不能把一个任意URL工具暴露给模型。每个用途有独立域名/MIME/认证上限，不能为了支持JSON而放松原网页或图片策略。

保留并补测：初始/每跳URL检查，http/https默认端口限制，拒绝userinfo/控制字符/反斜杠/歧义IP/本地与保留地址；解析结果全公网且混合公网/私网整组拒绝；连接固定这些地址并核对实际peer；HTTPS证书与目标主机名校验；trust_env=false/无代理/默认无Cookie/无自动重试。DNS重新解析、HTTP压缩前后、字节/总耗时/重定向限制均不能旁路。CNAME或重定向最终到私网也拒绝。

网页用户URL含明显密码/token/session/key等凭据型query或本机/内部域名时拒绝，不把凭据发第三方；图片/字幕由已准入可信响应给出的临时签名query只在受控fetch内部使用，不输出/持久化。不要把所有query一刀切丢掉导致文章定位错误；正常非凭据文章参数仍受safe_url校验。

| 配置/固定策略 | 默认及合同 |
| --- | --- |
| public_network.resolver | system；仅system/cloudflare_doh，缺字段沿用system |
| public_network.ca_bundle_file | null；可显式选固定项目忽略`secrets/public-network-ca.local.pem`，拒任意路径/符号链接/私钥/超1MiB文件 |
| DoH服务 | 代码固定`https://cloudflare-dns.com/dns-query`，公共bootstrap仅1.1.1.1；TLS仍验证cloudflare-dns.com，不从系统DNS得到该bootstrap |
| DoH请求 | 仅已验证公共hostname的A查询，无URL路径/query/群消息；一次32KiB/3秒、无重定向/无Cookie/无代理 |
| DoH结果 | Status=0、Question匹配、有限CNAME链且无环、有限A答案；所有返回地址逐一公网检查，混合结果拒绝；不跟随任意服务URL |
| DNS预算/缓存 | 每轮最多8次远端解析/最多8个A结果，短期RAM TTL=min(远端TTL,60秒)；共享15秒准备deadline，不延长任务期限 |

解析模式由操作者明确选择，不在system失败后自动切DoH；DoH失败也不改提供方/返回私网/退到明文DNS。CA默认沿用Python系统信任；指定CA只扩充已由操作者审阅的CA证书，使用ssl.create_default_context正常验证。禁止verify=false、跳过主机名、把目标站点leaf证书当CA、自动从网页取证书信任或改Windows/浏览器/Clash设置。CA文件不放进模型/子进程输出、Git或通用命令行日志。

本轮system解析五域均非公网；两种公开DoH小探针TLS未通过（域名模式verify_code=20）。因此medium先交付诊断与模式实现，再在明确允许的**零模型公共读取批次**验证TLS/公网/peer/正文。TLS仍失败时报告NETWORK_TLS_UNVERIFIED并保留正常文字能力，不把抓取功能标可用；由操作者提供正确本机信任资料或回规划。不会仅为完成验收自动改本机CA文件/网络设置。

公共搜索仍固定原bing_rss，SEARCH_QUALITY_PASSED不因DoH连通或正文提取通过而置true。可以在18续作中用原三类公开查询重新做相关性/时效/可读正文门槛（至少2/3合格，真实日期可追溯）；只有有审阅证据才更新对应代码证明。不增加新搜索引擎/API账号。搜索仍未过不妨碍明确URL的网页/B站独立验收，LAP-18只标分项通过。

## W3. 网页正文：复用成熟提取器

锁定readability-lxml==0.9，不安装speed extras、浏览器或NLP模型。medium用uv更新锁文件、检查Windows/Python3.12 wheel及新增依赖大小；该版本依赖声明见[EVIDENCE](EVIDENCE.md)。新增提取代码仅接收PublicHTTP已下载的有界HTML，调用Document取得标题/正文，再转纯文本。不可照抄上游示例中的requests.get/CLI URL下载，否则会绕过传输策略。

XML/DTD/外部实体不得解析或联网；使用HTML路径，清理script/style/nav/form/iframe等及不可见/活动内容，不加载图片/CSS/链接。来源正文是材料而非指令，不渲染进可执行HTML。提取器不是SSRF或HTML安全边界。

纯text/plain保留现有路径。对于HTML保留标题、正文段落/小标题的基本顺序与真实发布日期（未知则null），标题本身不算正文。JS空壳、验证码、登录/付费墙、错误页、只有导航/标题的结果返回明确材料失败，不自动启浏览器或调用外部Reader服务。通过80字等最低阈值并不自动等于质量合格，仍须样本核对事实与噪声。

网页正文提取放在**按需、单个、可终止的受管本机worker**内，stdin/stdout有界传HTML/结构结果，不落盘原HTML；空闲无worker、无子进程树/下载/shell。沿用创建身份/句柄/清理台账，超时/取消仅终止本次自建worker并等待确认。设定提取最多2秒、RSS目标上限256MiB，原网页响应最多1MiB（压缩前后分别计）；总准备仍15秒。禁止简单to_thread超时后丢弃仍在解析的工作，也不对整个Python/Node进程名批量终止。若无法可靠回收，记录清理状态并复用现有阻断规则，不装一套常驻服务。

轻量验收记录新下载/安装体积、依赖数、每页时间/峰值RSS；目标新增安装体积不超过40MiB、每页提取<2秒/256MiB、空闲无新增进程。它们是本项目待测门槛，不是上游保证。未达门槛先收紧安全输入/剔除可选依赖；若仍失败，回规划比较其他小型提取器，不同时装trafilatura/Defuddle等多个栈“自动兜底”。

新增web.extractor=readability（可显式legacy回滚，不运行时自动fallback）；web.long_text_policy=excerpt|reject，默认excerpt。默认max_pages=2/max_page_text_bytes=4000/max_evidence_bytes=6000/max_sources=2/timeout=15沿用。已有web.enabled不自动改为false或true；新解析逻辑随代码下次正常启动生效，需先完成离线/公共质量检查。

## W4. B站字幕：固定的最小开源复用

新增`bilibili_subtitles.py`包装与`vendor/ytdlp_bili_subtitles.py`最小复用文件、Unlicense及来源/上游提交/修改说明；不安装整套AstrBot总结插件或另接模型API。来源固定yt-dlp提交`897341241f2bfb2439fe0367f4c7c9ccd29a3828`。

保留上游字幕列表/字段语义，移除danmaku条目、下载所有语言、json2srt冗余编号；先选一轨再下载。上游`_get_subtitles`在此快照没有调用_sign_wbi；按相同字幕端点使用，不预先复制播放/指纹/签名流程。失败不切端点、指纹伪装或连续刷新认证。记录这项改造的差异，方便以后对照上游小片段更新；不能把整个播放器源码复制进来再长期维护。

每轮最多6次业务HTTP请求（每跳也计）、最多1个视频/1个P/1条字幕：

1. 短链才请求b23.tv，最多2跳且每跳目的必须为明确B站允许域；不读取跳转页正文，不接受JS跳转，不向短链发Cookie。规范化成功后统一长链；非短链省去这步。
2. 固定`https://api.bilibili.com/x/web-interface/view`，仅bvid或aid，取得真实bvid、pages/cid/part/duration、title、pubdate；不使用desc做视频总结。响应<=1MiB，有限pages数组和数值/类型检查，拒错误code/缺页/超20分钟当前P。
3. 固定`https://api.bilibili.com/x/player/wbi/v2`，仅当前bvid（或aid）与cid，读取need_login_subtitle及subtitle.subtitles。错误/需登录分别归类，不再请求播放信息或平台AI摘要。
4. 轨道选择优先明确语言的人工字幕，再同语自动字幕；中文默认，其次英文；一次只选一轨。人工/自动与语言进入来源。没有合格轨道返回NO_SUBTITLE，不下载弹幕/音轨替代。
5. 字幕只接受来自上述响应的https或scheme-relative URL，scheme-relative固定补https；精确域仅aisubtitle.hdslb.com、i0.hdslb.com、i1.hdslb.com，路径限定/bfs/ai_subtitle/或/bfs/subtitle/；每跳同样验证、公网/peer/TLS/1MiB/JSON限制，无Cookie。新增其他域名/路径须有新证据回规划，不开*.bilibili.com或*.bilivideo.com通配。
6. 解析JSON.body，最多10,000行，每行有限content/有限非负from/to且to>=from，时间不超当前P允许范围；稳定按时间处理，去空白/相邻重复字幕但不生成新语义。MIME/JSON结构/错误HTML/截断压缩/异常时间返回对应错误。

API/字幕响应独立于网页验证码关键词检查，不能把JSON中正常出现“验证码”等字幕文字误判成HTTP登录墙。反之，错误HTML不被当JSON内容。B站端点是第三方维护的事实接口，兼容性须真实验证，不承诺长期稳定。

### 认证选择

bilibili.auth_mode=none默认；可显式选sessdata。none匿名失败后不自动换身份重试。sessdata仅在操作者明确提供的固定忽略`secrets/bilibili-session.local.json`读取SESSDATA，不读浏览器/日常QQ/WorkBuddy密码，不扫码登录，不把Cookie写进features.yaml、命令行、日志、报告、模型或Git。实现可提供无回显本机录入/校验格式工具，但不验证账号密码或自动刷新登录。

仅对api.bilibili.com上述固定API发送Cookie，禁止重定向携带；网页、短链、字幕CDN、DoH、模型/SSH都不接收该凭据。none不读取凭据文件。凭据缺失/过期、403/412/429分别短错误，0重试/换账号/付费接口；提供方要求更多Cookie字段/WBI新流程才可工作时记录缺口回规划。无需凭据的代码/离线部分先交付，不能要求用户把Cookie发进聊天。

## W5. 长内容与token预算合同

原始网页HTML、完整字幕JSON、多个语言或SRT编号不进入模型；只保留当前问题、必要标题/来源/有限文本。新增提取/筛选0模型调用，成功请求所选runner至多1次生成。继续用最终system+历史+记忆+成员+图片预留+材料整体预算，裁整对旧历史后再减材料，当前用户问题和固定政策不能截掉。CLI内部恢复次数仍按旧差额，不作上游精确一次承诺。

默认公共材料总计6000 UTF-8字节，含JSON字段、标题/来源/范围/时间戳，不能各模块分别塞满6000；单网页4000，最多2页共享6000；B站只处理一个视频，正文片段和元数据共享6000。若与图片/记忆等合用，取最终剩余较小值；准备期限同用现有15秒，不每阶段重新计时。字节数不宣称等于模型tokens，记录真实usage（如果后端有返回）与保守输入量。

`long_text_policy`/`long_subtitle_policy`为excerpt时，本地只做**确定性的片段裁选**：

- 全文在材料/最终预算内，发送全部合格正文，coverage=full。
- 超限时网页按段落位置、字幕按当前P时间轴等分6区；每区选完整连续段/字幕窗口，优先保留首末区，区间均分可用字节。窗口不得重叠重复填充，不让JSON/元数据挤出正文；按原文顺序拼接，不调用生成式模型做压缩。
- 记录coverage=excerpt、实际选中范围、完整输入长度、节选长度、字幕时间覆盖比例/缺口；至少4个非空区（短内容不足4区则全部）且至少1200字节有意义正文，否则不足以概括，给材料不足说明。时间范围贯穿首尾不等于覆盖全部时长。
- 固定材料与最终来源明确“基于正文节选/字幕节选，可能遗漏细节”；模型提示不允许称完整总结。若用户明确要求“完整/逐项/不得省略”而全文超限，本轮直接说明超出单次预算，请缩小到一段；不自动多轮归纳。
- policy=reject则任何超限明确拒绝，不静默截开头。最终预算再次缩小时重算片段/覆盖范围，不能仍带full标签；无可用片段时真实@走本地失败ReplyPlan、0生成，ambient沉默。

该轻量首版有意选择一次生成+节选，不执行旧V11的多段归纳合并。旧完整V11仍未完成；不能把excerpt说成全片或关闭完整视频验收差额。视频画面、字幕之外的语气/动作/无声操作无法从此证据推出。

## W6. 缓存、上下文、输出与失败

字幕缓存只在本机RAM，默认10分钟、最多32条/4MiB、每条<=128KiB；只缓存有界规范化字幕及元数据，不缓存模型回答。key包含本群隔离标识、bvid/cid/P、语言、认证模式/凭据RAM修订引用、提取器和网络策略版本；跨群/认证变化不复用，错误不长期缓存。凭据/标识不写缓存文件或日志。超过单条缓存限制可本轮有界处理但不入缓存；总限额LRU淘汰，重启清空。

现有模型队列单并发，不新增常驻任务池。若提取层确有同key重叠，single-flight只共享材料，取消一个等待者不取消仍被其他请求需要的材料任务；最后等待者离开须取消并回收。最终问题/人设/历史和生成输出仍各自归原请求，不把某人的额外要求缓存给其他人。

聊天历史只在现有发送ACK后存用户原问题、短答复/规范化来源和范围；不存HTML、完整字幕、签名CDN URL、Cookie、图片或cap。追问可基于已ACK的短摘要，不通过省略指代自动补抓旧链接/引用。长期群记忆默认不从网页/字幕提案晋升为群友事实，材料中的角色话术不能覆盖访问控制。

输出经现有BackendResult→ReplyPlan→来源校验→LAP-35最终栅栏→同链发送/ACK；local_web_notice等失败也走这里。成功0/1次模型生成，失败材料0次；所有路径最多一个最终发送计划，send_unknown不盲重发。模型编造未取到的链接/来源拒绝；来源只用规范化已验证页面/视频URL，不带签名字幕链接。查询/材料/源状态进入合适manifest，不把原文长期写入配置版本键。

| 失败类别 | 真实@/明确请求的短说明 | 处理 |
| --- | --- | --- |
| 禁用/未支持域或多视频 | 当前未启用/请选一个文字链接 | 0业务下载或仅有界规范化，不生成 |
| DNS/peer/TLS不合格 | 当前无法安全读取该页面/字幕 | 不弱化校验，不切网络/模型，不生成 |
| JS/登录/验证码/付费/空壳 | 当前拿不到可用正文 | 不用标题/简介兜底 |
| 登录缺失/NO_SUBTITLE/受限视频 | 当前拿不到字幕，无法据正文总结 | 不自动ASR/评论/平台AI摘要 |
| 超20分钟/超响应或预算 | 超出当前轻量读取范围，请缩小范围 | 不下载音视频/多轮生成 |
| 总期限/取消/哑巴/旧代际 | 保持现有取消/哑巴语义，按must_reply与栅栏处理 | 终止自有worker/请求；不输出过时结果 |
| 模型失败/unknown/ACK未知 | 沿用现有失败分类和未决账 | 不重试/旁路send/清账重发 |

## W7. 配置及涉及文件

全部字段归features.yaml，代码校验/中文同行旁注/索引/旧单文件/双摘要与版本一起更新。配置修改下次正常启动生效；本轮及默认代码实施均不填写真实local/凭据、不自动启动/启用。

| 字段 | 默认/约束 |
| --- | --- |
| public_network.resolver / ca_bundle_file | system / null，W2固定选项/路径 |
| web.enabled / trigger / provider及既有上限 | 原默认false/auto/bing_rss，不改用户已保存值 |
| web.extractor | readability，允许显式legacy回滚；缺字段同readability |
| web.long_text_policy | excerpt；仅excerpt/reject |
| bilibili.enabled | false，bool；true要求web.enabled=true，否则配置错误 |
| bilibili.trigger | explicit，唯一首版值；涵盖真实@+单定位，拒扩到free所有链接 |
| bilibili.auth_mode | none；仅none/sessdata；凭据位置代码固定 |
| bilibili.preferred_language | zh；zh/en，人工优先、同语自动次之/英文回退并标注 |
| bilibili.long_subtitle_policy | excerpt；excerpt/reject |
| bilibili.max_duration_seconds | 1200；60..1200，不因只有字幕就改20分钟旧上限 |
| bilibili.max_subtitle_response_bytes | 1048576；65536..1048576，压缩前后分别限额 |
| bilibili.max_evidence_bytes | 6000；1000..6000，且再取web/最终剩余更小值 |
| bilibili.cache_ttl_seconds | 600；0..600，0禁缓存；数量/总大小代码固定上限 |

新增/修改：public_http.py、web_retrieval.py/web_policy.py、web_extractor.py及受管worker脚本、evidence_selection.py、bilibili_subtitles.py、vendor最小片段/许可证/来源、config/config_files/config_comments/config_layout_ops/backends/persona/turn_v2最终manifest与版本接点、model_gateway/WebRunner/router/provider、vision网络复用、LAP-34模板/配置索引、pyproject/uv.lock、README；新专项tests/probe/verify及报告、对应任务交接/进度。按任务拆提交；18不提前实现06，06不得悄悄改28生产能力表。

## W8. 验证矩阵与验收出口

| ID | 离线/真实核对重点 | 完成要求 |
| --- | --- | --- |
| NW-01 | system混合/私网/IPv6映射/重绑定/peer不匹配；DoH伪Question/CNAME环/私网答案/超限 | 全部拒绝，0私网HTTP |
| NW-02 | 固定bootstrap、TLS错证书/主机名/未知CA、CA路径/私钥注入、代理环境 | 不跳过验证，固定解析不借系统DNS，0全局设置改动 |
| NW-03 | 所选网络模式3个公开页面的实际TLS/公网/正文+图片域/字幕CDN解析 | 只按真实材料记录；失败仍network_unverified，不能借浏览连接器成绩 |
| WP-01 | 中文新闻/长文章/技术文档/英文文档至少各1个合成或可保存公开样本；两类失败页 | 有效页标题/至少3个关键事实仍在提取正文，去导航/脚本；失败页无假正文 |
| WP-02 | 真实公开样本至少中文2/技术文档1，先0模型人工比较 | 正文能支撑原问题、噪声可接受；JS页标限制，不算静态能力失败兜底 |
| WP-03 | 大/压缩炸弹/畸形HTML/worker超时/RSS/取消/stop | 有界且自有worker确实退出，WS/队列不被占死 |
| EV-01 | 全文/6区节选/4区不足/完整要求/最终预算缩小/源注入 | 范围标签与真实材料一致，固定政策不丢，成功最多1生成 |
| BV-01 | BV/AV/长链/短链/P2/重复形式/多视频/非法P/不支持域 | 只当前视频/P/cid，业务<=6 HTTP，无播放/音频下载 |
| BV-02 | 人工/自动/英文字幕；need_login/无字幕/404/403/412/429/错JSON | 单轨、明确错误，0认证重试/ASR/标题伪总结 |
| BV-03 | none/sessdata、跨域重定向、短链/字幕/DoH/模型请求 | Cookie仅固定api域API，无泄露；none不读凭据 |
| BV-04 | 时间乱序/重复/长字幕/6区覆盖/预算边界 | 时间与范围准确，未声称未读部分，片段真实可核对 |
| BV-05 | 缓存隔离/TTL/LRU/凭据变化/同P区别/取消共享/不同用户问题 | 命中减少提取，最终答案独立，重启不保留原文 |
| FW-01 | 实际AstrBot/provider/run_agent及CLI/Ollama底层替身组合 | 触发/最终manifest/失败0生成、成功1、来源/原问题历史/ACK正确 |
| FW-02 | mentions/free、黑名单、哑巴/真实@恢复、图/记忆/成员组合、停止/unknown | 新读取不绕过既有准入、租约、冻结目标或输出栅栏 |

真实B站材料批次先选用户允许的公开视频：人工字幕、自动/英文、P2/短链、无字幕/受限各有覆盖；每例明确0模型抓取预算，最多一个字幕，不试填未知Cookie。真实生成再单独对所选后端用已取得材料验证一次生成；人工核对至少3个要点能在实际送入的正文/字幕中定位，标题与正文不一致样本以正文为准。群ACK另指定一个真实@事件，来源与范围必须随最终输出；不为对照两路线自动各消费一次。

旧矩阵关系：V01/02/03/05/07/08/09/10/12/14/15/16/17/19按实际适用项补证；V04无字幕ASR、V06画面证据不足、V11多段合并、V13/18 ASR/多段资源与O10完整混合观察保留差额。单次字幕阶段、节选质量、真实完整总结不是同一验收结论。

## W9. 兼容与回滚

新bilibili缺字段默认false，现视频“不支持”分支仅在明确启用且触发符合W1时替换；其他平台仍原提示。新增字段进入LAP-34五文件映射/旧配置导出/配置版本与旁注，不退回要求用户用旧配置菜单。仅必要时保留菜单兼容测试，不恢复日常菜单工作流。

网络、正文提取、B站三部分可分别关闭/回退；真实启用由后续操作者执行。先正常关闭、保留pending/unknown/模型清理台账和完整成对备份，再恢复配对旧代码/兼容配置；不删除群记忆/图库/历史或凭据文件来“修复”。回system解析不改任何全局配置。已有任务18搜索、28容量、24登录、07 ASR和旧人体验收不因本计划自动完成。
