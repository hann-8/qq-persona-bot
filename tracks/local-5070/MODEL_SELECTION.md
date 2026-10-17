# 家庭5070：本地模型选择与只读盘点

返回[PROGRESS](../../PROGRESS.md) / [PC交接](HANDOFF.md) / [CLI主线计划](../laptop-workbuddy/tasks/LAP-14/PLAN.md)。2026-10-17；当前是选型建议和实机只读盘点，**没有部署、加载模型或做推理验收**。用户正在自行部署小LLM；仍先完成CodeBuddy CLI人设/有限分条，后续再接本地后端。

## 1. 授权、数据和已验证事实

用户在本轮明确追加授权通过SSH查看配置；该授权仅适用于家庭PC，与工作环境无关。SSH入口和Windows DPAPI保护的访问资料只在本机忽略的secrets/home-5070-access.local.md；主机公钥只在本机忽略known_hosts文件。跟踪文档不写入口、用户名或密码，不写Codex全局工作记忆。

2026-10-17 10:50:29（Asia/Shanghai，本机证据保存时间）实机快照：

| 项目 | SSH只读观测 |
| --- | --- |
| OS | Windows 10，版本10.0.19045；版本已读，中文edition字段编码不完整，不据此确认具体发行版 |
| CPU | AMD Ryzen 7 7800X3D，8核16线程 |
| 系统内存 | 系统可见31.16 GiB，盘点时可用16.72 GiB；可按约32GB机器规划，未独立读取内存条容量 |
| GPU | NVIDIA GeForce RTX 5070；nvidia-smi总显存12227 MiB、当时已用69 MiB，驱动576.88 |
| 磁盘可用 | C盘约71.5 GiB，E盘约268.7 GiB；不擅自搬现有模型缓存位置 |
| 推理服务 | Ollama 0.40.5进程存在；PC回环11434的GET /api/version、/api/tags、/api/ps及/v1/models可读 |
| 模型状态 | 本次tags和ps均为空；只说明快照时未列出已安装/已加载模型，用户部署可继续变化 |
| 其他候选端点 | 回环1234/8000/8080的GET /v1/models未成功；不等价于整台机器绝无其他服务 |

证据在本机忽略state/home-5070-inventory-2026-10-17.json。只读命令包括CIM硬件字段、nvidia-smi、限定进程名/命令是否存在和模型元数据GET；没有读取用户工作文件、环境凭据或群聊天。第一次盘点因输出编码未能解析，改本地解码后重读成功；2次SSH会话均未执行模型生成、安装/下载/启停或持久配置修改，远程修改0、真实模型请求0。

未验证：GPU实际推理、驱动/模型组合的加载兼容性、峰值显存、速度/首字延迟、中文人设效果、局域网监听与鉴权、SSH以外的笔记本→模型访问。本地临时SSH依赖通过uv隔离缓存使用，没有加入项目pyproject依赖。

## 2. 推荐结论

**首选Qwen3.5-9B，Q4_K_M**，Ollama明确标签为`qwen3.5:9b-q4_K_M`，作为本项目中文群聊/人设、简短问答和后续小规模结构化回复的第一验证候选。

这是根据本项目任务、已安装Ollama和约12GB显存作出的选型判断，**不是实机A/B后证明它是所有模型里最自然的结论**。先用较有余量的9B量化模型验证质量，避免一开始把主回复质量压到极小模型；如果要给游戏/其他GPU任务留更多显存或追求更低延迟，再由操作者显式选4B。

