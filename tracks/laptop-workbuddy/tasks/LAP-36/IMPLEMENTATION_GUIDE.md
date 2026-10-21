# 交给sol medium的实施指引

返回[PROGRESS](../../../../PROGRESS.md) / [总计划](PLAN.md) / [图片合同](IMAGE_PLAN.md) / [网页/B站合同](WEB_VIDEO_PLAN.md) / [证据](EVIDENCE.md) / [HANDOFF](HANDOFF.md)。

## 1. 先读与执行边界

用户自行在会话设置选择gpt-6.1-sol/medium；本文件不检测/切换模型，也不自动启动实施。**每次只复制下方一个阶段给一个medium会话**，前一阶段交接后再推进下一阶段。若当前只授权代码与离线验证，不执行真实bot/模型/群验收；计划不等于真实调用许可。

每次从根AGENTS→PROGRESS→工作线HANDOFF→TASKS→本任务交接→对应专项合同读取。检查git status、相关diff、其他活动任务及进程操作归属；在原任务行登记阶段/session/开始时间/文件并重读。A/C续领LAP-28；B续领LAP-18；D首次领取LAP-06再创建它的HANDOFF并双向登记。LAP-36是本轮规划任务，不替代实施台账。

本规划证据基线main/b23d961；规划时「实施 LAP-24 自动启动」曾并行写process_host/manage/configure_bot/日志观察器及共享文档，现已738ca0a独立交付并确认36归属。不能覆盖、夹带或回退它，也不能把24的操作/171回归归本任务。config/persona.md原有用户差异保留。领取前以最新磁盘/提交为准，必要时协调共享文件/提交顺序；不批量commit所有变更。

默认只在临时根/假服务/自造夹具验证；真实公共网页可做有界零模型只读探测并单列证据，但不能改本机解析/CA/凭据以使其通过。真实模型/家庭SSH与QQ群操作需用户明确指定阶段、当前选中后端、样本、总生成上限和唯一执行者；失败/取消/unknown也算一次，不能自动重试/换后端/换批次绕过。

## 2. 阶段A：LAP-28入站观察代码

复制以下整段：

    你按gpt-6.1-sol/medium职责，仅实施LAP-28续作A：图片入站证据与诊断工具，先不做生产放行。项目E:\CodexWS\QQbot。
    先读AGENTS.md、PROGRESS.md、活动工作线HANDOFF和TASKS、原LAP-28 HANDOFF，以及tasks/LAP-36的PLAN.md、IMAGE_PLAN.md I1/I2/I3/I6、EVIDENCE.md、IMPLEMENTATION_GUIDE.md。
    登记LAP-28阶段A及文件归属、写后重读。先核对LAP-24并行代码与process_host/manage归属，不覆盖用户persona或其他任务。复用既有材料cap/准入/第一图/租约；补图片段到可解码bytes的分级诊断、封闭脱敏日志和默认inspect，以及明确授权后才可运行的intake-only工具。诊断真实模式必须require_stopped/受管身份，只运行项目NapCat/gate，0 AstrBot/模型/群输出；本次不运行该模式、不登录、不启停真实bot、不下载真实群图、不SSH、不用真实模型、不改本机配置/凭据。
    先完成URL路径；只有后续真实观察证明必要才按I3固定get_image分支实施，默认关闭。不得从file路径读盘、补拉历史或跳到第二图。只出现“[图片]”的反例不能当识图成功。
    做自造事件/图片、入口拒绝、占位反例、日志去敏、诊断超时/取消/自有进程回收、真实AstrBot路径适用回归。vision.enabled=false及production硬门槛不放松；历史323/900不能当本轮结果。报告分清代码/离线/真实材料状态，给阶段B/C解除条件。
    只交本任务代码/测试/文档，更新28 HANDOFF及进度；按AGENTS长期授权在审阅检查点commit/push并核对完整远端SHA，不自动继续18或真实验收。

出口：默认inspect/合成观察可重现“有段/无像素”“URL成功取得并解码”“纯文本占位”三类；无隐私输出，普通模式无副作用。真实NapCat样本尚未授权/取得时，状态仍ingress_unverified，不能写“收到真实群图片”。

