# LAP-26：群聊理解、成员身份与长期记忆详细规划

返回[任务交接](HANDOFF.md) / [PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md)；后续执行入口见[medium指引](IMPLEMENTATION_GUIDE.md)。

状态：**仅规划，尚未实施、启用或验收。** 2026-10-18（Asia/Shanghai）；用户说明当前会话为sol6.1 Ultra，未自动检测/切换模型或档位。基线main/`29548796c662b0612f73c1d2b70e5f1b6a2201db`。本轮不改代码、人设、运行配置，不启停/认证/登录，不调用真实模型、群成员接口或群消息。规划中数值是明确的首版默认建议，不是已测出的最佳参数。

## 1. 需求、优先级与非目标

用户实际反馈：free能正常聊天，但明确叫“肥鱼”及对bot说“你”经常漏接；每次登录仍有密码和扫码验证，可暂缓。新增需求为收到图片的含义理解、小群成员名册/受控@以及群成员与背景的长期记忆。随后追加反复出现“模型进程清理未确认完成，已停止接收新请求”，怀疑session切换；本计划纳入可靠性LAP-31并前置。用户估计2—3k中文字不是硬性容量要求，本地约16k也不是本轮重新实测的有效上下文。

建议先处理LAP-31清理阻断可靠性，再按27关注/指代→28图片→29成员名册/@→30群记忆。共用可信身份、请求快照和预算；不让单项启用自动开启其他项。仅规划阶段领取LAP-26，后续分项等待用户指令，由AGENTS指定的gpt-6.1-sol/medium执行。

不包含图片编辑/生成、视频/音频理解、任意媒体下载、全群历史补拉、跨群画像、私聊、QQ管理/邀请/踢人、自动换账号/后端/模型、增加付费API或无限工具。识图仍使用操作者选择的现有后端与模型。登录延续LAP-24缺口，不把保存密码当作解决设备风控，不承诺免扫码。

## 2. 当前证据与诊断边界

### 2.1 代码证据

| 位置（基线行号） | 已有事实 | 影响 |
| --- | --- | --- |
| `plugins/qq_router/main.py:363`—`:366`、`:412`—`:446` | 真实At决定must_reply；其余为ambient | 叫名/第二人称没有相同优先权 |
| `participation.py:12`—`:19`、`:91`—`:140`；`main.py:193`—`:202`、`:404`—`:406` | ambient合批2—5秒、评估间隔5秒、发送冷却15秒/4次每分钟；90秒年龄包含等待和生成 | 有生成完成后过龄/抑制的可达分支；附件未证明发生该分支 |
| `src/qqbot_gateway/participation.py:69`—`:77` | RAM窗口分配临时uN；snapshot不保留稳定QQ、时间/对话对象 | 昵称/临时编号不足以形成可靠关系和长期记忆 |
| `plugins/qq_router/main.py:326`—`:329` | mentions裁剪当前AstrBot conversation历史 | 这是短期历史，不是共享群背景记忆 |
| `plugins/qq_router/main.py:301`—`:302`、`:383`—`:385`；`onebot_gate.py:266`—`:278` | mentions拒绝非文本；free把媒体降为占位，附件被清除 | 看到占位或URL不代表模型看到了图片 |
| `src/qqbot_gateway/contracts.py:28`—`:36` | content数组只接受text | 现有模型输入合同不支持图片 |
| `workbuddy_cli_runner.py:134`—`:143`；`ollama_ssh_runner.py:14` | CLI保持工具/MCP隔离，输入仍文字；原生chat无images | 官方视觉能力不等于当前链路已接通 |
| `onebot_gate.py:46`—`:85` | 授权群成员读取已在宽允许列表，但没有人数策略；发送仅文字/登记表情 | 实现人数限制必须落实到gate，@须扩充typed投递合同 |
| `token_budget.py:37`—`:56`、`turn_budget.py:15` | 预算按实际序列化UTF-8字节保守检查，保护target后裁剪窗口 | 配置名带tokens不代表精确token计数，不能直接把16k窗口当16k汉字 |
| `napcat_login.py:107`—`:130`、`napcat_login_client.py:202` | 生产数据归属unverified，不允许密码回退启用 | 反复验证未解决，不能绕过数据目录证据门槛 |

LAP-25已有260单元/384实际框架合成通过是旧离线证据；当前运行实例是否加载该版本未知。本轮没有重跑，也没有用新反馈关闭原真人差额。

### 2.2 用户附件日志（仅脱敏结构分析）

附件为NapCat stdout，215行、154343字节；可解析事件时间范围2026-10-18 12:58:47—13:14:13（Asia/Shanghai）。可解析arrayMsg中14入站/8出站、2群/4发送者；有8次send_group_msg，ERROR/WARN为0。7条入站是真实@bot；7条含“肥鱼”，其中4条无@、3条真实@；没有reply事件。

可观察的脱敏时间链：12:59:03叫名、12:59:09真实@、12:59:16相邻bot发送；13:01:05叫名、13:01:24真实@与bot发送同秒；13:05:35叫名、13:05:57真实@、13:06:02相邻bot发送。至少一次无@叫名+第二人称后出现bot发送。这里只说明事件先后，**不能把同秒发送归因于该条@，也不能据邻接时间计算可靠的请求响应时延。**

附件没有项目request_key、must_reply、decision、冷却/排队/关联ACK记录；因此能证明叫名到达NapCat，不能证明它已进入哪一轮模型输入、模型选择silent，或确定唯一故障点。原生sent也不是项目绑定到该请求的ACK证据。原始附件、群消息、账号/群号不复制入仓库；本轮不重放消息或补拉历史。

### 2.3 第二份典型案例（后续追加，仅脱敏结构）

第二份附件51074字节、81行，解析时间13:24:10—13:25:14，和第一份时间段不重叠；9条arrayMsg为6入站/3bot出站，1群/1名人类发送者，3次send_group_msg、无ERROR/WARN，同样没有项目request/decision或关联ACK。13:24:10无@句首叫名；13:24:27真实@与第二人称、13:24:32bot发送；13:24:39再次真实@、13:24:44bot发送；13:24:46和13:24:54同一人两条未@短文本；13:25:09真实@、13:25:14bot发送。三次相邻@→bot均5秒仍不能据此当作关联模型时延。

后两条短文本在上一次bot发送后2秒/10秒、没有他人插话，且**既无名字/真实@/Reply，也没有“你”**。这说明单靠补“你”的识别还不够，必须保留自然续聊/省略主语的焦点候选。不能据此认为每条短句都必须回复；也不能说确定被15秒冷却吞掉：实际配置/生成与发送前检查时刻未知，只能指出与默认冷却的可疑重叠。第4节因此加入focused_candidate同次语义判断，维持原60秒/零插话边界。

