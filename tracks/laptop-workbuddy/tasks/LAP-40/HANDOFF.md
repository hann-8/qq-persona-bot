# LAP-40：官方原版SnowLuma最小文字接入

返回[项目入口](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [任务台账](../../TASKS.md) / [计划](PLAN.md) / [准备与试用](TRYOUT.md) / [下一轮最小执行指令](NEXT_SESSION.md)。继承本根AGENTS，用户最新决定优先。2026-10-25，Asia/Shanghai。

## 当前状态

**项目侧已实现/上次离线合成通过；本轮交付只读复核与材料准备规划完成，真实未验，新根仍不能直接启动。** 官方原版SnowLuma现成OneBot经gate→AstrBot/router→既有gateway/CodeBuddy CLI；本轮必要调用未发现新增的基本文字收发代码阻断，不新增修复或测试任务。默认provider保持napcat，显式snowluma才走本路径。下一轮优先实际补环境和链路，功能恢复排在文字跑通之后，使用[NEXT_SESSION](NEXT_SESSION.md)；准确准备/启停/一次试用见[TRYOUT](TRYOUT.md)。

## 本轮只读复核

session `LAP-40-official-review-preparation-plan`，2026-10-25 10:31登记后重读；工作根`E:/CodexWS/QQbot_Snowluma`、分支`codex/lap-40-snowluma`。本地HEAD和`git ls-remote --heads origin refs/heads/codex/lap-40-snowluma`均为`89b7dfae0efcd1949fe8289aa76ed1492bdfd8ab`，开始时`git status --short --branch`干净。本轮审阅该提交三个生产文件的差异及必要消费者/材料接口，不重读全部历史、不查询现有bot在线状态。

| 必要调用证据 | 结论与限度 |
| --- | --- |
| `scripts/manage.py:_start_channel`（478行）、`_snow_framework_specs`（324行）、`stop_project`（269行） | 官方provider走共用项目启动规格，不调用require_runtime/_start_snow_channel；specs只包含AstrBot/gateway/gate，official_onebot的stop跳过私有控制；端口要求不含6099/5098。默认napcat追加原NapCat，QQ/Snow始终由操作者正常管理 |
| `onebot_gate.py:main`（683行）、`application`（559行）、`channel_ready`（218行）、`_status_loop`（300行） | 启动不调用私有runtime/monitor；就绪只用连接、online/good和45秒新鲜度，15秒标准get_status轮询。官方v2.1.1的WS headers和get_status字段与此匹配，来源见TRYOUT；尚无真实握手结果 |
| `onebot_gate.py:_incoming/_outgoing`（385/489行）、`plugins/qq_router/main.py:gate_metadata/transport_allowed`（81/111行） | 文字事件由gate附当前连接/输出票据进入现有框架；router要求本项目进程身份、相同实例/配置摘要与标准状态，不再要求私有健康证明。文字发送走原action/echo/ACK链；未以静态审阅冒充真实发送 |
| `config.py:load_gate_config`（311行）、`qq_transport.py:resolve_transport/validate_transport`（73/122行） | 旧proof/control字段仍有兼容格式/路径校验，但官方启动不读取其文件内容或要求产物存在；不用建立证明/控制密钥。`startup_unknown`所读的旧启动记录在本根不存在，不构成本根首启阻断；不要把旧state迁入新根 |
| `workbuddy_cli_runner.py:CLIRunner.__init__`（102行）与本机文件实查 | 锁定Node、CLI入口及headless文件存在，headless摘要匹配；构造器的这一项文件检查未发现缺口。没有认证或生成，不保证当前账号/站点/额度可用 |

准备说明的实际差额已修正：uv绝对路径存在但不在PATH；AstrBot除安装还需`.astrbot`、data/plugins和基础cmd_config，新说明提供官方init/配置类步骤，不能直接run来补材料。Snow完整包官方asset本轮已重新查到，新根launcher/QQ仍缺；不把旧报告当材料存在证据。

本根人设UTF-8正文19,256字节，超过新装模板16,384输入预算（另加2,048开销）；`router:455 → InputBudget.select_history/check`明确会在该默认组合下触发`INPUT_TOO_LONG`。这是配置准备时必须处理的兼容点，不是Snow接入代码缺陷；本根没有实际local，不能认定用户现用预算错误。保留现用预算和完整人设，下一轮零模型核对；缺值/不足交用户决定，不自动删改人设、改预算、增加代码或测试任务。

本轮只读结果不要求修复代码或改Snow内部。材料安装/初始化、真实启停和QQ/Snow登录、真实模型/群答的授权分开；start-text一旦接通即可能按保留free规则触发，不能把它当成纯材料检查。下一轮最小指令只授权准备，完成可做环境后交付用户缺项并停止；不加长稳或完整旧功能门槛。

旧私有改造路线整体被取代，B/C停止。A4按历史交付为已实现/合成通过、路线停止采用；代码、产物、证据原样保留，本轮未复核、未重跑或修改。账号屏蔽由用户在QQ客户端拉黑，不新增内部过滤、零日志/存储、资格/proof/probe或原生数据证明。

## 上次实现（89b7dfae）

session `LAP-40-official-onebot-implementation`，2026-10-25 00:16领取，起点`1702571`、工作区干净；分支`codex/lap-40-snowluma`，根`E:/CodexWS/QQbot_Snowluma`。TASKS登记后重读，发现router实际私有健康阻断后先扩登记再修改。无子代理、无模型切换。

- `scripts/manage.py`：snow分支不再调用无条件拒绝的require_runtime，复用现有配置快照和AstrBot/gateway/gate启动流程，只创建这三个组件。状态不再要求QQ/Snow受管身份或5098监听；官方实例stop不调用私有控制。记录transport_mode=official_onebot。NapCat默认仍创建NapCat并保留原登录回退，Snow不运行NapCat登录观察/回退。
- `src/qqbot_gateway/onebot_gate.py`：入口不再要求私有runtime；application不再创建私有monitor。Snow就绪来自标准get_status/heartbeat的online=true、good=true及45秒内状态，15秒轮询、失联/过期撤销当前连接；无私有health内容依赖。继续使用token、X-Self-ID、Universal、授权群、私聊关闭、既有票据/发送echo/ACK链。
- `plugins/qq_router/main.py`：实际阻断文字链的gate_metadata不再要求HMAC健康序列/过期单调时钟证明；保留本项目gate进程身份、实例/配置摘要、连接代际和标准状态新鲜度验证。既有模型、额度、触发模式、人设、一次尝试和业务逻辑未改。
- `tests/test_official_snowluma.py`：7项必要专项；仅临时根、自造身份/文字、动态回环测试服务及模拟创建/停止，不执行真实QQ/Snow/模型进程。实际导入AstrBot 4.29.0转换器与router，文字通过框架send和原gate ACK返回。

`qq_transport.py/config.py`经定向检索无需改动；旧私有配置可兼容读取但不以其证明文件、控制秘密/端口或构建作为新路径运行依赖。保留停止采用的私有helper/适配器代码，不维护其运行兼容。没有新增provider、自动fallback、恢复或部署。

## 上次离线验证证据与边界

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

## 实际准备差额及下一步

本轮重新查实：`config/persona.md`存在；新根`.venv`、AstrBot可执行/框架Python/实例标记和基础配置、官方Snow launcher、专用QQ可执行、local/兼容单文件配置及token缺失。uv和锁定CodeBuddy程序材料可用，认证与真实模型未验。准确路径、安装/init、业务值/token交接和零模型预算核对见[TRYOUT](TRYOUT.md)，不从旧资格/长稳差额派生前置。

交付后停止并释放本session归属；用户下一轮可按[NEXT_SESSION](NEXT_SESSION.md)授权medium实际准备环境、官方包、基础实例和已提供的业务值，不重复开发已完成接入。真实启动/登录/模型群答另由用户明确授权或亲自操作；只有实际握手、事件或ACK不兼容才做必要外部适配，必须修改Snow内部时才交具体阻断与外部尝试结果给用户决定。不自动推进B/C或其他功能。

## 本轮文件与Git交付

只改6份Markdown：PROGRESS.md、工作线HANDOFF.md/TASKS.md、本任务HANDOFF.md/TRYOUT.md及新增NEXT_SESSION.md。TASKS事先登记时间/归属并写后重读；未改生产代码、测试、模板、PLAN、AGENTS、local/persona、A4、Snow内部或其他工作根。未安装或执行任何测试/回归、启停、登录/扫码、模型/群/SSH操作；只读查官方文档/源码和文件元数据/非秘密程序摘要。文档检查及Git交付结果在最终交付消息与当前Git日志中核对，runtime/local/secrets不提交。

文档核对：`git diff --check`通过；6份文档的392个本地链接、20个围栏标记及8个PowerShell代码块语法解析通过（仅解析，没有执行块中命令）。`git diff --exit-code 89b7dfae -- scripts src plugins tests adapters config/persona.md config/examples config/versions.lock.json`无差异，未增加实现/配置/测试内容；全量回归和A4均未运行。按长期授权仅提交上述6份文档，推送并核对远端后释放本session归属，下一步只按用户新指令准备材料。

## 上次实现交付

归属修改：PROGRESS、工作线HANDOFF/TASKS、本任务HANDOFF/PLAN、TRYOUT、三个上述生产文件和一个新测试文件，共10份。未改AGENTS、配置模板、local/persona、A4代码/产物/证据和Snow内部；原工作区干净，没有夹带他人修改。git diff --check及六份变更Markdown的本地链接存在性检查通过；提交推送结果见本次最终交付及Git日志。长期Git授权用于本任务交付，不代表部署或真实试用通过。

回滚仅撤销本次项目侧接入提交并保持停机，不删除材料或自动启动原根。历史[A4交接](STAGE3_A4_HANDOFF.md)及[报告](../../../../reports/lap-40-A4-implementation-2026-10-24.md)保留；原官方材料记录见[历史报告](../../../../reports/lap-40-stage3-materials-2026-10-24.md)，不当作新根当前文件已存在的证据。
