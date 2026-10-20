# LAP-35：群临时停言、真实@恢复与重启复位

返回[HANDOFF](HANDOFF.md) / [medium指引](IMPLEMENTATION_GUIDE.md) / [PROGRESS](../../../../PROGRESS.md)。配置文件第一项见[LAP-34方案](../LAP-34/PLAN.md)。

2026-10-20（Asia/Shanghai）；详细规划，未实现/未启用。用户明确本会话为Max规划职责、后续由medium实施；模型/档位由操作者设置，不声称自动检测或切换。继承[AGENTS](../../../../AGENTS.md)。

## 1. 需求与非目标

每个授权群独立有普通normal/哑巴muted两种临时状态。非黑名单群友明确要求肥鱼不要参与讨论，本群立即停止输出；下一条非黑名单群友的真实@恢复普通，同一条@进入原回应流程。bot关闭重启或电脑重启，回普通。普通表示按当前配置的mentions/free及原有限额工作，不代表强制把mode改成mentions或free。

停言/恢复均无需管理员资格；黑名单、授权群、当前bot身份及自身消息过滤先执行，管理员也不豁免。只暂停对应群，不能影响其他群。

不增加额外模型分类调用，不依靠模型记住停言，也不改变persona；不设自动解除倒计时，不因聊天继续、叫名、回复引用、上下文重置或网络重连自行恢复。不新增定时主动任务、后端/账号/额度来源/付费API，不清除真实unknown/cleanup阻断，不删除长期记忆/本人历史，不处理QQ平台自身的群禁言解除。

## 2. 当前源码证据与影响

基线`main/29f75ff`；只有用户persona未提交差异，正文不读取不改写。下面均为源码取证，不是已运行/真实验收证据。

| 位置 | 证据及必须处理的影响 |
| --- | --- |
| [gate](../../../../src/qqbot_gateway/onebot_gate.py) `admitted_message/_incoming` | mentions在身份过滤后要求真实at，否则不转框架；非@停言需要本地控制入口，与普通聊天准入分开 |
| 同文件 `DedupStore.reserve` | 以bot/group/message_id持久去重，不存原话；状态变更必须在有效身份/去重后发生，重放不能重新唤醒/停言 |
| 同文件 `_outgoing/allowed_action` | 允许的send_group_msg/send_msg最终在此转NapCat；只在router放bool拦不住已排队输出，必须在gate作最终栅栏 |
| [Participation](../../../../src/qqbot_gateway/participation.py)、[Attention](../../../../src/qqbot_gateway/attention.py) | 有群epoch/候选取消/队列失效；invalidate与连接变化有关，不能拿这些短生命周期窗口保存哑巴状态 |
| [router](../../../../plugins/qq_router/main.py) `on_mentions/on_free_group/on_attention_group` | 三条分支、普通提示及记忆提交路径均存在；当前delivery_allowed在纯mentions单条路径缺少群请求epoch，需另加停言代际 |
| [EventSendGuard](../../../../src/qqbot_gateway/event_guard.py)、[ReplyDelivery/EventReceiptProxy](../../../../src/qqbot_gateway/reply_delivery.py) | 原event、文字/图片/typed@与逐条ACK已有保护；local_notice目前不经过receipt代理，必须覆盖；不能只封模型正文 |
| router `on_mentions`及[任务账本](../../../../src/qqbot_gateway/task_store.py) | single/无扩展有旧简单发送路径；启用停言时也须转已有受控投递/ACK路径，避免抑制后把未发送助手正文留入历史 |
| [model队列](../../../../src/qqbot_gateway/model_gateway.py)、[SSH runner](../../../../src/qqbot_gateway/ollama_ssh_runner.py) | 主动中断已提交远端调用可能形成REMOTE_RESULT_UNKNOWN；本需求是停止输出，不得为停言强行取消远端造成其他群全局阻断 |
| [session_version](../../../../src/qqbot_gateway/persona.py) | 当前复制整个participation入哈希；新增本地控制字段须明确排除，运行态停言尤其不能进入persona/上下文版本 |

## 3. 明确的行为合同

