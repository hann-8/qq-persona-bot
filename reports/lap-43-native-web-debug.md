# LAP-43：原生联网群测故障排查与隔离修复

日期：2026-10-29（Asia/Shanghai）。任务/session：LAP-43 / LAP-43-native-web-debug。

## 2026-10-29最新：后续答复时间线与两项确证修复

11:03:53问题在11:04:05失败（约12秒）；11:05:04带日期的文字属于后续另一请求，0联网工具。“真的查到了”及其对CLI的推测不是联网证据，不能把两段当作一次约90秒搜索。

用户明确允许2次独立真实诊断，实际2/2：第一次5.844秒，细分拒绝为tool_plan_missing；第二次12.578秒，已取得PlayStation官方页4295字节，但Steam公开商品ID被本项目的通用长号码规则误拦截。不是Steam施加的隐私限制。原始合成公开查询与回执仅本机忽略目录保存，不提交群消息/账号。

两项最小修复：工具事件没有完整next()计划时，使用同一CLI公开session.messages逐项核对准确ID/工具名/参数及上下文前缀、数量上限；无对应条目仍拒绝。公共WebFetch网址中的数字资源ID不再误当私密号码；原始URL仍先核对明确私密ID，其余query/prompt/敏感字段不放开。细分拒绝按发生序保存，避免后续native_ready覆盖首个失败点。

用户明确要求不要过度debug后，不再追加真实调用或扩展排查，只完成已确证修复、必要配对部署与Git交付。目前两处修复已部署并正常启动，实际connected/can_receive/router_ready，当前错误为空；识图/记忆/配置保护保持。用户追加不要过度限制或编码，本轮不再增加规则、代码或测试，只完成提交推送。隔离30项通过，含27个SDK场景；第3次没有授权、没有执行。本轮真实最终完整答复仍待用户实测，不称搜索质量已过。

## 2026-10-29 10:42反馈续修（已部署，待用户实测）

c2346cb部署后，用户正常游戏搜索仍失败。10:41:56入站对应10:42:04/eba52f9466，CLI PID179216两次WebFetch仍返回本插件固定deny，没有取得网页结果。本轮检查真实工具参数与首轮模型计划完全相等，公开URL/文本没有命中既有敏感规则或本机私密ID。旧运行没有保留具体拒绝phase，不能追认这条请求命中了哪一个分支。

定位并复现流式时序缺口：锁定CLI getStreamedResponse在response_done时通知turn.step结果，同时继续向主循环交付输出，并未等待Mod后处理完成。工具事件可先于插件从next(e)取得/登记计划到达，旧工具处理立即找不到planned而拒绝。修复以当前步的Promise等待准确计划登记，之后仍执行原白名单/参数/计数/预算，不猜测计划、不重试/加次数。

另外补齐<=8192字节的JSON字符串input封套；解析后必须是参数对象，外层副本存在时完全一致，畸形/数组/null拒绝。trace.toolInput为字符串本身只是日志序列化，完整CLI本地替身观察实际e.input为对象，因此字符串支持是兼容补全，不据此断言它就是用户本次失败原因。

验证：对c2346cb源码运行新增回归，3个JSON参数及2个提前工具事件子场景失败；新源码全部通过，合计21个实际适配器子场景。新增完整锁定CLI工具往返测试：仅在临时插件中固定替换模型next和工具core（均不调用原next），真实CLI控制/事件/消息历史/最终parser经历两次WebFetch后生成固定最终答复，远端生成/公共工具服务/QQ均0，不把替身结果称为真实搜索成功。

隔离30项通过：test_lap43 + test_cli_native_web + test_cli_runner。包含上述CLI往返、21适配器子场景、坏计划/重放/畸形JSON/私密参数拒绝及安全诊断落盘。安全诊断仅覆盖最后一次CLI失败，state/cli-last-failure.json只保存固定枚举、随机trace及计数，不保存原始错误、消息、查询、URL或凭据；失败摘要无法写入不覆盖原有生成/清理结果。

