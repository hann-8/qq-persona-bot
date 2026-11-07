# AstrBot 管理密码重置

返回 [PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md)。继承项目边界。

2026-11-07，session OPS-ASTRBOT-PASSWORD 唯一执行者，用户明确授权重置。范围：本机 AstrBot dashboard 密码及必要的单组件受管重启；不调用模型或发送消息。备份留忽略 state，密码不入 Git。

状态：已完成；新密码经本机 /api/auth/login 验证 status=ok。仅重启受管 AstrBot，其他组件保留。归属本交接及 PROGRESS/TASKS/工作线 HANDOFF 的本项入口、忽略运行配置和受管身份记录。保留原未跟踪 .workbuddy、vision 规划报告和启动 bat。

备份：忽略目录 state/astrbot-password-reset/。本机凭据：忽略文件 secrets/astrbot-dashboard.local.json。未改业务代码/config/local，不调用模型或发送消息。router-ready 创建身份仍有效。
