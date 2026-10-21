# LAP-18 两后端共用联网

2026-10-21续作仅规划：[LAP-36总计划](../LAP-36/PLAN.md)、[网页/网络合同](../LAP-36/WEB_VIDEO_PLAN.md)、[medium指引B](../LAP-36/IMPLEMENTATION_GUIDE.md)已完成；显式安全解析/TLS、readability正文/统一材料预算与来源，B站另由06D实施。当前本机五域DNS仍非公网、DoH TLS未过；本轮没有改18代码/运行配置/搜索门槛或做真实模型/群操作。下方历史离线/搜索差额保留，续作待新指令领取。

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md) / [合同](../LAP-19/PLAN.md)。继承AGENTS和实施指引。

2026-10-17 16:16（Asia/Shanghai）。独立部分已实现/离线通过；搜索未完成，质量门槛未通过、回规划。session `LAP-18-shared-web-implementation` / “LAP-18共用按需联网实施”，16:05领取；main起点`a0718087c73cdcebc1dd8e41d497a3a3b5ea3df3`工作区干净，仅18，无其他session变更。

目标：先探测3类公共搜索质量，再完成配置、安全读取、共用包装、预算/来源/失败取消、一次生成和原问题历史ACK；候选不足则明确搜索未完成并回规划。

文件归属：新增`src/qqbot_gateway/web_policy.py`、`web_retrieval.py`、`tests/test_web.py`、`scripts/verify_lap18.py`、`probe_lap18.py`；修改config/backends/model_gateway/persona、router、configure_astrbot/configure_bot、settings.example、test_configure_menu、README；本交接、[报告](../../../../reports/lap-18-2026-10-17.md)与6份安全JSON、TASKS/PROGRESS/工作线交接。独占这些任务修改，未操作任何bot。

验证计划：公共无隐私查询；离线SSRF/预算/触发/取消/次数测试；两真实runner底层合成替身+实际AstrBot保存发送/ACK/恢复。0真实模型、QQ/登录/群发、本机settings修改；不启用CLI工具/MCP，不新增账号/付费API/部署。不自动领取20/21。

## 最后检查点与验证

已完成：配置默认关闭/菜单/范围校验、确定性触发/隐私筛查、每跳解析绑定全局IP/peer/TLS/无Cookie代理、正文提取与日期状态、压缩前后/页数/时间/材料预算、两后端共用队列包装、来源单条与原问题历史、失败/硬期限不发送/取消/stop/远端未知结果传播。候选解析保留site过滤/去重，搜索门槛由代码关闭，配置不能覆盖；没有额外模型分类/重试或CLI工具。

- `.venv/Scripts/python.exe -m unittest discover -s tests`：164项通过，最终日志`state/lap18-unit.log`。
- 框架Python运行`scripts/verify_lap18.py`：26组网页实际框架+两真实runner底层替身合成通过；同脚本复跑原single各5/adaptive各40共90组通过，含SDK/gate/ACK/并发/启动恢复。证据链接见报告；0真实CLI/Ollama/QQ。
- `verify_g4_routing.py` / `verify_g4_adapter.py`在`state/lap18-entry-scratch`临时CWD运行：入口/隔离/历史/预算/停止及真实At转换器回归通过（adapter预期旧反例日志不算现实现失败）。日志`state/lap18-routing.log` / `lap18-adapter.log`。
- compileall、`runtime/tools/uv.exe lock --check`（23包，无新依赖）、diff检查通过；146个本地Markdown链接核对通过、最终差异已审阅，按长期授权交付。网页/查询/日期不进入会话版本，web设置进入版本。
- 最终公共探测`scripts/probe_lap18.py`：三类公共查询均blocked_ip，0返回字节/正文；[安全证据](../../../../reports/lap-18-public-probe.json)。当前DNS条件导致受控客户端无法取得公共页面，未满足2/3相关可读与时效日期门槛；不据此断言引擎本身质量坏，也不能标搜索可用。

## 剩余与下一步

搜索未完成，须回规划确定符合安全边界的网络条件/候选路线，并重新按原质量门槛验证；不自行改DNS/代理、接新账号/提供方/付费API、部署服务或放开CLI WebSearch/MCP。安全读取/稳定接口独立交付，实际公共正文成功读取未通过；两后端真实联网生成、模型来源/抗注入质量、群来源/ACK与旧LAP-10/09/13/15/16/原真人差额保留。无需继续重复无效候选探测；等待用户指定规划或后续任务，不自动领取20/21。

本机settings/persona/家庭连接资料未修改，没有SSH/启停/登录/探活bot、模型/群发/部署。默认web关闭。所有框架使用合成事件和临时CWD；一次源码inspect导入新建的空框架data已移至忽略`state/lap18-inspection-data`，没有覆盖用户资料。本机配置、secrets、测试日志继续忽略，不纳入提交。

回滚：操作者停机保存web.enabled=false再重启；保留旧历史/配置备份/两profile。回退旧代码先处理pending发送账本并恢复配对配置备份；不在本轮实际启用或回滚。只有独立代码/离线交付，不能标LAP-18完整完成。

Git交付：2026-10-17 16:18，内容提交`ebbe5d5d930dde2dce33e1c30a1b685a5ce35ee5`已推送origin/main，git rev-parse HEAD与git ls-remote的完整SHA一致，检查点工作区干净；随后仅同步本交付记录并按长期授权提交/推送。最终交付记录的SHA由main/HEAD恢复，不自引用自身SHA。不提交本机settings、凭据、测试data或原始网页/群消息。保留本机差异：无已跟踪或未跟踪任务文件差异，既有配置/secrets及新增state测试工件继续忽略；没有夹带或丢弃用户修改。Git交付不等于搜索完成、部署或真实验收。