本轮已部署：生产当前check为22项（含完整CLI零生成工具往返）/实际预算/static通过，额外8个runner检查在隔离树通过，合计30项。生产正式零生成probe正例1本地user/0 next，反例0/0 user；完整active绑定已激活，受管正常重启后running/connected/can_receive/router_ready、current_error=null、pending_restart=false。识图试用和群记忆读写true，thinking=false，16项保护不变。

当前binding e8a90ceae7a384e393a9431718c94899ed9e62254208be1e63eba363cd9fcbff；备份/回执state/lap43-web-json-deployment/20261029-1056。最后一次安全失败摘要路径state/cli-last-failure.json（也可能由本地负例probe更新，以trace/类别区分）。

另一个session正修改LAP-44的5份共享/规划文档，本轮均保留，不夹带提交；只从隔离2e0fe73取本次源码/测试/43专属报告到main。当前精确归属/回滚见43 HANDOFF，隔离TASKS保留本轮领取。本段覆盖前轮“两个缺陷即已解决”的推断；真实服务/群回复仍需用户实测。

## 结论

本次具体失败已找到本机证据：模型确实返回了两个WebFetch请求，但项目防护插件均返回固定拒绝结果，随后CLI没有最终答复，网关统一映射为BACKEND_UNAVAILABLE。现有证据不能把它归因于搜索服务宕机或模型账号失效。

定位到两个可独立复现的项目接线缺陷，先在隔离分支codex/lap43-web-debug修复；随后用户明确授权部署，本轮已合入main并正常停止/配对/重启。未改生产运行配置、调用真实模型/联网工具服务或发送QQ消息。

## 本机追踪依据（不附原始私密消息）

- Snow启动日志定位到09:17:38的用户核实请求；09:17:47，model.log记录trace=bdb43eb95e、generation=BACKEND_UNAVAILABLE。09:20:13的另一条请求也呈现同样工具拒绝链。
- 对应CLI PID 187944的本机日志：09:17:45模型开始生成WebFetch，09:17:46两次工具执行在5/7毫秒内失败。其进程trace的两个工具输出均包含项目固定`Native web call refused or unavailable; this request has not verified the claim.`，而非网页结果。
- 随后的CLI日志为EmptyStreamError、No response received from model及error_during_execution。这里的“空流”出现在项目拒绝后的下一步；不能据这句话认定最初远端模型未连接。首轮模型返回工具调用及usage已经存在。
- ResultParser在收到is_error/errors时只保留classify_error结果；runner的生产stderr也仅计数、不保存。故项目model.log本身无法解释该拒绝，具体链由CLI自己的本机日志/trace补回。原始消息、完整trace、工具查询、账号及群号不提交。

## 缺陷一：真实SDK参数封套误比较

锁定CodeBuddy 2.168.0的dispatchModsToolCall在非flat模式产生形如`{url,prompt,input:{url,prompt},tool,tool_use_id,agentId}`的事件。项目argsOf只排除了tool/tool_use_id/agentId，留下额外input，导致它不等于turn.step登记的`{url,prompt}`，工具在调用next前就被拒绝。

修复：只剥离SDK保留字段；遇到input副本，要求它是普通参数对象，且与外层参数完全一致后再用于比较。冲突封套仍拒绝，模型计划、工具白名单、重放及计数检查保留。

## 缺陷二：HTTPS被当成本机Windows路径

旧敏感数据正则中的Windows盘符分支没有词边界，会命中`https://`末尾的`s:/`（HTTP同样命中）。所以即使工具事件用旧测试的flat形状，正常WebFetch URL也会在tool_private检查失败；含公开URL的WebSearch查询同样受到影响。

修复：盘符前增加词边界。Windows正反斜杠路径、UNC和私密长号码的拦截仍经过负例验证；原publicURL、工具结果裁剪及预算不变。

## 修改文件

