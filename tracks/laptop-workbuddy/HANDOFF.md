# 笔记本 WorkBuddy 工作线

返回[全局入口](../../PROGRESS.md)。继承全局要求；细节以[实施计划](IMPLEMENTATION_PLAN.md)、[验收矩阵](ACCEPTANCE.md)为准。

状态：G0/G1通过；G2真实握手通过；G3本机真实provider通过；G4单条及修复后的群多轮通过，离线会话隔离通过；完整人工隔离/长稳待验。更新时间：2026-10-16（Asia/Shanghai）。

## 当前检查点与下一步

1. 初次真实@无回复：gate准入4条、tasks为空、CLI0；本机AstrBot认证日志API确认At昵称解析ActionFailed1403。群名片为空时框架回退get_stranger_info被拒并丢弃At。已限定允许查询bot自身昵称；其他用户仍拒绝，入站规则不变。scripts/verify_g4_adapter.py使用安装的实际转换器复现旧失败、验证修复，无网络调用。
2. 20:51:01重连后用户介绍测试收到1条正常胖鱼回复；健康页CLI1次、任务completed、发送ACK确认。随后普通文字无@静默，但两轮口令出现原样DSML Write/Read文本，P02失败，立即精确停止服务。没有实际CLI memory文件写入证据，不能将模型文本当真实工具执行。
3. 固定CLI源码确认默认MemoryContextInterceptor注入自动记忆指导。已加仅子进程生效的自动/团队记忆、抽取/相关性禁用环境开关；parser拒绝DSML/tool-call文本；trim_history排除受污染完整轮次，未手工删除数据库。39项离线测试通过。
4. scripts/verify_g4_memory.py --real本机实际AstrBot provider两轮通过：同账号/指定模型/相同人设，随机口令第二轮精确回忆，2请求/2次CLI，新增CLI memory文件0。证据reports/g4-memory-2026-10-16.json；不是QQ群验收。
5. 已恢复文本服务，20:56:01真实QQ握手及router_ready=true。用户确认新口令两轮正常纯文本；健康页CLI2次、错误null，新增2任务completed，历史3完整轮次/DSML0。scripts/verify_g4_routing.py以真实框架事件/unique session构造器+真实router、内存会话管理器替身验证同用户保留、跨用户/跨群为空、无At无请求，通过且无模型/网络调用。不是多人群人工验收。
6. 当前文本测试版可继续试用。下一步先核对真实跨用户交错/人设接受与运行恢复，再按用户文本优先安排视频；视频缺无字幕/受限样本与登录意愿，不擅自猜参数。README.md已补启停/配置/限制。不请求用户重复已通过的口令测试，不重放旧消息。

运行命令：scripts/Start-Bot.ps1完整文本模式；-ChannelOnly仅诊断；scripts/Show-BotStatus.ps1只读健康无推理；scripts/Stop-Bot.ps1按记录PID+创建身份停止本项目进程。回环端口AstrBot6185/6199、gate6200、model8765、NapCat6099。state/managed-processes.json记录身份，state/router-ready.json验证插件就绪；日志仅结构元数据，不导出原始群内容或凭据。

G3/G4实现：严格文本HTTP契约、CLI NDJSON解析、单并发FIFO、总期限和取消清理；唯一qq_router显式request_llm接管，同UMO FIFO、8轮短历史、5秒冷却，测试人设config/persona.md。禁止默认LLM旁路/工具/压缩/fallback。G3真实provider调用1次成功，429/超时/坏协议模拟各尝试1次，见reports/g3-2026-10-16.json。G4报告见[当前验证记录](../../reports/g4-2026-10-16.md)。B站本阶段未接入，不基于URL猜内容。

## 参数与不变约束

用户info.txt提供bot/admin/测试群；仅提取标识到被忽略的config/settings.local.yaml，不使用/复制其中密码。用户确认微信登录、独立CodeBuddy CLI与WorkBuddy**同一账号同一站点**；指定deepseek-v4.1-flash，报告1700 credits/每日100，精确扣减不可核验。保留模型入口、节省token，不自动切换、不提供独立API Key。

