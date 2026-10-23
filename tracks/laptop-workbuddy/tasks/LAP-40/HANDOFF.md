# LAP-40 SnowLuma替换试运行详细规划

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承AGENTS。

**当前：quota_hold。2026-10-24 03:19实际300分钟剩余4%，按用户指令停止新工作，本线程07:10一次性恢复已安排（automation `lap-40-snowluma`）。先读[额度交接与下一步](QUOTA_WAIT.md)。** 阶段1/2已根审；3仅静态核对；4A部分实现/离线/根审检查点通过，未全部完成、未部署。真实Snow启用总拒绝；[4A报告](../../../../reports/lap-40-stage4A-2026-10-24.md)区分项目侧独立剩余与外部前置。以下登记均为历史，不能跳到4B或称真实接线通过。

4A部分检查点已获根审接受，代码提交`c549ce3703dcec6f0f7a6976caaa1bdb04f19dfe`已推送且远端一致、代码工作区干净。追加续作待办：`manage.show_status`末尾对Snow/unknown阻断不得提示NapCat6099，应输出封闭对应状态并测试。其余4A未写项目侧能力见报告，未升级为完整完成。当前额度used94/remaining6%，不开始新实现，等待根agent续作安排。

状态：详细[PLAN](PLAN.md)与[分阶段实施指引](IMPLEMENTATION_GUIDE.md)已完成；阶段1/2项目侧实现与离线验证均经根agent复核。阶段3固定源码/指定材料只读核对与[私有接线清单](PRIVATE_WIRING_CHECKLIST.md)完成，原包/干净QQ/proof缺失且标准core构建复制native，未准备私有改版/构建/上游合成验证；待根agent复核后独立4A/4B。尚未部署或切换，真实/G0/G1/上游私有接线/长稳未验。详见[阶段1报告](../../../../reports/lap-40-stage1-2026-10-24.md) / [阶段2报告](../../../../reports/lap-40-stage2-2026-10-24.md) / [阶段3报告](../../../../reports/lap-40-stage3-2026-10-24.md)。用户要求SnowLuma替换试运行，长期运行优先，允许branch；随后授权根agent逐步调用`gpt-6.1-sol / medium`实施复核。规划阶段仅只读源码/元数据与6份文档，0代码/配置/安装/依赖/注入/启停/登录/模型/群/SSH操作。

session `LAP-40-SnowLuma-trial-plan`，2026-10-24 01:19（Asia/Shanghai）开始；基线main/66eea49623b76766e0569614207c80c78e57115f，工作区干净。已按用户授权新建`codex/lap-40-snowluma-trial`；本轮仅该分支规划，保留main和原运行状态，不声称自动检测或切换会话模型/档位。

规划归属：本HANDOFF、PLAN.md/IMPLEMENTATION_GUIDE.md，PROGRESS、工作线HANDOFF/TASKS，共6份Markdown。一个session仅推进LAP-40，LAP-39已完成调研作为证据来源，不抹掉其故障、o3候选及旧验收差额。实施时根agent独占3个共享入口，medium在隔离worktree按阶段领取代码/测试/40交接和报告，不并行覆写。

当前依据：[LAP-39长期运行评估](../LAP-39/SNOWLUMA_ASSESSMENT.md)；固定SnowLuma v2.1.1/f8cb15c，已有good/接收停滞及Windows管道重接，但原版在gate前答复/补历史/存储，当前项目硬编码NapCat且忽略good。干净QQ/原生数据归属和发行协议的原生组件部署限制是前置门槛，不能用安装成功或静态源码代替证明。

计划包括：可选provider及旧快照兼容；原创策略/私有早期过滤、禁#sl/补史/原始日志/磁盘消息store；固定版本/原生部署许可/干净QQ数据证明；独立armed健康与gate统一栅栏；有界身份恢复、CLI/有限字段回滚与72h/7天分级。public只交付原创代码，私有上游修改/native不入Git。无真实前置时完成独立实现离线验证，不动原bot。

