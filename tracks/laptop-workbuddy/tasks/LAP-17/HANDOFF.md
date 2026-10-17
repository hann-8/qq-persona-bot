# LAP-17 本地后端与配置切换

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [合同](../LAP-19/PLAN.md) / [报告](../../../../reports/lap-17-2026-10-17.md)。继承AGENTS及LAP-19共同边界。

## 当前检查点

2026-10-17 15:52（Asia/Shanghai）。状态：已实现、离线/实际框架合成通过、实际SSH零推理元数据通过；真实生成/QQ/完整验收未做，未部署或切换本机后端。仅领取17，18/20/21等待用户后续指令。

session `LAP-17-dual-profile-implementation` / “LAP-17双profile与SSH原生后端实施”，15:35登记；main起点6a2f244，开始工作区干净，没有其他session修改。Git已获授权，当前待内容审阅提交/推送及远端SHA核对，完成后同步交付记录。

## 已完成

- schema3与两profile、resolve_backend、旧schema1/2逐值内存迁移、停机/锁/hash/备份/原子保存；冲突拒绝。已只读核对真实本机旧模型/强度/超时/预算/output/access逐值保留，settings文件hash不变；未输出具体值。
- 配置cmd保持原入口，新增后端与连接页、当前profile编辑、独立本地参数、显式DPAPI连接初始化、只读元数据与手动解除未知状态。中文空格/外部CWD的真实cmd在临时夹具中来回切换通过。
- BackendResult及数值usage/unknown credits、CLI兼容，SSH固定既有指纹在认证前核验/只开direct-tcpip回环11434、原生单POST及请求级参数、有界预检/读取/取消。修复实际Paramiko通道的HTTP分块/CRLF和Connection:close兼容，新增反例测试。
- 完整原生JSON字节预算、共享会话版本/参数fingerprint、状态分层、本地model启动等待30秒；远端结果未知标记在POST前持久化，排队及重启后生成阻断，不自动重试/fallback或杀远端进程。
- 未修改角色正文；严格真实@、黑名单前置、私聊关闭、单并发、CLI工具隔离、LAP-16 ACK/部分交付/恢复保留。

## 修改文件归属

- `src/qqbot_gateway/config.py`、`backends.py`、`token_budget.py`、`model_gateway.py`、`ssh_transport.py`、`ollama_ssh_runner.py`、`workbuddy_cli_runner.py`、`persona.py`、`errors.py`。
- `plugins/qq_router/main.py`；`scripts/configure_bot.py`、`configure_astrbot.py`、`manage.py`；`verify_lap17.py`及可注入runner/独立报告的`verify_lap11.py`、`verify_lap16.py`；旧CLI专用`verify_lap10.py`/`verify_g4_memory.py`只改schema3兼容，未执行其真实路径。
- `config/settings.example.yaml`、`config/versions.lock.json`（新增SSH依赖记录，旧CLI hash不变）、`pyproject.toml`/`uv.lock`。
- `tests/test_local_backend.py`新增22项；`test_config.py`/`test_configure_menu.py`canonical路径断言与`test_cli_runner.py`结果对象兼容。
- README、reports/lap-17报告与5份安全JSON、PROGRESS、本任务/两条工作线HANDOFF和TASKS。所有修改归本任务，没有夹带用户变更。

## 验证与证据

1. `.venv/Scripts/python.exe -m unittest discover -s tests`：146项通过（原124+新增22），本机日志`state/lap17-unit.log`。
2. 框架Python运行`scripts/verify_lap17.py --backend <codebuddy_cli|ollama_ssh> --mode <single|adaptive>`四组合：single各5、adaptive各40，共90组，真实runner+实际AstrBot/SDK/保存/发送，底层模型/SSH仅合成替身。各adaptive含原SDK/gate5组ACK、并发与启动恢复；context_switch验证切后端/活动参数新建、非活动保留和旧历史不删。报告链接见[总报告](../../../../reports/lap-17-2026-10-17.md)。
3. 实际框架`verify_g4_routing.py` / `verify_g4_adapter.py`（state scratch CWD）：本人/跨人跨群/黑名单管理员/无At和引用At/私聊/预算/停止/At转换器通过，0网络或真实模型。
4. `runtime/tools/uv.exe lock --check` / compileall / git diff --check通过，23包锁定。7份Markdown/145个本地链接通过；私密值0匹配、依赖锁与已安装版本一致，最终差异检查通过。
5. 15:44:26新实现实际SSH元数据通过：固定旧指纹、Ollama0.40.5、指定tag/digest一致、think:false元数据支持，最新ps所选模型未加载。最终一次认证/4元数据请求；此前5次只读诊断定位通道HTTP兼容问题，总6次连接均0生成、无远程命令/写入。证据[安全元数据](../../../../reports/lap-17-metadata-2026-10-17.json)与忽略state/lap17-metadata.local.json；不把标称窗口或ps作为本次生成/忙闲证据。

## 未验与下一步

本机settings/persona/长期运行连接JSON未修改；没有启停/探活或登录bot、真实CLI/Ollama生成、群发、PC安装/下载/全局参数/服务修改。当前bot运行状态未知。项目.venv新增SSH依赖，家庭凭据/原始证据/配置和测试scratch继续忽略。

真实think:false、num_ctx实际生效/资源/速度/风格、single/adaptive/两轮记忆、取消后远端是否停止、QQ/多人/长稳及旧LAP-10/09/13/15/16/原真人差额仍未验。另由用户明确调用上限/群/时段/执行归属；不为补验自动消费额度。

回滚：操作者停机选保留CLI profile再启动，不删模型/旧历史/SSH资料。远端未知标记须独立核对并停机显式确认，不能以ps判断。回退schema2代码先处理/隔离pending发送与远端未知请求，恢复同一检查点配置备份并保留schema3/新历史。完整操作见README/报告。

下一步仅完成本任务Git交付；完成后停止，不开始18/20/21。后续真实启用：操作者停机初始化JSON→只读检查→核对digest→手动选择/重启；本轮没有执行这些步骤。
