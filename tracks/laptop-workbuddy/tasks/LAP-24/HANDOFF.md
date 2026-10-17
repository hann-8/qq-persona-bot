# LAP-24：登录持久化与自然分条排查规划

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md)。继承[AGENTS](../../../../AGENTS.md)；原分条合同见[LAP-14](../LAP-14/PLAN.md)，free/表情合同见[LAP-19](../LAP-19/GROUP_CHAT_PLAN.md)。

2026-10-17 23:42（Asia/Shanghai）领取；session `LAP-24-login-natural-replies-plan`，标题“登录持久化与自然分条排查规划”。开始分支main，HEAD `5024879ad06446ae7f12cf8a2e908d44a0cc5b79`，git status干净。

范围：只读排查NapCat反复新设备验证与free固定三条现象，形成详细修正计划；本轮不改代码/人设/运行配置，不启停/登录/调用真实模型/发群消息。密码不使用、不保存、不输出；真实账号不进入文档。未自行检测/切换会话模型或推理档位，后续遵循AGENTS指定设置。

文件归属：本目录HANDOFF/PLAN、PROGRESS、工作线HANDOFF/TASKS；不写其他任务文档或本机资料。Markdown台账无锁，首次写入前已核对共享文件无未提交修改。

当前检查点：源码发送器按plan.parts遍历，不补齐最大条数；free提示词缺少adaptive分支的“不凑条数”，人设含1—3句/15—60字篇幅目标，为行为偏向的静态线索，未以真实输出复现唯一根因。本机仅白名单读取确认ollama_ssh/free/adaptive/max_bubbles=3/web=true/memes=true；不沿用旧“未启用”快照。

NapCat：现有启动器固定bundle/CWD并传配置bot.qq；安装包快速脚本说明需登录过一次。安装v4.18.38支持快速登录、密码回退和新设备验证；Windows GUID在QQ实际data root下nt_qq/global/nt_data/msf/Registry20，并经CurrentUser DPAPI保护。独立安装目录不证明实际QQ数据目录隔离；本轮未读日常QQ资料、Registry20内容或登录票据，重复验证根因未证实。

状态：2026-10-17 23:50排查/详细[PLAN](PLAN.md)完成，未实施。计划覆盖需求/非目标、当前证据、登录数据归属/快速登录/可选DPAPI密码回退、自然条数/表情合同、配置/文件/顺序、验证接受、兼容回滚、未验证能力及Git分支。后续先自然分条，再推进可证实的登录独立部分；未知原生路径控制先补证据回规划，不碰日常QQ资料。

验证：`.venv/Scripts/python.exe -m unittest discover -s tests -p test_reply_plan.py`，8项通过；用PYTHONPATH等价sys.path加入src的stdin合成脚本调用group_plan，chat数组1/2/3分别返回1/2/3，无真实模型/QQ。当前free/web/memes组合prompt 5134 UTF-8字节、不含“不凑条数”。首次stdin探测未加src路径，报ModuleNotFoundError，补入后上述3例及尺寸核对通过；未改变环境/安装依赖。5份归属文档首次164本地链接全部存在、未发现独立6—12位账号样式数字、git diff --check通过；最终链接数随完成记录增加，以末次检查为准。

并行工作：开始工作区干净，23:48看到LAP-21新增configure_bot.py/test_configure_menu.py/21 HANDOFF差异。21交接明确其session只写自己的代码/测试/README/报告/任务交接，不写或提交24共享索引；24同样不覆盖、不暂存、不提交21文件。本次8项单元不是21新增代码的验证结论。

修改仅5份：PROGRESS.md、tracks/laptop-workbuddy/HANDOFF.md、TASKS.md、本目录HANDOFF.md与PLAN.md。不提交secrets、settings、state或其他session文件。

Git交付：内容提交`293422a4d75a49f329bab891426f160c8704750c`已推送origin/main，rev-parse与ls-remote完整SHA一致；内容检查点git status干净。最终168本地链接/差异空白/本任务新增行账号样式数字检查通过。期间LAP-21已由原session独立提交`fd2a35f`，24仅提交上述5份文档；没有保留未提交的21内容。本段交付记录随后单独提交/推送并再次核对远端，最终记录提交号以本session回执为准。

下一步：用户选择AGENTS规定实施设置并明确继续后，从PLAN第5节开始领取实施/更新归属；登录目录能力缺口与真实QQ/表达接受分别补证据。需要重启/真人扫码/真实模型/群验收时先登记唯一实例执行归属，规划与Git不构成部署授权。保留LAP-18搜索及旧真人/上下文控制差额。