2026-10-24 01:58（Asia/Shanghai）规划完成；下一步文档校验→commit/push核对远端→调用medium阶段1，串行复核再推进2—5，只有真实前置齐全才6。不得把用户睡觉当成放宽登录/数据/许可条件的授权。阶段6需人工扫码则waiting_operator，不循环登录。

额度约束：用户明确5小时剩余<=5%时，无论规划或medium执行都交接并等待北京时间2026-10-24 07:10恢复；根agent负责heartbeat。01:50实际300分钟used=2%，remaining=98%，未触发等待；不得使用reset credit/购买额度。每阶段及长步骤之间检查，medium约15分钟核对。

规划验证：6份Markdown本地链接/代码围栏检查通过；git diff --check通过。差异仅上述6文档，未运行代码测试或上游测试，没有把静态阅读当本机通过。规划Git交付后由根agent记录精确提交/远端SHA并开始阶段1。

## 2026-10-24 02:03 实施准备

规划内容提交`09ad5a43c3be57d8cc736029357dcc710d7a4368`已推送origin/codex/lap-40-snowluma-trial，git ls-remote核对完整SHA一致，规划checkout干净。

受管worktree `C:\Users\yutha\.codex\worktrees\lap-40-snowluma-impl\QQbot`，分支`codex/lap-40-snowluma-impl`从精确规划提交创建；不含原runtime/state/secrets/local，不复制认证/私改。原`E:\CodexWS\QQbot`仍为规划分支，运行代码/状态未动。可借原`.venv/Scripts/python.exe`作为只读解释器，测试工作目录/PYTHONPATH必须指向隔离worktree，禁止写原运行目录。

阶段1登记：`LAP-40-medium-stage1-config`，开始02:03，待根agent调用gpt-6.1-sol/medium。归属qq_transport/provider、config.py/config_files.py/config_comments.py/必要布局操作、scripts/transport.py只读inspect、模板/配置说明、对应测试及本任务交接/报告。共享3入口只由根agent写。完成后交根agent审阅，不自行越级启动真实阶段。

## 2026-10-24 02:15 根agent阶段1复核/阶段2登记

阶段2实际领取：2026-10-24 02:16（Asia/Shanghai），session `LAP-40-medium-stage2-policy-health`；已重读更新交接、PLAN第4/6节及实施指引阶段2，基线`0d2f8a71b5b04d3b4e6a6322668fd809bfbb8a87`、worktree干净。300分钟used22/remaining78%。独占`adapters/snowluma/project_policy.mjs`及README/JS测试、`src/qqbot_gateway/transport_health.py`、`config.py`、`onebot_gate.py`、`plugins/qq_router/main.py`、对应新增离线测试/框架替身脚本、40 HANDOFF及阶段2报告；共享3入口不写。目标是原创早期策略/有界RAM、独立健康合同和实际gate/router全路径时效栅栏；上游私有接线/监听/生命周期留后续阶段，默认缺证明closed，NapCat行为保持。

阶段2交接（2026-10-24 02:40）：[报告](../../../../reports/lap-40-stage2-2026-10-24.md)列12归属文件，含经根agent确认归属的config/README和新增两份实际测试。20健康/gate、17实际框架（含13gate复跑）、6JS及161既有回归通过，0skip，diff --check通过。早期纯信封先拒绝后convert；实际有界RAM；JS/Python HMAC互通；TTL尊重15..30配置；deadline定时无新WS撤销，不做10Hz扫描；实际gate入站/全输出/context/RPC及router镜像/最终栅栏接线。实际AstrBot解析确认最小sender/time/image兼容；旧事件与迟到结果不复活，NapCat缺省与旧快照保留。无真实服务/端口/模型/群/QQ/SSH/原生部署或本机配置操作。上游私有接线与运行owner/listener核验仍未验，阶段4接口尚待接入；不能称Snow适配完成。本session停在阶段2，待根agent复核再领取3；Git精确SHA由出口回报同步。

