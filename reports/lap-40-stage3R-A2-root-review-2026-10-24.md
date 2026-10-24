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
