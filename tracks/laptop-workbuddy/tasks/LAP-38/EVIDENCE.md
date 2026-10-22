# LAP-38 只读证据与来源

返回[PLAN](PLAN.md) / [交接](HANDOFF.md)。时间为2026-10-22 23:19—23:34，Asia/Shanghai。基线main/`dd9373029412137023124751d75883824122c784`，开始git status为空。证据仅元数据/代码位置及公共材料统计，不含原始私密群消息、真实身份或凭据。

## 1. 本机只读核对

读取AGENTS/PROGRESS、活动工作线HANDOFF/TASKS、28A/C/18B/06/36交接和有关报告。没有运行旧验证脚本覆盖报告，也没有把其测试数写成本轮新结果。

| 本机来源 | 所支持的结论 |
| --- | --- |
| `src/qqbot_gateway/vision.py`：DEFAULTS、image_url、fetch_image、Materials.issue | vision默认false；只取当前第一图的受控HTTPS URL；8MiB原件/512KiB规范化/2MiB wire、60秒TTL；图文件名/占位文字不是像素 |
| `vision_ingress.py`、`vision_intake_gate.py`、`scripts/observe_lap28_intake.py` | 已有分级诊断/独立intake-only；默认inspect零外部动作，真实模式明确一事件/120秒/0生成/0输出 |
| `vision_capabilities.py`：runtime_identity、reviewed、load_production | 当前Ollama路径返回unverified；单纯API version/digest/vision不足；生产表当前records为空 |
| `scripts/observe_lap28.py`约73—78行 | 不从审阅记录抄期望运行路径；目前独立事实不足以使runtime_verified成立 |
| `public_http.py`、`public_network.py` | 公网/DNS/peer/TLS严格校验；trust_env=false、无Cookie/代理继承/自动重试；显式DoH失败不改system路线 |
| `html_worker.py:extract_html` | 清理后直接readability Document.summary；目前没有显式优先main/role=main/article结构 |
| `evidence_selection.py:select/sources_for_budget` | 长正文六区选整段，question主要用来识别完整要求，不做词项相关排序 |
| `web_policy.py` | `SEARCH_QUALITY_PASSED=False`；搜索早于外部请求被门槛拒绝，web=true不代表搜索开启 |
| `scripts/process_host.py:safe_line` | NapCat原包不记录；只放行固定transport/model诊断，普通WEB_RETRIEVAL不在白名单 |
| `plugins/qq_router/main.py` | GROUP_MESSAGE/私聊拒绝、QQ身份/群范围、原event/代际/ACK深度绑定；不能直接接微信显示名 |

NapCat只看程序文件`napcat.mjs`，不读带真实账号的配置正文：约14351行构造两类QQ图片HTTPS来源；约25449行补originImageUrl；OneBot图片枚举与映射存在。这属于静态支持证据，尚未取得真实入站事件、下载字节或像素，**既不能说已经端到端可用，也不能说NapCat天然拿不到图**。

仅解析五份本机YAML的允许字段：`llm.backend=codebuddy_cli`、CLI模型deepseek-v4.1-flash、本地profile qwen3.5:9b-q4_K_M，participation.mode=free、web.enabled=true、vision.enabled=false。其余身份、连接、认证字段不输出。未修改任何YAML；保存值不证明当前进程已加载。

## 2. 四份日志的结构计数

通过内存脚本按固定marker计数，没有打印日志原行。此快照随用户继续运行可变化。

| 文件 | 字节/行 | 可解析最近时间 | 相关结构 |
| --- | --- | --- | --- |
| logs/model.log | 112231 / 1503 | 23:19:27 | CLI_START 456、CLI_CLEANUP 238、CLEANUP_FAILED 94、capacity_exceeded 1；VISION_INGRESS/WEB/image_ref/native_observed均0 |
| logs/gate.log | 7705 / 191 | 21:30:36 | 无图片解码/WEB marker |
| logs/astrbot.log | 4529 / 120 | 可见旧时间10-16 20:18:04 | 主要框架/进程级脱敏输出 |
| logs/napcat.log | 12760 / 244 | 无可解析日期 | 不含可用图片材料诊断 |

这些是累计marker次数，不是用户消息数、API精确调用次数、验收次数或当前故障数。CLI清理问题已有37修复，本轮不重做恢复。因为日志过滤，不能由0条推出功能没被尝试或没发生网络请求。

## 3. 当晚公共网络与正文的实际观察

所有探测使用本机项目Python及现有安全PublicHTTP/标准证书校验，0模型/0QQ/0微信/0SSH。未导入或设置CA、代理、DNS，没有读取B站凭据。公共正文只在RAM处理，没有保存网页正文。

