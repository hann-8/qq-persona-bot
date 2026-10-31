# LAP-45 本地工作区收敛与七天日志

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承根 AGENTS。

状态：本地清理已完成；日志补齐方案已规划，待用户后续 medium 实施。负责人：当前会话 Codex；session `LAP-45-local-worktrees-20261031`；开始时间：2026-10-31 12:57（Asia/Shanghai）。[七天日志方案](PLAN.md) / [后续实施指令](MEDIUM_START.md)。

## 目标与授权

用户明确 SnowLuma 已是 main 主线，其他本地 worktree 不再使用、不必保留，历史放 GitHub 即可；同时希望日志保留七天、过期自动删除。本次清理授权覆盖旧目录保留约定；仅操作本 QQ 仓库，WeChatbot 独立仓库保留。

## 起点与范围

- 工作根 `E:/CodexWS/QQbot_Snowluma`，main 与实时 GitHub main 同为 `bea429416142eeff7919689a03fb9246b80d2c02`。
- 共 9 个工作区，均无非忽略修改；保留 SnowLuma，删除其余 8 个。Git 公共目录目前位于旧根 `E:/CodexWS/QQbot/.git`，删除旧根前必须迁入 SnowLuma。
- 精确删除清单：`E:/CodexWS/QQbot`、`QQbot_LAP43`、`QQbot_LAP43_debug`、`QQbot_LAP43_native`、`QQbot_LAP44_impl`、`QQbot_LAP44_plan`（后五项均在 `E:/CodexWS/`）；`C:/Users/yutha/.codex/worktrees/lap-40-snowluma-impl/QQbot`、`C:/Users/yutha/.codex/worktrees/lap-43-stage-a/QQbot`。
- `QQbot_LAP44_impl/runtime` 为指向主线 runtime 的目录链接，必须只移除链接本身。所有递归删除先确认绝对目标和父目录，不跟随重解析点。
- 当前没有旧工作区可执行文件/命令行所属进程；Codex 自身有旧根 cwd，不终止这些进程。主线生产进程/配置/秘密/人设/会话/记忆/图库/运行环境不动。
- 本会话归属：本项目录、PROGRESS、工作线 HANDOFF/TASKS、AGENTS 的当前维护事实、项目目录与日志说明；忽略的 `state/lap45-cleanup/` 清单/校验/迁移回滚材料。只执行 Git 元数据迁移、远端历史保全、本地 worktree/本地历史分支清理。

## 顺序与验收

1. 确认所有本地分支提交可由 GitHub main 或历史分支找回；缺少远端分支时普通 push 保全，不覆盖较新的远端分支。
2. 保存主线配置/秘密/人设/记忆/图库等保护摘要及 Git 元数据恢复材料；复核实际路径和依赖。
3. 逐一移除 7 个旧 linked worktree；迁移公共 Git 元数据及当前 worktree 的 HEAD/index/config，验证后清理旧根。
4. 仅保留本地 main；远端历史分支不删除。检查 worktree list、分支、Git 连通性、工作区差异、保护摘要与项目零生成健康。
5. 记录回收字节/实际剩余，完成日志七天保留的详细方案；按项目约定待用户后续 medium 实施，不把规划写成已启用。
6. 审阅归属文档后 commit/push，核对本地与实时 origin/main 一致。

## 日志当前证据

`scripts/manage.py:514/666/784` 用 ab 模式持有固定日志；`scripts/process_host.py` 输出脱敏事件至 stdout。官方 Snow 的按日日志有原生七天保留，本机 `runtime/snowluma/v2.1.1/config/runtime.json` 的 logRetainDays 实际为 7，官方源码也有闭合日志过期清理。仅说明配置/源码，没有本轮观察跨七天实际删除。项目固定文件按 LastWriteTime 删除无法让持续追加文件中的旧内容过期，其补齐方案见 PLAN。官方初始密码仅 stdout，不能简单停掉控制台副本。

## 恢复和证据边界

工作区源码从 GitHub 对应 SHA 恢复；删除旧目录中的忽略运行数据属于本次清理，不能从 GitHub恢复。主线保护文件与运行态保留。Git 元数据迁移在新目录验证完成前保留原件；失败先恢复主线 .git 指针，不删除原公共目录。清理/Git检查不代表模型、QQ/微信回复或新日志功能真实验收。

## 实际结果与验证

- 8 个旧工作区文件已清除，移除文件逻辑大小 3,314,509,478 字节（3.087 GiB，包含随后迁到主线的原 Git 文件；不是物理可用空间差值）。旧 `E:/CodexWS/QQbot` 被 Codex 自身 cwd 句柄占用，仅留空目录，没有 .git/运行数据；未杀 Codex 或任何全局进程。两个 C 盘旧 worktree 的 checkout 均已删除，父目录各剩一个零字节 .codex-worktree-name；递归删除和进一步的仅删空标记/空目录操作均被自动审批拒绝（工具只返回 blocked by policy，未给更具体原因），因此保留这两个无源码/运行环境的目录壳，不再尝试删除。
- 本地 `git worktree list` 仅 `E:/CodexWS/QQbot_Snowluma [main]`；`git branch` 仅 main。公共 .git 已迁为本根实际目录，不再指向旧根；main HEAD/index/status 在迁移前后对应一致，Git connectivity fsck 通过。
- 16 个本地分支头逐项在实时 GitHub 核对；15 个非 main 本地分支已删除。6 个缺少同头远端记录已普通 push 保全：codex/lap-43-rollout、codex/lap43-native-web、codex/wx-akasha-all 及 codex/archive/20261031/{lap43-once-log,lap43-sdk-error-result,lap43-step-log}；未覆盖或删除原远端历史。其余 10 项远端同头。
- 先解除 `QQbot_LAP44_impl/runtime` 等重解析点本身，再用 Git 移除 linked worktree；旧根用同一 PowerShell 检查路径/解除 3 个链接后删除，不跨壳拼接或跟随链接。
- 22 个主线保护文件的 SHA256 在清理前后完全相同，包括 local、秘密、人设、图库/登记、Python 环境配置和 managed-processes 身份台账。未改业务代码、生产配置、运行环境、会话/记忆或启停 bot。
- 零生成实际健康：8765 alive=true/router_ready=true/current_error=null；6200 alive=true/channel_state=connected/channel_ready=true/online=true。
- 本机审计位于忽略的 `state/lap45-cleanup/`：before.json、github-preserved.json、linked-cleanup.txt、git-migration.json、old-root-result.json、deleted-local-branches.json、cleanup-result.json、final-verification.json 和本轮维护脚本；不提交任何忽略文件。8 份本任务文档的 260 个本地链接、代码围栏及 git diff --check 通过；仅文档/Git/文件维护，无业务代码测试或真实消息验收。

## 下一步与交付

日志项目机制尚未实现或启用；按 [PLAN](PLAN.md) 和 [MEDIUM_START](MEDIUM_START.md) 由用户后续选择 medium 实施。工作区清理不需要再做。真实七天运行/模型/QQ/微信消息效果均不是本轮验收。Git 文档交付：审阅、链接/diff 检查及 push 后远端 main 核对，最终提交号见会话回执。本会话交付后释放维护归属，WX-AKASHA-ALL 仍待用户实测。
