# LAP-42视觉闭环实际进度

## 2026-10-26 识图已启用并完成用户指定的缩减验收

识图已保存并运行加载为true，用户已确认真实授权群中收到正确识图回复，原事件任务completed、投递sent且有消息ACK。按用户决定只完成IQ-01和1000×1000大图IQ-05，两张真实理解均获人工通过；其余四例豁免，旧六例账本与首张评分记录异常保留，不称六例全通过。104单元/39框架、当前真实CLI零生成契约通过。双图片/成员凭证兼容已修；随后用户明确允许提高输入预算，仅将所选CodeBuddy文字政策30000→48000字节，overhead/output各2048、视觉reserve4096、模型/low/free/账号不变。15项保护中仅features与models的这两个授权标量改变，人设/图库/21 pending等保持。详见本轮closure-result；不续其他验收。

| 证据层 | 最终实际结果 |
| --- | --- |
| 代码与离线 | 双cap图片解析修复；真实loopback覆盖1/2cap与0/3拒绝；104单元、39框架通过 |
| 原生质量 | IQ-01真实1次、用户通过；TTY记录异常原行保留。IQ-05真实1次、1000×1000四角精确、用户通过；四例未测豁免 |
| 真实CLI契约 | 正向1本地user/0 next；缺插件/错回执0 user；当前48000配置重新probe通过，无新增远端生成 |
| 生产事务 | stopped下备份、prepare/activate、重读共享校验通过；当前binding 13fc6525cb150461ef18905213d438386b176ab762fa0da13bb529fd9bd9ec66 |
| 运行加载 | vision=true、文字政策48000、DeepSeek/low/free，OneBot ready；其他保护摘要符合授权 |
| 真实群图 | 一次原生图片模型调用，guard live/next1/completed/wire verified；T25814+F8985+V1024+O128000=163823≤C1000000 |
| 原消息ACK与客户端 | trace aa8ab95e717f4e3dbf4d11aa7c9bdcfe，任务completed、投递sent、part0有ACK；用户确认客户端回复且图片理解正确 |
| 限制 | 该回复走已有v2_core_recovery，未据此认定全部辅助字段/记忆学习/受控@通过；GIF群内未测。旧采样target与本次实际群不匹配，本次群符合当前授权白名单且由用户亲自发送，不冒称旧记录同群 |

本机受控真实请求总3（历史意外1+两张质量图各1）；最终真实群图片模型1次。首次两条群图片在本地退化且各有ACK，0图片模型调用；后续预算拒绝仍0生成，失败记录全保留。首次free恢复窗口另有自然文字CLI成功记录，独立于受控视觉计数，不能称全程只有这些调用。

群接线修复后大图保持原观察binding，不伪称在新binding重跑。改前原生执行指纹与当前一致（CLI/预算算法/归一化/插件未改；材料客户端和本地提示是单独修复）；当前配置另通过静态容量、真实零生成probe及完整人设+图片/成员cap+表情分支的零模型组合验证（实际政策占用27467字节），最终还有上述真实群调用。用户追加允许48000后未改model_gateway.py，原保守预留分支保留，没有在原30000限制下偷偷放行。

AstrBot独立Python环境readability-lxml0.9、lxml-html-clean0.4.5、cssselect1.3.0、chardet5.2.0已按项目现有版本补齐；未改第三方源码。原环境缺项导致的首次启动失败留档。所有备份、old active、旧IQ/unknown/ACK/清理台账均保留；当前last_error=null、remote_result_unknown=false、清理未阻断。配置回滚仍只撤本次vision/配对active；48000是用户另授权字段，有独立models原字节备份，不能覆盖后续变更。

本session完成LAP-42视觉用户指定范围，Git核对后释放唯一运行/验证归属，保留服务运行供用户使用；其他旧验收差额不自动推进。

## 历史检查点：真实CLI契约通过，原固定六例启动

2026-10-26T20:42:55.248901+08:00：用户明确授权7次本机真实请求总上限（已耗1+固定六例6），群图仍最多2。当前97单元/39框架通过，实际正向1本地user/0 next/0远端、反向缺插件/错回执均0 user。当前源码/资产/helper/来源/测试与offline、probe绑定已冻结，不能在IQ后变动。尚未启用vision或开始群图，当前代码检查点不等于识图完整验收。

