# LAP-43 原生联网最小接线：实际交付

返回[43交接](../tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md) / [PROGRESS](../PROGRESS.md)。2026-10-28，session `LAP-43-native-web-implementation`，20:39:53+08:00登记并重读归属。起点本地/实时远端 `9edbbbcf47e49188da0d8f269027caa4fc365bd0`，工作树开始干净；只在 `codex/lap-43-stage-a` 实施。

## 已实现及生效边界

普通CodeBuddy文字会话按 `web.provider=codebuddy_native`、`web.enabled`提供WebFetch；`search_enabled`为独立Search开关，但当前Search供给未证实，代码保持不开放，即使配置true也不添加工具。只交付URL阅读接线，不声称实际Fetch/Search成功。默认两个开关均false，旧bing_rss只兼容读取，不接运行链。本轮不写任何生产local。

runner同步派生 `--tools WebFetch`、相同 `--allowedTools` 和移除WebFetch后的当次deny；保留dontAsk、strict空MCP、setting-sources none、原账号/model/effort及请求timeout。有工具时最多8 CLI代理轮次，否则2；单次CLI尝试/无外层重试。内部可以多次模型推理/Fetch，不能当作一次远端生成、HTTP次数或credits上限；原起始输入预算不覆盖工具后的全部上下文。

ResultParser核对init的准确工具集合、model和空MCP；只接受已许可工具的assistant tool_use/tool_call、对应user tool_result，拒绝其他工具、重复/孤立结果和未完工具终端。中间文字/工具JSON不返回QQ，仅最终成功result走原gateway协议、原event发送与ACK。工具失败可以作为对应tool_result留给当前CLI会话，外层不补试。输出字节/事件上限保持。

移除gateway的WebRunner/Retriever外层包装，Ollama仍直接聊天、没有联网、不自动切换。当前问题的禁网要求从冻结target读取，不用旧web_anchor或旧历史判断；ambient仍受allow_ambient_web。图片guard继续原无工具/2轮路径，R1自然图片政策保留，图+URL不得声称完成网页阅读。实例停机标记检查移入CLI执行边界/等待/最终返回，取消仍由既有受管清理处理；暂停发言的最终发送guard未变。

## 删除与最小兼容保留

删除6个仅服务已停止路线的文件：`scripts/probe_lap43_search.py`、`scripts/probe_lap43_materials.py`、`scripts/verify_lap43_materials.py`、`tests/test_lap43_search_probe.py`、`tests/test_lap43_materials_probe.py`、`tests/test_lap43_materials.py`。复用原`verify_lap43.py`和框架Harness，撤掉其自建材料矩阵/日期来源断言，改为原生过程与最终投递验证。模板和配置页只展示provider/enabled/search_enabled；旧自建字段保留兼容解析/校验，已说明不控制原生工具。

引用审查采用 `rg -n 'web_retrieval|web_policy|web_freshness|web_extractor|html_worker|evidence_selection' src scripts tests`：`turn_v2`仍用日期parse和manifest校验，`group_protocol`仍校验manifest；`meme_import`经web_retrieval兼容导出公共网络类型，`process_host`仍用safe_material_log；历史18/27/28等工具也导入原Retrieval/worker/选材接口。因此这些共享兼容模块暂留，原生生产聊天已不调用它们，不再修Bing/worker/gist/日期质量链，不把保留当第二条运行路线。图片用的PublicHTTP/public_network、配置/vision校验、owner/暂停/输入/表情/记忆模块及历史实际报告完全保留。

## 离线验证及失败过程

最终命令：

```powershell
& E:/CodexWS/QQbot_Snowluma/runtime/astrbot-tool/astrbot/Scripts/python.exe -B -X utf8 scripts/verify_lap43.py
```

21项单元、62项实际框架场景通过。单元包括原生工具参数/deny/low、独立Search开关的拒绝、init/多轮中间工具/最终结果、其他工具/MCP拒绝、禁网、原无工具、图+URL无工具、控制只读握手替身、超时/取消/停机的单尝试清理。框架使用既有Harness、实际runner/gateway/AstrBot/provider、合成CLI/RPC与事件ACK：CodeBuddy和Ollama各31项，含原event最终发送、仅最终result不泄漏过程、唯一owner、暂停/恢复后旧结果、分条/图片/受控@最终guard和排队取消。没有真实QQ ACK或原生Fetch结果。

配置页另定向运行 `test_configure_menu.MenuTests` 的 `test_web_menu_preserves_profiles_and_never_probes`、`test_meme_menu_explicit_enable_preserves_profiles`、`test_explicit_free_menu_preserves_profiles_and_units`：3/3通过，保存仅临时配置，保留profile/其他菜单。

