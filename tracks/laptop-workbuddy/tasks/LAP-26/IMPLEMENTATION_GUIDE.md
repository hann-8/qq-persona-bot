# LAP-26后续medium实施指引

返回[PROGRESS](../../../../PROGRESS.md) / [LAP-26交接](HANDOFF.md) / [总体合同](PLAN.md) / [精确实施合同及验收ID](IMPLEMENTATION_SPEC.md) / [TASKS](../../TASKS.md)。

本文件只是后续入口，不构成当前实施、启停、真实模型或群消息授权。用户说明规划会话为sol6.1 Ultra；实施按AGENTS由操作者选择gpt-6.1-sol/medium，agent不自动检测或切换。新能力默认关闭，不修改忽略的本机配置来自动启用。

## 执行顺序

用户追加反复清理失败后，建议**LAP-31清理可靠性→LAP-27关注/指代→LAP-28图片→LAP-29名册/@→LAP-30群记忆**。每次session只领用户指定的一项；本轮不预建空实施HANDOFF。登录留在LAP-24，联网搜索仍留LAP-18，不能趁新任务顺手改后端/QQ资料或掩盖旧验收差额。

1. 读AGENTS→PROGRESS→工作线HANDOFF/TASKS→LAP-26 PLAN/HANDOFF，再查所选任务当前归属和git status。不要把历史“未启用free”当成现状；用户已确认free可聊，当前加载版本仍未确认。
2. 领取该任务、记录session/Asia-Shanghai开始时间/涉及文件，创建本任务HANDOFF并登记返回链接，写后重读。共享文件有不明修改先协调；只读子任务不能代替主session拥有bot实例。
3. 在对应HANDOFF写目标/范围/合同/验收/能力缺口，先做独立可离线验证部分。关注/身份从可信事件和ACK来；模型不能指定真实QQ/RPC/路径。
4. 复用一次原生生成，不额外加关注classifier、图片caption、记忆summary或embedding模型。CLI工具/MCP隔离、固定SSH/tag/digest及项目级单次尝试不变，LAP-10内部上游次数差额继续保留。
5. 配置校验/示例/菜单同交付，保持schema3无损默认补齐，新增开关默认false、重启生效。后端与额度来源不变，保存不重启或自动启用。
6. 用新任务独立verify/report入口做有意义的单元与实际框架合成：真实run_agent/两实际runner底层替身/原event投递及ACK；不能只手动构造成功结果。合成图片、群和成员均用自造夹具，不读附件原始群聊来当测试素材。
7. 记清已规划/已实现/离线通过/真实通过/完整验收，独立交付文档与Git。真实调用/登录/群成员查询/启停另按用户后续明确范围与唯一执行归属；不能为“验收”自行发群消息或消耗模型额度。

## 各项最小完成出口

- LAP-31：当前每轮创建CLI且禁session持久化，附件不能证明session切换根因。分开原生成结果与observed_empty/owned_alive/identity_unknown、coverage；单独持有同一cleanup task、总deadline复用cleanup_seconds=5，不因重复cancel失管。按创建身份逐个处理、不因单个AccessDenied跳过其他已知对象；有界未决台账/脱敏阶段事件。已经阻断后只做零推理检查，有完整覆盖与退出证据才恢复；普通legacy成功与故障后恢复门槛分开。Windows请求容器先用自造进程核验，能力不足交付独立诊断并保留unknown，不全局kill/删flag/改后端；不改Ollama未知解除合同。

- LAP-27：真实@ > 叫名/Reply > 合格焦点 > focused_candidate > ambient，同级FIFO且direct各消息独立ticket，不打断已发请求；焦点60秒/无他人插话/仅文字ACK形成，保留真实@他人以消歧。没有“你”/名字的承接短句也作为候选同次判断，最多4次/分钟、跳过ambient冷却但允许silent，不把确认/感叹都设必答。测试“肥鱼”及同人“你”、省略续聊/结束确认、多人交错/忙时不吞target；新增随机trace，不保证固定时延。
- LAP-28：当前获准事件图片typed信息→安全blob→provider→CLI stream-json/Ollama images；原始附件剥离、不让框架自动下载，不开放Read工具。首版1张、规范化<=1024边长/1MP/512KiB、body<=2MiB/cache<=8MiB/TTL60秒；原图/规范化hash与target绑定。文本/图片预算分开、4096视觉余量仅待验证假设；生产关闭时可在用户另授权范围做独立验证，不自动启用；视频音频仍不接。
- LAP-29：1..49才可取名册，50/51/未知不取；gate防宽RPC旁路；承认缓存/非原子缺口。人数与名册双缓存必须同时有效，完整名单本机缓存、只给当轮少量候选；typed@最多1人同文字链，不猜QQ，不@all，仍逐条ACK。
- LAP-30：按bot/group/user稳定键与持久HMAC key，有限JSON主库+本机MD只读视图；每群全JSON<=64KiB、全模块16群/8MiB含所有副本。同轮memory proposals严格来源验证、去重/更新/TTL/评分淘汰；固定base_revision/phase幂等、来源actor依赖不可丢。silent自述与ACK承诺分开，清除后迟到ACK不得复活，删除副本失败禁读写；不加额外模型/向量库。

