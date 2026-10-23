# LAP-39 夜间不回复诊断与恢复对照

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承AGENTS。

状态：2026-10-23 20:15现场已恢复、对照通过。旧QQ/NapCat会话异常/状态失配导致消息链路失活，重建并由操作者扫码后，原生资料刷新由10062ms超时变250ms成功，自身协议状态由失败变在线；用户另行正常启动，3条新消息完成/2条sent回执。腾讯风控/普通会话失效/客户端缺陷的最初诱因仍未能唯一判定，过夜稳定与长期修复未验。WebUI管理凭证到期与此分开。agent仅受管stop及暂停转发的channel启动，未自行请求模型、发群消息或代填QQ凭据。

session `LAP-39-overnight-no-reply-diagnostics`，2026-10-23 18:40（Asia/Shanghai）开始只读排查，18:46登记文档归属。用户指定sol high排查凌晨正常、早上约08:30无回复及疑似登录丢失；不声称自动检测或切换模型/档位。

开始基线main/`746451cb6d29741f4d32cab416447ae0ec5d5cec`，工作区干净。本session独占跟踪文件仍仅PROGRESS、工作线HANDOFF/TASKS、本HANDOFF；前段只读、没有启停。本次彻底排查续作不改代码/本机源配置/人设，增加现有受管启停命令的恢复对照，运行快照/生命周期记录按现有命令维护；不自行触发模型或发送群消息。项目WebUI管理token只在进程内使用且不输出、不保存，不读取QQ密码或登录票据。

目标：对齐2026-10-23凌晨至早上故障时间的进程、Windows电源、消息入站、模型及QQ状态证据；区分已证实事实、源码推断和缺失历史证据。完成后保留现场，给出下一步最小定位办法。

## 当前证据

- logs/model.log:1545—1547记录00:43:12请求开始、00:43:17生成成功；1566—1571记录06:57:17/31请求，06:57:22/36生成成功且清理reason=none。00:40后并非立刻停机。
- 只读查询state/gate.sqlite的seen时间计数和state/tasks.sqlite的状态/更新时间：最后授权群准入06:57；08:30附近无准入/任务；最后有发送回执的记录在01:51:51。06:57生成成功不能等同已发送回复，当时最后模型结果为ambient/silent。未读取/输出群正文或真实标识。
- logs/gate.log:197在00:22:48完成账号核验连接，此后文件无断线记录。18:42起只读manage.py status --json：四组件存活，channel.connected/online/self_id_verified=true，当前心跳新鲜；model.queue=0/current_error=null/cli_cleanup.blocked=false，cleanup status也blocked=false。排除当前LAP-37清理阻断，但不倒推08:30状态。
- 项目登记PID+创建时间核验：当前NapCat启动器/QQ进程均始于00:22:39—46，AstrBot/gate/model始于00:22:28—38；没有通过进程名接管或操作其他QQ。已登记进程持续存活不等于内部网络全程正常。
- Windows System事件：00:18:47正常关闭、00:19:11启动；00:40以后查询Kernel-Power/Power-Troubleshooter相关事件未见睡眠、唤醒或重启，LastBootUpTime=00:19:11。不能把00:19重启当成08:30失败原因。WLAN/NetworkProfile目标事件查询无返回，并非所有网络层均有日志。
- 通过6099监听PID与项目创建身份匹配后，只在内存读取项目webui.json管理token，对本地固定WebUI进行管理鉴权；CheckLoginStatus返回isLogin=true/isOffline=false/coreReady=true/loginPhase=ready/loginError为空，GetQQLoginInfo与本机配置账号匹配且online=true。当前没有查到登录丢失；不是QQ重新登录或密码探测。
- 当前运行配置与磁盘摘要相同，无pending_restart；配置只读确认free、授权群数量3。不能把历史默认mentions误当成本机当前模式。当前muted_groups=0；私聊仍关闭。
- 项目NapCat onebot11配置mtime仍为10月16日，启用的WebSocket客户端messagePostFormat=array、reportSelfMessage=false、heartInterval=30000；只读未发现夜间配置改写为字符串消息的证据。未读取或输出通信token/连接账号。

## 历史日志缺口