新修复仅作用于NativeImage子进程：关闭CLI自身rules注入，保留完整项目system/prompt；公开API toApiMessages实际仅投影文字，不能用它断言图片丢失。原生图片stdin帧由父进程逐字节hash与子进程原文/像素hash分别校验。prompt.context改为无I/O纯双空返回；回执置于插件兄弟目录，独立phase文件避免并发覆盖/递归。F当前8985，原30000/2048/2048、4096、null及模型/low/free不变。

私有frozen-before-iq保存当前binding/adapter/offline/probe摘要；旧失败/unknown及known-zero本机协议失败均保留，不伪改通过。六例只使用一个持久batch，每例一次、真实回答只临时显示并由用户逐例审阅；任何失败/unknown停止，不换batch洗过。

## 先前失败与停止记录（历史，不是当前契约结果）

**没有完成识图闭环。** 用户确认可配合后实际进入CLI契约probe，最终出现1次意外DeepSeek真实请求/SSE；已按原指令“若出现真实生成迹象立即停止并实记次数，不装作probe后再额外跑满六次”停止后续调用。vision=false，六例和群图均未开始。新guard异常拒绝分支已离线修复，尚未重新真实验证。

| 证据层 | 当前实际结果 |
| --- | --- |
| 代码/插件/安全激活工具 | 已实现并交付；不是生产通过 |
| 最新离线 | 96单元、3组合39框架场景通过；[固定报告](lap-42-vision-offline.json)，offline_valid=true |
| 实际CLI装载与投影 | 已装载4个官方事件，完整system身份/摘要和双上下文清空有实际阶段回执；尚未取得合格的整轮probe |
| 实际本机probe | 21条尝试记录、7条本地user，失败均保留；只有1次观察到远端请求，非成功零生成probe |
| 意外真实模型请求 | 1次当前DeepSeek/low，请求开始及SSE首块有日志；完成、有效回答和质量未验证，按耗次保留 |
| 固定IQ/人工评分 | 0/6，未创建真实六例批次，未预填人工评分 |
| 配置保存/运行加载 | 未执行prepare/activate或正常加载；vision=false |
| 原群图像理解/ACK/显示 | 0/2，agent未发群，操作者尚无需发图 |
| 运行状态 | 最后核对stopped/disconnected，model/gate/AstrBot=0；外部QQ保留 |
| 本机保护 | 15份local/persona/图库/pending原字节不变；既有decoded有效、normalize AST未变，未重采样/拉旧URL |

## 具体失败与真实证据

2026-10-26T19:25:40+08:00恢复，起点本地/实时远端`84da0e9d6ff0029c317dba5829634a78d69b53b9`、工作区干净。TASKS登记重读同23路径和唯一真实执行归属，停止/冻结/保护检查通过；没有启动bot服务。

真实装载暴露了离线直接Node测试未覆盖的宿主差异：Node内置模块导入被Mod loader拒绝；声明类型中的crypto在实际事件环境不可用；直接loader从manifest.options读取选项，userConfig.default不足；跨事件状态须用每请求私有回执协调。已改为纯JavaScript UTF-8/SHA-256、公开fs API和manifest.options，不改CLI/SDK/Snow内部、全局配置或鉴权来源。

prompt.compose事件给出65个注册工具名；公共tool.list给出83个全局catalog项，包含未挂载到本agent的工具，不能将其视为SDK实际工具集。锁定createIsEnabledChecker对空session --tools返回false，SDK getAllTools过滤disabled函数；原deny/dontAsk/strict空MCP、空--tools及父进程init tools/MCP为空的检查保留。只使用原模型/low/账号/额度，没有其他后端或额外模型。

19:51:03，实际turn.step在API transcript块数量检查处抛出`VISION_GUARD_blocks`；宿主报告skipped并继续。随后ModelProvider发出同次当前DeepSeek请求，19:51:05记录SSE建立及首块接收。父进程检测assistant事件后拒绝结果、关闭受管进程，没有把正文发送到QQ。该失败来自新guard异常路径未成功封闭；不能把它解释成模型不支持图片，也不能称作0远端生成或IQ通过。