进一步只读比较确认13:24:54的短句包含前一短片段，13:25:09真实@消息去掉At后的正文与其完全相同；后续显式重发支持此前是在尝试同主题承接/补充的解释，但不能反推当时模型已收到或必然应该回答。只保存此布尔比较与抽象分类，不保存原句。

### 2.4 第三份清理失败反馈（与第二份部分重叠）

第三份附件151172字节、171条物理行，解析事件13:24:10—13:28:54；与第二份时间重叠，不把事件数相加当独立故障。27条arrayMsg中18入站/9出站，9次send_group_msg里2次为清理失败固定提示，对应原生出站时间13:28:33与13:28:46。提示在请求/回显等结构出现16次，不能说发生了16次故障；第二次提示也可能只是首次失败后全局阻断的回显。

附件仍只有NapCat事件，没有项目request_id/CLI_START/REQUEST_FAILED/Traceback、PID/创建时间或cleanup结果。没有精确匹配既有三种重置命令的入站文本也不能排除本机操作。可证“提示被发送”，不能证实真实残留/误判、具体PID或session切换原因。当前源码每轮新建CLI、明确`--no-session-persistence`且无resume，故不把它表述为已证实的常驻session切换故障。修复合同见第13节。

## 3. 共用合同：可信身份、一次生成与预算

1. 入口先检查机器人身份、授权群、非私聊和黑名单，再构造窗口、图片引用、成员候选与记忆。被屏蔽发送者不触发后续查询/下载/模型/记忆。引用只解析同bot/group/epoch当前已经获准的本群窗口或仍有效的有界ACK索引，不用重启前旧账本升级reply_bot，不调用get_msg/转发接口补拉未知作者内容；只能确认引用对象但正文不可见时明确降级，不声称看过。
2. 本机稳定键为`(bot_qq, group_id)`，成员为`(bot_qq, group_id, user_id)`；QQ字符串是身份，昵称/card只是可更新显示字段。不同群同一QQ的档案不共享。epoch/uN仅当轮/连接标识，不能作为持久身份。
3. 模型只获得请求内opaque member_ref、显示名、可信speaker/recipient关系、相对时间与来源级别。明确`self.speaker=bot`及配置别名、当前target/发言者；保留事件中真实@其他人的对象关系（同群ref或other_member），禁止把它删除后让“你”失去消歧线索。原生附件/At组件仍由可信层转换，不触发框架额外查名字。服务器保留ref→QQ映射；模型不能提供任意QQ、群号、路径、RPC。ref需要覆盖同轮快照及ACK响应身份，不能用昵称直接定位@或记忆主体。
4. 扩展版本化输入/输出envelope，digest覆盖消息、attention、成员候选、记忆revision、图片hash/处理方式与配置版本。保持旧v1纯文本路径兼容，v2结果必须与原请求/epoch/版本绑定；v1强绑must_reply与trigger=mention，新协议须增加独立addressing枚举，不能把叫名冒充真实mention。仅新增功能显式启用时provider/gateway成套协商v2；关闭新功能继续严格v1，不把新trigger硬塞旧协议。文本、表情、@及memory proposals可同轮输出；辅助字段损坏只丢弃该字段，保留经过既有规则验证的文字，不触发二次修复生成。
5. 每个获准turn最多一次项目级模型生成；关注判断、看图、回答、记忆提议放在同一次输入/响应里。CLI内部force压缩/恢复尚未证实可严格限制上游API次数，继续保留LAP-10差额。元数据/解码/目录查询不是模型生成；不借此启动额外caption/summary/embedding模型。
6. 先保证固定政策、当前目标消息/当前图、必要身份与回答输出余量，再考虑可选窗口、相关名字和记忆。共享附加文字上限`min(2304字节, 输入预算的20%, 核心输入后的实际剩余)`；其中memory最多1536字节、名册最多768字节。裁剪优先去掉无关旧窗口/候选，再压缩可选事实数；当前目标过大则明确失败，不能裁掉目标来假装支持。相对百分比只是硬上限，不能覆盖最终序列化检查。
7. 图片编码字节、文本字节、原生视觉token/patch占用分开计算。不能把base64长度当模型token，也不能让新图片/成员/记忆suffix绕过LAP-25最终system检查。原生视觉预算未核验的profile保持视觉unverified/禁用；不以放大输入预算解决未知占用。

## 4. free关注、称呼与第二人称

### 4.1 行为合同

真实@继续最高优先、必须进入回应流程。新增以下分级，仅在原free模式内生效；mentions模式仍要求真实@，不因新别名扩大触发范围。

- `direct_name`：显式配置别名的独立呼唤/句首句尾称呼，或“别名+明确对话请求”。默认别名包括肥鱼、大肥鱼、鱼鱼、鲸鱼娘、小鲸鱼、DSH；大小写/空白正规化、词边界/引用过滤、最长别名优先。整句只有别名可回短应声，不强求群友同时带问题。谈论该角色、引用别人叫名、代码/网页内出现别名只作软提示，不能简单substring必答。
- `reply_bot`：Reply指向本群本epoch已确认ACK的bot消息，可解析为直接回应；引用未知ID、被屏蔽者、其他群消息均不补拉，不能误判为reply_bot。
- `focused_followup`：bot有ACK确认的文字回复焦点，且同一位群友在60秒内、没有其他群友插话时继续对它发第二人称问句/请求，优先作为续聊。焦点仅由已确认文字发送形成，只保留最近1个明确目标及最多3条必要ACK bot消息；仅发图片/本地未关联通知不建焦点。人类互相真实@/引用他人、显式更换对象、焦点超时/重连/重置立即失效；有他人插话后仅可保留软提示，不能强判必答。第二人称本身不是全群关键词触发器，多人歧义交同次模型判断，可保持沉默。
- `focused_candidate`：同一焦点/60秒/零他人插话条件下，没有“你”或名字的省略续句也进入关注候选。带入当前目标、上一轮实际已发送的bot文字和双方speaker关系，同次模型判断是在回答bot问题、补充/纠正/继续请求、结束确认还是另起话题；清楚的继续请求应回应，单纯确认/感叹可沉默。候选不是强must_reply，不能把“同一人又发了消息”自动变为必答。
- `ambient`：保留自然参与，模型同次选择speak/silent；提到bot的第三人称和无明确对象的“你”属于此类或soft_hint。