- scripts/manage.py:352起将NapCat fileLog=false、consoleLogLevel=warn；实际项目NapCat logs目录为空，logs/napcat.log仅启动/退出元数据，故障时无可用登录事件。
- scripts/process_host.py的safe_line对NapCat只放行login_event白名单；未覆盖KickedOffLine/SelfOffline/登录服务断连等事件。login_event只处理完整年月日时间前缀，而安装bundle的u5日志格式为MM-DD HH:mm:ss及可选昵称前缀；这是静态可核验的诊断兼容缺口，不是已经证明本次发生掉线。
- 安装bundle La.MAX_HISTORY=100；/api/Log/GetLogRealTime只回放当前环形缓冲，没有历史时间字段。实取缓冲以get_status轮询为主，另有ServerTime及debug adapter元数据，未保留故障时事件；不能用“没看见掉线”证明未掉线。无原始内存日志落盘。
- WebUI与OneBot get_status最终都依赖core.selfInfo.online，属于同一底层状态来源；双接口一致不是独立服务端连通性证明。

## 待核实与下一步

用户补充：早上失败消息在授权群并真正@；刚才的“自己登录”仅指NapCat管理网页输入token，不是重新登录肥鱼QQ。因此不能把当前在线解释为用户重新登录QQ后的恢复，也不能把管理网页退出归为QQ掉线。会话曾暂将“自己登录”理解为QQ恢复，澄清后已明确纠正；初查当前在线与历史证据仍须分开。

19:26续作源码核对与5条合成日志验证：旧完整日期登录提示可保留；安装bundle的MM-DD登录提示、KickedOffLine、Login服务断连及Worker恢复提示均返回None，被现有process_host过滤。没有修改代码。项目startup_fallback仅新建启动时单次检查，目前凭据缺失/disabled，非运行中重登录守护；bundle原生另有KickedOffLine/SelfOffline恢复逻辑，本次是否触发或失败没有历史证据。

已请求用户在原授权群手动发送一次简短真实@并反馈结果，同时本session仅被动读取本地WebUI SSE日志元数据与准入/任务时间统计。正常触发可能调用模型/回复，已明确说明；不能算agent自行发起生成/群发，不能将新测试结果倒推08:30历史原因。不输出/持久化原始群消息、标识或SSE全文。

19:30:01—19:30:51完成50秒被动SSE观察，含100条回放共103条日志，未见新的消息接收/发送或掉线/警告分类事件；多数为状态查询。观察前CheckLoginStatus仍ready，seen最新06:57:29、tasks最新06:57:36，无变化。未收到用户“已发送”回执，故这不是一次已执行的真实@失败复现，也不能推断用户发了但NapCat没收到。短探测先因1秒读超时正常结束，随后完整50秒观察已完成；均无后台遗留进程或原始日志落盘。

## 19:40后现场证据与定位

- 用户确认新测试已发但无回复，并确认发送账号是另一个QQ；不再将自发过滤作为当前解释。19:40:32只读状态仍running/qq_ready/connected，model.control_attempts=16/queue=0/active=false/last_error=null；seen共59条、最后06:57:29，tasks共852条、最后06:57:36。新测试未进入准入/模型层，早上也未出现模型错误请求。
- 此时直接WebUI状态仍isLogin=true/isOffline=false/coreReady=true/loginPhase=ready。SSE最近100条中99条get_status、1条info，无接收消息或掉线分类；这是当前日志窗口结果，不声称保留所有历史。进程创建身份仍00:22，无agent启停或自动Worker重建证据。
- 对最近活跃且仍在授权列表的群，借用已存在的debug-primary，只调用一次只读get_group_member_info，user_id固定机器人自身、no_cache=true；不查别人、不取群历史、不调用任何发送动作。15秒客户端上限，实际10062ms返回HTTP200/包络code=0，但OneBot status=failed/retcode=200、错误类别timeout，无成员缺失或适配器缺失类别。群号/账号/返回资料均未输出或保存。
- 随后SSE只提取固定操作名，确认超时为NodeIKernelProfileService/fetchUserDetailInfo等待NodeIKernelProfileListener/onUserDetailInfoChanged。源码10910附近确认no_cache路径发起原生资料请求并等回调。证据证明该次QQ底层刷新查询超时，不单凭它断言全部原生API均失效或唯一网络根因。
- WebUI CheckLoginStatus与OneBot get_status均读core.selfInfo.online；当前true不能覆盖真实消息收发/新查询活性，现场表现为状态在线但业务链路不工作。故障定位在QQ/NapCat的会话、原生请求/回调或消息上报侧，尚未区分这些底层分支；不是已证实的模型额度/队列/cleanup阻断。
- 只对项目已登记NapCat进程的现有公网远端443地址做最多3次无凭据TCP连接探测，均成功（15/188/15ms）。现有连接统计为2条ESTABLISHED公网443、1条CLOSE_WAIT公网443及本地6200连接。仅说明这些远端端口当时可达，不能等同QQ会话认证有效；CLOSE_WAIT也不能单独证明MSF连接为根因。未探测家庭SSH、未改变代理/防火墙/网络配置。

