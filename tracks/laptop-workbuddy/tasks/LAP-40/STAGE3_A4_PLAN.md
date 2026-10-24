# LAP-40 / A4：全链非阻塞接线详细规划

返回[项目入口](../../../../PROGRESS.md) / [总交接](HANDOFF.md) / [工作根与用户实测流程](WORKTREE_AND_USER_TEST_PLAN.md) / [medium实施指令](SOL_MEDIUM_START.md) / [A4交接](STAGE3_A4_HANDOFF.md)。2026-10-24，Asia/Shanghai；Sol max规划，**当前不实施、不自动派代理**。

## 1. 目标与非目标

把SnowLuma私有适配的同步身份helper改为全链非阻塞验证，使现有控制、早期入站过滤和允许发送路径真正可用。复用AstrBot与自研业务层，沿用同一访问控制、一次模型、单次发送及unknown语义。完成本阶段只证明A2接线的离线合同；B资格代码与真实QQ前置另列，不把它写成已经能开bot。

用户实测出口是：基础可运行条件通过后，即交给用户启动、正常收发和记录问题；实际性能、回复效果、72小时和7天分别由真实使用验证，测试后拟由Sol high调试。72小时/7天不作为首次试用前置。

本阶段不新增功能/触发范围、public配置、后端或付费API；不调整账号/群/黑名单/人设/模型，不实施B/C、不安装QQ、不加载native、不监听真实端口、不启停/登录/发消息/调用模型。Sol max当前只读核对和写文档；用户另开Sol medium会话并给出实施指令后才可执行下述任务。

## 2. 当前证据和未审草稿

| 已核源码/证据 | 对方案的约束 |
| --- | --- |
| public `adapters/snowluma/control_plane.mjs:createControlHandler` | 请求期限与成功绑定后的ownerLease已分离；wire/HMAC/seq/nonce和3秒保持不变。identityCurrent/observe仍是同步回调，须读取当前操作已核scope，不再触发阻塞进程 |
| private `src/a3-channel.mjs:createPythonChannel` | init及identity/stop_identity/created/pipe/gate/stopping/meme目前经spawnSync；层层current重复启动helper。120ms慢helper的bind共51次/6077ms，不能通过3秒合同 |
| private `src/a3-runtime.mjs` | dataCurrent/observation/ownerLease/permission.current相互调用；仅替换最外层spawn为Promise不够，不能让同步回调误将Promise视作true |
| private `a3-work/boundary.ts:admitPacket`及HookManager | 现同步准入先检查PID/account、固定消息类型、body<=65536、元素<=128，再纯投影和policy；异步排队必须仍在转换、历史、store和logger之前 |
| private `src/a3-actions.ts:createFixedActions` | 已限定动作，最多16个pending、请求<=65536字节；冻结参数和socket能力、单次提交/unknown ACK应保留 |
| private QqHookClient、HookManager、HighwayClient | 最后敏感点在实际connectSocket、控制写队列、注入与Highway connect/write；上层先检查后长await不足以覆盖最后提交 |
| 旧A4候选与根额外fake复现 | 候选5项通过；fresh后5ms close，120ms回包后仍resolve，scope无效但killCount=0。close/stop必须撤销等待及自己创建的在途helper，不能只置flag |

新工作根`E:/CodexWS/QQbot_Snowluma`、分支`codex/lap-40-snowluma`，迁移检查点72536d3。私有2901文本/27内部junction迁移已根审，集合SHA256 a500823f5096cd560cb2edc54c0a4b3c5c4d76f81ae05276bc46f1e4a87e8a30。旧C根及原E运行根未改。

本轮曾误自动续派，用户纠正后已interrupt，状态为interrupted。只读核对：迁入2901基线文件没有改动；忽略区额外留下`a4-work/`424文件、`prepare-a4.py/build-a4.mjs`及`src/a4-actions.ts/a4-entry.mjs/a4-material.mjs/a4-native-factories.mjs/a4-runtime.mjs`。没有a4-dist或A4执行证据。这些仅为未审准备稿，保留不删除，不作已实现/离线通过基线；下次medium先审文件归属和与A3的差异，不能直接运行它们。