输入明确说明“bot/assistant就是肥鱼；你/我指代需要结合speaker、recipient和最近已发送内容判断”，角色正文不能再把所有称呼例子强制约束为真实@前置。别名从配置来，不能由群消息临时改名或覆盖访问控制。允许用户本机调整别名，不把复杂匹配规则写进人设台词。

### 4.2 调度、冷却与失败

真实@、高置信direct_name/reply_bot以及严格合格focused_followup，跳过ambient合批、评估间隔/每分钟评估次数、自发表达冷却/自发每分钟上限；仍遵守全局单并发、去重、访问控制和同级FIFO。优先级明确为真实@ > 可靠叫名/引用bot > 合格焦点续聊 > focused_candidate > ambient。首版所有direct按不同message_id独立ticket，真实@永不与相邻消息合并；去重只针对同一条消息，不能以2秒去抖吞掉第二个真实请求。高置信direct的`must_reply=true`；有歧义且不满足焦点条件的soft_hint保留模型选择与ambient限流。

focused_candidate在焦点有效期间跳过ambient的15秒自发冷却/5秒评估间隔等限制，以当前事件进入同一次语义判断/回答；不额外启动classifier，也不强迫模型发言。每个焦点候选最多4次评估/60秒、从该群非真实@direct的4个待处理额度共用，超限退回原ambient/静默，不侵占真实@。候选一旦决定silent，不为同一message_id自动重评；需要后续新消息才可能再触发。模型输出无可确认目标时可沉默；新真实@始终优先。

每群最多保留1个待处理ambient快照，新消息更新快照；direct优先于尚未开始的ambient，不取消已经发出的上游生成、不重复启动模型。运行中有新direct时记入pending_direct有界优先FIFO，不能用后到覆盖前到的单槽；下一轮在原请求完成/确定失败后重建最新快照。真实@保留既有mention_queue_limit=8默认额度，非真实@的direct单独最多4个，不能用叫名挤占真实@名额；满/超时使用绑定请求的受控短提示，不无限积压。必须保留target_seq及必要的引用bot行/焦点行，不能在窗口裁剪/marked evaluated时吞掉呼唤；引用行被裁掉则显式降为未解析，不能保留悬空seq。结束/取消时清理pending与锁，重连丢弃旧epoch。

不能承诺固定秒数：全局max_concurrency=1、已有长请求/模型加载/联网/发送ACK仍影响等待。验收将分别测事件→入队、排队、模型、ACK；若长时间排队是主因，先调度再决定是否另行规划并发/模型变更。错误使用现有绑定请求的短状态或静默策略，不能每次漏接另起兜底模型。

### 4.3 可观察性

新增默认不含正文的固定类别事件：received/filtered/queued/merged（仅ambient）、attention_reason、cooldown/rate_limit、snapshot seq范围与target保护结果、model_started/model_done/decision、delivery状态及取消原因。用额外随机trace关联各阶段，不把既有digest(request_key)误称随机；记录阶段耗时、backend/model/config版本、裁剪字节数。群/人只用本次运行随机ref或秘密key的本机HMAC，禁止裸SHA号码，避免可枚举身份；不输出QQ/群号/正文/图片URL或base64。CLI/模型返回原文仍不写普通日志；收集诊断不能再次消耗额度。

## 5. 收到群图片的理解

### 5.1 能力与启用门槛

官方协议/模型能力与本项目实际集成分别记录：现链路明确只收文字；后续只在操作者选择的现有profile支持原生图片且适配器通过时启用。CodeBuddy走stream-json用户image content，不开放Read/文件/MCP工具；Ollama走同一次原生`/api/chat`消息images，继续固定SSH/指纹/tag/digest/think设置，不建立旁路视觉服务，不在CLI与本地之间自动切换。

启用前需分别核对锁定CLI版本、当前所选模型的视觉能力、现有隔离参数组合、图片schema、原生预算/错误、两后端实际runner的合成序列化。零推理元数据不能当实际识图通过；真实模型图片验证必须由用户后续指定后端/样图/调用预算。提供独立受控验证入口：保持生产vision关闭，对用户指定组合/样图执行一次原生图片请求，输出不含图片/私密内容的版本与预算证据；只更新该锁定组合的证明，不自动启用，失败不换后端/重试。这样不要求先开启生产才能取得验证证据。一个profile失败保持该profile不可用，文字仍可用。

### 5.2 入站与数据流

黑名单/群准入之后，仅为当前获准新消息保留typed image_ref；ref绑定bot/group/sender/message/epoch、原图hash和TTL，规范化后再绑定实际blob SHA256/MIME/字节数/宽高/规范化版本，请求前重验实际传输字节。原始URL、CQ码、文件路径不交给模型。不读取日常QQ文件夹，不随意接受file://、localhost/内网URL、任意重定向；复用安全下载/解码思想，但必须为收到图片单独核对NapCat图片ID/URL域名来源，不能照搬收藏域名白名单。无法证明来源即拒绝该图。

首版仅JPEG/PNG/WebP及GIF首个完整可见帧；GIF明确只看静态帧，不能声称理解动画。每轮默认最多1张（多图明确只读取选中的当前目标图，不能假称比较了全部图）、原文件<=8MiB、解码前检查<=16M像素，去EXIF、等比缩小最长边<=1024且规范化<=1M像素/512KiB。不得裁掉语义区域来凑尺寸。超限/损坏/SVG/视频/音频不处理；长截图/小字不清须说明看不清，不能凭附件名补想象。规范化只为模型输入，不向群友提供编辑后的图；多图联合理解以后另规划。

下载只允许当前事件已有的HTTPS QQ图片来源，初始精确主机`gchat.qpic.cn`/`multimedia.nt.qq.com.cn`；复用现有PublicResolver/PublicConnector思想、每跳重新校验，禁私网DNS/重绑定、代理/cookie/auth，本地filePath拒绝。不增加get_image通用RPC，也不为失败自动换域名。已知来源后仍验证类型、尺寸与字节限制。

经有界fetch/decode进入本机忽略的短命blob缓存（默认60秒/规范化总8MiB，LRU清理、完成释放；原始下载单独限8MiB且最多一个解码任务），provider只接带身份校验的blob描述，由gateway解析为当前profile原生图片。单轮HTTP body<=2MiB，payload限制单独考虑编码膨胀，仍保持文本旧上限；图片字节不进普通日志/任务账本/长期记忆/Git。禁止复用已过期/跨群ref，重连/黑名单变化清理引用；排队过期时明确不可见，不为刷新blob再次下载或生成。

