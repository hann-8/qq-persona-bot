# LAP-40：官方原版SnowLuma最小文字接入

返回[项目入口](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [任务台账](../../TASKS.md) / [计划](PLAN.md) / [准备与试用](TRYOUT.md)。继承本根AGENTS，用户最新决定优先。2026-10-25，Asia/Shanghai。

## 当前状态

**项目侧已实现，离线/合成通过，真实未验；本根运行材料缺失，当前不能直接启动。** 官方原版SnowLuma现成OneBot经gate→AstrBot/router→既有gateway/CodeBuddy CLI文字链；无需修改Snow内部或薄转换层。默认provider保持napcat，显式snowluma才走本路径。当前缺项与准确启停/一次试用/脱敏故障材料位置见[TRYOUT](TRYOUT.md)。

旧私有改造路线整体被取代，B/C停止。A4按历史交付为已实现/合成通过、路线停止采用；代码、产物、证据原样保留，本轮未复核、未重跑或修改。账号屏蔽由用户在QQ客户端拉黑，不新增内部过滤、零日志/存储、资格/proof/probe或原生数据证明。

## 本次实现

session `LAP-40-official-onebot-implementation`，2026-10-25 00:16领取，起点`1702571`、工作区干净；分支`codex/lap-40-snowluma`，根`E:/CodexWS/QQbot_Snowluma`。TASKS登记后重读，发现router实际私有健康阻断后先扩登记再修改。无子代理、无模型切换。

- `scripts/manage.py`：snow分支不再调用无条件拒绝的require_runtime，复用现有配置快照和AstrBot/gateway/gate启动流程，只创建这三个组件。状态不再要求QQ/Snow受管身份或5098监听；官方实例stop不调用私有控制。记录transport_mode=official_onebot。NapCat默认仍创建NapCat并保留原登录回退，Snow不运行NapCat登录观察/回退。
- `src/qqbot_gateway/onebot_gate.py`：入口不再要求私有runtime；application不再创建私有monitor。Snow就绪来自标准get_status/heartbeat的online=true、good=true及45秒内状态，15秒轮询、失联/过期撤销当前连接；无私有health内容依赖。继续使用token、X-Self-ID、Universal、授权群、私聊关闭、既有票据/发送echo/ACK链。
- `plugins/qq_router/main.py`：实际阻断文字链的gate_metadata不再要求HMAC健康序列/过期单调时钟证明；保留本项目gate进程身份、实例/配置摘要、连接代际和标准状态新鲜度验证。既有模型、额度、触发模式、人设、一次尝试和业务逻辑未改。
- `tests/test_official_snowluma.py`：7项必要专项；仅临时根、自造身份/文字、动态回环测试服务及模拟创建/停止，不执行真实QQ/Snow/模型进程。实际导入AstrBot 4.29.0转换器与router，文字通过框架send和原gate ACK返回。

`qq_transport.py/config.py`经定向检索无需改动；旧私有配置可兼容读取但不以其证明文件、控制秘密/端口或构建作为新路径运行依赖。保留停止采用的私有helper/适配器代码，不维护其运行兼容。没有新增provider、自动fallback、恢复或部署。

## 验证证据与边界

新根没有Python依赖环境，使用原根已有Python/框架库**只读作为测试运行时**，`-B`及PYTHONDONTWRITEBYTECODE=1禁写字节码；工作目录始终本根，AstrBot导入副作用和测试状态均在临时目录。没有修改原`E:/CodexWS/QQbot`或旧C根，也没有准备本根local/persona。

PowerShell验证环境：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='E:/CodexWS/QQbot_Snowluma/src;E:/CodexWS/QQbot_Snowluma/tests'
$env:QQBOT_TEST_ASTRBOT_SITE='E:/CodexWS/QQbot/runtime/astrbot-tool/astrbot/Lib/site-packages'
$env:ASTRBOT_DISABLE_METRICS='1'
# 首次25通过：7新专项+18gate；随后状态显示/测试资源清理小修后末次：
& E:/CodexWS/QQbot/.venv/Scripts/python.exe -B -m unittest test_official_snowluma test_lifecycle -q
# 21通过：7新专项+14生命周期，8.873秒
```

25项组合7.014秒通过；21项组合8.873秒通过；合计39项不同用例。后一次改动只纠正Snow明确offline应显示disconnected并消除新测试未关闭socket告警；NapCat gate代码未在两次之间变更。验证覆盖官方式握手、标准状态/失效、目标群文字事件、实际AstrBot转换/router连接判定/框架回复、匹配及不匹配echo、基本账号/授权群/私聊边界、显式free、项目组件启动停止归属、默认NapCat生命周期/配置保留。框架旧audioop/register弃用及异步调试慢导入提示不影响通过。

未运行A4矩阵、全量旧功能/极端竞态/性能/72h/7天；未安装、真实启停、登录/扫码、调用真实模型、发群或SSH。实际模型生成和目标群可见文字闭环未验，合成ACK不晋升为真实成功。

## 实际准备阻断及下一步

本根存在`config/persona.md`，但不存在`.venv`、AstrBot可执行/框架Python/实例cmd_config、官方Snow v2.1.1包、专用QQ可执行、五文件local/兼容单文件配置及token。仅列这些实查缺项，不从旧私有资格/长稳差额派生前置。没有原本机配置，不能宣称已继承其当前模式/模型/人设；准备时由操作者保留当前业务选择。准确路径/命令见[TRYOUT](TRYOUT.md)。

交付后停止并释放本session归属；下一步为用户准备材料或另行授权准备/真实试用。只有真实握手、事件或ACK不兼容才做外部薄适配；实际必须修改Snow内部时交回具体阻断与外部尝试结果。不自动推进旧B/C或其他功能。

## 文件与Git交付

归属修改：PROGRESS、工作线HANDOFF/TASKS、本任务HANDOFF/PLAN、TRYOUT、三个上述生产文件和一个新测试文件，共10份。未改AGENTS、配置模板、local/persona、A4代码/产物/证据和Snow内部；原工作区干净，没有夹带他人修改。git diff --check及六份变更Markdown的本地链接存在性检查通过；提交推送结果见本次最终交付及Git日志。长期Git授权用于本任务交付，不代表部署或真实试用通过。

回滚仅撤销本次项目侧接入提交并保持停机，不删除材料或自动启动原根。历史[A4交接](STAGE3_A4_HANDOFF.md)及[报告](../../../../reports/lap-40-A4-implementation-2026-10-24.md)保留；原官方材料记录见[历史报告](../../../../reports/lap-40-stage3-materials-2026-10-24.md)，不当作新根当前文件已存在的证据。
