# LAP-42视觉闭环：代码与离线交付检查点

返回[PROGRESS](../PROGRESS.md) / [42交接](../tracks/laptop-workbuddy/tasks/LAP-42/HANDOFF.md) / [闭环计划](../tracks/laptop-workbuddy/tasks/LAP-42/VISION_CLOSURE_PLAN.md)。2026-10-26，Asia/Shanghai；session `LAP-42-vision-closure-implementation`。

本轮实际实现阶段A并完成定向离线验证。用户在本会话选择“稍后配合，先完成代码和离线验证”，所以真实CLI/六例/启用/群图阶段等待操作者，不称识图闭环完成，不记录虚构通过。

| 证据层 | 当前结果 |
| --- | --- |
| 代码/资产/激活工具 | 已实现，当前检查点冻结；实际CLI装载前仍待验证 |
| 定向离线 | 95单元、3组合39框架场景通过；[固定报告](lap-42-vision-offline.json)，当前offline_valid=true |
| 插件执行 | 锁定Node实际运行项目TS，宿主事件模拟；完整system中英/emoji/双大括号保持，双上下文清空、拒绝/catch/回执失败/一次next通过 |
| 实际CLI契约probe | 本轮0进程、未执行；不把上述插件单测当成CLI装载证明 |
| 固定真实模型IQ | 0/6；未创建真实批次、无人工代评 |
| 人工质量 | 0/6，等待逐例明确反馈 |
| active/vision保存 | 未执行prepare/activate；vision=false，其他本机配置原字节不变 |
| 正常生产加载 | 未执行；新核对项目stopped/disconnected、model/gate/AstrBot=0，外部QQ保留 |
| 原群图像理解/ACK/显示 | 0/2、均未执行，agent未代发消息 |
| 入站复用 | 1条既有成功decoded结构仍有效、下载一次，normalize函数AST未变；未拉旧URL或新采样 |

## 实现与来源

项目所有的`adapters/codebuddy_vision_guard`三份资产仅对当前NativeImage经当次`--plugin-dir`装载。普通文字不装载。每请求在runtime/requests复制核验资产，完整system/prompt、模型/low、预算、nonce与私有回执放manifest的本次选项默认值；静态包、请求选项、派生manifest分别摘要，不自引用。

engine.create回执与既有get_available_models握手都必须先于唯一user。父进程验证资产、manifest、nonce/system摘要及当前模型容量。prompt.compose返回完整原system的一个session section；prompt.context同时清blocks和instructionFiles。项目原prompt中的记忆/成员/web/群材料保留。

turn.step检查投影、上下文、本次身份/TTL、主turn第0步、model/low、单消息及无工具形状；公开API transcript只允许原text或其user_query封套，加当前PNG的像素hash。它不声称TurnStepInput包含SDK system。probe始终不next，live最多一次；关键事件catch在未next时返回锁定空TurnStepResult，已next时沿用宿主重放语义，不再次生成。回执I/O失败不放行，父进程拒绝短路结果为AI正文。保持deny/dontAsk/strict空MCP、无续接/持久化、禁自动记忆/compact；仅视觉子进程设hook开关并移除库模式禁止值，未改全局或第三方内部。

当前组合唯一记录更新为`hosted_codebuddy_deepseek_v41_mod_v2`，绑定模型/low、CLI/node、插件包及[新来源审阅](lap-42-vision-closure-sources.json)。旧[实际结果](lap-42-vision-result.md)、[来源](lap-42-vision-sources.json)和旧28报告保留。

预算仍为原30000/2048/2048字节政策、4096视觉预留、null窗口。最终检查T+F+V+O≤C：T=原system+prompt UTF-8字节上界；V=1024；O=max(2048,当前CLI maxOutputTokens)，当前记录128000；C=min(CLI有效输入容量,1000000)。F=5692，是219已知编码文字，加锁定composer/context桥/单次wrapper审阅源码段的保守整段字节收费880+4529+64，逐项摘要及固定偏移由代码复核。原样投影移除了动态产品system，双清空移除了动态CLI材料，transcript准入拒绝额外历史/工具/文字扩张；该有限收费仅适用于此封闭请求形状，实际CLI仍须probe证明接线。它不是把219或政策2048直接当完整框架。

