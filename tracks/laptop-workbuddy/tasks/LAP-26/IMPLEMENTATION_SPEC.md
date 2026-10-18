# LAP-26实施合同补充：协议、状态与验收

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [PLAN](PLAN.md) / [交接](HANDOFF.md) / [五项复制指令](IMPLEMENTATION_GUIDE.md)。

本文件与PLAN共同构成31/27—30的实施合同，仍是**仅规划、未实施/启用/真实验收**。针对PLAN中尚属原则的接口补齐确定规则；同一事项以本补充的精确约束为准，不扩大账号、群、触发模式、媒体和模型范围。模块名、私有HTTP路径名、类/函数名可由medium决定；材料所有权、认证、字段/状态、预算、失败和验收出口不可自行更换。

## 1. 覆盖与交付出口

| 用户反馈/需求 | 对应合同/后续任务 | 详细规划后的明确出口 |
| --- | --- | --- |
| 登录重复账号密码/扫码，可暂缓 | PLAN1/2、既有LAP-24 | 本轮明确延期；不实现新的免扫码方案，不开启unverified密码回退；保留人工登录与原缺口 |
| 叫名、“你”、省略主语的自然续聊 | PLAN4、本文件2—4 / LAP-27 | 确定关注/队列/时间/归因与trace；mentions触发保持真实@ |
| 群图片理解 | PLAN5、本文件2/5 / LAP-28 | 原生适配/离线/独立验证入口；实际能力和预算证明不足则保持不可启用 |
| 小群名字、按QQ稳定识别、受控@ | PLAN6、本文件5/6 / LAP-29 | 1..49门槛/固定RPC/typed@；人数新鲜度缺口独立列出，不假称已可真实使用 |
| 群成员/背景永久记忆 | PLAN7、本文件7 / LAP-30 | 本群有界JSON、相关注入、明确学习/更正/遗忘/删除；无新增模型调用 |
| 清理失败、停接新请求 | PLAN13、本文件8 / LAP-31 | 31A诊断/生命周期独立完成，31B完整覆盖/恢复另判；附件未证实session切换根因 |

实施顺序31→27→28→29→30。31A独立离线交付允许27继续；31B缺口仍必须保留。28的原生视觉未通过不阻断29/30独立开发。30依赖29的共用身份/候选代码交付，**不要求启用名册/真实@**，大群也可从获准发言者学记忆。每项各自创建HANDOFF，不能在同一session混领五项。

## 2. 开关矩阵与v2可信材料

### 2.1 模式、依赖与路由

- 所有新增能力effective=false：完整保留旧v1，包括已有web/memes/single/adaptive，不仅是“输出差不多”。
- attention仅在free且其enabled=true时effective；mentions即使填写attention也不放宽准入。vision/members/memory分别由自己的enabled与能力状态决定。只有至少一个新增能力effective才使用v2，provider与gateway成套协商；不支持v2直接失败，不自动退v1漏掉保护。
- 拒绝非法配置组合：members.mentions_enabled=true而members.enabled=false；memory.learning_enabled=true而memory.enabled=false。所属新section中未知键/拼写错拒绝；不属于本任务的其他扩展字段按既有合同保留。
- mentions仍用原UMO/按群+用户历史，不改成旁听群RAM。该模式可学习来源只有本次获准新消息；既有个人history只作当前对话上下文，不升为群共享事实。free使用本次最终群快照。
- 只开memory不启叫名/图片/成员RPC；只开vision不扩大mentions准入；名册开关与记忆无运行依赖。开关写入/保存不启停、不真实调用，正常重启加载。

### 2.2 请求合同

保留本地provider既有顶层`model/messages/stream/qqbot_request`。v2由router内部会话元数据/ContextVar构建，绝不解析群友正文来构造sideband；`stream=false`、model仍为既有本地适配器标识。v2可信头固定如下（封闭字段，duplicate key拒绝）：

