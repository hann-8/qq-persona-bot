# LAP-20 自由群聊与直接群发

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md) / [合同](../LAP-19/GROUP_CHAT_PLAN.md)。继承AGENTS与LAP-19共同边界。

2026-10-17 16:44（Asia/Shanghai）检查点：已实现、离线/实际框架合成通过；真实未验、未部署、未切free。session `LAP-20-group-participation` / “LAP-20自由群聊与直接群发实施”，16:19领取；main起点109f4ee，工作区干净。仅20，不开始21。

目标：先以实际AstrBot/SDK合成验证无conversation、silent/异常发送防护、ACK/停止/恢复门槛；再实现显式mentions/free、RAM窗口/合批、一次决策、真实@优先与全模式直接群发。验收区分实现、离线与真实；不关闭旧真人差额。

文件归属：src中的config/persona/contracts/model_gateway/onebot_gate/reply_delivery/task_store/web_retrieval及新增participation/group_protocol/event_guard；router main/新增provider；configure_bot/configure_astrbot、settings.example；新增test_participation与菜单测试；新增verify_lap20/verify_lap20_gate，旧verify_lap16仅改无Reply断言，verify_lap18增加独立报告前缀；README/AGENTS事实、报告及6份安全JSON、本交接/TASKS/PROGRESS/工作线交接。仅本session修改，没有夹带用户/其他任务内容。

禁止：启停/登录/探活真实bot、真实模型/群发、修改本机settings/persona、读取旧个人历史进free或拉QQ历史、开始21。LAP-18搜索缺口保留。

已完成：首先实际框架collect_initial_request无conversation/保存跳过/事件级silent与异常防护/授权ACK；最终完整build_main_agent与runner请求→项目provider→SDK→网关→两真实runner底层替身通过。群协议、配置默认mentions、free RAM窗口/合批/全局优先调度、真实@独立ticket、群账本与未知ACK隔离/人工解除、连接身份/失效、所有模式直接群发落地。详见[报告](../../../../reports/lap-20-2026-10-17.md)。

重要实施细节：框架默认日期提醒会污染snapshot摘要，配置脚本关闭identifier/group_name/datetime并固定原样prefix；框架会注入主动发消息工具，当前event复制平台元数据关闭proactive能力，不改共享适配器。新任务provider用ContextVar传递可信session_id元数据，不从正文识别触发字段。事件发送能力只在ReplyDelivery/受控本地状态的当前任务链授予，silent/异常/迟到发送不获授权。WebRunner只检索本批新消息anchor，不上传群快照或重搜旧问题；canonical正文只格式化一次。连接watcher仅失效RAM，没有推理/搜索/发言。

验证（全部合成/离线）：

1. `.venv/Scripts/python.exe -m unittest discover -s tests`：187项通过；`state/lap20-unit.log`。新增22项群协议/窗口/调度/入口/联网及1项配置菜单，原164项保留。
2. 框架Python运行`scripts/verify_lap20_gate.py`通过；`scripts/verify_lap20.py`四组合各27组，共108组，通过记录见[JSON](../../../../reports/lap-20-framework-offline.json)。包含完整建请求、SDK保留元数据、single/adaptive speak/silent/@错误、停止/断连/过期/未知ACK、多人快照/去重/抢占/两独立@与anchor、权限/纯媒体/内嵌引用及重启群未知隔离。没有访问个人conversation或发送旧话题。
3. 框架Python导入`verify_lap18.main(scratch,'lap-20-regression')`：26网页框架+两后端single各5/adaptive各40，共90原路径回归通过，含原SDK/gate5组ACK、并发发送与启动恢复。证据使用lap-20-regression-*，旧17/18报告未覆盖。
4. `verify_g4_routing.py` / `verify_g4_adapter.py`在state scratch CWD运行：严格准入/历史隔离/预算/停止和真实At转换器回归；compileall、uv lock --check（23包）与git diff检查通过。最终链接/差异及交付核对在下段记录。

运行边界：未修改本机settings/persona/家庭资料，没有探活/启停/登录bot、SSH/真实模型/群发；模型/后端及工具隔离不变。所有框架数据只在临时夹具或忽略state；测试中“CLI_START”是自造脚本，不调用真实CLI。默认mentions，web搜索门槛仍关闭。

剩余：自然参与/协议质量、两后端真实生成/额度、真实QQ/ACK/多人/恢复/停止/长稳与全部旧真人缺项继续未验。LAP-18搜索需回规划。下一步仅等待用户明确真实范围或后续任务，不自动启用free或开始21。

回滚：操作者协调停机保存mentions后重启，保留旧个人历史。回退旧代码先核对/隔离pending/unknown账本、备份数据库并恢复配对配置；RAM目标不进入旧个人修复器，未知输出不补发。群隔离解除只在停机本机核对后进行，保留unknown证据。

Git：完成差异/链接检查后按既有授权commit/push并核对本地/远端完整SHA；最终结果在交付记录同步，不自引用自身提交。保留差异：仅忽略的本机配置/secrets和state测试工件，任务外未提交修改为0。
