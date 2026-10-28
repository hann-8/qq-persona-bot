# LAP-43：Snow表情、时效搜索、群参与、唯一操作者与主线整合

返回[PROGRESS](../../../../PROGRESS.md) / [工作线HANDOFF](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [详细规划](PLAN.md) / [medium指令](MEDIUM_START.md)。继承根AGENTS边界；本任务不替代LAP-18/21/27/35/42的历史证据及未验差额。

## 当前状态：LAP-43统一实施与部署进行中

2026-10-28 22:24（Asia/Shanghai）session `LAP-43-rollout`，用户已提交统一实施prompt并明确授权四项启用、受管停启和main部署；QQ群实测由用户执行。隔离树`E:/CodexWS/QQbot_LAP43`、分支`codex/lap-43-rollout`，生产起点main/c4c52ca，开始无非忽略差异。唯一实现和运行执行者为本session，无代理。目标/成功条件：四项实现、必要权限/材料/预算检查、7表情锁内激活、vision完整当前绑定试用、正常加载就绪、main提交推送。文件归属见TASKS首段；不改persona/账号/模型/预算，不主动真实模型/QQ测试。

已完成输入/叫名/同人续聊、唯一owner停言/恢复与重置、搜索正文日期/manifest/来源及识图明确试用代码；37项针对性检查通过（包含受管worker、真实gate发送栅栏、当前CLI来源预算和TS工具隔离替身）。两项历史测试分别固定旧30000/persona和旧native签名，本轮不重写或作为当前成功证明；改用当前实际配置预算检查。尚未部署。

发现全局CLI已升级2.177.1，与锁定2.168.0 bundle不符，当前受管bot stopped/disconnected。用户随后明确授权仅从本机npm缓存恢复旧版到项目runtime；已解包并核对原bundle hash完全一致，不改全局CLI/不下载/不换模型或账号。对应新增归属versions.lock、workbuddy_cli_runner、hosted_cli_budget；项目改用相对路径，完整签名仍绑定。真实CLI零生成、当前配置预算、配对激活与就绪检查尚待部署事务执行。若出现技术失败保留具体证据及配对备份，不因缺用户质量评分停下。

下一步：补必要框架/图库与最小公共连通性检查，审阅提交；正常受管停止确认后合入main，备份及一次保存新增search字段、7条表情、当前vision试用记录，正常启动；同步结果/用法及远端SHA。原旧验收/unknown/人工记录保持，搜索及新版本识图质量待用户实测。

## 2026-10-28前轮文档修订记录（历史）

2026-10-28 21:56（Asia/Shanghai），session `LAP-43-use-first-handoff`续修同一任务。用户明确流程过重、自己实测，要求评估计划后给medium直接落地prompt，并写入AGENTS。本轮仅7文档：AGENTS、PROGRESS、工作线HANDOFF/TASKS及43 HANDOFF/PLAN/MEDIUM_START；起点main与实时远端均`52866fe10cc654d2e12c5520f7afc5aa8bbe0179`，工作区干净，TASKS登记后重读。

结论：原四项功能合同足够，缺口是执行合同。已将MEDIUM_START改成一个同轮实现、必要检查、配置启用和配对部署的prompt；PLAN第0/5/10/11节覆盖原A/B/C/D分轮停止及固定质量批次。搜索支持明确启用后的待人工实测试用，仍逐请求要求可靠正文/日期；识图新增明确待实测的当前完整绑定试用模式，沿用旧接受事实但不捏造新IQ/人工通过。不增加真实模型批次或自动群发，不改账号/模型/预算/工具隔离/unknown及数据边界。下一轮用户提交prompt才执行运行授权，本轮不实施功能或操作运行态。

文档检查通过：差异恰为上述7份Markdown，UTF-8/围栏/237个本地链接、统一prompt的部署授权及试用模式引用、git diff --check均通过；源代码/配置/运行文件不在本任务差异中。未运行功能测试、公共探测、bot管理或模型/QQ/SSH。只提交本次7文档到main，push后核对实时远端SHA并释放归属；最终提交号以本次Git/会话回执为准，不在提交内自引用。

## 2026-10-27历史：规划及main整合已完成

2026-10-27 19:01（Asia/Shanghai）登记并重读，session `LAP-43-snow-memes-web-attention-plan`。用户累计五项意图全部纳入：表情、最新消息搜索、空@/free漏答、Snow分支合main、本人唯一控制权。只有Git整合为本轮实际动作，其余仅详规/medium指令，**没有实施或启用新功能**。

19:27检查点：PLAN和分阶段medium指令已交付，规划提交已快进main并在两条远端核对一致，本根已切main、切换文件树无变化。7份文档/232本地链接等检查通过，17项保护与起点相同。当前仅同步Git回执；回执push/远端核对后释放归属并停止，不执行medium模板。

## 起点和精确文件归属

- 活动根：`E:/CodexWS/QQbot_Snowluma`；起点分支`codex/lap-40-snowluma`。
- 起点HEAD/实时远端Snow：`4616186e1e26990837503b8f43195ddf04e53241`，初始无非忽略Git差异。
- 远端默认HEAD为main，起点实时main=`66eea49623b76766e0569614207c80c78e57115f`；0个main独立提交、65个Snow后续提交。main未被其他worktree占用，适合fast-forward；操作前仍复核最新远端。
- 本session只拥有7份文档：`PROGRESS.md`、`AGENTS.md`、`tracks/laptop-workbuddy/HANDOFF.md`、`tracks/laptop-workbuddy/TASKS.md`、本HANDOFF、同目录`PLAN.md`和`MEDIUM_START.md`。
- 没有业务代码/local/persona/图库/pending/依赖修改；无其他session差异需要夹带或覆盖。不访问原NapCat根/旧C/A4，不修改其他worktree。

## 已完成的事实核对与规划决定

| 事项 | 当前证据与未来决定 |
| --- | --- |
| 表情 | 7条pending及7张引用hash一致，5 GIF+2 JPEG共4,100,086字节，active仍不存在；规划当前根新摘要/停机内置锁激活，不重迁，不直接重放仍绑定旧两根配置的verify.py |
| 搜索 | 硬编码质量门槛false；当前web读取开关不等于搜索可用。保持唯一bing_rss候选，新增默认false的search_enabled、有限正文日期筛选/来源/manifest，真实质量过后才可选中启用；不新增账号/付费服务/CLI工具 |
| 空@ | router本地无字/无图分支含所述文案；规划实际媒体类型分流，纯@短应声0模型、图片沿已接入能力、音视频等准确提示，不猜相邻事件或视频 |
| free | called的纯函数计算证实“鱼鱼查查最新消息”等未识别；规划有限直接叫名语法及同人已ACK短续聊，direct由本地must_reply，普通ambient仍单次模型决定，0额外分类 |
| 操作者 | 本机admin_users恰一项且与用户声明一致；旧gate停言未鉴权、任意真实@可恢复。规划仅真实sender为本人且明确暂停/恢复才能改状态，统一现有重置及框架管理来源；本轮不写真实号码到Git、不改local |
| 识图兼容 | 42缩减验收/vision=true为既有事实；全部gateway Python和配置进入binding，新代码会使旧凭证不匹配。未来隔离实现，新固定43证据/模式/报告路径，明确新次数预算后1张大图+1条群图回归，旧记录/豁免/失败保留 |
| 分支 | 用户明确要已有Snow成果进入main；本轮仅Markdown变化，用普通快进push/fetch及同提交switch保持工作树业务内容，不先checkout旧main；原分支保留、不强推 |

详细行为、默认值、文件清单、验证、迁移/回滚与失败分支见PLAN；公开日期规范/微软退役公告已在相应段落附一手链接。公开文档浏览不是本机PublicHTTP/搜索候选的真实验收。

## 本轮验证及证据边界

- 只读Git：`git status --short --branch`、`git log`、`git branch -vv`、`git worktree list --porcelain`、`git ls-remote --symref origin HEAD`、两分支`ls-remote --heads`及`git rev-list --left-right --count origin/main...HEAD`。19:24远端起点未变。
- 无I/O的`called` AST独立计算8个自造短句，结果写PLAN，不当作项目测试或线上命中率。
- Python `-B -X utf8`只读取YAML必要metadata及SHA；7条引用资产hash匹配、base对应空catalog，17项保护无变化。未调用旧迁移helper或项目配置加载/运行管理入口。
- 7份文档严格UTF-8、最终232个本地链接、8行围栏、41个唯一任务表ID/无重复、真实号码未写入、`git diff --check`与暂存差异/7文件白名单通过。写后重读并按最终回执差异再次核对。
- 没有运行项目单元/框架测试、公共候选probe、bot状态、启停、安装、登录/扫码、模型/QQ/群/SSH。本session主动模型/消息为0，未读取或统计自然free流量，不宣称运行进程/状态保持已被实测。

## medium接续及未完成范围（2026-10-28更新）

用户下一轮直接提交[MEDIUM_START](MEDIUM_START.md)中的统一prompt；同一session续LAP-43，完成实现、必要检查、启用和部署后交用户试用，不再选择或逐段执行旧A/B/C/D。当前只有文档修订session，没有实施或运行执行者；本轮交付后释放归属。

不再安排agent主动真实模型质量批次或群发测试，QQ群体验由用户自己发消息实测，正常free触发不混作agent主动验收。必要的静态预算/当前CLI零生成接线检查保留，不要求用户先打分才上线；当前试用记录必须标待实测，不能记质量通过。共享上下文重置/记忆删除等破坏性真实操作仍未授权。

未完成的是未来功能实现/离线/加载/真实验收；本轮规划完成不清除旧18/21/27/35/42差额。所有local/persona/秘密/群历史/key/图库和原证据保持。

## Git交付回执

2026-10-27 19:27（Asia/Shanghai）：规划内容提交`2986667cf88c85db39947871941a81a0014acba4`，已推送`origin/codex/lap-40-snowluma`并普通快进`origin/main`。刷新main后`merge-base --is-ancestor`通过，合并前独立提交数0/66（原65+本轮文档1）。无强推/无冲突/未删除原分支。

为避免运行目录临时回到旧代码，先`git push origin HEAD:refs/heads/main`，再无force的`git fetch origin refs/heads/main:refs/heads/main`更新未占用本地main；`git diff --exit-code HEAD refs/heads/main`为0才`git switch main`。本地HEAD/main/Snow和两条实时远端均为上述完整SHA，检查点工作区干净；相对本轮起点只改7份Markdown，业务文件未变。

随后只提交本次归属内的入口/交接回执到main并核对最终远端；原Snow分支保留在已合入的规划提交，main的回执后续提交不代表原分支未合并。最终回执文档自身SHA以main HEAD和会话最终报告为准，不自引用。确认远端后释放本规划session归属并停止，不实施或推进下一项。