## 3. 内部接口与生命周期

以下名称表达内部合同，可按现有模块组织调整命名；不增加JSON wire字段、CLI参数或配置绕过。

| 内部对象/操作 | 必须行为 |
| --- | --- |
| 异步channel初始化 | 受管限定继承管道读取正式Python loader投影/独立秘密，严格结构和当前父Node身份；未初始化/未资格前不构造native/server。错误保持closed，不用任意accepted=true替代 |
| `withOperation(kind, deadline, callback)` | 创建不可从wire伪造的逻辑许可，绑定owner/epoch、Node与QQ PID+created、配置摘要和适用socket generation；用ALS仅在该操作内传播。callback结束/取消即释放引用 |
| `freshBoundary(operation, boundary)` | 异步短helper核验当前身份/stop/pipe/gate；结果为本操作短scope，最长100ms，且不超操作deadline。敏感边界只接受其真实当前scope，不用全局永久trusted缓存 |
| 同步`current/observe/identityCurrent` | 只读当前操作的已核scope与本地不可逆撤销状态；无scope、过期、回拨或绑定不符即拒绝，不启动进程、不返回Promise、不递归fresh |
| 持续ownerLease | 只捕获handler的绑定/代际状态；在每个后续操作自己的fresh上下文查身份/stop。不能捕获bind请求的100ms scope或requestCurrent |
| `cancel/close/stop` | 立即不可逆撤销适用逻辑许可/排队项，取消timer及等待，停止接受新工作；只对本次创建的child handle请求终止。kill请求不等于已退出，退出未知仍留账/closed，不能再起helper掩盖未知 |

短scope过期仅意味着需要新鲜证明，**不能靠过期scope继续提交，也不能把正常长操作自动变成永久无权刷新**。逻辑操作只要仍在既有总deadline、未撤销且绑定不变，可以在下个敏感边界重新fresh；已经被stop/epoch/socket失效撤销的逻辑许可永远不能因此复活。

helper并发上限1、单次最多2000ms；普通输出最多16KiB，登记meme沿用既有最多12MiB响应/8MiB图像及摘要校验，不能推广到任意文件。所有helper时限取剩余操作预算更小值，返回必须核实际spawn PID、自捕获created/parent、完整退出和封闭schema；stdout超限、异常、时钟异常或终止未知永久关闭对应broker。保留最多16条helper元数据，不常驻watch、不新增registry writer、不写正文。

## 4. 控制面和停止顺序

HTTP壳收到请求即启动3秒总期限，包含收body、排队、身份fresh、handler及ACK，继续8KiB输入限制。不能在身份helper之后才开始timer，不能增加3秒。正式handler仍负责原HMAC/seq/nonce/issued/expires；HTTP取消是内部能力，不能由JSON伪造。

bind：入请求fresh → 原handler验证 → 在实际注入/新pipe连接前按边界fresh → 同turn同步校验后执行一次副作用 → await后再查命令期限与撤销 → 原ACK。后续health/发送在自己的操作中复核长期ownerLease，bind结束后的请求完成标记不应切断它们。

drain/stop：保留控制代际和停机优先；停止新准入并撤销未提交native/排队操作。stop-only身份仅用于合法stop/ACK，不能授权bind或数据发送。正常可证身份的stop应完成ACK；若helper退出/身份已未知，则如实unknown/拒绝，不伪造成功或重试。服务最终close与ACK完成顺序明确，不能先销毁唯一校验通道再误丢本可完成的stop ACK。

控制请求优先于尚未开始的普通工作，但未经认证的请求不能触发stop副作用。helper被占用时仍按收到时的剩余期限处理，不无界排队、不并发起第二个helper；超时即取消原请求，不迟到bind。