```text
qqbot_request = {
 version:2,
 kind:"group_turn"|"member_turn",
 request_key:hex64, epoch:hex64, config_version:hex64,
 source_digest:hex64,
 mode:"free"|"mentions",
 addressing:"mention"|"direct_name"|"reply_bot"|"focused_followup"|"focused_candidate"|"ambient",
 must_reply:bool, target_seq:positive_int,
 resource_caps:[opaque_cap]       # 0..2；只在sideband，不进模型正文
}
```

`group_turn`对应free，`member_turn`对应mentions；mentions的addressing只能mention且must_reply=true。free中前四种为must_reply=true，candidate/ambient=false；真实@的意义不变。target_seq始终指向本次触发的新入站消息，即使可沉默也不能省略；ambient可另有eligible_seq供模型选择对象。配置mode/epoch由服务器复核，不信任客户端声明。

当前最后一个user消息承载下列结构化source body；mentions的旧角色history在它前面保留。source_digest=SHA256(canonical source body)，canonical为UTF-8、sort_keys=true、ensure_ascii=false、无空白分隔的JSON；不包含digest本身。body字段：

| 字段 | 类型/限制 |
| --- | --- |
| `self` | `{speaker:"bot",names:[str]}`，最多16名，每名<=16字符 |
| `target_seq`,`eligible_seq` | 当前目标；1..200个已获准且可回应的人类seq，必须仍可见 |
| `messages` | 1..200行递增seq；每行`seq/member_ref/name/text/reply_seq/at_refs/age_ms/images`；bot ref固定bot，其他ref为当前请求不透明编号；名字<=40字符、人类文字<=4000字符、bot<=8000；at_refs最多8，images最多1 |
| `focus` | null或`{version,member_ref,bot_seqs,received_age_ms}`，bot_seqs最多3，所指文字必须可见并已ACK |
| `member_candidates` | source固定[]；gateway兑换成员材料后effective最多8个`{member_ref,name}`，总块<=768序列化UTF-8字节；不是全量名册 |
| `memory` | null或`{generation,base_revision,records:[...]}`，最多8条，整块<=1536字节；记录仅`fact_ref/record_revision/subject_ref/kind/slot/fact` |
| `images` | source最多1个`{image_ref}`；gateway兑换后effective扩为`{image_ref,sha256,mime,width,height,byte_length,normalizer_version}`，没有URL/路径/base64 |
| `web_anchor`,`meme_question` | null或确切的一条获准文字；direct仅当前target，candidate/ambient依既有政策；不得外发全窗口/名册/记忆 |

age_ms取宿主单调时钟，取值0..900000；显示时区Asia/Shanghai。未知引用/其他人@只给unresolved/other_member，不补拉其正文/名字。可信本机映射包含(bot,group,user,message_id)，只在gate/router内存和必要忽略存储；它不进入模型或普通日志。

行字段封闭且类型固定：seq为1..2^63-1整数（不接受bool），member_ref为bot或`p_[a-f0-9]{16}`；text/name为字符串，reply_seq为null/同快照正整数/字符串unresolved；at_refs为0..8个有效member_ref或other_member，images为0..1个`i_[a-f0-9]{32}`引用。候选member_ref沿用该命名空间，fact_ref为`f_[a-f0-9]{32}`；focus.version、memory.base_revision及record_revision为非负整数，generation为hex32。source body所列字段始终出现，无材料时为null/[]。旧history不伪造seq或加入eligible_seq。

### 2.3 有效材料与输出

gateway先验证source_digest，再按第4节裁剪/兑换，构造实际送模型的effective body。effective_digest按相同canonical算法计算；独立返回保留seq、member_ref、fact_ref+revision、image hash的manifest。模型输出不能指定request/epoch/digest/attention或真实QQ。仅允许：

