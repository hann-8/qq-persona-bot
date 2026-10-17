# LAP-19追加合同：自由群聊、真实@必答与表情包

返回[PROGRESS](../../../../PROGRESS.md) / [总体计划](PLAN.md) / [本任务HANDOFF](HANDOFF.md) / [执行指引](IMPLEMENTATION_GUIDE.md) / [TASKS](../../TASKS.md)。2026-10-17，Asia/Shanghai；**仅详细规划，未改运行代码/配置/人设，未登录/启停/调用模型或发送QQ消息**。

用户本轮追加：不再仅靠@触发，像真人一样自由参与已授权群聊天；真实@必须回应，答复直接群发、不引用原消息；复用现有黑名单；可发送表情包，优先兼容QQ已收藏，也提供本地文件夹；额度由用户后续自行观察。该需求明确覆盖总体计划初稿“未@参与另规划”的旧状态，实施拆为LAP-20和LAP-21，不给本轮部署/群发授权。

## 1. 范围、证据与黑名单准确边界

### 1.1 当前代码事实

| 证据 | 当前行为 | 后续动作 |
| --- | --- | --- |
| `onebot_gate.py:admitted_message/_incoming` | 先检查账号/授权群/blocked_users/自身，再要求结构化真实at，之后才DedupStore.reserve及转发 | 保留前半过滤；free模式允许非@消息进入受控观察，mentions模式仍保留旧合同 |
| `plugins/qq_router/main.py:on_group` | 框架入口再次检查群/发送者/黑名单/真实@；以event.unified_msg_origin维护本人持久历史 | free分支使用独立群窗口；不把多人正文拼进旧个人会话 |
| `reply_delivery.py:ReplyDelivery.send` | adaptive第一条硬插Reply；`configure_astrbot.py`设置reply_with_quote=true | 两处都调整，single/adaptive/free/错误提示统一直接群发，不靠只改UI开关 |
| `task_store.py` | 文本逐条ACK/恢复，保存before/expected历史用于修复 | 群窗口需新的历史目标；表情需类型化发送部件，不能仅拼成文本绕过账本 |
| AstrBot本机`astr_message_event.py:request_llm`、`astr_main_agent.py`显式provider_request分支、`internal.py:_save_to_history` | 提供contexts、system_prompt、conversation=None可构造无持久conversation的请求；无conversation时跳过保存 | free可用RAM群窗口；此为源码证据，必须以实际框架合成测试验证默认路径不会补建个人会话 |
| 本机`napcat.mjs`的FetchCustomFace/FetchCustomFaceDetail | count默认48；前者把emojiInfoList映射成URL列表，后者返回详细列表 | 可规划QQ收藏导入；当前gate不放行这些动作，也未实测本账号2个收藏 |

**现有黑名单确实在项目入口阻止被屏蔽者的直接群消息进入AstrBot、模型和新增历史，可复用。** QQ/NapCat底层仍接收事件，不能承诺QQ客户端本身看不见；其他群友重新打字/转述的文字不能可靠按原作者识别。本轮未读取真实群消息验证，只核对实现与已有合成测试。

free分支仍在黑名单判断之后进行序列分配、去重、缓存、合批、检索和模型调用。引用/转发中的内嵌正文不得绕过：忽略原始raw_message、JSON/XML/合并转发正文和Reply.chain；只可从本项目已过滤的当前RAM窗口解析引用ID。目标未知/已过期/被屏蔽时保留“引用未解析”而不拉QQ历史。`get_msg/get_group_msg_history/get_forward_msg`继续不开放；不使用QQ客户端拉黑替代入口规则。

### 1.2 行为优先级与非目标

优先级为：账号/群授权及黑名单→停止/失联→真实@必答队列→自由参与决策→发送前复核。黑名单中的人即使@也保持屏蔽；@all、昵称文字、伪CQ片段不算强制@，但在free模式下可作为普通聊天内容。

“@必答”指不受沉默判断、自发冷却或频率上限丢弃；每条去重后的合规@有一次回应机会。空@、不支持的图片问题可本地说明；后端/额度/连接故障或队列满给短本地状态提示，不能承诺网络故障时仍有完整模型回答或QQ必达。重复投递同一消息只处理一次。

