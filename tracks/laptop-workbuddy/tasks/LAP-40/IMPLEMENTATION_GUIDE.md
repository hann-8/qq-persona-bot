# LAP-40 sol medium分阶段实施指引

返回[PROGRESS](../../../../PROGRESS.md) / [PLAN](PLAN.md) / [HANDOFF](HANDOFF.md) / [TASKS](../../TASKS.md)。所有相对路径相对本项目`E:\CodexWS\QQbot`，worktree内则以其根为准。

## 执行授权与协作

用户已明确要求：规划完成后根agent逐步调用`gpt-6.1-sol / medium`落地，并复核；用户已允许branch，现休息。不要重新索取阶段1—5独立代码/离线验证/Git授权。不要为用户创建新的Codex chat；使用当前任务内的medium子代理，串行阶段即可。

根agent先完成PLAN与本指引、提交推送规划分支并核对远端。每阶段派发时附精确规划commit和worktree，实施者读根AGENTS、PROGRESS、工作线HANDOFF/TASKS、40 HANDOFF/PLAN/本指引，再写其阶段领取记录并重读。一个子任务只推进LAP-40当前阶段，不推进其他LAP。

根agent独占PROGRESS/工作线HANDOFF/TASKS，子代理可写40目录内阶段交接、报告及已派发代码；任何同文件不明修改先报告根agent，不覆盖。不并行改共享文件，不启第二个真实bot。父agent通过collaboration继续派发，无须给其他chat发消息。

配额遵照用户最新指令：检查300分钟窗口remaining，<=5%时保存交接并停止新步骤，通知根agent安排北京时间2026-10-24 07:10恢复；不得使用reset credit或购买额度。领取、提交前和约15分钟检查一次，未知值不能当充足。任务可独立推进则继续，不因用户睡觉擅自结束于计划。

## 共同硬约束

- 原有账号/群/黑名单/私聊关闭、mentions/free/停言、一次模型尝试、工具隔离、model profile和personality不变。本机local、secrets、QQ数据和登录不为离线验证修改；零真实模型/QQ群消息/SSH。
- 官方原生组件有单独限制：禁止自动化下载/解压/搬运/重打包/部署；禁止绕过保护。只public提交原创代码，不提交上游修改源码/patch/衍生bundle/native。私有源码与JS适配只在忽略runtime，不能假定.gitignore天然排除了被git add -f的文件。
- 原NapCat QQ已patched，不能Snow二次注入；不读日常QQ认证、不adopt已有QQ、不按进程名kill。无G0/G1证据就不进入真实阶段，不停止当前bot，不切本机provider。
- 所有健康/管理检查零推理、无群消息；不靠#sl、get_msg/history/forward回查来探活。静态状态不能造假成为实时健康。
- 不能只实现helper而不接现有入口/最终发送；也不能只写原创模块就称上游已完成适配。缺口分层标记，继续独立部分。
- 只运行离线自造夹具；不得导入带真实启动副作用的manage/运行模块到测试中。若框架依赖需复用，指定只读路径和工作目录，禁止扫描/写原运行data。

## 阶段1：配置/provider/只读准入

根agent可直接发送以下任务：

> 你是LAP-40阶段1实施者，按已固定PLAN实施，模型由根agent指定为gpt-6.1-sol/medium。先读AGENTS/PROGRESS/工作线HANDOFF与TASKS及LAP-40三文档。仅完成阶段1，结束后停在交接，等根agent复核再继续。先检查5h额度。根agent会提供规划commit与隔离worktree，勿在真实运行checkout改代码。检查干净状态并在LAP-40/HANDOFF增加阶段领取/文件归属，根入口台账由根agent管理。实现可选qq_transport与消费层resolve默认值、provider描述、固定本机proof结构、只读inspect、模板及同行中文注释；旧raw规范化/snapshot semantic_digest/schema1/2/3保持兼容，无节仍默认NapCat，不回写本机配置。不执行任何安装、QQ/服务/端口/模型/SSH动作，不实现自动原生部署。缺官方包/干净QQ只报告，不阻塞原创代码与测试。用有意义自造测试验证边界；阶段交接列变更文件、命令/结果、未验证和下一阶段。按长期授权可commit/push本阶段归属变更并核对远端SHA，不force、不合main、不提交私密资料。

阶段1检查点：新字段校验/默认值、旧快照精确摘要、未知/碰撞/链接路径/非法端口；inspect无真实网络/秘密输出。proof是严格字段/摘要证据，不是“valid=true”开关。先提供结构和静态检查，没真实包不输出G0/G1通过。

## 阶段2：原创策略、健康与gate

根agent复核阶段1后，在同一worktree串行派发：

> 继续LAP-40阶段2，只按PLAN第4/6节完成原创project_policy、独立HMAC健康proof和统一channel_ready，接实际onebot_gate和最终router发送栅栏。先更新本阶段文件归属/额度检查。拒绝事件必须在store/log/history/model callback前终止；引用/转发不补拉，#sl不得旁路。单响应/缓存/日志有界，测试全用自造消息和假transport，不启动QQ/Snow/AstrBot服务或真实模型。覆盖未armed/good缺失与false/过期重放/nonce/seq/PID复用/摘要变化/停机/晚到模型结果，保留NapCat默认和ACK/停言语义。原创接口测试与上游真实接线证明分别记录；未接线不能称Snow适配完成。完成有意义回归，提交推送核对SHA并给根agent审阅。

