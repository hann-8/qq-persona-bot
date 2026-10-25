# LAP-40 本轮实际材料准备结果

返回[项目入口](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [台账](../../TASKS.md) / [交接](HANDOFF.md) / [准确试用命令](TRYOUT.md)。

2026-10-25 10:49（Asia/Shanghai）；session `LAP-40-material-preparation`。仅材料准备完成，最小文字链仍待业务配置和专用QQ，真实未验；完成后停止，不部署。

## 起点与归属

工作根 `E:/CodexWS/QQbot_Snowluma`，分支 `codex/lap-40-snowluma`。开始时HEAD和重新查询的远端均为 `4de910007b4fd221af7738a365992694c012e9c1`，工作区干净；接入代码检查点仍为 `89b7dfae0efcd1949fe8289aa76ed1492bdfd8ab`。10:45在TASKS登记session、时间、文件归属并重读。没有子代理或模型切换。

## 已实际准备与核对

| 材料（均相对本根） | 实际结果 |
| --- | --- |
| `runtime/python/cpython-3.12.14-windows-x86_64-none/python.exe` | uv下载官方受管CPython 3.12.14；`.venv`及工具环境的sys.base_prefix均在本根。versions.lock中的python字段记录3.12.15，本轮按TRYOUT的3.12选择器实际取得3.12.14，未修改版本记录或锁 |
| `.venv/Scripts/python.exe` | `uv sync --frozen`安装28项锁定依赖；yaml/markdown_it/aiohttp/psutil本地导入通过；uv.lock未改 |
| `runtime/astrbot-tool/astrbot`、`runtime/astrbot-bin/astrbot.exe` | AstrBot 4.29.0、PyYAML 6.0.3、markdown-it-py 4.2.0导入/版本核对通过；150项实际包与versions.lock中AstrBot依赖逐项比较，0差异 |
| `cache/uv`、`runtime/python-bin` | uv缓存/Python下载/工具目录通过进程环境变量定向本根，没有更改全局PATH；python install使用--no-bin，不创建全局命令 |
| `runtime/astrbot/.astrbot`、`runtime/astrbot/data/plugins` | 官方`init --yes`成功，未执行run |
| `runtime/astrbot/data/cmd_config.json` | 官方配置类生成，dashboard host=127.0.0.1、port=6185核对通过；只生成基础实例，尚未接项目业务provider。初始化输出/初始密码仅留忽略的`runtime/astrbot/bootstrap.local.log` |
| `runtime/downloads/SnowLuma-v2.1.1-win-x64.zip` | 官方完整包42,694,125字节，SHA256 `c739171f95c27706767e69ba36099707c222fcec639b46f4d59689997b527772`与本轮官方asset列表一致 |
| `runtime/snowluma/v2.1.1` | 全部71个文件展开并逐项SHA256与zip内容比较通过；launcher.bat/index.mjs/node.exe/client/native均保留，没有运行launcher或构建Snow |
| `secrets/local-tokens.json` | 原先不存在，进程内生成onebot_inbound/onebot_upstream/model_gateway三个独立随机token；键、各至少32字符、互异检查通过，仅写忽略文件、不回显。不生成旧控制密钥/proof或登录凭据 |
| 锁定Node/CodeBuddy入口及`dist/codebuddy-headless.js` | 只查程序文件及headless摘要，与锁匹配；没有安装/升级、认证、生成或读取登录资料 |
| `config/persona.md` | 19,256字节，SHA256 `ff6f629d92afab7ea1c47830bd4a7e8735e944862573a90764645604e96f2804`前后相同；全程原样保留 |

首次TRYOUT命令让uv复用了全局已安装Python；随后显式下载本根Python、重新绑定本session刚创建的两个环境，最终均核实独立。首次AstrBot无约束解析得到的若干传递依赖比版本记录新；已在初始化前用现有versions.lock的150项精确约束重新安装，最终0差异，没有改锁。约束及实际包清单只留忽略的`runtime/downloads/astrbot-constraints.local.txt`与`astrbot-installed.local.json`，不把临时解析状态当成交付。

GitHub releases API遭遇共享出口限流，改读[官方asset列表](https://github.com/SnowLuma/SnowLuma/releases/expanded_assets/v2.1.1)获取摘要，再从[官方release](https://github.com/SnowLuma/SnowLuma/releases/tag/v2.1.1)下载完整包；没有使用私有产物或镜像。

## QQ下载实际阻断与手工位置

已读取[腾讯官方Windows入口](https://im.qq.com/pcqq/)和该页面引用的[官方Windows配置](https://cdn-go.cn/qq-web/im.qq.com_new/latest/rainbow/windowsConfig.js)。本轮给出的x64材料为9.9.36（2026-09-24）：

[QQ_9.9.36_260924_x64_01.exe官方下载](https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.36/release/e8e54bbb/QQ_9.9.36_260924_x64_01.exe)。

实际普通下载、带官网Referer/浏览器UA重试以及查询参数重试均返回HTTP 403；刷新官方配置仍为同一URL。另试腾讯官方备用CDN常见Windows路径返回404，没有采用该未发布地址。安装包未下载成功，不存在可验签的安装器，不能记为材料齐备。官网HTML/配置快照保留在本根忽略的`runtime/downloads/qq-*.local.*`。

操作者在浏览器从官方入口下载，保存到`E:/CodexWS/QQbot_Snowluma/runtime/downloads/QQ_9.9.36_260924_x64_01.exe`（若官网更新则保留实际新文件名），验证腾讯有效数字签名后使用正常安装界面。专用目标目录为`E:/CodexWS/QQbot_Snowluma/runtime/qq-snowluma`，期望主程序精确位置`E:/CodexWS/QQbot_Snowluma/runtime/qq-snowluma/QQ.exe`；若安装器自动增加QQ子目录，需相应调整目录选择，不能复制/覆盖旧patched或日常QQ。取消完成后自动启动。若界面只允许覆盖现有日常QQ或不能保证独立安装，停止安装并保留该阻断，不卸载日常QQ。

本轮未运行任何QQ安装器，无法保证其只写新根和不自动启动，因此未做专用安装；未碰日常QQ安装。本轮也未创建QQ.exe占位文件。官方新版本与Snow真实兼容性未验。

## 最小待提供业务值与容量

`config/local/`和`config/settings.local.yaml`重新查实均缺失。本轮没有生成模板业务local，也未读/迁移旧根配置。用户可手工放入当前完整的五份local（bot/models/chat/features/runtime.yaml），或完整兼容单文件；不要留下半套分层目录。最小需保留/提供：bot账号、授权群、管理员、既有blocked_users；mentions/free及相关输出/历史设置；CodeBuddy模型、推理、输入/开销/输出预算与超时；现用功能开关及其必要参数。五份当前文件最能避免漏项，不需要提供token正文或QQ登录资料。

业务值齐备后才将provider显式选为snowluma，私聊false，其他值不变；已有local/persona不覆盖。然后运行`config_files.py check`及TRYOUT中同router参数的compose_persona/InputBudget零模型容量核对。本轮业务值缺失，**未运行这两个依赖业务配置的校验，不记通过**；token检查独立通过。

单人设正文比16,384预算多2,872字节；加入模板2,048开销后，下界21,304，比模板至少多4,920字节，尚未计固定政策和请求封装。实际需求须按用户现用配置compose后计算。优先保留现用预算；若不足，可由用户决定提高`llm.profiles.codebuddy_cli.input_budget.context_input_limit_tokens`，或调整其`context_overhead_reserve_tokens`，输出预留另行保留；没有业务参数时不预设一个可通过的数值，不改人设、不静默调参。这是可见UTF-8保守字节预算，不是原生token或额度承诺。

## 本轮验证、边界与下一步

执行了安装、官方init/配置类生成、包导入/版本对照、官方包摘要/完整展开核对、秘密键/长度/互异检查、只读程序摘要和人设完整性核对。未新增代码/测试任务，未重跑全量测试或A4；39项合成通过仍仅为历史证据。本轮没有manage start/stop/status、AstrBot run、QQ/Snow启动、登录/扫码、CLI认证/真实生成、SSH或群消息操作；也未探活其他根。旧B/C停止，A4原样保留且未复核/重跑/修改。

后续顺序：用户放入当前业务配置及完成专用QQ下载/独立安装→仅本地check/容量核对→用户另行明确授权真实启停、接通后按既有规则模型/群答，并亲自启动QQ/Snow和登录→按[TRYOUT](TRYOUT.md#明确授权真实启动后项目与官方端)执行start-text/status与一次目标群新真实@文字→按[停止步骤](TRYOUT.md#一次目标群文字与准确停止)结束。保留free时其他新消息也可能触发，不能将启动视为只有一次调用授权，不能擅自改mentions/free。

文档交付归属：PROGRESS、工作线HANDOFF/TASKS、本任务HANDOFF/TRYOUT/MATERIALS共6份。runtime/local/secrets/persona均不提交，uv.lock/versions.lock与代码无差异。Git内容提交/推送的最终SHA以当前Git日志、远端核对及最终交付消息为准；完成后释放session归属，不自动部署或恢复其他功能。

文档交付检查：6份文档390个本地链接/围栏核对通过，TRYOUT的7段PowerShell仅语法解析通过（0错误）；git diff --check通过。代码/scripts/plugins/tests/adapters/persona/uv.lock/versions.lock与起点无差异；环境、实例日志、官方包及token路径均经git check-ignore核对忽略。未将本地导入或材料完整性核对晋升为真实通道/生成/群验收。
