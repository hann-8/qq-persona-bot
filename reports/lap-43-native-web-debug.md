# LAP-43：原生联网群测故障排查与隔离修复

日期：2026-10-29（Asia/Shanghai）。任务/session：LAP-43 / LAP-43-native-web-debug。

## 结论

本次具体失败已找到本机证据：模型确实返回了两个WebFetch请求，但项目防护插件均返回固定拒绝结果，随后CLI没有最终答复，网关统一映射为BACKEND_UNAVAILABLE。现有证据不能把它归因于搜索服务宕机或模型账号失效。

定位到两个可独立复现的项目接线缺陷，已在隔离分支codex/lap43-web-debug修复；生产main/1e607b7尚未更新。未启停bot、改生产配置、调用真实模型/联网工具服务或发送QQ消息。

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

## 生效、剩余与回滚

修复仅存在本隔离分支，生产工作区保持干净，bot运行态未操作。未改变模型/账号/额度、thinking=false、3工具调用/4步骤/90秒、8000/12000结果预算、48000政策、访问控制、owner/free、人设或记忆。

下一步若部署，沿已有43配对流程：确认生产无新修改及唯一执行归属；正常停止受管实例；合入本分支，使用当前实际配置重做固定技术检查及CLI零生成正反接线，更新完整vision/native试用绑定后再正常启动、复核health/连接。旧binding不能直接冒用，不能为了上线静默关闭识图。真实搜索服务可达性、网页质量、群答复及ACK仍未被本轮离线验证证明，应由用户正常群测。

回滚本隔离成果不影响生产；后续若部署，必须配对恢复旧代码/active及该次部署备份，保留unknown、记忆及日志，不删除状态/锁。Git提交推送不等于部署或真实验收。
