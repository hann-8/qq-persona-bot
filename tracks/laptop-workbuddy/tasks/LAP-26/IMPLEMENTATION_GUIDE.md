# LAP-26后续medium实施指引

返回[PROGRESS](../../../../PROGRESS.md) / [LAP-26交接](HANDOFF.md) / [详细合同](PLAN.md) / [TASKS](../../TASKS.md)。

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

## 给后续实施会话的复制文本

选择对应任务编号后使用，不把四项一次交给同一session：

```text
阅读 E:\CodexWS\QQbot\AGENTS.md 和 PROGRESS.md，再按活动线入口读 TASKS、LAP-26 PLAN/HANDOFF/IMPLEMENTATION_GUIDE。
我已在会话设置选择 gpt-6.1-sol/medium。本次仅实施 LAP-31（请求模型进程清理、阻断诊断与有证据恢复），先登记任务归属并创建任务HANDOFF，按LAP-26 PLAN第13节完成代码、必要离线/自造受管进程及框架验证和文档，再按长期授权commit/push并核对远端。
不改忽略的本机配置/凭据，不启停/登录真实bot，不调用真实模型、群成员API或群发；不自动开始LAP-27/28/29/30。只能操作自造测试进程及有本任务创建证据的子孙，不按进程名批量结束。遇改变方案的能力缺口先完成独立部分、保留证据并回规划，不能删unknown假恢复、换模型/付费API/放宽工具。
```

后续改为LAP-27/28/29/30时，把任务编号、任务名和第13节限定一同替换为对应合同，先检查依赖已交付，不能只替换编号而保留错误范围。用户提供的三份日志包含私密消息，只允许脱敏诊断，不能入Git或复用作模型输入。
