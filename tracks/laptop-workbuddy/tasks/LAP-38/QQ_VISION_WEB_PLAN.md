# QQ功能闭环：LAP-18续作C / LAP-28续作R

返回[总计划](PLAN.md) / [证据](EVIDENCE.md) / [medium指令](IMPLEMENTATION_GUIDE.md)。本合同补36，不重新领取已交付28A/C、18B或06D；仅规划，真实样本与部署另批。

## 1. 需求、非目标与成功定义

识图成功须是：授权群非黑名单的新消息→当前第一张图真实像素→所选模型同次原生输入→依据图片作答→原群发送确认。当前可接受GIF首帧、第一图、有限分辨率；不声称看了其他图片、视频、被引用历史、具体群友身份。只“识别出image段”或成功发表情不算。

网页成功须是：拿到安全公共正文→保留问题所需事实/真实来源与范围→最多一次生成→原事件确认。网页源站不可达、登录/付费/JS空壳可明确不支持；仅给主页标题、搜索摘要或丢掉正文不能算成功。B站字幕仍按06合同，不扩ASR/画面理解。

所有修复保持入口准入、私聊关闭、工具隔离、单次模型尝试、无自动后端切换、free新消息驱动、停言代际与原事件ACK。

## 2. 先把责任划分清楚

| 观察 | 分类 | 后续处理 |
| --- | --- | --- |
| 文本里只有“图片”/文件名 | 无像素证据 | 本地说明材料不可见，0生成；不能用文件名猜图 |
| image段有允许URL，下载/解码成功 | 入站已证实 | 继续后端/预算阶段，不能再归因NapCat拿不到图 |
| 真实image段有opaque file但无可用URL | 可能适配缺口 | 仅在真实样本证明必要后按36 I3实现固定get_image，无通用RPC/历史读取 |
| 所选NapCat版本确无URL/安全opaque取图能力 | 上游边界 | 记录unsupported_ingress、版本/能力证据；停对应能力，不加文件系统旁路 |
| CLI仅有图片编码但无所选模型视觉/窗口声明 | 后端unverified | 不生成猜测；可完成代码/诊断；操作者未来显式选择本地路线，不自动分流 |
| 安全HTTP成功、正文关键内容丢失 | 可修复网页问题 | 结构提取/选材与事实验收 |
| 公网偶发超时、RSS候选不相关 | 网络波动/搜索质量问题 | 当前请求失败不重试；搜索门槛保持，按固定样本报告 |

## 3. LAP-18续作C：正文与相关选材

### 3.1 正文提取算法

复用PublicHTTP与现有受管html_worker，不改下载安全策略/外部依赖/2秒及256MiB边界。保持 `web.extractor=readability` 的既有配置入口，在该模式内部升级为“显式主体结构优先、没有合格主体时才使用readability”。`legacy`继续只是操作者明确回滚选择。

1. 下载后仍禁DTD实体/外部网络，删除脚本/导航/隐藏/表单/页头页尾等；不执行网页JS/下载子资源。
2. 按层级找显式`main`、`role=main`、`article`；去掉相互包含的重复根，优先main/role=main。候选须包含至少80字符有效正文、多个实际内容块，不能仅为链接目录。只选一个主体，不拼接多次相同DOM。
3. 当同层有多个不相含候选，以正文字符/段落和链接密度等固定规则评分；代码保留确切输入节点范围。无法确定时使用已存在readability提取，仍是同份RAM文档一次本地选择，不是再次网络请求或额外模型调用。
4. 对文档型页面保留标题层级、列表、表格行、代码块和顺序；不能把`section`/所有`header`一概当正文，也不能为去导航误删嵌套内容。输出纯文本，不把DOM/任意属性交给模型。
5. `body_method`仅为封闭枚举`semantic_main/semantic_article/readability/legacy/plain`；`body_scope=extracted_main`表示提取主体，不声称完整读取整个网页/互动内容。空壳或事实缺失按质量用例失败，不能因HTTP200或80字符就标质量通过。

现有JSON文档反例只证明材料缺关键标识；修复实施须对原公共页面与最小自造同结构夹具对齐，不能仅让测试“出现三个词”就通过。

### 3.2 问题相关段落选择

新增唯一可选配置 `web.selection_policy: coverage|question`，默认coverage，旧配置无字段继续六区逻辑；question是操作者显式选择的增强。保存后下一次正常启动生效，无热更新；`web.enabled`默认false保持，本机保存值不改。

question策略不增加LLM：只从当前目标问题提取至多32个词项，英文/数字/代码标识保留词边界，中文用受限二元词组；去固定停用词，不拿历史/群号/人名补搜索。来源只在本地RAM评分，不把问题发送第三方分类服务。

