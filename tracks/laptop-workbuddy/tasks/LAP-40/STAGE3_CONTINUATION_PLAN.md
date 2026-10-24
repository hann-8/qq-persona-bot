# LAP-40 阶段3续作：真实材料、私有入口与probe资格（旧路线，已被取代）

> 2026-10-25用户决定：本私有改造续作规划已整体被[官方OneBot最小接入计划](PLAN.md)取代，以下仅为历史。不再领取其中A4复核、B/C或probe/资格任务，不把缺项转为首次试用前置。A4代码、产物和证据原样保留，不追加复核/测试；当前下一步只看[Sol medium最小指令](SOL_MEDIUM_START.md)。

返回[项目入口](../../../../PROGRESS.md) / [任务交接](HANDOFF.md) / [总计划](PLAN.md) / [私有清单](PRIVATE_WIRING_CHECKLIST.md) / [材料核验报告](../../../../reports/lap-40-stage3-materials-2026-10-24.md) / [B资格/probe合同](STAGE3_QUALIFICATION_SPEC.md)。2026-10-24，Asia/Shanghai；`LAP-40-max-realentry-next`。本文件细化总计划阶段3，1/2/4/5已有独立交付不重做。属于规划，未宣称私有接线、probe或真实切换通过。

2026-10-24 22:49最新执行边界：当前Sol max仅做详细规划，用户另开Sol medium并下实施指令；此前根自动派发/续派的工作安排已被用户纠正，不能沿用。新根与当前A4范围见[A4详细规划](STAGE3_A4_PLAN.md)/[medium指令](SOL_MEDIUM_START.md)，以下技术合同仍作为按需参考。

## 目标、范围与现状

先得到符合固定版本/许可/项目隐私合同的私有JS入口及执行级合成证据，再补可信资格判定和受控probe。QQ原生数据范围另证，满足前置才一次真实试验。账号、模型、触发范围、默认配置及恢复预算不变；不增后端、WebUI动作台、自动登录、无新消息主动任务或其他环境。

2026-10-24用户已提供两下载路径，随后明确“接受，并且已经解压完成”。12:43只读复核指定runtime：原版index/两协议/Node及5个原生文件摘要与原ZIP一致，自带`node.exe --version`为v24.22.1，满足固定engines；没有运行Snow入口、加载原生组件或QQ。用户同意不能替代私有构建/数据范围证据，也不是书面扩展原生部署许可。

原ZIP仍只在用户指定Downloads，项目runtime内原ZIP不存在；干净QQ、私有源码/入口、proof仍不存在。当前静态检查要求runtime内原ZIP，文件已下载/解压不能冒充该检查通过；若沿用原检查，由操作者手动将完整原ZIP保留到`runtime/snowluma/v2.1.1/SnowLuma-v2.1.1-win-x64.zip`，agent不自动复制/搬运原生包。

## 决定性代码证据