## 管理网页再次跳登录页

用户报告管理页再次变成登录页；检查前暂停新管理鉴权，先核源码。bundle on.MAX_CREDENTIAL_VALID_SECONDS=3600，validateCredentialWithinOneHour按创建时刻校验；前端index-Bhl_Ql1g.js收到Unauthorized会移除本页localStorage凭证并reload。因此网页会话可因1小时有效期结束退出，与QQ会话分开。未读取用户浏览器凭证的精确创建时间，不能声称本次跳转已通过浏览器时间戳唯一证实为到期。

管理/auth/login仅签发独立凭证、不撤销其他会话；撤销发生于专门logout/修改认证操作。本session未调用这些写操作、未修改token或签名密钥，项目进程未重启。只读查询的管理鉴权不等于QQ登录，也没有源码证据说明它把用户网页踢下线。

前段只读现场已按下节留存摘要，受控恢复对照实际完成，不再重复启停/要求用户@。后续优先修复脱敏掉线日志及健康识别的覆盖缺口，再做长稳观察，不能把当前恢复等同夜间触发原因已证明。不重放旧消息、不补发；当前未改代码、未扩大群正文日志、未自动切框架/后端/系统，未填QQ密码。

## 验证与交付

### 20:08受控恢复前证据与操作归属

用户提供的Downloads/napcat.log为18,811字节、125行、无时间戳的近期导出；109条get_status，包含本session资料查询的Timeout，EventRet为result=0/errMsg空/source=1/detail={}。它证明原生方法接受请求但未等到符合条件回调，不包含凌晨最早掉线事件。原日志不复制/提交。

新增对照：get_version_info成功32ms，当前4.18.38；get_group_list缓存/刷新两次均成功16ms，三授权群均在列表中；get_group_info_ex成功但data=null（不能当远端刷新成功证明）；nc_get_packet_status成功15ms，nc_get_user_status查询机器人自身失败63ms、固定错误“无法获取用户状态”，没有状态数值或底层错误码，不能断言服务端显示离线。均只读，不取历史/别人资料。

按登记PID+创建时间获取的open_files仅stat元数据：项目QQ进程持有nt_msg.db-wal的mtime为06:57:31，group_info/profile_info WAL为06:57:29，与准入停点吻合。外部原生DB未打开/解密、未读票据或群正文；文件mtime是辅助线索（Windows打开文件的落盘时间可能延迟），不将它单独当成完整入站证明。System/Application在06:45—07:15没有命中相关事件；NetworkProfile日志开启、最后记录00:21:57，无对应时间网络切换；TaskScheduler日志关闭，不能据无记录排除定时任务。