状态由gate进程中的每群内存状态机唯一持有。用户说的“bot重启”落实为停言状态owner所在gate进程重新创建（完整bot/系统重启必然包含）；AstrBot/plugin/model单独重连或重载但gate仍存活时继续保持哑巴。gate真的重启时产生新boot_id、丢弃旧状态/签名密钥，所有群普通，旧门票全部失效。

| 当前状态 | 当前新消息/事件 | 结果 |
| --- | --- | --- |
| 普通 | 有效群友的明确停言要求，无论是否@ | 本群进入哑巴，递增输出代际；本消息不入框架/模型，不发“好的/收到/我闭嘴了”或表情 |
| 哑巴 | 新的明确停言要求（含同时真实@） | 仍哑巴；本消息不作为唤醒，重复停言幂等 |
| 哑巴 | 有效群友真实@且不是停言要求 | 本群恢复普通并递增输出代际；该@本身按原must-reply流程处理，不额外发恢复通知 |
| 哑巴 | 普通消息、叫名、单纯引用bot、文字伪@、@全体/@别人 | 仍哑巴，0框架/模型调用/输出；不向RAM窗口、材料服务或学习新增该消息 |
| 任意 | 黑名单/非授权群/自己/私聊/伪身份/重复事件 | 不改变状态、不转框架/模型/新增历史；保留原过滤合同 |
| 任意 | QQ离线、WebSocket重连、断线恢复、普通上下文重置 | 不解除哑巴；连接/票据仍按原合同失效 |
| 任意 | gate进程/完整bot/电脑重启 | 本群回普通；不补发旧任务、不读取磁盘上的旧哑巴快照恢复 |

同一条消息先判断明确停言，再判断真实@恢复。例如“@肥鱼，先别说话”必须停言/保持哑巴，不能先唤醒再回答。除非当前消息同时有新真实@，单说“肥鱼可以说了”不能解除，这是用户指定的恢复条件。

恢复后是完整普通状态：配置free时后续新群消息可继续自然参与，配置mentions时仍只回复真实@；不是仅放行一次。@无文字时按原空@提示处理；用户不在黑名单即有唤醒资格，不要求是发出停言的那个人。真实@只认当前OneBot原始message数组中指向当前bot.qq的at段，不认raw_message字符串、适配器展开引用或嵌入转发中的at。

新消息顺序以gate实际接收、验证并去重后的顺序为准；不声称能恢复QQ服务端未提供的全局因果顺序。不查询QQ历史补判断；旧事件重放、旧模型结果和旧ACK都不是新的恢复消息。

## 4. 停言表达识别：本地受控规则，无额外推理

只读当前群友本次直接写下的text段，结合原始真实@和配置别名判定。先严格基础身份/群/黑名单检查，再做有界本地识别，早于合批、冷却、队列、材料RPC与模型调用；控制指令不受普通闲聊评估节流而漏处理。mentions里新增的非@本地识别不会把其他非@消息放进AstrBot或模型。

采用高精度、可审阅的句式规则，必须同时满足明确bot对象+要求暂停说话/参与的命令语义；不能只搜“别/肥鱼/闭嘴”关键词。目标指向来自当前真实@或已有participation.attention.aliases（即使attention.enabled=false也只用于本控制识别，不开启叫名回复）。中文别名按受控句式对象位置识别，英文别名大小写折叠且有词边界；NFKC/空白归一化，正则转义别名，不从人设自动猜新别名。

允许的核心结构：直接称呼bot后否定“说话/发言/插话/插嘴/接话/参与讨论/加入讨论/掺和”；“别/不要/先别让或叫 + bot + 参与类动词”；称呼/真实@后肯定要求“安静一下/闭嘴/暂停发言”。“先/暂时/这会儿/请/麻烦”等修饰及明确礼貌请求“能不能/可以先……吗”可以识别。否定作用域必须区分“别让肥鱼参与”和“别让肥鱼闭嘴”，后者不触发。

