# 笔记本 WorkBuddy 工作线交接

返回[全局入口](../../PROGRESS.md)。继承[AGENTS](../../AGENTS.md)；原规格见[实施计划](IMPLEMENTATION_PLAN.md)，本轮体验改进执行[UX_PLAN](UX_PLAN.md)，验收见[ACCEPTANCE](ACCEPTANCE.md)，领取/交接见[任务台账](TASKS.md)。本轮任务记录：[LAP-08](tasks/LAP-08/HANDOFF.md)。

更新时间：2026-10-16 23:41（Asia/Shanghai）。本次任务[LAP-11](tasks/LAP-11/HANDOFF.md)已实现/离线通过，未部署，真实验收待补。用户授权提交/推送，开始工作区干净。

LAP-11交付提交`d00d11f`已推送origin/main；本记录随后以文档提交同步，未部署。

## 当前状态与第一步

文字核心已有历史证据，完整文本交付未完成。LAP-11网关单次纯文本转换、固定政策/人设v2、实际框架原文保留与版本迁移已落地；82项单元、5组provider/runner/保存/装饰/OneBot模拟ACK及入口反例回归通过。见[LAP-11报告](../../reports/lap-11-2026-10-16.md)。本轮未启停、改实际配置、登录、真实推理或群发，实例未加载新代码，当前状态未重新探测。

当前无需用户登录。后续实际部署/QQ ACK、人设P01需用户在NapCat按需登录并参与；下次请求会因组合人设hash变化新建当前上下文，旧会话不删。本轮只交付LAP-11，不自动领取LAP-12。

LAP-10独立预算/参数实现和high真实证据保留；原生窗口仅ACK未证实，force压缩/内部恢复可绕过普通关闭开关，不能保证严格单次上游推理。见[LAP-10报告](../../reports/lap-10-2026-10-16.md)，需符合AGENTS要求的规划会话处理，不能因LAP-11离线通过而默认整体可部署。

LAP-09历史检查点：配置菜单及groups/blacklist命令、共享校验/迁移/原子保存、gate/router黑名单静默前置拒绝已落地；当时53项单元测试及实际AstrBot router/At转换器离线回归通过，未真实推理。详情见[LAP-09报告](../../reports/lap-09-2026-10-16.md)。本机存活身份检查拒绝写配置，旧运行实例未更新；提交不代表部署或完整验收。

以下为22:10规划阶段历史记录（LAP-09最新结果以上段为准）：

- 上次21:35前后执行`./scripts/Show-BotStatus.ps1`：进程在、router_ready=true、queue=0、active=false、cli_attempts=7、backend_state=ready，最后模型成功21:21:24。是历史快照，本轮未重新探活，不能当作22点的实时状态。
- 历史失败模型追踪11aacf9b18：21:02:07接受并启动CLI一次，21:02:23返回BACKEND_UNAVAILABLE；业务追踪a0c16673b2于21:02:24标failed。具体上游原因未保留，不能猜成登录失效、额度耗尽或断网。两种追踪ID不同。
- 本次以SQLite只读连接复核任务库：累计completed=9、failed=1；该失败后21:12:42、21:16:15、21:17:16、21:21:25各有1条completed，最后业务追踪bc9b6f9210。仅查询trace/status/updated和计数，没有读取聊天正文。任务完成计数不等于功能验收通过率。
- `last_error`仍指向历史失败；源码`model_gateway.py`成功时更新state/last_success但不清空last_error，因此它与ready同时出现不能直接判定当前持续故障。仅确认之后有请求成功，尚无“已定位/已修复”证据。
- 用户说明NapCat未登录记为现场事实；旧模型追踪已出现CLI_START，现有日志没有证明跨层因果，不伪报技术根因复现。没有新独立失败时不为旧trace循环真实推理。
- **下一实施会话第一步：**先读AGENTS、PROGRESS、本文件、TASKS和UX_PLAN，核对git status；LAP-09实现/离线已完成，真实差额见其交接；新实施按用户后续指令领取LAP-10，不自动开始。不要重装或从G0重新开始。
- 本会话已核对用户六项反馈并读取指定人设v2；上下文重点为模型输入上限，聊天轮数为辅助。仅编辑文档，未改运行人设/配置、代码、原Obsidian笔记或服务状态；未调用模型、发群消息、提交推送。