检查所有读取self.connected/online的门槛，含成员、视觉、收藏、free窗口和最终发送，不只HTTP status。旧unknown/partial账本和历史ACK不清理。控制面不能有任意动作/路径/账号/PID；构建/策略/监听身份也要核验，不能接受任意自己签名的假healthy。

## 阶段3：固定上游私有接线

> 继续LAP-40阶段3，先依据PLAN第3节确认本机是否存在操作者准备的官方原包、适用部署证据和干净QQ证据，只只读检查指定项目目录。不得自动下载/部署原生文件，不触日常QQ，不clone带native blob的全仓。允许在忽略runtime/snowluma-private内做源码范围的私有JS接线/测试，保持原生组件与保护不变；若源获取会连带原生组件，改为定点读取所需源或记录缺口。public只交付原创接口/合成测试/摘要和报告，不提交上游修改源或patch。核对core早期分支、禁广域发现/内置发送/#sl/历史补拉/磁盘消息store/所有原始logger sink/其他网络入口的实际接线，给固定源码位置+私有摘要和执行证据。当前全局Node24.22.0不满足Snow实际引擎，不能冒充构建通过，也不能改全局Node。无合格本地运行时/原包或保护不允许私有构建时，完成可做部分并精确记录未通过门槛，随后交接阶段4；不要在此空等操作者，不伪造适配manifest，不做真实注入/登录/启停。

根agent判断是否需要补计划。一般私有接线细节可自主完成；保护不兼容、原生条款/原生数据无法满足属于能力缺口，不得靠关闭保护/扩边界解决。尚未执行完整私有合成测试时，最多称“接口/接线源码已准备”，不能称已可启用Snow。

## 阶段4：受管生命周期/恢复/操作CLI/试验采样

> 继续LAP-40阶段4。实现provider-aware manage/process_host、单writer身份registry/stop优先、固定health控制面、持久write-ahead恢复预算、CLI prepare/verify/activate/trial/rollback和有界状态资源采样。G0/G1/私有证明缺失仍可用假进程假时钟验证全部项目侧代码，真实启动必须硬拒绝。recovery默认false，QQ重启另需3/3证明且默认false；每事故最多一个动作，24h Snow<=2/QQ<=1，冷却1800，grace30/drain150/ready180，stop和cleanup未知优先。禁名字kill/未知进程adopt/自动重登/自动NapCatfallback/Startup/自动群消息。activate及回滚只停机有限字段原子事务，源变化拒绝覆盖；不实际修改local配置。提交前受影响回归，报告精确文件/测试/缺口，commit/push核对SHA。

不得启动真实组件作fixture、睡眠多分钟凑验证或将静态proof当实时。watch与manage共享锁唯一写registry，不分裂进程归属。停止按已加载provider与snapshot，不按当前磁盘settings猜旧实例身份。没有完整退出证据保留unknown，31B差额不清空。

## 阶段5：集成审阅/Git/等待清单

根agent先查差异归属、实现是否接上真实调用点、离线用例是否经过实际项目路径、是否泄漏原始日志、遗漏历史补拉或持久store；有缺陷退回medium修复，根agent不越过其medium实施职责去大改代码。验证通过后更新PROGRESS/工作线入口与40 HANDOFF，明确：实现/离线/私有接线/真实启动/长稳各自状态。

阶段交付要求：

1. 任务代码、模板和用户可读操作说明；原创/私有上游文件边界清楚。
2. 可重复离线报告，真实调用/未知项分开，旧persona字节断言失败如实单列；不改人设。
3. inspect输出的当前阻断类别：如official_bundle_missing、native_deployment_unverified、clean_qq_unverified、data_scope_unverified、private_build_unverified、operator_scan_required；无账户/私密内容。
4. 本阶段/分支commit和远端完整SHA一致，剩余工作区差异归属清楚；不擅自merge main。
5. 没真实前置时，保留原运行checkout/运行配置/进程不动，交付“尚未切换”，不用含糊的“迁移完成”。

## 阶段6/7：真实试运行的执行出口

用户授权尝试替换，但受AGENTS身份和本PLAN技术前置约束。不能假定新包、原生数据、无扫码条件已经满足。只有全部证据成立，根agent才派一个唯一的medium执行者；其余agent此时不得启停或发起真实验收。

若前置齐全且不需要睡眠中的操作者，执行一次受管暂停/停止、有限配置切换、Snow单次启动，记录实际channel_ready和armed；观察授权群自然新消息，不自行发测试消息/调用模型。任何步骤需扫码就waiting_operator，不循环登录。不自动运行3次QQ重启或导入QQ收藏。

72h/7天由本机采样器在已授权真实运行后记录；agent不空等7天，也不凭本次短时结果打长稳通过。按PLAN记录中断/未知/人工介入/资源，必要时提供继续检查命令。完整长期结果待足够时间/证据，旧验收差额保留。

## 配额触发时的最小交接模板

写明北京时间、300分钟剩余额度、当前stage/branch/HEAD/worktree、已提交/未提交文件、刚执行验证、下一条可执行动作、真实bot是否被动过、阻断和待人工项。子代理通知根agent后停止。根agent用Codex heartbeat安排本线程2026-10-24 07:10恢复；提示先读该交接和用户后续输入、查额度与子代理状态，按阶段续做，勿重新创建任务/重复启动。无阈值触发不提前安排无意义唤醒。