视觉输入暂按每张4096 token余量作保守规划假设；它不是测得消耗。适配器需证实缩放后最大patch/token约束、chat模板/system/输出余量，并在本地num_ctx内为视觉扣除余量后降低可见文本预算，再跑最终envelope检查。若已有固定system加当前目标都装不下，直接拒绝该图，不删政策、不增num_ctx、不自动压缩调用。CLI原生容量若仍未知，报告该限制，不能声称4096保证不超窗。

free中普通图片是有界新消息候选，不自动对每张图发表评论；明确叫名/@/reply_bot并带图时按direct理解。一次生成同时决定是否发言并理解图意，不先caption再问模型。短期窗口仅保留“图片可用/已过期”等状态和本次回答的有界语义描述；只有当前受保护目标图进入首版视觉请求，未解析引用不补拉旧图。模型看不到图、下载失败或视觉不支持时，direct给一次准确的能力状态并可回答仍存在的文字；ambient静默。不能说“已看图”而实际只送占位。

图片及其中OCR文字均是用户材料，不可覆盖system、准入、工具权限、@候选或记忆主体；识图描述不得直接作为长期已证实成员事实。保存图片/人脸身份、识别人像对应QQ群友不在范围内。

## 6. 少于50人的成员名册与受控@

用户使用“少于50”和“大于50”，恰好50未指定；首版保守定义为**1—49才可拉名册，50及以上/未知不拉**，不把50默认扩大为允许。

固定读流程：授权群获准新消息按需触发→get_group_info检查member_count为整数1..49→最多一次get_group_member_list→验证列表群归属、QQ唯一/有效、数量与count一致且<50→过滤bot/黑名单→仅缓存user_id/card/nickname。card非空优先，否则nickname；不保存性别/年龄/地区/活跃时间等无关字段。count/名单缺失、超时、重复/群不符、返回>=50或不一致立即丢弃、不补拉；单次查询超时2秒、整个流程<=4秒，无连接不启动bot。

count TTL默认60秒，名册TTL300秒；只在有新获准群消息且缓存失效时刷新，不开后台定时主动任务。名单注入和typed@必须同时有未过期合格count与未过期名册，300秒名册不能覆盖60秒count；count过期未刷新/失败时立即停用两者。可验证的入退群变更事件立即使count/名册失效；不依赖它一定送达。count达到50/未知立即清理可用名册及其注入，不经名单API探测人数。群大时允许沿用当前获准事件本身已有sender显示名，不外查完整名字、不补拉单成员名字来绕开门槛。

必须收紧gate现有宽允许RPC：框架/插件不能绕过人数策略直接get_group_member_list/get_group_member_info/get_stranger_info获取群友名字。只提供绑定当前授权群、目的/期限和请求身份的固定成员查询能力；bot自身就绪等既有必要查询单独审计保留，不给模型通用RPC。预检/健康不查询名册。

NapCat安装包的get_group_info优先缓存，get_group_member_list的no_cache刷新也可能立即返回旧缓存；先count再list不是原子事务。因此无法承诺“现实人数刚跨50的同一瞬间绝不发出list RPC”。严格口径是按可证明的当前人数快照控制，并列出新鲜度限制；如果实施时无法获得可用count证据，保持roster不可启用，不能伪造实时人数。读取后发现超阈值/不一致必须丢弃。此能力门槛须在实现报告中单独保留，不以官方字段存在当真实新鲜度通过。

缓存完整名册不等于全量注入。每轮仅给当前/引用发言者和文本明确提及且唯一匹配的候选（最多8人、总768 UTF-8字节，计入共用上限）；其余按需匹配。重名、多名称混淆、已过期名单不猜。名字中的指令只当数据；模型用member_ref选择，不因文字中出现QQ号允许@。

输出新增typed mention节点，模型最多选择1个本轮可信candidate；代码解析为OneBot `at`，禁止all/跨群/黑名单/任意QQ或失效ref。首版只在roster已启用且群人数合格时开放此发送能力，默认不自动@：普通回答仍直接群发，只有确需指出对象/用户要求代为提及时选择。不能以文本CQ码偷偷@，也不能由名字反查并盲发。

@与文字组成同一消息链、共用原event/同群队列/逐条ACK，不另发一个孤立@气泡；投递前再次验证成员候选/阈值/epoch/config。@失效降级保留正常文字，不换人、不补发；最多一个@、不@all、不为通知牺牲正文。body canonical_text不混入内部ref，历史保存语义@名称与稳定主体引用，账本保存typed组件/身份hash以校验，ACK未知遵守LAP-25不重发。

## 7. 群独立长期记忆

### 7.1 形态与隔离

建议使用**有界事实库+相关条目注入**，不要每轮加载整篇不断增长的Markdown。主文件为忽略的`state/group-memory/<本机HMAC群键>/memory.json`，可在本机导出该群memory.md供查看；修改通过本机受控字段操作写JSON，首版不支持把任意MD回导覆盖主库。Markdown是可读视图，模型无文件读写工具。HMAC key持久化于项目忽略的`secrets/group-memory-key.local.json`、不打印；已有目录但key丢失时拒绝新建空命名空间，先报本机恢复缺口。目录由服务器固定生成，群消息不能提供路径。重启保留记忆；连接epoch/后端切换不改变群键，切账号/群一定隔离。

文件包含schema_version/revision以及有界records；record有id、scope(group/member)、稳定member key、kind、简短fact、source message hash/actor key、observed_at/updated_at/expires_at、confidence、pinned。QQ只留本机忽略文件；模型ref由当轮映射生成。事实写入以(bot,group,user)为边界，其他群同一用户不读取、不合并。

### 7.2 写入与可信度

首版仅记少量稳定背景、群内约定、自述称呼/长期偏好及操作者手工固定事实；不逐字记所有聊天，不把玩笑/第三人称指控/模型猜测当事实。第三方转述只能标注不确定候选且不注入active；禁记密码/令牌/家庭访问资料、联系方式/位置/健康等无关敏感细节、被屏蔽者内容。成员目录负责名字，不重复把49个昵称塞进记忆。

同一次模型响应可附最多3条memory proposals（每条fact<=240 UTF-8字节），每条必须引用当前快照真实可见seq/source、合法subject_ref及操作类型。允许自述/明确群约定作为新增候选；修改冲突旧事实必须提供同一主体的新自述或本机人工确认。不能由A的猜测改B身份/偏好；不能把模型自己的回答当证据。代码再做身份、来源、大小、敏感形态、重复与冲突检查；无效提议丢弃，正常回复不受影响。

