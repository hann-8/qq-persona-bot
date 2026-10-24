# LAP-40 / A2续作：命令期限与请求取消检查点

返回[项目入口](../PROGRESS.md) / [续作交接](../tracks/laptop-workbuddy/tasks/LAP-40/STAGE3_A2_CONTINUATION_HANDOFF.md) / [根复核](lap-40-stage3R-A2-root-review-2026-10-24.md)。2026-10-24，Asia/Shanghai。session `LAP-40-medium-stage3R-A2-continuation`，基线e5b1e3a92729680ddb48019d038331a1ee057f84。仅在指定worktree/分支实施，本检查点待根审，未继续整体接线。

## 修复

根复现的bind等待越过签名3秒期限仍current/200/bound已修复：签名字段、HMAC分域、nonce/sequence均保持；handler在await后及调用方每次提交检查时同时验证期限、请求存活、owner及generation。恰好到expires_ms也拒绝；一旦观察到过期、时钟回退或取消，当前命令不可复活。失败的已开始bind保持未知/不可自动重绑。

请求存活由内部`handle(request, {requestCurrent})`传入，不从JSON读取；带同名JSON字段仍拒绝。单次`onBind(commandCurrent, ownerLease)`两个回调明确分离：commandCurrent在请求取消/完成/过期后无效，ownerLease仅成功bound后有效，持续依赖owner/generation/stop/drain，未设3秒自动失效。drain/stop保持安全状态，即使延迟导致ACK过期也不回滚；stop仍撤销等待bind。

忽略private中的HTTP壳将timeout、abort/error、异常request/response close以及service.close统一为不可逆取消；取消清timer/缓冲并阻止迟到data/end调用handler。已完整接收的正常request close不误撤销等待操作。壳在到达起3秒截止与签名期限中取更严条件，实际timer尚未调度时也按时钟拒绝。服务仍只接受显式factory，测试没有真实监听。

## 验证

使用原包Node v24.22.1，在`C:/Users/yutha/.codex/worktrees/lap-40-snowluma-impl/QQbot`执行：

- `runtime/snowluma/v2.1.1/node.exe --test adapters/snowluma/control_plane.test.mjs runtime/snowluma-private/check-a2-cancellation.test.mjs`：20项通过，公开8项/私有fake-server12项。含根原复现4001、精确4000边界、await后检查、过期不可复活、取消不可伪造、持续owner lease、六种等待中取消、三种迟到body、正常close、timer未触发及跨连接stop。
- 既有`check-a2-control.mjs`20项、`check-a2-races.mjs`2项重放通过，全部退出0。
- 原项目venv只读借用，worktree cwd/PYTHONPATH及PYTHONDONTWRITEBYTECODE=1：`python -m unittest discover -s tests -p test_transport_owner.py`16项、`test_transport_lifecycle.py`20项通过，含Python/JS控制wire互操作及跨客户端持久sequence。测试输出的停机文字来自合成管理fixture，无真实进程停机。
- `python runtime/snowluma-private/check-a2-checkpoint.py`继续核原71文件/ZIP与A1一致、private无native；它保留的103是既有组件证据计数，本轮未宣称重新执行所有103。新增代码/测试摘要在忽略`a2-cancellation-checkpoint.json`。

公开仅修改原创control_plane.mjs及test和本任务文档；上游修改源/产物仍仅在忽略private。未新增依赖，未改原A1源/构建、require_runtime、local/persona或原E运行状态；0真实native/QQ/Snow/端口/登录/模型/群/SSH。

## 待续

本检查点仅修期限/取消，尚待根审。Node正式快照/owner消费、Hook/control整体装配、实际单PID创建时间与目标pipe提供器、同一受认证gate连接的允许RPC、最终lease/epoch/native提交栅栏和一次ACK仍未实现；这是代码剩余工作，不归为用户缺材料。B/C及Windows原生数据机制/生产资格/真实probe/72h/7天未通过，不自动推进。
