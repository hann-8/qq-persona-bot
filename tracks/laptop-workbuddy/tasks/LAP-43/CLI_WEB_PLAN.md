# LAP-43续作：仅开放CLI原生WebSearch和WebFetch

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [HANDOFF](HANDOFF.md) / [medium指令](MEDIUM_START.md)。

2026-10-28，session `LAP-43-native-web-plan`。用户已确认第一批仅开放这两个工具，沿前述规划方→medium实施分工接续。本轮只改文档；功能尚未实现，当前CLI仍全部工具关闭。本文覆盖原PLAN中当前CodeBuddy路线的Python检索前置和“全部工具为空/一次主模型生成”要求，其他已部署功能不重做。

## 1. 需求、现状和非目标

目标：QQ→Snow→gate/AstrBot→gateway→CodeBuddy CLI，模型在同一CLI任务内自行决定是否调用WebSearch/WebFetch，再按既有群聊JSON协议给出最终答复。Python不再先猜“现在/最新/几度”是否联网，也不先执行Bing RSS、HTML正文和日期筛选来阻断当前CodeBuddy问答。用户希望保留只暴露少量工具的token优势，QQ群效果由本人实测。

用户现场确认表情/管理员控制已能用；提供的medium只读诊断称Python页面提取失败、天气问法漏判、搜索候选日志不足，具体回复与检索追踪尚未唯一对应。本轮没有复跑公网或读取原始群消息。实际代码证据：

| 位置 | 已核对事实与实施含义 |
| --- | --- |
| model_gateway.py约511行 | 当前无条件包WebRunner/ Retriever；原生模式必须绕开检索部分，但保留该包装器承担的取消、stop、成员/图片上下文及v2最终处理 |
| workbuddy_cli_runner.py约77/83/179行 | init要求tools/MCP为空，任何tool_use报错，argv使用tools空字符串及全量deny；这三处须一起改 |
| persona.py约41行 | 仍写无自主检索、外层给材料；须按实际engine生成能力政策，不改用户persona正文 |
| vision guard register.ts约133/151行 | 假设全部工具被禁、仅第0步、恰一条user、next仅一次；原生工具往返必须配对适配，不能只开argv |
| 锁定2.168.0的headless源码 | 含WebSearch/WebFetch、tools白名单与NoDefer筛选；SDK类型声明tool.call middleware可返回deny、turn.step可检查当前API投影。包里有工具不等于本账号/服务已真实成功 |

非目标：开放Read/Write/命令/REPL/Skill/Agent/ToolSearch/MCP/定时工具，改CLI上游或全局CLI，换主模型/账号/credits来源，修复全部旧网页抓取问题，扩ASR/视频或家庭后端，重做表情迁移/owner控制/质量评分/旧完整验收。工具实际服务失败不伪装联网成功，不自行回退另一提供方。

## 2. 工具与行为合同

- 代码拥有的全集固定为WebSearch、WebFetch；不增加任意YAML工具名列表。web.enabled=false全部关闭；true且search_enabled=false只允许WebFetch；当前两开关均true时恰好两个。其余工具及全部MCP始终不可用。
- argv用tools白名单和显式许可配合dontAsk；可用`NoDefer(WebSearch),NoDefer(WebFetch)`确保直接暴露且不自动带入ToolSearch/DeferExecuteTool。从本次有效deny中仅排除实际允许项；默认全关模式仍保留原完整deny。以实际模型init/执行集合为准，不拿包含全部注册名的公共catalog误判。
- native模式不调用旧web.intent/Retriever，不以关键词或严格7天窗口拦截模型；是否需要联网由模型决定。用户本轮明确不联网仍优先，现有参与策略/真实@必答/暂停状态不改；ambient可直接silent，不为普通寒暄强制联网。
- 一个QQ群事件只启动一次CLI业务任务；允许有限主模型→工具→主模型往返，失败不启动第二个任务补答，不自动切模型。只转发最终JSON结果，工具事件、网页正文、进度文字都不直接发QQ。
- WebSearch用于未知网址的问题，WebFetch读取指定页面；仅公共http/https。tool.call边界拒绝非白名单、agent/MCP调用、文件/本机路径、显然本地/私网/元数据地址及含已知私密ID/凭据的查询；复用已有轻量校验，不再自建搜索/HTML/DNS/重定向抓取链。原PublicHTTP逐跳证明不套用于CLI，原生工具的网络实现由CLI承担。
- 页面/搜索结果只是材料，不能授予控制权限、改本地配置或要求调用其他工具；来源只能引用实际工具结果中出现的公开URL，至多2条。没有成功结果就准确说明本次未核实，不用历史知识冒充实时核验。正文继续自然纯文本；用过web的答复走单条answer、meme_id=null、memory_proposals=[]，不把网页变成长期群事实。