## 代码与Git检查点

以下前三条为22:10规划历史检查点；本轮新增实现/验证以顶部LAP-09报告及任务交接为准。原规划修改全部保留，按用户最新授权与LAP-09一起交付提交；不将历史“未改代码”描述为当前状态。

- 分支main；实现提交4560ab6，已push至origin/main（https://github.com/hann-8/qq-persona-bot）。本会话开始时代码与该提交一致；已有5份已跟踪文档修改及TASKS.md来自上次盘点，已保留。
- 本轮新增AGENTS.md、UX_PLAN.md、tasks/LAP-08/HANDOFF.md；同步PROGRESS、TASKS、本文件、ACCEPTANCE、IMPLEMENTATION_PLAN及REQUIREMENTS。共9份文档，未改源代码、脚本、config/persona.md、settings.local.yaml或版本锁，未提交推送。
- 旧39项离线测试仅是当前旧实现证据，本轮未重跑。新增U01—U20均是待实施合同；文档链接/一致性核对记录在LAP-08交接，不冒充运行验收。
- info.txt本机文件保留且已停止跟踪，.gitignore排除它及本机参数、secrets、state、runtime、logs等。既有Git历史仍有用户旧参数文件，已提醒更换密码；不自动改写历史，不读取/使用其中密码。当前账号/群标识从config/settings.local.yaml取，凭据只在被忽略路径。

## 已验证与重要修复

| 范围 | 证据与结论 |
| --- | --- |
| G0 | [报告](../../reports/g0-2026-10-16.md)：用户自行安装的官方CodeBuddy CLI2.168.0，同WorkBuddy账号/站点，指定模型调用、system/history、工具隔离、编码和超时树清理/恢复通过。桌面内置CLI早期失败，不回退该路线，ACP不进入主线。精确credits扣减未核验。 |
| G1 | [报告](../../reports/g1-2026-10-16.md)、[版本锁](../../config/versions.lock.json)：项目Python3.12.15、uv0.13.1、AstrBot4.29.0、普通Node24.22.0；NapCat4.18.38+独立QQ9.9.33-52230，未改日常D:/QQ。 |
| G2 | [报告](../../reports/g2-2026-10-16.md)：严格准入/认证/去重/出站动作控制与WS传输离线通过；真实登录与self_id握手通过。 |
| G3 | [证据](../../reports/g3-2026-10-16.json)：实际AstrBot provider本机真实请求1次成功、CLI1次；429/超时/坏协议模拟各仅1次尝试。 |
| G4 | [记录](../../reports/g4-2026-10-16.md)：用户真实@介绍成功，无@普通文字静默；修复后口令两轮正常纯文本。39项离线测试通过。实际框架事件+router+内存会话替身验证同用户保留历史、跨用户/跨群为空、无At无请求；不是多人群人工验收。 |

必须保留的修复：

1. AstrBot群名片为空会回退get_stranger_info获取@目标昵称；原gate拒绝后框架丢弃真实At。现仅允许查询配置bot自身昵称，其他用户仍拒绝。`scripts/verify_g4_adapter.py`用实际安装转换器复现旧失败和修复，无网络调用。
2. `--tools ""`不足以禁用工具；`--disallowedTools`必须将每个名称分别传argv，逗号合并无效。使用config/cli-tools-denied.json并校验init tools/MCP为空，不能删除该检查。
3. 工具空和`--setting-sources none`仍不关闭CLI MemoryContextInterceptor。它曾导致模型将Write/Read的DSML文本发到群里，口令首次验收失败。现仅在CLI子进程禁用自动/团队记忆及记忆辅助服务；parser拒绝DSML/tool-call结果，trim_history排除污染完整轮次。没有实际文件写入证据，不将生成文本当工具执行。`scripts/verify_g4_memory.py --real`同模型本机两轮精确回忆，2请求/2次CLI、新增CLI memory文件0，见[证据](../../reports/g4-memory-2026-10-16.json)。

