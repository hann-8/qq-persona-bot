# 下一轮medium：Snow既有功能实际落地

返回[PROGRESS](../../../../PROGRESS.md) / [交接](HANDOFF.md) / [详细PLAN](PLAN.md)。

用户在会话设置中选择gpt-6.1-sol/medium，再发送以下整段。当前规划没有实施；下列授权仅在用户把它作为下一轮指令发送时生效。

```text
在 E:/CodexWS/QQbot_Snowluma、codex/lap-40-snowluma，用用户已选的gpt-6.1-sol/medium实际落地LAP-42。不要派代理/切模型，不要再只交计划。本轮只领42这个Snow既有功能整合任务，不并领27/28/29/30等旧任务；旧实现/真实差额保留。

先重新核对Git根、HEAD、实时远端、工作区/负责人。规划起点9bb1b58270dbcaa3c5e40c53f804d5e50c54449b，文档交付提交在其后，不回退/强推/覆盖并行修改。按PROGRESS → AGENTS → 工作线HANDOFF/TASKS → tasks/LAP-42/HANDOFF.md/PLAN.md/MEDIUM_START.md → docs/BOT_USAGE_COMPARISON.md读；原功能合同只按具体项补读。

用户最新目标：长期群记忆、关注增强、成员增强落地，尝试图片内容识别，撤下B站字幕。用户已明确当前deepseek-v4.1-flash支持视觉；保持当前CodeBuddy/model/low/账号/额度，重点验证QQ图片的实际像素是否经CLI进入该模型并同次返回，不以“文本模型不支持”为前提转Ollama。官方Snow只是现成接入，共用业务复用，不改Snow/QQ/CLI发行包、SDK全局对象或其他封装内部。

修改前登记本session、Asia/Shanghai时间、精确文件及唯一真实实例执行归属，写后重读；保存本机配置/persona/图库/pending保护摘要。按PLAN S0—S5实际做，某项受阻不拖住可独立项：
1. 复用MemoryStore与attention/v2，目标memory.enabled=true、learning_enabled=true、participation.attention.enabled=true。保留配额、别名/焦点/队列/free频率，从新消息学习，本根独立HMAC key；不迁旧history/记忆/秘密，不加summary/embedding/classifier。silent入站与文字ACK承诺分开；缺key/损坏/purge不得删库强解。当前persona组合预算离线核对但不输出正文、不抬预算。
2. 真正撤下B站运行服务/入口/能力提示，不再构造Subtitles/抓字幕/读SESSDATA/做ASR，普通web读取保留。旧bilibili=false节兼容，不必改原字节；true不能重启退役服务。专用源码/测试先清引用再删，不删共用网络/材料schema或旧报告；不是把false再写一次就算完成。
3. 成员不能只改开关。按PLAN第4节补项目外部Snow强刷观察：get_group_info(no_cache=true)已审阅为await本次FetchGroupList网络结果，失败不回旧缓存；名单no_cache=true走force。gate内部绑定请求时间窗/连接/指定群，不接受模型字段伪造freshness，不简单received_at改age=0。保留1..49、60/300秒双TTL、8项/768字节候选、单cap及最多1受控@；不每条强刷、不重试。统一gate/router/gateway/configure_astrbot/配置保存的effective members，旧NapCat/未知版本仍暂停。独立context token与只开members的唯一性检查补齐。通过后members.enabled/mentions_enabled=true；大群/来源无效只暂停增强，普通文字继续。
4. 按QQ新消息→Snow OneBot→第一图像素→当前CLI原生文字+图片输入→DeepSeek理解→原router/typed投递ACK回群推进。已有cli_message/stream-json/base64复用，核对实际MIME/像素hash/同次调用返回，修项目接点、不改CLI/Snow内部。JPEG/PNG/WEBP/GIF自定义表情以真实image像素处理，GIF只首帧；face ID/无图/文件名不得假装看见。opaque ID确需get_image时，只做来源于本条cap/当前连接的一次固定读取，不读QQ/Snow缓存或历史。
5. 旧intake固定拉NapCat，不能在Snow根照搬真实运行；只在项目manage/observer补所需Snow单图采样适配。视觉支持用户已确认，但实际传图/预算/质量仍要验。按当前托管CLI元数据/传输契约补可信依据，不伪造远端processor/projector或eligible，不套家庭GGUF要求；原预算/质量门槛不放宽。缺必要项则先交取图/CLI适配与精确缺口，vision留false，其他功能继续实际交付。
6. 定向用现有test_lap30/test_lap27/test_lap29及视觉单元、实际AstrBot原event/runner底层替身，补新成员观察/token/字幕退役/原生像素/组合预算检查。重点当前CodeBuddy+free+adaptive+web+memes组合；不跑全部旧矩阵或覆盖旧report writer，不读验A4，不手填成功metadata。

本消息在本轮明确授权：
- 上述外部业务代码、离线夹具/测试、备份/候选、指定开关及本根独立记忆key/context token。保留其余local/persona、模型参数/账号/额度/free/web/memes及冷却0/0。字段级补丁、原字节备份、双摘要/停机配置锁，不拿模板重建整个配置。
- 代码/离线/候选检查通过后，由唯一session至多两次受管加载周期：先可用功能一次，视觉后来符合条件再一次。只用新根既有管理器处理有创建身份依据的项目组件，外部/手工QQ/Snow不接管，不按进程名批量杀；若需扫码/密码/安装则停该步交操作者，不擅自登录/重装，不删state/lock/清理台账强启。
- 正常恢复当前free后，授权群新消息会按既有业务消耗原额度并答群；自然流量单列，不能声称全程0真实调用/0群输出。不重放旧消息、不定时制造话题。
- 成员只读限当前授权群及固定RPC/TTL，无群管理/收藏。人工群测试消息由操作者发，agent不代发；多个授权群且受测对象未明时不自行挑群测试，独立代码/加载继续。
- 允许现选模型固定IQ-01..06原生批次，总最多6次、每case一次，失败/取消/unknown耗次不洗批，前置输入/预算条件必须满足。QQ取图限120秒/1条指定操作者自造图，该样本0模型/0bot输出；随后明确对象的群图片闭环最多2次生成。缺受测group/sender或人工审阅时只保留该真实环节待验，继续独立部分；agent不得代发群测试消息。
- 不授权Snow/QQ/CLI内部或全局WorkBuddy修改、旧E/旧C/家庭SSH、模型/后端/账号/额度切换、付费API、额外caption/OCR/summary模型、任意媒体、无限试验/重试/旁路裸发。B/C停止，A4代码/产物/证据原样保留不读不验。

启用目标：记忆读取/学习、关注开启；成员/受控@在外部适配通过后开启；视觉在当前路径入站/原生输入/预算/质量符合合同后才开，不写true卡死整个bot。新装模板仍默认false。21已有7图/pending数据准备，不复做图库、不激活/删除其他任务pending、不拿表情尾项阻塞42。

阶段完成即同步42交接/TASKS，逐项区分代码/离线/配置保存/运行加载/真实通过。记忆“记住了”不是已持久化证据，图片编码/模拟ACK不是QQ识图通过，GIF首帧不是完整动画理解。真实原生调用、自然流量、群ACK/客户端显示分别记。遇到需改内部、换后端/额度、加模型或放宽门槛的真实阻断，先完成独立部分，再以具体证据回规划，不自行扩大。

回滚按停机锁及本任务摘要撤回拥有字段/配对代码，保留并行修改与记忆key/库、purge、ACK/pending/unknown/清理台账及21 pending；不删数据/锁、不重建key、不git reset/clean。旧代码不能理解新状态时保持该能力关闭。

交付reports/lap-42-*和实际结果，更新PROGRESS、工作线HANDOFF/TASKS、42交接及使用对照。图库/标签/记忆/名册/秘密/local/persona/原始消息/观察工件不提交。沿用长期Git授权，只commit/push本任务已检查文件到原分支并核对完整远端SHA，报告保留差异。完成42后释放归属并停止，不扩微信/长稳/字幕新功能。
```
