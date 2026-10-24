# 原创SnowLuma私有接线接口

这些文件是本项目原创合同与自造测试，不含上游修改源码/patch/native。阶段2只完成接口，尚未在固定上游v2.1.1接线，不能称Snow适配或真实部署通过。阶段3须在忽略runtime中按PLAN核对最早分支、所有store/logger/补史/内置答复及原生保护，缺证据保持阻断。

阶段3已完成[固定版私有接线清单](../../tracks/laptop-workbuddy/tasks/LAP-40/PRIVATE_WIRING_CHECKLIST.md)的只读核对；随后操作者已准备原包/手工解压并接受两份条款，自带Node v24.22.1通过。新增[阶段3续作计划](../../tracks/laptop-workbuddy/tasks/LAP-40/STAGE3_CONTINUATION_PLAN.md)先私有JS-only/早期入口，再实际隐私接线/观测、资格及probe；干净QQ/原生数据与私有执行证据仍缺。普通core构建仍禁止直接运行；清单/规划不是接线通过，真实启用仍硬拒绝。

`createProjectPolicy`要求已核对的受管实例/代际及实时`identityCurrent`回调，只有授权group新事件、匹配账号、非self/黑名单、合法ID与有界message通过。私有适配必须在任何转换/store/logger/history/model回调前调用`admitEnvelope/processEnvelope`，拒绝事件不会进入convert、metadata或forward回调。唯一forward只收到净化后的当前事件；引用只保留ID，当前image仅限长最小元数据，其余媒体/转发占位，无原始昵称/正文日志、内置#sl答复、文件写入或回拉API。`allowsRpc`是内部同样必须遵循的动作白名单，不能以其代替gate的参数、身份与最终发送许可校验。

`admitEnvelope`不需要message数组，只核验原生身份信封；`processEnvelope`先准入，再调用convert，再限长sanitize/forward。time保留正整数Unix秒；image只透传当前事件限长file/url元数据给既有gate校验，不缓存/下载；非法at丢弃，合法all可保留。

实际RAM接口将message/media/reaction/temp/RKey元数据共享在512条/2MiB/300秒上界；发送关联另128条/64KiB/600秒。全部Map内存，淘汰/时钟回拨/TTL执行，无磁盘回退。只存ID/受控类型/时间和计数，不保存正文或URL。`status()`仅输出封闭计数/容量，无QQ/群/正文/任意异常字符串。

`createHealthProducer`与Python `HealthProducer/HealthVerifier`使用同一8KiB、nonce挑战、HMAC-SHA256规范化JSON合同。创建时间是Unix整数毫秒，PID与创建时间均来自受管登记和实际进程核验；不从QQ事件接受自报身份。固定字段在PLAN基础上加入`config_digest`及`listener_port`，绑定加载快照与监听归属；每个nonce最多3秒、一次使用，seq严格增加，健康按配置TTL15..30秒生效，mirror不超过该证明剩余有效期。生产端必须从真实私有pipe/login/armed/rx/outbound观测取值，不得把初始good当armed。

阶段4A的Python `RuntimeOwner`读取加载快照、唯一管理器registry、固定PID创建毫秒身份、exe路径和该Node进程的固定回环listener；build/policy首次验hash后文件身份/大小/时间变化即closed。monitor不写registry、不扫描或adopt进程、不恢复。`HealthMonitor`在gate应用startup绑定verifier、签名bind一次后按配置poll、每次accept/ready重新核验，cleanup撤销并关闭session；默认缺资格/秘密仍closed。

`control_plane.mjs`仅导出固定health/bind/drain/stop纯handler，不监听端口。控制命令与health/ACK分域，3秒有效、严格规范化JSON、单调seq和有界nonce去重；同owner lease的bind至多调用一次，未决重入拒绝，已成功bind可幂等ACK。`onBind(current)`必须在真实副作用前调用current，stop/drain会立即撤销该lease；失败/超时不允许重试注入。可信observe必须来自真实私有运行观测，不能拿handler自身状态冒充armed/outbound。

