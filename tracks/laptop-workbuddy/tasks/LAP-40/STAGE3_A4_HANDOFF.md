# LAP-40 A4：已实现 / 合成验证通过 / 待Sol max复核

返回[项目入口](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [总交接](HANDOFF.md) / [A4详细规划](STAGE3_A4_PLAN.md) / [实施报告](../../../../reports/lap-40-A4-implementation-2026-10-24.md) / [Sol max复核入口](SOL_MAX_REVIEW_START.md)。继承AGENTS；2026-10-24 23:34，Asia/Shanghai。

## 当前状态与归属

用户本次明确授权按SOL_MEDIUM_START完整指令实施A4。session `LAP-40-A4-medium-implementation` 于23:03:15领取并写后重读，本次代码/验证/报告已交付，释放实施写入归属，下一步仅Sol max独立复核，不自动B/C。无子代理、无自动模型切换。模型/档位由用户会话设置决定，未伪称检测或切换。

唯一活动根 E:/CodexWS/QQbot_Snowluma，codex/lap-40-snowluma；起点74b3c77，检查点b5b0bc4/806c981均已push核SHA。最终Git号见交付消息/本分支日志；public仅原创文档。本地忽略private是复核所需材料，禁止归档清理导致丢失。

## 已完成

- 先核Git/远端/额度/归属；核2901迁移文本与27 junction不变。保留早期424文件+7准备稿于a4-draft-archive后审查，未直接跑旧prepare/build。
- 新异步channel初始化/封闭正式投影、受限helper；ALS持续逻辑许可与100ms scope分开，helper并发1/最多2秒/16条元数据。取消撤销等待并只kill自身handle；未知退出封闭且不再spawn。异步转换retained直到完成，超时/close有界。
- 新control壳从收到请求起3秒，包含body、排队、fresh、原handler和ACK；原wire/HMAC/seq/nonce/ownerLease不变。bind取消同步quiesce，stop-only身份不能发数据；正常stop ACK可完成。
- 实际HookManager/HookSession、正式owner/单PID pipe、受认证gate固定RPC装配。原包队列16条/256KiB/单包64KiB，计入既有2MiB，清除准入前正文复制；纯投影/黑名单先于转换/历史/store/logger，断连/登录代际清队列/许可。
- 实际inject/pipe connect/writeControl最终socket.write、Highway connect/write前fresh后同turn复核；冻结目标/socket/参数，scope过期可在仍有效逻辑操作中刷新；stop/epoch失效不可恢复。最终原生提交一次，ACK一次，unknown不重发。

## 最终验证（全为合成I/O）

`runtime/snowluma-private/check-a4-final.py`：21命令全部通过。316模块构建、321 ESM纯语法；channel/control15项；15运行场景，大多各30项，load/load-slow各34、pipe-connect31（重复基例不累加）；正式Python provider10类；实际gate/CQHTTP/AstrBot Event.send/TaskStore/Router/MemoryStore四种ACK13项；public control/policy14项。生产入口退出1，A4_PRODUCTION_QUALIFICATION_REQUIRED。

慢helper120ms：bind1336ms、窗口内12次helper（含并行gate/owner），HTTP health121ms/1次；load-slow压力中health238ms，原包峰值16/262144字节，第17RPC拒绝。put-slow的150ms写回调跨scope，2次Highway write和最终消息成功；中途撤销无后续body/消息。队列scope过期仍合法fresh成功，旧代际/stop/socket/账号/断连/pipe socket替换均阻断。实际注入函数配fake addon仅1次，实际connectSocket精确PID pipe仅1次。

原2901/27/官方71/ZIP全部摘要不变，旧C工作根和原E运行根Git干净。private原件及源/产物闭包摘要见a4-integrity-evidence.json；424源中13个overlay，sourceSet f86489260a2f5d43eae9790e03909152ee353d3db2ae1d6b7833d0e4a24c9888；产物集合fe5cea20d9a1a8709ae7079cd7fa362324e52a10581c0fd34603f5493e7249e1。详细命令、依赖锁、逐helper边界、各场景次数见实施报告/忽略证据。

## 下一步和未验证

交[Sol max复核入口](SOL_MAX_REVIEW_START.md)审查；本轮尚无max接受结论。优先看取消/未知退出、持续ownerLease、早期队列预算与不可逆代际、最后提交点/一次ACK。重建仅用prepare-a4-reviewed.py（--check只读；--prepare拒绝覆盖现存树）与build-a4；旧prepare-a4.py/finish-a4.py/make-a4-check.py仅过程历史，不再运行。

无真实native/监听/安装/部署/QQ/Snow启停/扫码/模型/群消息/SSH，local/persona不改，生产qualification/require_runtime仍closed。A2整体未获max接受；B资格代码/G1 Windows机制、原生保护/完整退出/真实pipe/数据范围/真实收发与性能、72h/7天仍未验。旧18/24/28/29/31B和23393字节人设预算失败保留。基本运行前提通过后才交用户试用，本次不要求扫码、不自动B/C。
