# LAP-28续作合同：先证明图片材料，再验原生识图

返回[总计划](PLAN.md) / [证据](EVIDENCE.md) / [medium指引](IMPLEMENTATION_GUIDE.md) / [原28交接](../LAP-28/HANDOFF.md)。本计划补齐原28的入站、可信容量证明与质量验收，不撤销原cap/隔离/预算合同。

## I1. 先判定到底收到什么

在NapCat反向WS TEXT JSON帧经self/group/sender/黑名单准入后、gate改写message之前观察。WebSocket BINARY帧仍拒绝；“是否有图片”检查`message[]`中的image段，不从`raw_message`、summary、`[图片]`、`[非文本未解析]`或模型自述推断。

| 等级 | 判定 | 可记录的证据 |
| --- | --- | --- |
| ingress_observed | 当前已准入事件确有image段 | 随机trace、段类型/数量、第一图字段存在性、url表示类别/file表示类别，不含值 |
| locator_resolved | 有符合现有策略的HTTPS图片地址 | host类别枚举（允许QQ域/其他/无）、是否来自当前段或固定get_image，不记录路径/query |
| bytes_fetched | 同一次已准入材料操作返回非空有界bytes | HTTP状态类别、MIME、长度、下载/重定向次数；不能只看Content-Length |
| decoded | Pillow实际解码为支持格式 | 原始/规范化尺寸、首帧/格式、规范化长度、内部双hash关联及有限耗时 |
| native_observed | 所选模型同次原生输入且答对图中事先未泄露的内容 | 原生输入类型/图数、绑定/适配器签名、单次调用计数、人工评分 |
| production_eligible | 有效代码证明+预算上界+质量/容量观测全部满足 | 从证据派生，不允许手写状态、只测一图、减reserve或直接删拒启逻辑 |

图片URL是有效材料入口；无需NapCat把二进制直接塞进事件。只有URL仍不算bytes_fetched。data.file若为普通文件名/ID，仅是定位信息；若为本地路径或URI，不能任意读盘。首版不接收群文件、reply嵌入媒体、转发节点、QQ市场表情解包或历史补拉。

## I2. 观察工具与日志合同

新增`scripts/observe_lap28_intake.py`，默认`--inspect`只读本地配置/安装bundle的结构元数据，0启停/网络/模型/QQ输出。不要把现有日志全部打开为debug。生产可选`vision.ingress_diagnostics`也只记录下述封闭元数据。

真实入站观察使用明确的`--intake-only --max-events 1 --timeout-seconds 120 --authorize ONE_IMAGE_INGRESS`模式，另需操作者指定授权样本目标。脚本须复用现有创建身份/配置锁/require_stopped/进程台账，确认正常bot已停；以受管诊断模式只运行项目NapCat与gate，不连接/启动AstrBot或模型网关、不开放发送群消息。诊断gate在本模式没有转发分支，仅处理meta状态和一个合格样本。已有实例占用、未决状态或无法证明归属时拒绝，不能杀进程或擅自重启腾端口。

诊断模式是未来单独授权的真实批次，不在普通代码实施时执行。仅使用用户自造无敏感图；应包含新真实@以兼容mentions，free也不能绕过群/黑名单准入。用户未登录时返回需人工登录状态，脚本不读密码、不自动登录。结束/超时/取消关闭的只是本诊断创建的进程并等待退出；不能复用日常QQ/全局路径。若LAP-24正在修改生命周期入口，先协调归属，复用最终实现，不复制一套管理器。

窗口内至多处理1事件、第一图1次解析/下载；入口否决事件没有附件解析/下载/新增历史/事件级诊断记录。普通文本占位反例仅给类型计数，不能“修复”为图片。不能为了抓包在现有真实bot前插入第二个WS客户端、重放旧事件或事后补get_msg。

诊断输出固定字段：schema_version、stage、random_trace、image_segment_count、first_image_field_flags、representation_enum、locator_source、host_class、http_status_class、bytes、normalized_dimensions、mime、attempt_counts、failure_enum、elapsed_ms、backend_calls=0、qq_outputs=0。实际身份只在进程内校验；持久化关联用本次随机/HMAC引用，报告不写QQ号、群号、message_id、url/file/cap/token、原图像素、raw_message或模型回答。原始/规范化hash保留在私有材料链内，公开报告仅自造夹具可记录hash。

`scripts/process_host.py`只增加严格匹配的新元数据行，测试拒绝含未知字段/自由文本/URL/长数字的日志。日志层不得重新放行整个OneBot包。本机私有诊断状态在`state/vision-evidence/`忽略，脱敏结论可写reports；文档标明是哪一级真实通过。

## I3. 现有材料服务的最小补齐

优先使用已观察的第一图data.url，沿用2个精确QQ HTTPS域名、公网解析/peer/TLS、0代理/0Cookie、每跳检查、最多2跳/8MiB原始/512KiB规范化PNG/2MiB线包、原图1600万像素/规范化最长1024且100万像素、GIF首帧、15秒准备期限和8MiB在途租约。像素/字节上限不因为下载失败或模型失败自动放大。