入站事实与bot行为分开提交：通过原请求身份/快照验证的入站自述，可在有效silent决策时进行一次memory-only事务，避免bot不说话就永远不能记事；其证据只来自入站，不声称bot已发言。涉及“bot答应了/上轮我向谁说”的内容及对话焦点，必须有相应发送部件ACK才生效。格式/身份失效、取消、黑名单/授权变更不写；未知投递不得据此生成bot承诺。事务ID固定绑定原请求request_key+proposal_index+输入base_revision+phase（入站或指定ACK依赖集合），不得随当前revision/CAS重算；CAS冲突只重做本地scope/来源/冲突校验、不重调模型、不覆盖已更新事实。事务ID与内容在同一次JSON原子replace落盘。每群最近128条已应用marker和最多8个待处理turn/24条提议（合计<=16KiB、10分钟过期）有界保留；marker只有在无pending/恢复事务引用时才可轮转，满且不能轮转则拒新提议。旧request已关闭/超时不得重入；不自动回放旧响应或群发送。

### 7.3 容量、更新与遗忘

每群上限64条/事实文本总计<=16KiB，pinned最多4条/总<=1KiB，单条<=240字节；**完整序列化主JSON（含元数据、索引、事务标记）<=64KiB**，不是元数据再加64KiB。活动成员最多32位，目录不计入该32位记忆主体；不是每个群友都必须有档案。本模块最多16个授权群、所有主文件/MD/备份/pending/tmp/隔离坏文件合计<=8MiB；超限拒新写入/新群启用，不自动删除其他群来腾空间。每轮最多8条、1536字节且受第3节共享剩余预算限制，优先当前发言者/被提及者和相关群背景。群大时不外查名称，记忆仍只从获准新消息和稳定主体得出；不能把名册禁用解读为跨群画像许可。

每条最多4个消息来源ref、8个完整来源actor依赖、1个冲突旧值（<=120字节且计入主文件）；合并会超来源/actor上限则拒绝该合并，不通过截断actor集合丢失黑名单删除依赖。来源消息hash可有界替换，但完整actor依赖只能因该来源内容被移除而减少；不能“压缩”掉依赖后保留派生事实。目录只保存当前获准事件与合格小群名册的有界名字，别名列表每人最多2个，不做无限改名历史。

不要简单“越旧越先删”，也不要为压缩开第二次模型调用。采用：同主体同类事实去重/更新→同次模型可提出保留来源的合并→代码按过期、可信度、近期引用、重要性和冗余评分淘汰→仍超限拒绝新低价值条目。群约定/人工pinned优先；短期事件默认7天，成员长期偏好90天，稳定群背景180天，到期在读取/新消息时懒清理，不开启定时发言。pinned不自动遗忘但计入硬上限、可人工删；所有时间/分数由代码计算，模型不能把任意条目标永久或无限重要。

合并失败时保留可验证旧事实，淘汰低价值/过期项，不压缩成脱离来源的“全群总结”。用户纠正采用较新同主体自述，保留有界版本/冲突标志；过期/被删事实不通过summary复活。检索首版用稳定主体/关键词/类型与最近相关引用，暂无embedding、向量库、后台做梦或额外LLM；效果不足再带实测回规划。

### 7.4 管理、黑名单与恢复

仅本机提供按群查看/导出、固定/纠正、清除成员/全群的管理入口，默认只显示条数/字节，不把整库输出普通诊断；编辑采用停机、配置锁/双摘要/原子替换。群内自然语言不能任意读取/批量导出所有成员档案，也不能让模型访问文件。原“重置本人会话”语义不偷偷改成删除全群记忆；提供清楚独立的本机动作。

黑名单变更加载时先清除该user作为主体、来源或关联引用的记录/索引/名字缓存/pending proposals/内存缓存/可读导出、本功能有界备份及坏文件隔离副本，再允许使用记忆；引用/合并条目必须保留来源集合，以便删除而非只删除显示名。派生条目无法安全拆除来源则整条删；损坏副本无法选择性解析则删除该群副本，不从中恢复。清除失败先禁用该群记忆读写并报告本机固定状态，禁止继续召回或从backup复活。后续消息在入口直接拦截。第三方手工转述无法保证识别原作者，保留既有边界。

原子replace、每群revision/generation、进程内群锁和跨进程排他写锁；先预留原子替换临时空间，空间不足拒写。群清空/成员删除先使相关generation失效，迟到ACK不能复活清除前提议。损坏文件最多隔离1份并关闭该群记忆，文字聊天继续，不擅自空库覆盖。备份最多1份、MD最多1份，均计全局配额且本机忽略；删除操作同步清除副本，不能宣称安全擦除磁盘。临时文件受固定根路径与配额约束，崩溃后只清明确归属的过期tmp，不扫QQ目录。不同进程争用时拒绝写入，不能依靠Markdown台账充当运行锁。

## 8. 配置、默认值与生效

维持schema3，新增严格校验section；旧配置只在内存补默认，保存才原子迁移并备份，未知扩展字段保留。行为/输入合同变化更新相应config/persona epoch，重启加载，不自动改本机settings。schema3外壳兼容不表示旧代码认识新功能，回滚须先关闭对应功能。

