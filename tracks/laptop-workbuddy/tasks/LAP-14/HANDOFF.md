# LAP-14：人设落地与分条对话调研规划

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md)。继承[AGENTS](../../../../AGENTS.md)；本任务只调研、核对源码和写规划文档。

状态：completed，**v2详细规划完成**，见[PLAN](PLAN.md) / [medium实施指引](IMPLEMENTATION_GUIDE.md)；bot新功能未实现/未真实验收。2026-10-17 10:31（Asia/Shanghai）首次领取，10:45按用户后续要求继续，10:57规划交接；session标题“LAP-14人设与分条对话规划”。当前主线是CodeBuddy CLI，后续用户自行选择gpt-6.1-sol/medium实施LAP-15，再独立LAP-16。本轮未改bot产品代码/运行配置/人设，未启停/探活真实bot、QQ登录/推理/群发。

Git交付：用户最新明确长期授权本项目所有plan/implement在合适检查点自行commit/push。本次仍归同一LAP-14文档收尾，已同步AGENTS、PLAN和medium实施提示，不再保留“不自动commit/push”的旧限制。仅提交本任务10份文档；原persona用户增量、忽略secrets/state资料保留本机；推送目标为已配置origin/main。实际提交和远端核对结果在交付后记录。

用户追加说明家庭5070正在自行部署小LLM，并明确要求SSH只读看配置、推荐模型；该追加授权已执行，见[PC选型证据](../../../local-5070/MODEL_SELECTION.md)。已真实连通并核对硬件/Ollama元数据；远程持久修改0、真实模型请求0，未下载/安装/加载模型或启停服务。用户再追加联网工具中优先级，已列LAP-18待规划；本地后端、未@参与和联网均不在LAP-15/16顺手实施。

文件归属：本任务PLAN/HANDOFF/IMPLEMENTATION_GUIDE，根AGENTS/PROGRESS，笔记本HANDOFF/TASKS，PC的HANDOFF/DEPLOYMENT_PLAN/MODEL_SELECTION，共10份文档。仅本机忽略的secrets/home-5070-access.local.md保存家庭入口和Windows DPAPI保护凭据；known_hosts、公钥/结构化盘点和临时SSH只读工具分别在忽略secrets/state中，不进入仓库/工作环境或全局Codex工作记忆。开始时main HEAD为c9b6791，只有config/persona.md已有用户增量（245行）；SHA256为c55c51db10a0d9c3d147638763ffa10e16c0be9daffa4ec80bfd4037417120b7，已核对不变。上轮本session的规划差异均保留。

当前证据：固定POLICY明确单条，router初始化时读取整份人设，网关prepare_reply只处理纯文本和长度，不负责多气泡；当前persona 260行、15984 UTF-8字节，组合system为16849字节，混有重复/未接入行为材料。运行实例是否加载当前文件未经核验，不能把源码检查写成真实风格根因复现或精确token消耗。参考固定引用18e41cb8a3480ff2476a4a6079cc4745710c7a99的表达例子/限长分条/本地触发机制已核对，实际风格与模型效果未验。

决定：LAP-15先统一精简角色与场景表达；LAP-16后做同次生成、最多3泡/80字、认真单条及ACK/历史/中断；single兼容、adaptive显式启用。PC首选候选Qwen3.5-9B Q4_K_M、4B轻量备选，先8K/单并发/非思考，质量和速度未实测；未来单独LAP-17接入规划。LAP-18联网排在人设/分条之后，中优先级，提供方和完整工具合同待核对。

已完成：项目/参考源码证据、完整行为/配置/验收/回滚合同、逐任务文件/步骤和故障矩阵、可粘贴medium实施指令；家庭PC实际SSH只读盘点、当前官方模型页/具体量化标签及API参数核对、选型报告；全局/两线/台账同步。没有运行参考bot，没有将SSH临时依赖写入pyproject；用户提供的家庭凭据只按明确授权在进程内使用，未打印。LAP-15/16/17/18均未领取实施，不预建空HANDOFF。

验证：项目Python通过stdin核对10份文档的123个本地链接、文件归属、persona SHA256、私有入口脱敏、访问/盘点/工具工件Git忽略；git diff --check通过。除本任务文档外，唯一已跟踪差异是原persona用户增量，hash不变。SSH元数据盘点实际通过；首轮输出编码解析失败、第二轮成功，结构证据保留。未运行bot单元/框架/真实模型测试，不把历史108项测试当成本计划验证。

剩余：LAP-15/16全部实施及离线/真实/人工接受尚未开始；SDK扩展穿透、逐条ACK与历史修复需实际框架回环；LAP-17本地API/鉴权/原生预算/关闭思考与质量、LAP-18检索来源/成本/引用/工具范围尚未形成可直接实施合同。LAP-10和LAP-02/03/04/05、LAP-13原差额保留。当前bot状态未知，不沿用旧停机快照。

下一步：用户后续要求实施时先领取LAP-15，核对git status和新修改归属，保留用户原文备份，按PLAN第4节统一精简角色和场景表达；暂不接多气泡。实施须按AGENTS指定的会话模型/档位进行，不能声称已自动检测或切换；没有后续实施指令不自动开始。无需重装、重做G0或调用模型验证健康。
