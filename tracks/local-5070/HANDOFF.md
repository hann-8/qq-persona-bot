# 5070 PC 本地模型工作线

返回[PROGRESS](../../PROGRESS.md) / [LAP-19计划](../laptop-workbuddy/tasks/LAP-19/PLAN.md) / [TASKS](../laptop-workbuddy/TASKS.md)。继承[AGENTS](../../AGENTS.md)，家庭访问与工作环境隔离。

更新时间：2026-10-17 15:21（Asia/Shanghai）。状态：planned；**用户已完成模型安装并加载，项目只读元数据/SSH回环转发通过，后端尚未接入**。LAP-19仅规划，后续17本地接入/切换→18共用联网→20自由群聊→21表情包，详见[追加合同](../laptop-workbuddy/tasks/LAP-19/GROUP_CHAT_PLAN.md)和[执行指引](../laptop-workbuddy/tasks/LAP-19/IMPLEMENTATION_GUIDE.md)；free已纳入本轮规划，未启用。

## 最新已验证事实

2026-10-17 14:53:59 +08:00，通过既有家庭SSH凭据和固定既有SHA256主机指纹，只读得到：

- Ollama0.40.5，11434监听分类仅loopback；已装`qwen3.5:9b-q4_K_M`，GGUF/Q4_K_M/9.0B，6550825550字节。
- digest为`56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`；模型已加载，context_length=16384，size_vram=6147423600字节；RTX5070整卡显存快照7019/12227MiB。
- show允许think:false/true，默认true，标称窗口262144；completion/vision/tools/thinking只是元数据声明，本项目不因此启用视觉或工具。
- SSH direct-tcpip访问PC127.0.0.1:11434的GET /api/version返回200，未建立持久本地转发监听。

本机忽略证据state/lap19-pc-metadata.local.json。既有known_hosts为空，首次严格检查拒绝；随后使用10:50盘点留存指纹，认证前比对通过才连接，不自动信任新指纹、不改SSH配置。入口/账号/DPAPI凭据仅在忽略secrets，未输出/提交；临时Paramiko只在uv隔离环境。

旧10:50硬件盘点Windows10/7800X3D/约32GB/RTX5070和[MODEL_SELECTION](MODEL_SELECTION.md)保留；当时空tags已由新观测更新，不能再据此说未安装。模型安装/加载由用户完成，本轮只读查看，不读取私人聊天或工作文件。

## 已规划的接入合同

保留笔记本唯一NapCat/gate/AstrBot/模型网关，PC只提供Ollama；CLI不依赖PC在线。本地原生chat走固定SSH通道，单次POST/单并发、think:false、请求级num_ctx初始16K/生成1024，实际生效/资源仍待验证。配置cmd分别保留两套参数，停机保存/重启生效/手动切换，失败不自动换后端；切换新建当前上下文，旧历史保留。

PC使用前提是开机不睡眠、Ollama后台运行、SSH可达；接入完成后不要求一直开ollama run聊天窗口。停机器人只释放本项目连接，不关闭用户Ollama。联网由笔记本网关共用受控检索，打开本地Ollama本身不会自动赋予搜索；提供方/质量/预算/来源/失败处理见LAP-19。

原[DEPLOYMENT_PLAN](DEPLOYMENT_PLAN.md)全套迁PC/Qwen3-8B/周末预案为历史，不直接执行；原模型选择8K候选由LAP-19按当前16K加载更新为新的试验起点，未实际改参数或承诺速度。

## 未验证与下一步

未验证项目模型生成、think:false/结构化输出/实际窗口、峰值显存/速度/风格、超时后远端停止、联网质量或QQ接入。加载/GET成功不能代替这些验收；本轮远程修改/下载/安装/启停/模型生成0，当前bot状态未探测。

后续17先完成schema3/profile/菜单/SSH原生runner与离线回归，18独立联网，20/21按追加合同实现自由参与/表情。真实推理/群启用按后续范围登记；不把仅规划的free当当前已放开准入，不关闭旧验收差额。