完整失败、私有回执和各次journal在忽略的state/lap42-vision-closure；已生成实际尝试清单及日志SHA。公开报告不包含原始请求options/nonce/消息/图片/名册/秘密。当前state/vision-evidence/lap42-cli-probe-unknown.json保留1次实际请求及完成未验事实，工具在该标记存在时启动CLI之前拒绝。此前skipRun本地失败的历史来源/解析结论保留，但不再允许用另一条日志自动清除隔离。

## 已做的离线修复与验证界限

普通turn.step身份、消息形状和host I/O验证现在全部在handler内部try/catch中返回本机空拒绝，不让普通异常透传。外层Registration.catch仅在同nonce回执已持久保存next_calls=1、stage next且host next.called成立时重放该次原结果；宿主called但本请求没有准入时返回空拒绝。next之后回执失败只沿用宿主重放，不再次生成。拒绝/探针结果仍不能作为AI正文发群。

新增/扩展的实际项目TS离线执行覆盖缺块、host读取失败、回执I/O失败、host called但无本请求准入、已next后回执失败；另有集成测试证明隔离在async runner和新journal之前生效。96单元0失败0错误、39框架场景通过。**这些修复只获离线证据，出现真实请求后没有再次运行CLI或模型。**

[来源审阅](lap-42-vision-closure-sources.json)补充锁定工具过滤/SDK启用筛选/catalog上下文的源码段和摘要。T/F/V/O/C仍分账：T为原system+prompt UTF-8保守界，F=7968为219已知文字与逐项审阅框架源码段的保守收费，V=1024，O=max(项目2048,当前CLI输出上界128000)，C=min(CLI有效容量,1000000)。原30000/2048/2048、4096及null窗口未改；有限框架仅适用于所审闭合形状，真实probe失败不能用静态/离线通过替代。

当次资产、完整system/prompt、nonce、预算和私有回执仍在runtime/requests，静态包、canonical请求及派生manifest独立摘要。普通文字不装载插件。新kind仍仅替换当前组合唯一记录；guard/helper/source/test及deny规则进入adapter/offline绑定，IQ尚未开始，无旧批次被洗掉。

## 清理和保护

第一次本地user因宿主skipRun/无响应结束时，新增错误标签不属于既有清理结果枚举，导致pending清理记录未能完成保存。已改回项目现有错误枚举、细节放私有元数据；核对其登记owner及11个观察身份全部退出，使用原`manage.py cleanup recover`归档恢复，保留原记录。该覆盖只是observed_only，不声称完整所有后代证明。后续清理状态独立核对，不以旧退出推定未来状态。

未启停bot服务、登录/扫码、安装、调用家庭SSH、访问旧根或A4；未修改本机模型/persona/free/预算/记忆key或库/其他开关、图库/21 pending。未执行激活、回滚或群发。运行配置原字节/SHA保持。

## 验证命令与下一步

已实际执行现有环境的`python scripts/verify_lap42_vision.py`、probe helper的真实`--run`及管理器状态/必要清理恢复；实际probe为上述失败结果，不提供假成功回执。最新定向验证仍为96单元/39框架，不跑全库、旧矩阵或A4。先前阶段A的95/39和当时0真实调用是Git检查点历史，不能套用到本次真实阶段。

后续不得直接重跑probe或另建六例批次：先明确已耗1次实际请求、完成未知及后续预算。重新进行合格零生成probe和完整6例将使本机实际请求上限成为至少7次（已发生1+六例6），超出原“probe应为零生成+固定6例”的计数，须由用户明确后续范围。群图仍至多2条且必须等实际启用/加载就绪后操作者手工发送。未处理隔离及预算前，vision保持false。

只提交本任务检查过的代码、测试、公开脱敏报告与进度文档；所有实际journal/图/原始日志/options/nonce/未知和清理归档继续私有保留。完成commit/push与远端完整SHA核对后释放唯一运行/真实验证归属，不恢复free或推进其他任务。
