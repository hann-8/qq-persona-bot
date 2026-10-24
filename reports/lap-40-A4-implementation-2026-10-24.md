# LAP-40 A4 实施与离线证据

返回[项目入口](../PROGRESS.md) / [A4交接](../tracks/laptop-workbuddy/tasks/LAP-40/STAGE3_A4_HANDOFF.md)。session `LAP-40-A4-medium-implementation`；唯一工作根 E:/CodexWS/QQbot_Snowluma。

## 检查点一：异步 helper 生命周期

2026-10-24，已领取并写后重读。HEAD/远端起点 74b3c777b78ab170ce21cf07aa94a3b80996a756，分支 codex/lap-40-snowluma；5小时额度剩73%。逐项核对迁移2901文本摘要和27 junction，零变化。原C工作根、原E运行根只读保留。

未审草稿确认为部分prepare输出：仍未接异步channel，且native/Highway等编辑未执行。原稿完整保存在忽略private/a4-draft-archive，未直接执行原prepare/build。

新增私有 src/a4-channel.mjs、check-a4-channel.test.mjs：异步初始化/封闭schema和实际spawn PID/parent/created核验，ALS逻辑许可与100ms短scope分开；并发1/队列16/每helper最多2秒且受操作deadline限制，控制优先；取消立即撤销等待并仅kill自身child handle，退出未知封闭broker且禁止再spawn。同步current只读scope，不递归helper；登记图像读取保留原12MiB/8MiB边界。

命令（cwd新根）：原C工作根 runtime/snowluma/v2.1.1/node.exe --test runtime/snowluma-private/check-a4-channel.test.mjs。8/8通过：120ms helper不阻塞、100ms过期后在持续许可内刷新、close在途取消/迟到、hang期限、并发/控制优先、假PID/epoch/超限/回拨。只用合成child，无真实spawn/监听/native/QQ/模型/群/SSH。

本检查点只证明上述组件；控制/入站/RPC/最终栅栏和完整A4矩阵尚待实施。production qualification仍closed，不进入B/C，不把旧A3分项计为A4通过。

## 检查点二：全链接线与定向执行

控制HTTP壳改为从收到请求计3秒（含body/排队/fresh/handler/ACK）；沿用public原HMAC/seq/nonce/ownerLease，未修改public业务代码。异步初始化仍由正式Python loader投影和独立秘密产生，生产入口继续拒绝。watcher/串行HookSession操作独立取得短scope；操作取消有同步清理钩子，事件pipeline异步转换纳入操作寿命。

原包在上游完整协议处理前进入16条/256KiB/单包64KiB队列，排队中项也计费。去除HookSession的准入前正文复制，队列仅保留一份固定快照；私有2MiB预算扣除队列256KiB和发送索引64KiB。断连/登录代际切换撤销旧队列及许可。受认证gate保留固定动作/16 pending；登记图像改异步读取。最终注入、精确PID pipe connect、实际writeControl取出队列、Highway connect/write均fresh后同turn复核；messageSubmitted只在实际socket.write前登记，成功/unknown ACK单次尝试。

阶段验证：实际316模块私有装配；慢120ms helper的合法bind约1.2秒成功，窗口内11次helper启动（包含并行gate工作），不是拒绝及时。实际类已覆盖允许入站、文字/群别名、授权群元数据、受限收藏、登记图像、unknown/前拒绝、stop/epoch/socket/account/disconnect、scope过期队列恢复与pipe socket替换。原包队列压力和RPC第17条拒绝通过；channel/control当前15项通过；实际gate/CQHTTP/AstrBot/TaskStore/Router/MemoryStore四种ACK结果13项通过，partial只保留确认前缀，未确认部分不晋升、不重发。

上述为中间定向结果；最终固定源码、慢图像/压力矩阵和完整摘要另见下节。曾发现慢图像fake响应早于读监听而丢帧，已使合成socket模拟真实缓冲顺序；不把该测试夹具现象当作真实QQ故障。原件/旧A0-A3与运行环境继续保留。
