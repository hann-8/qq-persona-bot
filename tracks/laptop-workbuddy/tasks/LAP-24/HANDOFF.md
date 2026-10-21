# LAP-24：自然分条与登录独立部分交接

## 2026-10-21自动登录规划续作

2026-10-21 18:56（Asia/Shanghai）领取；session `LAP-24-autostart-login-plan` / “保存登录状态与开机自动登录规划”，基线`main/3e4122b4e9046f154ff9fa82d2be317413e69056`。用户指定本会话承担sol/max规划；不自行检测或切换设置。只读研究并形成[AUTOSTART_PLAN](AUTOSTART_PLAN.md)和[实施指引](AUTOSTART_IMPLEMENTATION_GUIDE.md)，区分QQ会话保存、设备信任、密码回退和Windows触发；本轮不实施、不启停或登录运行中的bot。

归属8份文档：PROGRESS、工作线HANDOFF/TASKS、本HANDOFF、旧PLAN/IMPLEMENTATION_GUIDE仅加续作入口、新AUTOSTART_PLAN/AUTOSTART_IMPLEMENTATION_GUIDE。保留`config/persona.md`未提交差异；不触及本机配置/凭据、设备文件内容、日常QQ、SSH、模型或群消息。旧自然分条交付与登录缺口分别保留。

2026-10-21 19:15（Asia/Shanghai）检查点：详细规划完成，**未实施/未部署/免扫码未验收**。原生会话优先，WebUI管理Cookie/密码回退不能替代QQ设备信任；双来源脱敏诊断、独立管理token、受控login-check-only、锁外有界等待/实例状态、自有Startup与备用独立环境分支均已明确。原生目录位于项目外及Registry20旧mtime只采用本会话前段元数据证据，不推断共享、GUID有效或根因。新规划仍无经验证的Windows原生路径覆盖，未解除旧data_scope。

下一步：用户设置medium并按新指引第4节只实施P1/P3代码/离线交付；不重做自然分条。真实D/R1/R2需另定唯一负责人并阻断群转发；正式R3正常free运行须另定允许的真实触发范围，不承诺全程0生成。两次普通重启+一次Windows重启免人工先通过，才能安装Startup；失败按分支回规划，不重复填密/重置GUID/自动换环境。

验证：只读核对固定bundle哈希/符号、现有锁/状态/配置入口及官方资料；8份文档316个本地链接全部存在、代码围栏配对、归属检查与git diff --check通过；新增文本未含本机真实QQ/访问控制ID，persona原字节哈希未变。没有新增运行探活或单元/框架测试；前段在线观察和18日248/324分别是既有证据，不算本次新验收。0本轮真实启停/认证/登录/模型/QQ/SSH/本机配置修改，Git待交付。

## 2026-10-18实施检查点（历史）

2026-10-18 00:20（Asia/Shanghai）领取；session `LAP-24-natural-login-implementation`，标题“LAP-24自然分条与登录独立部分实施”。开始main/`d319811`，工作区干净。仅实施本任务：先统一自然分条，再核对数据归属并实现DPAPI配置/固定WebUI单次回退；离线及实际框架合成验证后文档、commit/push。无真实启停/认证/登录/模型/群消息，不填本机凭据或运行配置。

文件独占归属：`src/qqbot_gateway/persona.py`、`config/persona.md`、新增`napcat_login.py`/`napcat_login_client.py`、`scripts/manage.py`、`scripts/configure_bot.py`、`scripts/verify_lap24.py`、相关tests、README、LAP-24报告及本HANDOFF、PROGRESS、工作线HANDOFF/TASKS。仅必要时扩充既有框架verify函数的合成场景；不修改其他任务交接/旧报告。数据目录未证实则保持unverified、不启用、不迁移。会话模型/档位由用户设置，不声称自动检测或切换。

当前检查点（2026-10-18 00:35 Asia/Shanghai）：B自然分条及A登录独立代码已实现/离线通过；**数据归属/原生报告接入未完成，生产回退保持unverified且不能启用；真实登录/表达/QQ及完整验收未通过。** 没有启停或认证真实bot，未填写本机凭据/运行配置，未读/用聊天密码。开始工作区干净，至今仅本任务归属差异，未发现其他会话改动。

实现：共享表达规则覆盖全部提前返回分支、移除人设最低篇幅暗示、max=1无多条指令，普通single纯文本保留；DPAPI严格密文schema/无回显TTY配置、配置锁/停机/双摘要/fsync后复核、固定WebUI有界客户端、先记账后POST/同实例不重试、所有受管子进程环境清理、只读状态和新建start接入。生产协议/发送/历史代码未改。新增实现文件为napcat_login.py、napcat_login_client.py；既有verify_lap20/21只扩充可选合成场景/full_lifecycle，不覆写旧报告。

