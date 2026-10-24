# LAP-40 官方OneBot文字试用

返回[交接](HANDOFF.md) / [项目入口](../../../../PROGRESS.md)。2026-10-25，Asia/Shanghai。

## 当前能做什么

项目侧接入已实现，7项新专项、18项既有gate、14项生命周期离线/合成检查通过。真实安装、启动、QQ登录、CodeBuddy生成、群收发均未执行。**本根运行材料尚缺，当前不能直接双击启动并试用。** 以下是材料齐备后的准确入口，不是已经运行成功的记录。

本根实查缺项（只检查存在性，没有读取原运行根配置）：

| 缺项 | 项目需要的位置/内容 |
| --- | --- |
| 项目Python环境 | `.venv/Scripts/python.exe`，Python 3.12，依赖按根`uv.lock`；操作者准备时可用`uv sync --frozen --python 3.12` |
| AstrBot运行环境和实例 | `runtime/astrbot-bin/astrbot.exe`、`runtime/astrbot-tool/astrbot/Scripts/python.exe`、`runtime/astrbot/data/cmd_config.json`，现有项目版本为4.29.0；需正常准备该隔离实例的基础配置、data/plugins目录和运行依赖，不能把私有A4目录当框架环境 |
| 官方SnowLuma、QQ | `runtime/snowluma/v2.1.1/launcher.bat`及原包其余文件、专用`runtime/qq-snowluma/QQ.exe`均缺；使用官方v2.1.1完整包和正常QQ安装方式，不使用`runtime/snowluma-private`产物 |
| 本根业务配置和token | `config/local/`、兼容入口`config/settings.local.yaml`及`secrets/local-tokens.json`均缺；必须由操作者准备账号、授权群、管理员和三个独立token `onebot_inbound`、`onebot_upstream`、`model_gateway`（至少32字符），秘密仅放忽略文件 |

`config/persona.md`存在，本轮未改。由于本根没有当前本机配置，不能宣称已继承原运行根的free/mentions、模型或人设实际值。操作者准备配置时保留其当前选择及人设；仅把`qq_transport.provider`显式设为`snowluma`，私聊维持false。不使用新装模板默认值覆盖现有业务选择。若确为全新配置，五文件入口和校验见[配置说明](../../../../config/README.md)，`scripts/config_files.py init`仅创建模板，不会生成身份/token；本轮没有执行。

旧`snowluma.proof_file/control_secret_file/control_port`、recovery/trial配置可保持已有兼容值；官方运行不读取证明/控制密钥内容、不访问控制端口，也不启动私有健康、恢复或长稳任务。无需准备这些文件或填写proof=true。默认provider仍是napcat，不能漏设provider后直接启动本根。

当前没有在本根试装AstrBot，因此不提供未经验证的安装器参数或跨根复制命令。上述四类是已确认的准备缺项；不追加资格、probe、A4或长稳前置。CodeBuddy继续使用现有显式配置和既有账号/额度来源，本轮没有验证其当前登录、模型额度或真实生成。

## 官方端正常启动、配置与停止

