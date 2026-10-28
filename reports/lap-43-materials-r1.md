# LAP-43 R1材料对话实际结果

返回[PROGRESS](../PROGRESS.md) / [43交接](../tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md) / [续规](../tracks/laptop-workbuddy/tasks/LAP-43/MATERIALS_CHAT_PLAN.md)。

## 结论与交付边界

2026-10-28，session `LAP-43-materials-r1-implementation`。R1代码与适用离线验证完成，未部署；仅隔离根 `C:/Users/yutha/.codex/worktrees/lap-43-stage-a/QQbot`、分支 `codex/lap-43-stage-a`。起点HEAD/实时远端 `0734c26afeee97f8c272c52931c324779c1bf22c`，工作区干净，19:36:19（Asia/Shanghai）登记精确路径并重读，追加路径亦先登记重读。所有者/表情/记忆实现保留，必要v1材料metadata接点没有改变触发或权限。

新[机器报告](lap-43-materials-offline.json)：**74项单元、6组合78项框架通过**。两后端均为真实项目runner底层替身，provider/原事件/run_agent/模拟ACK；包括v1摘要manifest及冻结snapshot漂移拒绝、v2摘要与图片+web/记忆/候选组合。它们不是实际模型、QQ投递或图片自然性验收。旧47/74/25只作历史，旧B的0/3失败及冻结manifest/attempt不覆盖。

## 已实现

- worker封闭`error/stage/reason`，父进程校验枚举与未知字段，有限指标保留输入字节/hash/模式、阶段、耗时和清理结果，不回显异常/HTML。HTML5与普通XHTML声明在no_network HTML解析下兼容，内部子集/实体仍拒绝。无二次worker或legacy重试；原1MiB输入/2MiB输出/2秒/256MiB限制保留。元简介在同一次提取中标为link_metadata。
- 候选保留原实体，排除site/日期/操作词作为主题；多个ASCII主题需共同匹配，中文匹配有最小主题覆盖。具体页优先，已知移动/展示参数去重，业务查询参数保留；日期仅辅助排序。固定bing_rss/1搜索/5候选/2页面/2来源/15秒与网络合同不改。
- 来源分级page_excerpt/search_snippet/link_metadata。正文优先，已取得的相关实质摘要可在已知正文/普通传输故障后退化；空标题壳拒绝，URL/公网/peer/TLS/实体/访问限制拒绝不得以摘要绕过。摘要仅自己的hash/range，独立reported_at/rss_item不填成目标页published_at。
- turn time_policy区分strict_window/current_status/recent_hint/none。严格窗仍须页面日期证据；仅RSS报告时间不证明事件发生时间。未知/旧/冲突事实状态保留，现行状态与近期提示可有限利用材料。当前/近期的确定性触发保留隐私筛查、“不要联网”和双开关；`search_enabled`缺省false、`SEARCH_QUALITY_PASSED=False`。
- gist选取少量连贯主题/相关段落，短通知可通过；不再要求1200字节和四区。明确完整/逐条仍拒绝无法完整容纳的材料；显式legacy/coverage兼容。配置新增`material_goal=gist`、`search_fallback=snippet`，验证/注释/模板/导出所用规范化默认同步，不写local。
- 材料身份和范围在最终预算重选后保持；manifest携带material与独立hash、freshness与hash及time_policy。v1通过gateway/provider返回web manifest并绑定本地冻结snapshot，v2复用既有manifest/metadata校验。普通mentions继续同一来源guard；来源最多2条，不删除实际使用来源来挤预算；虚构URL拒绝，标题嵌入额外URL不传播。后缀简化，只在摘要/简介时标级。
- 固定图片政策结合配文和允许语境自然接话，明确分析/OCR/图表仍认真回答；不默认逐物讲解或播报步骤。文字与当前原生图仍同轮一次生成，config/persona.md未改；普通web材料移除退役字幕/250—500字等提示。无caption模型、图像数据库、网页长期记忆或存档。

