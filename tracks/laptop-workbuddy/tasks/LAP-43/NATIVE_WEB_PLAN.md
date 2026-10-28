# LAP-43收敛方案：复用CodeBuddy原生联网

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [43交接](HANDOFF.md) / [medium指令](NATIVE_WEB_MEDIUM_START.md)。2026-10-28，session `LAP-43-native-web-simplify-plan`。

## 1. 路线纠正和当前证据

用户已在CodeBuddy会话演示Fetch取得python.org等页面；另说明WorkBuddy具备联网搜索。本项目当前运行CodeBuddy CLI，优先复用它的会话原生能力，不换后端。演示证明对应会话Fetch可用，不把演示答案中的版本/日期当成本轮独立核实的事实，也不把Fetch等同“任意主题搜索已证实”。

实际阻断在项目自己：[runner](../../../../src/qqbot_gateway/workbuddy_cli_runner.py)以`--tools ''`清空工具、deny WebFetch/WebSearch；ResultParser要求init.tools=[]并拒绝所有tool_use/tool_call。只改变一个允许开关还会被后两层拒绝。当前安装包`dist/codebuddy-headless.js`静态定义了`--tools`/`--allowedTools`和WebFetch/WebSearch，但bot同账号/模型/headless的真实调用本轮未执行。

原方案绕开了现成能力，额外构建搜索、提取、日期、gist/manifest和公共批次门槛，已偏离用户的普通联网聊天目标。**停止这条自建联网路线，不继续修B/R2来争取放行。** 旧失败记录保留为历史；它们不再是原生联网启用前置。原R1/R2/R3/旧C不按旧顺序继续，后续从本指令进入。

本轮只收敛文档、准则和交接；不改业务代码、运行配置、人设或服务，不执行真实CLI/模型/QQ/SSH，不合生产main。实际原生接入与代码清理由用户后续指定medium实施。

## 2. 最小行为

授权群新消息进入既有gate/router/gateway → 当前CodeBuddy会话可使用被许可的原生联网工具 → 同一CLI尝试内完成查找/阅读并生成最终自然纯文本 → 既有原event投递/ACK。中间Fetch/Search进度、思考、工具JSON不发到QQ，不要求先输出网页解析报告。

明确要求查找、现行/近期事实时可联网；已有公开URL可Fetch读大意。普通闲聊不强迫联网；用户说不联网则本轮禁用联网工具。普通文字会话由模型在原生能力内判断是否需要工具，不再要求群友命中自建搜索关键词或先贴URL。仅围绕本次明确公共问题查找，不把群历史、记忆、账号/凭据拼进搜索词。

图片继续已有同轮原生输入；保留R1“结合配文/语境自然接话，明确问分析才展开”的固定政策。首期原生联网只接普通文字/URL会话，图片专用guard仍走现有无工具路径，不能为联网直接删除它的限制；图+URL组合先按图片任务处理，不声称已联网。以后确需两者同轮再按实际需求扩展，当前不扩项目。

保留唯一owner、暂停/恢复、授权群/私聊关闭、去重、最终发送guard、单次CLI尝试/无自动重试/无自动切后端。原生工具过程可能包含多次模型内部推理与多次Fetch，不能再声称每条消息只有一次远端生成或成本与纯文字相同；沿当前账号/credits，不新增付费服务。它们共同属于一次CLI执行尝试。

## 3. 只改四个接点

1. **会话启动**：在本次CLI参数中用明确工具名限制并预授权：`--tools WebFetch`，需要且确认可用时加WebSearch；对应`--allowedTools`必须一致，并从本次disallowedTools中排除这些名字。保留dontAsk（未授权工具拒绝）、strict空MCP、setting-sources none和独立请求目录；不使用default全工具/bypassPermissions，不改CLI全局设置或日常WorkBuddy。Fetch的UI显示名与实际内部名以init/源定义为准，不猜别名。
2. **返回解析**：ResultParser接收本次预期白名单内的工具声明和工具过程，其他工具/MCP继续拒绝；只取最终成功result进入聊天协议和发送链。中间assistant文字/tool_use/tool_result不当最终答复，不泄漏进度。保持输出/事件上限、错误分类、取消与受管清理；不为每种网页内容新建证据协议。
3. **轮次和提示**：纯文字原无工具会话保持现有限制；有原生联网工具的会话将`--max-turns`从2放到固定8，保持当前请求超时，不另建重试/调度器。8是CLI代理轮次上限，不是HTTP/模型请求精确计数。提示允许按需使用已开放原生能力，答复围绕用户问题、必要时附简短实际来源；不知道/没查到就如实说，不硬编码每日公告或强制分析模板。
4. **路由与配置**：CodeBuddy选择原生工具后，移除该路径的WebRunner外层抓取/材料包装和自建搜索质量常量前置。正常聊天/图片/成员/记忆/表情继续同一模型和投递链，不另开旁路。web.enabled控制原生Fetch，web.search_enabled控制是否加入WebSearch；web.provider新增/改用`codebuddy_native`，公开默认仍enabled=false/search_enabled=false。本机provider迁移及启用在后续运行授权时定向保存，不自动改local。