依据[官方v2.1.1 README](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/README.md)和[官方配置参考](https://snowluma.github.io/zh/docs/guide/configuration)，Windows完整包运行`launcher.bat`，再在本机WebUI `http://127.0.0.1:5099`按正常引导选取专用QQ进程、登录并设置账号连接。本项目不启动/接管QQ或Snow，不新增加载器。保留官方默认的手动选择方式，只选择bot专用QQ。

材料准备好后，在PowerShell中正常启动专用QQ：

```powershell
Start-Process -FilePath 'E:/CodexWS/QQbot_Snowluma/runtime/qq-snowluma/QQ.exe'
```

另开终端启动官方Snow：

```powershell
Set-Location E:/CodexWS/QQbot_Snowluma/runtime/snowluma/v2.1.1
.\launcher.bat
```

WebUI密码按官方启动输出由操作者本机查看，不贴进交接。账号OneBot连接只需一条反向WS，目标是**gate** `ws://127.0.0.1:6200/ws`，不直连AstrBot。填入本根`onebot_inbound` token，角色`Universal`，消息格式`array`，自身消息上报false。账号级`config/onebot_<uin>.json`覆盖全局，确认改的是实际bot账号。官方`networks.wsClients`条目示例（占位token须在本机替换）：

```json
{
  "name": "qqbot-gate",
  "enabled": true,
  "url": "ws://127.0.0.1:6200/ws",
  "role": "Universal",
  "accessToken": "REPLACE_LOCALLY_WITH_ONEBOT_INBOUND",
  "messageFormat": "array",
  "reportSelfMessage": false,
  "reconnectIntervalMs": 5000
}
```

来源：[v2.1.1反向WS实现](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/network/ws-client-adapter.ts)使用Bearer、X-Self-ID及X-Client-Role，与现有gate一致，无需转换层。实例配置保存/应用遵循官方WebUI；若连接未刷新，操作者正常重启官方Snow。停止时在其前台终端Ctrl+C，专用QQ通过客户端正常退出；项目stop只停止项目登记进程，不替你关闭这两者，不按进程名批量结束。

## 项目组件启动和停止

配置与依赖准备好后，在本根执行：

```powershell
Set-Location E:/CodexWS/QQbot_Snowluma
.\.venv/Scripts/python.exe scripts/config_files.py check
.\.venv/Scripts/python.exe scripts/manage.py start-text --no-pause
.\.venv/Scripts/python.exe scripts/manage.py status --json
```

`start-text`一起准备隔离AstrBot配置/插件并启动AstrBot（6185/6199）、model gateway（8765）、gate（6200），沿用同一实例快照，不另起第二套手工进程。不启动NapCat、不访问6099或私有5098。状态中的项目进程running只表示这三个组件；QQ/Snow由操作者另管。等待gate `connected=true`、`channel_ready=true`及`can_receive_group_messages=true`，然后才做群试用。Snow通过标准get_status/heartbeat报告online/good，状态15秒轮询，45秒过期；false、缺失、超时或断线不算就绪，这不是群收发成功证明。

只准备无模型通道时可用`start-channel --no-pause`，但该模式不生成答复；试用文字回复请直接使用`start-text`。已启动另一模式时先正常stop，再换模式；不要重复运行单组件入口或另开多个bot。

停止本根gate/AstrBot/gateway：

```powershell
Set-Location E:/CodexWS/QQbot_Snowluma
.\.venv/Scripts/python.exe scripts/manage.py stop --no-pause
```

也可用本根`启动机器人.cmd`、`查看状态.cmd`、`关闭机器人.cmd`。这些命令未在本轮真实执行。端口冲突时按错误定位现有归属；原运行根本轮未探活或启停，不为新根清理旧根进程。

## 一次目标群文字试用与故障材料

由用户亲自操作或另行明确授权后：按上面步骤准备/启动并确认gate就绪；从允许成员在目标授权群发送一条新文字，明确真实@bot（兼容mentions/free；free的普通消息允许决定不说话）；观察是否经既有模型链产生可见纯文字回复。只做一次，不用重复发消息来自动重试。记录时间、是否已接入/在线、是否有模型任务、是否收到发送回执和群内可见回复。只有该次真实闭环成功才记“最小文字真实试用通过”；其余功能和长稳仍未验。

失败材料留在本根忽略目录：`logs/gate.log`（固定握手/协议类别）、`logs/astrbot.log`、`logs/model.log`，准备失败另看`runtime/astrbot/configure-error.log`；`state/gate-connection.json`和`state/service-mode.json`用于本机核对连接/实例。`state/tasks.sqlite`仅本机检查该次任务和发送状态，不直接上传整库。官方日志使用官方WebUI/前台输出，本轮未假定其磁盘路径。对外只给该时间窗的脱敏错误类别、组件状态、ACK结果；删去token、账号群号、原始群消息、模型正文和WebUI初始密码，不提交原始日志/配置/数据库。

不重复跑A4，不扩建私有过滤/证明或恢复系统。只有实测握手、事件或ACK不兼容才补外部薄适配；必须改Snow内部才能继续时，将具体失败与外部尝试结果交回用户决定。