- 有明确对象/问题时，至少60%正文预算优先容纳命中词项的整段及相邻标题/至多一段上下文，余量覆盖开头/中间/末尾；按命中率、标题/精确标识命中、原位置稳定排序，合并重叠段，最后按原顺序交付。
- 纯“总结/概括这页”或没有有效词项时走coverage；这是明定本地分支，不是模型/提供方fallback。
- 所有选材仍与标题/URL/抓取时间/ranges共用总6000字节上限、单页默认4000、最多2页，且受最终模型剩余预算约束；不增上下文、不截断当前问题/系统/输出预留。单段太大时取其他完整段；无法取得至少1200字节可靠节选则明确材料不足。
- question路径允许少于四个位置分区，但须至少两个相邻内容块且覆盖命中上下文；原四区条件仅保留coverage，不能使相关节选因不分布全页被错误拒绝。两策略都输出真实字符偏移/UTF-8字节数，不能伪造连续范围。
- `coverage=full`仅指本次提取主体全部入包；任何节选都标excerpt并告知可能遗漏。完整/逐项/不得省略请求超过预算继续0生成拒绝，不用question策略偷降成节选。

### 3.3 搜索和可观测性

新增 `scripts/diagnose_public_materials.py`，默认inspect仅本地结构，不读身份/凭据、不网络；`--public-samples`仅固定公开样本、0模型/0bot，输出枚举/字节/段落数/关键事实对齐结果，不保存正文。每份样本一次请求、无失败重试；当前成功与当次失败分别记。普通健康检查不调用该网络模式。

在process_host白名单加入封闭`PUBLIC_MATERIAL`诊断：random_trace、stage（intent/transport/body/selection）、kind、body_method、coverage、数量/大小/耗时和固定failure枚举。禁止原问题/URL或query/网页正文/群身份/原异常message。日志缺失不再被当能力成功或失败；仅关联同次准备，不改模型尝试数。

搜索仍只用bing_rss。代码门槛保持false直到独立报告满足三类固定公开查询：知识/时效/指定site，每类前5至少3条相关候选（site不足5时至少1条且全部域匹配）、前2至少1份确实回答问题的可读正文；时效项还需正文中的可核日期/版本，RSS pubDate不足。当前三个查询仅传输通过，知识项候选不够精确，不能直接开搜索。若先做本地相关排序，仅用本次query/候选字段，不补一次外部搜索；失败保留false，不新增付费/其他引擎。

### 3.4 涉及文件、验证与回滚

`html_worker.py`、`web_extractor.py`必要元数据枚举、`evidence_selection.py`、`web_policy.py`、`web_retrieval.py`、config loader/模板/旧导出/注释、`process_host.py`、新诊断脚本与受影响测试/报告。`public_http/public_network`只在确有本轮复现缺陷时做合同内修复，不因网络波动重写。

离线用例：文档main/role=main、嵌套article/重复根、代码/表格、导航诱饵、隐藏/实体/注入、无主体readability、空壳、超大/超时/取消回收；两选择策略及中文/代码标识、真实范围/最终预算、完整请求拒绝。实际AstrBot矩阵至少mentions/free×single/adaptive，含网页+视觉关闭/记忆/表情/停言旧代际，保持同次v2/ACK。

真实材料批次至少文章/技术文档/长正文/受限或JS空壳四类，前三每页预先人工记录3项事实及位置，最终选材可还原且不含导航诱饵；第四诚实拒绝。实际回答每个正例最多1次，另需用户明确选定后端/总预算/群对象后执行；不得将取材质量通过当LLM/ACK通过。

回滚：先停机审阅；selection_policy=coverage可恢复旧选材。若须恢复旧提取，可显式extractor=legacy或恢复配对旧代码，不能自动降TLS/公网策略。保留现有投递/清理状态。

## 4. LAP-28续作R：实际运行路径与可信预算

### 4.1 路线决策

当前CLI文字路线保持；没有所选模型视觉/窗口依据则留unverified，不据编码支持发图。**为了尽快获得可用识图，优先补已装Qwen3.5/Ollama路径的证据和工具，后续是否选择它由操作者决定；不会建立“文字CLI、图片自动换Ollama”的新路由。** 两条路线不能互相借用质量或容量证据。

