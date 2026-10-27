# LAP-43：Snow表情、时效搜索、群参与、唯一操作者与主线整合

返回[PROGRESS](../../../../PROGRESS.md) / [工作线HANDOFF](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [详细规划](PLAN.md) / [medium指令](MEDIUM_START.md)。继承根AGENTS边界；本任务不替代LAP-18/21/27/35/42的历史证据及未验差额。

## 当前状态：规划完成，Git整合待执行

2026-10-27 19:01（Asia/Shanghai）登记并重读，session `LAP-43-snow-memes-web-attention-plan`。用户累计五项意图全部纳入：表情、最新消息搜索、空@/free漏答、Snow分支合main、本人唯一控制权。只有Git整合为本轮实际动作，其余仅详规/medium指令，**没有实施或启用新功能**。

19:24检查点：PLAN和分阶段medium指令已完成；7份文档初检通过，17项保护与起点相同。实时远端main/Snow仍等于下面的起点，无未知修改。接下来仅精确暂存/commit/push、main快进整合和实际回执同步，不执行medium模板。

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
- 7份文档严格UTF-8、229个本地链接、8行围栏、41个唯一任务表ID/无重复、真实号码未写入、`git diff --check`初检通过；本HANDOFF更新后交付前重核实际结果。
- 没有运行项目单元/框架测试、公共候选probe、bot状态、启停、安装、登录/扫码、模型/QQ/群/SSH。本session主动模型/消息为0，未读取或统计自然free流量，不宣称运行进程/状态保持已被实测。

## medium接续及未完成范围

用户后续选[MEDIUM_START](MEDIUM_START.md)中的一个阶段：A全部代码/离线（隔离分支）→ B有限公共质量0模型 → C明确授权的配对运行；也可D仅启用当前已有7图。每段独立领取/交付并停止，不自动推进。当前没有实施session，不自动创建新任务/空交接。

未来真实上限建议是1本机大图+最多5群模型请求，只有用户实际选中C才授权；D仅两次表情，不授新视觉回归。需要另一名群友配合的控制反例，未实际发生则保留未验，不冒充。共享上下文重置/记忆删除等破坏性真实动作不在该C验收授权内。

未完成的是未来功能实现/离线/加载/真实验收；本轮规划完成不清除旧18/21/27/35/42差额。所有local/persona/秘密/群历史/key/图库和原证据保持。

## Git交付回执

规划内容即将按7文件白名单提交推送Snow，再快进main。合并后在此写入实际规划提交/主线SHA与核验；最终回执文档自身SHA以main HEAD和会话最终报告为准，不自引用。确认远端后释放本规划session归属并停止，不实施或推进下一项。