阶段2提交前额度used54/remaining46%，未触发等待；最终新增用例还证明socket任务内时效检查与传输异常保留unknown，未清空或重试旧账本。

阶段1内容提交`cec6c2a`及测试LF修正`6ee3d0c72c4bd8d504734fd28dfb7f2e3b71c0eb`已推送origin/codex/lap-40-snowluma-impl，根agent再次ls-remote核对完整SHA一致；11文件，worktree干净。审阅实际配置/loader/注释/inspect/proof/测试差异及[报告](../../../../reports/lap-40-stage1-2026-10-24.md)，旧对象/语义/快照字节摘要对照、83离线通过、0skip、真实junction拒绝与只读/脱敏覆盖；控制端口6185和CLI --json两项预审问题已修复。git diff 6556b24..HEAD --check通过。没有真实部署/服务/模型/群，未清除旧差额。

阶段2登记`LAP-40-medium-stage2-policy-health`，02:15，仍由同一gpt-6.1-sol/medium子代理串行执行。归属原创adapters/snowluma策略、transport_health.py、onebot_gate.py与必要GateConfig/router接线、对应JS/单元/框架替身测试及40交接/报告；根agent独占3共享入口。额外审阅点：Snow router mirror须独立在配置health TTL内到期（默认15秒，支持15..30），不能沿用原45秒；健康/控制帧可继续观测以避免启动死锁，用户入站/上下文/输出才关闭；NapCat原路径兼容。

## 2026-10-24 02:45 根agent阶段2复核/阶段3登记

阶段3实际领取：2026-10-24 02:46（Asia/Shanghai），session `LAP-40-medium-stage3-private-preflight`；基线`6c71bf72064b457ef409ec48058e7de5ed63c4ea`、worktree干净，已重读本交接/PLAN3、4、9与GUIDE阶段3。额度used57/remaining43%。本阶段归属`PRIVATE_WIRING_CHECKLIST.md`、`reports/lap-40-stage3-2026-10-24.md`、`adapters/snowluma/README.md`的接线清单链接及本HANDOFF；无代码改动预定，如需小修先另登记。指定两checkout的官方包根/QQ入口/proof/private根只读exists均false，未扫描其他位置。仅固定提交官方源码定点核对；不准备无原包/合格环境可验证的上游改版，不建伪manifest，不绕保护、不部署原生、不启停/登录/模型/群/SSH。根3入口不写。

阶段3交接（2026-10-24 02:54）：四份归属Markdown完成；固定提交30份源码资源定点只读，八项指定路径exists=false、Node24.22.0、忽略规则与实际自造配置inspect保持channel_ready=false。清单15项列最早protocol副作用/日志、原生信封字段、#sl/补史/所有store/RAM/RKey fallback、扫描/额外网络、armed/outbound/控制面、native构建与保护/数据范围的固定源码位置、现有接口、未完成及具体待验。标准core build也复制native，未运行；本轮0私有改版/构建/上游测试/部署，不把清单称接线通过。缺口保留但不阻塞下一阶段4A/4B独立原创离线部分。未动原bot/配置/数据/凭据；本session只收尾3，待根agent复核再派4。

阶段3提交前used69/remaining31%；4文档23相对链接/围栏及diff --check通过。Git仅四份原创Markdown，精确SHA及远端一致由本阶段出口回报根agent同步共享台账。

阶段2提交`8f58b2e353cf64886262faf661231bbb039f5626`已推送origin/codex/lap-40-snowluma-impl，根agent再核对远端完整SHA一致，worktree干净；12文件，整阶段diff --check通过。审阅最终策略/健康、gate所有准入和上下文异步结果/代际检查、router mirror/原event、实际框架与跨语言测试和[阶段报告](../../../../reports/lap-40-stage2-2026-10-24.md)。20健康/gate、17实际框架（13是gate复跑）、6JS及161旧回归均通过，未将复跑算不同场景。已处理时间/sender/image兼容、非法at、envelope转换前拒绝、可配TTL15..30、deadline取代10Hz轮询、迟到proof不掩盖旧代际、socket调度后复查/unknown。项目侧阶段2通过；没有上游私有适配/实际监听/真实QQ证明。提交前额度remaining46%。