| 拟新增字段 | 缺省/上限与意义 | 生效/兼容 |
| --- | --- | --- |
| `participation.attention.enabled` | false；free内新关注规则总开关 | mentions仍仅真实@；显式启用、正常重启 |
| `participation.attention.aliases` | 上述6个别名；最多16个/每个1..16字符 | 配置数据，不能群消息热改 |
| `participation.attention.focus_ttl_seconds` / `max_intervening_messages` | 60，允许15..180 / 固定0 | 无文字ACK无焦点，有他人插话不强判，重连/重置清空 |
| `participation.attention.direct_queue_limit` | 4，允许1..8，仅非真实@direct | 真@保留既有独立队列额度；不同消息不合并 |
| `participation.attention.focus_candidate_evaluations_per_minute` | 4，允许1..8 | 焦点候选跳过ambient冷却但可silent、无额外classifier |
| `vision.enabled` | false | profile未验证则拒启用，不fallback |
| `vision.max_images_per_turn` / `max_file_bytes` / `max_normalized_bytes` | 1 / 8MiB / 512KiB硬上限 | body<=2MiB、总规范化缓存8MiB，不能放大为任意媒体 |
| `vision.max_pixels` / `max_edge` / `blob_ttl_seconds` | 16M / 1024 / 60 | 规范化<=1M像素，profile视觉预算更小则从严 |
| `llm.profiles.<现有后端>.vision.input_reserve_tokens` | 4096规划假设，实际启用需能力证据 | 可见文本预算相应降低；未知不伪称精确token |
| `llm.profiles.<现有后端>.vision` | `status=unverified`、支持schema/锁定版本/model/digest证据 | 无真实试验不标真实通过；变版本重新核验 |
| `members.enabled` / `members.mentions_enabled` | false / false | 两开关均显式，群人数门槛不能配置大于50 |
| `members.roster_member_count_lt` | 固定50，仅1..49允许 | 恰好50默认不取；未知fail closed |
| `members.count_ttl_seconds` / `roster_ttl_seconds` | 60 / 300 | 仅新消息驱动刷新 |
| `members.max_prompt_entries` / `max_prompt_bytes` | 8 / 768 | 硬上限，最终预算可更小 |
| `memory.enabled` / `learning_enabled` | false / false | 可先人工固定记忆，再启学习；群间隔离 |
| `memory.max_records` / `max_fact_bytes` | 64 / 16384 | 硬限；不等于每轮注入量 |
| `memory.max_group_file_bytes` / `max_groups` / `max_total_bytes` | 64KiB / 16 / 8MiB | 全JSON与所有副本/pending/tmp/隔离文件共同受限 |
| `memory.max_prompt_records` / `max_prompt_bytes` | 8 / 1536 | 和members共享2304字节及20%剩余预算 |
| `memory.max_proposals_per_turn` / `max_record_bytes` | 3 / 240 | 一次输出提议，无额外模型 |
| `context_extras.max_bytes` / `max_input_fraction` | 2304 / 0.20 | 预算只是cap，当前目标与最终envelope检查优先 |
| 既有`llm.cleanup_seconds` | 继续默认5秒/范围1..60，定义为整次cleanup总deadline | LAP-31不自动放大或改本机值；恢复必须有退出证明 |

精确公开配置名在实施前按此合同落地；一般命名/模块拆分可由medium决定，但改变阈值、默认开关、后端、额度、单次生成或敏感访问范围必须回规划。配置菜单新增独立页/子项，不挪走现有编号；不要求用户手工拼JSON。

## 9. 任务、涉及文件与依赖

| 后续任务（本轮仅规划，不预建实施HANDOFF） | 范围/文件 | 完成出口 |
| --- | --- | --- |
| LAP-31 清理状态、请求进程归属与阻断恢复（优先） | CLI runner、ModelQueue、process_host白名单、项目status/管理入口、清理身份台账/必要Windows容器适配、测试/新报告 | 不误把未知当退出；原始错误/清理结果可区分，零推理检查且有完整证明才恢复；第13节 |
| LAP-27 关注/指代与可观察性 | `participation.py`、`group_protocol.py`、`main.py`、`model_gateway.py`、`task_store.py`、`persona.py`/`config/persona.md`必要固定合同；新增attention/identity辅助；配置/菜单/测试与新报告 | direct不被ambient吞掉；“你”不全群误触发；时间阶段可解释 |
| LAP-28 原生图片理解 | gate、contracts、provider、两runner、InputBudget/turn_budget、图片blob/fetch/decode模块、配置/菜单/测试 | 当前模型原生输入/隔离/预算分别有证据；离线与真实分开；仍0图像编辑 |
| LAP-29 小群成员名册/受控@ | gate固定RPC/人数门槛、member目录、typed plan/delivery/EventSendGuard/ACK、窗口/协议、配置/菜单/测试 | 49/50/51/未知及黑名单门槛；本群候选@一次ACK；缓存新鲜度差额明确 |
| LAP-30 群长期记忆 | group_memory存储/验证/有界检索、协议/网关/ACK关联、配置/菜单/测试 | 重启保留/群隔离、单次提议/幂等/删除/预算/崩溃恢复 |

LAP-31优先解决全局拒单/不可诊断问题；27再提供可信speaker/recipient与ACK焦点；28可在27后独立完成；29复用身份而不是另建昵称匹配；30依赖27/29统一身份和最终envelope。所有阶段维护自己的新verify/report入口，不运行会覆盖旧报告的verify主程序；已有脚本只扩充必要兼容场景。不是在一个实施session顺手完成五项。

## 10. 验证与验收

本轮仅源码/附件脱敏/公共官方资料核对与文档检查；以下全部是**待实施验收合同，不是已通过结果**。

- 清理：正常退出、root先退出/子孙慢退出、快速多层spawn、AccessDenied仍处理其他已知对象、PID复用、wait超时、成功结果但清理失败、原超时保留、第一次/重复cancel、关闭中cleanup、清理线程仍活跃时禁止下一生成、阻断后零CLI启动、完整身份确认退出后恢复、观察不完整不自动恢复、重启保留未决台账、状态/日志脱敏；仅自造受管子进程/替身。Windows容器另测创建后执行前归属、无breakaway、归零查询、嵌套限制、句柄清理及外部进程不受影响。

- 关注：合成真实@、独立叫名、仅叫名、第三人称/引用中别名、同人“你”续聊及无主语/名字的承接短句、结束确认可沉默、focused_candidate预算、过期焦点、A/B交错/人类@他人、断连/重置、忙时direct排队、ambient限流、重复消息；每条至多一次项目级生成，保护target、无锁泄漏。测阶段耗时而非只看消息相邻；夹具自造，不复制附件原句。
- 视觉：两后端实际runner+底层替身捕获原生图片schema/同一生成；实际AstrBot run_agent验证原始附件已剥离且框架无额外下载/补拉，受校验typed blob/target绑定穿透provider到原生runner；超限/损坏/恶意URL/私网重定向/跨群或过期blob/黑名单图片/OCR提示注入/GIF静态声明；纯文本旧路由回归。native token余量单列，不能用visible byte测试假证实。
- 成员：人数49/50/51/未知/boolean/陈旧count/名单>=50或重复/异常群/掉线/TTL/黑名单；验证受限时没有list/member_info/stranger_info旁路。重名、改群名片、候选失效、@all/任意QQ/CQ码拒绝、@与文字同链、ACK未知/部分失败不补发。
- 记忆：同QQ不同群、不同bot同群、跨epoch/后端、冲突自述/第三人称、来源不在快照、伪造ref/revision、silent入站事实、未ACK承诺、重复请求、并发CAS、断电/坏JSON、容量/TTL/pinned、黑名单删除含备份/合并来源、清除后迟到ACK、只看本群相关条目；第17群/全局满/tmp空间不足、marker轮转后重复ACK、memory-only与ACK两阶段、actor依赖超限、删除副本失败、HMAC key丢失、MD不能回导越权。
- 组合：mentions/free × single/adaptive × CLI/local；web/memes分别开关，并与新typed@/图片/记忆组合验证最终system/envelope预算、sender block、逐条ACK与停止。对受影响路径做覆盖，不为文档变更重跑所有旧测试。
- 真实范围另由用户指定唯一执行session、后端/模型/请求上限/授权群/样图/人工接受场景。最小关注样例需能把日志关联到原请求；识图用有明确答案的截图/照片/表情且含“看不清”的负例；成员先核实API新鲜度；记忆跨正常重启并人工纠正/清除。未做不标真实或完整通过。

