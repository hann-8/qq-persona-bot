# LAP-40 阶段4A独立剩余续作

返回[40交接](../tracks/laptop-workbuddy/tasks/LAP-40/HANDOFF.md)。session `LAP-40-medium-stage4A-continuation`，基线`052f0161473e926fb9ec7813ae6319d31af0ae72`。原[部分检查点](lap-40-stage4A-2026-10-24.md)作为历史保留；本轮只补4A独立剩余，待根审，不开始4B。

## 实现与调用证据

1. `configuration_lock`现在yield仅当前线程/作用域有效的lease，旧调用方忽略返回值继续兼容。`transport_launch.OwnerWriter`要求该lease并核对加载实例/stop marker，从创建回调Popen结果获取PID及创建时间，不接受PID输入、不adopt进程。创建前先写启动意图，获取身份失败保留unknown；缺证据时不声称停净、不允许启动另一provider。registry与runtime owner只由持原锁的管理器写，watch不写registry。
2. `snow_specs`由显式`PrivateLayout`与加载snapshot/proof构造固定QQ/Node argv，路径须在runtime、入口与proof build_file相同，独立密钥不进argv/env。它是未来本项目私有入口的固定CLI合同，**不是已获得包的运行布局**；没有目录搜索或猜测上游启动器。QQ/Node原始stdout/stderr直接丢弃，不留原始日志。
3. `manage._start_channel`在原资格检查后连接`_start_snow_channel`，后者实际调用spec→writer.create→writer.register→身份/监听等待→既有framework spec，出错撤销并清理已登记身份。测试仅patch资格函数返回原创假路径、fake进程/端口/framework边界，运行真实管理入口和writer。生产`require_runtime`仍总拒绝，未引入manifest布尔或配置开关；写snapshot/启动状态/创建组件前拒绝的测试仍通过。
4. `_wait_snow_owner`仅证明身份/监听，不等于armed或channel_ready；实际gate仍要求独立新鲜签名证明、online/good、armed/rx/outbound。monitor是gate拥有的任务，状态分离为真实PID计数和封闭`transport_monitor.running`，无虚构watch PID。gate自身崩溃关闭准入，人工恢复边界保留。
5. gate与manage从同一原锁内write-ahead seq ledger分配控制seq，单调、安全整数、绑定实例/epoch；缺失/损坏/时钟回拨拒绝，不由消费方自动重置。网络前释放锁。gate抢锁失败为非阻塞异常并异步yield后再申请，仅重试尚未发送的bind，未知bind ACK不再次注入；等待遵循ready_timeout_seconds。初始writer初始化新实例seq，不宣称完成4B恢复epoch/预算。
6. `manage.stop_project`先marker、锁内冻结已加载owner/预占drain-stop seq，释放锁后真实调用控制客户端，重新取锁核对实例/registry后再执行已有安全回收。控制客户端只发送drain/stop，签名/固定回环/8KiB/3秒/ACK域校验；marker后允许drain/stop，禁止bind。snapshot损坏或磁盘provider/secret引用改变不影响使用冻结owner记录核验停止；较弱stop-only身份路径不能用于health/bind/准入。ACK未知不重试，缺密钥跳过控制，仍仅回收registry中已证明身份；权限未知、实例变化、未知创建均保留阻断。
7. `show_status`对Snow/unknown不再输出NapCat6099登录提示或密码回退资料；NapCat旧提示保留。控制命令时间戳保守向下取100ms，避免跨运行时毫秒精度导致未来命令；有效截止仍为该更早时刻+3000ms，不延长期限。

## 验证

cwd与PYTHONPATH均为隔离worktree；`PYTHONDONTWRITEBYTECODE=1`，只读借原venv解释器。所有配置、key、PID、进程、listener、创建/控制transport均自造；Node仅执行原创handler stdin/stdout，不启动server。0真实QQ/Snow/AstrBot/端口/模型/群/SSH/本机配置/persona/native操作。

- 最终Python组合128项通过：`test_transport_lifecycle`20、`test_transport_owner`16、`test_transport_health`20、`test_process_host`2、`test_config`14、`test_config_files`30、`test_qq_transport`15，另11项安全LifecycleTests。后者通过unittest loader选出该class全部方法，再排除会启动真实测试端口/子进程的`test_port_conflict_does_not_kill_owner`和`test_cleanup_discovers_late_child_and_leaves_external_process`，未运行这两项。
- 核心命令：`python -m unittest test_transport_lifecycle test_transport_owner test_transport_health test_process_host -q`为58通过；全组合用相同loader加其余3模块/安全LifecycleTests运行。
- `node --test adapters/snowluma/control_plane.test.mjs adapters/snowluma/project_policy.test.mjs`：9项通过。
- 真正跨客户端/跨语言证据：实际Python gate monitor签名bind(seq1)→新manage StopControl签名drain(seq2)→stop(seq3)，同一个真实原创JS handler验签/抗重放，Python验ACK，全部通过；随后原bind重放403。实际manage.stop入口另覆盖marker后drain/stop、损坏snapshot、改后磁盘provider、坏ACK不重试、安全fake PID回收、缺secret、权限未知和I/O期间实例变化。
- 非阻塞时序：持启动锁时运行gate任务，seq申请立即失败/yield，事件循环可继续且没有发送bind；释放锁后只发一次bind。未知ACK用例只发送一次并保留已预占seq。创建回调期间stop marker使writer不再注册/创建，未知意图保留。
- 旧schema1/2/3精确摘要/旧快照兼容回归通过；`git diff --check`通过。此前115项/67项中间回归不与最终128重复合算。

## 尚未验证及下一步

当前只完成4A已授权项目侧独立剩余的实现/离线验证，待根agent复核。阶段3缺口没有消失：原包/G0/G1、合格Node/专用QQ/原生数据、私有受保护入口/早期过滤/真实listener/armed/outbound接线、构建与执行级验证仍未交付；真实启动总拒绝。固定spec、合成创建或监听身份不应被称为上游适配/armed/免扫码/72h/7天通过。

4B尚未做：新epoch恢复与跨重启预算、恢复门控监督、prepare/activate/rollback/trial事务和有界采样。由根agent审4A后再派，不自动推进。根agent已知未提交PLAN/GUIDE调整不属于本轮文件，提交时保留不夹带；三共享入口未改。Git精确SHA/远端一致与最终配额在阶段出口回报。
