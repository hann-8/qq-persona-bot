# LAP-19 双后端、联网、自由群聊与表情包总体规划

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承[AGENTS](../../../../AGENTS.md)。

## 当前检查点

2026-10-17 14:49（Asia/Shanghai），session `LAP-19-dual-backend-web-plan` / “双后端切换与联网详细规划”领取本任务；开始分支main，HEAD `391be0f`，工作区已跟踪/未跟踪差异为空。

范围：原LAP-17本地接入/配置切换、LAP-18共用按需联网，以及用户15点后追加的自由参与授权群聊天、真实@必须响应、直接群发不引用原消息、QQ收藏/本地表情包。仍是同一LAP-19规划任务；实施拆为LAP-17→18→20自由群聊→21表情包。用户明确仅详细规划，后续自己用gpt-6.1-sol/medium执行；本轮不修改代码/运行配置/人设、不启停服务、不调用真实模型或发群消息。原“未@参与另规划”状态已由本次追加需求更新为本轮明确规划范围，尚未实际启用。

任务归属文件：本目录HANDOFF.md、PLAN.md、GROUP_CHAT_PLAN.md、IMPLEMENTATION_GUIDE.md，../../TASKS.md、../../HANDOFF.md、../../../../PROGRESS.md、../../../local-5070/HANDOFF.md、../../../local-5070/MODEL_SELECTION.md的最新快照说明，以及../../../../AGENTS.md中与用户最新自由群聊/表情包规划一致的范围说明（不改模型档位/只规划/Git规则）。家庭资料和原始只读证据仅在已忽略目录，不提交。

用户已选择联网触发：“按需自动：明确搜索请求、时效问题，或要求读取网页时联网”；普通闲聊不联网。具体触发合同和能力缺口已写入PLAN。AGENTS要求的规划/实施模型与档位由用户会话设置选择，本任务不声称检测或切换。

## 已完成与验证

- 已读AGENTS、PROGRESS、两条工作线HANDOFF、TASKS和PC模型初选记录；已核对git status干净。
- 当前config.py/model_gateway.py只接codebuddy_cli；CLI的WebSearch/WebFetch仍禁用，AstrBot内建联网关闭。相关实现上下文已读；结论仍仅静态证据。
- 14:53:59 SSH固定既有指纹核对成功：Ollama0.40.5、9B Q4_K_M已安装/16K加载、回环监听及direct-tcpip GET通过，0生成/远程修改，证据state/lap19-pc-metadata.local.json忽略保留。
- 当前gate的blocked_users判断位于转发/去重落库前；被屏蔽者直接消息不进AstrBot/模型/历史，其他人转述不在其保证内。自由群聊须保持此顺序并清理引用嵌入。
- 本机NapCat静态包有fetch_custom_face/详细接口，当前gate不放行；官方文档也列出收藏表情读取。未调用真实QQ接口，用户“已收藏2个”仅记用户说明。
- 已查框架request_llm显式contexts/无conversation与_save_to_history跳过条件，free模式可采用RAM群窗口而不复用个人持久历史；仍需实际框架离线验证，不能把源码推断当运行通过。

## 规划交付检查点

2026-10-17 15:23（Asia/Shanghai），四项详细规划完成；内容提交`91b96d592e5bb5be67950909c5ae8df54c3e161a`已推送origin/main，git ls-remote核对完整SHA一致，内容交付检查点工作区干净。随后仅同步本交付记录。交付物：[PLAN](PLAN.md)、[GROUP_CHAT_PLAN](GROUP_CHAT_PLAN.md)、[IMPLEMENTATION_GUIDE](IMPLEMENTATION_GUIDE.md)。已同步AGENTS范围、PROGRESS、TASKS、两线HANDOFF和PC选型最新快照；仅上述10份Markdown纳入提交。

验证：`.venv/Scripts/python.exe state/verify_lap19_docs.py`通过10份Markdown、143个本地链接、代码围栏/1个JSON样例、21个唯一任务ID和文档文件范围检查；`git diff --check`无错误。另在进程内对照家庭访问资料扫描本轮10份文档，主机/用户名/密码原值匹配均false，未打印值；长凭据块检查无匹配。扫描脚本/报告仅忽略state，本轮没有新增实现测试或重跑旧124项。

只读能力：PC实际元数据/通道通过；搜索适配器只做公共探测、质量未验；黑名单/NapCat收藏/框架无conversation为源码证据，不冒充运行通过。未改任何运行源代码/settings/persona/PC配置，未启停/探活真实bot、登录QQ/CodeBuddy、生成或群发，未读取真实收藏。

## 剩余与下一步

本轮规划与内容Git交付已完成，无实施任务在本session领取；本交付记录也按相同授权提交/推送并再次核对。后续用户在会话设置选择gpt-6.1-sol/medium，按执行指引分别开会话实施17→18→20→21；真实推理/观察群/收藏导入/发图和最终启停范围另由用户指定。PC目前只需保持Ollama后台/SSH可达作为接入前提，无需常开聊天窗口，但项目本地runner仍未实现。

旧LAP-10/13/15/16及真人差额继续保留；新功能仅已规划，无实现/离线运行/真实生成/完整群验收结论。内容交付检查点工作区干净，本次仅有交付记录同步；家庭凭据、本机settings、原始证据和临时脚本均继续忽略，不纳入Git。