| 候选 | 官方标签与包大小 | 本项目定位 |
| --- | --- | --- |
| 首选 | [qwen3.5:9b-q4_K_M](https://ollama.com/library/qwen3.5:9b-q4_K_M)，约6.6GB；本轮库页短ID56671c2ab938 | 默认先验证的本地回复模型；非思考、短上下文、单并发 |
| 轻量备选 | [qwen3.5:4b-q4_K_M](https://ollama.com/library/qwen3.5:4b-q4_K_M)，约3.3GB；本轮库页短IDd8b0f5e9760c | 同机还需GPU余量时的替代；未来若做候选筛选可再评估，但当前不添加双模型路由 |
| 暂非首装 | [Qwen3.5标签表](https://ollama.com/library/qwen3.5/tags)中的9B Q8约10GB、27B Q4约17GB、35B-A3B约22GB | 12GB还要容纳缓存/运行时/桌面；前者余量紧、后两者包大小已超显存，不作为低延迟群聊的第一方案 |

包大小不等于峰值显存，不能用6.6GB直接承诺8K/16K上下文一定全GPU。Ollama标签可能更新，未来下载时记录完整manifest/model digest和量化类型；不用latest把具体格式留给不确定的默认选择，不混淆MLX、NVFP4与本计划GGUF Q4_K_M候选。

[Gemma 4 E4B官方卡](https://huggingface.co/google/gemma-4-E4B-it)也可作为后续表达A/B备选；E4B表示有效参数，官方列含embeddings总参数约8B，不能按字面4B推显存。当前没有本项目中文人设比较证据，不先扩成多个模型同时安装的任务。[Qwen3.5官方卡](https://huggingface.co/Qwen/Qwen3.5-9B)有多语言/非思考与模板说明，但通用榜单不证明“像真人”。

## 3. 后续验证时的初始配置建议

下表是待实施profile，不是本轮写入了PC/本机设置：

| 项 | 初始建议 | 生效口径 |
| --- | --- | --- |
| 模型 | qwen3.5:9b-q4_K_M | 操作者显式选择且实际已安装的本地tag/digest；不切换当前CodeBuddy设置 |
| 上下文 | 8192 tokens，单并发 | 原生Ollama请求options.num_ctx或项目专用模型profile控制；要通过实际加载/请求确认，和本项目UTF-8输入预算字段区分 |
| 思考 | 关闭 | 原生/api/chat传顶层think:false；OpenAI兼容接口按当前文档传reasoning_effort:"none"并实测。不能把vLLM的chat_template_kwargs随便当成Ollama通用开关 |
| 输出生成上限 | num_predict/max_tokens先1024 | 真正的生成输出上限，支持与截断行为须验证；日常篇幅靠LAP-15/16规则，不能以截短代替自然表达 |
| 采样 | temperature=0.7、top_p=0.8、top_k=20；presence_penalty按官方候选1.5先记录 | 来自官方非思考通用建议，框架字段需按实际API核对；重复/串语言时根据样例调整，非运行时自动换模型 |
| 历史/显存 | 初始只取少量完整轮次，先4轮；留约2GiB显存余量作为项目目标 | 先测实际prompt_eval/生成和显存，不能承诺固定tokens/s；不同时常驻9B/4B/ASR/视觉模型 |

依据：[Qwen非思考配置](https://huggingface.co/Qwen/Qwen3.5-9B#instruct-or-non-thinking-mode)、[Ollama思考控制](https://docs.ollama.com/capabilities/thinking)、[Ollama原生chat](https://docs.ollama.com/api/chat)、[OpenAI兼容字段](https://docs.ollama.com/api/openai-compatibility)、[上下文配置](https://docs.ollama.com/context-length)。Qwen3.5不支持把旧Qwen3的/think、/nothink文字当成可靠软切换；隐藏think显示也不等于没有生成思考。

8K是本项目短中文群聊的起点，不采用模型卡256K宣传上限做实际分配。严肃复杂推理质量与非思考短答目标不同，不为此自动启用长思考；可承认局限，保留CodeBuddy路线作为操作者显式可选方案。

## 4. 分阶段验证，不抢当前CLI主线

1. **模型准备：**用户自行部署继续；未来进入PC任务时先GET核对最新tags/版本，不重复安装已存在Ollama或打断正在下载。模型安装/加载/推理另由用户实施指令确定范围，本轮不做。
2. **离群验证：**先验证单模型8K、非思考、一次请求、严格输出协议；三类各2个短样例覆盖闲聊/角色反应/具体问题，沿用同一人设版本，不用长文benchmark代替群聊验收。
3. **质量与资源：**记录冷/热启动、总耗时、输出token与实际tokens/s、峰值VRAM、GPU/CPU offload；无证据不报速度。还需测试1/2/3气泡计划遵循、错误JSON、字面代码及少量多轮记忆。
4. **项目接入另规划：**当前config.py只允许codebuddy_cli，不能改model名或AstrBot provider地址就绕过网关。保留单QQ入口、人设/预算/纯文本/回复计划/ACK约束；新增后端须单独确定配置、工具隔离、鉴权、上下文和回滚合同。
5. **拓扑先比较：**优先评估笔记本保留QQ入口、PC只提供模型，以复用用户现有部署并减少同号迁移；两机常在线与受控连接是前提。SSH隧道/鉴权代理或全套迁PC在后续任务中选，当前不开放无鉴权端口、不复制QQ/CodeBuddy登录目录。
6. **未@参与另规划：**本地模型连通不启用旁听/概率/主动任务；联网工具也单独列LAP-18中优先级。当前模型选型不授权这些行为。

若9B资源不足先缩原生上下文和并发，再由操作者明确选4B；不存在自动转付费API或云端fallback。没有质量/资源验收前，结论只能是推荐候选，不能写本地路线已交付。

## 5. 和历史预案的关系

[DEPLOYMENT_PLAN](DEPLOYMENT_PLAN.md)原Qwen3-8B/周末全套PC迁移是2026-10-15历史预案，不是用户已经安装的事实，也不再作为本轮首选。用户现在已有Ollama，本轮按实际机器更新候选为Qwen3.5-9B Q4_K_M；历史视频/ASR目标继续保留，不能在当前文本路线中顺手开启。未来部署前仍应核对当日版本及用户实际已安装模型。