非目标：私聊/未授权群、定时冷场冒泡、无新消息的后台轮询推理、群管理/私信/代发文件、识图/视频理解、抓取其他人表情或群历史、真人身份冒充、无限制多代理/工具。自由参与是授权群新消息驱动，不安装定时任务；既有工具隔离、单次尝试与无自动换模型保持。

## 2. LAP-20自由群聊的状态与调度

### 2.1 模式、上下文与生命周期

`participation.mode=mentions|free`，缺失仍mentions，以保证升级不悄悄读入未@消息。配置cmd由操作者显式选free时，对当前access.allowed_groups生效；新增授权群仍通过既有配置入口，不能由模型或群消息加入。模式、后端、模型/人设/生成协议变化开启新epoch，运行中不热改访问控制。

mentions保持原本人会话合同，free使用`(bot, group, epoch)`独立RAM窗口。窗口只保留启动后准入的群消息、时间/单群别名和ACK确认的bot输出，默认最近60条/15分钟/32768 UTF-8字节，任一超限淘汰最早项。重启/断开登录/模式切换清空RAM，不回拉QQ群历史；旧本人持久历史保留，但**不导入free群窗口**，避免把原个人上下文公开给全群。

每条规范化记录含本地seq、可信消息ID/发送者身份（只供代码）、去控制字符显示名、模型使用的单群短别名、文本/非文本占位、时间。真实QQ号不必进入prompt；显示名/正文都是不可信数据。只取当前群，不跨群或跨epoch；框架全局group_icl/group_message_history/active_reply仍关闭，由项目这一处受控窗口管理。

当前版本先看文字：图片/GIF/音频/视频只记录“图片未解析”等占位，不下载、不识图、不让文件名/图片URL成为搜索查询。纯媒体非@不单独触发推理；@携媒体无文字则给当前能力说明，不伪称看过。发送表情能力不代表能理解收到的表情。

### 2.2 每个新事件如何处理

1. gate与router双重准入，blocked/self/private/未授权群/非法结构先丢弃；观察事件也去重，同一个消息不重复开窗口或计费。
2. 符合重置指令的管理员真实@按本地分支处理；非@普通文字“重置”不能清空群上下文。free新增“重置本群上下文”，只给已配置管理员、明确真实@；mentions原本人重置保留。
3. free新文字先入RAM。非@按2秒去抖合批，距第一条最多5秒，持续刷屏也会结算；每群只有一个待选批次，不按每条消息各排一个模型任务。
4. 自发决策距上次评估至少5秒；每群每分钟最多12次ambient评估。新消息仍缓存，超限只合并/推迟本轮，不发“限流”刷群提示。没有新消息不再次评估，silent不触发下一轮。
5. 每个候选都允许模型决定“说/不说”，不要求命中特定关键词/昵称，不预设掷骰概率；结合自然话题、是否有内容可补、是否打扰他人聊天。一个批次只生成一次，分类与正文在同一结果中完成。
6. 非@发言之间默认至少15秒、每分钟至多4次**发言轮次**；有限气泡/一张表情同属一轮。此为防刷屏的可调起点，不是额度自动策略；@绕过这两个限制。
7. 每条真实@独立登记必答ticket，取消尚未启动的ambient候选并优先排队；不同消息ID的@不默默合成一个可能漏答的结果。已开始的ambient生成不重发/强杀另起模型；完成后若@在等待就丢弃该ambient发言，再处理@。
8. 全局仍单并发；新增队列元数据与优先级，@优先、ambient按群轮转，每群至多一个未开始ambient槽。每群@等待槽默认8，全局仍受有界队列限制；队列满/到期的@立即给一次本地忙碌提示，不静默丢弃。
9. 新消息在生成期间进入下一窗口；当次只看不可变snapshot。非@输出超过默认90秒有效期、epoch变化、群/发送者权限不再有效或已stop，不发送旧结果；不为“换个更合时宜的回复”再次调用模型。
10. 最终发群前再核对实例/epoch/授权/黑名单、必答状态与发送账本。bot自身回显不触发新评估，自发发言失败不发送第二条错误消息。

如果实际框架以原event.unified_msg_origin加个人锁，项目群协调器必须覆盖多用户并发：同一群共享快照/提交序列并共用发送队列；不能仅依赖原个人锁。长时间持有的待选event有TTL/身份依据，连接变化立即作废；未取得发送授权的框架默认结果全部吞掉。