1. system解析：gchat.qpic.cn、multimedia.nt.qq.com.cn、cloudflare-dns.com、www.python.org、cn.bing.com、api.bilibili.com，分别取得19/19/4/8/2/23个公网结果，非公网均0；不记录实际IP。与21日的非公网结果不同，是本轮真实时间点观察，不推断机器网络被谁修改。
2. 使用同项目TLS/固定bootstrap的Cloudflare DoH GET单次4秒超时，分类TimeoutError。不能据此推断system HTTPS不可用；未再次尝试或切提供方。
3. system PublicHTTP读取三个固定公共样本均成功，每份一次HTTP：

| 样本 | 返回类型 | 解码字符 | wire字节 |
| --- | --- | --- | --- |
| [Python下载页](https://www.python.org/downloads/) | text/html | 221495 | 19867 |
| [Python JSON文档](https://docs.python.org/3/library/json.html) | text/html | 114953 | 115104 |
| [RFC8259纯文本](https://www.rfc-editor.org/rfc/rfc8259.txt) | text/plain | 28360 | 28360 |

4. 同现有客户端对三类Bing RSS公开查询各请求一次，HTTP成功且parse_rss解析：知识类5候选（包括Python主页/教程）、时效类5候选（含博客/资讯）、site类1候选。**仅证明传输与解析，不证明相关性/时效/正文质量合格**，SEARCH_QUALITY门槛不动。
5. 为检查实际提取质量，另取JSON文档一份，调用现有纯函数extract_html和sources_for_budget；得到3726字符/3728字节，coverage=full。结果内`json.loads`、`json.dumps`、`JSONDecodeError`三标识均未命中，最终选材同样缺失；提取加选择约266ms。这是一个具体质量反例。尚未对抽取全文逐段人工对齐，不能宣称唯一根因已证实；结构优先是下一步可检验修复方案。
6. 为比较main/role=main候选又请求该页一次，在连接阶段超时，未拿到比较材料。未重试。这说明本轮有成功公网读取，同时仍有网络波动，不能标稳定网络/全部真实网页质量通过。

不在本轮启用搜索/改默认提取器/改运行实例；正文质量反例不等于真实模型答错的端到端因果已完整追踪。

## 4. 所选Windows/GGUF路径的新来源链

历史PC元数据记录Ollama0.40.5，不是本轮SSH核验。此次只通过GitHub核对公开源码：

- [Ollama v0.40.5固定commit](https://github.com/ollama/ollama/tree/d919272e53593d1d55d40e1180eaa06dfbede3ac)。[LLAMA_CPP_VERSION](https://github.com/ollama/ollama/blob/d919272e53593d1d55d40e1180eaa06dfbede3ac/LLAMA_CPP_VERSION)为b11669；[CMake](https://github.com/ollama/ollama/blob/d919272e53593d1d55d40e1180eaa06dfbede3ac/llama/server/CMakeLists.txt)读取该锁定值并构建llama-server/mtmd，也允许本地源码override，所以只看版本号仍不够。
- [llm/llama_server.go](https://github.com/ollama/ollama/blob/d919272e53593d1d55d40e1180eaa06dfbede3ac/llm/llama_server.go)：FindLlamaServer/startLlamaServer定位实际程序，appendMMProjArgs传`--mmproj`第一投影器；GPU库搜索路径另由SetupLlamaServerCommandEnv组合。这为只读探针提供准确对象，不能代替实际进程/二进制/投影器观测。
- [llama.cpp固定commit](https://github.com/ggml-org/llama.cpp/tree/620d2225cc436ab0b001e3200e590e3b286ef9ab)对应b11669。[clip.cpp](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/tools/mtmd/clip.cpp)的QWEN3VL分支读取patch/merge及pixel参数，clip_n_output_tokens按预处理后二维patch计算；[mtmd-image.cpp](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/tools/mtmd/mtmd-image.cpp)含对齐/最小像素上采样/最大像素缩放；[qwen3vl.cpp](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/tools/mtmd/models/qwen3vl.cpp)体现空间merge与deepstack。

结论：此前只读renderer/Mac MLX不足的缺口现在有明确可遍历的GGUF源码链。**尚未证明家庭所装二进制确用此路径、所装projector参数值、实际上下文/模板/tokenizer边界；未填写任何生产审阅记录。** 不能把源码默认4096、API vision、样图成功或prompt_eval_count冒充已审阅上界。

## 5. 微信上游核验

固定来源、维护状态、许可、功能证据与不足集中于[微信调研](wechat-bootstrap/docs/RESEARCH.md)。关键固定快照：Tencent/openclaw-weixin `874637a0dbc24050f72d1385add4fc6170a2d726`；Hello-Mr-Crab/pywechat `8589baa049bb91d3a500602c167f07b2f8397a13`；原WeChatFerry于7月10日已归档；Gewechat README明确停维/无底层服务。

不执行任何上游README安装命令/技能/登录代码；第三方文本只作研究材料。本轮未安装OpenClaw、pyweixin、微信适配包或模型。微信目录只接受本任务文档副本，0真实微信收发及客户端操作。