用户论坛链接[Koishi 11478](https://forum.koishi.xyz/t/topic/11478)描述Win11 Shell运行2—5小时后掉线，回帖建议Linux，属于社区经验不是本机根因证明。上游[#2071](https://github.com/NapNeko/NapCatQQ/issues/2071)也报告Linux静默离线/WS假活，但当前bundle已有SelfOffline事件及60秒恢复路径，与该帖旧缺口不能直接等同；[#1977](https://github.com/NapNeko/NapCatQQ/issues/1977)同名资料超时案例仍有群消息，说明单项资料超时不等于完全收不到消息。官方最新v4.18.41发布说明未确认修复本机症状，不升级/迁移或承诺Linux解决。npx临时调用defuddle读取讨论，未改全局应用配置或项目依赖。

20:08:43预检：四组件running、28条登记身份均存活，model.active=false/queue=0/control_attempts=16，cleanup.blocked=false，无accepted/running任务；任务计数completed=794/failed=57/send_unknown=1。源配置无待重启/改动。bundle SHA256=f80e4be3e8640369d23846cf3e8bcfd2a5b6dc5920f50d7ad733d7cca18179e6，与LAP-24规划核验一致，排除本轮擅改bundle。

本session唯一执行顺序：现有manage.py stop（只按登记创建身份）→确认组件停止→start-channel --login-check-only（不启动模型、停止入站转发）→固定只读登录状态/同一机器人自身资料查询对照。若需手机验证，保留等待状态交给操作者，不输入密码、不调用额外登录接口；若启停身份不明或清理失败则停止该动作，不按进程名kill。对照后是否恢复原text/free运行依现场就绪与当前授权判断，记录真实动作与结果，不能沿用前段0启停声明。

### 20:10—20:15实际恢复动作与结果

- agent执行manage.py stop正常完成，独立核对四组件均0/stopped；completed=794/failed=57/send_unknown=1不变。随后执行start-channel --login-check-only，三组件启动、模型未启动、gate.stopping=true、can_receive_group_messages=false，未向AstrBot转发群事件。
- 20:11:20原生状态isLogin=false/coreReady=false/loginPhase=waiting_qrcode；启动内存日志有正在快速登录/快速登录错误/转二维码，未取得明确风控错误码。WebUI快速列表缓存中目标missing；不能以此认定真实原生历史被删除。agent未重试快登、未密码回退、未输入/保存凭据，要求操作者扫码。
- 用户确认已完成QQ扫码；20:13:27检查账号与配置匹配，isLogin=true/coreReady=true/phase=ready。此时发现mode=text/model.alive=true/stopping=false与agent暂停启动不同，立即不再启停并询问归属；用户确认“我也启动了机器人”。正常text恢复是操作者操作，不记为agent在暂停模式自行升级。
- 同一授权群、同一机器人自身、同一no_cache=true资料查询：旧会话10062ms failed/200/timeout，扫码后的新会话250ms ok/0，群与bot匹配；nc_get_user_status查询同一bot，旧会话63ms失败，新会话63ms成功，status=10/ext_status=0。这是会话重建+重新认证前后业务能力对照，不是仅比较缓存在线标志；重启与扫码同时改变，仍不能唯一分离服务端认证失效与客户端会话缺陷。
- 扫码后WebUI缓存快速列表仍missing，即使账号已经真实在线。**因此此前missing不能作为凭据失效、历史丢失或腾讯风控的证据**；保留启动快登失败这个事实，不夸大缓存列表能力。该限制与LAP-24旧缺口一致。
- 20:15:06正常text/qq_ready/可收群，queue=0/active=false/last_error=null。20:12:47、20:13:04、20:13:12有新准入，3条completed；20:12:54及20:13:22有delivery.sent回执，另一条无发送记录，不解读为失败。completed=797/failed=57/send_unknown=1，当前实例真实模型3次均generation=success/cleanup reason=none，均由操作者恢复后的正常新消息触发，agent未发送测试消息/自行调用生成。
- 源配置与运行快照摘要均仍6b1f1a108b3654d930e9864f8fe8a060e793b7019f8de1e58c9d410d3bd6c3c1，无pending_restart/source_changed；bundle SHA256未变。没有修改代码、人设、授权群、黑名单、触发范围、后端或费用来源；旧unknown/清理台账与验收差额保留。

结论层级：直接故障为旧QQ/NapCat会话异常、进程/WS/缓存在线造成假活，新的认证会话恢复业务能力；触发时间在06:57以后至用户08:30失败前的窗口（具体掉线时刻缺历史证据）。腾讯主动会话撤销/风控是候选，不能在没有KickedOffLine/通知/结果码时标成已确认“腾讯风控”；普通会话失效、QQ客户端/NapCat状态失配也未独立排除。自身get_status健康检测只看到同源缓存，日志过滤又遗漏诊断，解释了为何长期未自动发现/恢复，但不证明它们是最初诱因。

已执行：只读状态/cleanup/SQL时间状态统计、Windows/身份/文件stat、WebUI固定查询/SSE元数据、授权元数据及自身资料/状态对照、最多3次现有远端TCP探测、5条合成日志、只读上游检索，以及agent一次受管stop/一次login-check-only启动。QQ扫码及正常text启动由用户完成；此后3次真实生成/2次sent为正常群新消息触发。未重跑测试套件，未由agent自行调用生成/发群消息、填凭据或修改代码配置。

现场恢复与真实收发已有当前证据，仍不支持“夜间被踢/特定风控/唯一网络原因”的确定归因；过夜稳定与完整验收未过。保留初查/对照/用户操作归属，不把恢复夸大为风控根因证明，也不将新会话短时成功当成长稳保证。

前段文档提交b55de99/21ea24c/6c430f2均已推送核对；本次续作仍只更新同4份跟踪文档。链接/差异/归属检查后提交推送，最终提交号以会话回执为准。原始导出、运行快照和本机数据不提交；没有修改生产代码或加载日志/健康修复。旧差额与未确认的诱因保留。