## 3. 群聊生成协议、框架集成与历史

### 3.1 一次决策与一次生成

free请求使用新的内部结构，与现有`qqbot_reply:1`兼容分支分开：

```json
{"qqbot_group_reply":1,"decision":"speak","kind":"chat","bubbles":["这段我站鱼片这边"],"meme_id":null}
```

silent严格为decision=silent、bubbles=[]、meme_id=null；speak为chat/answer，文本限额沿用output，kind=answer仍单条。无需reason/思考过程。LAP-20的meme_id只允许null，为21留兼容点；`output.delivery_mode=single`时把合法闲聊内容合为单条，adaptive才有限气泡，但两者都允许内部silent。

真实@的可信请求标记must_reply=true，不能由模型改成false。若返回silent/非法格式/空白，给一次本地“这条没接住，请再说一次”类状态回应，不再生成；不能把这一失败当模型完整答复质量通过。非@非法输出静默，计protocol_error，不把内部JSON或错误解释发群。

所有决策由当前显式选择的后端完成，CLI不偷偷用本地模型筛选，反之亦然。silent仍可能消耗真实额度；usage按trigger=mention/ambient、decision=speak/silent/error分别统计，不能仅用群里发出的消息条数估计成本。此次用户决定自行观察额度，不增加自动阈值/额度不足切换或强制更便宜模型。

### 3.2 可信请求与返回合同

网关当前只接受model/messages/stream，LAP-20增加严格的`qqbot_request`白名单：version=1、kind=group_turn、trigger、must_reply、epoch、snapshot_digest和本地request_key。由已认证router根据真实OneBot事件产生，模型不能从用户正文伪造这些字段；原mentions请求无此字段继续兼容。group/事件实际ID留代码元数据，不让模型自由决定发送目标。

网关解析内部群协议并返回受限`qqbot_group_plan`元数据，正文只含可显示文本/受控silent占位。router在on_agent_done和on_decorating_result中校验原响应ID、plan hash、epoch、request_key，所有group_turn都由统一ReplyDelivery接管，不能只在adaptive接管。silent的结果/内部占位必须在发送和历史前被吞掉。

实际SDK对空content/额外字段的行为须先用合成provider验证；若需要非空内部占位，则加事件级发送防护，未经ReplyDelivery授予的结果不能发出，包括框架异常路径直接event.send。不得通过裸HTTP旁路群发或改AstrBot全局对象解决；这是LAP-20的离线能力门槛，未验证前不能进入真实群。

### 3.3 RAM群上下文与ACK历史

free使用`event.request_llm(prompt=序列化群snapshot, contexts=[], system_prompt=共用政策+人设, conversation=None, tool_set=None)`。本机源码显式provider_request分支不会自行补conversation，保存函数对无conversation直接返回；实施必须以实际框架合成追踪证明，不依赖猜测。不要切AstrBot全局unique_session来混并旧个人历史。

群snapshot是带说话者标记的user数据；所有准入人类消息已在RAM窗口内，不能逐条假扮assistant。原始group snapshot不进入个人conversation，不放进持久发送账本的before/expected或日志。新增群投递历史目标，只持久化snapshot hash/seq范围、响应ID、bot准备部件和逐条ACK；RAM只有ACK确认的bot输出可追加为bot记录，未发出的生成不成为“我已说过”。

重启恢复时group RAM丢弃，未完成投递标为unknown/aborted，不回放旧话题、不重发未知图片/文字。原mentions的before/expected修复与quarantine合同保留。未知ACK时暂停本群自发发言并保留本机检查状态，真实@给一次简短本地状态说明，操作者核对解除；不能当成功后继续接龙。

## 4. 联网与自由聊天的组合

复用LAP-18的有界检索；自由观察不会把整个群窗口上传搜索站点。每批至多选择一条具有明确对象的最新查找/时效问题或公共网页请求作为anchor，查询只从该条规范化文本形成；其他群成员的闲聊/历史不外发。模糊指代时不拼整个群历史“让搜索引擎理解”。

`web.enabled=true`且`participation.allow_ambient_web=true`时，ambient候选可以按同样规则先检索再在一次模型生成中决定说/不说，因此silent也可能有一次搜索消耗。普通闲聊、仅提到价格/日期但不是查询、非文本、禁止联网的本条都不搜索；不为了找话题主动搜索。若未取得实时证据，模型不得编造新近事实，可沉默或说明未核验。

