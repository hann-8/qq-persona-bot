# QQ 人设文字 Bot（笔记本测试版）

项目进度从 [PROGRESS.md](PROGRESS.md) 开始。当前支持指定群的真实 @ 文字聊天，使用已登录、同账号同站点的 CodeBuddy CLI 和指定模型；群单条和多轮记忆已验证，隔离已通过离线集成检查；真实多人和长期运行仍在验收。视频、音频和网页正文尚未接入。

在 `E:\CodexWS\QQbot` 的 PowerShell 中使用：

```powershell
.\scripts\Start-Bot.ps1
.\scripts\Show-BotStatus.ps1
.\scripts\Stop-Bot.ps1
.\scripts\Test-Bot.ps1
```

启动脚本仅管理项目独立实例；已运行时会拒绝重复启动。停止依据项目记录的PID及创建时间，不按QQ进程名停止其他程序。`-ChannelOnly`启动选项仅用于关闭模型的通道诊断。不要同时启动两个实例。

QQ登录正常时可自动恢复；需要扫码时使用本项目NapCat本机界面。AstrBot管理页为 `http://127.0.0.1:6185`，NapCat为 `http://127.0.0.1:6099`；密码/令牌在被忽略的 `secrets` 目录，勿外传。日常QQ安装不属于该实例。

仅指定群且消息含QQ真实 @bot 时处理；普通文字、私聊、仅@全体、仅引用旧消息和手打“@昵称”不会触发。每个用户至少间隔5秒；收到回复后再问下一句。历史按群和用户隔离，最多保留8轮短文字上下文。管理员在真实@后发送“重置会话”，只重置其本人在当前群的会话。

人设在 `config/persona.md`；修改后停止并重新启动，新的设定版本会在下次请求建立新会话。本机账号、群、模型及队列参数在被忽略的 `config/settings.local.yaml`，格式参考 `config/settings.example.yaml`。已确定的账号、模型、额度来源及触发规则应保持原决定，禁止自动切换模型或另接收费API。

状态页查看队列、累计CLI尝试、最近错误和router_ready，不会调用模型。`backend_state=not_probed`表示本次启动尚未真实推理，不能据此判定登录失败。认证/配额故障后暂停请求；在官方界面处理后再重启，不反复尝试登录。进程运行不等于文本链路通过，验收证据见 `reports`。

`runtime`、`state`、`cache`、`logs`及`secrets`为本机数据；会话数据库可能含聊天内容，分享项目时不要附带这些目录。暂未配置开机自启；电脑睡眠时不承诺在线。