## 五项独立复制指令

先在会话设置选择gpt-6.1-sol/medium，再按31→27→28→29→30逐项发送下面的对应文本。每项使用独立实施session，上一项写好交接后再领取下一项；不用手工替换任务名。以下授权只在用户实际发送到对应实施会话时生效，本规划会话不实施。

### 第1项：LAP-31 清理可靠性

```text
项目 E:\CodexWS\QQbot。本会话使用由我在设置中选择的 gpt-6.1-sol/medium。
先读 AGENTS.md、PROGRESS.md、活动线HANDOFF/TASKS，再读 tracks/laptop-workbuddy/tasks/LAP-26/{HANDOFF.md,PLAN.md,IMPLEMENTATION_SPEC.md,IMPLEMENTATION_GUIDE.md}。
本次仅实施 LAP-31。按PLAN第13节、SPEC第8—10节与CLEAN-01—06，先登记session/文件归属并创建LAP-31 HANDOFF，写后重读。
完成原请求结果/清理状态分离、同一cleanup task的取消/关闭接管、总deadline、PID+创建身份逐项处理、有界未决台账、零推理检查和脱敏诊断。31A独立修复与31B容器/完整恢复分别报告；自造进程通过不等于真实CLI组合通过，历史job_complete不能在重启后直接解锁。能力不足先完成31A并保留31B差额，不删unknown、不扩大kill范围。
实现对应tests和独立scripts/verify_lap31.py，报告写reports/lap-31-*，只用替身及本任务自造受管进程；适用旧生命周期/ModelQueue回归必须通过。不运行会覆盖旧报告的verify主程序。
不修改忽略的本机配置/凭据，不启停/登录真实bot，不调用真实CLI/Ollama生成、真实QQ接口或群发，不按进程名批量结束。账号/后端/模型/额度及Ollama未知解除合同保持。
完成代码、必要验证、README及任务/进度交接，按长期授权仅commit/push本任务检查过的文件并核对远端SHA，报告保留差异。一般细节和已规划失败分支自行处理；会改变方案的缺口记录后回规划。不自动开始27—30。
```

### 第2项：LAP-27 关注、指代与自然续聊

```text
项目 E:\CodexWS\QQbot。本会话使用由我在设置中选择的 gpt-6.1-sol/medium。
先读AGENTS、PROGRESS、活动线HANDOFF/TASKS，再读LAP-26 PLAN/IMPLEMENTATION_SPEC/IMPLEMENTATION_GUIDE与LAP-31交接。确认31A已交付；31B未验证差额保留，不据此操作真实实例。
本次仅实施LAP-27，先登记归属并创建本任务HANDOFF。按PLAN3/4/8—11和SPEC2—4/9/10，完成可信identity、封闭v2协议/source与effective digest、router优先dispatcher/Q-R保留槽、冻结目标、真实@/叫名/引用/60秒焦点与无主语续聊候选、ACK对象归因和随机trace。
mentions仍仅真实@并保留原群+用户历史；所有新开关关闭完整保留v1。direct不同消息不合并；candidate每群滚动额度、结束确认可沉默；单活动turn且不抢断。预留v2未来材料空字段，不提前实现图片下载、名册RPC/@或持久记忆。同步配置/菜单/示例及旧配置兼容导出合同，不自动启用。
实现ATT-01—12与独立tests/verify_lap27，实际run_agent/两runner底层替身和原event ACK验证受影响路径；报告写reports/lap-27-*，不覆盖旧报告，不把离线当真实效果。
不修改忽略的本机配置/凭据，不启停/登录真实bot，不调用真实模型、QQ接口或群发，不读取/重放私密附件。模型/额度/工具隔离和单次尝试保持。
完成代码、适用验证、README/任务/进度交接后，仅commit/push本任务文件并核对远端。一般细节自行完成，方案级缺口保留证据回规划。不自动开始28/29/30。
```

### 第3项：LAP-28 图片理解