@的检索全部失败仍给本地简短说明；ambient检索全失败静默并记录计数。成功的联网发言仍为单条answer/完整来源，默认不加表情。当前批存在多条不同人查找请求时，优先必答@，其余不声称同时解答；不会为一批开展多轮自主研究。

## 5. LAP-20配置、默认值与生效

下列字段在schema3扩展，1/2经17迁移后读取仍保持mentions；所有改动停机保存/重启生效。菜单显示“自由参与会读取授权群新消息，并可能在未发言时消耗模型额度”；人设政策由配置驱动，同时更新configure_astrbot/router，共用compose不盲改角色正文。

| 字段 | 缺省/范围 | 合同 |
| --- | --- | --- |
| `participation.mode` | mentions；mentions/free | free对access.allowed_groups生效，@始终优先；最终试用由操作者显式启用 |
| `.debounce_seconds` / `.max_batch_wait_seconds` | 2/5；0.5..5 / 2..10，后者>=前者 | 新消息事件内短合批，不是定时主动任务 |
| `.min_evaluation_interval_seconds` | 5；1..30 | 仅ambient，@绕过 |
| `.max_evaluations_per_minute` | 12；1..60 | 每群ambient推理起点；silent计入，@不计此上限 |
| `.unsolicited_cooldown_seconds` | 15；0..120 | 每群非@发言轮次间隔 |
| `.max_unsolicited_per_minute` | 4；1..20 | 一轮多气泡/表情只算一轮；@绕过 |
| `.context_messages` / `.context_ttl_seconds` | 60/900；10..200 / 60..3600 | 群RAM窗口双限 |
| `.context_max_bytes` | 32768；4096..131072 | 缓存限额；投喂还须按当前后端输入预算裁剪 |
| `.message_max_chars` | 2000；200..4000 | 群观察每条有界；@原问题超限仍走明确错误，不静默截断后回答 |
| `.mention_queue_limit` | 8；1..32 | 每群待答@；超限本地回应，不漏无声 |
| `.max_ambient_age_seconds` | 90；10..180 | 自发回复过期不发；不能反复生成以保鲜 |
| `.allow_ambient_web` | true | 仅free且web.enabled时生效，不新增后台搜索 |
| `output.quote_reply` | false；首版仅false | 用户本次要求所有模式直接群发，Reply/自动@关闭 |

频率是可调的防刷屏起点；没有random概率门、关键词唯一触发或额度自动降档。@可以超过自发频率，但仍受授权、停止、技术排队和传输限制。菜单提供mode与“自由参与活跃度”高级参数，保留每项单位/范围，不把5秒说成每条消息都只收费一次。

## 6. LAP-21表情包来源与配置入口

### 6.1 确定方案：QQ收藏可导入，本地图库统一发送

支持两种来源，统一进入本机受控图库，避免运行时依赖过期QQ URL：

1. 配置cmd“表情包→从机器人QQ收藏导入”，读取机器人账号的收藏列表/详细列表，导入文件并让操作者填简短名称/情绪标签。用户已有2个收藏为用户说明，本轮不查询或验证它们；不要求用户先手工把这2个另存为文件。后续在QQ继续收藏后，按需再次导入，不自动监控账号全部收藏。
2. 本地入口拟为`E:\CodexWS\QQbot\assets\memes\inbox`，实施时创建并在配置cmd提供“打开文件夹/扫描本地表情”。可放PNG/JPEG/WEBP/GIF；扫描后进入`assets/memes/library`及本机忽略的`config/memes.local.yaml`目录表。角色说明/模板README可以跟踪，用户图片/标签/QQ来源信息保持忽略。

二者都能用；QQ收藏读取仍需机器人账号在本项目NapCat可用，导入按钮是显式本机管理动作，不让模型调用。若本地API/账户不支持，保留本地文件夹能力并报告QQ导入未验/未完成，不能说收藏已经可发或要求读取日常QQ密码/修改收藏。

### 6.2 最小管理通路，不放开账号工具

