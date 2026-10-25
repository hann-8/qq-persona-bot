# LAP-21 受控表情图库与类型化投递

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md) / [合同](../LAP-19/GROUP_CHAT_PLAN.md)。继承AGENTS及实施指引共同边界。

## 当前接续：Snow主线7条受控表情迁移，仅规划完成

2026-10-25，session `LAP-21-snow-controlled-memes-plan`，15:46开始只读复核、15:49登记7份文档并重读。工作根`E:/CodexWS/QQbot_Snowluma`，分支`codex/lap-40-snowluma`；起点HEAD和实时远端同为`e2d9a0c082f3400904d8a4032eb01b4290ef08a8`，开始无非忽略Git差异。沿用LAP-21，未新开任务/同时领取其他实施。

已完成[详细计划](SNOW_MIGRATION_PLAN.md)及[下一轮完整medium复制指令](SNOW_MEDIUM_START.md)。旧NapCat根7条已启用登记及对应7张文件均通过现有路径/真实类型/尺寸帧数/hash校验：5 GIF+2 JPEG、4,100,086字节，7候选紧凑JSON 1134字节。新根catalog不存在/0条，两个根pending均不存在；两根memes=true、冷却0/0、free与persona保留。7份相关共用业务源码与旧根相同；缺口首先是数据未迁移，预计0生产代码修改，不能把它写成Snow真实图片成功。

本轮只改PROGRESS、工作线HANDOFF/TASKS、本交接、新PLAN/medium指令、BOT_USAGE_COMPARISON共7份Markdown；未迁移、暂存或激活数据，不改代码/local/persona，不安装、启停、登录/扫码、调用真实模型或QQ接口/群发送。源根仅本机只读，旧C根不访问；B/C停止，A4代码/产物/证据不读不验。34份本机配置/persona/目录表/pending及图库文件状态纳入前后保护摘要，最终结果在下文交付检查点记录。

下一轮由用户选择gpt-6.1-sol/medium并发送新指令，**实际复制、备份、暂存7图与原标签**，只在目标本来已停止且既有锁/摘要通过时激活目录；运行中交付已准备/未激活，不擅自停机。保留现有local/persona/模型/额度/free选择，不增配置/依赖/架构。真实启停、模型和群验收另行授权，保存/激活不等于已加载或真实通过。之后推荐记忆30→识图28，但完成本项即停止；B站字幕退出近期路线，本项不删代码。

本轮验证限只读资产解析/源文件比较、Markdown链接/围栏、保护摘要和git diff检查；不运行代码测试或旧完整矩阵。长期Git授权仅交付本任务文档并push核对远端；最终SHA与保留差异见当轮回执。交付后释放文档归属，不自动实施。

16:01交付检查点：7份Markdown、223个本地文件链接及2个围栏行检查通过；`git diff --check`通过。两根共34个保护路径的字节摘要/不存在状态前后相同，目标catalog/pending仍不存在，未迁移图片或历史。`git check-ignore`确认local、catalog、pending、迁移工件与用户图库保留忽略；仅7份任务文档进入Git，不运行代码测试/A4或真实操作。Git交付后的完整SHA、远端一致性和最终工作区状态见当轮回执，不在文档自引用提交号。

## 以下为原LAP-21历史实现/验收记录

2026-10-17 16:49（Asia/Shanghai）领取，session `LAP-21-controlled-memes` / “LAP-21受控表情实施”。main起点d70000674861b718d020d14b57f676f547b6b7dd，工作区干净。仅领取21；目标为本地inbox/library、目录表、固定收藏只读导入、单次生成候选ID、typed parts及逐条ACK/恢复，完成离线与实际框架合成回归及Git交付。

文件归属：新增meme_catalog/meme_import/media_protocol；config、onebot_gate、model_gateway、contracts、group_protocol、reply_plan/reply_delivery/task_store、persona、router/provider、配置脚本与示例、依赖锁、.gitignore、assets模板、相关测试/框架验证、README/报告及本交接/TASKS/PROGRESS/工作线交接。独占本任务文件写入，不操作运行bot。

边界：0真实收藏读取/用户图片下载/登录/启停/探活/真实模型/群发，不修改本机settings启用memes。测试仅自造图片。用户说有2收藏不是可发证据；LAP-18搜索和旧真人差额保留。

2026-10-17 17:25检查点：已实现、离线/实际框架合成通过，真实未验，未部署。207单元、136媒体框架（两后端×single/adaptive×mentions/free）、108旧群框架、26网页与90旧文本/ACK回归通过；严格入口/At转换器通过。完整实现/限制/命令/证据见[报告](../../../../reports/lap-21-2026-10-17.md)。日志在忽略state/lap21-{unit,framework,regression,g4}.log；7份安全JSON均仅合成数据。

关键决定：运行中收藏导入只写忽略暂存，停机锁/hash复核激活后再确认标签；精确QQ媒体域名仅取当前静态包证据，实际域名不符拒绝。图库/模型候选/冻结文件均受控；SDK会转base64，由事件私有回执代理验证字节hash后映射冻结file URI，再经gate/同一逐条ACK账本；不改共享SDK，不裸发。PreparedPart与新增prepared_part表保留v1文本修复，图片成功才追加语义标签；发送前抑制可为partial，未知ACK隔离/不重发，RAM重启丢弃。单轮1图，不增加模型调用。

