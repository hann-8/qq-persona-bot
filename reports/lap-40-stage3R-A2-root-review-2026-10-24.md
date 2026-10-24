# LAP-40 / A2根复核与续作入口

返回[项目入口](../PROGRESS.md) / [总交接](../tracks/laptop-workbuddy/tasks/LAP-40/HANDOFF.md) / [A2续作](../tracks/laptop-workbuddy/tasks/LAP-40/STAGE3_A2_CONTINUATION_HANDOFF.md)。2026-10-24，Asia/Shanghai；根`LAP-40-max-realentry-next`，重领基线b605d03。

用户17:24指令“继续”。已实际重查额度余99%，Git分支/HEAD/远端一致、工作区干净；未复用过期17:18预测或重建07:10 automation。根重新领取并写后重读TASKS。只在指定worktree工作，E运行态不动。

## 已重放与限制

根审读A2 formal loader、control服务壳、Hook源码准备脚本、竞态/正式快照测试和原创control handler。显式使用worktree cwd/PYTHONPATH、PYTHONDONTWRITEBYTECODE=1与原包Node；Python只读借E项目venv，无新依赖。

依次prepare-a2、build-a2、check-a2-inherited/hook/control/races、check-a2-formal、check-a2-checkpoint，17:29:29全部退出0：315模块；继承A1 61项、Hook10项、control20项、竞态2项、formal10项。原71/ZIP保持一致。以上仅重现既有组件检查点，未将组合计数当真实/完整A2通过。

## 必修发现：异步bind过期仍有效

对当前公开原创createControlHandler进行额外只读合成复现：签名bind issued_ms=1000/expires_ms=4000；onBind等待；fake时钟推进4001后恢复回调。实际结果为`current()=true / response.status=200 / bound=true`，真实副作用0。原103项未覆盖此分支。

代码原因：初始验3秒，但await后的current只核owner/generation/stop/drain，不含期限；A2 HTTP壳timer拒绝响应也未撤销handler中的许可。迟到请求body同样必须在handler前截断，close/aborted/error不能让已过期或撤销的请求继续驱动bind。该缺口须修复后才接受此控制组件，不把原测试通过改写成完整审阅通过。

这是原3秒/单次/stop优先合同内的修复，不改wire字段/默认值/账号/模型。实现派给sol/medium，公开原创文件仅control_plane.mjs及对应test；上游私有接线继续仅runtime忽略区。要求回归延迟bind、HTTP超时后迟到body、close/aborted、stop竞态及原handler合同，expired未知不重试、不回滚成可重绑。

## 后续

先修期限与取消，再继续A2 Node正式快照消费/整体装配、单PID创建时间及目标pipe提供器、受认证gate允许动作、最终lease/epoch/native栅栏和一次ACK。现有load_formal本身尚非完整Node入口；合法动作不能永久all-closed。平台/上游真实能力缺口精确记录，但不把尚未写代码当用户缺包。

B仍仅规划，C真实前置仍未证。0原生加载/QQ/Snow/真实监听/模型/群/SSH/local/persona/原运行配置动作。根不直接改实施代码，不覆盖其他session；后续实施归属/提交见续作交接。

## 期限修复根审（17:44）

medium检查点9162d2cc823ff74dd3c7701e17d0040f9592af31已提交/推送。根审实际diff及HTTP壳：命令请求current在期限/取消/完成后失效，ownerLease只在成功绑定后生效且独立于3秒；超时/abort/error/异常close及service.close不可逆取消，迟到body不再进入handler；wire字段不变。

根实际重跑公开+private取消Node20项、既有control20/竞态2、Python owner16/lifecycle20，全部退出0（17:44:47）。这些验证含无监听跨语言wire与持久seq，停机文字来自临时合成fixture。本缺陷修复可接受，组件复核不代表A2总体通过。

按原归属续派同一medium补Node装配/单PIDpipe/认证gate允许动作/最终栅栏ACK。成功控制请求的持续lease与请求期限不得混用；停止时控制面身份核验可沿用原stop-only合同完成ACK，不能因为数据准入已关闭就误丢合法stop ACK，也不能把stop-only核验用于bind/发送。

## 既有群发送提交合同核对

medium指出gate剥离output_ticket后私有端无法重核实时group silence generation。根核LAP-35 PLAN第84/102行、对应指引第41/66行及onebot_gate._outgoing实际源码：群锁内最终校验，以有界下游socket write提交为线性化界，不等QQ ACK；在途不能撤回、可以晚到。故不新增gate许可接口，不透传内部票。

A2仍严格在native前查transport lease/epoch/身份/健康、来源socket和冻结参数。群停言提交栅栏由gate执行，已提交在途不宣称可追溯撤销；transport停止或换代则取消未提交native的旧回调。这是原合同解释，未扩业务/触发/允许动作，也不假造已有wire未携带的实时票。完整接线测试需覆盖上述不同边界。

## 同步helper的集成阻断

根读当前a3-channel.mjs/a3-runtime.mjs确认：每个identity/stop_identity/gate/stopping查询均spawnSync短Python进程，无缓存；ownerCurrent、ownerLease、observation及permission.current多层重复调用，单次2秒上限不等于一次health/发送的总2秒。control receive甚至先执行同步live再创建3秒timer。现有零延迟fake不能证明3秒响应性和高频入站能力，尚不接受该生产路线。

已要求medium以私有非阻塞有界短helper/一次请求或包的已验证原子scope复用及敏感边界新鲜复核收敛；保持无常驻watch/无第二registry writer，不扩大既有deadline或删除校验。每scope绑定owner/epoch/pipe/socket，停止和失效不可因后续快照恢复；控制总3秒含前置校验，需慢helper及高频回调集成证据。同步helper自报PID+created/parent并与创建句柄PID及正常exit互证属于本机实现证据，Node异常退出后的真实完整覆盖仍未证，不替代31B/C。

medium在此发现前已跑的316模块/允许动作/延迟native/实际框架unknown等合成仅是分项结果；新的异步方案未整体接线前不能据旧零延迟计数称A2完整通过。B审核还须纳入Python helper/解释器及安全相关依赖与子进程归属，不仅hash JS入口。

## 阈值交接

medium057441e已交付：最终29项零延迟基线940次helper；120ms慢helper bind51次、6077ms后403，明确未通过3秒响应性。A3分项及实际框架unknown子测通过，详见续作报告；根尚未逐项重放A3。非阻塞`a4-scoped-broker.mjs`5项仅候选，根只读源、未运行新测试/未接受，更未整合进真实固定链。

18:37根重查额度used96%/余4%，按用户约定仅保存交接/Git，停止新实现/测试，不续派大块、不自动唤醒/重置。当前ROOT source4项与QQ静态核验报告归根，将单独提交，medium已释放private。下一次先核额度/归属再审候选，重点区分短原子证明过期与持续逻辑许可；全链慢helper、取消/代际、原始包有界准入及ACK闭环仍需完成，所有真实资格继续拒绝。