现有gate不允许fetch_custom_face。新增**固定用途**回环管理端点`POST /admin/memes/favorites`，使用项目独立本机管理token，和模型bearer/OneBot token分开；只允许count=1..48、一次固定收藏读取，不接任意action/user/group/URL。gate在已验证的当前机器人连接上关联独立echo，内部处理结果，不把收藏URL交给AstrBot或模型。默认使用已在本机静态包确认的fetch_custom_face_detail；若仅基础接口可用，菜单显式选择基础读取，不悄悄循环重试。

不向框架通用allowed_action加入所有收藏/账号动作。add_custom_face/delete_custom_face/set_custom_face_desc、get_credentials/get_cookies/get_clientkey和群历史继续禁止；只导入不改QQ收藏。连接不存在/未登录直接提示，禁止为导入启动/登录QQ。管理端点只在已运行的gate处理当前连接，不单独重启机器人。

导入客户端只接受该固定收藏RPC产生的公开QQ媒体URL，域名/重定向/全局IP/TLS逐项校验，禁止用户或模型任意URL下载；实际媒体域名须实现时以官方/当前响应证据建立白名单。不可用时不自动扩大通配域或绕过鉴权。rkey/临时URL只在导入进程内，日志/目录表不保存完整签名URL；不借日常浏览器Cookie下载。一次最多48项，每项<=8MiB，总导入<=128MiB、总期限60秒，逐项有界/可取消，不重试失败项。

这是本机管理功能，不是聊天模型工具；读取收藏不消耗模型额度，但后续接收/下载与发送能力都要单独验收。本轮没有调用该接口/创建管理token/下载用户表情。

### 6.3 图库与语义目录

文件先验证真实类型/尺寸/动画限制，再按SHA256去重入库；禁止目录穿越、链接/junction越界、扩展名伪装和可执行/SVG/HTML。初始最大4096×4096、总像素16M，GIF最多120帧、累计解码像素128M；验证库需在项目锁定依赖，不自动转格式/裁剪用户原图。

稳定meme_id绑定文件hash，目录项含id/显示名/简短使用语境/tags/enabled/相对文件名/sha256/media_type。QQ详情里有说明可预填，无说明就让操作者填标签；未命名/未确认的图片默认不进入模型候选。不加视觉模型自动识图，不把原QQ URL、绝对路径或图片base64发给文本模型。

模型每次只看当前可用候选的ID/名称/标签（最多16项、总<=2000 UTF-8字节）；候选可用本地标签匹配选择，非第二次模型检索。标签都是材料不能覆盖系统规则；每次完整输入仍受当前profile预算控制，优先保留当前问题，图库为空时正常纯文字。

### 6.4 选择与发送协议

在20的group协议中允许`meme_id`是本次候选之一，或null。mentions且memes.enabled=true时采用明确的媒体回复封套：`{"qqbot_media_reply":1,"kind":"chat","bubbles":["笑出了声"],"meme_id":null}`；选图时将null替换成候选真实ID字符串。此模式没有silent/decision字段，@仍必答；memes关闭继续原v1纯文本合同。网关/router按可信模式选择解析器，不能在任意正文中搜JSON；对应`qqbot_request.kind=media_turn`由认证router添加，发送历史目标仍为本人conversation，不改成free的RAM群历史。

free与mentions/single/adaptive都只调用模型一次；内部媒体封套绝不发群。网关统一编译为带版本/hash/response_id的typed投递plan，兼容接收旧文本plan；模型只能选ID，代码映射到本地文件，模型不能给file/path/URL/base64/CQ或原生face ID。

默认每轮最多1张、总发送部件不超过output.max_bubbles（缺省3）；single最多1个文字部件加1张图，max_bubbles=1时文本优先。认真answer/代码/联网来源答复默认无图；日常可“短文字+图”或ambient仅图。真实@默认至少有文字回应，用户明确要求“发个表情”时可仅图；不能用无关图替代认真问题答案。单条纯文本只约束文字正文，允许本合同已登记表情图片段；图也计入总部件限额。

发送为OneBot image、本地file URI（NapCat仍在笔记本，PC只推理），不是发送文件附件、消息反应/戳一戳或随意远程图。GIF能否动画/以收藏样式显示须实测；API ACK不等于客户端显示质量，不能保证它与QQ收藏手点发送的所有属性相同。

