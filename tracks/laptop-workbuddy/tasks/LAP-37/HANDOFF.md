# LAP-37 清理容量故障修复与手动恢复

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承AGENTS。

状态：2026-10-22修复已实现、105项离线回归通过、停机现场人工恢复通过；bot保持停止。用户放弃开机自启，根自启入口已退役，项目Startup status/remove均not_installed。真实聊天/长期稳定/31B完整退出证明未验，旧差额保留。

session `LAP-37-cleanup-capacity-recovery`，21:20（Asia/Shanghai）登记领取，开始main工作区干净。用户指定sol high做debug/简单修复；本轮按最新指令修复既有清理合同并将LAP-33人工维护固化为显式脚本，不扩展自动恢复/触发范围。

## 原因与证据

- logs/model.log：2026-10-21 19:07:54 trace 15864d4165，19:08:04 generation=success/outcome=observed_empty/reason=capacity_exceeded/count=128；随后请求拒绝且没有新的CLI_START。不是模型生成失败或uv.lock依赖问题。
- 旧逻辑每次观察向列表追加身份，从不回收已经退出的条目，累计128后拒绝更多身份，持久unresolved使重启继续拒单。现场128条身份/121个PID，创建跨度8.364秒；本轮核验owner及128条均exited、四组件0、五端口关闭。
- 此为32/33同类未决台账持续阻断，但直接原因不同：32是ledger_error（初次OS操作未知），本次日志明确capacity_exceeded。后续observation_incomplete/identity_changed是被动检查结果，不能当作初次根因。历史证据不能还原128条当时是否同时存活，故不保证回收修复覆盖真实并发>128的情况。

## 完成与归属

- src/qqbot_gateway/cleanup_identity.py：满128时仅移除inspect实时确证exited的身份，保留alive/拒绝访问/复用未知；最多检查128条，清理deadline到期不再追加探测，真超限仍阻断。容量/schema/单次模型尝试和unknown合同不变。
- scripts/cleanup_recovery.py、scripts/manage.py、根清理模型阻断.cmd：显式cleanup recover，持配置锁，严格校验台账/路径、受管身份/owner/记录身份全部退出、6185/6199/6200/6099/8765全关闭，备份原字节/hash/人工说明，再核验状态和源字节后归档。没有kill、模型调用、重放、历史/ACK/unknown修改；任何核验失败保留活动记录。无未决时幂等not_needed。该动作是用户选择接受observed_only的人工维护，不是自动恢复或完整后代退出证明。
- tests/test_lap37.py新增10项：400短命假身份/未知不淘汰/deadline/完整备份及幂等/存活owner-child-managed拒绝/复用及权限/端口/二次核验/锁及坏记录/I/O/源文件变化；test_lap31旧容量用例改为明确模拟未知身份，避免依赖系统PID是否存在。
- 根开机启动机器人.cmd退役为提示；scripts/autostart.py历史实现保留，未再注册Startup。README/项目目录与日志说明、LAP-24交接及PROGRESS/工作线HANDOFF/TASKS同步弃用与恢复入口。.gitattributes仅为两个中文cmd指定CRLF，实测LF会破坏Windows批处理中文行，CRLF原生入口已通过。
- 未修改uv.lock、本机配置/人设/凭据。开始无其他未提交差异，本任务没有需要保留的用户工作区修改。本机运行/归档/测试日志继续忽略。

## 验证与现场恢复

- `.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_lap37.py -v`专项；最终聚合test_lap37/test_lap31/test_lap32/test_cli_runner/test_model_gateway/test_lifecycle/test_process_host/test_local_backend共105项、0失败/错误，详单仅本机state/lap37-regression.log。假runner含既有单次请求/清理/后续请求准入回归，不调用真实CLI/模型。
- 21:21:50实际运行`.venv/Scripts/python.exe -X utf8 scripts/manage.py cleanup recover`，归档到忽略的`state/cli-cleanup-manual-archive/LAP-37-20261022-212150-6d6d26af14/`，backup与archived原始字节相同，SHA256与manual-recovery记录一致。独立cleanup status返回blocked=false/observed_empty/observed_only/reasons=[]。
- manage.py status --json恢复前后均stopped、四组件0；任务计数completed=742/failed=57/send_unknown=1不变，配置摘要不变。0真实bot启停/登录/SSH/模型/群发。
- 实际`cmd.exe /d /c call 清理模型阻断.cmd --no-pause`返回not_needed、退出0；旧自启cmd仅输出退役提示、退出0，未启bot。Startup status/remove均not_installed，没有移除外部自启项。
- Git差异/暂存检查、本次Markdown本地链接检查在交付前完成；内容提交与远端核对见后续Git记录。

## 使用、回滚与剩余

现在可由用户双击根启动机器人.cmd。以后再遇相同提示：先关闭机器人.cmd，再清理模型阻断.cmd，成功后手动启动；拒绝时保留提示检查存活身份/端口，不直接删除台账。uv.lock只锁依赖，不用于进程恢复。

回滚须保持bot停止且无新unresolved，在配置锁内从归档原字节恢复原路径（会恢复阻断）；代码可回退本任务提交，两个cmd的CRLF按属性保留。归档证据不删除。不为恢复操作回滚数据库、历史、配置或unknown。31B完整覆盖/未观察后代退出证明、真实稳定/QQ群效果仍未验；本轮不再推进24自启验收，不自动启bot。