```text
{
 qqbot_turn_reply:2, decision:"speak"|"silent", kind:"chat"|"answer",
 bubbles:[string], meme_id:null|string,
 response_to_seq:null|positive_int,
 mention:null|{member_ref:string,bubble_index:nonnegative_int},
 memory_proposals:[Proposal]    # 0..3，第7节
}
```

所有字段应出现；缺失的辅助字段`response_to_seq/mention/memory_proposals`可规范化为null/null/[]并记类别，不能缺核心版本/decision/kind/bubbles。single仍只发一条，adaptive仍按既有上限，不为协议凑条数。silent必须bubbles=[]、meme_id=null、mention=null；must_reply=true不能silent。meme_id沿用受控图库候选，识图不自动启用表情发送。

正文通过既有纯文本/工具隔离/长度合同后再独立检查aux。坏mention/响应对象/某条proposal只丢该辅助信息；坏JSON/duplicate key/版本或核心decision/正文错误沿用LAP-25有界恢复及必答固定提示，**不可从破损或身份不符的输出抢救@/记忆**，不可二次模型修复。gateway在响应元数据附原请求、effective_digest/manifest、response_id和完整plan hash；router核验后才能发送/写记忆。

PreparedPart已有v1/v2含义保留；带mention的新投递metadata使用version=3，扩展text part的受控mention元数据，不把任意OneBot segments交给模型。模型bubble_index指原输出bubble；规范化合并/截断后建立原bubble→最终文字part映射，依赖被裁掉则丢该@或承诺，不猜新位置。@与文字同一发送/ACK，图片part仍独立；invalid aux不影响已验证文字。

## 3. 关注票据、队列、焦点与归因

采用router内一个v2优先dispatcher：lease覆盖本次生成直到原event投递/ACK结束，全局只有一个活动v2 turn。gateway保留单并发底线，正常最多一个v2请求进入其生成队列。v2不先持旧per-group lease再等待gateway，避免低优先请求阻住同群真实@；v1路径保持原实现。不同群因此也共享该dispatcher；发送等待占用时延必须记录，若成为瓶颈回规划，不偷偷增加并发或旁路发送。

优先级mention > direct_name/reply_bot > focused_followup > focused_candidate > ambient，同级FIFO、不抢断活动turn。全局待处理容量为既有llm.queue_limit Q（默认5）；保留R=min(2,Q)个待处理槽仅供真实@，其他类型待处理数<=Q-R。空闲且无已排队高优先票时低优先可立即启动，不受“待处理保留槽”限制；Q=0不排队。每群真实@8/其他direct4是额外上限，**不是保证12个全局名额**；全局或群上限先到者拒新票并给既有受控busy分支，candidate/ambient可静默。每群pending ambient最多1个，可合并；其他不同message_id不合并。

票据入队时冻结target、当时可见的引用bot/焦点必要行、接收时间、分类依据、focus version、原配置/epoch；每票冻结<=32KiB，所有待处理冻结材料合计<=256KiB（若Q配置更大仍从严），超限拒新票。不能只保存会被RAM trim掉的seq。派发时只重建可选窗口，不能拿后来focus重新解释旧票中的“你”。队列等待用既有session_queue_timeout_seconds（默认600）总deadline；direct不因排队跨过60秒丢失必答，权限/epoch/停止或排队超时仍取消。candidate/ambient入站总年龄仍<=90秒，超龄不生成；活动模型不抢断，发送前复核新鲜度和取消原因。

60秒焦点窗口按新消息**到达时**判断。focused_candidate额度为每群滚动60秒最多4次，跨focus版本累计；开始实际处理时消耗，失败不返还、未启动不算。重复message_id不重评；不能批量marked evaluated吞掉尚未处理direct。可靠叫名匹配按PLAN词边界/呼语，@他人或引用他人的关系优先用于排除误触发；正文引用/第三人称不能只凭substring升必答。

ACK完成、partial/unknown、silent、坏协议/无结果、gateway业务错误、框架取消/停止/异常都经同一幂等finally释放dispatcher恰好一次；无发送结果不等待不存在的ACK。若31清理仍未完成，释放路由票据不代表允许gateway新生成，后者继续按清理阻断合同执行。