表情冷却默认每群60秒，相同meme_id默认5分钟不复读；这些仅抑制附图，保留已生成文字，不再调用模型换图。明确请求某张表情可绕过普通图片冷却一次，但仍每轮1张/黑名单/去重/总发送限额。无效ID/文件缺失/未验证类型时丢弃图片，文本继续；仅图且无法发时@给一次本地说明，ambient静默。

## 7. 文字与图片共用发送账本

先将结果冻结为`PreparedPart(type=text|image, digest, payload_ref, semantic_label)`；image绑定已验证库文件hash，发送前再检查路径真实解析/hash，必要时复制到本轮忽略临时目录防止扫描/替换改变准备内容。日志不输出文件内容或QQ签名URL。

每个文字气泡/图片各是一个有顺序的发送部件，以原event与同一群队列发送、各有一次OneBot调用和关联ACK；不另开媒体旁路。配置reply_with_quote=false、reply_with_mention=false，代码不插Reply/At/AtAll。最终gate对send_group_msg/send_msg增加段级验证：仅本合同的text/image（图片只能受控库/本轮临时目录），拒绝任意文件路径/远程URL/forward/node/record/video/群管理；文本中的CQ字面量不能被当作图片指令执行。

账本存part_type/digest/media_ref/semantic_label、prepared/sending/sent/failed/unknown和message_id；同一消息ID重复ACK不代表第二张已发。文本成功图片失败时只保留确认文字；图片成功才向RAM群窗口记“bot发了表情：名称”，不把图片路径/字节当聊天正文。图片-only的内部canonical可为受控表情占位，但群里发送真实image，不能额外发一条假图片描述。

发送中stop/权限变化/断连即停止剩余部件，未知ACK不重发，重启恢复不重新生成/补图，不用QQ全历史查ACK。原mentions修复按已确认typed parts重建；free只更新当前epoch的RAM确认输出，恢复时不重新载入人类群文本。若不能在现有SDK中可靠关联图片ACK，先完成图库/导入及离线部分，保持真实发图关闭并报告能力缺口，不能用直接NapCat裸发跳过账本。

## 8. LAP-21配置和迁移

| `memes.*`字段 | 默认/范围 | 生效方式 |
| --- | --- | --- |
| `enabled` | false | 升级不自动发图；操作者显式启用，重启后生效 |
| `inbox_dir` / `library_dir` | assets/memes/inbox / assets/memes/library | 项目内真实路径，拒绝越界/链接；配置cmd打开文件夹 |
| `catalog_file` | config/memes.local.yaml | 本机忽略，原子保存/版本号，按停机配置锁激活；扫描/导入可准备暂存但运行中不替换活动目录表 |
| `max_candidates` / `catalog_prompt_max_bytes` | 16/2000；1..32 / 500..4000 | 只发文字标签，计入模型输入预算 |
| `max_images_per_turn` | 1，固定 | 计入总部件数，不额外模型调用 |
| `cooldown_seconds` / `same_meme_cooldown_seconds` | 60/300；0..600 / 0..3600 | 每群图片限制，普通文本照常 |
| `allow_meme_only` | true | 仅ambient闲聊/明确要图时；普通@问题需文字 |
| `max_file_bytes` / `import_count` | 8388608/48；1MiB..8MiB / 1..48 | 导入/扫描统一校验，不向模型开放 |

目录表版本/有效标签变化应更新能力hash；重启新epoch，未发送旧图不继续发。raw图片和本机catalog从首次创建前加入.gitignore；只提交示例目录表、README、代码/合成测试资源。测试图片必须是自造的最小无私人内容夹具，不复制用户QQ表情进测试/Git。旧无memes字段继续纯文字，LAP-16 v1协议继续兼容mentions。

## 9. 实施文件、顺序与验收

| 任务 | 文件范围 | 顺序/依赖 |
| --- | --- | --- |
| LAP-20 | gate/config/strict router；新增group_context/participation/群协议模块；model_gateway/contracts/queue；persona统一能力版本；configure_astrbot/configure_bot；reply_delivery/task_store与框架验证脚本/README | 先17后18的共用合同稳定；①新模式/准入 ②RAM上下文与合批/@优先 ③一次决策与可信元数据 ④无conversation框架门槛 ⑤直接群发/ACK与停止 ⑥离线/实际框架验证 ⑦另授权真实启用 |
| LAP-21 | 新增meme_catalog/导入器；固定gate管理RPC/token管理；config/menu/CLI目录入口；群/mentions回复协议；typed投递/账本/恢复；.gitignore/README/合成图片测试 | 20已实现离线通过；①受控库与本地文件入口 ②QQ收藏只读导入 ③候选ID/一次选择 ④typed parts/ACK/直接群发 ⑤反例/恢复/两后端离线 ⑥另授权QQ导入/真实发图 |