fitter/IQ/runner共用新kind。插件、probe/activate helper、测试、规则和来源均进入adapter_signature/offline绑定；真实IQ开始后禁止改变这些材料。若实际CLI接线暴露问题，在IQ前修复、重验并重新冻结；不沿用失效批次。

新激活工具共用完整生产校验，prepare重新读取当前offline/probe/真实decoded及持久六例，不接受手编eligible。activate在停止/配置锁、源/语义双摘要和binding稳定时备份，先原子保存已验证active，再仅替换features中的vision.enabled标量并重读load_production。失败/rollback核对两个目标拥有摘要，先恢复features再恢复active，保留并行修改；不删IQ失败/unknown、记忆、锁、ACK、图库或pending。旧lap42_rollout apply未运行。

## 已执行验证

在`E:/CodexWS/QQbot_Snowluma`：

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe scripts/verify_lap42_vision.py
.\.venv\Scripts\python.exe scripts/activate_lap42_vision.py --help
.\.venv\Scripts\python.exe scripts/probe_lap42_vision_contract.py --help
.\.venv\Scripts\python.exe scripts/observe_lap28.py --inspect
git diff --check
```

末次95单元0失败0错误、39框架场景通过；helper help及inspect、23份归属文件语法/JSON/UTF-8、248个Markdown本地链接、受测对象隐私扫描及diff检查通过。新增激活测试覆盖active先于开关、保存后校验失败恢复、候选摘要过期、并行features变动与回滚冲突保护；新质量校验拒绝仅有quality_passed而无人工来源/时间/case/回答hash的行。单元日志的模拟“Batch stopped”来自故意验证一次预占后失败不重试的临时测试根，不是真实IQ耗次。

本轮所有真实模型/群输出/启停/配置写入为0，未启动CLI模型控制进程。15份local/persona/图库/pending原字节/SHA核对无变化。私有备份、保护摘要、decoded复用检查及测试日志在忽略的state/lap42-vision-closure，未提交原始图/消息/名册/秘密/options/nonce。

## 操作者就绪后接续

先重核Git/归属、当前受管停止与运行状态、配置/绑定及真实IQ台账，不把本轮停止记录当未来现场。接续只领42；用户授权范围仍为固定6原生+最多2群图，失败/取消/unknown耗次停止，不能换batch洗过。

1. 执行`python scripts/probe_lap42_vision_contract.py --run`。正向应1本地user、0 next/远端生成；两项反向均0 user。实际回执/结果/源绑定写私有journal；出现远端生成迹象保留unknown并停止，不能再额外跑满六次。probe不要求已IQ或生产eligible。
2. probe与冻结offline有效后，用现有observer创建唯一`lap42-vision-closure-v2`批次。六例spec自造图/真值保留私有；每例一次。直接TTY评分，或明确逐例本会话反馈后忠实转录，并使用`--review-source conversation_explicit_feedback`。等待人工时不重新生成。
3. 六例全过后执行新工具`prepare --batch-id lap42-vision-closure-v2 --ingress-instance <有效私有decoded实例> --expected-binding <当前binding>`；用其返回的候选摘要执行`activate --candidate-sha256 <prepare摘要> --expected-binding <同一binding>`。目前这两项未执行，不伪造实际命令成功回执。
4. 正常受管加载一次，读实际vision=true和原模型/low/free/其他开关，受测对象从已有私有记录核对。通知就绪后操作者手工最多两条真实@自造图（清晰PNG/JPEG；优先GIF首帧）。逐条核对理解、同trace/request_key/原事件ACK和客户端显示，不旁路代发，free自然流量单列。

rollback入口为`python scripts/activate_lap42_vision.py rollback --expected-binding <配对binding>`，须停止和拥有摘要不漂移；代码回退只处理本任务配对文件，禁止reset/clean/覆盖并行修改。普通文字不依赖新插件。

本轮起点本地/实时远端`61124d583c3fba49c17d38a3ed549ccc6c50856b`；只提交已检查归属文件，交付后释放运行/原生验证归属。最终提交号及实时远端完整SHA核对见本次交付回执；Git交付不代表部署或识图完整验收。
