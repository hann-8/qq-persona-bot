# LAP-31 请求清理可靠性

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承AGENTS；合同为[LAP-26 PLAN第13节](../LAP-26/PLAN.md)与[SPEC第8—10节](../LAP-26/IMPLEMENTATION_SPEC.md)。

2026-10-18 18:16（Asia/Shanghai）领取；session `LAP-31-cleanup-reliability`，用户说明已选gpt-6.1-sol/medium，不自动检测/切换。开始main工作区干净，根agent独占实现与共享台账，无真实bot执行归属。

目标：31A分离原结果/清理状态、同一cleanup task取消/关闭接管、总deadline、逐项PID+创建身份、有界原子台账、零推理被动检查及脱敏诊断；31B仅在执行前容器归属及退出证明成立时交付完整恢复。legacy正常成功不强加容器门槛；历史job_complete重启不直接解锁。验收CLEAN-01—06及旧生命周期/ModelQueue回归，独立verify_lap31与reports/lap-31-*，不运行旧verify主程序。

归属：src/qqbot_gateway/workbuddy_cli_runner.py、cleanup_identity.py（新增）、model_gateway.py，scripts/process_host.py、manage.py、verify_lap31.py，tests/test_lap31.py，README.md、reports/lap-31-*、本HANDOFF、PROGRESS、工作线HANDOFF/TASKS。必要容器辅助仅本任务拥有。其他文件不改。

边界：不改本机忽略配置/凭据，不探活/启停/登录真实bot，不真实CLI/Ollama生成/QQ/群发；只替身及本任务自造受管进程，不按名称批量kill。保留Ollama未知解除及账号/模型/额度合同。不推进27—30。

当前检查点：2026-10-18 18:34（Asia/Shanghai），**31A已实现/离线通过，31B未完成**。起点main/`b7ccdcbdf64c1a1dd01ddcfc16c346e639564070`，开始工作区干净；当前差异全部属本任务。完整CLEAN映射见[报告](../../../../reports/lap-31-2026-10-18.md)。

已完成31A：原生成结果/清理结果/coverage分离；单cleanup task强持有与重复取消/关闭接管；kill、wait、process.wait及落盘共用总deadline；逐个PID+创建身份处理，AccessDenied不跳过其他对象，PID复用不操作；1未决/32摘要/128身份/32KiB每文件/2MiB模块的原子台账及超限前置；启动恢复未决，零推理/零kill的status/check与固定schema事件。正常legacy成功保留observed_only，故障后的观察空集合或历史job_complete文件不解锁。被动检查有5秒限频/2秒等待，独立命令不因默认executor退出等待而无界拖延；线程未返回仍保留阻断。

最终验证：`.venv/Scripts/python.exe -X utf8 scripts/verify_lap31.py`，退出0；283单元（新增23项，适用旧CLI/ModelQueue/lifecycle/process_host/Ollama未知等回归均通过），12组合384实际框架合成（两runner底层替身、真实run_agent/provider/原event及ACK）通过。[汇总JSON](../../../../reports/lap-31-offline.json)/[框架JSON](../../../../reports/lap-31-framework-offline.json)，控制台忽略路径state/lap31-final-console.log。初次直接用网关Python导入AstrBot失败，已改用既有框架Python子进程，未安装/修改依赖；收口后最终完整重跑通过。旧verify主程序未运行、旧报告没有覆盖。

31B：自造进程原生suspended→Assign→Resume、Job active归零及失败分支句柄回收有离线证据；Create/Assign/Resume三个注入失败分支通过。但强化正常/kill-on-close两个分支发现：Job未设breakaway flags时，子进程breakaway创建请求仍被接受。这不证明实际逃逸，也没有它仍属目标Job的创建身份匹配证据，禁止breakaway/完整覆盖门槛未过，JSON明确unverified_capability_gap。不能把只检查flags/一次active_count成功当成完整容器证明，不能归因Windows完全不支持。

生产CLIRunner仍为原asyncio创建/管道，未接入实验Job，不产出当前请求job_complete，也没有完整退出恢复器。31B生产创建/stdio适配、目标Job逐身份成员/嵌套breakaway核验及跨重启可靠退出证明均保留为未交付差额，回规划确定受支持路线；真实CLI隔离组合未获授权、未验证。31A独立交付不能标清理问题完整解决。

修改文件：src/qqbot_gateway/{workbuddy_cli_runner.py,cleanup_identity.py,model_gateway.py}，scripts/{process_host.py,manage.py,verify_lap31.py}，tests/test_lap31.py，README.md，reports/lap-31-{2026-10-18.md,offline.json,framework-offline.json}，本HANDOFF及PROGRESS/工作线HANDOFF/TASKS，共15文件。无用户/其他session修改夹带；忽略的本机配置/凭据/真实台账未读写，只有测试临时根与忽略控制台工件。

生效/回滚：没有新增公开配置或schema，不改默认cleanup_seconds=5/1..60。本轮没有部署/启停/探活/登录真实bot或真实模型/QQ/SSH调用；当前加载/运行状态未知。回旧代码前须确认cleanup task结束并保留未决身份，旧版不认识新台账则保持停机直到独立完整退出证明；不删unknown/marker、不切后端绕过。账号/额度/模型、Ollama未知解除、历史/ACK/pending及旧真人验收差额保留。

下一步：仅交付本任务已检查文件并核对origin/main完整SHA；31B缺口回规划，用户指定后续范围前不做真实CLI/模型/QQ验证、不自动开始27—30。Git交付不等于部署或完整验收。

Git交付检查点（2026-10-18 18:35，Asia/Shanghai）：内容提交`fc7fce70c079c8c21cee2ca31d6c040cb22b5593`已推送origin/main，`git rev-parse HEAD`与`git ls-remote origin refs/heads/main`完整SHA一致，内容检查点工作区干净。提交恰15份上述归属文件；283单元/384实际框架及229本地文档链接、围栏、JSON计数和暂存diff --check通过。没有旧报告或本机配置/凭据夹带；忽略的测试控制台/临时框架工件保留，真实运行状态未知。此段另作交付记录提交/推送，最终记录SHA见会话回执；31B缺口和真实验收差额不因Git交付消失。
