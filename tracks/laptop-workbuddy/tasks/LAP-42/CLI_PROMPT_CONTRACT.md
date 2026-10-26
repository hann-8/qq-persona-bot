# LAP-42：通过官方接口固定识图输入

返回[PROGRESS](../../../../PROGRESS.md) / [42交接](HANDOFF.md) / [闭环计划](VISION_CLOSURE_PLAN.md) / [medium指令](VISION_CLOSURE_MEDIUM_START.md)。2026-10-26，Asia/Shanghai。只读基线355f7eec2971946595efd057ea3f2a5790afa6f3；此页是来源与实施合同，插件及真实检查尚未运行。

## 已查明的外部接点

[官方Mods说明](https://www.codebuddy.cn/docs/cli/mods)提供按进程装载项目扩展的入口。以本机锁定包为准确合同，网页作为接口索引。本项目提供小型提示词插件，经`--plugin-dir`当次装载；不修改Snow/QQ/CLI发行包、不安装市场插件、不改日常WorkBuddy配置或登录来源。

CLI 2.168.0的bundle SHA256：`13e6dd30a22d2f11857675193f909a2ccb935da67a067f580fcfe764e474ff60`。同包`types/codebuddy-code.d.ts` SHA256：`450476f6346507eb032a00a90c3a90c036e37ef57fbc442b52d5ec725a365a92`。路径由config/versions.lock.json的cli.entry推导；不能把本页或自写审阅摘要冒充上游原文摘要。

调用链已只读核对：ownInstructions先渲染、追加产品agent文字/CLI记忆；eR.instructions随后调用模块9443的composeThroughMods，才向SDK返回system。该事件允许返回完整sections；只有一项session section时，其text原样作为system。因此能在未知产品文字追加之后，投影回CLIRunner传入的**完整原始system**，不再猜产品文字长度。

| 锁定bundle接点 | Unicode字符偏移 | 已核对含义 |
| --- | --- | --- |
| nk=ec(9443) | 4830792 | 模块导入 |
| instructions:async…await ownInstructions | 4867475 | 全部agent组装后才调用Mod投影 |
| composeThroughMods | 4986567 | prompt.compose结果按scope拼接，单项无额外分隔 |
| foldModsPromptContext | 5966330 | CLI分支只读取instructionFiles，不能仅清blocks |
| SDK initialContext | 5967952 | SDK分支读取blocks及instructionFiles |
| bootstrapFunctionHookMods调用 | 5179121 | 正常启动在dispatch前装载，能在首条user前检查 |
| withModsTurnStep | 5376831 | answered短路先于model.getResponse/getStreamedResponse |
| wrapUserQuery | 14096651 | 固定user_query文字框架 |

类型文件核对了PromptComposeInput/Result/Section、PromptContextInput/Result、TurnStepInput/Result、Registration.catch、HookBudget。普通Mod异常/超时默认可能失效后透传，**仅throw不构成阻止模型调用**。TurnStepInput仅有身份/计数等，不含完整system或图片，不得冒称它直接暴露完整SDK请求。

## 选定方案与每次请求

普通`--agent`可能把自定义instructions/tools叠到默认项上并保留appendInstructions；`--system-prompt-file`也仍会渲染/追加。这里采用追加之后的官方事件，不改第三方核心，不换模型/提供方。

项目资产放`adapters/codebuddy_vision_guard/`，含`.codebuddy-plugin/plugin.json`、`hooks/hooks.json`、`hooks/register.ts`。使用现有CLI及其已有加载能力，不加npm依赖/新服务/新模型。等效纯JS模块扩展名可以按同包loader支持选择，不能因此安装新运行时。

仅当前NativeImage识图请求装载插件。父进程在既有runtime/requests私有目录复制并校验资产，在本次manifest options放入完整system、UTF-8长度/hash、model/low/预算、随机nonce、probe/live及私有回执位置。options是受信本机数据，不能由模型/HTTP选择plugin目录或force。静态包摘要与每次manifest摘要分开，不造自引用hash；正文、nonce、真实图片不打印/提交。

**投影对象是最终传给CLIRunner的system参数，须逐字节一致。** 不能只读persona.md而丢掉项目协议/安全政策；原prompt中的项目记忆、成员、网页、历史材料保持。普通文字路径不装载插件。

| 事件/父进程 | 必须行为 |
| --- | --- |
| engine.create/就绪检查 | 挂载后产生本次nonce/资产/system长度hash的私有回执；父进程首条user前核对。缺装载/回执时0 user受管退出，不用任意stderr“loaded”代替 |
| prompt.compose | 返回单项本插件session section，text是完整原system，不调用下层未知组装。校验model、无工具、固定形状；catch仍有界投影或让后续step拒绝，不能透传未知system |
| prompt.context | 同时返回blocks:[]、instructionFiles:[]，覆盖CLI/SDK两个接点；catch同样有界。只去CLI环境/记忆附加，不删库、不改项目prompt |
| turn.step | 验证已投影/本次身份/预算、当前model/low、主turn第0步与单次准入；不满足短路0生成空结果。probe无条件不next；live合格才next一次 |
| 失败与回传 | 关键handler登记catch；未next不能透传，已next只能按宿主重放/原结果语义处理，不能再生成。父进程将拒绝/空短路记为项目错误，不当成AI回复或发群 |

空短路须采用锁定TurnStepResult的turnId/index/answer/toolUses/stopReason/usage形状。回执I/O失败也不放行。插件只做提示词与准入，不给模型注册工具，不改MCP/权限/账号；保留原deny、dontAsk、strict MCP空配置、无会话续接/持久化及禁自动记忆/compact。

无UI启动的functionHookBootstrapAllowed还检查库模式/宿主和显式开关。仅这个视觉CLI子进程设置CBC_ENABLE_FUNCTION_HOOKS及兼容别名为1，独立CLI入口不继承CODEBUDDY_LIBRARY_RUNTIME=1；不改全局env、HOST或鉴权配置。真实零生成检查验证该接线，不能只看源码说已加载。

## 预算与真实CLI检查

T为原system+prompt的UTF-8保守界；保留30000字节政策、2048开销/输出预留、4096视觉预留及CLI窗口null。F逐项核算有限模型模板和CLI框架，V=1024，O=max(2048,当次CLI输出上界)，C取CLI有效容量与模型合同较小者，要求T+F+V+O≤C。

现有known_template_parts静态求和为219字节，**只是已知部分**。新投影与双上下文清空后，补审单system/单user/单图剩余固定框架再给F；不得直接把219、0或2048写成已证明总界。所有实际原生请求复查当前model/low/容量，不裁persona、抬预算或按base64字符估视觉token。

真实CLI本机检查包括：正向自造图＋含中英/emoji/双大括号的system，证明实际装载/原样投影/上下文限制和step短路；反向缺插件/回执错误，证明父进程0 user。正向有本地user帧但应0远端生成，不能称0 user，更不能记为IQ/QQ识图通过。依据是来源短路、实际阶段回执与结果共同核对，不用cost=0或模型自述单独证明。

本轮只读，没有执行上述检查；下一轮实际完成它们并冻结源码/资产/报告后，才开始一个固定六例原生批次。probe不以生产eligible或六例已完成为前置，生产最后回查全部项，不能形成循环。
