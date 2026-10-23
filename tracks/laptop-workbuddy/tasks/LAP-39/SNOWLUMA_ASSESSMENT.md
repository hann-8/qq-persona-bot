# LAP-39 SnowLuma替换评估：长期运行优先

返回[PROGRESS](../../../../PROGRESS.md) / [任务交接](HANDOFF.md) / [TASKS](../../TASKS.md) / [前轮诊断](RESEARCH.md)。

2026-10-24（Asia/Shanghai），session `LAP-39-SnowLuma-longrun-assessment`。用户要求调研能否替换SnowLuma，随后明确两者最重要的是长期运行。本轮只读调研与文档，不安装、不启动/停止/注入/登录，不改代码、运行配置或人设，0真实模型/群操作/SSH；未重新探活bot。00:36:41的NapCat故障现场是上一轮检查点，不冒充本轮当前状态。

## 判断

**SnowLuma可以作为迁移目标，值得验证；目前不具备原版直接替换上线并宣称更稳定的条件。** 本机NapCat已经两次出现业务失活，继续仅看进程和online不足以满足长期运行；SnowLuma有针对持久连接与接收停滞的实际代码改进，但尚无本机长期数据。它仍依赖真实QQ客户端、原生Hook和腾讯会话，不能承诺换后不掉线或永不扫码。

用户的优先级是长期运行，因此推荐先完成迁移前置与详细规划，再做72小时初筛、7天连续运行验证，以假活、人工扫码、恢复和真实收发结果决定是否转正；不因功能列表更多、维护活跃或首次登录成功就替换。原有o3单变量试验仍是低改动候选，见[原报告](RESEARCH.md)，本次不抹掉它，也不把它当迁移必经步骤。

## 版本与证据口径