## 5. 入站与RPC有界接线

原始包只接受已有固定owner PID/account/类型/source/retCode与<=65536字节限制。新增异步准入队列固定最多16条、合计256KiB、每条最多65536字节，按先到先处理；从现有私有2MiB RAM预算中预留并计费，不能另增无界正文副本。入队前只做封闭元数据/长度检查；异步fresh后才做既有纯信封投影/黑名单/授权群判断。拒绝/超限/过期/stop包不得进入protocol主体处理、身份补全、引用回拉、store/logger/群窗口。满额直接丢弃并只记封闭计数。

队列项冻结owner/epoch/source与当前回调存活关系，保留原HookSession的armed/rx/outbound真实观测来源；排队本身不证明业务准入或健康。停止/断连/换代清引用且旧项不恢复。不得把Promise交回原同步if判断，也不能在普通Bridge/OneBot转换之后才补过滤。

RPC保持原固定动作、16 pending/65536字节上限和现有认证gate socket。参数最终冻结后发放逻辑许可；所有async阶段继续核socket/epoch/存活，不能从请求JSON接收authenticated/current。元数据只限授权群，成员/收藏/视觉旧资格不放开；`send_msg`仅沿用群别名。任意历史/文件/URL/私聊RPC仍关闭。

## 6. 真正提交点与ACK

每个敏感函数须await fresh，再在**同一event loop turn内同步检查**逻辑许可、短scope、pinned目标、当前socket和冻结参数，然后调用唯一副作用。不能await检查后再排一个未受保护的callback，也不能把原void栅栏改async却漏await。

| 敏感点 | 要求 |
| --- | --- |
| 单PID/新pipe连接及注入 | 核登记PID+created+exe、精确目标pipe与当前owner；禁止全局枚举或日常账号库发现；真实提供器仍待后续资格 |
| QqHookClient实际writeControl队列 | 在队列真正取出且最终socket.write前fresh；核仍为同一socket，记录提交状态只发生一次 |
| Highway tcpConnect/socketWrite | 每次真实connect/write前fresh；长上传跨scope有效期可重新证明，stop/换代后零后续body/最终消息提交；不恢复重试 |
| 最终MessageSvc.PbSendMsg | 以实际native提交点标记messageSubmitted，防重复提交；前拒绝与提交后unknown分开，不能先标成功再被底层栅栏拒绝 |

gate原有群停言栅栏仍以其有界WS写为线性化点，内部票已剥离；Snow不承诺撤回gate已提交的在途帧。transport stop/失效撤销尚未native提交的动作。成功/partial/unknown按一次原event ACK流转；unknown无助手历史/记忆晋升，不重发、不自动fallback。

## 7. 涉及文件与实施顺序

1. medium重新领取LAP-40 A4、记录新session/时间/文件、写后重读。只读审未审草稿和迁移清单；先确认旧2901基线未改，禁止先跑prepare/build。
2. 独立`a4-work/a4-dist`，完善私有异步channel/broker及合成process测试；先交close/超时/未知退出/短scope与长许可分离的可审检查点。旧A0—A3源/产物/证据原样保留。
3. 接控制和正式snapshot/owner、单PIDpipe/Hook装配；用实际固定上游类+fake native/server/process证明慢120ms helper下bind/health成功且总期限达标，合法stop ACK与取消均过。
4. 接原始包有界队列、允许RPC和最后writeControl/Highway/native栅栏；再穿实际gate/CQHTTP/AstrBot Event.send/TaskStore/QQRouter/MemoryStore的ACK闭环。
5. 给执行级报告、源码/产物/依赖闭包摘要与准确命令，完成本阶段Git交付，停在A4/A2交给Sol max审阅。**不自动进入B/C，不自动派别的代理。**

