# LAP-18 当前交接：阶段B离线交付、网络真实缺口保留

2026-10-22最新规划：[LAP-38](../LAP-38/PLAN.md)本轮现有安全PublicHTTP取得公开HTML，旧DNS全非公网是历史；另一次连接仍超时。JSON文档正文提取缺关键标识，新增[18续作C合同](../LAP-38/QQ_VISION_WEB_PLAN.md)/[medium指令](../LAP-38/IMPLEMENTATION_GUIDE.md)补结构主体/相关选材与封闭诊断。仅规划，SEARCH_QUALITY仍false，本机配置/运行实例不改；旧B报告与真实/完整差额保留。[38证据](../LAP-38/EVIDENCE.md)。

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md) / [36合同](../LAP-36/WEB_VIDEO_PLAN.md)。继承AGENTS；本轮仅18，不领取28C/06。

2026-10-21（Asia/Shanghai），session `LAP-18-B-public-body`，20:38登记/重读。本session独占本轮归属；起点main/b02d6b92f6fe2b7bbda47733ccc2ec0c7bf89e2f，git status干净。24/28已交付及用户persona（sha256 ff6f629d92afab7ea1c47830bd4a7e8735e944862573a90764645604e96f2804）原样保留。

## 已完成与证据

安全公共HTTP兼容抽出；显式system/固定Cloudflare DoH、默认无项目CA/固定CA严格扩充、无环境代理/信任旁路/重试/提供方切换；图片复用共用安全网络而不放宽其域/MIME/生产能力门槛。readability-lxml==0.9与4依赖锁定；默认及legacy HTML均按需受管worker，字节/2秒/256MiB/叶进程Job、创建身份/清理台账/取消回收。统一6000字节元数据预算、六区完整段落/真实范围、完整要求拒超限、最终预算重算、来源/封闭manifest、真实@本地失败ReplyPlan/普通候选沉默、网页材料不晋升成员事实；触发/队列/工具/最终哑巴栅栏/ACK保持。

- [报告](../../../../reports/lap-18-B-2026-10-21.md)，[单元](../../../../reports/lap-18-B-unit.json)：232受影响单元通过/32.609秒；新增23专项，末次107/62/40等定向回归独立记录，不累加宣称。最终worker兼容复验命令与结果见JSON。
- [实际框架](../../../../reports/lap-18-B-framework-offline.json)：16组164例，末次39.922秒；两实际runner底层替身、实际AstrBot/provider/run_agent/原event ACK，覆盖mentions/free、正文worker+图片+记忆+表情与哑巴/成员组合。0真实模型/QQ。
- [依赖与资源](../../../../reports/lap-18-B-resources.json)：5包，约10.97MiB实装/4.07MiB Windows wheel；prepare4.21秒/install0.193秒。四类正文含11KiB长文，均3事实/去噪；逐页及816KiB压力页耗时/RSS以JSON实测为准，均<2秒/256MiB、exited/cleanup=true、空闲0。缓存/下载纯流量未分离，不冒称测得。
- [本机公开探测](../../../../reports/lap-18-B-public-probe.json)：初批6正文+3原类查询，另2DoH原因诊断；合计11次HTTP入口/4次DoH TLS尝试、0可用正文。七域系统DNS全非公网；DoH异常链verify_code=20。TLS/公网/正文真实通过均没有；network_unverified、SEARCH_QUALITY_PASSED=false。未借浏览连接器冒充可用。

命令：`.venv/Scripts/python.exe -X utf8 -m unittest`（具体模块见unit.json/忽略state/lap18-B-*.log）；框架Python `scripts/verify_lap18_body.py`；项目Python `scripts/measure_lap18_body.py`、`scripts/probe_lap18_body.py`及`--diagnose-doh`；`runtime/tools/uv.exe lock --check`、compileall与diff/链接/归属核对。原报告不覆盖。公开探测不应为刷新报告重复调用，后续须重新登记限额。

## 文件归属与生效

新增public_http/public_network/evidence_selection/web_extractor/html_worker/extractor_limits、test_lap18_body、probe/verify/measure_lap18_body、本轮报告与4JSON；修改web_retrieval/web_policy/config/config_files/config_comments/persona.py/backends/model_gateway/onebot_gate/vision/turn_v2必要接点、pyproject/uv.lock、两个示例模板/README与config索引、test_web、verify_lap28_framework仅body_reader参数/断言、18交接/PROGRESS/工作线HANDOFF/TASKS。完整归属以本轮Git差异为准；没有修改24进程/登录或28生产能力表。

新增public_network.system/null、web.extractor=readability、long_text_policy=excerpt默认随代码/正常启动生效。现有web.enabled保存值true未写改；本轮未修改真实local/CA/代理/DNS/凭据，不SSH/启停/登录真实bot、不调用模型或QQ，不声称已部署。真实工件/凭据/HTML/群消息均不提交。用户人设旧23393字节预算测试差额保留，没有替换人设来通过测试。

## 剩余、解除条件与回滚

本轮仅代码/离线与合成提取质量合格，LAP-18未完整验收。先由操作者处理本机合法公网解析/严格TLS信任或回规划，再验证中文2/技术1真实静态正文质量、实际peer及图片/字幕域解析。搜索仍须按原至少2/3相关可读/日期证据单独复核；页面成功不能打开门槛。所选后端真实生成、来源抗注入/真实群ACK另批授权。保留28C质量/可信容量/生产拒启、24登录、31B、07 ASR、V11与全部旧差额。

回滚按既有正常停机/配对备份流程，保留pending/unknown/清理台账，分别显式legacy/system或关闭web后正常启动；不动全局网络、真实群记忆/图库/历史。下一步等待用户针对真实网络条件或28C/06的后续指令，不自动续领。

Git交付（2026-10-22，Asia/Shanghai续作核对）：归属38文件内容提交`74eff6bb1a86a8ecb633f33ac303985f88d94de7`已推送origin/main；git rev-parse HEAD与git ls-remote origin refs/heads/main完整SHA一致。核对时git status --short为空，未夹带24/28/用户人设差异；本机local/secrets/state/runtime保持忽略。随后仅本交接与报告补交付记录，记录提交以main/HEAD为准，不自引用自身SHA。没有新增网络/模型/QQ调用或部署；保留全部真实差额。

---
以下为旧检查点与验收差额（历史当时的默认/启用状态不得覆盖上文当前保存值）：

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