阶段3登记`LAP-40-medium-stage3-private-preflight`，02:45，仍由sol medium执行。范围只读指定项目材料/固定上游接线与私有构建前置，允许的私有源码/JS仅在忽略区、原创核对说明和40报告/交接；禁止公开上游修改源/patch/bundle/native和自动原生部署。已有39/40证据复用，不重跑泛化版本调查。缺原包/合格运行时/数据范围或保护证明时明确未通过，继续独立阶段4，不空等操作者、不动原bot。

## 2026-10-24 02:58 根agent阶段3复核/4A登记

4A实际领取：2026-10-24 03:00（Asia/Shanghai），session `LAP-40-medium-stage4A-runtime-owner`；基线`6e0639ba656b430d33c1689b9e9a1ed101bd9682`、worktree干净，重读更新HANDOFF/PLAN/GUIDE，额度used73/remaining27%。本阶段独占`scripts/manage.py`、`process_host.py`、`src/qqbot_gateway/transport_owner.py`、必要`qq_transport.py/transport_health.py/onebot_gate.py`、`adapters/snowluma/control_plane.mjs`及JS测试/README、`tests/test_transport_owner.py`、必要config/README、40交接和4A报告。先完成默认写状态前硬拒启、加载provider状态/停止、独立秘密/受管身份与固定listener/nonce poll闭环和供未来私有入口的固定控制handler；完整Snow原生启动因3缺口不实现、不称通过。真实管理路径用假组件/传输验证，0真实端口/QQ/Snow/AstrBot/模型/群/SSH。4B预算/恢复/CLI/采样不做；根3入口不写。

阶段3提交`c495e20a3ac0f4ca5e8f7c1feeb03e64e3e16686`已推送，medium核对完整远端SHA一致/干净；根agent审阅4文档差异、15项固定SHA接点清单与报告，diff --check通过。仅完成静态核对，**上游私有源改动/构建/执行级合成接线全部未做**。普通core构建也复制native；protocol副作用/enrichment/printEvent及raw trace早于OneBot；RKey/OIDB/server fallback和缓存上界需单独处理。原包/QQ/proof/private根八项不存在、Node24.22.0、实际inspect=false及文档检查为本阶段执行证据，没有拿旧测试冒充上游通过。提交前剩余31%。

根agent据此定向更新PLAN/GUIDE：禁普通core build，明确最小原生信封须早于协议副作用，阶段4拆4A/4B；没有扩大账号/模型/真实触发范围。4A登记`LAP-40-medium-stage4A-runtime-owner`，02:58；归属manage/process_host、qq_transport/transport_health/必要健康owner模块、gate启动绑定/轮询、原创固定控制面JS、必要README及自造测试/40交接报告。共享3入口由根agent写，私有上游保持未完成，真实资格缺失硬拒启；4A结束先复核再派4B。新控制面不得变任意命令/路径/PID/API代理。

## 2026-10-24 03:18 根agent复核4A部分检查点

4A代码`c549ce3703dcec6f0f7a6976caaa1bdb04f19dfe`已核对远端一致；medium另推交接`802fac13c8262bb3ca7f489675383abb5192c2d5`，干净。根agent审阅管理/owner/poll/控制面/停止差异与报告，整阶段diff --check通过。最终41项Python、9项JS通过；更广104项在最后少量新增用例前通过，未重复合算独立数量。接受为**部分交付检查点，4A尚未全部实现**。已修损坏快照不阻止已核验owned停止、bind并发/超时重入至多一次、stop先撤销等预审项；未进行任何真实组件/端口/QQ/模型/群/SSH操作。