## 3. 配置、默认值与token约束

| 字段 | 默认/本机部署值 | 生效与范围 |
| --- | --- | --- |
| web.engine（新增） | 缺省gateway以兼容旧配置；本机显式codebuddy_cli | 仅codebuddy_cli后端支持该engine，停机保存/正常启动；家庭后端不自动切换或替换检索 |
| web.enabled / search_enabled | 保持本机true/true | 控制固定白名单；关闭时仍沿同一业务链普通回答，不触发旧网关联网 |
| web.cli_max_tool_calls（新增） | 默认3，整数1..3，本机3 | 同一CLI任务总工具调用上限；失败/拒绝后的已发调用不退还，不是底层HTTP/内部AI请求数 |
| web.cli_max_turns（新增） | 默认4，整数1..4，本机4 | 传CLI max-turns并在guard中计主模型步骤；保持既有90秒总deadline，不按每步重置 |
| web.cli_tool_result_bytes（新增） | 默认8000，整数1000..8000 | 单工具返回给主会话的可见UTF-8文本上限，标题/来源计入；同任务合计12000固定硬限 |
| 原模型/预算 | DeepSeek/low、48000文字政策/2048开销/2048输出、4096视觉reserve保持 | 每个主模型轮次都将实际工具定义、历史工具结果计入可见预算；不能只验首次prompt或自动扩大预算 |

同步validate_web、分层模板/旁注/导出及设置快照；旧gateway字段兼容保留，在native模式显示不生效，不按trigger/日期筛选它的请求。原搜索质量false是历史，不控制原生工具可用性。状态展示engine、有效两工具、上限及待用户实测；普通主模型未用工具时不宣称发生搜索。

工具定义即使未调用也可能占上下文；仅声明两个，关闭其他CLI记忆/skills/MCP等既有隔离保持。WebFetch本身可能有内部AI处理，3工具/4主步骤上限不等于3次HTTP、精确原生模型调用数或固定credits；可见usage/次数如实记录，不据此换主模型或新账号。无需先跑测量项目才交付。

## 4. 接线与识图兼容

1. StreamParser参数化有效白名单。init工具集合须与本次有效白名单匹配，MCP为空；允许这两种tool_use/tool_result并核对调用ID/工具名/边界，拒绝其他工具。仍只接受一个成功最终result和既有JSON协议；工具中间文字不混入答复。工具失败可在原任务剩余上限内由CLI解释，无自动重启或无限恢复。
2. 复用锁定SDK的tool.call middleware，在调用next前检查名字/参数、预占本次工具计数，失败也保留次数；同tool_use_id重放不重复执行。以请求级串行计数或原子更新处理并发，不让并行只读调用绕过3次上限。返回后裁剪已知文本结果字段并保留真实URL，超出总预算准确停止；不执行网页命令或把内部文件路径带入模型。
3. turn.step按同任务nonce、单调step索引、固定主模型/effort、总deadline及max-turns授权。第一轮绑定原user/system/当前图像素；后续仅允许本次已登记调用及其结果扩展API消息。保留同一次CLI内部的合法工具历史，不再每轮清空成单user，也不放入CLI旧历史/文件提示；逐轮核算schema/结果及视觉容量。异常必须明确拒绝，不能依赖host跳过异常后继续未检查推理。
4. 图片仍走当前OneBot材料cap和原生stdin，工具往返不重新消费cap、不补历史图；有图也允许同一两个工具，原像素、工具白名单、每步预算检查保持。现有Guard收据/finish与hosted_cli_budget中F/工具定义分账须同步，不沿用“零工具/恰一次next”的旧通过结论。
5. 复用lap43_operator_trial及prepare/activate，纳入当前完整源码、工具策略、最终设置和helper摘要；使用独立当前native-web检查/私有记录路径，不覆盖42/已交付43报告/失败。必要技术检查通过即可配对启动，quality_state仍pending_user_test，不新增IQ评分/模型质量批次，不静默关掉识图。