| 必须识别为停言 | 必须不识别为停言 |
| --- | --- |
| 不要让肥鱼参与讨论了 | 不要让肥鱼闭嘴 / 肥鱼别不说话 |
| 肥鱼先别插话了 / 大肥鱼这会儿别掺和 | 肥鱼不是不让你说话 / 不用阻止肥鱼参与 |
| 能不能让肥鱼先安静一下 | 为什么不让肥鱼说话？ / 肥鱼为什么不说话？ |
| @当前bot 请先不要说话 | 你先别说了（没有明确bot对象） / @其他人 别说了 |
| 肥鱼闭嘴 / 肥鱼先别参与这段讨论 | “肥鱼闭嘴”这句话不礼貌 / 有人说肥鱼别参与 |
| 肥鱼，这段讨论你先别参与了 | 如果有人说不要让肥鱼参与就…… / 举例：肥鱼别说话 |

去除成对中文/英文引号、行内/围栏代码与引用行中的被引述材料；对于条件、假设、转述、讨论句式及嵌套/多重否定不明确的候选子句采取不触发。礼貌形式的直接请求不能被普通问号规则一刀切排除。回复/转发/附件/网页/记忆/模型正文均不作控制来源，不补拉引用内容；若消息同时带reply但当前新写正文明确指定bot停言，仍可识别正文。

字符处理使用既有message_max_chars上限，完整当前text超限时不截成一个看似独立命令；不执行控制，继续原超长输入合同。识别函数纯函数、无网络/模型/磁盘副作用；测试覆盖正反例和否定作用域。此版不保证理解任意自然语言隐喻或讽刺；无法确定就按原聊天合同处理，不额外问确认、不调用第二次模型。新增句式仍须有明确对象/语义及反例测试，不能自行改成任意情绪词触发。

## 5. 状态、代际及输出门票

不能只检查muted bool：停言前的模型结果可能在下一次@恢复后返回。必须使用不回退的每群generation，使旧结果永远不能借新状态发送。

gate启动创建随机boot_id和只在进程RAM中的32字节HMAC密钥；每个授权群状态为`mode=normal,generation=0`。normal→muted、muted→normal各递增一次；已经muted再停言不重复递增；正常普通消息/@不改代际。群状态仅对授权群分配，不因TTL/冷却/重连驱逐或重置，以免重新接受旧门票。状态主数据不落盘、不进入配置/数据库/模型历史。

每条实际转入框架的新消息，gate附加私有输出门票`qqbot_output_ticket`；原事件自带的qqbot_*字段先剥除，mentions旧快速透传在本功能开启时也走净化/签发路径。门票只保存在该event私有上下文，不进入prompt、source-effective manifest、session_id或模型产物。

门票格式为base64url规范JSON载荷与HMAC-SHA256签名（以点分隔），总长≤2048字节。闭合载荷字段为`v=1, boot_id, connection_id, bot, group, sender, message_id, generation, expires_ms, nonce`；身份沿用规范数字字符串/message_id长度约束，generation/到期为非bool整数，nonce为随机16字节。到期使用本进程monotonic毫秒；有效期固定`chat.session_queue_timeout_seconds + 210秒`（原provider上限180秒+30秒发送余量），无额外配置。解析校验类型、签名、当前boot/连接/群/发件者准入、当前normal与generation、到期及目标group，任一不符拒绝。单次/幂等仍由既有event代理和逐条投递账本控制，不将这个可跨气泡的代际票误称为一次性发送许可。

在原event.send及per-event EventReceiptProxy上携带门票到gate；必须覆盖正文、single/adaptive每条、图片/仅图、typed@、普通/错误/冷却/空@提示与失败图片提示。保持原event/同群/无引用的发送路径，不增加裸API旁路、不patch共享CQHttp或AstrBot类。typed@的qqbot_mention_permission与门票并存、分别验证，不能因新增参数破坏原精确字段校验或放开任意@。

gate对send_group_msg和send_msg(group)均先做原范围/段校验及门票检查；发往NapCat前在该群async锁中再次核对mode/generation。停言/唤醒状态转移用同一群锁，以提交send到下游这一点为线性化界；不持锁等待QQ ACK，不跨群持锁，网络写入有界。内部门票参数在发给NapCat前剥掉，不能透传给QQ。get_status/心跳/只读管理等原能力不因静默丢掉，静默群的材料/模型请求则在准入前被拒绝。

