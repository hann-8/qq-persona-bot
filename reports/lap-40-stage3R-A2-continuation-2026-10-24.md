# LAP-40 / A2续作：命令期限与请求取消检查点

返回[项目入口](../PROGRESS.md) / [续作交接](../tracks/laptop-workbuddy/tasks/LAP-40/STAGE3_A2_CONTINUATION_HANDOFF.md) / [根复核](lap-40-stage3R-A2-root-review-2026-10-24.md)。2026-10-24，Asia/Shanghai。session `LAP-40-medium-stage3R-A2-continuation`，基线e5b1e3a92729680ddb48019d038331a1ee057f84。仅在指定worktree/分支实施，期限修复检查点9162d2c已获根审；随后A3装配及A4异步候选见下，整体A2仍未接受。

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


## 后续A3装配与A4异步候选（2026-10-24 18:34）

**A2仍未完成。A3同步helper热路径存在已复现阻断，A4尚未替换它；以下合成通过不能当3秒响应性或完整运输通过。** 用户前次额度停工已由17:24“继续”撤销；本次自然检查点前额度used92%/余8%，保留<=5%停止阈值。

独立private `a3-work/a3-dist`构建316模块，未覆盖A0/A1/A2。正式Node入口消费固定结构的Python loader投影及控制/反向WS独立秘密，限定继承管道、实际父Node PID/created/exe核验，CLI总拒；没有JSON true晋升生产。新增实际单PID/目标pipe提供器：复用RuntimeOwner registry/PID/created/exe，Windows只查两个固定mojo目标pipe、前后核身份，无全局枚举/账号库/猜数据路径；WaitNamedPipeW只证明定名pipe可用，真实pipe服务器/保护及数据归属仍待受控资格验证。

Hook/control/唯一反向WS已接到真实固定源：真实心跳armed分源；同一验证过的当前gate socket、owner lease/epoch/身份/健康与冻结最终参数绑定每次动作。文字/群别名用实际MessageApi，授权群metadata与self资料/成员用固定官方类/服务，favorites仅固定gate管理echo；全成员material仍MEMBERS_CAPABILITY_UNVERIFIED，self成员单页找不到返回不可用，不伪造完整名册。控制stop-only身份与bind/send强身份分开，marker后合法stop ACK仍可返回。

受控图片只从现有启用catalog/library或既有delivery快照精确URI/hash读取，Python验证图片后经有界管道给Node RAM；任意URL/path/base64请求不准入。实际官方NTV2 fast路径及字节PUT路径已用fake客户端/网络执行，QqHookClient控制写队列、Highway connect/write前均有最终transport栅栏；只保留一次尝试，未知不重发。群停言遵循原gate有界WS写线性化，不承诺撤回gate已提交后发生的新群停言；transport stop/换代继续在native前撤销。

最终`check-a3-final.py`退出0，详情/摘要在忽略`a3-final-evidence.json`：

- 七个整体场景stop/epoch/socket/account/disconnect/put/put-fence分别29项通过，多数重复基线，不能合称203个独立合同。含实际入站projection/parser/converter/forward及黑名单/越群先拒，原APIHub/store/logger/RKey/backfill计数0。
- channel/argv/子进程退出身份11项，Provider10项，catalog/隔离6项通过；后者还实际执行-I/-B helper负例，stdout/stderr空且exit1，普通CLI不能dump秘密。
- 实际gate→已安装CQHTTP响应处理→原AstrBot Event.send→EventReceiptProxy/ReplyDelivery/TaskStore→history repair与QQRouter.close_memory/MemoryStore.close，10项通过。`status=ok,retcode=1500,data=null`是当前wire的unknown映射，不是成功；无sent/助手历史/记忆晋升，pending收束，重复delivery不重发。已知native前拒绝与成功有符号MID另验。
- 原71文件/ZIP与A1一致、private无native；0真实QQ/Snow/native/端口/模型/群/SSH，旧E/local/persona不动。

复现：原包Node执行`check-a3-runtime.mjs <场景>`、`--test check-a3-channel.test.mjs check-a4-scoped.test.mjs`；venv只读借用执行`check-a3-provider.py`、`check-a3-meme-isolation.py`、`check-a3-framework-ack.py`，均在private根；统一用`python runtime/snowluma-private/check-a3-final.py`。所有路径相对本报告开头指定worktree，原包Node/借用venv绝对位置沿期限检查点。

### 已证实未解决：同步helper与创建/退出覆盖

A3同步短helper不是常驻/watch，但多层同步检查重复创建：最终29项零延迟基线940次helper（此前27项884次）；120ms慢helper的bind发生51次，实际6077ms后403。总响应明显不是2秒，也未满足3秒控制合同，不能据零延迟fake宣布可用。Node异常退出后helper完整归属/退出覆盖未证，不把自报JSON或正常exit0等同31B完整覆盖。

A3当前每次spawnSync并发1、2秒/16KiB（登记图片12MiB）、无数据缓存；固定root/.venv解释器、-I/-B/固定root.src，大小写清除所有PYTHON*/SNOWLUMA*与Node预载。helper自捕获PID/创建毫秒/parent，Node绑定实际spawn返回PID和已等待退出；保留最近16条内存证据。任何创建/信号/超时/字段/代际未知永久closed，仍不能解决事件循环阻塞和异常退出覆盖。B必须冻结helper、解释器/pyvenv、全部Python安全依赖及进程归属，不只hash Node入口。

新`src/a4-scoped-broker.mjs`是**未集成候选**：异步短helper、单并发、同次总deadline至多2秒、仅operation的100ms原子scope、1000次scope回调不增helper、敏感commit再fresh、超时仅kill创建handle并unknown永久closed；无常驻watch或全局永久trusted cache。5项慢helper事件循环响应性/范围复用/超时/epoch/过期scope检查通过。它尚未替换A3 runtime/控制壳/原始包回调/pipe与注入/最终native链；因此当前A3仍被上述缺陷阻断，不能当已修。

下一步先根审本检查点，再完成A4异步scope完整接线及慢helper整体验证、原始包有界排队/取消、每个敏感边界fresh与期限后ACK收束；重放隐私/允许动作/框架unknown后才可能接受A2代码。真实原生数据/QQ/probe/G1/生产资格/长稳另待B/C，本轮不实施。