| 已核对路径 | 结论与实施含义 |
| --- | --- |
| `transport_owner.py:require_runtime` | 当前无条件抛TransportBlocked；缺口包含项目资格代码未实现，不能全部归因于操作者缺材料 |
| `scripts/transport.py:capability-probe` | 目前调用同一`blocked_runtime`，没有真实probe执行器；若直接要求probe完成后的完整资格才允许probe，会形成循环依赖，续作需分层 |
| `qq_transport.py:validate_static_proof/inspect_transport` | v1仅严格校验路径/摘要并始终保留G0/G1阻断，不解析证据语义。不能靠填写证据JSON或改一个布尔解除总拒 |
| `transport_launch.py:snow_specs` | 现argv是未来私有入口合同：`--root/--config/--owner-record`；当前不是已知官方包可直接启动的布局 |
| 固定[core/vite.config.ts](https://github.com/SnowLuma/SnowLuma/blob/f8cb15c27bca3d2d1bd044a921e55bfc44bb5e60/packages/core/vite.config.ts) | 标准构建要求/复制native，sqlite插件也进入构建；禁止直接运行。保留protobuf转换、合法文档检查及第三方声明，设计独立JS-only配置，不能删guard后声称标准构建通过 |
| 固定[common/native-path.ts](https://github.com/SnowLuma/SnowLuma/blob/f8cb15c27bca3d2d1bd044a921e55bfc44bb5e60/packages/common/src/native-path.ts) | 官方根据模块位置寻找native。私有产物在另一目录时，须显式固定到已核验原包原位置，禁复制native到新目录、搜索全盘或替换保护 |
| 固定[core/webui/consent.ts](https://github.com/SnowLuma/SnowLuma/blob/f8cb15c27bca3d2d1bd044a921e55bfc44bb5e60/packages/core/src/webui/consent.ts) | 官方有`resolveEnvironmentConsent`，要求`SNOWLUMA_ACCEPT_EULA/PRIVACY`均显式接受；支持无UI的短期声明。私有早期入口需在native/扫描/缓存/监听前实际检查两份原文/接受证据，不能利用原UI“缺文档fail open”分支 |
| 固定[bridge/qq-account/paths.ts](https://github.com/SnowLuma/SnowLuma/blob/f8cb15c27bca3d2d1bd044a921e55bfc44bb5e60/packages/bridge/src/qq-account/paths.ts) | Windows使用共享Public Documents的UserDataInfo.ini或当前用户Documents/Tencent Files，`qqDataRootsForPid`的Windows分支也不提供每PID隔离。不能复用默认探测器读取日常登录库，不能把Linux HOME测试套用到Windows |
| 固定[Windows/Linux路径测试](https://github.com/SnowLuma/SnowLuma/blob/f8cb15c27bca3d2d1bd044a921e55bfc44bb5e60/packages/bridge/tests/qq-account-path-isolation.test.ts) | Linux测试覆盖进程HOME；Windows用的是合成共享ini，并非真实QQ原生路径重定向证明。当前没有已核验的Windows原生数据参数 |

固定提交均为`f8cb15c27bca3d2d1bd044a921e55bfc44bb5e60`。上表为源码事实；“须/设计”是待实施合同。编译成功不证明实际保护允许、原生范围隔离或真实收发正常。

## 私有入口与构建合同

1. 修改源、私有构建配置、执行级合成夹具、依赖与产物全部在忽略的`runtime/snowluma-private/`。只取构建所需的固定纯文本源/锁文件/声明；不得clone含native的整仓、下载另一原生包或搬动原包。public只记原创合同、结果和摘要，不提交上游修改源码/diff/bundle。
2. JS-only构建输出也在该私有根，且不得清理/覆盖原版目录。按实际依赖闭包读取相关源文件，采用独立配置，禁止import或执行标准core/vite配置、build:all、安装生命周期脚本或sqlite原生构建。第三方构建工具如确需项目内依赖，应先记录精确版本/锁摘要/安装命令与禁脚本策略，不改全局Node/pnpm/WorkBuddy；发现自动拉取Snow原生的路径立即停此分支。
3. 原生模块/FFmpeg/SQLite只按已核验原版包原位置解析；限定路径并校验文件身份/摘要，不递归发现、不复制或修改其字节。正常保护/许可/激活机制原样执行；运行时保护拒绝就是能力缺口，不能修补保护。构建/执行合成测试不加载真实native。
4. 入口先校验固定root、加载快照、owner/代际及两协议原文摘要与操作者接受证据；缺失/变更/部分同意/非法值都在native导入和所有副作用前closed。使用官方公开支持的声明语义；接受仅注入受管Snow子进程副本，不改全局环境，不伪造consent.json。`snow_environment`仍先清除继承`SNOWLUMA_*`；未来只从已验证接受记录派生两项固定值，不接受任意新增环境键。
5. 不运行原版index/launcher作试验。最早过滤、纯信封投影、所有logger/store/history/内置答复/扫描/额外网络的15项实际私有接线按原清单逐项完成，任一缺项保持未完成。OneBot过滤位置不能替代protocol/Bridge前置。
6. health/control监听由实际私有入口挂接原创handler，严格固定回环地址/端口、8KiB/3秒/nonce/HMAC/持久seq及owner；观测来自实际HookSession，armed/rx/outbound分开。合成注入只存在测试路径，生产入口禁止测试依赖或“默认healthy”。私有入口argv须与现有snow_specs逐项对照。

## 分阶段任务与唯一归属

根独占PROGRESS、工作线HANDOFF、TASKS、本HANDOFF及本规划；每次只派一个`gpt-6.1-sol/medium`，实施前登记并重读。私有文件不得与后续agent并写。每步根审后才续派，不创建用户chat替代子代理。

| 顺序 | medium本次任务 | 验收/停止出口 |
| --- | --- | --- |
| 3R-A0 | 核实并实现私有早期bootstrap/合法同意/固定native解析与JS-only构建路径；先完成最小可执行合成检查，不接真实QQ | 实际私有源与JS产物/依赖摘要；合成副作用计数、原包摘要前后一致；不能合法分离就给精确缺口，不运行标准build试错；不生成已合格manifest |
| 3R-A1 | 在A0通过后完成原清单1..11的纯投影/早期访问控制、关闭旁路/历史/磁盘消息/全sink，以及有界RAM与单一反向WS入站；当前WS动作可全closed | 固定上游实际parser/dispatch/handler执行级合成，拒绝路径convert/store/log/history/send=0；正常授权新事件可达净化forward。全closed动作只是中间检查点，不等于完整1..11或可用运输 |
| 3R-A2 | 完成原清单12..14实际armed/rx/outbound、控制handler/listener、正式snapshot/owner/spec及受认证gate原有允许动作的实际执行接线 | 固定观测源、身份/seq/nonce/stop/失效及允许动作参数校验；未绑定时全closed，合法允许动作不能永久省略；无真实native动作，保护允许仍待真实受控验证 |
| 3R-B | 实现下面的资格分层与真实probe执行器，先全部fake验证 | preflight不依赖probe结果，probe不放生产；缺G0/数据机制/身份时创建数0；正常启动仍closed，直至C真实证据全部存在 |
| 3R-C | 经根审确认Windows数据机制/候选干净QQ/唯一运行归属及人工窗口后，一次真实DROP probe，最多240秒 | 真实创建链/组件/数据访问互证；没有扫描窗口则waiting_operator，不自动扫码/重登/发消息；失败/未知保留账本并精确回规划 |

A0当前材料已足以开始，不等待QQ安装。A1/A2一般实现细节可自主处理；若需要改变原生保护、公开修改版、Windows用户/系统数据配置或原定项目边界，应先完成独立部分、记录能力缺口并回根，不自行扩大授权。3R-C不是本轮自动执行事项。

阶段划分补充：A1验证固定OneBot/Network构造链的隐私时，可暂时拒绝来自反向WS/debug的全部动作，不引入无owner身份的发送入口。A2必须补回总计划已有的gate允许动作：以当前owner/epoch、受认证的固定gate连接、加载快照和最终参数/许可为准，不能仅检查`allowsRpc`字符串。读取现有onebot_gate实际白名单及独立成员/收藏固定RPC合同；普通任意成员list仍拒绝，旧成员/视觉资格不解锁，收藏不自动导入。`send_msg`若兼容，仅接受现有group别名后规范化为send_group_msg，不增加私聊/其他参数。群metadata结果限制在授权群，受控表情只接受现有登记图片，不接任意URL/文件；引用/媒体不得通过允许发送分支触发历史或入站回拉。ACK按原成功/partial/unknown单次合同，不重试。A1/A2最终映射需同时保留“已关闭旁路”与“已实现允许路径”，两者不能互相替代。

发送提交边界澄清：沿用[LAP-35第84/102行](../LAP-35/PLAN.md)及onebot_gate._outgoing现有实现，群mode/generation在同群锁内最后校验，以gate有界WS写向下游提交为线性化点；内部qqbot_output_ticket在此前校验并剥离，不透传QQ。A2原生提交前栅栏复核的是当前transport owner lease/epoch/身份/健康、受认证的当前gate socket及冻结后的已验证最终参数，不宣称能撤销gate已经提交的在途帧。提交后发生群停言可晚到的既有在途消息仍据实ACK，不重发；transport stop/身份或epoch失效则继续撤销尚未native提交的旧回调。不得以伪造实时群票、自报authenticated或新增旁路接口补一个不存在的强保证；当前无须增加onebot_gate写权限。验证须区分提交前停言零下游提交、提交后延迟ACK，以及延迟native期间transport失效取消。

身份提供器集成补充：禁止在Node控制/入站/发送关键路径中层层spawnSync阻塞事件循环。可用非阻塞短helper，限定并发、缓冲与各场景既有总deadline（控制3秒含前置身份校验）；一次请求/原始包可复用同一已核原子scope，不能变成全局永久trusted缓存。scope绑定owner/epoch/pinned pipe及socket，进入敏感native提交、新pipe或注入前须新鲜复核；停止/失效不可因后续快照恢复旧scope。未经准入消息不能进入新增历史/群窗口/正文缓存，异步排队仍须遵守原有界内存/数量。新增慢helper/高频回调及总超时测试，不以零延迟fake证明响应性。无额外常驻watch/registry writer；短helper创建身份、退出/超时与Node异常退出限制必须公开说明，31B真实覆盖不因自报元数据而通过。

## 资格与probe的分层合同（待实现）

- **原版材料核验**只读文件/摘要/Node/协议。下载路径核验和项目内原包准备分开，核验不写配置、不登记启动、不打开任何端口。
- **probe前置资格**必须实际核验G0、私有合成记录与构建、可信干净QQ候选/创建路径、经审查的Windows数据机制、操作者指定的数据允许根及唯一执行归属；允许只建立DROP链路，不要求probe自己的结果、不要求登录ready/armed/生产activate。缺任一项创建QQ/Node数0。
- **真实probe**单次创建本次owner的QQ/私有Node，不进入AstrBot/模型/反向消息转发/发送。专用probe mode必须在最早私有入口DROP所有入站；没有get_msg/历史/默认账号数据库探测。仅收固定PID链、exe/原生加载、允许范围文件访问元数据、pipe/login/armed/账号匹配布尔及封闭诊断。240秒总期限包括等待/退出，取消/stop优先；未证明退出则unknown，禁止下一启动。不打印路径/身份/正文到普通CLI；详细元数据仅忽略本机证据。
- **生产资格**由可信收集器解析封闭的版本化证据、绑定固定原包/全native/QQ exe/私有依赖闭包/构建/策略/协议/配置摘要和实际probe结果推导。现有v1静态proof只作旧的静态检查；不得把某个JSON的`true`或哈希匹配当真实通过。新资格格式及字段需在B实施前先落精确schema和失败码复审；本规划不授权临时放开`require_runtime`。
- **实时准入**仍由当前owner、创建时间、listener与独立健康证明控制；生产资格只允许关闭准入的受管启动，绝不代替当前channel_ready。新epoch/构建/配置/协议变更使旧相应证据失效；旧消息/结果不复活。

Windows当前缺少原生数据路径覆盖依据。禁止修改共享`UserDataInfo.ini`、日常QQ设置、HOME/APPDATA、用户注册表或猜测`--user-data-dir`。probe也不能先启动未知范围再靠“未见异常”补资格；需先有可信机制和限定元数据观察方法，再受控验证。若同一Windows用户无法满足，回规划讨论独立系统用户/其他隔离环境，不自动创建账号/VM/切Linux。

## 配置、文件、验证与回滚

现有`qq_transport`默认provider仍napcat，恢复/QQ重启默认false；不改local/persona/profile，也不热加载。A阶段不新增public配置字段。协议接受和私有材料映射记录只在忽略区，其精确schema先由A0记录为私有实现合同；B新增资格schema须先根审。用户原有配置事务/快照摘要及旧NapCat兼容继续适用。

预计改动：A阶段私有`runtime/snowluma-private/`及原创报告；必要时原创公开接口/自造测试，但不向public写上游派生实现。B可能涉及`transport_owner.py/qq_transport.py/transport_launch.py/transport_cli.py/scripts/transport.py`和对应测试；限定为资格/probe接线，不重做恢复/采样。真实证据仅`state/qq-transport/`、秘密仅`secrets/`忽略文件。根台账每步更新确切归属。

验证优先在实际固定源路径用合成native/client/process/FS/network观察器，覆盖导入级副作用、缺同意、单份同意、文档变更/缺失、native路径逃逸/变化、PID复用、所有logger sink、引用/转发/超限/异常分支。构建前后核验官方index/docs/native摘要一致，输出中无native。公开接口变更才跑对应Python/JS/框架受影响回归；只改文档不重跑旧全量。所有合成计数单列，不能称真实保护/QQ隔离通过。

兼容：旧NapCat/旧snapshot和旧proof保留；旧proof即使hash一致也不授予新资格。迁移不删除原设备/历史/pending/unknown/恢复预算/旧验收差额。A失败只保留忽略区诊断和报告，不触原运行；B失败保持原总拒。将来回滚沿用停机有限字段事务与完整归属退出，未知不切换provider。原版目录和旧`E:/CodexWS/QQbot`均不覆盖。

## 当前出口与人工最小待办

原包解压、条款接受、自带Node已核对；A0可开始。操作者后续仅需手动保留原ZIP到检查器固定位置；QQ安装包暂不运行，先补可信Windows原生数据机制。需要扫码时再约单次窗口，无需现在等待扫码。所有真实切换/收发/免扫码/72h/7天资格仍未取得。
