# LAP-13：配置控制台与启动提示交互

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md)。继承[AGENTS](../../../../AGENTS.md)；上层规格[UX_PLAN](../../UX_PLAN.md)，本任务详细设计见[PLAN](PLAN.md)。

状态：已实现/离线通过，真实终端视觉接受待用户体验。用户后续明确“执行吧”授权实施；未声称自动核验或切换模型档位。2026-10-17 09:54（Asia/Shanghai）领取。session“LAP-13控制台交互规划”。本轮用户要求改善菜单堆叠、输入提示和每次启动的NapCat地址；按AGENTS先落盘详细方案，再由gpt-6.1-sol/medium按用户后续实施指令执行。不声称自动检测或切换模型/推理档位。

本轮文件归属：本任务PLAN/HANDOFF、PROGRESS、TASKS、工作线HANDOFF、UX_PLAN的增量索引；仅规划文档。后续实施范围：scripts/configure_bot.py、manage.py，必要的配置cmd编码/终端环境处理，tests及README/验收文档，不改后端/触发/模型预算算法。

开始检查点：基线0d9d309，发现用户未提交config/persona.md（增加245行），内容不属于本任务，不读取正文、不改写、不纳入交付提交。用户粘贴的真实群号不写入文档，预算现值只视为用户提供的现场信息，不读取或重置本机配置。

目标/退出条件：详细约定清屏/结果页、分组菜单、每项名称/类型/范围/单位与示例、能力驱动的强度编号映射、停止后写入与原子保存兼容、启动及重复启动始终展示NapCat地址；验证用临时配置和替身，不启停bot、不登录/群发/调用模型。写后重读领取记录，再完成方案与索引同步。

最终规划检查点：2026-10-17 09:56（Asia/Shanghai）。[PLAN](PLAN.md)已覆盖需求/非目标、当前代码证据、页面合同/清屏回退/结果等待、逐项输入名称与描述、强度编号映射、启动地址所有分支、涉及文件/顺序、C01—08验证、兼容/回滚及未验能力。预算语义保持UTF-8保守计数，实际用户配置不回默认；LAP-10缺口及其他任务差额保留。

本轮只修改本任务两份文档及PROGRESS/TASKS/工作线/UX_PLAN索引，没有改代码、运行配置、人设或服务状态，没有模型/群消息/登录；用户persona增加245行仍保留。旧97项测试未重跑，不作新交互证据。下一步由gpt-6.1-sol/medium按用户后续“实施LAP-13”指令领取本任务实施阶段，先重读本交接/PLAN并核对归属与git status；不要覆盖或提交用户人设变更。会话模型档位按用户设置，不伪称已自动核验/切换。

文档核对：87个本地链接全部存在，git diff --check通过。config/persona.md仍仅为用户原有245行增量；本轮交付仅6份规划/索引文档。

实施领取：2026-10-17 09:58（Asia/Shanghai），session“LAP-13配置控制台交互实施”，基线578cf84；拥有scripts/configure_bot.py、manage.py、可新增console_ui.py、配置机器人.cmd、tests及必要文档写入。保留用户config/persona.md，开始SHA256：c55c51db10a0d9c3d147638763ffa10e16c0be9daffa4ec80bfd4037417120b7。不启停或探活真实bot，测试仅临时配置/替身。沿用用户提交/推送授权。

最终实施检查点：2026-10-17 10:02（Asia/Shanghai）。已完成分组/清屏回退/结果等待/逐项说明/强度映射/安全错误提示/编辑摘要复核；启动公共收尾固定URL，失败标可能不可访问；配置cmd环境和外部CWD导入兼容。修改scripts/configure_bot.py、console_ui.py、manage.py、配置机器人.cmd、tests/test_configure_menu.py/test_lifecycle.py、README及进度/验收/本交接、reports/lap-13*。未改配置schema、能力快照、预算算法或任何真实配置。

证据：[实施报告](../../../../reports/lap-13-2026-10-17.md) / [入口结构化结果](../../../../reports/lap-13-console-2026-10-17.json)。命令：项目Python `-m unittest discover -s tests -q`，108项通过；末次只补解除屏蔽路径后菜单10项单独通过。实际配置cmd在中文空格路径/外部CWD、清除注入PYTHONPATH下走临时配置菜单及show通过。真实TTY无截图/未人工接受，不冒充完整视觉验收。

用户persona内容SHA256核对不变；只会选择性提交本任务文件。未探活/启停真实bot、登录、群发/模型调用或打开浏览器，没有改settings.local；不声称当前服务仍停机。下一步用户重新打开配置cmd体验，启动URL提示下次自行启动生效；菜单更新无需重启bot。LAP-10与旧真人验收差额保留，不自动领取其他任务。

最终文档核对：117个本地链接存在、git diff --check通过，清屏不可用回退及解除黑名单路径的末次菜单10项通过。用户persona的SHA256与实施领取一致，保留未提交。

LAP-13实现提交`ee7f2d4`已成功推送origin/main；随后仅同步交付检查点。108项全套及末次菜单10项通过，117个链接/差异检查通过；未操作真实bot，用户persona仍保持原有未提交改动。