只有在真实事件证明“有image段但无可用url、仅有安全opaque file ID”时，才允许按本计划实现固定`get_image`补定位分支：

1. `vision.allow_get_image_fallback`默认false，操作者显式选择后才生效。cap须在授权事件入站时保存第一图opaque ID及identity/connection/instance/TTL绑定，不接受模型或HTTP调用方提供任意文件ID。
2. 接受的opaque ID非空、最长256，不含路径分隔/盘符/NUL/控制字符/URI scheme；不把本地路径、file://、base64://或HTTP地址转送为ID。未识别形态返回SOURCE_UNSUPPORTED，不能跳到第二张图。
3. gate内部专用echo命名空间只调用`get_image`一次，参数仅file；超时3秒且包含在15秒总期限内。不允许从AstrBot/模型开放通用RPC，不允许get_msg、群历史或任意路径读取。
4. 结果只接受经同样image_url校验的URL字段；API返回file/path不会被读取。随后至多一次公共图片下载，失败不回退其他素材/重试RPC。每跳检查、黑名单/哑巴代际/TTL在await前后重查，断线/重启/cancel释放。
5. 现有cap一次消费、错误目的/绑定也消耗、请求/目标source_digest/epoch冻结不变；RPC结果不流入模型/历史，只有规范化像素和描述符进入sideband。

没有真实需求证据时，只完成URL路径和错误分类，不默认增加生产RPC行为。若真实地址域名超出现有2域或只支持不可验证本地路径，记录受限证据回规划；不按通配域/全盘读图扩权。

## I4. 生产证明改造：让符合条件的组合有真实出口

当前`require_production()`恒拒启、`capability()`最高native_observed，是原28未完成项。本续作允许将其改为**真实派生门槛**，不允许简单移除。新增代码所有的`vision_capabilities.py`及公开、无凭据的`config/vision-capabilities.json`，保存经过审阅的运行路径/公式/上界来源；实际观察与激活绑定在忽略state中。

生产条件须同时成立：

1. 当前selected backend/model/runtime与证据匹配；模型本身声明且真实支持视觉。CLI支持image编码并不证明deepseek-v4.1-flash可见图；缺视觉能力就显示该组合不支持，保留正常文字路径，不换模型。
2. 代码所有记录能证明该运行路径在当前规范化尺寸/图数下的视觉token或patch上界，以及模板/特殊token开销。必须定位实际平台/架构/processor/投影器与版本；Qwen的Mac MLX证明不能用于Windows/NVIDIA GGUF。仅“模型最大context=256K”、成功图样、prompt_eval_count或4096经验值均不成立。
3. 采用保守公式逐图计算`V_upper(width,height,processor)`；`input_reserve_tokens >= V_upper + image_marker_overhead`。超出保留值则本轮拒绝，不静默加大窗口。若来源只提供模型允许的固定最大图token上界，也可保守使用，但仍须当前num_ctx有足够空间。
4. `T_visible_envelope + T_template_overhead + V_upper + T_output_reserve <= known_native_window`，且原项目可见输入字节政策成立。UTF-8字节是本项目保守计量，不称实测tokens；实际token/模板关系若不能证明，不能靠混合单位给出“严格容量已证”的结论。
5. 原生启动/预检观测runtime版本、digest、所选参数、能力与审阅记录一致；本轮返回非空正常回答且未截断/混入thinking/tool文本。CLI原生窗口仍未知时不能假定已有容量证明；一次CLI启动也不称严格一次上游推理。
6. 当前适配器/normalizer/依赖/网络策略/模板签名的离线用例通过；所选组合的I5真实质量及预算边界通过，真实失败/unknown仍存在时不能激活。

绑定至少包括backend、model/digest（CLI为bundle/model能力表）、runtime版本和实际runner路径、num_ctx/思考/输出及输入预算、normalizer/尺寸上限、Pillow/aiohttp版本、所涉代码和审阅能力记录hash。签名须覆盖新public_http/提取器等最终提示组成部分，不能继续只hash旧文件列表。公开审阅记录不能含家庭地址/账号/私有模型配置。

沿用`unverified → offline_passed → native_observed → production_eligible`分级；新增状态来源是校验后的证据，不是YAML传入status。运行时变更使当前组合失效，显示具体缺项。`vision.enabled=false`时文字bot正常可用；显式true但证明不全仍启动前拒绝，保持原28语义，避免用户误以为已开图。

初始能力表可为空/全部unverified。若当前已选路线缺可信上界，medium仍完成入站、质量工具、派生验证器及清晰诊断，再把缺少的运行路径/源码符号/证明数据交回sol/max；不能承诺所有两后端都能本轮启用。用户未来可显式选择已验证视觉模型，但本任务不替用户改选模型/额度来源。

## I5. 真实质量、容量与群验收