初选旧视觉guard矩阵时出现1失败/25错误，核心原因是安装CLI artifact已漂移；这不是本轮修复通过的项目。另有替身默认编码读中文、首次选择缺AstrBot的Python环境、移除wrapper后的旧夹具拦截/metadata断言不匹配，已分别修正UTF-8夹具、选择既有AstrBot运行库和直接runner夹具。曾有配置菜单批量文本替换误及其他菜单，在差异审阅中已恢复，随后上述3项菜单回归通过。旧guard测试未删/未改，也未冒称完整视觉回归通过。

本轮最终日志在忽略的 `state/lap43-native-web/validation.log`；机器结果见[offline](lap-43-native-web-offline.json)，来源/缺口见[sources](lap-43-native-web-sources.json)。0真实CLI、0模型、0QQ、0SSH、0公共probe、0启停/安装/登录/图库激活。回环HTTP与子进程均为临时替身，不等同真实能力。

## 视觉配对和真实缺口

沿现有 `lap43_current_regression` 模式，将offline读取路径、writer、tests和source audit成组改为本轮native文件；签名仍包含全部gateway源码及既有图片guard/审阅源，未缩小集合。旧42/A/R1/R2报告和active不重写。当前新offline_valid=true；分别篡改adapter/writer/tests/source四个hash均拒绝，旧offline不能匹配新源码。

当前安装包只读显示 **CodeBuddy 2.177.1**，bundle SHA `f6a04da8f7dbe9eed2fd0651c9a8d098b71a45263dcd422ac97d2e691e41dc38`，项目仍锁定2.168.0 / `13e6dd30a22d2f11857675193f909a2ccb935da67a067f580fcfe764e474ff60`。现有template_diagnostics返回`CLI_MOD_FRAMEWORK_SOURCE_CHANGED`，正常runner构造也会因artifact不匹配拒绝。没有更新lock、CLI、框架源码或旧视觉凭证。框架回归明确只构造合成runner，不用mock把这个真实检查改成通过；offline报告保留该诊断及production_eligible=false。

静态安装包确认WebFetch/WebSearch名字、参数与工具事件封套，未执行当前账号/model/headless会话，故Search供给仍未证实、保持不开。下一轮用户选中运行前，先明确处理实际CLI版本与锁定审阅不匹配，再做当前契约/新binding图片配对和实际URL/原event ACK；不能直接部署本分支或翻旧active放行。本轮不追加旧B/R2批次或新搜索后端，不保证真实语义/页面质量、长稳或成本。

## 本轮文件清单与回滚

以下均为登记归属文件；本轮新增/修改/删除以隔离提交可审阅差异为准：

- 修改：`PROGRESS.md`
- 修改：`config/README.md`
- 修改：`config/examples/features.yaml`
- 修改：`config/settings.example.yaml`
- 新增：`reports/lap-43-native-web-offline.json`
- 新增：`reports/lap-43-native-web-sources.json`
- 新增：`reports/lap-43-native-web.md`
- 修改：`scripts/configure_bot.py`
- 删除：`scripts/probe_lap43_materials.py`
- 删除：`scripts/probe_lap43_search.py`
- 修改：`scripts/verify_lap43.py`
- 修改：`scripts/verify_lap43_framework.py`
- 删除：`scripts/verify_lap43_materials.py`
- 修改：`src/qqbot_gateway/backends.py`
- 修改：`src/qqbot_gateway/config_comments.py`
- 修改：`src/qqbot_gateway/model_gateway.py`
- 修改：`src/qqbot_gateway/persona.py`
- 修改：`src/qqbot_gateway/vision.py`
- 修改：`src/qqbot_gateway/vision_capabilities.py`
- 修改：`src/qqbot_gateway/web_policy.py`
- 修改：`src/qqbot_gateway/workbuddy_cli_runner.py`
- 修改：`tests/test_configure_menu.py`
- 删除：`tests/test_lap43_materials.py`
- 删除：`tests/test_lap43_materials_probe.py`
- 删除：`tests/test_lap43_search_probe.py`
- 新增：`tests/test_native_web.py`
- 修改：`tracks/laptop-workbuddy/HANDOFF.md`
- 修改：`tracks/laptop-workbuddy/TASKS.md`
- 修改：`tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md`

回滚先禁用本次原生工具许可（web.enabled/search_enabled=false），恢复无工具聊天；若未来部署，源码/配置/visual active必须按既有43事务整组回退。原账号/model/low/persona/群资料不动，不自动切旧Bing或其他后端。本轮只提交已检查任务文件、push隔离分支并核对远端后释放归属停止；最终提交号以分支tip/会话回执为准，不合生产main。