## 11. 兼容、回滚与能力缺口分支

旧配置默认所有新增能力关闭；不改当前后端/deepseek模型/额度/人设本机内容，不重写旧历史/图库/pending/unknown账本。已确认运行free是用户反馈，不能据此自动开启本计划attention/vision/members/memory。

回滚先停机、关闭新增开关并保留配置快照/ACK/未知账本，处理pending身份后回旧版本；群记忆只停止注入，不删除已有数据，必要时本机导出有界JSON/MD；旧版本不写新envelope/记忆文件。图片缓存可按所属目录/身份有界清理，不清QQ设备数据。关成员名册同时关typed@并清RAM候选；关关注清焦点/pending，不改真实@合同。

LAP-31回滚必须先确认cleanup task结束及未决受管进程归属，保留未决身份/阻断台账；不能通过回旧代码、删flag或重启抹去unknown。Windows容器能力不支持时交付独立诊断/取消修复，保持阻断，不临时改为全局taskkill。

未验证能力与处理：图片模型声明≠CLI当前隔离组合/当前量化模型实际识图；原生视觉token预算未测则保持禁用；群人数缓存与成员变更非原子，不能承诺瞬时准确；附件缺request trace不能证明silent/排队根因；本机当前配置/运行加载未探测；登录原生数据根目录与报告仍缺；LAP-18公共搜索仍未通过。独立部分可实施/离线交付，能力缺口明确保留，禁止临时加caption API/向量服务、放宽RPC/网络校验或自动切模型。

分支：基线main且干净，本轮只在当前分支交付6份规划/索引文档；后续实施先重新读PROGRESS/TASKS/git status，确认没有同文件归属冲突。需要新分支使用`codex/`前缀，但不为纯规划无故新建worktree。只提交本任务文件；本机配置/secrets/state/用户日志绝不stage。每个独立可审阅检查点按长期授权commit/push并核对本地与远端完整SHA，Git不等于部署/真实验收。

## 12. 官方资料与GitHub参考

以下均为2026-10-18只读资料证据；网页通过defuddle/官方正文或官方raw文档读取，GitHub源码固定commit，非本项目真实验收。只借鉴机制，不直接安装插件，不把其他项目默认跨群身份/额外模型调用带入本项目。

### 12.1 图片与成员协议

