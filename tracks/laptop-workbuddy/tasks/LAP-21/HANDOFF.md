# LAP-21 受控表情图库与类型化投递

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md) / [合同](../LAP-19/GROUP_CHAT_PLAN.md)。继承AGENTS及实施指引共同边界。

2026-10-17 16:49（Asia/Shanghai）领取，session `LAP-21-controlled-memes` / “LAP-21受控表情实施”。main起点d70000674861b718d020d14b57f676f547b6b7dd，工作区干净。仅领取21；目标为本地inbox/library、目录表、固定收藏只读导入、单次生成候选ID、typed parts及逐条ACK/恢复，完成离线与实际框架合成回归及Git交付。

文件归属：新增meme_catalog/meme_import/media_protocol；config、onebot_gate、model_gateway、contracts、group_protocol、reply_plan/reply_delivery/task_store、persona、router/provider、配置脚本与示例、依赖锁、.gitignore、assets模板、相关测试/框架验证、README/报告及本交接/TASKS/PROGRESS/工作线交接。独占本任务文件写入，不操作运行bot。

边界：0真实收藏读取/用户图片下载/登录/启停/探活/真实模型/群发，不修改本机settings启用memes。测试仅自造图片。用户说有2收藏不是可发证据；LAP-18搜索和旧真人差额保留。

2026-10-17 17:25检查点：已实现、离线/实际框架合成通过，真实未验，未部署。207单元、136媒体框架（两后端×single/adaptive×mentions/free）、108旧群框架、26网页与90旧文本/ACK回归通过；严格入口/At转换器通过。完整实现/限制/命令/证据见[报告](../../../../reports/lap-21-2026-10-17.md)。日志在忽略state/lap21-{unit,framework,regression,g4}.log；7份安全JSON均仅合成数据。

关键决定：运行中收藏导入只写忽略暂存，停机锁/hash复核激活后再确认标签；精确QQ媒体域名仅取当前静态包证据，实际域名不符拒绝。图库/模型候选/冻结文件均受控；SDK会转base64，由事件私有回执代理验证字节hash后映射冻结file URI，再经gate/同一逐条ACK账本；不改共享SDK，不裸发。PreparedPart与新增prepared_part表保留v1文本修复，图片成功才追加语义标签；发送前抑制可为partial，未知ACK隔离/不重发，RAM重启丢弃。单轮1图，不增加模型调用。

未验证：真实账号收藏/实际媒体域名、QQ图片/GIF客户端显示、真实ACK/模型协议质量/额度、多人/长稳及全部旧真人差额。用户说明有2个收藏未查询，不能写可发。默认memes=false、本机settings/persona未改。无SSH/真实生成/群发/登录/启停/探活。LAP-18搜索缺口继续保留。

交付前检查：159个本地Markdown链接、compileall、uv lock --check（24包）、Git diff及忽略规则通过；7份JSON可解析且仅合成内容，新增assets仅2份README，无用户素材。剩余：仅等待用户指定真实范围，不启用任何新模式或推进其他任务。回滚见报告/README，回退旧文本代码前先隔离pending/unknown并配对备份。开始无用户/其他session差异，所有本轮已跟踪和新增文件归本任务；state测试工件继续忽略。

Git交付：2026-10-17，内容提交`5bb29d04c9966aa0e11f9cc6d26b3f6cc2c42eb9`已推送origin/main，git rev-parse HEAD与git ls-remote完整SHA一致，内容检查点工作区干净。42份任务文件已检查，未夹带用户/其他任务修改；本机settings、secrets、原始群消息、用户图片和state测试工件持续忽略。随后仅同步本交付记录/入口，最终记录提交SHA由main/HEAD恢复，不自引用；最终SHA在回复中核对报告。无保留的已跟踪/未跟踪差异。Git交付不等于部署或真实验收。