原生Search先核对bot当前组合是否真正提供；若只有Fetch可用，就交付URL阅读并明确“自由主题搜索尚未接通”，不伪称全面联网，不回头自动重建Bing链。现有Ollama路线保留聊天，不声称拥有CodeBuddy工具，也不为追求两后端共用而复制一套搜索；切到它时如实提示该联网能力不可用，不自动切回CodeBuddy。

原生工具的抓取、页面理解和上下文管理交给CLI。旧max_pages/max_results/提取日期等自建字段不再宣称控制原生工具；迁移时可兼容读取并标退役，本机只删操作者选中的过期字段，不重写整份local。起始输入仍沿48000字节政策，工具后续材料由CLI管理，不能称原起始输入预算覆盖全部原生工具成本。

## 4. 删除/回退范围

**保留**：A的owner/暂停、输入分流/叫名/空@、既有表情激活helper、群记忆与受控@，R1自然图片政策，运行进程/发送账本/原生图片支持、预算和清理。所有实际报告/失败、IQ/ACK/unknown/状态及配置备份保留，不清库或删锁。

**退役并在medium实施时删减**：CodeBuddy上的WebRunner包装、自建Bing搜索触发/排名、日期和gist质量常量/manifest扩展、只为该链新增的probe/测试/writer及启动入口。`probe_lap43_search.py`、`probe_lap43_materials.py`不再作为当前实施命令；对应报告留档。web_freshness、html_worker/web_extractor、evidence_selection等仅在无其他活跃引用时删除，若仍被兼容材料/历史工具导入则去掉新路线接线后最小保留，不为了“文件少”破坏导入。

**不得误删**：图片下载共用的PublicHTTP/public_network、仍用的配置解析/当前vision证据校验，或A中其他独立功能。先用rg核引用和diff，再按任务归属改动；不用整分支reset/revert抹掉A/R1独立成果，不编辑框架/CLI内部。能回退的仅回退对应自建联网增量，必要兼容保留不等于继续维护第二路线。

旧MATERIALS_CHAT两份冗长方案本轮直接压缩成兼容指针和必要自然对话合同，原文在Git历史可恢复；旧原始报告不删。不给已失败批次补写通过，也不继续追加“质量冻结批次”证明原生组件可用。

## 5. 文件、顺序与必要验证

medium精确登记后，按“runner启动/ResultParser → gateway路由/固定政策与配置 → 删除无引用旧联网代码和相关测试 → 定向回归”完成。主要涉及workbuddy_cli_runner.py、model_gateway.py、backends.py、persona.py、web配置/模板/旁注、必要的旧web接线、相关测试及交接。global deny清单可原样保留，按本次会话派生许可，不全局放开。

离线只测必要合同：工具参数/deny一致、init和工具过程仅接受白名单、其他工具/MCP拒绝、最终文字只投递一次；无工具/图片路径兼容；停止/超时不补试；owner/暂停与相关已有框架路径不回归。无需重跑整个旧B/R2、全套历史矩阵或另建网络提取器评测平台。

源码改变会影响现有vision版本绑定：沿已实现43配对校验处理，不缩小签名/伪改旧active，也不新增一套凭证系统。没有运行授权时实施分支离线交付并停止，生产main/原vision=true保持；不得先合代码让生产启动失败。

后续用户明确选择运行时，验收就用实际bot会话两题：一条给定公共URL阅读，一条不提供URL的近期信息查询。实际Fetch/Search轨迹与最终回答/原event ACK、客户端体验分开看；Fetch成功不代替Search成功。需要当前图片版本回归时复用43的1次既有IQ-05和最多1条群图，合计最多4次受控请求尝试（内部工具/模型子步骤另计），不加旧六例或全量网页样本。用户逐次内容反馈忠实记录，失败不重试；未覆盖的旧owner/表情真实验收仍列为剩余，不冒称完成。

## 6. 回滚和停止点

原生联网问题先在本次会话禁用联网许可，恢复无工具文字路径；运行配置变更按本任务备份及配对代码/vision active恢复，保留原账号/模型/人设/数据。不要为原生Fetch失败切到新API、旧Bing链或反复增加验收批次。

本轮11文档规划/准则收敛后commit/push现有隔离分支、核对远端即停止；生产main不动。下一步仅等用户把[新medium指令](NATIVE_WEB_MEDIUM_START.md)作为实施任务提交，不再按旧R1/R2/R3/C串行执行。
