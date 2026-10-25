# QQ主线交接：SnowLuma与共用bot业务

返回[项目入口](../../PROGRESS.md) / [AGENTS](../../AGENTS.md) / [任务台账](TASKS.md)。2026-10-25，Asia/Shanghai。保留原目录名以兼容已有链接；此处今后以SnowLuma为主线。

## 当前状态

LAP-40官方接入与日常入口已实现/离线通过，用户已现场确认Snow可运行、QQ群可回复，最小文字首试成功。来源是用户说明，未据此认定停止/免扫码/其他功能/长稳完整验收。

LAP-41已完成新根整理：uv报告清除38,269缓存文件约626.1MiB、5份网页快照和退役提示cmd已删除，4份旧入口说明归档；少量字节码缓存因自动审批拒绝删除而保留。当前入口以Snow主线压缩整理，使用对照已交付。起点本地/远端3d3361ea、工作区原先干净，session `LAP-41-snow-mainline-cleanup-comparison`；25份保护文件摘要相同，未改生产代码/配置或启停bot。清单、限制和验证见[41 HANDOFF](tasks/LAP-41/HANDOFF.md)/[CLEANUP](tasks/LAP-41/CLEANUP.md)。

## 当前需要读的文件

- 日常使用：[SnowLuma使用说明](../../SnowLuma使用说明.md)。
- 旧NapCat用户：[实际bot使用对照](../../docs/BOT_USAGE_COMPARISON.md)。
- 接入/日常入口事实：[40 HANDOFF](tasks/LAP-40/HANDOFF.md)，按需要查其PLAN/桌面入口合同。
- 模型、聊天和功能配置：[config/README](../../config/README.md)，不输出本机配置原文或秘密。
- 原有所有任务及验收差额：[TASKS](TASKS.md)。其他任务仍保留，不自动展开。

## 主线合同

官方Snow只是QQ接入，gate/AstrBot/router/gateway/CodeBuddy仍承担共用bot业务。当前两个根的非秘密业务设置和persona内容相同；新根图库尚无登记，不会自动继承旧图库或聊天历史。

NapCat旧根和旧C根不修改/启停；保留本根仍被导入的NapCat兼容代码、旧任务/报告和A4代码/产物/证据。B/C停止，不再把旧私有资格/proof/probe/原生数据证明或长稳作为首试前置。模型/账号/额度、local/persona、群历史、登录和图库不因整理自动变化。

本次维护不改生产Python/插件，不新增功能，不启停/登录/模型/群/SSH，不派代理或切模型。只提交已检查的本任务文件；缓存与运行数据不提交。

## 历史接续

需要查历史时打开[整理前完整交接](../../docs/archive/pre-snow-mainline-2026-10-25/LAPTOP_HANDOFF.md)或具体任务，不重读所有历史。

- [LAP-39 NapCat故障观察](tasks/LAP-39/HANDOFF.md)：只作旧根历史，不能推断Snow当前故障。
- [LAP-38后续功能/独立微信规划](tasks/LAP-38/HANDOFF.md)：仅用户指定后推进，不自动启用。
- [LAP-37人工清理恢复](tasks/LAP-37/HANDOFF.md)：保留维护边界，不删除任务台账或依赖锁。
- [家庭5070备用路线](../local-5070/HANDOFF.md)：原有后端保留，未在本轮认证或调用。