拒绝返回固定本地协议错误`GROUP_MUTED_OR_STALE_OUTPUT`，只有请求端得到，不能生成群内解释/二次错误；缺门票也拒绝，不为旧发送路径加逃生例外。签名密钥/门票/原话/真实身份不记日志。既有ScopeDenied等非本功能错误保持原分类。

## 6. 跨进程失效、在途消息与ACK

gate先在RAM变更/撤销旧代际，最终发送栅栏即刻生效。为router及时取消等待，在既有忽略`state/gate-connection.json`发布只读状态镜像：协议版本/boot_id/enabled、每授权群的散列ref→mode/generation。ref为固定域分隔的bot/group哈希，不直接写群号或原话；镜像不是恢复源，新gate不读取旧状态。原身份/更新时间核对保留；写失败沿用通道失效处理，不能回退为“允许输出”。

router在两种mode都启用现有有界元数据监测（约100ms，无网络/推理），保留每个event收到时的代际/门票，禁止发送前替换成当前最新门票。转移时仅使该群旧候选、router本地等待ticket、未提交provider请求的调用及RAM关注/焦点失效，唤醒后从当前@和后续新消息开始；哑巴期间不积压素材，恢复后不补答。其他群继续原队列。断线清窗口/票据，但不清gate的哑巴主状态。

所有valid/delivery_allowed路径加入boot/代际/当前状态检查；metadata缺失、过期或不匹配时不能推断普通并出声。memory_allowed同步检查本地可观察代际：哑巴期间的新消息根本不进入学习；已观察失效的旧proposal不晋升，停言前已完成事实/历史不回滚，不把停言当purge。

仅取消router本地尚未提交provider/model_gateway HTTP的等待工作。HTTP一旦提交就视为可能已开始，包括仍在ModelQueue内部排队的请求；本任务不通过跨进程猜测started或取消HTTP去抢停，允许该次请求按原超时/清理协议收束，丢弃不能再投递的结果，不主动断开SSH/流、不另启生成。因此“哑巴期间0模型”指不因新的哑巴期消息提交新请求，不抹去停言前已提交的请求或额度。不保证已经开始的推理额度可退回。真实REMOTE_RESULT_UNKNOWN或清理失败仍按原合同处理，唤醒不是解除这些阻断的授权。

启用本能力时，纯mentions/single也进入已有受控投递与ACK账本：输出仍是一条，模型协议不为停言增加新字段。停言前已ACK成功的部件保留事实；已准备但未发的部件取消/失败为未发送，不写入助手正文或假表情历史；发送结果未知仍unknown、不重发。普通本地提示也经每event门票代理，不能留一个直接event.send遗漏。

使用独立本地`needs_guarded_delivery`标志/判断贯通on_mentions建账、preserve_gateway_text的成功/失败分支、deliver_reply与finally修复；不能为了复用ACK将纯文字强行标成qq_media_turn或把session_id改成qqbot-media，那会改变模型协议。沿用已认证网关原文字和现有trusted_plan的single解析/降级，仍一次生成、单条输出。已知未投递的助手文本通过现有事务/修复移除，已ACK事实保留；实际框架验证必须覆盖自动保存先后顺序。

已提交NapCat/QQ的消息无法收回，可能在停言被处理后才在客户端显示。保证的是停言线性化后不再提交新的本群发送；在途ACK照常关联并诚实记录sent/partial/unknown，不谎称撤回、不补发、不用重试修正。显式gate拒绝且确认没有转下游的部件属于已知未发送，应有固定失败分类，不能错误标unknown或把本群/全局永久锁住；确实已发无ACK仍unknown。快速停言→@→停言及延迟ACK必须验证。

## 7. 配置字段、默认、生效与LAP-34衔接

唯一新增用户设置：

```yaml
participation:
  silence:
    enabled: true  # 允许群友明确要求本群临时停言；下次非黑名单真实@恢复
```

