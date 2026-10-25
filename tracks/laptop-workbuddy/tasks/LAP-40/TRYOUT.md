# LAP-40 官方OneBot准备与一次文字试用

返回[交接](HANDOFF.md) / [当前medium实施指令](DESKTOP_MEDIUM_START.md) / [桌面入口计划](DESKTOP_PLAN.md) / [项目入口](../../../../PROGRESS.md)。2026-10-25，Asia/Shanghai。

## 当前结论与授权边界

11:18最新只读实查：环境/官方Snow/token、专用QQ和local均存在，项目组件text running、gateway/router就绪，但gate尚未收到OneBot连接，CLI 0次。旧[MATERIALS](MATERIALS.md)的QQ/local缺项为10:49历史，不能据此重装/覆盖。现有`启动机器人.cmd`只起项目三组件，未启动QQ/Snow；中文状态还存在错误提示。用户不熟悉Snow，下一轮应按[DESKTOP_PLAN](DESKTOP_PLAN.md)/[medium指令](DESKTOP_MEDIUM_START.md)实际补日常入口，不能把下面的高级手工命令当成日常入口已经交付。

**桌面入口目前只完成规划，尚未实现。** 未来用户将双击同一启动/查看/关闭入口，脚本准备OneBot并打开管理页；首次用户只在官方网页确认条款、选择专用QQ并登录/扫码，不手填JSON/token。本轮没有启停、登录或模型/群操作；下面材料命令仅作空环境复现，高级手工方式保留给熟悉者。真实启停/接通后的模型群答仍需用户后续明确授权或亲自操作。

| 动作 | 下一轮材料准备指令的范围 | 仍需用户亲自操作或明确授权 |
| --- | --- | --- |
| Python/AstrBot环境、官方Snow完整包 | 可下载、解压、安装到本根，执行不启动服务的AstrBot init和基础配置生成 | 不因安装完成自动run/start |
| 专用QQ | 可下载官方安装材料；能确认仅写新根且不自动启动时才安装，否则留给用户正常安装 | 启动QQ、选择进程、加载官方Snow、登录/扫码；不读日常密码或登录资料 |
| 本根业务配置与秘密 | 仅在用户提供当前选择后写新根；新token可经准备指令授权在本机生成、不回显 | 未提供的账号/群/管理员、当前触发与模型预算由用户提供或手工保留；不猜值、不用模板覆盖 |
| 项目start-channel/start-text | 都属于真实启停，材料准备不执行 | start-text接通已登录账号后即可能按既有规则触发真实模型和群输出，必须同时覆盖这些操作的授权 |

## 当前材料实查