## 实现入口与运行方法

- 自有代码：src/qqbot_gateway/{onebot_gate,model_gateway,workbuddy_cli_runner,contracts,session_queue,task_store,text_safety,config,errors}.py；唯一业务插件plugins/qq_router/main.py。AstrBot唯一保存历史，按群+用户隔离、最多8轮，CLI每请求新上下文；同UMO FIFO、5秒冷却、模型全局单并发。
- 仓库config/persona.md已采用人设v2草案；persona.py固定政策优先、统一版本hash，运行实例未更新，最终风格接受待LAP-03。默认模型仍deepseek-v4.1-flash；最新需求允许操作者显式设置模型、上下文输入上限和强度，额度不必极限节省，仍不自动换账号/站点/模型或另接收费API。
- 隔离实例：runtime/astrbot；框架Python为runtime/astrbot-tool/astrbot/Scripts/python.exe，框架验证脚本用它运行，CWD须为runtime/astrbot。项目服务/离线单元测试用.venv/Scripts/python.exe。
- 本机PowerShell：`scripts/Start-Bot.ps1`完整文本模式；`-ChannelOnly`仅诊断；`scripts/Show-BotStatus.ps1`无推理健康检查；`scripts/Stop-Bot.ps1`按state/managed-processes.json中PID+创建身份停止本项目进程。不要重复启动，不按QQ.exe进程名批量停止。
- 回环端口：AstrBot管理页6185、OneBot6199、gate6200、模型8765、NapCat6099。state/router-ready.json验证插件PID/创建身份。运行配置cmd_config.json有UTF8 BOM，读utf-8-sig；不要覆盖用户日常应用配置。
- `scripts/Test-Bot.ps1`为39项离线测试；`scripts/verify_g4_adapter.py`及`scripts/verify_g4_routing.py`为额外离线框架集成验证；带--real的verify_g3.py/verify_g4_memory.py会消耗真实额度，不当健康探针循环运行。
- [使用说明](../../README.md)。日志仅保留结构元数据，原始错误被process_host.py丢弃，这是当前上游诊断信息不足的原因之一。

## 剩余工作与任务归属

1. LAP-09共享配置/授权群/黑名单已实现/离线通过，U04/05真实群及U07全组件重启待验；LAP-10参数/预算独立实现、70项离线及high真实通过，原生窗口及force压缩/内部恢复缺口需先回规划。LAP-11纯文本/人设v2已实现/离线通过、真实待验；LAP-12启停/状态未实施，详见UX_PLAN及LAP-10报告。
2. LAP-01合并到LAP-12，不抹掉历史trace限制；只有出现新的独立模型失败再重开。上下文原生控制仅有静态候选证据，实施时先零推理验证，不用autoCompactWindow冒充上限。
3. 原LAP-02真人交错/隔离/重置和P02三轮差额、LAP-03最终人设接受、LAP-04恢复/文本长稳、LAP-05交付汇总全部保留。旧基线不无故重跑；新代码触及的路径必须重做相应有意义回归。
4. LAP-06/07视频/ASR仍延期；目前遇链接只说明未支持。已有BV178JX6wEaa样本，进入相关阶段再补其余样本/登录意愿；PC不启动。
5. 任务归属见台账；LAP-09交付后按用户明确指令转入LAP-10，LAP-11本轮已独立交付，LAP-12未领取。真实@入口、无工具/主动任务/项目自动重试/fallback保持，成功路径不stop_event；CLI内部强制压缩/恢复仍未排除，不冒充上游严格单次推理。

本次交接可恢复：读取PROGRESS→本文件→TASKS→被领取任务的记录及相关代码/证据，不必重读全部历史报告。代码已增加LAP-09、LAP-10独立实现及LAP-11纯文本/人设，实际运行实例尚未重启加载。