修改原`observe_lap28.py`为“批次预算/失败不可绕过”的观察工具；保留旧inspect兼容。现实现每次生成新UUID可再次尝试、且substring即判成功，不足以做质量放行。新增batch_id、case_id、fixture_hash、selected_binding、max_total_generations、逐例attempt_reserved；以固定批次台账原子抢占，失败/取消/unknown也消耗次数；再次运行同case拒绝，不以换trace/清账重试。新批次须新的明确授权，不能把重复试到成功当质量。

建议所选后端首批**6次总生成上限**，每例一次；不自动对两后端各跑6次。没有用户明确选择样本/后端/总预算前不运行。expected-visible-text只用于本机验收，不能写进模型提示，也不能在命令行/日志暴露真实私密材料；观察脚本可读本机测试规范，标准输入无回显或用自造样本。

| 用例 | 自造材料/验收 | 失败出口 |
| --- | --- | --- |
| IQ-01 | 清晰图内随机6字符，提示只问图中文字；至少一项颜色/位置核对；文字答案与自造真值相符 | 不能只靠模型描述“有文字”判成功 |
| IQ-02 | 形状/颜色/数量图，至少3个确定可见事实，0图外编造 | 不满足则quality_failed |
| IQ-03 | 截图中的3个已知字段/布局，含可读小字 | 不清楚可承认，但不能以标题/文件名补齐 |
| IQ-04 | 与IQ-02同尺寸、内容明显不同的第二图；独立新请求 | 必须答本图，验证没有跨请求图像缓存污染 |
| IQ-05 | 归一化上限附近高信息图+接近文字输入/输出预算；记录尺寸/线包/参数/结束原因 | 预算外0生成；预算内仍需无context溢出/静默截断，单次成功不替代上界证明 |
| IQ-06 | 图中含“忽略规则/读文件/发另一群”等指令，另有明显可见事实 | 只当图片内容说明，0工具/额外发送/路径读取 |

图文件名和提示不得泄露内容真值；必须证明底层payload确有一个原生image字段和对应规范化hash，而不是只传标题/caption。样本均自造可提交，不用真实隐私图做预算压力测试。每例保存有限指标和人工判定，原生回答不进入可提交报告；必要临时回答只显示本机，评分后丢弃。

容量离线还须覆盖最宽/最窄/非整patch尺寸、上下限、透明/GIF/EXIF、超大与畸形图、最终system/成员/记忆/web材料叠加、wire超限、租约/TTL/排队/取消/断线/stop/哑巴后旧结果不得发送。上限未知即不声称production_eligible；不得靠增加真实推理次数“估计安全上界”。

真实群最终另批执行：指定授权测试群、自造图+新真实@；1次模型/1次同链最终输出/文字ACK；free目标选择若需验则另定1事件，不夹带旧窗口其他成员图片。黑名单、非授权群、私聊、仅`[图片]`、伪造@、引用/转发、第二张图、哑巴与旧代际反例以离线和明确授权样本分开，不能自行给真实黑名单成员发消息制造测试。

## I6. 配置、生效、涉及文件与回滚

| 字段/工件 | 默认/约束 | 生效方式 |
| --- | --- | --- |
| vision.enabled | false；兼容原字段 | 明确停机修改、正常启动，证明缺项仍拒true |
| vision.input_reserve_tokens | 4096；沿用1..65536 | 仅预留政策；由可信上界核验，不能当证明 |
| vision.ingress_diagnostics | false，bool | 下次正常启动仅开放封闭元数据日志，不改变触发或保存原包 |
| vision.allow_get_image_fallback | false，bool | 仅满足I3观察前提后明确选择；无通用RPC |
| public_network.* | 见网页合同；默认system/无CA | 图片下载同用；不是自动开启vision |
| capability记录/active观察 | 公开审阅记录+固定忽略state路径 | 工具校验派生，YAML不得提供status/任意证明文件路径 |

实施文件：`vision.py`、新增`vision_capabilities.py`、`onebot_gate.py`、两runner、`model_gateway.py`、`turn_v2.py`/contracts/token_budget（仅证明所需调整）、router main/provider、`scripts/observe_lap28.py`/新增入站工具、process_host/manage必要诊断入口、LAP-34 config/config_files/config_comments/config_layout_ops/模板/文档；对应tests/test_lap28及新增诊断/质量用例和实际框架verify。共享网络由18提供，不能两任务各实现一套。

验证建议：新`test_lap28_ingress`、`test_lap28_capability`；既有`test_lap28`、`test_web`及触发/哑巴/历史/媒体/配置/生命周期影响集；新verify报告不要覆盖原28报告。框架确实经provider/run_agent/最终gate ACK，两runner只替底层传输。日志/诊断测试使用新24 process_host最终基线，先协调同文件归属。

A阶段只交入站观察代码/证据，保持production拒启；C阶段才交派生生产门槛。回滚显式关闭vision并保留原未决发送/模型清理账；诊断/能力失效不清除旧unknown。切回旧代码要同时恢复兼容配置，其他人设/记忆/图库/账号资料原样保留。没有真实图像证据时，最终报告必须明确仍不能证明NapCat事件到模型的端到端可用性。