`participation.silence.enabled`为布尔值，缺省true；实施后新/旧配置内存补齐，正常下次启动生效，不自动写本机文件。true只开启控制能力，各群初始仍normal，不是默认哑巴。设false并重启关闭整个临时停言能力，普通聊天保持原合同；不能通过写`muted: true/false`保存状态。恢复方式、无TTL、重启复位及非黑名单普通成员资格是固定合同，不增加自选参数。

别名复用`participation.attention.aliases`，enabled=false时也只用于停言指向识别；无另一个aliases来源。添加/改别名仍按原停机编辑/重启生效。

建议先实施34，再在35扩展`config/local/chat.yaml`与`config/examples/chat.yaml`注释/校验；旧单文件模板对应同一路径。34与35各自独立领取/提交，不能在一个实施session同时领取两项。若用户选择35先做，支持现有单文件，不创建第二个配置目录；之后34迁移必须保持silence设置与其他字段，不依赖原34规划时的字段全集做丢字段映射。

`validate_participation`新增SILENCE_DEFAULTS，拒绝未知/错误类型；GateConfig与项目/启动快照显式携带开关、别名和门票期限所需的队列配置。能力开关属于本地准入/投递控制，不进入模型persona或session_version的participation投影，不因增加字段、静默/恢复或运行态generation制造新聊天版本；当前规范化配置/source digest仍记录实际值。不能把门票、状态镜像或静默命令放入群长期记忆。

LAP-34布局导出/回滚继续导出完整schema3（含silence），不剥功能；要回退到35之前的代码，旧严格participation validator不认识silence，须在停机/锁/备份/双摘要审阅下使用功能兼容导出移除该节，或恢复对应代码检查点的配对配置。现有`export-legacy-config`扩展剥除此节，split时仍遵循34先受控布局回滚、后功能兼容处理，不直接改快照。用当前新代码禁用应显式false，不能靠省略enabled（省略会补true）。

## 8. 涉及文件与任务顺序

| 步骤 | 文件/职责 | 完成出口 |
| --- | --- | --- |
| S35-01 | 新`group_silence.py`、participation.py/config.py、配置模板/索引、纯函数测试 | 句式/否定反例、默认开关、RAM状态、票据类型/签名/代际/到期与配置兼容 |
| S35-02 | onebot_gate.py、gate/协议测试 | 基础身份与普通准入分离、去重后控制、元数据净化、静默期零转发/材料、最终群锁栅栏/拒绝分类/状态镜像 |
| S35-03 | plugins/qq_router/main.py、event_guard.py、reply_delivery.py、task_store.py及队列需要的局部失效接口 | 三分支/提示/媒体统一门票，旧任务永不复活；启用时single受控ACK；不主动取消已提交远端/不影响他群 |
| S35-04 | persona.py、scripts/manage.py状态展示、configure_bot.py旧导出、README/项目目录说明、34实现后的chat模板/索引 | 不改人设正文/会话版本；本机只读状态、旧导出/回滚、5文件层级一致；不开新cmd |
| S35-05 | tests/test_group_silence.py及受影响测试、独立verify_lap35.py、reports/lap-35-*和本交接/索引 | SM-01—12、两后端实际框架离线、差异/隐私与Git交付，真实/完整未验单列 |

实施可按既有风格拆模块，不改变QQ客户端可见内容合同或模型输出JSON协议，不添加第二分类模型；本项目内部新增门票字段不对外透传。任何无法贯通所有发送路径的能力缺口，先完成独立部分并保持本能力不能激活，记录缺口回规划；不得仅做router bool就宣称完成，或在缺门票时默默裸发。

## 9. 验证与验收

仅自造身份/文本、临时目录、假OneBot上下游与两runner底层替身；不使用私密群消息、真实bot/模型/SSH或本机配置。本轮只检查规划文档，下列为后续实施待执行。