预计私有文件：`src/a4-*-channel/broker/runtime/actions/material/entry/native-factories`、对应prepare/build/check脚本、独立overlay及产物；具体命名可沿现有风格，禁止把上游修改源/patch/bundle提交public。公开默认只改本交接、原创报告、PROGRESS/工作线HANDOFF/TASKS的归属段；如必须动原创public控制接口，只限原合同内修复、先登记路径和理由，不改wire/期限/业务。会改变方案的缺口回Sol max，普通已规划实现细节由medium自行完成。

## 8. 验证与验收矩阵

| 必测合同 | 通过条件 |
| --- | --- |
| 120ms慢helper bind/health/文字 | 穿实际装配成功，control总<3000ms；列实际helper次数与每次对应边界。不能用403/仅超时及时/零延迟计数称可用 |
| 请求取消/迟到body/close/stop | await中的许可同步失效；promise有界收束，只终止本次handle，迟到回复/回调零副作用；退出未知不再spawn |
| bind后超过100ms再health/发送 | 在新操作fresh后合法成功，证明长期ownerLease不捕获旧scope；旧epoch/取消scope仍永久拒绝 |
| helper卡住/输出超限/伪PID/时钟异常 | 受总deadline约束、closed/unknown，无第二helper和自动重试，无秘密/路径原样日志 |
| 并发高频原包/RPC与内存 | 数量/字节峰值不超限，满额不进入任何下游sink，控制仍有界响应；排队不把黑名单正文留到历史 |
| native队列中stop/换epoch/socket | fresh后同turn提交；未提交零native，已经提交仅一次ACK/unknown，不回滚成可重发 |
| 长图片成功及中途撤销 | 跨100ms正常上传可逐边界fresh；旧scope不被延长；撤销后零后续PUT body/最终消息提交 |
| 实际框架ACK/历史/记忆 | 真实框架类配fake I/O分别覆盖前拒绝/成功/unknown/partial，pending收束，unknown无晋升和重发 |
| 隐私/兼容/原件 | 原15项sink限制与允许路径同时成立；旧NapCat/快照兼容，原71文件/ZIP摘要不变、private无native，public无派生源码/秘密 |

合成结果不能证明原生保护、真实pipe、QQ数据范围、真实收发或性能满足。测试按决定性合同和重复场景分开记录，不累加夸大；只重跑受影响检查，已过全量不为计数重跑。当前规划阶段不运行这些实施测试。

## 9. 配置、材料、兼容和回滚

不新增public字段；provider默认napcat、恢复/QQ重启false、mentions/free及用户local/persona不变。helper、队列和scope上限是受审私有实现常量，不能以local临时放宽。原官方Node可原位置只读借用做合成，原E venv亦只读借用；cwd/PYTHONPATH明确新根且禁止写pyc。

新根缺独立venv/官方运行包、接受记录仍留旧根，不创建整套运行态链接或伪造接受。开发材料读取只允许固定旧根只读anchor；生产安装/准备必须后续单列，B不能把开发anchor当可写配置或合格部署。无真实资格时entry/require_runtime继续closed。

A4失败保留独立草稿/诊断，旧A3及原运行环境不动；选择旧A3作离线比较不等于可部署回退。未来真实回滚需证明受管退出、保留unknown/预算，再显式恢复有限provider字段；本阶段不执行。若Windows数据机制、原生保护或进程覆盖迫使改变环境，先完成独立可做项，记录证据并回规划，不能猜参数或创建系统用户/VM。

## 10. 后续可运行出口

A4审阅后，用户再指令medium实施[B资格/probe合同](STAGE3_QUALIFICATION_SPEC.md)的代码/fake验证；真实Windows数据机制、干净QQ和原生部署另证。它们通过后才形成可交用户的启动/停止、基础真实@/收发/受控表情、脱敏日志和故障收集步骤。试用与72h/7天状态分开，不因长稳未完成阻止具备前提的首次实测。所有后续实施/真实probe均由用户另行指令，当前不自动执行。
