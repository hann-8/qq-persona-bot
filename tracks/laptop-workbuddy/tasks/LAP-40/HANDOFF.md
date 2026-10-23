# LAP-40 SnowLuma替换试运行详细规划

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承AGENTS。

状态：详细[PLAN](PLAN.md)与[分阶段实施指引](IMPLEMENTATION_GUIDE.md)已完成；阶段1配置/provider/只读静态检查已实现、83项离线测试通过并经根agent复核；阶段2项目侧原创策略/独立健康与实际gate/router栅栏已实现、离线通过，待根agent复核。尚未部署或切换，真实/G0/G1/上游私有接线/长稳未验。详见[阶段1报告](../../../../reports/lap-40-stage1-2026-10-24.md) / [阶段2报告](../../../../reports/lap-40-stage2-2026-10-24.md)。用户要求SnowLuma替换试运行，长期运行优先，允许branch；随后授权根agent逐步调用`gpt-6.1-sol / medium`实施复核。规划阶段仅只读源码/元数据与6份文档，0代码/配置/安装/依赖/注入/启停/登录/模型/群/SSH操作。

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

阶段2登记`LAP-40-medium-stage2-policy-health`，02:15，仍由同一gpt-6.1-sol/medium子代理串行执行。归属原创adapters/snowluma策略、transport_health.py、onebot_gate.py与必要GateConfig/router接线、对应JS/单元/框架替身测试及40交接/报告；根agent独占3共享入口。额外审阅点：Snow router mirror须独立在health TTL内到期，不能沿用原45秒；健康/控制帧可继续观测以避免启动死锁，用户入站/上下文/输出才关闭；NapCat原路径兼容。

阶段1实际领取：2026-10-24 02:05（Asia/Shanghai），session `LAP-40-medium-stage1-config`；已读规定入口/计划与codex-handoff，隔离分支HEAD `6556b24c5102e3bac21b6197a39902ae0c4a7334`、工作区干净。300分钟used=8%，remaining=92%。本阶段独占`src/qqbot_gateway/qq_transport.py`、`config.py`、`config_files.py`、`config_comments.py`、`scripts/transport.py`、`config/settings.example.yaml`、`config/examples/runtime.yaml`、`config/README.md`、`tests/test_qq_transport.py`及本HANDOFF/`reports/lap-40-stage1-2026-10-24.md`。按既定计划完成配置/provider/只读静态证据，成功标准是精确旧摘要兼容与自造离线边界通过；不触运行checkout、local/secrets/persona、不实现阶段2健康或恢复。

阶段1交接（2026-10-24 02:12）：上述11归属文件完成；15新增/14配置/30分层/6注释/18菜单共83通过，0跳过，diff --check通过。缺节schema1/2/3精确语义摘要和旧snapshot raw摘要保持，经过实际load_consumer/迁移验证；NT junction、非法/碰撞/独立秘密引用、严格proof/摘要绑定/变动失效、inspect只读与--json均有自造证据。inspect永不放行实时ready/G0/G1；原包/干净QQ/原生数据/私有接线未验，原运行目录/配置/进程全未触及。提交前额度used20/remaining80%。根agent复核本阶段diff及报告，再按指引串行派阶段2；本session停在阶段1，不自行推进。Git提交/远端一致性待本阶段出口精确回报并由根agent同步共享入口。
