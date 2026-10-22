# WeChatbot项目入口

2026-10-22（Asia/Shanghai）。唯一根进度入口，不另建根HANDOFF。位置 `E:\CodexWS\WeChatbot`；当前仅规划文档，无代码/运行配置/依赖/凭据/服务/独立Git或remote。

目标：个人微信中和朋友家人聊天，复用已有QQ项目的显式CodeBuddy/家庭Ollama路线与工具隔离/预算/未知结果保护，保持两个项目的账号、配置和历史独立。

当前状态：**WX-00详细规划完成；尚未实施或真实验证。** 首选验证候选是pywechat项目中的pyweixin（Windows微信4.1系列UI）。它尚未证明稳定身份、真实@、跨重启消息ID和可靠发送确认，不能直接启用群自动回复。腾讯iLink源码当前direct only，保留为用户以后明确接受Bot私聊形态的可选方案。

阅读顺序：[AGENTS](AGENTS.md)→本入口→[活动交接](tracks/bootstrap/HANDOFF.md)→[TASKS](TASKS.md)→[PLAN](docs/PLAN.md)/[调研](docs/RESEARCH.md)/[medium复制指令](docs/IMPLEMENTATION_GUIDE.md)。

| 工作线 | 状态 | 下一步 | 交接 |
| --- | --- | --- | --- |
| 独立项目规划/引导 | completed，仅规划 | 用户选择gpt-6.1-sol/medium后，仅领取WX-01离线骨架 | [HANDOFF](tracks/bootstrap/HANDOFF.md) |

任务顺序：WX-01离线骨架与模型固定快照→WX-02候选接入探针→能力满足才WX-03实际适配→WX-04明确小批次接受。一个session一个任务，不自动登录/发送/生成或推进整串任务。

默认：transport=mock、enabled/sends=false、授权群空、私聊关闭/名单空、mentions、视觉/网页/记忆/表情等均关闭。用户后续明确启用亲友私聊时仅微信独立白名单生效，QQ私聊边界不变。

未验证：客户端安装/版本、UI树可见性、可信群友身份/@/消息ID、实际图片像素、发送结果、登录持久化/锁屏/24h、模型真实效果。没有用上游README代替这些证据。

文档来源：QQbot任务LAP-38的wechat-bootstrap是版本化引导快照，本目录逐文件复制核验。后续实施以本目录为工作区和维护入口，不编辑QQ的镜像来驱动微信；源项目历史规划见 `E:\CodexWS\QQbot\tracks\laptop-workbuddy\tasks\LAP-38`。本目录尚未独立推送；不要推断QQ远端就是微信远端。