## 5. 涉及文件与实施顺序

主要接点：web_policy.py/config.py/config_comments.py及模板；model_gateway.py、web_retrieval.py（仅engine分派及保留包装职责）、workbuddy_cli_runner.py、persona.py；vision_mod_guard.py/hosted_cli_budget.py/vision_trial.py/vision_capabilities.py及adapters/codebuddy_vision_guard/hooks/register.ts；revalidate_lap43_vision.py（最小当前路径/策略接点）及必要定向测试。必要时新增小型cli_web_policy.py，集中固定工具/计数/结果限额；不复制CLI工具本身，不改第三方包。下一轮先登记实际归属，不要求照表全改。

顺序：隔离实现engine/固定白名单→parser及tool/turn hooks→预算/最终结果和能力政策→必要定向检查→停机后main及当前local/vision试用配对更新→正常启动供用户试用。表情已激活、owner已可用，不重新迁移/部署整套旧阶段。单轮完成，不以缺人工质量评分或旧完整矩阵为由再拆轮。

## 6. 必要检查、部署与回滚

只测真实风险：有效tools严格两项/关闭分支无工具/MCP空/第三工具拒绝；最多3个调用及并发/重放、总4步骤/90秒、返回文本与上下文超限；中间事件不发QQ/最终v2和来源/记忆规则；带图+工具结果上下文保留及预算；原暂停发送栅栏仍覆盖最终答复。用已存在runner/SDK边界替身和当前CLI零生成init/接线检查，少量定向检查足够，不跑全库、旧六例或安排agent真实模型/群发。当前实际WebSearch/WebFetch服务效果交用户群测，未做就标未验。

用户已选定这项变更。下一轮medium按统一prompt同轮执行必要当前Snow受管停启、main合入、web.engine及新上限保存、当前完整vision试用记录配对更新，启动后核对实际tools/配置加载和通道。模型、账号、预算、persona、图库、记忆及唯一操作者保持；只操作有创建身份依据的项目进程，不登录/安装、不改全局CLI/旧根/家庭主机。

部署前备份本次字段/active和代码提交，正常停止后再更新生产Python；失败先当轮修复，不能解决则恢复配对旧代码/config/active供原功能继续使用。旧gateway的提取/词法问题仍是已知差额，回滚不等于联网故障已修；不为“回退可用”隐瞒它。不删除unknown/清理账本、历史、记忆key、图库或锁，不用旧完整local覆盖新修改，不强推。

Git按长期授权提交本任务已检查文件，部署后的main推送并核对实时SHA；原43交付及用户已用事实保留。本轮规划文档同样commit/push，只报告已规划，不能称工具已开放。若当前服务/账号拒绝原生工具，完成实现和其他独立成果，报告具体错误，不擅换CLI版本、后端/付费API或开展大规模试验。

## 7. 参考与当前限制

- [官方工具说明](https://www.codebuddy.cn/docs/cli/tools-reference)：WebSearch与WebFetch的职责。
- [CLI参数](https://www.codebuddy.cn/docs/cli/cli-reference)：tools白名单、许可及max-turns。
- [延迟加载覆盖](https://cloud.tencent.com/document/product/1831/137045)：NoDefer只直接暴露指定工具，避免额外发现工具。
- 锁定包types/codebuddy-code.d.ts声明tool.call输入/返回、PreToolUse及turn.step；实际实现以项目2.168.0为准，不把最新版文档当当前真实服务验证。

当前没有运行原生联网、CLI模型生成、群发或启停；原Python链失败/用户已用表情与owner来自用户反馈和既有交接，不能互相替代。本文满足下一轮实施所需合同，不新建资格、长期监测或测量项目。