## 实际验证与限制

最终命令（使用既有解释器，只读其运行库）：

```powershell
& E:/CodexWS/QQbot_Snowluma/runtime/astrbot-tool/astrbot/Scripts/python.exe -B -X utf8 scripts/verify_lap43_materials.py --current-persona E:/CodexWS/QQbot_Snowluma/config/persona.md
```

最终writer的单元cwd与框架工件均为临时隔离根；HTML/图/事件/假RPC、账号和凭据均自造。当前persona只在capacity进程内只读，没有输出原文、写夹具或报告。日志中的CLI_START/ACK均是替身链路，不是实际CLI/QQ。初期定向检查40项通过；合同补齐后定向42项通过，最终74/78以上述新报告为准。

首次扩展83测试选入不适用的旧42全组，出现2失败/2错误：旧配置缺失、旧来源缓存缺失、旧原生签名固定值不再匹配，以及当前43报告路径旧断言。未下载缓存或复制配置，不改旧原生签名常量；当前路径断言按新writer迁移。最终writer明确选用适用的HostedRunner替身、人工接受guard与image/member cap测试，旧本机/固定历史原生合同测试不列作当前通过。首次框架旧日期后缀断言亦暴露新合同差异，改为核metadata日期/摘要等级；v1只跑材料专用场景，不把无attention模式重放为叫名验收。

当前persona组合：CodeBuddy政策48000下，实际固定图像/成员政策+两摘要来源+7候选+成员768/记忆1536字节保守材料+1000×1000图的可见组合 **35074字节**，容纳通过；Ollama政策12288在必需输入阶段返回INPUT_TOO_LONG，未提高预算或切后端。模型原生容量计算与可见政策分账见机器报告，不能称家庭组合也可用。

来源/模式配对：保留`lap43_current_regression`及原签名全集，追加新writer/tests/[来源审阅引用](lap-43-materials-sources.json)。当前offline路径改为本轮新报告，不覆盖旧43/42报告；实际`offline_valid(settings,MODE)=true`且adapter_signature一致。新来源文件只固定引用旧已审阅native来源hash，不冒充本轮重新观察CLI。当前真实CLI契约、单次原生IQ-05与人工自然性/群ACK均未运行，生产资格仍false，不能只复制本报告/旧active部署。

## 生产、未验与后续

本session主动公共网络批次/真实CLI/真实模型/QQ/SSH/启停/登录/图库激活均0；没有读取生产群历史、记忆事实或秘密，没有写生产源码/local/图库/运行。结束只读Git确认生产根仍main `52866fe10cc654d2e12c5520f7afc5aa8bbe0179`，tracked干净；未检查或改变运行进程，不对自然业务流量作推断。7项旧A/B/视觉报告与隔离根tracked persona逐字节同HEAD；旧manifest保留原SHA和字节。

尚未证实：真实候选可用率、URL主要内容质量、实际图片回复自然性、真实CLI新契约及图像/群端到端。旧B四次失败没有HTML工件，不能据新合成结果回填原因。R2须用户另选新有限冻结批次，不能重跑旧B；R3须另授权最终冻结后的实际CLI/原生大图/人工反馈及配对部署。若R2仍缺相关候选或遇新能力缺口，保留关闭与具体失败回规划，不换provider/账号/网络。当前没有需要改变已规划后端方案的新增缺口；Ollama预算限制继续保留。

回滚：隔离分支可审阅/反向本轮提交，生产尚未合入，无需触碰生产数据。未来部署必须整体配对worker/schema/默认配置/视觉证据，先停受管实例再操作；不能整份覆盖local、删除旧证据或缩小来源签名。

## Git与停止点

只提交TASKS登记的本任务文件，差异/链接/隐私/旧证据及当前offline配对核对后commit/push本隔离分支；最终SHA以分支tip及会话回执为准，不自引用。推送后核对实时远端SHA，释放本session归属停止。不合main，不自动执行R2/R3。