## 3. 阶段B：LAP-18安全网络和正文提取

    你按gpt-6.1-sol/medium职责，仅续领LAP-18：安全公共网络与轻量网页正文。项目E:\CodexWS\QQbot。
    先读AGENTS/PROGRESS/工作线HANDOFF/TASKS、原18 HANDOFF和LAP-36 PLAN、WEB_VIDEO_PLAN W1/W2/W3/W5至W9、EVIDENCE、IMPLEMENTATION_GUIDE。登记文件/session并重读，保留28/24/用户persona所有归属差异。
    复用安全HTTP/一次模型队列/来源/ACK；抽出兼容public_http，增加项目内显式system或固定cloudflare_doh解析及默认无CA文件的严格信任配置，绝不接受私网地址、取消TLS或自动换解析提供方。现网络五域非公网和DoH TLS verify_code=20仍是未解决条件，不能靠浏览工具联网冒充本机可用。
    锁定readability-lxml==0.9及最小依赖，使用已受控下载的HTML本地提取；按需受管worker有字节/2秒/资源/取消回收约束，0浏览器/服务/模型分类。完成最终材料统一预算、六区节选/完整要求拒超限、来源/范围与真实@本地失败同链输出，不扩大触发。先不实现B站，不改28生产能力门槛。
    本次做代码/模板/文档与离线/真实框架替身；可以在临时参数下做少量无隐私公开页面零模型读取探测，记录上限/域名/状态，不改真实local/CA/代理/DNS/凭据，不SSH/启停/登录真实bot、不调用模型或发QQ。网络仍不通过则独立交付正文和诊断代码并标network_unverified。搜索质量另按原门槛核对，未过保持SEARCH_QUALITY_PASSED关闭，不能因页面成功就宣称联网搜索完成。
    验证SSRF/DoH/TLS/CA隔离、中文与文档提取质量、畸形/空壳/压缩上限、取消与worker退出、最终预算/manifest/模型次数/ACK及图/记忆/成员/哑巴组合。报告准确列分项完成与真实差额。
    更新18 HANDOFF/进度，按AGENTS仅提交归属文件并push/核对SHA。不要自动领取28C/06、改本机配置或启用功能。

出口：离线与提取质量合格；本机PublicHTTP真实TLS/公网/正文分别有证据或清楚标未验。现有web.enabled保存值不变，正常启动加载前不称已部署。新增依赖体积/时间/RSS实测列明，不只报测试数量。

## 4. 阶段C：LAP-28质量、容量及派生门槛

    你按gpt-6.1-sol/medium职责，仅续领LAP-28阶段C：原生图片质量/容量验证工具及可审计生产门槛代码。项目E:\CodexWS\QQbot。
    按入口读取AGENTS/PROGRESS/工作线HANDOFF/TASKS、原28最新交接、18最新交接、LAP-36 PLAN/IMAGE_PLAN全部/EVIDENCE/本指引。登记本阶段文件/session并重读。
    保留原gate唯一材料/一次cap/第一图/sideband/预算/TTL/租约/工具隔离；复用18最终安全传输，不重做网络栈。把当前恒拒启改为I4条件全部成立才派生可用的验证器；初始未验证组合仍拒启，默认vision=false。审阅能力记录必须对应实际选定runtime/model/平台处理路径，不拿Mac MLX公式替Windows/NVIDIA GGUF，不把4096、图样成功、API有vision或模型自述当可信上界。CLI所选模型无视觉支持就明确不支持，不换模型。
    按I5补固定批次/总次数/逐例原子预占及质量评分：失败/取消/unknown也消耗，重复case不能换trace重试。自造随机文字/图形/截图/同尺寸异图/最大图/注入六例，内容真值不进提示；两runner原生payload和最终system/文字/视觉/wire预算都有离线证据。
    本次只做代码/审阅来源/本地自造夹具/底层替身，不默认执行真实模型/家庭SSH/群图下载/QQ/登录/启停/本机配置修改。若用户另附明确选定后端与6次总生成授权，才运行一套真实IQ观察；不能自动两路线各跑。真实群ACK另批授权。没有可信视觉/模板上界时，完成工具与缺项诊断并回sol/max规划，绝不手写eligible或放松预算。
    更新28交接的分级证据与报告，保留旧31B/18/24等差额；按长期授权只提交本阶段归属文件并push/核对SHA，不自动启用vision/进入06。

出口：有明确production_eligible推导实现与缺项诊断；真实样本/容量未过则拒启仍正确。真正启用需所选组合材料/质量/可信预算都通过并由操作者停机审阅配置后启动，不能在验收脚本里自动把vision.enabled写true。