验证：根目录`.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests`，**248项通过**（24.155秒，最终代码版本）；含新登录/HTTP/提示组合/菜单及既有生命周期、process_host、ACK/恢复。实际框架从`runtime/astrbot`运行`& 'E:\CodexWS\QQbot\runtime\astrbot-tool\astrbot\Scripts\python.exe' -X utf8 'E:\CodexWS\QQbot\scripts\verify_lap24.py'`，**12组合324用例通过**（群148、mentions媒体84、free媒体92）。两后端实际runner底层替身+真实run_agent，不手动补链；仅动态端口假管理HTTP/合成秘密和图片。详见[报告](../../../../reports/lap-24-2026-10-18.md)/[JSON](../../../../reports/lap-24-framework-offline.json)。24种web开启的提示组合4298..5839 UTF-8字节，未放大输入预算；生产两处compose结果一致。测试日志中启停字样属于临时根/进程替身，不能算真实操作。

归属核对：锁定NapCat包hash与PLAN相同；只读取项目账本的PID/创建时间，2条NapCat身份当时均匹配存活，未读取命令行/账号库/票据/Registry20。无项目原生身份记录，原生data root未证实。data_scope要求可信原生报告与路径/bundle/Windows身份记录复核，但生产启动器尚无已验证报告读取方法；**本次明确不伪造记录、不启用、不迁移、不重置GUID。** 可选配置/客户端交付不等于登录持久化修复完成。

剩余顺序：先回规划补原生路径/归属证据和报告接入方法，再由用户另行指定唯一实例负责人/启停与登录范围，操作者本机录入并做正常重启观察；表达接受另指定后端/请求预算/群范围。旧LAP-10/18及其他真人差额保留。回滚不删除设备/历史/图库/pending/unknown及登录尝试账本；无明文降级或删除账本重试。

最终文件：PROGRESS、README、工作线HANDOFF/TASKS、本HANDOFF、config/persona.md、src/qqbot_gateway/{persona,napcat_login,napcat_login_client}.py、scripts/{manage,configure_bot,verify_lap20,verify_lap21,verify_lap24}.py、tests/{test_lap24,test_napcat_login_http}.py、reports/lap-24-2026-10-18.md与lap-24-framework-offline.json。Git交付检查点见下段；忽略的测试日志未纳入，其他任务文档/旧报告/本机配置无改动。

交付检查：最终192个本地Markdown链接均存在，git diff --check通过；18份归属文件，未发现其他session差异。远端main在提交前仍为开始SHA `d3198117f5868709b12da9d9d1c7be01a1665597`。2026-10-18 00:37（Asia/Shanghai），内容提交`b8cc29901c5893eae9f18a0db495d08b0916e5ec`已推送origin/main，rev-parse与ls-remote完整SHA相同，检查点工作区干净。随后仅同步本交付记录并独立提交/推送，最终记录提交SHA以会话回执为准。Git交付不等于部署或真实验收；本机忽略配置/凭据未改，合成测试日志保留忽略。

以下是规划阶段历史记录，当前实施状态以上为准。

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md) / [medium实施指引](IMPLEMENTATION_GUIDE.md)。继承[AGENTS](../../../../AGENTS.md)；原分条合同见[LAP-14](../LAP-14/PLAN.md)，free/表情合同见[LAP-19](../LAP-19/GROUP_CHAT_PLAN.md)。

2026-10-17 23:42（Asia/Shanghai）领取；session `LAP-24-login-natural-replies-plan`，标题“登录持久化与自然分条排查规划”。开始分支main，HEAD `5024879ad06446ae7f12cf8a2e908d44a0cc5b79`，git status干净。

范围：只读排查NapCat反复新设备验证与free固定三条现象，形成详细修正计划；本轮不改代码/人设/运行配置，不启停/登录/调用真实模型/发群消息。密码不使用、不保存、不输出；真实账号不进入文档。未自行检测/切换会话模型或推理档位，后续遵循AGENTS指定设置。

文件归属：本目录HANDOFF/PLAN、PROGRESS、工作线HANDOFF/TASKS；不写其他任务文档或本机资料。Markdown台账无锁，首次写入前已核对共享文件无未提交修改。

2026-10-18续领：用户明确本会话承担max详细规划、后由其安排6.1-sol/medium实施。同一session仅续作LAP-24；续作基线`cf69570a1a4c129f17c9d13750890ca41a04edb1`、工作区干净。范围仍仅只读核对/文档；在原5份归属文档基础上增加本目录IMPLEMENTATION_GUIDE.md。补核原生Worker环境继承、固定WebUI认证/密码回退接口与失败分支，收紧计划，准备medium复制指令；不读取秘密值、不启停/登录/认证、不运行真实模型或群验收。

