# LAP-09：配置基础、授权群和黑名单

返回[全局PROGRESS](../../../../PROGRESS.md) / [任务台账](../../TASKS.md) / [工作线HANDOFF](../../HANDOFF.md)。继承全局规则；合同为[UX_PLAN v1](../../UX_PLAN.md)第3、4节及U04—07。

状态：**已实现、离线通过；真实重启/群验收待完成，非完整验收通过。** 执行session：LAP-09配置准入实施；2026-10-16 22:54（Asia/Shanghai）领取，23:00交付检查点。用户授权仅实施此项，并补充允许自主commit/push。不伪称检测或切换会话模型档位。

## 范围与归属

- 共享配置加载/校验、v1内存迁移、保留未知字段、锁/摘要/备份/原子保存、本机菜单与授权群/黑名单子命令、gate/router前置拒绝。
- 文件归属：src/qqbot_gateway/config.py、onebot_gate.py、model_gateway.py，plugins/qq_router/main.py，scripts/configure_bot.py、manage.py，配置机器人.cmd，config/settings.example.yaml，相关tests/离线验证脚本、README及进度/验收文档。
- 不开放LAP-10参数菜单、不改人设或启停实现。成功条件为U04—07离线证据齐备，真实群/重启验证单独记录。
- 开始时保留已有PROGRESS、REQUIREMENTS、ACCEPTANCE、工作线HANDOFF、IMPLEMENTATION_PLAN修改，以及未跟踪AGENTS/TASKS/UX_PLAN/tasks/LAP-08；实现代码无已有修改。共享文档在原内容基础上增量同步。

## 完成与验证

- 共享load_settings/normalize_settings，v1只在内存迁移，BOM/ID规范化/非空群/私聊关闭/全配置校验；gate、router、model共用loader，start在启动任何子进程前校验。
- 配置工具菜单及groups/blacklist命令、中文cmd、默认脱敏show；OS锁与start共用、PID+创建身份停止检查、摘要冲突拒绝、忽略目录逐次原字节备份、同目录临时文件/fsync/os.replace。
- gate在reserve/forward前拒绝黑名单；plugin在trace/任务/冷却/会话前拒绝并stop_event，成功路径不stop。管理员无豁免，出站白名单/heartbeat/echo保留，解除不删除历史。
- 53项单元测试通过；实际AstrBot router和At转换器两项离线集成通过；从其他CWD调用中文cmd show通过。细项、命令与限制见[验证报告](../../../../reports/lap-09-2026-10-16.md)。
- 新增参数默认合同已留在示例/共享loader；LAP-10/11非默认控制暂拒绝，不能静默忽略或宣称已接通；后续实现时解除对应限制。

## 修改文件与保留内容

实现文件为上列归属，另修改scripts/verify_g4_routing.py、tests/test_config.py、tests/test_onebot_gate.py、README；新增本交接与reports/lap-09-2026-10-16.md，增量同步PROGRESS/TASKS/工作线HANDOFF/ACCEPTANCE/UX_PLAN。本轮前已有规划文档完整保留并纳入用户新授权的交付提交；REQUIREMENTS/IMPLEMENTATION_PLAN/AGENTS/LAP-08内容不作本轮实现改写。

## 剩余与下一步

本机只读身份检查发现项目进程仍存活，运行实例尚未加载本轮代码；未修改实际settings.local.yaml或人设、未启停、未登录、未调用模型/发群消息。U04/05真实群及U07实际全组件重启验证待用户选定实际配置和测试发送者后参与；NapCat如需登录由用户本机操作。双击菜单及空格路径完整复制运行未人工验证。

LAP-09保留“实现/离线通过，真实待验”差额；不自动领取LAP-10。后续用户可启动LAP-10或单独继续本任务真实验收；不为旧错误反复推理。实现提交fc20133已成功推送origin/main；93个本地文档链接、git diff --check通过，结果在全局入口与台账同步，未改历史凭据或重写Git历史。