4A续作已实现`OwnerWriter`：原configuration_lock提供仅当前线程/作用域有效的lease，唯一管理writer从创建回调结果捕获PID+创建时间、写前置启动意图、验证exe/registry并冻结v2 owner记录与独立秘密引用。未取得创建身份时保留unknown意图，禁止另一provider继续启动。`snow_specs`只接受未来经核对的显式Node/私有入口路径，argv是本项目未来私有入口合同，**不是已知上游可运行包布局**；不搜索目录或推测启动器。

QQ/Node专用子进程环境大小写无关地清除继承的全部`SNOWLUMA_*`与`NODE_OPTIONS/NODE_PATH`，再强制`SNOWLUMA_HOOK_AUTOLOAD=0`、`SNOWLUMA_TELEMETRY=0`，无配置绕过。仅构造子进程副本，不改全局/HOME/APPDATA或既有framework/NapCat环境，不向该副本写独立控制key。

gate拥有单一monitor任务，`processes`只统计真实PID，任务是否运行另列`transport_monitor`布尔。gate和manage共同从原锁内原子预占持久控制seq，网络不持锁；seq文件缺失/损坏/回拨closed。gate抢启动锁失败会异步等待至配置ready timeout，仅重试未发出的bind，未知ACK不再注入。命令时间戳保守向下取100ms，实际有效期至多3秒，不扩大期限。

manage stop先置marker，在锁内冻结owner/预占drain-stop序列，释放锁后消费签名ACK，再重新锁定核对实例/registry并回收已证明身份。stop-only核验允许snapshot损坏，但仍检查冻结owner、实际PID/创建毫秒/exe和固定listener；该较弱路径不用于健康、bind或channel_ready。marker后的drain/stop可通行，bind始终关闭；ACK未知不重试，未知身份/未确认退出仍保留原有失败语义。

当前`require_runtime`仍明确总拒绝真实Snow启动（`private_runtime_entry_unavailable`），管理器在snapshot/状态/子进程创建前、gate在监听前检查，无配置开关或自填manifest绕过。真实私有入口/原生资格、listener挂接和armed/outbound观测仍未交付；`_wait_snow_owner`只确认身份/监听，不能代替armed/channel_ready。以下4B1虽补齐项目侧新epoch/预算，完整Snow生命周期及上游接线仍未真实验证。

4B1现补齐原创恢复接口及离线闭环：原gate monitor任务消费当前独立健康观测，`RecoverySupervisor`持久记录grace30/drain150/一次动作/ready期限和短断计数，`ManagementRecovery`在原锁下经OwnerWriter替换已确认退出的身份、换epoch及控制seq、重绑verifier；网络等待不持锁，不另开nonce消费者。旧WS代际、材料和输出票撤销，未决ACK保留阻断；模型/cleanup未知、活动发送/历史repair未收敛时不kill。

首次停机准备API为`RecoveryLedger.initialize(lease)`，供后续CLI调用，watch不会自动初始化。prepared哨兵、预算、事故与预占意图分开保存；缺失/坏账/回拨/写失败closed。失败/未知占用额度，watch或bot重启不再执行同一事故；QQ动作同时创建Node，故同时占Snow与QQ资源预算，24h Node最多2、QQ最多1，间隔至少1800秒。新Node可在本次ready期限内异步等待监听，只有尚未发出的bind可等待重试，ACK未知不重发。旧seq严格坏账不能借新epoch洗成0。生产仍因私有资格总拒；QQ另有固定3/3未证拒绝，配置true不放行，完整演练仅用测试依赖注入。

测试：`node --test adapters/snowluma/project_policy.test.mjs`。本机Node24.22.0仅执行这些原创无依赖测试，不满足Snow实际运行引擎，不作为其构建/运行通过证据。

4B2新增`scripts/transport.py`停机prepare/有限provider事务与rollback、离线verify及trial入口。生产资格仍无配置绕过；probe/activate/trial不执行真实QQ或私有入口。`transport_trial.py`仅由同一gate健康task调用，不增加PID/nonce消费者；原生观测与扫码变更信号仍需未来私有接线。发送统计来自实际gate转发/回执：RAM中至多128个关联时间，15秒无有效ACK或断线计unknown，不重试，不将echo/消息ID写进采样；control ACK指标另列。数据格式/边界见config/README，未证明真实长稳。
