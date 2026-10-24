# LAP-40 A4 实施与离线证据

返回[项目入口](../PROGRESS.md) / [A4交接](../tracks/laptop-workbuddy/tasks/LAP-40/STAGE3_A4_HANDOFF.md)。session `LAP-40-A4-medium-implementation`；唯一工作根 E:/CodexWS/QQbot_Snowluma。

## 检查点一：异步 helper 生命周期

2026-10-24，已领取并写后重读。HEAD/远端起点 74b3c777b78ab170ce21cf07aa94a3b80996a756，分支 codex/lap-40-snowluma；5小时额度剩73%。逐项核对迁移2901文本摘要和27 junction，零变化。原C工作根、原E运行根只读保留。

未审草稿确认为部分prepare输出：仍未接异步channel，且native/Highway等编辑未执行。原稿完整保存在忽略private/a4-draft-archive，未直接执行原prepare/build。

新增私有 src/a4-channel.mjs、check-a4-channel.test.mjs：异步初始化/封闭schema和实际spawn PID/parent/created核验，ALS逻辑许可与100ms短scope分开；并发1/队列16/每helper最多2秒且受操作deadline限制，控制优先；取消立即撤销等待并仅kill自身child handle，退出未知封闭broker且禁止再spawn。同步current只读scope，不递归helper；登记图像读取保留原12MiB/8MiB边界。

命令（cwd新根）：原C工作根 runtime/snowluma/v2.1.1/node.exe --test runtime/snowluma-private/check-a4-channel.test.mjs。8/8通过：120ms helper不阻塞、100ms过期后在持续许可内刷新、close在途取消/迟到、hang期限、并发/控制优先、假PID/epoch/超限/回拨。只用合成child，无真实spawn/监听/native/QQ/模型/群/SSH。

本检查点只证明上述组件；控制/入站/RPC/最终栅栏和完整A4矩阵尚待实施。production qualification仍closed，不进入B/C，不把旧A3分项计为A4通过。
