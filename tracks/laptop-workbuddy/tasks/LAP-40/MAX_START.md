# LAP-40 新max session最小入口

返回[项目入口](../../../../PROGRESS.md) / [精简交接](HANDOFF.md) / [台账](../../TASKS.md)。2026-10-24 12:32，Asia/Shanghai。

用户请求新`gpt-6.1-sol / max`会话接续，避免旧聊天上下文。不要fork旧会话历史，不创建新worktree。

实际工作根为`C:/Users/yutha/.codex/worktrees/lap-40-snowluma-impl/QQbot`，分支`codex/lap-40-snowluma-impl`。QQbot项目默认目录`E:/CodexWS/QQbot`仅保留原运行态；即便新chat默认cwd在那里，所有实际操作也显式指定上述worktree。不要切原目录的代码。worktree的app附件仍属于原聊天，用户此次已请求接续其文件工作；无需重新attach，直接在工具参数指定workdir，勿归档旧附件。

读取顺序：

1. 本worktree的PROGRESS顶部当前入口与AGENTS。
2. 工作线HANDOFF顶部及TASKS的LAP-40行。
3. 本目录HANDOFF（已压缩；当前事实/已验/未验/下一步完整在此）。
4. 按具体缺口读取PLAN第3/4/9/14节、PRIVATE_WIRING_CHECKLIST和相应报告，不盲读全部历史/源码。

当前：独立项目集成代码/离线验证完成；真实Snow适配/探针/资格仍缺，未切换，72h/7天未开始。生产准入仍总拒；原运行态不动。新会话已领取，用户现已提供两包路径、接受EULA/PRIVACY并手工解压Snow；原包/解压摘要和自带Node v24.22.1通过。QQ安装/数据范围/扫码仍未完成，不能假定已准备。

首动作已完成：`LAP-40-max-realentry-next`于12:38接手；材料计划282527e/A0 871e3de/A1 add12af已交付，根重放315模块/61 A1/10路径/A0 21+5通过。下一步按[阶段3续作计划](STAGE3_CONTINUATION_PLAN.md)/[A2归属](STAGE3_A2_HANDOFF.md)推进，[B资格合同](STAGE3_QUALIFICATION_SPEC.md)仅规划。实际进度看HANDOFF；不重复材料索取。根独占共享3入口，实施代理按阶段独占代码，先根审再续派；旧根/medium不再写此worktree。

接续不是从零调研Snow，也不是立即运行activate/trial或补填proof。按精简HANDOFF的真实前置与阶段3续作路线推进；没有材料先给用户最小待办。