本轮已找到明确GGUF源码链：Ollama v0.40.5固定commit→LLAMA_CPP_VERSION b11669→llama.cpp固定commit→mtmd/clip/Qwen3VL，见[证据第4节](EVIDENCE.md#4-所选windowsgguf路径的新来源链)。Windows不能套Mac MLX公式，版本/默认参数不能证明实际安装包与加载路径。

### 4.2 零生成只读收集器

新增本机 `scripts/inspect_vision_runtime.py` 与固定PowerShell采集脚本；默认只inspect本地公开文件/所选profile，不SSH/读取连接秘密。后续明确授权家庭只读时，复用既有固定主机指纹SSH，执行固定采集脚本；不让消息/模型传任意shell、路径或参数，不探测密码有效性。

收集内容：OS/CPU架构、Ollama版本/可执行文件hash和发布工件来源；所选tag/digest与manifest层；真实模型/投影器文件的独立摘要及GGUF允许键；所选llama-server进程PID+创建身份、exe、`--model/--mmproj/--ctx-size`和实际加载的CUDA/mtmd相关DLL摘要；加载日志仅提取固定处理器/patch/merge/min/max/prompt模式字段。绝不导出整条命令行、环境、日志、用户目录或网络地址。

- 路径只从授权安装目录/已确认所选进程/manifest解析，不信任用户消息路径；禁止链接/重解析点越界，固定扩展/允许键/文件数量。大模型文件在远端流式hash，不传权重；每阶段有期限、大小和进度元数据，超限明确incomplete，不缩小证据域冒充完成。
- 本机私有工件存 `state/vision-evidence/runtime-observation.json`，报告只存内容摘要和相对工件别名。绝对家庭路径/SSH信息仍留忽略文件，不写代码所有注册表。
- 若模型没加载，不为了看路径调用chat或启动/重启Ollama；输出artifact_observed/live_path_unverified。稍后六例授权中允许在唯一已预占调用加载模型后重新被动读取同一进程路径；不额外warmup/预填充。
- 收集器不回填“期望processor”；`runtime_identity`仅由实际文件/元数据/进程独立计算。CLI按锁定bundle/所选模型声明/已知窗口收集，缺失继续unverified。

### 4.3 源码边界计算与注册表

新增 `vision_runtime.py / vision_bounds.py`，扩展代码所有审阅记录但保留旧空表拒绝行为。数据中分开**静态工件/源码身份**和**短期实际运行观测**；前者入binding，后者为同工件的进程租约，过期或进程/模块变化须重新0生成核对，不用换PID就丢掉所有六例质量，也不能复用另一工件的通过记录。

须核对六类claim：模型支持、实际runtime路径、视觉token、模板/特殊token、可见bytes→tokens、实际请求窗口。每类源为不可变commit/blob hash/具体符号/适用条件。不能仅有renderer、model_info.context_length、prompt_eval_count或“默认4096”。

对已证明的mtmd Qwen3VL分支：从实际projector读取patch/merge/min/max及任何命令行覆盖；按对应源码的对齐/上采样/缩放步骤计算最终W'/H'，以实际`clip_n_output_tokens`分支求输出位置数；marker另算，deepstack是否增加序列位置按实际路径核对。不能未经观测便写死patch=16、merge=2或上限4096。

固定最大值U必须覆盖现有规范化全部域：1≤w,h≤1024且w*h≤1000000、一图、旋转后/RGB/首帧规范化结果；涵盖极细长/最小图、非patch整倍数、round半值及min-pixel上采样。可用该有限整数域穷举尺寸推导最大值（不做模型计算），用独立的源码同语义算例/边界证明校验C++round和整数除法，不能拿Python银行家舍入替代。若当前型号实际分支不同，先完成采集/通用框架，回max审阅，不套公式。

文本BPE的bytes→tokens系数须审阅所选GGUF tokenizer/normalizer、byte fallback与特殊token处理；允许证明保守整数系数，但不凭经验填1。模板开销覆盖系统/全部消息数/图片marker及think=false实际渲染分支；容量满足：

`可见包络UTF-8预算 × 审阅系数 + 模板上界 + 视觉U + 输出预留 ≤ 已证实请求窗口`

`vision.input_reserve_tokens ≥ 视觉U`，最终每次runner入口重算。原reserve4096保留为政策值；不足时明确需要操作者审阅预算，不能自动减图片/历史系统/输出预留或增窗口来强行通过。只允许既有历史裁剪/材料预算策略。当前审阅表仍空，**本规划不是可直接填入生产的数值证明**。

新增观测的采集值/公式适用性在实现后交回sol/max审阅一次；medium可实现计算与负例，不可自己把未知标true。这样把缺口收敛为具体采集值与固定源审阅，不再循环“现有API不够”而无可做代码。

### 4.4 生产激活工件的闭环

保留固定六例IQ台账及失败/取消/unknown占用、同case不重试。修正observe_lap28对实际运行身份的接点，让它读取独立采集值，而非从record填值。真实调用预算不足或record未获审阅时不运行IQ。

避免“必须先加载才能证明路径、必须先证明路径才能进行唯一加载调用”的循环：静态工件/processor参数/上界已审阅而live路径未观察时，可以在明确六次总授权内先原子预占IQ-01，再进行该例唯一原生请求；同次加载后被动采集实际进程/投影器/模块并核对。实际路径不符即该例失败、停止余例，不能追加探测生成或改trace重试；生产激活仍须完整live及六例通过。若静态工件/上界都未获审阅，则连该测量例也不发。

新增 `scripts/prepare_vision_activation.py`：默认只报告缺项；明确`--prepare`时在停机配置锁内从固定入站记录、代码审阅表、当前离线签名、实际runtime工件和六例SQLite台账派生candidate，不接收passed/eligible布尔字段。候选写固定`state/vision-evidence/candidate.json`；另一明确`--activate`在重读双摘要/配置和全部门槛后原子替换active。两步均0生成、不开vision、不启停；并发修改/unknown/过期观测直接拒绝。

操作者最后停机审阅 `features.yaml` 的vision开关和所选models profile，正常启动才加载。发送前重新检查所选version/digest及实际路径租约；改变工件/processor/参数/人设/模板/源码的binding使旧观察无效，不静默重新授信。状态输出区分ingress_unverified/runtime_unverified/bounds_unreviewed/quality_unverified/production_eligible/loaded，不能只显示一个“支持图片”。

### 4.5 涉及文件与离线验收

新增上述采集/计算/激活脚本与模块；修改vision_capabilities/vision、observe_lap28、两runner仅必要实际身份/租约与预算接点；配置状态展示/公开能力表/适用测试和独立报告。SSH传输不新增任意命令接口；不改登录/群参与/31B。

离线必须证明：真实观测字段缺失/复制期望值无效；错版本/平台/文件/模型/投影器/override/过期租约拒绝；整个尺寸域U及最终预算边界；CLI未知仍拒；intake绑定、六例原子预占/禁止洗台账、candidate不能手写开门、重读/原子替换失败保旧active；无图文字路径和实际框架mentions/free、single/adaptive、web/记忆/表情/成员/停言组合不回归。

## 5. 真实验收分批执行合同

以下是未来执行参数，不是本轮授权。后续任务先登记唯一实例负责人、当前版本/配置摘要/样本/预算；不重复启动，不把故障重放成新调用。

| 批次 | 最大外部动作 | 通过标准/失败出口 |
| --- | --- | --- |
| A 入站 | 正常实例已按归属停机；现有intake-only 120秒、最多1条操作者自造图，0模型/0bot输出 | 同一次准入记录有bytes和Pillow decoded/hash；失败精确分为段/URL/传输/解码，不归咎整层 |
| R 家庭只读 | 仅明确授权主机/所选模型文件和进程元数据，0生成 | 固定源码链与实际工件/processor参数可对齐；未加载只记部分，不擅自暖机 |
| IQ 质量 | 明确选择一个后端和一个固定6例批次，总最多6次；失败/取消/unknown均耗次，不换trace重试 | 六例精确事实+人工评分、native hash、预算、正常结束/无工具、实际runtime全部通过 |
| Q 群闭环 | 单个明确授权测试群，2条自造真实@样本，模型最多2次/按配置有限文字气泡 | 第一图事实正确、图片注入无效、原群原event ACK/历史一致；另用离线负例验证黑名单/非授权/停言，不随意拉真实成员制造案例 |

Q完成前可以记“原生图片质量通过”，不能记完整QQ识图验收。普通free没有@时允许一次说/不说；必答只绕过沉默/冷却，材料不可见或模型不可用仍走诚实本地说明，不虚构内容。多图/视频、旧引用附件不纳入本次已支持范围。

## 6. 配置、迁移、回滚总表

| 字段/工件 | 计划默认/生效 |
| --- | --- |
| vision.enabled / ingress_diagnostics | 均false；继承现有字段，下次正常启动；本机不写 |
| vision.input_reserve_tokens | 4096政策预留，不是被证明上界；不因计划自动调值 |
| llm.backend/model/profile | 保留现有CodeBuddy默认及已装Qwen profile；操作者显式选择；不按媒体自动切换 |
| public_network.resolver / ca_bundle_file | system/null默认；保持严格校验；DoH单独失败不触发切换 |
| web.enabled / extractor | 新装false/readability；readability内增强主体识别；legacy仅明确选择 |
| web.selection_policy | 新增coverage默认，question显式选择；缺失兼容coverage、unknown字段仍严格拒绝 |
| bilibili.enabled / trigger / auth_mode | false/explicit/none保持；不动字幕认证或ASR |
| runtime observation/candidate/active | 固定忽略state路径，不能由消息或随意YAML指定；不提交任何私有工件 |

旧配置/模板/旁注/单文件导出及双摘要都须同步新增selection_policy。任何新源码/人设变更可能使视觉旧签名失效，要明示重绑，不能偷偷复用旧离线报告。回滚先正常停机、保留未知/发送/清理台账、关闭vision/恢复coverage与配对代码；若旧代码无法理解新证据，保持关闭，不删状态强启。
