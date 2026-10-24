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


## 根审后继续（2026-10-24 17:50）

根已接受9162d2c期限小检查点并交付6c2c432；本session继续同一A2剩余接线。重查used25%/余75%。独占归属不变；先实现private正式Python验证器→Node限定管道消费及单PID/目标pipe提供器，再Hook/control装配与gate动作。数据身份和stop-only分离；无生产资格/真实行为。


## A3装配可恢复检查点（2026-10-24 18:25）

独立`a3-work/a3-dist`316模块，保留A0/A1/A2路径；新增private a3-broker/channel/material/entry/native-factories/runtime/actions及对应检查。正式Python loader经当前Node父身份绑定的继承管道给Node固定结构/秘密，-I/-B/固定root.src与root/.venv解释器；env清全部Python/Snow/Node预载。单次短helper并发1、2秒/16KiB（登记meme12MiB）、无缓存，返回OS自捕获helper PID/created/parent并和spawnSync实际pid/退出核对，RAM仅最近16；异常不可再启动helper。无常驻/watch/registry写。Node异常退出下helper完整归属/退出覆盖仍未证，B须纳入helper与依赖闭包，不能称已受管。

已实际执行：Provider10项；Node通道/生命周期/argv11项；整体runtime七场景stop/epoch/socket/account/disconnect/put/put-fence各27项（大部分重复基线，非189个独立合同）。真实Hook/Onebot/WS、info、文字/alias、授权群metadata、self资料/成员、固定favorites、登记image NTV2 fast/实际TCP PUT fake链已执行；原QqHookClient控制写队列及Highway connect/write前最终transport栅栏，禁自动重试；stop marker后合法stop ACK保持通。图片PUT中途撤销零后续body写/零消息提交。

实际gate/CQHTTP/AstrBot Event.send→Proxy/Delivery/TaskStore→history repair与QQRouter/MemoryStore另10项通过：Node的ok+1500+null为unknown，不是已发送成功，无助手历史/记忆晋升；native前拒绝/成功分别核，pending收束，不重发。群停言以gate有界WS写线性化为准，Node不承诺撤回gate已提交后新停言；transport stop/换代仍在native前撤销。

组件代码仍待根审，本轮A2整体未宣称通过。正在收敛登记meme提供器和固定Python隔离检查、最终原件/构建摘要；当前额度used80%/余20%。真实pipe/原生保护/QQ/生产/B/C未执行；短helper异常退出覆盖及G1另待资格路线。


## 当前安全检查点（2026-10-24 18:34）

最终private `check-a3-final.py`退出0：316模块、七场景各29项（大部重复）、channel11/provider10/catalog隔离6/真实框架ACK-history-memory10，原71/ZIP不变、private无native。详见[续作报告](../../../../reports/lap-40-stage3R-A2-continuation-2026-10-24.md)新增A3/A4节；旧27项/884调用为早期，最终29项940调用。

**未解决阻断**：A3同步helper热路径，120ms慢helper bind共51次、6077ms后403；不能称3秒响应通过。新`src/a4-scoped-broker.mjs`异步operation scope候选5项通过但未接入A3，真实runtime/控制/入站包/注入/最终native仍须改造。当前A2整体未完成、待根审；不将此未写接线归为用户缺材料。短helper自捕获PID/created/parent+spawn退出证据已补，Node异常退出下完整归属仍未证；B需纳入helper/解释器及依赖闭包，生产总拒不变。

本轮只归属修改本交接和续作报告，所有A3/A4源码/产物/fixture/证据均在忽略private。根dirty（总HANDOFF、续作规划、根复核、QQ静态报告）保留不提交。先交此可审检查点；下一首项为A4全链异步scope及慢helper端到端测试，不开始B/C。最新额度used92%/余8%，<=5%立即停止新实现/测试。
