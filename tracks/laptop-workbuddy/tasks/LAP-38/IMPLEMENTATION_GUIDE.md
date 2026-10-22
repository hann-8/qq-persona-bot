# 给gpt-6.1-sol/medium的分阶段指令

返回[PLAN](PLAN.md) / [QQ精确合同](QQ_VISION_WEB_PLAN.md) / [HANDOFF](HANDOFF.md)。用户自行在会话设置选择medium；以下每段只领取一个任务，不自动串行推进。代码/离线工作无需为已授予范围重复确认；真实登录/启停/模型/消息批次按后续明确指令执行。

## 1. 建议先执行：LAP-18续作C

```text
你是gpt-6.1-sol/medium。工作目录E:\CodexWS\QQbot。
请先读AGENTS.md、PROGRESS.md、tracks/laptop-workbuddy/HANDOFF.md及TASKS.md，再读tasks/LAP-38的HANDOFF.md、PLAN.md、EVIDENCE.md和QQ_VISION_WEB_PLAN.md（路径均相对tracks/laptop-workbuddy）。

本轮只续领LAP-18阶段C：按LAP-38合同第3节修复网页正文与相关选材，复用已实现18B/06，不重做其底座。先核对git status/归属，登记本session和涉及文件，更新18 HANDOFF/TASKS/PROGRESS，写后重读；保留用户和其他session修改。

落实语义main/role=main/article优先、受控readability分支、保留代码表格及去重；新增web.selection_policy=coverage|question，默认coverage，旧配置兼容、中文旁注/模板/导出/双摘要同步。question只用当前问题本地词项选整段，真实范围与来源/最终6000字节预算、完整请求超限拒绝；不得增加LLM预处理、浏览器、提供方或后端。不要把HTTP200/出现关键词当正文质量通过。

完成默认inspect零外部动作的公共材料诊断脚本和process_host封闭PUBLIC_MATERIAL元数据，不输出URL/问题/正文/身份。SEARCH_QUALITY_PASSED保持false，除非另外有满足合同的独立真实公开检索质量报告；本轮代码/离线不自动开搜索。旧日志缺WEB行不能被写成无网络请求。

只改合同所列代码/测试/公开模板/必要文档；不修改config/local、persona、CA/代理/DNS/凭据，不启停bot、不登录、不SSH、不发QQ消息、不调用真实模型。真实公共样本读取也不自动包含在普通离线测试中；若用户另外明确同意固定公共材料批次，可按第3.4节单独0模型核验并如实记录网络波动。本轮已取得公共HTML但仍有超时，不能沿用“所有DNS非公网”结论或声称稳定全通。

运行有意义的受影响单元和实际AstrBot mentions/free×single/adaptive、web+相关功能/停言/ACK矩阵；保留06字幕/关闭兼容及28/31B/旧真人差额。不因功能已规划就开启本机配置。完成独立报告、18交接和三个索引，按Git长期授权只提交归属变更并push，核对完整远端SHA，报告保留差异。结束后不开始28R/微信。
```

## 2. 另一独立会话：LAP-28续作R

```text
你是gpt-6.1-sol/medium。工作目录E:\CodexWS\QQbot。
先读AGENTS.md、PROGRESS.md、工作线HANDOFF/TASKS，再读LAP-28/HANDOFF.md、LAP-38/PLAN.md、EVIDENCE.md和QQ_VISION_WEB_PLAN.md第4—6节；原36 I4/I5和固定六例台账合同继续适用。

只续领LAP-28阶段R，补Windows/GGUF实际路径、可信边界计算和激活工件工具。先登记session/时间/归属、更新交接/台账并重读。现有28A/C代码不重写，不开始其他任务。

按38已经定位的固定源码链实现默认本地inspect/独立固定家庭只读收集器、实际工件/模型/投影器/runner/DLL/processor允许字段；默认不SSH或读取家庭秘密。实现vision_runtime/vision_bounds、全规范化尺寸域及C++舍入语义、模板/tokenizer/输出容量负例、静态工件与短期live租约区分；修正observe工具只读独立观测，不从record抄期望路径。第一例IQ允许在已审阅静态工件/上界和明确6次授权下完成模型加载及同次实际路径被动观测，不能为补路径另暖机；路径不匹配使该例失败并停余例，不能重试。

完成prepare_vision_activation的缺项/候选/显式激活工件流程，固定路径、停机锁、双摘要重读、从真实入站/六例SQLite/当前离线签名派生；工具不开vision、不启停、不接手写passed/eligible。原unknown/cleanup/失败占次不能删除或换批次洗掉。

本轮只代码、公开审阅来源结构、自造夹具与底层替身，不跑真实收集/IQ、不SSH/模型/QQ/启停/登录、不改本机配置/人设/凭据。当前默认CLI组合未知视觉，vision=false/生产拒启保持；不自动按图片分流或切Ollama。不要把版本、API vision、源码默认4096、Mac MLX公式或一次图样成功当可信上界。

若实际参数/工件尚未获取，先完成上述独立代码/离线测试，清楚列出剩余采集字段；实际收集后所选分支适用性与数值记录回sol/max审阅，不能自行填true。明确“已实现/离线通过”和“真实路径/质量/群ACK未验”。运行受影响单元/实际框架和旧文字兼容，独立报告、不覆盖旧报告。同步交接/TASKS/PROGRESS，按长期授权commit/push并核对完整SHA，不进入其他任务。
```

## 3. 真实验证应如何另外发指令

当前不是实际授权文本，不能直接运行。用户决定执行时需给出所选后端/对象和对应批次；可以由操作者在本机忽略配置填写真实身份，不放入版本化文档或报告。

- A：只领28入站；指定自造第一张图、一个已授权测试群/发送者，正常实例按归属停机；既有intake-only最多1事件/120秒，0模型/0bot输出。使用真实已存在脚本参数，不凭本文臆造命令。
- R：只领家庭零生成采集；明确对应主机与所选模型/安装目录和进程只读范围，使用项目固定指纹SSH，在进程内使用秘密；不启动/重启/加载模型、不输出路径/凭据；交回参数与源码适用性供max审阅。
- IQ：只领一个明确后端、固定6例总最多6次；先检查实际静态工件审阅/预算/入站与台账，无资格不消费模型；首次加载可在同一次预占调用后补live观测。失败/取消/unknown占次，未决不重试，不启用/群发。
- Q：只领群闭环；一个已授权测试群、2条自造真实@图，最多2次模型，原事件有限文字投递；不借此增加图库/成员/视频/ASR。ACK通过与原生质量通过分别记。

可见能力缺失先报告固定阶段、当前证据与下一解除条件；不为补报告反复消费额度。源码与离线修复只需本任务授权，不反复为实现细节开规划或索取确认。

## 4. 微信独立项目

在新会话把工作目录选为 `E:\CodexWS\WeChatbot`，复制[微信指引](wechat-bootstrap/docs/IMPLEMENTATION_GUIDE.md)的WX-01段。它与QQ18/28是独立领取任务；不要在当前QQ实施会话顺手开发微信，也不在微信会话修改QQ共享实现。