## 5. 阶段D：LAP-06轻量B站字幕总结

    你按gpt-6.1-sol/medium职责，仅领取LAP-06轻量B站字幕总结。项目E:\CodexWS\QQbot。
    先读AGENTS/PROGRESS/工作线HANDOFF/TASKS、18最新交接、LAP-36 PLAN/WEB_VIDEO_PLAN全部/EVIDENCE/本指引及原ACCEPTANCE的V矩阵。领取06并首次建立任务HANDOFF/双向链接，记录本session/时间/文件；保留07 ASR和完整V11差额。
    复用18受控公共传输与同一生成/预算/ACK管道。按固定yt-dlp提交只复用最小字幕元数据/字段片段并保留Unlicense/来源/修改记录，禁止直接装第三方AstrBot总结插件、整套extract_info/下载器或另接模型API。实现当前文字BV/AV/长短链/单P、单轨人工/自动语言优先、严格API/CDN用途与Cookie隔离、6次HTTP/15秒/1MiB等限额、确定性六区节选与真实范围、RAM有界缓存。无字幕/受限/多视频/超长明确失败，0ASR/视频音频/评论/弹幕/封面/平台AI摘要。
    独立bilibili.enabled=false/trigger=explicit，free裸链接不自动总结；只有真实@单定位或当前目标明确总结请求。禁止补拉引用/转发/QQ卡片历史。凭据默认none，不读浏览器，SESSDATA只有操作者本机明确提供才按固定私有路径/固定API域使用，不在本次填写/登录。
    本次代码/模板/文档与离线/实际框架替身交付，不改真实local/凭据，不启停/登录/SSH/调用真实模型/QQ。可用用户允许的公开样本做有界零模型字幕读取时，单列anonymous/auth/正文材料状态；缺网络或登录只记录限制，不绕过/重试。真实生成与群ACK另有明确样本/后端/总次数/负责人后再做。
    按W8验证多P/短链SSRF、认证泄露、正文与标题矛盾、单次生成、来源/范围/最终预算、缓存/取消、黑名单/哑巴/unknown和两runner底层替身。轻量节选不冒充V11完整多段总结，完整第一版仍未完成。
    更新06 HANDOFF/报告/进度，按长期授权只提交归属修改并push/核对远端完整SHA；不自动开启本机bilibili或推进07。

## 6. 验证命令、真实批次与报告格式

以下是实施方应维护的验证方式，不是本轮已经运行的测试，也不是要求现在运行真实命令：

    # 根目录；先选相关影响集，新模块名以实际实现为准
    .venv/Scripts/python.exe -X utf8 -m unittest discover -s tests
    # 每任务新增独立verify脚本/报告；实际AstrBot环境使用仓库既有框架Python
    # 不直接重跑会覆盖旧报告的verify main；先检查输出路径与零真实传输约束
    git diff --check
    runtime/tools/uv.exe lock --check

本轮不为只改规划跑代码测试。medium首次相关影响集通过后，只有新改动/失败/未决风险才扩大或重复验证；不要靠重复全套测试制造“质量已通过”。源码/框架/底层替身/真实模型/真实群验收分列。

真实批次必须先写入对应HANDOFF：唯一负责人、所选已保存后端、当前模型/能力绑定、公开或自造样本、网络/模型/群输出各自总上限、是否允许受管启停、终止条件。示例预算分别为：入站1自造事件/0模型/0群输出；IQ六例/合计6次所选后端生成/0群输出；公共正文/字幕若干固定样本/0生成；群验收1授权事件/最多1生成/1最终输出。不能将这些例子当成本轮已授予的调用许可。

每份实施报告至少写：变更文件归属、行为/配置与加载方式、离线命令及结果、真实材料/生成/群ACK各自状态、实际调用计数、依赖/时间/RSS、未验证及失败分支、回滚、提交/远端SHA和仍保留的本机差异。不要提交凭据、本机运行配置、原始群图/消息/字幕/网页或真实模型回答。

验收不达标仍应交付已完成独立部分与具体缺口；未改变方案的一般适配/解析问题自行修复，涉及新提供方/浏览器/ASR/不同模型或放松准入/预算则回规划。不得删除旧差额或把“能调用API”写成“完整验收通过”。
