# LAP-39 夜间不回复只读诊断

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承AGENTS。

状态：2026-10-23 19:40—19:46续查定位到QQ/NapCat底层请求/消息事件异常：用户再次以另一个QQ在授权群真实@仍无回复、准入/模型均无新增，原生刷新资料接口约10秒回调超时，但在线缓存仍true。底层故障可复现，夜间具体触发原因未确认；尚未恢复或完整验收。管理网页重登不等于QQ重登。只读诊断由本session独占，agent不登录QQ、不发群消息、不自行调用模型或重启。

session `LAP-39-overnight-no-reply-diagnostics`，2026-10-23 18:40（Asia/Shanghai）开始只读排查，18:46登记文档归属。用户指定sol high排查凌晨正常、早上约08:30无回复及疑似登录丢失；不声称自动检测或切换模型/档位。

开始基线main/`746451cb6d29741f4d32cab416447ae0ec5d5cec`，工作区干净。本session独占归属仅PROGRESS、工作线HANDOFF/TASKS、本HANDOFF；不改代码、本机配置、人设或运行数据，不启停、不执行QQ登录、不调用真实模型或发送群消息。项目WebUI管理鉴权仅为读取状态与内存日志；管理token只在进程内使用且不输出、不保存，不读取QQ密码或登录票据。

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

不重放旧消息、不补发、不重启保留现场。现在不再重复要求用户@或核对发送账号。下一步：若用户要求恢复，先按唯一负责人/项目创建身份重建受管QQ/NapCat会话，再由操作者同群真实@验证；恢复前保留当前定位证据，不能把重启有效等同夜间触发原因已证明。补全受控脱敏掉线日志是已识别的后续修复，当前未改代码、未扩大群正文日志；没有自动切框架/后端或填QQ密码。

## 验证与交付

已执行：manage.py只读状态/cleanup status；SQLite mode=ro仅时间/状态统计；Windows电源/网络事件与进程创建身份核验；本地WebUI状态/账号相等性/SSE元数据读取；一次机器人自身资料刷新只读查询、最多3次当前远端TCP连通性探测；5条合成safe_line验证与源码核对。未重跑测试套件、未调用真实模型、QQ登录、群发或启停。用户手工测试未进入模型层。

现场已缩小到QQ/NapCat底层请求/事件异常，管理登录页与QQ登录分开；仍不支持“夜间被踢/特定风控/唯一网络原因”的确定归因。保留初查证据与用户澄清，不把当前true或一次超时夸大为完整根因证明，也不标已恢复。

初查文档提交`b55de99a5ac953b244328862b76a688e9143ae15`已推送并核对origin/main一致，检查点干净。本次续作只更新同4份归属文档；5条合成safe_line验证、只读50秒观察与文档链接/差异检查后提交推送，最终提交号以会话回执为准。没有修改生产代码/配置，也没有重启加载诊断修复。历史验收差额保留，根因未确认不能标已修复或完整验收通过。