2026-10-25 10:49的实际结果以[MATERIALS](MATERIALS.md#已实际准备与核对)为准：本根Python/.venv、AstrBot工具与基础实例、官方Snow完整展开及三个token均已存在并本地核对；Node/CodeBuddy程序文件/摘要匹配。QQ下载失败/未安装；业务local和兼容单文件均缺失。人设19,256字节原样保留，模板16,384预算下正文差2,872、加2,048开销后至少差4,920，尚不含政策/请求封装；优先保留用户现用预算，待业务值后精确计算，不改人设或静默调参。

## 材料准备复现参考（已存在的本轮材料不覆盖）

1. 复核根、分支、HEAD/状态并登记session/文件归属。先补齐能独立准备的环境、官方包和框架基础实例，不因缺业务值退回纯规划。
2. 用以下命令创建本根两个Python环境；uv工具、Python下载目录和缓存仅定向本根，不修改全局PATH或原运行根。每条外部命令非零即停止该步骤、保留错误；网络/包准备失败只处理实际错误，不改锁或自动升级后端。

```powershell
$taskRoot = 'E:/CodexWS/QQbot_Snowluma'
$taskUv = 'C:/Users/yutha/.local/bin/uv.exe'
Set-Location $taskRoot
$env:UV_CACHE_DIR = "$taskRoot/cache/uv"
$env:UV_PYTHON_INSTALL_DIR = "$taskRoot/runtime/python"
$env:UV_PYTHON_BIN_DIR = "$taskRoot/runtime/python-bin"
$env:UV_TOOL_DIR = "$taskRoot/runtime/astrbot-tool"
$env:UV_TOOL_BIN_DIR = "$taskRoot/runtime/astrbot-bin"
& $taskUv python install 3.12 --no-bin
if ($LASTEXITCODE -ne 0) { throw 'Local Python preparation failed' }
$taskPython = "$taskRoot/runtime/python/cpython-3.12.14-windows-x86_64-none/python.exe" # 本轮实得版本，先核对存在
& $taskUv sync --frozen --python $taskPython
if ($LASTEXITCODE -ne 0) { throw 'Project environment preparation failed' }
$taskLock = Get-Content "$taskRoot/config/versions.lock.json" -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Force "$taskRoot/runtime/downloads" | Out-Null
$taskLock.astrbot.dependencies.psobject.Properties | ForEach-Object { '{0}=={1}' -f $_.Name,$_.Value } | Set-Content "$taskRoot/runtime/downloads/astrbot-constraints.local.txt"
& $taskUv tool install --python $taskPython --constraints "$taskRoot/runtime/downloads/astrbot-constraints.local.txt" --with 'PyYAML==6.0.3' --with 'markdown-it-py==4.2.0' 'astrbot==4.29.0'
if ($LASTEXITCODE -ne 0) { throw 'AstrBot environment preparation failed' }
```

AstrBot独立工具环境也要能导入项目使用的yaml/markdown_it；安装到`.venv`不会使工具环境自动可见。依据[uv工具安装](https://docs.astral.sh/uv/guides/tools/)、[uv目录环境变量](https://docs.astral.sh/uv/reference/environment/)及[AstrBot 4.29.0包入口](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.0/pyproject.toml)。本轮已实际执行环境准备，显式绑定本根Python并用现有版本记录约束工具传递依赖，最终版本对照0差异；见MATERIALS。

3. 仅对新建空AstrBot实例做官方初始化。`init --yes`建立`.astrbot`和data目录；它不保证单独生成`cmd_config.json`，所以再通过官方配置类生成基础配置并把dashboard约束到回环6185。现有实例若已出现，先检查归属并保留，不覆盖。

```powershell
New-Item -ItemType Directory -Path "$taskRoot/runtime/astrbot" -Force | Out-Null
$env:ASTRBOT_ROOT = "$taskRoot/runtime/astrbot"
$env:ASTRBOT_DISABLE_METRICS = '1'
Push-Location "$taskRoot/runtime/astrbot"
try {
    & "$taskRoot/runtime/astrbot-bin/astrbot.exe" init --yes *> bootstrap.local.log
    if ($LASTEXITCODE -ne 0) { throw 'AstrBot init failed; inspect local bootstrap log' }
    & "$taskRoot/runtime/astrbot-tool/astrbot/Scripts/python.exe" -B -c "from astrbot.core import astrbot_config; astrbot_config['dashboard']['host']='127.0.0.1'; astrbot_config['dashboard']['port']=6185; astrbot_config.save_config()" >> bootstrap.local.log 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'AstrBot base configuration failed; inspect local bootstrap log' }
}
finally { Pop-Location }
```

[官方init](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.0/astrbot/cli/commands/cmd_init.py)、[基础配置生成](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.0/astrbot/core/config/astrbot_config.py)及[run的实例标记要求](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.0/astrbot/cli/utils/basic.py)支持上述准备方法。此处只生成本机实例材料，不调用`run`、配置项目provider或启动监听；初始密码等输出留本根忽略日志，由操作者本机查看。

4. 下载[官方v2.1.1完整Windows x64包](https://github.com/SnowLuma/SnowLuma/releases/tag/v2.1.1)中的`SnowLuma-v2.1.1-win-x64.zip`，展开到`runtime/snowluma/v2.1.1`，确认launcher就在该层且保留全包。本轮重新查到官方asset：42,694,125字节，SHA256 `c739171f95c27706767e69ba36099707c222fcec639b46f4d59689997b527772`；这只是下载核对，不是运行/proof或真实兼容证据。[官方打包流程](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/.github/workflows/release.yml)给完整Windows包加入node.exe，不先安装Lite所需Node或构建Snow。QQ从[腾讯官方Windows入口](https://im.qq.com/pcqq/)正常准备为新根专用安装；不能把已patched的旧QQ目录复制过来，也不猜静默安装参数。若安装器不能保证只写新根且不自动启动，先完成其他材料，由用户完成专用安装到`runtime/qq-snowluma/QQ.exe`。
5. 用户提供业务值后准备本根local与秘密，完成下节校验。交付材料就绪/缺项和脱敏结果后停止；不会自动进入真实启动。

## 业务配置交接与零模型校验

用户需提供或亲自在新根保留：bot QQ、目标授权群、管理员，既有blocked_users（如有则原样保留，无需新增）、当前mentions/free、模型/推理强度/输入预算/超时/输出与功能开关。可由用户手工带入五份local或兼容单文件；不复制旧state、聊天历史、QQ登录数据或日常密码。若确为全新配置，明确允许后才运行`scripts/config_files.py init`，按[配置说明](../../../../config/README.md)补齐五文件；目录一旦存在就不再回退单文件，不能留下半套。

仅将`config/local/runtime.yaml`中的`qq_transport.provider`明确改为`snowluma`；私聊维持false，模型和额度来源保持既有CodeBuddy。本根token文件中保留三个独立键`onebot_inbound`、`onebot_upstream`、`model_gateway`，各至少32字符。新根无token时，下一轮准备指令允许在本机生成三个随机值并只写忽略文件，不打印或提交；已有文件不得覆盖。用户在Snow WebUI中手工填本根inbound值，不能把upstream/model token填过去。

兼容的旧proof/control/recovery/trial字段保持合法默认或已有值，不准备其证明/控制密钥文件，不启私有服务。runtime示例里的旧G0/G1/72h注释以LAP-40当前[PLAN](PLAN.md)为准，不形成首试门槛。

配置保存后仅做本地校验：

```powershell
Set-Location E:/CodexWS/QQbot_Snowluma
.\.venv/Scripts/python.exe scripts/config_files.py check
```

`check`不读取token，不能代替token存在/长度、框架材料或预算可容纳性的核对。准备方用本根Python加载`read_project`，按router参数调用`compose_persona`，再用`InputBudget.from_settings(settings, validate_model_settings(settings)).select_history(system, '你好', [])`做一次零模型容量核对，仅报告用量/上限/通过与否，不输出人设或配置值。该调用只计算本地字节预算，无CLI/SSH/QQ/模型调用。预算是可见UTF-8字节保守值，不是原生token或credits承诺。若不通过，保留人设和现有选择，将具体差额交用户；不修改代码或新增测试矩阵。

## 明确授权真实启动后：项目与官方端

真实文字试用应在用户准备好的安静目标群时间窗执行。保留free时，一旦接通就可能被其他新消息正常触发，不能承诺总共只消耗一次模型；若要严格限制次数，须由用户决定临时触发设置/试用窗口，不能由agent擅改模式。材料检查和健康查询不需要模型调用。

先启动项目三个组件，在本根执行，任何命令失败都先看本机错误，不继续后续启动：

```powershell
Set-Location E:/CodexWS/QQbot_Snowluma
.\.venv/Scripts/python.exe scripts/manage.py start-text --no-pause
.\.venv/Scripts/python.exe scripts/manage.py status --json
```

`start-text`为隔离AstrBot准备项目provider/插件，然后依次启动AstrBot（6185/6199）、gateway（8765）、gate（6200），使用同一实例快照。不另起单组件，不启动NapCat，不访问6099/私有5098。此时官方端尚未连接可以显示等待连接，三个项目组件running不代表QQ已登录。原根本轮未探活；若端口被旧根或其他进程占用，只按错误报告归属，由用户决定如何释放，不能擅停其他根。

操作者正常启动专用QQ，再另开前台终端运行官方包：

```powershell
Start-Process -FilePath 'E:/CodexWS/QQbot_Snowluma/runtime/qq-snowluma/QQ.exe'
```

```powershell
Set-Location E:/CodexWS/QQbot_Snowluma/runtime/snowluma/v2.1.1
.\launcher.bat
```

依据[官方v2.1.1 README](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/README.md)，操作者在`http://127.0.0.1:5099`用启动日志中的初始密码按正常引导选择bot专用QQ进程并完成登录/扫码；官方端由操作者管理，项目不接管。保持官方手动选进程方式，不设置自动加载到日常QQ。

按[官方配置参考](https://snowluma.github.io/zh/docs/guide/configuration)，实际bot账号`config/onebot_<uin>.json`覆盖全局。通过WebUI将一条反向WS连接接到gate；`networks.wsClients`内的单条配置示例如下，占位值仅在本机替换，不把此对象当成整个配置文件覆盖：

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

Snow不直连AstrBot。gate用本根upstream token连接`ws://127.0.0.1:6199/ws`，模型token只用于8765。官方[反向WS实现](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/network/ws-client-adapter.ts)发出Bearer、X-Self-ID、Universal；[get_status实现](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/onebot/src/actions/info.ts)提供online/good，未发现需要先改Snow的理由。保存/应用按官方WebUI，未刷新时由操作者正常重启官方端。

再执行`manage.py status --json`，确认provider为snowluma、process_state为running，`channel.connected=true`、`channel.channel_ready=true`、顶层`can_receive_group_messages=true`。标准get_status每15秒轮询，45秒过期；false、缺失、超时或断线均不算就绪。状态就绪仍不是群收发成功证明。

只有另行授权仅验证通道时才用`start-channel --no-pause`；它不启动模型答复，仍是真实启停。换成text前先正常stop再start-text，不把分阶段通道检查设为首次试用的额外前置。

## 一次目标群文字与准确停止

1. 由允许成员在目标授权群发一条**新文字并真实@bot**，例如“你好，请用一句话回复”；不发图片/链接，不用普通free消息是否回复判成功。
2. 观察同一时间窗：入口已接入/在线、该次任务是否进入模型、发送回执是否成功、群里是否看到纯文字回复。只做一次人工触发，不自动重复发消息或重试生成。只有真实模型链和群内可见回复都成立，才记“最小文字真实试用通过”。
3. 失败则保留脱敏类别和时间，先区分材料/配置、握手/状态、AstrBot/router、gateway/CLI或发送ACK哪一段；不把无模型任务直接当Snow内部问题。其他功能和长稳保持未验。

停止顺序：先停止本根项目组件以关闭模型/群输出，再由操作者停止官方端和专用QQ。

```powershell
Set-Location E:/CodexWS/QQbot_Snowluma
.\.venv/Scripts/python.exe scripts/manage.py stop --no-pause
.\.venv/Scripts/python.exe scripts/manage.py status --json
```

项目stop按登记PID/创建身份只停止gate/AstrBot/gateway；不关闭QQ/Snow。[官方launcher](https://github.com/SnowLuma/SnowLuma/blob/v2.1.1/packages/runtime/launcher.bat)在前台运行Node入口，操作者在该终端Ctrl+C结束；随后若停在批处理pause提示，按提示退出，专用QQ从客户端正常退出。也可使用本根`启动机器人.cmd`、`查看状态.cmd`、`关闭机器人.cmd`；关闭启动窗口不会停后台。禁止按QQ/Node/Python进程名批量结束，不清理旧根进程。停止后的官方进程是否退出由操作者确认，项目status不证明它们已退出。

故障材料仅留本根忽略目录：`logs/gate.log`、`logs/astrbot.log`、`logs/model.log`；配置准备失败看`runtime/astrbot/configure-error.log`，初始化看`runtime/astrbot/bootstrap.local.log`。`state/gate-connection.json`、`state/service-mode.json`核对本机连接/实例，`state/tasks.sqlite`仅本机核对该次任务和发送状态，不上传整库。官方日志从WebUI/前台查看，不假定磁盘路径。对外交接仅含时间窗、脱敏错误类别、组件状态、ACK结果；不含token、账号群号、原始群消息、模型正文或初始密码。

不重跑A4或全量回归，不增加资格/proof/probe、内部过滤/零存储、恢复或72h/7天前置。实际握手、事件或ACK不兼容时只做必要外部适配；只有实际必须改Snow内部才能继续，才携具体阻断与已尝试的外部解决结果交用户决定。