```text
项目 E:\CodexWS\QQbot。本会话使用由我在设置中选择的 gpt-6.1-sol/medium。
先读AGENTS、PROGRESS、活动线HANDOFF/TASKS、LAP-26 PLAN/SPEC/GUIDE和LAP-27交接，确认v2/可信身份基础已交付；仅领取LAP-28并创建HANDOFF。
按PLAN5及SPEC2/4/5/9/10，实现gate唯一图片材料服务/专用本机认证/一次cap、provider只转sideband、gateway一次兑换、RAM blob规范化与hash、CLI stream-json和现有SSH Ollama原生images同次输入、最终文本/视觉/wire预算及能力证明状态。
只处理当前获准消息第一张图片，不编辑/发回处理图，不接视频音频；图片中文字不能变工具指令。原始附件剥离，框架不自动下载，黑名单零下载，失败不换图/重试/换backend/开放Read工具。生产默认关闭。
区分unverified/offline_passed/native_observed/production_eligible；4096只是待验证reserve，一次样图成功不证明上界。交付独立受控验证命令，本次不执行任何真实识图；预算/容量无可靠证明则交付适配器、离线和明确不可启用状态，不能改门槛。
完成VIS-01—04和ATT适用回归、实际provider/runner/run_agent替身集成、独立verify_lap28及reports/lap-28-*，不覆盖旧报告。同步配置/菜单/README/交接。
不改忽略本机配置/凭据，不启停/登录真实bot，不真实下载群图、调用模型/QQ或群发；无额外caption模型/付费API。完成后仅commit/push本任务检查过的文件并核对远端，保留差异/能力缺口；不自动开始29/30。
```

### 第4项：LAP-29 小群名册与受控@

```text
项目 E:\CodexWS\QQbot。本会话使用由我在设置中选择的 gpt-6.1-sol/medium。
先读AGENTS、PROGRESS、活动线HANDOFF/TASKS、LAP-26 PLAN/SPEC/GUIDE及27/28交接。依赖共用v2/材料服务代码交付，不要求vision生产启用；仅领取LAP-29并创建HANDOFF。
按PLAN6及SPEC2/5/6/9/10，实现gate固定成员服务、人数/名册双TTL、1..49门槛、全量仅本机缓存/当轮最多8候选、RPC防旁路、v3 typed mention/一次mention.send许可与文字同链ACK、发送前失效同次剥@及可信回执。
50/51/未知/过期零list；不得member_info/stranger_info绕过。received_at不等于人数观测时间，现锁定NapCat缓存接口尚无新鲜度证明；严格门槛未通过则完成固定RPC/typed@独立离线交付并拒激活，不临时增加人数来源或默认接受陈旧值。不得@all/任意QQ/CQ码/猜重名，不额外通知或补发。
完成MEMB-01—04、候选/ref/ACK/错误与旧文字表情回归，独立verify_lap29及reports/lap-29-*；只用自造成员夹具/假OneBot，不调用真实群人数/名单/@。同步配置菜单/示例/README/任务交接。
不改忽略本机配置/凭据，不启停/登录真实bot，不真实模型/QQ/群发；访问控制/模型/额度保持。完成后仅commit/push本任务检查过的文件并核对远端，分别报告离线与真实可用门槛；不自动开始30。
```

### 第5项：LAP-30 群长期记忆

```text
项目 E:\CodexWS\QQbot。本会话使用由我在设置中选择的 gpt-6.1-sol/medium。
先读AGENTS、PROGRESS、活动线HANDOFF/TASKS、LAP-26 PLAN/SPEC/GUIDE及27/28/29交接。依赖共用身份/候选/v2代码，不要求members或vision生产启用；大群仍可从当前获准sender记忆。仅领取LAP-30并创建HANDOFF。
按PLAN7及SPEC2/4/7/9/10，实现稳定bot/group/user隔离、有限JSON/持久HMACkey/MD只读视图、相关注入；固定record/proposal schema、自述/管理员/candidate晋升、单值/多值槽、同来源不续TTL、合并/过期/稳定淘汰、同轮proposals与正文共用输出预算，不增加模型/embedding/后台做梦。
明确speak/silent入站提交与文字ACK承诺分开，固定base_revision/generation/phase幂等及CAS，重启丢未提交pending，删除/黑名单写持久purge intent并净化所有副本，失败禁读、迟到ACK不复活；mentions旧个人history不能升为群共享事实。配置/学习默认关闭，本机固定/确认/纠正/删除走同一锁与校验。
完成M01—12、组合预算/协议/原event ACK及两runner实际路径替身验证，独立verify_lap30和reports/lap-30-*，不得覆盖旧报告。同步菜单/示例/README/任务进度和回滚。
不修改忽略的本机配置/凭据/真实记忆，不启停/登录真实bot，不调用真实模型、QQ接口或群发，不使用私密附件当素材。完成后仅commit/push本任务检查过的文件并核对远端；一般细节自行处理，方案级能力缺口记录后回规划，区分离线/真实/完整验收。
```

五项代码/离线交付后，再按用户指定的唯一session、后端、总调用预算、授权群和样图做部署/真实验收；本指令不自动授予真实登录、群消息/成员查询或模型消耗。登录LAP-24、搜索LAP-18及旧验收差额继续保留。