用户授权自行设计大肥鱼人设，无3组问答，最终人设仍需人工验收。仅1个B站样本，用户明确视频低优先级，样本通过非当前文本交付前提；无字幕/失败样本和B站登录意愿待补，不阻碍文本线。

个人QQ+NapCat独立副本+外置严格WS gate+AstrBot，唯一业务qq_router。AstrBot唯一维护历史，按群+用户隔离；CLI每请求新上下文。modalities必须[text]，禁默认重试/压缩/fallback；成功路径不stop_event。视频后续瞬时system证据不入完整历史，ASR必须可终止子进程。不能擅自改变账号、额度和触发规则。

## 已完成与证据

- [G0报告](../../reports/g0-2026-10-16.md)：桌面内置CLI5.8.2首次失败（退出0但error_during_execution；首版漏采errors，具体原因未知），不再重试该路径；ACP只读未发现新鲜Gateway。用户随后自行安装官方独立CLI2.168.0，确认同账号/站点后继续，指定模型多次成功，init tools/MCP均空，system/history/中文emoji/换行/伪system及哨兵隔离通过。采用--tools空参数，并逐项传--disallowedTools（逗号合并无效）。不启用ACP或/gateway。
- [G1报告](../../reports/g1-2026-10-16.md)、[版本清单](../../config/versions.lock.json)：uv0.13.1、Python3.12.15（项目安装、无注册表/PATH修改）、项目.venv、独立uv tool AstrBot4.29.0。AstrBot管理页HTTP200。普通Node为C:/Program Files/nodejs/node.exe v24.22.0，同等回归通过，不依赖Codex私有Node作为最终路径。
- 超时证据以g0-4eb446b67c9b为准：taskkill退出128因嵌套Job退出竞争，不单凭退出码判成功；psutil超时前捕获4个后代及创建身份，等待后全部退出，process_tree_cleanup_verified=true。下一请求g0-8ac6e1852519成功。早期只验证根退出，已补足完整树证据。
- NapCat固定v4.18.38 OneKey/Shell、腾讯官方QQ9.9.33-52230安装包预置后执行官方安装器，独立副本runtime/napcat/installer/NapCat.52230.Shell。未改D:/QQ，未运行包内按QQ.exe名称结束进程的脚本。源码仓库main与二进制版本不一致，不宣称源码复现；本机hash用于追溯，不冒充独立真实性校验。
- [G2报告](../../reports/g2-2026-10-16.md)：严格准入/双向认证/第二连接拒绝/出站action限制/echo/心跳/SQLite去重/断线重连离线通过。16项unittest通过（G0协议6+G2谓词4+实际本机WS6）。真实QQ握手及Q01单条调用/答复已补验；Q13应用队列离线验证通过，真实压力未测。

## 文件与安全检查点

自有实现：src/qqbot_gateway/{config.py,onebot_gate.py}；scripts/g0_probe.py、g0_protocol.py、manage.py及Start/Stop/Test/Show-BotStatus.ps1；tests/test_g0_protocol.py、test_onebot_gate.py；pyproject.toml；config/settings.example.yaml、mcp-empty.json、versions.lock.json。运行状态/config本机副本/凭据/缓存/logs在忽略路径，不导出。

旧规划8个Markdown文件保留，PROGRESS是唯一全局入口。仓库已存在；info.txt为用户本机文件，之前已进入Git历史。用户本轮授权commit/push，现保留本机文件并停止跟踪；不改写历史，既有历史密码仍需用户更换。用户本轮提供的独立CLI是外部安装，不由代理安装/修改。其余可见代码/报告/文档变更均为本轮代理工作；用户已授权以中文提交说明提交并推送至origin/main。

验证限制：精确额度扣减、真实认证失效/配额耗尽未制造；G3已本机实测、G4单条和多轮真实通过、隔离离线通过但真人交错待验，不能声称完整验收通过；视频/ASR/PC未部署；锁屏、睡眠和长稳未测。不靠反复模型请求代替定位错误。