- [DeepSeek V4.1 Flash官方发布说明](https://www.deepseek.com/en/news/deepseek-v4-1-flash/)声明原生视觉并列出WorkBuddy/CodeBuddy支持。项目仍使用CodeBuddy内既有模型名与额度，不采用页面的独立API模型名。
- [CodeBuddy官方headless文档](https://www.codebuddy.ai/docs/cli/headless)给出stream-json base64 image content。当前机器CLI 2.168.0自带同名文档`dist/web-ui/docs/en%2Fcli%2Fheadless.md:175`—`:187`可静态核对；这不证明现有隔离参数/所选模型组合已实际看图。
- [Ollama视觉](https://docs.ollama.com/capabilities/vision)与[chat API](https://docs.ollama.com/api/chat)定义当前user消息images；[精确Qwen量化tag](https://ollama.com/library/qwen3.5:9b-q4_K_M)与[Qwen官方9B模型卡](https://huggingface.co/Qwen/Qwen3.5-9B)支持该路线的视觉能力声明，不套用其他大模型benchmark到本机9B。
- [OneBot 11公开API](https://github.com/botuniverse/onebot-11/blob/master/api/public.md)、[消息段规范](https://github.com/botuniverse/onebot-11/blob/master/message/segment.md)及[NapCat官方API目录](https://napneko.github.io/onebot/api)定义人数、成员字段与真实at；模型输出`@名字`纯文本不等于协议@。
- 安装NapCat包`runtime/napcat/installer/NapCat.52230.Shell/versions/9.9.33-52230/resources/app/napcat/napcat.mjs`：`:73503`—`:73524`入站图片；`:75494`—`:75520`人数接口优先缓存；`:78360`—`:78391`名单刷新后可读旧缓存。此为本机静态包证据，未调用真实接口或读取群名单。

### 12.2 GitHub记忆实现比较

| 参考实现与锁定源码 | 值得借鉴 | 不直接采用的原因 |
| --- | --- | --- |
| [AstrBot User Memory评分/限额](https://github.com/Himukai-Kanata/astrbot_plugin_user_memory/blob/37174e1790668ae3f05e859771daaff6e1830e19/core/store.py#L47-L58)及[owner选择](https://github.com/Himukai-Kanata/astrbot_plugin_user_memory/blob/37174e1790668ae3f05e859771daaff6e1830e19/main.py#L271-L283) | 置信度/时效/印证评分、按类型限额、代码保护pinned、事实去重 | 个人owner跨群、软删除保留数据、后台巩固另调模型；不满足本项目直接安装条件 |
| [Memoria候选/合并](https://github.com/fttawa/astrbot_plugin_memoria/blob/a462338d18e698faecafdc8b8957126c3b37fd51/memoria/db.py#L148-L183)、[有界相关召回](https://github.com/fttawa/astrbot_plugin_memoria/blob/a462338d18e698faecafdc8b8957126c3b37fd51/memoria/db.py#L442-L496) | candidate/active分层、冲突标记、相关性与时间衰减、有界注入 | 个人层跨会话；[dream路径](https://github.com/fttawa/astrbot_plugin_memoria/blob/a462338d18e698faecafdc8b8957126c3b37fd51/memoria/dream.py#L61-L92)补拉历史/额外生成不适合入口隔离；衰减不等于物理删除 |
| [Mem0实体scope/到期](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L760-L800) | 身份字段不可被metadata覆盖、scope过滤、到期与删除分离 | 默认依赖向量库/embedding/提取生成；该SHA默认additive extraction，不能照旧资料宣称自动完整增删改 |

本计划的压缩与遗忘因此同时存在：有证据的同类事实去重/提炼保留价值，过期/撤回来源/容量淘汰实现真正有界；单纯扩大上下文或不断把旧摘要再摘要，不能解决错误事实、群间隔离和遗忘删除。

## 13. 追加：模型进程清理失败与停接新请求（LAP-31）

### 13.1 已证实代码及未证实原因

`workbuddy_cli_runner.py:134`—`:166`每次独立创建CLI进程，禁session持久化；`:176`—`:190`使用PID/create_time对象、50ms观察后代，不是按进程名或裸PID盲杀。`:248`—`:277`所有成功/失败/超时/取消都会进入finally；`:265`—`:274`遇一个AccessDenied即False、wait仍有alive也False；`:275`—`:277`把False统一提升为CLEANUP_FAILED，可覆盖原始结果/超时。psutil已有PID复用保护，不能把源码描述成没有身份检查。

`model_gateway.py:68`/`:92`/`:104`—`:118`使该错误阻断整个模型队列，不只某个群或个人会话；后续请求可不启动CLI就再次返回同码。`process_host.py:16`—`:18`只保留请求开始/失败，尚无清理阶段/剩余对象分型。现有附件不能确定遇到了权限问题、退出等待、取消竞态还是其他分支；增加cleanup_seconds或删除阻断不是已证实修复。

采样追踪不是完整容器，父进程快速退出或短命中间层可能漏采后代；反过来，观察失败也不等于一定有活进程。`shield(to_thread(cleanup))`能保护被包裹工作，但外层再次取消仍可能先退出，必须有强引用/接管完成结果；不能仅靠shield字样宣称清理生命周期已完整保证。

### 13.2 最小修复合同

1. 分开保存generation_outcome与cleanup_outcome；清理状态为observed_empty / owned_alive / identity_unknown，另外记录coverage=observed_only/job_complete。observed_empty只表示已知集合退出，不冒称全部后代。原因细分AccessDenied、wait_timeout、identity_changed、observation_incomplete、cleanup_in_progress。原始MODEL_TIMEOUT/PROTOCOL_ERROR/取消或成功结果元数据仍可诊断；已进入清理失败阻断时不发送可能迟到的旧答案。
2. 每请求只创建一个显式cleanup task，保存强引用与monotonic总deadline，取消/close都接管同一任务；不得创建多套并行kill或让ModelQueue在清理线程仍运行时判ready。既有cleanup_seconds默认5秒/1..60，覆盖kill、等待、进程wait及状态落盘；不能无限shield等待，也不能timeout后把仍运行的线程当退出。
3. 单个对象AccessDenied不提前终止其他已证明归属对象的清理；逐项记录结果，NoSuchProcess、PID/create_time变化、新复用进程、仍活跃、无法读取身份分开处理。PID复用的新进程绝不操作。只对本请求创建身份/可靠容器内对象操作，禁止按Node/Python/QQ/CodeBuddy名称清理，也不扩大到日常WorkBuddy。
4. 忽略的`state/cli-cleanup/`保存原子有界台账：实例/随机request/root与已观察后代的PID+创建身份、容器标识摘要、覆盖证据、generation/cleanup分类及时间；不存argv/env/system/prompt/群号/消息/凭据。最多1个active/unknown请求与32份resolved摘要、每请求最多128身份/完整文件<=32KiB、模块总<=2MiB；不能丢unknown腾空间。身份或台账超限在发送user前失败；运行中发现超限则阻断并记录不完整。
5. 对已经进入CLEANUP_FAILED/identity_unknown阻断的请求，阻断保留：已有cleanup task尚活跃、任一owned对象存活或覆盖不明，均不得接下一推理；新消息只能触发限频被动检查（每5秒最多一次、<=2秒、0模型/不再kill/不重试旧请求），本机`cleanup status/check`用同一固定检查路径。只有同创建身份的受管集合已退出且覆盖完整性有依据，才可将阻断转为已解除并处理新的请求；旧失败请求不重放、不补发。仅root消失、等待较久或删marker不能证明全清。
6. 重启读取未决台账、复核实例/创建身份；未知不直接抹掉。记录存活但当前操作者无权检查时保持阻断，使用现有有归属的受管停止流程或后续人工处理；不尝试全局提权/清进程。健康页及process_host新增严格固定schema事件，只显示原因枚举/数量/耗时/随机trace/最后检查时间，原始异常和群内容继续抑制。

### 13.3 完整性能力门槛

Windows每请求Job Object是可验证的增强路线，非现有能力。实施方先用自造进程验证CreateProcess suspended→AssignProcessToJobObject成功→ResumeThread的执行前归属，或等价的官方受支持创建时归属方式；任一步失败时，已创建（含suspended）的进程与Job句柄仍由同一cleanup task接管并记台账，不能遗留挂起进程。禁breakaway，设置kill-on-close，并用受管句柄/active process accounting确认归零。不能以一次父进程children()空列表代替完整性证明。嵌套Job/权限/CLI运行方式不支持或出现容器外未知进程时，保留identity_unknown并交付独立诊断/生命周期修复，回规划补缺口，不退化成全局kill或假自动恢复。

普通观测legacy路径不能因缺完整性证明被伪称“所有后代绝无残留”；保留原实现无检查异常且已知集合清空的正常成功准入，不因缺新增容器证据把每次旧请求都改成失败。它与**已经进入CLEANUP_FAILED后**解除阻断的完整性门槛分开记：后者须job_complete或等效可靠证据。完整自动恢复只有受支持且已验证的容器/创建身份覆盖才能开启；尚未达到时不得标完整验收。容器不修改CodeBuddy账号/设置、CLI工具隔离/单次user输入或模型参数。

官方依据：[Python asyncio shield](https://docs.python.org/3/library/asyncio-task.html#shielding-from-cancellation)区分内部task保护与外层取消；[psutil官方API](https://psutil.readthedocs.io/stable/)定义身份复用检查与wait结果；[Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)及[Nested Jobs](https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs)描述进程归属/后代管理。这里只据文档规划，未在真实CLI或当前机器执行容器试验。

适用文件：`workbuddy_cli_runner.py`、`model_gateway.py`、`process_host.py`、`manage.py`/本机菜单、必要新增cleanup_identity/Windows helper及相关单元/框架验证；不修改Ollama的REMOTE_RESULT_UNKNOWN解除合同。无新增付费后端/模型、无默认参数放大；新台账/状态版本变更纳入启动/回滚检查。具体未决分支、离线/真实结果和Git交付由后续LAP-31 HANDOFF记录。