- adapters/codebuddy_vision_guard/hooks/register.ts：上述两处最小维护修复，不改第三方CLI。
- tests/test_cli_native_web.py：增加锁定SDK实际适配函数的离线回归。先核对bundle SHA256与versions.lock一致，再只提取该纯适配模块，在替身host/替身工具下运行；不启动完整CLI，不加载登录材料。支持QQBOT_TEST_CLI_BUNDLE指定只读安装路径，未安装时该项显式skip；本机本次未skip。
- PROGRESS、工作线HANDOFF/TASKS及43 HANDOFF：登记分支状态、证据、验证和接续。

## 验证结果

1. 修复前，新增实际适配器回归中search/fetch/fetch_parallel/fetch_flat四项均复现核心工具调用次数为0、项目deny和下一步空回答；冲突封套负例拒绝正常。现有纯flat WebSearch替身用例未能覆盖前两种真实接线问题。
2. 修复后12个实际适配器子场景通过：search/search_flat/search_url、fetch/fetch_parallel/fetch_flat/fetch_http，以及冲突封套、Windows正反斜杠路径、UNC和长号码拒绝。正例进入下一步并返回最终合成答案；两个并行WebFetch均执行替身核心，次数/结果/上下文验证仍生效。
3. 当前43定向组合`python -B -X utf8 -m unittest test_lap43 test_cli_native_web -q`：21项通过，含上述12子场景、已有三调用四步骤、结果剪裁/上下文篡改拒绝、图片/文字native链、真实AstrBot事件对象及权限/发送栅栏替身场景。运行18.058秒，真实模型=0、真实联网工具服务=0、真实QQ输出=0。
4. 命令使用生产项目解释器；PYTHONPATH指向隔离树src/tests，QQBOT_TEST_CLI_BUNDLE仅指向生产锁定bundle，QQBOT_TEST_ASTRBOT_SITE仅指向已安装AstrBot依赖。未修改这些只读依赖。
5. 额外探索`test_cli_native_web test_vision_mod_guard`整模块时，旧guard检查被隔离树未安装runtime及固定review不匹配阻断（21项/22个error）；该次不是通过结果，未借机改旧质量记录或扩大修复。最终通过的是上面的当前43定向组合。

## 已部署、剩余与回滚

2026-10-29用户追加明确授权后，正常停止受管实例、快进main，已加载两处修复。部署检查发现能力表仍登记旧插件来源摘要，config/vision-capabilities.json仅同步plugin_assets_sha256为当前实际assets_signature；未改模型能力或上界。随后重新完整check：21项通过、实际预算通过、static_missing=[]；锁定CLI正例1本地user/0 next、反例0/0 user，真实生成=0。

vision/native当前完整绑定12d5f947e863327f278c3977837ffb84164acb35b5f49ec1b86398742660023b已配对激活，active SHA b36ffe0bcf8ca89361d542cc1f1c41243f430b320f31f0b53bfc3c5bcc33ea90。正常启动后已独立复核running、OneBot connected、can_receive=true、router_ready=true、current_error=null、pending_restart=false。识图继续lap43_operator_trial/pending_user_test，群记忆读取/学习true，thinking=false；该次实例复核user_messages_sent=0。

16项运行配置、人设、图库和pending保护摘要不变。保持原模型/账号/额度、3调用/4步骤/90秒、8000/12000结果预算、48000政策、owner/free和访问控制。初次启动回执的通道尚未就绪是连接恢复中的快照，最终status已实际确认就绪；未安装、登录或接管外部QQ。

备份及运行证据：state/lap43-web-debug-deployment/20261029-1024，含部署前代码/保护摘要、active/offline/probe/能力表备份、前后status与deployment-result。回滚先正常停止、确认无后续改动，配对恢复部署前1e607b7代码与对应能力表/offline/probe/active；保留unknown、记忆和日志，不删锁或状态。提交推送main并核对远端后交付，精确SHA见Git及会话回执。

真实搜索服务可达性、网页质量、群答复及ACK仍未由本轮代理验证，由用户正常群测；旧IQ/质量差额不改写。