- 官方最新稳定版为[SnowLuma v2.1.1](https://github.com/SnowLuma/SnowLuma/releases/tag/v2.1.1)，北京时间2026-10-22 01:07发布；到本轮约两天。提供Windows x64完整包，内含Node.js；本轮不下载。其Windows包约40.7MiB，不包含完整QQ客户端，仍需干净NTQQ实例。
- 已用GitHub tag核对：`v2.1.1`与本轮main均指向`f8cb15c27bca3d2d1bd044a921e55bfc44bb5e60`。以下源码判断固定在此版本，不把dev代码当稳定版能力。
- 官方Windows文档仍有旧Node版本、包扩展名和自动加载默认值描述；部署时以固定版发行说明、源码和真实文件为准。例如当前源码默认`hookAutoLoad=false`，环境变量可覆盖；不是照旧网页“默认自动注入所有QQ”直接运行。
- 本轮检索了官方发布、掉线/假死/内存/重连/崩溃/稳定关键词的原始issue及相关评论。没有取得与本机Windows、同一账号、同负载可比较的当前版本7天长稳证据；这是本轮证据不足，不是证明别人都无法长稳。上游测试仅静态阅读，未运行，不能写成“本机离线通过”。

## 围绕长期运行的比较

| 项目 | 当前NapCat路线 | SnowLuma v2.1.1 | 实际含义 |
| --- | --- | --- | --- |
| 本机收发证据 | 短时真实通过，但已两次业务失活；23日重建+扫码曾恢复 | 未安装/未真实接入 | NapCat本机长期门槛未过；SnowLuma尚无本机优胜证据 |
| 假活识别 | 当前WebUI和get_status主要依赖同源缓存online | 有QQ接收心跳停滞监测，并通过good表达健康 | SnowLuma的信号更细，但要确认本机心跳确实被观测，且项目消费good |
| Windows持久连接 | 当前故障尚未唯一归因，原生查询超时且缓存仍在线 | 有管道仍存在、客户端EPIPE断开后重接的专门分支 | 对一类长期运行后挂住有针对性；不等于已覆盖本机这次原因 |
| 下游WS断线 | 已有项目连接管理，但QQ会话假活未暴露 | 有ping/pong失联检测与重连 | 恢复的是SnowLuma→gate连接，不是QQ服务端重新认证 |
| QQ会话恢复 | 当前包已有KickedOffLine/SelfOffline接线及Worker恢复 | 可恢复管道/会话绑定；接收停滞代码本身只报告不健康 | 都不能用“支持重连”概括所有故障；需要区分TCP、管道、登录和业务 |
| 整个进程崩溃 | 当前进程管理不等于已具备全链长期恢复 | Windows launcher是版本检查→node→pause，没有整进程守护循环 | 原版启动器不能兜底进程消失；后续如加受管守护须另做规划 |
| 登录与数据 | 原生路径/快登持久化仍有旧缺口 | Windows依赖桌面QQ扫码登录，仍受原生数据与会话有效性影响 | 不把更换接入层当成免扫码承诺，不复制日常QQ登录资料 |
| 跨系统迁移 | Linux也有静默掉线原始报告 | 官方推荐Linux Docker作服务器部署，但旧版也有Linux崩溃报告 | 推荐部署方式不是稳定性对照实验；不顺带迁家庭主机/WSL/Docker |

### 已核实的有利机制与边界

1. [HookSession](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/bridge/src/hook-session.ts#L1015)先观测QQ的`SsoHeartBeat`接收包，再启动接收看门狗；后续任意接收包刷新活性。90秒无包后再留15秒确认窗口，确认停滞才标接收不健康；后续新包可恢复。它避免把普通安静群误判为掉线，也考虑休眠后事件循环延迟。
2. **从未见过指定心跳时不会启动该看门狗，内部健康标志初始为true。** 因此这时good=true只能表示未检出故障，不能当独立收发证明。试运行必须记录“本QQ版本是否实际armed”；做不到就保留未知状态，而不是算稳定通过。
3. [Windows管道恢复分支](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/bridge/src/hook-manager.ts#L398)明确处理QQ端管道尚在、SnowLuma端连接已断的情形，重试connecting/disconnected/error会话。[反向WS](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/network/ws-client-adapter.ts)也有约90秒失联探测和默认5秒重连；这两层都不自动等同QQ重新登录。
4. [get_status](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/actions/info.ts#L25)返回`good=online && bridge.receiveHealthy`。[主动请求健康](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/bridge/src/hook-packet-client.ts)还响应特定原生连接不可用错误；普通业务超时不必然走同一分支。接收停滞处理没有直接重启QQ或强制重新认证，不能把“检测到坏”写成“已经自动修好”。
5. 上游有对应的[接收健康测试](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/bridge/tests/hook-session.test.ts#L1352)、[管道重接测试](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/bridge/tests/hook-reconnect-no-login.test.ts)和[WS心跳测试](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/tests/ws-client-heartbeat.test.ts)。它们说明分支有合成覆盖，不替代真实长期负载。

### 不能把旧故障或关闭issue直接当成当前结论

- [#549](https://github.com/SnowLuma/SnowLuma/issues/549)报告2.0.2每6秒账户识别导致Windows系统日志持续增长；维护成员回复已解决。[2.0.3](https://github.com/SnowLuma/SnowLuma/releases/tag/v2.0.3)明确改为事件驱动，当前源码/README也匹配。不能继续宣称2.1.1一定保留该轮询问题。
- [#507](https://github.com/SnowLuma/SnowLuma/issues/507)报告1.14.20发送视频时整个进程退出；[1.14.22](https://github.com/SnowLuma/SnowLuma/releases/tag/v1.14.22)有对应ffmpeg原生组件更新。它证明历史上出过整进程故障，不证明当前文本/受控图片路线仍有同一缺陷；本项目也不开放视频发送。
- [#473](https://github.com/SnowLuma/SnowLuma/issues/473)有旧Linux版本周期崩溃及后续更正，后被关闭；没有取得同环境修复后7天收发对照。既不标“当前必崩”，也不标“关闭即长期通过”。
- [#530](https://github.com/SnowLuma/SnowLuma/issues/530)、[#563](https://github.com/SnowLuma/SnowLuma/issues/563)涉及Windows完整性级别/非标准安装目录的枚举与注入问题，后者包含本机同系列QQ52230。说明环境和加载权限必须验，不可只看支持Windows字样；不为本轮修改权限或注入任何进程。
- 最新[2.1.0](https://github.com/SnowLuma/SnowLuma/releases/tag/v2.1.0)继续修缓存上界、消息上报与原生适配；2.1.1主要更新运行时安全基线。维护活跃是有利信息，但当前版本发布约两天，不能据此证明7天无人值守。

## 本项目能否接上

目标链路可以保持为`专用QQ + SnowLuma → 现有gate → AstrBot/qq_router → 既有显式模型后端`。QQ账号、群授权、黑名单和模型额度来源不需要因协议端替换而改变；以下仅静态兼容判断。

| 接点 | 已核对 | 尚需验证/适配 |
| --- | --- | --- |
| 严格反向WS入口 | SnowLuma提供X-Self-ID、X-Client-Role和Bearer；支持Universal | 真实握手/echo、重连代际及旧连接拒绝 |
| array消息和真实@ | 参数名为`messageFormat`，支持array；自发消息可关闭上报 | 不能照搬NapCat的`messagePostFormat`字段；实际@/self_id/引用/去重验收 |
| 群文字、受控图片 | 有标准send_group_msg/send_msg与message_id返回路径 | 单条/分条ACK、发送未知/部分成功、停言最终栅栏、file URI图片实测 |
| 群资料/成员 | 有相关OneBot动作 | 保留LAP-29人数新鲜度等未验证门槛，不据动作存在自动激活 |
| QQ收藏导入 | 两个fetch_custom_face动作存在，基本/详情返回形状与当前固定RPC相符 | 本机真实来源/限额/URL规范与收藏读取另批验收，不自行导入 |
| 业务健康 | SnowLuma good有额外含义 | 本项目onebot_gate.observe_online仅消费online，原样接入仍会忽略good=false |
| 启停/状态/登录观察 | 模型与AstrBot大部分可继续复用 | manage.py硬编码NapCat路径/6099/进程组件；现有NapCat WebUI观察与登录回退不能套到5099 |
| 识图/记忆/网页 | 均为本项目上层能力 | 原LAP-28/29/30等默认值及真实验收差额保持；不因换协议端宣布已验收 |

## 当前阻止“原版直接替换”的事项

### 1. 需要干净、归属明确的QQ实例

本机项目`resources/app/package.json`静态读取确认`main=./napcat/napcat.mjs`。不能把SnowLuma再注入这份已经加载NapCat的QQ，当成干净对照。要准备项目专用的原版NTQQ运行入口，证明PID+创建时间和原生数据归属；LAP-24关于数据目录的旧缺口没有因此消失。不得借用/修改日常QQ或复制其登录数据库。

当前源码默认自动加载关闭，但[开启后的Windows选择逻辑](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/bridge/src/hook-manager.ts#L672)对枚举PID直接放行，不按账号白名单选项目进程。[#561](https://github.com/SnowLuma/SnowLuma/issues/561)也明确提出该限制。因此必须在首次启动前显式关闭自动加载，后续只对已有创建身份依据的项目QQ PID加载；不能靠“启动后赶紧在网页关掉”保证日常QQ不被碰。源码环境覆盖名为`SNOWLUMA_HOOK_AUTOLOAD=0`，本轮未设置或运行。

### 2. 默认内置状态答复绕过项目gate

[默认配置](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/config.ts#L29)启用`statusCommand`，触发词为`#sl`。[instance.ts](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/instance.ts#L568)在向网络上报前直接处理，群和私聊都可直接发送状态答复，swallow=false也不阻止这条答复。迁移必须在首次接入前关闭内置答复，不能让黑名单、群授权、私聊关闭和全部输出最终栅栏出现旁路；健康观测不靠群内状态命令。

### 3. 原版会在gate之前补历史并新增本地消息存储

[event-pipeline.ts](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/event-pipeline.ts#L208)在上报前调用`backfillReplyTarget`；[具体实现](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/modules/message-actions.ts#L442)遇缺失引用可从服务器查询群消息/私聊历史并持久化，尚未经过本项目黑名单或群授权。`historySync.enabled=false`仅控制登录历史同步，不能关闭这条引用补拉路径。

[dispatchEvent/cacheMessageEvent](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/instance.ts#L460)还会在网络分发前写自己的MessageStore，并记录接收消息日志。后置gate不能追回这些先发生的读取/落盘。必须在迁移详细规划中解决授权群/黑名单的前置、引用不补拉、新增应用历史与日志范围；不能默认扩大“底层仍收到事件”为可以新增任意应用历史。本轮没有找到能仅靠已核对的原版配置同时满足这些约束的入口，这是实际前置缺口。

若需要私有源码适配，还要依据[项目许可](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/LICENSE)确认维护与交付方式：其为源码可见非商业许可，原生附加组件另有条款，不应把修改版直接按普通开源依赖公开交付。这里记录许可明示限制，不代替具体用途的法律判断。

### 4. 长期恢复需要项目层的明确合同

[Windows launcher](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/runtime/launcher.bat)没有守护整个进程的循环；看门狗good=false本身也不执行QQ重登。后续若增加受管守护，应先规划身份核验、并发/活动发送/cleanup未知处理、重试上限、冷却、人工扫码出口、脱敏日志和回滚。不能把定时全杀QQ或持续扫码重试当长期方案；本轮不新增守护器、Startup或任何自动任务。

## 以长期运行为目标的试验准入与验收建议

以下是评估门槛，尚非已实施或已完成的正式迁移计划；新增代码/配置/行为仍按AGENTS先详细规划，随后由medium按用户后续指令实施。

1. **先解除前置缺口**：固定版本/摘要、干净QQ与数据/进程归属、只加载项目PID；关闭内置答复；证明黑名单/授权群在补历史、日志和新增存储前生效，默认禁止引用补拉。无法满足即不进入真实接入。
2. **再验兼容和恢复**：先合成握手、准入/发送/去重/ACK/停言回归；真实阶段按用户指定范围，用新消息验证一次生成及发送。单独测试gate连接断开、SnowLuma重启后的同PID管道重接、项目QQ重启、网断恢复；操作者需扫码就记人工介入，不能改口为自动恢复。启停必须唯一归属，不以进程名选择目标，不对日常QQ做故障注入。
3. **72小时初筛**：跨至少三个过夜窗口，维持正常授权群使用；不创建自动发群消息或模型探活。记录是否实际观测并启动QQ接收看门狗，连续记录传输/登录/业务信号与自然新消息回执。2小时无故障只算短时通过，不能判长期通过。
4. **7天转正门槛**：固定同一Windows、QQ、SnowLuma、账号/网络和上层配置，记录全部非计划退出、假活、恢复耗时、人工扫码、漏/重发及发送未知。要求无未恢复假活、无无证据重发或越权输出、无非计划反复扫码；确认过的中断能按合同有界恢复，不能用不断重启掩盖。72小时/7天是本项目工程验收建议，不是上游稳定性承诺。
5. **资源与观测有效性**：保存进程RSS/句柄/磁盘日志与消息库增长的脱敏时间序列，检查是否持续增长；用相近负载比较趋势，不用固定一刻的内存量排名。安静群不记故障，good未armed不算独立健康证明，无法判断的时间窗记未知。只保存状态/事件类别/延迟/计数，不存原始私密消息。
6. **保留回滚**：NapCat安装和配置保留，单一bot账号不同时跑两套；停止试验须确认无活动输出，保留未决发送账本。回滚只恢复试验归属项，不覆写操作者后改设置，不清空旧失败/unknown、人设、记忆或登录资料。回滚不把原NapCat长期问题当已解决。

## 交付和下一步

本轮结论是“可以迁移，但需要前置适配与长期验证；原版不能直接替换”。优先下一步是独立完成迁移详细规划，首先解决第三项补历史/落盘的能力缺口，再设计受管QQ/进程与good消费；不能只把NapCat路径替成SnowLuma路径。若原版没有满足边界的配置或可维护适配办法，应在此停止迁移路线并保留候选，不为安装成功放宽项目边界。

本轮仅六份Markdown。源码/发布/测试阅读属于静态证据；0安装/依赖修改/编译/上游测试运行/配置修改/注入/启停/QQ登录/真实模型/群/SSH，没有接受EULA或隐私协议，没有复制任何QQ数据或原始群消息。文件归属、文档校验及Git交付见[HANDOFF](HANDOFF.md)。
