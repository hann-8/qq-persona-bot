# LAP-40 / A2续作：期限修复与完整接线

返回[项目入口](../../../../PROGRESS.md) / [总交接](HANDOFF.md) / [A2既有交接](STAGE3_A2_HANDOFF.md) / [续作计划](STAGE3_CONTINUATION_PLAN.md) / [根复核](../../../../reports/lap-40-stage3R-A2-root-review-2026-10-24.md) / [TASKS](../../TASKS.md)。2026-10-24，Asia/Shanghai。

实际根仍`C:/Users/yutha/.codex/worktrees/lap-40-snowluma-impl/QQbot`、分支codex/lap-40-snowluma-impl，17:24重领基线b605d03；本交接提交后以Git当前HEAD为准。E运行态保持不动。根已重放既有A2组件315模块/61继承/10 Hook/20 control/2竞态/10 formal，生产仍closed；根另复现bind等待越过3秒仍current/200，尚未修。

执行session `LAP-40-medium-stage3R-A2-continuation`。medium独占private根、本交接、待建reports/lap-40-stage3R-A2-continuation-2026-10-24.md，以及**公开原创**adapters/snowluma/control_plane.mjs与control_plane.test.mjs。根独占共享3入口/40总交接/规划和根复核报告。其他public文件若确需改，先报路径与理由供根登记，不直接扩大。

1. 先修根复核的3秒/撤销问题：current须在await后和实际副作用前仍满足当前请求期限/存活、owner/generation/stop；HTTP timeout/abort/error/close撤销是不可逆的，迟到body不能再调用handler/副作用。HTTP壳不能仅拒绝响应却留下有效许可。停机/未知不得通过重试bind恢复；drain/stop继续优先，不能因改期限破坏合法快速ACK。保持现有签名wire字段/分域/seq/nonce及默认值，新增能力只能是内部不可由request JSON伪造的请求存活合同。用fake clock/server回归，避免真实等待多分钟或真实端口。
2. 接既有A2交接六项剩余合同：Node正式快照/owner消费、控制与Hook总体装配、实际单PID创建时间与目标pipe提供器、同一受认证gate连接的原允许动作、native提交前lease/epoch/身份健康栅栏及一次ACK。单PID提供器须按登记PID+created+exe再验，不枚举日常QQ/读账号库/猜数据路径；只能实现代码+fake测试，不实测真实pipe。没有可信提供器保持closed。
3. loader应复用现有Python正式验证或严格等价解析，Node消费的投影/秘密只能走当前受管身份的限定通道与固定结构，不向普通CLI/log打印；不能用任意JSON accepted=true或A0 synthetic fixture当生产身份。模块导入、未资格/未绑定前禁止构造真实native/server。生产require_runtime继续总拒，A2不得实施B或新增配置绕过。
4. 允许动作按原onebot_gate及续作计划的阶段补充，不恢复普通APIHub/历史/磁盘store/RKey自动刷新。文字/受控表情与元数据路径分别审计；成员/收藏/视觉旧资格保留，不支持的真实上游能力明确unsupported，不能造成功。只用实际固定上游代码+合成native/client/FS/network，最终提交前再验当前许可；unknown/partial不重发。需要改变方案的能力缺口先记录回根，其他独立部分继续完成。

保留A0/A1/A2既有复现路径，用独立overlay；固定源f8cb15c，实际protobuf转换/许可/原位置native与保护保留。禁止clone/native下载/复制/搬运/加载、普通core build/生命周期、真实QQ/Snow启停注入/监听/登录/模型/群/SSH/local/persona/旧运行目录操作。所有上游修改源/patch/bundle只在忽略private，不进public。

开工核Git/TASKS/额度，更新本交接领取并重读；不编辑共享根文档。解释器可只读借E:/CodexWS/QQbot/.venv/Scripts/python.exe，cwd/PYTHONPATH仍本worktree，PYTHONDONTWRITEBYTECODE=1。额度用户阈值仍<=5%立即落可恢复检查点、停止新实现/测试，不reset credits/重建旧automation；按领取/约15分钟/自然里程碑/提交核对，接近阈值加密。

本任务每个实际里程碑及时写本交接。先交可审的小检查点（期限修复）供根审，再继续较大接线；允许同一A2任务串行推进，禁止并行写private。仅提交自己归属的原创代码/test/报告/本交接，不夹带根未提交文件；push核对远端，给可复现命令/原件不变/差额，等根审不自动B/C。

当前：2026-10-24 17:36 session `LAP-40-medium-stage3R-A2-continuation`已领取；基线e5b1e3a92729680ddb48019d038331a1ee057f84，Git干净，额度used12%/余88%。先修单次请求期限/不可逆撤销并新增fake clock/server回归，保持持续owner lease独立；本小检查点交付根审后再继续整体接线。


## 期限/取消小检查点（2026-10-24 17:41）

已修公开原创handler单次期限/内部请求撤销与await后检查，签名wire不变；commandCurrent与成功后的持续ownerLease分开。private壳统一timeout/abort/error/异常close/service.close，不允许late body/end执行；正常完整request close保留操作。独立fake timers/server执行，无真实端口。

验证：公开8+private12=20项JS通过，旧control20/races2通过，Python owner16/lifecycle20通过；原71/ZIP与A1一致、private无native。旧103 helper仅核原件/既有证据，本次不称完整103重跑。文件/命令与缺项见[续作报告](../../../../reports/lap-40-stage3R-A2-continuation-2026-10-24.md)，摘要在忽略`a2-cancellation-checkpoint.json`。

本次修改仅public control_plane.mjs/test、本交接/报告和private src/a2-control.mjs、新check-a2-cancellation.test.mjs/摘要。停止于可审小检查点等根审；不继续Node消费/整体装配/PIDpipe/RPC/最终栅栏ACK，不实施B/C。原运行状态未动，生产总拒。领取used12%，检查点used17%，剩余阈值仍按用户<=5%。