下一步仍先sol medium完成4A独立剩余：原锁内唯一writer生成/验证owner登记API与fake创建路径、固定Snow启动spec构造/合成验证（生产仍硬拒）、manage实际消费drain/stop ACK及失败分支、show_status不再对Snow提示6099。再根审→4B恢复预算/CLI/采样→5集成。私有入口资格/真实listener/armed/outbound/QQ部署另受阶段3阻断，不能把项目侧未写部分笼统归为外部条件。03:17实际300分钟used94/remaining6%，未使用reset credit；达到<=5%保存交接并安排北京时间07:10续作。

原运行checkout规划分支新文档指针`a798e62498a60b8d061e917d1d8242f42d564ef0`已推送核对，仅改PROGRESS引导来此活动worktree，原代码/配置/进程未改。与实施分支仅本任务文档分叉；未来部署前由根agent协调归属文档合并，保留可审历史/停机快进条件，勿强推或在原运行中切代码。

阶段1实际领取：2026-10-24 02:05（Asia/Shanghai），session `LAP-40-medium-stage1-config`；已读规定入口/计划与codex-handoff，隔离分支HEAD `6556b24c5102e3bac21b6197a39902ae0c4a7334`、工作区干净。300分钟used=8%，remaining=92%。本阶段独占`src/qqbot_gateway/qq_transport.py`、`config.py`、`config_files.py`、`config_comments.py`、`scripts/transport.py`、`config/settings.example.yaml`、`config/examples/runtime.yaml`、`config/README.md`、`tests/test_qq_transport.py`及本HANDOFF/`reports/lap-40-stage1-2026-10-24.md`。按既定计划完成配置/provider/只读静态证据，成功标准是精确旧摘要兼容与自造离线边界通过；不触运行checkout、local/secrets/persona、不实现阶段2健康或恢复。

阶段1交接（2026-10-24 02:12）：上述11归属文件完成；15新增/14配置/30分层/6注释/18菜单共83通过，0跳过，diff --check通过。缺节schema1/2/3精确语义摘要和旧snapshot raw摘要保持，经过实际load_consumer/迁移验证；NT junction、非法/碰撞/独立秘密引用、严格proof/摘要绑定/变动失效、inspect只读与--json均有自造证据。inspect永不放行实时ready/G0/G1；原包/干净QQ/原生数据/私有接线未验，原运行目录/配置/进程全未触及。提交前额度used20/remaining80%。根agent复核本阶段diff及报告，再按指引串行派阶段2；本session停在阶段1，不自行推进。Git提交/远端一致性待本阶段出口精确回报并由根agent同步共享入口。

## 2026-10-24 阶段4A可审检查点

session `LAP-40-medium-stage4A-runtime-owner`；基线6e0639b。实际归属除领取段所列外，定向同步adapters/snowluma/README.md、config/README.md及本任务HANDOFF/report；未修改根agent的3共享入口。

已实现manage provider加载/启动前硬拒/状态closed/损坏快照仍可stop、Snow精确毫秒创建身份、process_host封闭码；原创RuntimeOwner/独立key/固定回环HealthMonitor与gate startup/cleanup连接、纯JS health/bind/drain/stop handler。最终38项Python加3项受影响lifecycle共41项及9项JS通过，更广104项回归通过（最终新增3项后41项重跑）；详见阶段4A报告的实际命令/限制。无真实端口/QQ/Snow/模型/群/本机配置操作。

未完成分层：项目侧owner记录唯一writer生成API、Snow启动spec合成路径、管理stop的drain/stop ACK实际消费仍需继续写，不能记成外部阻断；私有入口资格证据、真实listener/armed/outbound接线和真实启动验证另被阶段3/材料缺口阻断。require_runtime现在总拒绝，完整Snow生命周期未交付。根agent复核当前检查点后继续4A缺项或额度续作，不自动4B。额度本检查点used92/remaining8%，每块继续核对，<=5%最小交接即停。
