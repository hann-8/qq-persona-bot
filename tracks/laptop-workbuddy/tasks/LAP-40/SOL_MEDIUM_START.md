# LAP-40：交给Sol medium的实施指令

返回[项目入口](../../../../PROGRESS.md) / [总交接](HANDOFF.md) / [A4详细规划](STAGE3_A4_PLAN.md) / [用户实测流程](WORKTREE_AND_USER_TEST_PLAN.md)。本文件由Sol max规划；**写下指令不代表当前已获实施授权**。请用户在新会话选择`gpt-6.1-sol / medium`后发送以下文字。

```text
现在实施LAP-40 A4，按已落盘详细规划执行；本次只做A4，不进入B/C。

唯一工作根：E:/CodexWS/QQbot_Snowluma
分支：codex/lap-40-snowluma

先读该根PROGRESS顶部和AGENTS，再读tracks/laptop-workbuddy/TASKS.md的LAP-40行、tasks/LAP-40/HANDOFF.md顶部、STAGE3_A4_PLAN.md及STAGE3_A4_HANDOFF.md。这里tasks/LAP-40均指tracks/laptop-workbuddy/tasks/LAP-40；只按缺口检索，不重读全部历史。

Sol max已完成详细规划；现在由本次用户指令授权你实施。不要自动派子代理，不自动换模型。旧C:/Users/yutha/.codex/worktrees/lap-40-snowluma-impl/QQbot只读保留；E:/CodexWS/QQbot是原NapCat运行根，不修改代码/配置/进程。

先核Git/远端/额度/文件归属，登记LAP-40 A4的新session、开始时间和涉及文件，写后重读。此前误自动派出的代理已interrupted，没有活跃写入归属；忽略区2901文本/27内部junction迁移已根审，另有未审a4-work 424文件、prepare-a4.py/build-a4.mjs和5个src/a4-*准备稿，没有a4-dist或A4执行证据。先审草稿与A3差异及基线摘要，保留历史，不直接运行现有prepare/build或把草稿当实现通过。

严格按STAGE3_A4_PLAN.md分步实现：全链非阻塞helper、短观测scope与持续操作许可分开、控制收到时起3秒总期限、close/stop取消在途helper、原始包有界早期准入、正式owner/PIDpipe、认证gate允许RPC、实际writeControl/Highway/native最后fresh栅栏和一次ACK。先交最小可审检查点，再完成计划矩阵；slow120ms合法bind必须成功且在3秒内，报告真实helper次数，不能以拒绝及时代替成功。

只允许合成native/process/server/FS/network；不加载native、不真实监听、安装QQ、启停/登录/扫码、模型调用、群消息或SSH，不改local/persona，不复制/搬运/链接官方原生包或整套运行态。Node和原E venv只可原位置只读借用，cwd/PYTHONPATH指新根并禁pyc；生产资格始终closed。本次不实施B/C或正常启动，不要求用户现在扫码。

public只提交原创代码/自造测试/文档；上游修改源、patch、bundle和依赖只在忽略private。修改PROGRESS、工作线HANDOFF、TASKS和本任务交接/原创报告时只更新本任务归属，保留其他差异。确需public控制合同内修复先登记路径，改变方案的能力缺口回Sol max；普通已规划细节自行处理。

每个可审检查点更新交接，按长期授权检查归属/diff/适用验证后commit/push并核远端SHA。5小时余<=5%立即保存检查点并停止新实现/测试，不reset credits、不建automation。完成A4后报告实际已实现/离线已过/未过/未验证及下一步，停在交给Sol max复核，不自动推进下一阶段。
```

A4完成后由用户决定是否交Sol max复核；B实施和真实试用再另给指令。真实可启动阶段才给用户实测，性能/长稳与后续Sol high调试按实际结果推进。