direct回复对象固定冻结target。candidate/ambient的response_to_seq仅允许effective eligible_seq中的人类行；无合法对象仍可普通自然发言，但不能建立个人焦点。只有正常模型文字part的sent+message_id ACK建立焦点；本地错误/状态兜底、只有图片、unknown/failed不建立。partial只使用已确认文字，并绑定服务器已核验的对象；不能把承载ambient快照的event sender默认为被回应者。

## 4. 最终预算与联网兼容闭环

按已选profile实际InputBudget检查，UTF-8 wire字节依然是保守预算，不冒称精确token。额外context cap取min(2304字节,输入limit的20%,核心后剩余)，完整JSON转义/键名/身份/引用开销都计入。输出JSON、@、proposals共用原output reserve/num_predict，正文优先；允许proposals=[]，不自动加大参数。

固定流程：构造不可丢的政策/当前target及必要引用→选择附加材料→最终序列化检查→超限去最旧非目标非依赖窗口行→再减低相关成员候选→再减低排名记忆→修复引用并重建所有允许ref/source集合→重新检查，循环至通过。目标/必要依赖本身装不下就明确失败，不删政策/target。裁掉某人、事实或图片后，输出再引用它一律无效；曾在source里出现不够，必须仍在effective manifest。

v2 web资格使用可信must_reply/allow_ambient_web及单条web_anchor，不把新direct伪装mention。不得把名册/记忆/全窗口作为搜索问题。meme_question同样只取允许锚点，继续受图库/serious/single/adaptive合同限制。图片下载/兑换与web检索共用原15秒准备预算，不能各加15秒；CLI cleanup计入原profile/180秒provider总裕量。任何阶段失败不重试模型/不自动换backend；同次回答仍可说明图片不可见。

## 5. 材料服务、视觉证据与人数门槛

### 5.1 唯一材料所有权

gate是当前入站图片URL、规范化RAM blob、固定成员RPC和最终@映射的权威持有者。router只保留当前获准发言者的本机身份/记忆映射；provider只传sideband cap，**仅gateway兑换**，模型不见cap。source只带已获准image_ref和空成员候选，不预先下载/兑换完整描述；gateway校验source后一次兑换，再构建effective body/manifest和预算。内部服务复用现有loopback监听，使用独立context_service_token（随机>=32字节、项目secrets忽略文件保存，不复用QQ/SSH/CLI凭据）；无任意URL/路径/群号/QQ/action参数，无通用代理/MCP。

材料purpose只允许vision.resolve、members.resolve。cap为随机不透明值，绑定instance/connection/epoch/已获准event及用途/有效期；兑换前一次性绑定request_key、target_seq和source_digest。每个用途每轮最多一次兑换；并发、其他请求重放、错用途/target/epoch/取消/过期拒绝，失败也消耗、不再次下载/查询。图片采用RAM cache（规范化总8MiB/TTL60秒、原下载8MiB单任务）；以有界typed bytes返回SHA/MIME/尺寸/normalizer版本，不接受共享任意本机路径。内部认证/材料服务能力不足时不开放替代读文件工具。

成员服务可在可信本机返回受限映射用于router关联，但完整名单只缓存gate内存，最终给模型仍最多8候选。投递时只接受原turn的member_ref，gate再次解析与校验；另由gate根据同turn成员兑换收据、最终plan hash/part index签发mention.send一次许可，发送尝试前消费并剥离再交NapCat。不能复用已消费材料cap发送，模型/provider不能签发投递许可。普通框架RPC不能借新许可查询或@任意人。

### 5.2 视觉证据与启用出口

证明状态固定：unverified→offline_passed→native_observed→production_eligible。状态由证据计算，不能手改配置里的status升级；配置中只保留desired enabled和有界参数。证据绑定backend/model/tag或CLI bundle SHA、runtime/model digest、normalizer、原生context、推理/输出参数，任一变化失效。