17日排查基线：源码发送器按plan.parts遍历，不补齐最大条数；free提示词缺少adaptive分支的“不凑条数”，人设含1—3句/15—60字篇幅目标，为行为偏向的静态线索，未以真实输出复现唯一根因。当时白名单读取确认ollama_ssh/free/adaptive/max_bubbles=3/web=true/memes=true；不是18日新探测/运行加载证据。

NapCat：现有启动器固定bundle/CWD并传配置bot.qq；安装包快速脚本说明需登录过一次。安装v4.18.38支持快速登录、密码回退和新设备验证；Windows GUID在QQ实际data root下nt_qq/global/nt_data/msf/Registry20，并经CurrentUser DPAPI保护。独立安装目录不证明实际QQ数据目录隔离；本轮未读日常QQ资料、Registry20内容或登录票据，重复验证根因未证实。

状态：2026-10-18 00:15 max详细[PLAN复审](PLAN.md)/[medium复制指引](IMPLEMENTATION_GUIDE.md)完成，未实施。补核Worker重启复制环境、WebUI认证hash/包络/固定登录接口，明确本版采用固定WebUI单次回退，取代首版原生密码环境注入；DPAPI双凭据、稳定未登录判据、20秒/8请求/密码POST一次、按实例保留unknown账本、single/adaptive/表情24组合及真实接受门槛均已细化。先自然分条，再完成登录独立部分；原生数据根路径覆盖仍未验证，不能猜路径迁移或伪标project_only。

17日验证：`.venv/Scripts/python.exe -m unittest discover -s tests -p test_reply_plan.py`，8项通过；用PYTHONPATH等价sys.path加入src的stdin合成脚本调用group_plan，chat数组1/2/3分别返回1/2/3，无真实模型/QQ。当时free/web/memes组合prompt 5134 UTF-8字节、不含“不凑条数”。首次stdin探测未加src路径报ModuleNotFoundError，补入后通过；未改变环境/安装依赖。首版最终168本地链接/差异空白/新增行账号样式数字检查通过。

18日验证：只读安装包源码/启动脚本/静态接口与现有验证入口，无单元/框架重跑、真实认证或运行探测。安装napcat.mjs SHA256及关键函数证据见PLAN；6份文档182本地链接/章节去重/差异空白和新增行账号样式数字检查通过，src/scripts/config/tests无差异、无其他session已跟踪差异。旧verify脚本main会覆盖旧报告的限制已写入指引，要求新lap-24入口/报告。全部待实现测试仅是验收合同，不能计入本轮通过数。

并行工作：开始工作区干净，23:48看到LAP-21新增configure_bot.py/test_configure_menu.py/21 HANDOFF差异。21交接明确其session只写自己的代码/测试/README/报告/任务交接，不写或提交24共享索引；24同样不覆盖、不暂存、不提交21文件。本次8项单元不是21新增代码的验证结论。

首版修改5份：PROGRESS.md、tracks/laptop-workbuddy/HANDOFF.md、TASKS.md、本目录HANDOFF.md与PLAN.md；本轮新增IMPLEMENTATION_GUIDE.md，共6份文档。不提交secrets、settings、state或其他session文件。18日续作未发现其他session未提交差异。

首版Git交付：内容`293422a4d75a49f329bab891426f160c8704750c`及记录`cf69570a1a4c129f17c9d13750890ca41a04edb1`均已推送origin/main并核对完整SHA；检查点工作区干净。期间LAP-21由原session独立提交`fd2a35f`，24首版只提交其5份文档，未夹带21内容。

18日Git交付：复审内容`d03f40aed0c5a087f05be4fecfc64d02f1d4b153`已推送origin/main，rev-parse与ls-remote完整SHA一致，内容检查点工作区干净。该提交仅6份归属文档，182本地链接及差异/隐私模式/非代码归属核对通过；0真实运行操作。本段随后独立提交/推送并再次核对远端，最终记录提交以本session回执为准。

下一步：用户已明确由其后续安排6.1-sol/medium实施，复制IMPLEMENTATION_GUIDE第7节即可；实施方先登记续作/文件归属，按指引先B后A，不把本次规划当部署授权。登录目录能力缺口与真实QQ/表达接受分别补证据。需要重启/真人扫码/真实模型/群验收时另按用户范围登记唯一实例执行归属，保留LAP-18搜索及旧真人/上下文控制差额。