未验证：真实账号收藏/实际媒体域名、QQ图片/GIF客户端显示、真实ACK/模型协议质量/额度、多人/长稳及全部旧真人差额。用户说明有2个收藏未查询，不能写可发。默认memes=false、本机settings/persona未改。无SSH/真实生成/群发/登录/启停/探活。LAP-18搜索缺口继续保留。

交付前检查：159个本地Markdown链接、compileall、uv lock --check（24包）、Git diff及忽略规则通过；7份JSON可解析且仅合成内容，新增assets仅2份README，无用户素材。剩余：仅等待用户指定真实范围，不启用任何新模式或推进其他任务。回滚见报告/README，回退旧文本代码前先隔离pending/unknown并配对备份。开始无用户/其他session差异，所有本轮已跟踪和新增文件归本任务；state测试工件继续忽略。

Git交付：2026-10-17，内容提交`5bb29d04c9966aa0e11f9cc6d26b3f6cc2c42eb9`已推送origin/main，git rev-parse HEAD与git ls-remote完整SHA一致，内容检查点工作区干净。42份任务文件已检查，未夹带用户/其他任务修改；本机settings、secrets、原始群消息、用户图片和state测试工件持续忽略。随后仅同步本交付记录/入口，最终记录提交SHA由main/HEAD恢复，不自引用；最终SHA在回复中核对报告。无保留的已跟踪/未跟踪差异。Git交付不等于部署或真实验收。

2026-10-17 23:32：LAP-21既有标签流程体验修复，session `LAP-21-controlled-memes` 续作。起点main/0a7fdab8c8a32e847a4678207f5580a6204b2311，工作区干净；后续LAP-22/23已交付内容保留。本轮归属：meme_catalog.py、configure_bot.py、test_memes/test_configure_menu、README及PROGRESS/TASKS/工作线与本交接。目标：编号本机预览总览、单图预览、返回重选后再编辑；预览支持未启用图片但复用路径/真实类型/hash校验，不修改激活规则。只用自造图片和模拟打开器验证；不读取真实图库/收藏、不打开用户图片、不改settings或素材标签、不启停/模型/群发。已实现/离线通过；按既有计划范围内修复处理，不另开新任务。

续作结果：菜单7“看图填写标签”提供P编号缩略图总览、编号原图查看、E确认编辑和回车重选；隐藏完整hash，列表显示名称/未命名、格式与状态，已有字段回车保留。MemeCatalog.preview允许查看禁用素材但复用真实路径/类型/hash校验，不扩大模型候选；HTML仅本机file图源、无JS/远程资源、名称转义，位于忽略state/meme-preview。保存/停机锁/激活与发送规则保持。
验证：`.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests` 215项通过（state/lap21-preview-unit.log）；菜单定向16项通过，自造红/蓝图片+模拟os.startfile验证总览编号/选择正确图编辑、取消和非法编号不写目录；禁用预览不开放候选/名称HTML转义/hash变更拒绝通过。compileall/diff检查通过。未实际打开用户图片/默认浏览器，系统关联及真人预览观感由用户重开配置窗口确认；未读真实素材、QQ或settings，未改标签/启用状态。LAP-22/23和旧真实差额保留。
Git：本次9份范围文件及报告补充将单独commit/push，并在最终回复核对完整SHA；交接记录随同提交，不自引用。没有其他session未提交差异；本机素材/设置/state继续忽略。


2026-10-17 23:44：同session续作修复首次启用留空标签后错误提示混淆。基线5024879，检测到LAP-24正在修改PROGRESS/工作线HANDOFF/TASKS及其新任务目录；本轮不写、不暂存或提交这些共享改动。已领取LAP-21内修复继续登记在本任务交接，归属仅configure_bot.py/test_configure_menu.py、README、本交接及21报告。目标：至少1标签合同不变，YES后标签为空时保留名称/语境并补填；区分预览/校验/停机保存错误。仅自造图片/模拟打开器，无真实图片/目录标签/settings读写，无bot/模型/群发。

23:44续作已实现/离线通过：标签首次为空时YES不再直接失败，保留名称/语境要求补填至少1标签，0可取消；支持中文逗号。预览异常与保存异常分别处理；字段/停机/目录竞争使用固定原因，不输出任意异常/路径内容。保存失败可R重试，草稿留在当前配置进程内，不写额外持久草稿。原启用校验/停机锁/真实素材范围保持。
验证：`.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests` 217项通过（忽略state/lap21-label-validation-unit.log）；新增自造图片+模拟打开器/停止检查覆盖用户步骤、空标签补填保留名称语境、停机保存错误准确显示且R重试不丢草稿。未操作用户真实图片/标签/运行配置或bot。compileall/diff和任务本地链接检查通过。
交付：本轮仅configure_bot.py、test_configure_menu.py、README、21报告/本交接共5文件；LAP-24所属PROGRESS、工作线HANDOFF、TASKS及其新目录均保留，不暂存或夹带。上一轮预览修复5024879已推送核对；本轮随本交接单独提交/推送并在回复核对最终SHA，不自引用。真实系统界面/当前bot状态仍未探测。