两任务分别领取/建HANDOFF/登记文件归属；不与17/18同时写同一共享文件或操作同一bot。需求不再叫“未@另规划”，但实施仍须后续指令；不删除旧验收差额。

### 9.1 离线必须通过

- mentions旧真实@/无@静默兼容；free非@可以speak/silent，@不走沉默/冷却；黑名单含管理员/@反例都先丢弃，0窗口/历史/HTTP/模型/表情；引用/转发不补读被屏蔽历史。
- 同群多人合批不串个人历史，跨群/跨epoch隔离；同ID去重；持续刷屏最大等待/内存/队列有界，@优先且不因自发限流无声丢失；没有新消息0周期模型/搜索。
- 假时钟覆盖silent不再评估、@到来取消待选、生成中插入新消息、旧话题过期、不读旧个人会话；实际框架prove contexts/无conversation、silent/异常所有发送路径拦截、single/adaptive直发无Reply/At。
- 输入预算包括群snapshot/图库/检索及封套，坏格式/模型tool事件/原始CQ/昵称指令不能开放动作；每批至多一次生成，两后端都测，usage计silent不计发送。
- 目录穿越/junction/hash变化/格式/大小/帧数/候选ID篡改、空图库、QQ接口失败/未登录、过期URL/非白名单跳转/取消导入；不读账号凭据接口、不改QQ收藏。
- 真实SDK合成图片链/图片only/文字后图失败/未知ACK/重复回执/stop与重启恢复、发送canonical与已确认历史一致；所有发图经统一gate/账本，无裸API旁路。

### 9.2 真实验收分开记录，当前均未做

先用户明确受测群/模式/执行session/时段/后端/调用上限，再启动既有项目实例。离群模型样例先分别验group协议、沉默/@与meme_id遵循；使用合成群窗口，不重放真实私密历史。

群验收至少含：非@自然接话和合理沉默、真实@不受冷却、黑名单直接@仍无输入、多人交错/跨群不串、直接群发无引用/自动@、联网来源、QQ收藏2项导入（数目以实际为准）、本地图片/GIF实际显示、图片失败和关闭中行为。ACK通过/视觉显示/人设自然度/长稳分别打状态，不能以源码或合成ACK关闭真人缺项。

用户自行观察成本时按backend/trigger/decision统计总调用、silent数、可核验tokens/credits、检索与发送轮次；真实credits仍unknown则如实保留。正常的沉默评估开销不能藏在“仅几条回复所以几次请求”里，也不为比较同时调用两个后端。

## 10. 回滚与未验证能力

可分别设participation.mode=mentions、memes.enabled=false、web.enabled=false并停机保存/重启，不删除模型/图库/旧个人会话。若回退typed账本之前的旧代码，先停机并隔离pending/unknown发送，再恢复同检查点数据库/配置备份；不能让旧文本修复器处理未知image部件。

模型/模式/人设/目录表变动新epoch清空RAM；原@个人历史保留，但不强行迁为群共享。重新启用free从新事件开始，不补发停机时漏过的对话。QQ群收藏只读导入不修改原收藏，回滚也不删除用户原图片；本机库留存待操作者处理。

未验证：真实框架silent/no-conversation所有路径、事件持有/优先队列公平性、两模型自然参与与meme标签遵循、账号收藏列表及QQ媒体域名、GIF显示、图片ACK和恢复。一般实现细节自行处理；改变账号/提供方、扩大群或访问范围、额外模型调用/视觉模型、裸发绕过账本等方案变化必须回规划。

依据：[NapCat收藏接口](https://napneko.github.io/develop/api/doc)、[API兼容清单](https://napneko.github.io/develop/api)、[NapCat源码](https://github.com/NapNeko/NapCatQQ)。本机包源码优先于线上新版本接口推断；官方资料/静态支持不代表已登录本账号或真实收发通过。