offline_passed要求真实provider/runner底层替身证明图片schema/隔离/单次输入/大小与预算；native_observed要求后续用户明确后端/样图/**整轮调用总上限**后验证原生理解。每个批准用例至多一次生成、不重试；已知内容图片/截图/最大规范化尺寸分项记录，样图成功只能证明观察值，不能证明4096上界。

production_eligible另需可信模板和视觉token/patch上界证据。令L为原profile输入预算、V为已验证视觉reserve（初始规划值4096）：effective_text_limit=L-V且必须>0，现有overhead/system/目标/窗口/extras在此检查；排除base64，另检查完整body<=2MiB。V必须不低于证据要求的最低值，调低V使原证明失效。local同时验证effective_text_limit+V+output_reserve<=num_ctx。4096只是待证明假设；缺可靠上界/原生容量则保持生产不可启用，交付适配器/离线/验证入口和明确缺口，不能以一次试图成功或放大预算放行。

### 5.3 人数证据

count证据必须含数值、来源和实际观测时间或可证明最大陈旧度；received_at只是本机收到响应，不能冒充QQ群刚刷新。接收时已陈旧S秒，则count只剩max(0,60-S)秒有效期；S未知即不通过。count与名单TTL300秒必须同时有效。当前锁定NapCat get_group_info优先缓存且不消费no_cache，**不能仅凭重请求/HTTP成功证明新鲜度**；本轮没有证实可用来源。

严格门槛维持：无可证明的新鲜人数来源，拒绝激活members功能并报告capability_unverified；可完成固定RPC/防旁路/缓存/typed@的独立离线交付，不能标真实名册可用。若启用动作不满足门槛，配置工具拒绝开启；手改desired开关时启动只暂停该功能，文字聊天继续。不得临时改用新人数接口/默认接受陈旧值；新来源须补规划证据再实施。即使新鲜度通过，先count后list仍非原子，不承诺人数变化瞬间绝对无RPC。

只有整数1..49才允许list，50/51/未知/过期零list，返回>=50/重复ID/不一致全部丢弃。生成期间count过期，发送时去掉@，不得为恢复@追加成员查询或模型。大群memory仍可用当前获准sender，不能用member_info/stranger_info绕开名册限制。

## 6. @与候选失败边界

mention最多一个且必须附正常文字；member_ref来自effective member_candidates并仍满足count/roster/epoch/黑名单。不得all、bot、任意QQ/CQ码。重名不猜，显示名不作为权限。最终typed text part携带受控@，与文字同一个send_group_msg/ACK，不另发@气泡；映射或人数在发送前失效，由gate在同一次发送尝试剥@转纯文，并在可信ACK元数据标记mention_applied=false，历史/账本不能声称已@。若是否已转发不明，整part按unknown，不能另发文字。旧图库image不因识图能力扩大为任意发送图片。

框架必要的bot自身信息查询单独保留，群友名字查询必须经过固定成员服务。schema/mapping/manifest/part hash失败不准旁路原event补发。ACK未知不重发、重启不补发，沿用LAP-25的新消息不锁群合同。

## 7. 记忆schema、晋升、事务与遗忘

主JSON字段固定：schema_version=1、namespace_hmac、generation、revision、records、applied_txns、pending、purge。purge为null或`{generation,scope:member|group,subject_keys:[],state:pending|blocked}`，最多一项/<=2KiB并计主文件配额。Record：id/revision、scope(group|member)、subject_key|null、kind/slot/fact、status(active|candidate)、source_refs/actor_dependencies、observed_at/last_confirmed_at/updated_at/expires_at、confidence、pinned、conflict_old|null。ID/时间/confidence/status/pinned/TTL均由宿主生成，模型不能指定。

Proposal字段固定：`op(add|replace|merge),subject_ref,kind,slot,fact,source_seqs,target_ids,phase(inbound|acked_bot),ack_parts,privacy(general|sensitive|uncertain)`。每轮<=3、每条fact<=240 UTF-8字节；source_seqs 1..4且在effective来源集合，target_ids只可引用本轮实际注入的fact_ref和原revision。add无target，replace恰好1个，merge为2..4个同subject/kind/slot；pinned不可由模型更改。首版模型不delete，删除由本机管理/TTL/容量执行。ack_parts是原模型bubbles[]的0基编号，宿主映射到最终正常文字part；无法映射/正文被丢则丢该承诺，single合并后只需共同part的一次ACK，不用图片ACK证明承诺。

subject_ref只允许group或该轮已映射的member_ref；不能自填QQ/命名空间/路径。数组禁止重复项，未知proposal键或枚举只拒该条。inbound的ack_parts必须[]；acked_bot必须非空。普通事实只用inbound，bot_commitment只用acked_bot；两者不能互相伪装。

类型/槽与TTL固定：成员name/preferred_name、preference/likes或dislikes、background/skill或interest为90天；temporary/state或plan为7天；群background/purpose或shared_topic、convention/rule为180天；bot_commitment/commitment为7天且只能acked_bot。其他kind/slot拒绝。明确本人自述且subject等于来源本人→active；配置管理员明确群背景/约定或本机确认→active；无害第三方转述→candidate且不注入，只有后来本人独立自述/本机确认可晋升；群背景candidate仅管理员/本机确认晋升。指控/敏感内容拒绝，不能晋升为“事实”。

candidate晋升由宿主完成，不要求把候选全文注入：后续合法本人自述的add，与本机已有candidate按同subject/kind/slot及NFKC+去首尾/重复空白后的fact一致匹配，复用原ID、加入新来源并转active；不同事实不盲合并。候选期限取min(原kind TTL,7天)，仍计64条总限。confidence固定manual/admin=3、本人自述/已ACK承诺=2、candidate=1；模型不打分。bot_commitment在全部依赖文字ACK满足后才转active，不能作为用户自述覆盖其偏好。

slot是类别而非一律唯一键。单值槽仅name/preferred_name、temporary/state、群background/purpose；其他已列槽为多值，去重键为subject/kind/slot/normalized_fact，可并存多个likes/rule并merge。同批仅拒相同target/去重键，单值槽另外拒重复slot。合法较新本人自述可由宿主替换其单值槽未pinned的旧candidate/active（以来源时间判新旧，不用commit时间），不受不可见candidate阻塞；多值不同事实保留，pinned冲突需本机处理。

模型privacy只作过滤建议：宿主仅接受general，并叠加秘密/令牌/密码/密钥形态、联系方式/位置/健康等固定拒绝类别；语义分类可能误判，不能宣称绝对识别。来源不保存原文片段，只保留有界hash/actor依赖/宿主时间。角色设定/工具权限/访问控制不能写成群记忆规则覆盖系统。

inbound：有效speak/silent都可validated→committed，不以发群成功为条件；mentions来源只当前新消息，free来源为effective窗口。acked_bot：validated→pending_ack→committed/discarded，ack_parts必须非空且全部对应正常文字part的sent+message_id；failed/unknown/超时discard，partial只提交全部依赖满足的提议。普通bot回复不自动成为用户事实。

txn_id固定request_key+proposal_index+输入base_revision+phase+generation，CAS不得重算；有效批次一次原子replace，事务标记同写。同批冲突按上述单/多值规则只接受首个有效操作；CAS后add只允许不冲突的事实或宿主可验证的较新单值更新，replace/merge要求目标revision完全等于输入，冲突则拒绝、不重调模型。重启丢弃所有未提交pending，保留已提交事实/marker；不追补模型/ACK或群发送。所有当前pending关闭/过期后，128个marker才可轮转；迟到ACK还查request已关闭和generation，不能只靠marker是否存在。

last_confirmed_at取来源宿主received_at最大值；同source hash在重复窗口出现不增加证据、不续TTL/置信度，召回也不续期。过期清理→candidate优先淘汰→未pinned低置信度/低类型优先级/较久未确认→record ID稳定打破平局。类型优先级convention/background > name > preference > temporary；不是按模型自报重要性。pinned最多4条/1KiB，人工超限拒绝；pinned仍可被隐私/黑名单删除。

每次成员删除、全群clear、黑名单净化先持锁，在同一次原子写入中轮换整群generation、删主记录/清pending并持久写purge intent，再净化副本/索引/缓存；clear保留新generation空壳，旧ACK不能重建。启动先检查purge，未完成时禁读并继续本地净化，绝不恢复旧backup；全部净化成功后才清intent。净化期间不创建含旧数据的新备份。若首个intent都无法持久化，报告删除未完成并关闭该群当前读写，不能宣称重启已保存该意图；需本机排除存储错误后重试。其余任一步失败保留pending/blocked intent，文字继续。正常主JSON预留2KiB purge空间，暂存替换空间也预检，不能用尽配额后才发现无法登记删除。合并来源actor依赖不截断，超上限拒合并；固定主文件64KiB/事实16KiB/64条/32主体、全模块16群8MiB含副本/tmp/pending配额及持久HMACkey沿用PLAN7。MD首版只读导出，本机确认/固定/纠正/删除均走JSON同一锁/校验，不导入任意MD。

## 8. 清理状态、重启和31A/31B出口

31A：原结果与observed_empty/owned_alive/identity_unknown及coverage分开、一个cleanup task接管、总deadline默认5秒、PID/create_time逐项处理、有界台账、被动check、脱敏诊断及legacy正常成功回归通过，可标“31A独立实现/离线通过”。31B容器未通过仍是未完成，不能把“日志更详细”写成清理问题完整解决。

31B：自造进程证明执行前入Job、无breakaway、句柄生命周期/失败清理、active_count归零、外部进程不受影响，只证明容器实现离线能力；job_complete必须取自该次请求实际纳入容器及退出的证据。真实CLI组合另验证，未授权不执行。历史台账写过coverage=job_complete不是重启后的退出证明；重启必须重新取得可验证容器或退出证据，否则unknown继续阻断。观察集合空只能证明observed_empty，不能自动改job_complete。

被动check不kill、不生成、不补发旧答，清理task未结束不再启动模型。完整覆盖未知不自动解锁，不删marker/改后端/扩大到全局进程。Create/Assign/Resume失败也由同一个cleanup task回收已创建/挂起进程和句柄。能力不足先完成31A、记录31B缺口后回规划；实施方无须为已写清的失败分支重复开设计任务。

## 9. 配置与回滚的可执行合同

schema3外壳保留；所有新增开关默认false。新增私有材料token、记忆key、视觉证明/清理台账只在项目secrets/state忽略文件；本轮不生成。视觉status是只读派生值，从公开配置移除；配置中的vision.input_reserve_tokens只是有限参数，不能替代证明。

回旧代码前提供本机`export-legacy-config`等价动作：在停机/配置锁/双摘要下，从当前设置生成可审阅旧schema3兼容副本，移除本任务拥有的新section/键（尤其participation.attention），保留其他旧值/未知非本任务扩展字段；原设置完整备份，确认兼容副本后才能激活。不能只设enabled=false留下旧代码会拒绝的未知键。旧历史、memes、ACK/pending、REMOTE_RESULT_UNKNOWN、CLI未决身份及群记忆不删除。

代码回滚只在受管清理已结束或unknown已按合同保留阻断后进行，不能借旧版本忽略新台账恢复接单。若旧版不能尊重未决清理，保持停机直到独立确认退出。数据schema只读或版本不支持时拒绝写入，不能自动空库覆盖。

### 9.1 文件与分阶段所有权

| 阶段 | 必须涉及的实现面（模块名可等价拆分） | 此阶段不提前做 |
| --- | --- | --- |
| 31 | workbuddy_cli_runner/model_gateway/process_host/manage、cleanup身份/Job辅助、test_lap31/verify_lap31/本任务报告 | 不改人设/触发/图片/成员/记忆；31A和31B分开记录 |
| 27 | participation/group_protocol/provider/contracts/persona/turn_budget、可信identity/dispatcher/v2共用结构、配置/菜单/示例、test_lap27/verify_lap27 | v2为未交付功能保留空字段；不开下载/RPC/持久记忆；材料服务仅可留固定接口骨架 |
| 28 | gate内固定图片材料服务、专用认证/cap、blob规范化、两runner原生输入、能力证明/预算与验证命令、test_lap28/verify_lap28 | 不做任意图片发送、视频音频/成员或记忆；首版多图仅按消息顺序选第一张，不失败换图重试 |
| 29 | gate固定成员服务/阈值/RPC策略、候选目录、v3 PreparedPart/guard/delivery/ACK、配置/菜单与test_lap29/verify_lap29 | 不扩大人数来源、全量prompt、任意@；不要求vision生产启用 |
| 30 | memory schema/store/检索/校验/事务/本机管理、v2同次proposals、配置/菜单与test_lap30/verify_lap30 | 不要求members生产启用，不读取旧history当来源，不增模型/向量库 |

各阶段均按实际变更同步README、对应任务HANDOFF/PROGRESS/TASKS及新报告；不改其他session文件，不覆盖旧报告。本轮规划只修改文档，不创建上述源码或实施HANDOFF。

## 10. 最低验收矩阵（全部待实施）

| ID | 任务/通过条件 |
| --- | --- |
| ATT-01—03 | v2封闭schema/source与effective digest、回复对象、坏aux隔离；身份失败不抢救@/记忆 |
| ATT-04—08 | 冻结target/依赖、入站60秒与排队过期、每群滚动candidate额度、Q/R保留槽/FIFO与单活动、ACK对象归因 |
| ATT-09—12 | 最终裁剪引用闭合、web/meme单锚点、所有开关/模式矩阵、旧配置导出回滚 |
| VIS-01—04 | 黑名单零下载/SSRF与炸弹/尺寸hash；cap伪造/并发/重放/错用途；原生runner一次输入；证据状态/版本失效/未知上界不启生产 |
| MEMB-01—04 | 49/50/51/未知；cached received_at不能当fresh；双TTL/生成中失效；真实@同文字单ACK且无RPC旁路 |
| M01—03 | 记忆schema/配额；self→active/peer→candidate/管理员群背景/pinned；mentions旧history不升格且大群无名册仍能记当前sender |
| M04—06 | speak/silent入站、partial/unknown承诺；CAS/重叠/marker；clear/黑名单generation、迟到ACK、重启pending丢弃 |
| M07—09 | 同source不续TTL/召回不强化；裁剪后source/fact失效；输出截断/坏aux/磁盘错无额外模型且正文可用 |
| M10—12 | 副本删除失败/pinned隐私删除；第17群/8MiB/tmp/marker/pending上限；新功能全关v1与组合单次生成 |
| CLEAN-01—06 | 正常/慢/多层/快速spawn、AccessDenied/PID复用、success+cleanup fail/原超时、重复cancel/close、阻断零新CLI、31A/B分开与重启证明 |

每个ID在新任务报告映射具体测试/结果；实际run_agent/两runner底层替身/原event ACK覆盖受影响路径，不能用手工成功metadata代替。新报告分别`reports/lap-31-*`、`lap-27-*`、`lap-28-*`、`lap-29-*`、`lap-30-*`，对应独立verify入口；不覆盖旧报告。真实样图、成员API/QQ/模型/启停另指定唯一执行人/范围/预算。本轮仅文档检查，表内没有任何“已通过”。