| ID | 验收合同 |
| --- | --- |
| SM-01 | 正反句式表及同义修饰、否定作用域、礼貌请求、转述/条件/代码/引号/长文本；不把模糊情绪/对别人说话当停言 |
| SM-02 | normal→muted→真实@normal状态矩阵、同条@停言优先、重复停言幂等/重复事件不变；不同人可唤醒；恢复后free/mentions各按原合同 |
| SM-03 | 黑名单在识别/去重/RAM/框架/材料/模型/历史前过滤；自己/非授权/私聊/伪身份无控制权，管理员不豁免；群A停言不影响B |
| SM-04 | 哑巴期间名字/引用/文字伪@/@全体/@别人/定时/超时不恢复，0框架/模型/网页/材料/学习；原始当前真实at才恢复 |
| SM-05 | 只断WS、QQ离线、插件/框架/model重连与上下文重置不解除；gate/完整bot/OS式新进程初始化恢复普通，旧镜像不恢复旧状态，旧boot门票拒绝 |
| SM-06 | mentions非@停言能在入口识别，其他非@不进框架；free在合批/频率/排队满时仍立即停言；停言消息0模型/确认消息/表情 |
| SM-07 | 队列中、生成中、气泡间隔、图片前、typed@、本地错误/空@/冷却/重置提示均守门票；无门票/错群/错身份/改签名/过期/旧连接失败，参数不泄给NapCat或模型 |
| SM-08 | 停言后@恢复，旧模型结果仍不可发送；快速多次切换、入站/出站锁竞态与群隔离；在线性化前已提交的ACK延迟据实记账，之后零新提交 |
| SM-09 | 已知gate拒绝无下游发送记未发送，非unknown；真正ACK未知仍unknown且不重发；single/adaptive/仅图/partial历史与提示正确、不生成假助手记录、不清旧账本 |
| SM-10 | 仅取消router本地未提交provider HTTP的工作；已提交请求（含ModelQueue内部等待）/两runner自然收束、结果丢弃，不因停言主动造REMOTE_RESULT_UNKNOWN/CLEANUP_FAILED；原真实阻断仍保留；他群无全局取消 |
| SM-11 | enabled true默认/false兼容、严格类型与未知字段；单文件/34分层模板/迁移/布局导出/旧功能导出；silence与运行态不进入persona/session_version，原角色文件不改 |
| SM-12 | 实际AstrBot框架完整事件/发送回执矩阵：mentions/free，attention关/开，single/adaptive，媒体/成员/记忆关键组合，两个后端实际runner底层替身；状态镜像缺失/写失败不放声，日志无原话/真实ID/门票/秘密 |

先新测试与受影响gate/participation/attention/配置/投递/历史测试，再适用单元全套。独立verify_lap35复用当前实际框架夹具，不运行可能触现场的旧verify主程序；证明真实EventSendGuard/receipt代理/异步回执链，不能只单测状态机或手动调用send方法就算全部通过。

离线通过只记“已实现/离线通过”。真实人工验收待明确授权后，由两名非黑名单群友验证一句停言、无输出、另一人真实@恢复、重启复位及另群隔离；不为此读取黑名单原话或自动发群消息。QQ视觉接受/时序与真实自然话识别、在途可见延迟、原模型效果和旧任务差额未验不能关掉。

## 10. 回滚、失败分支与交付

关闭新能力：操作者停机编辑silence.enabled=false后正常启动；所有群按原普通流程，状态不恢复。不自动改本机配置、不代为重启。回旧代码前先停机、处理原投递/cleanup/远端unknown兼容边界、完整备份并用第7节配对配置；不能让旧代码误读未知silence字段，也不能用重启/唤醒清掉真实unknown。

新实例自动normal是用户要求，只复位这个群参与状态，绝不重放或清账本。状态镜像/签名解析失败、代际未知或gate不支持时拒绝相关输出；普通校验失败沿用原本机提示，不向哑巴群发错误。gate和router能力必须成套验证，保留旧能力差额。

本轮交付6份规划/交接/索引文档，不改34已完成文档或任何代码/模板/配置；按长期Git授权审阅commit/push并核对SHA。后续medium按[实施指引](IMPLEMENTATION_GUIDE.md)执行，34和35分别会话实施。未实现的本地表达覆盖率、跨框架门票传递/ACK竞态与真实QQ效果均明确待验，不靠设想标通过。
