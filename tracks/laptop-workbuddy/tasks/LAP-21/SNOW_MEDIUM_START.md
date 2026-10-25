# 下一轮medium：实际迁移Snow主线7条受控表情

返回[PROGRESS](../../../../PROGRESS.md) / [任务交接](HANDOFF.md) / [详细计划](SNOW_MIGRATION_PLAN.md)。

本文件是待用户在下一轮发送的实施指令。本轮只交付规划，没有执行其数据迁移。请由用户在会话设置中选择`gpt-6.1-sol / medium`；agent不检测/切换模型、不派子代理。

以下整段可直接复制：

```text
在 E:/CodexWS/QQbot_Snowluma 接续SnowLuma主线，使用用户会话已选择的gpt-6.1-sol/medium执行。不要派子代理、不要切换模型。

分支：codex/lap-40-snowluma。
规划起点：e2d9a0c082f3400904d8a4032eb01b4290ef08a8；规划文档交付提交在其后，先查实际HEAD/实时远端/工作区，不能回退到起点，也不能沿用过去干净状态。
本轮唯一任务：续LAP-21，实际完成旧7条受控表情及对应图片向Snow新根的数据迁移准备；不要再交一轮只有计划的答复，不开新ID或同时领取其他实施任务。

按顺序读：PROGRESS.md → AGENTS.md → tracks/laptop-workbuddy/HANDOFF.md与TASKS.md → tasks/LAP-21/HANDOFF.md → SNOW_MIGRATION_PLAN.md与本SNOW_MEDIUM_START.md → docs/BOT_USAGE_COMPARISON.md。只补读LAP-19/GROUP_CHAT_PLAN.md第6—8节等所需原合同；不重读所有历史，不访问/复核A4。

动笔前先在TASKS和LAP-21交接登记session标题、Asia/Shanghai开始时间和精确文件归属，写后重读；共享文件或图库/pending有不明修改先保护，不能覆盖别人的工作。Git根/分支与预期不符先只读查明，不擅自切分支。工作区用户修改保持原样，不能夹带交付。

已确认基础：官方Snow原版接入及日常脚本已交付，用户已确认Snow可运行、QQ群bot文字可回复，不重复安装/接入/文字首试。共用模型、聊天、人设、媒体协议和统一投递逻辑继续复用。预计生产代码修改为0，这次优先只做数据，不为换接入重做架构或新建通用迁移系统。

源：E:/CodexWS/QQbot（只读，不对源根加写锁/生成pycache/备份，不启停）；源config/memes.local.yaml及其中引用的assets/memes/library文件。
目标：E:/CodexWS/QQbot_Snowluma（唯一写入根）。旧C工作根不访问、不修改、不运行。
规划时源7条全部enabled=true且通过MemeCatalog校验，5 GIF+2 JPEG，共4,100,086字节；目标catalog不存在/0条，两根pending均不存在。7候选紧凑JSON为1134字节。下一轮必须重查，不能把这些事实当成覆盖新数据的许可。

按SNOW_MIGRATION_PLAN.md的M1—M5实际执行：
1. 用现有Python -B与PYTHONDONTWRITEBYTECODE=1，read_project只读两根配置/摘要；MemeCatalog/preview/inspect_image及plain_path校验7条登记、7张源图、各级路径/reparse、hash/格式/大小/帧数。只迁catalog引用的7张，不迁inbox/未登记图库/任何历史。前后重读源catalog与7图摘要，避免使用变化中的来源。
2. 先在目标忽略的state/meme-migration/<本轮session>/备份目标catalog/pending原字节或不存在标记、配置摘要及私密manifest。完整标签/资产清单只在本机忽略目录，文档只留数量/类型/字节/校验结论。不输出账号、群号、token、原始消息、用户标签或图片。
3. 复用MemeCatalog.add按hash排他复制实际7图；保持源id/name/context/tags/enabled/file/sha256/media_type和原字节，不重打标签、不转码、不改ID。目标已有全同资产可复用；其他目标行保留，冲突字段或不同pending不覆盖。复核目标图、目录引用和7候选/预算；不放宽任何路径/类型/发送限制。
4. 在既有配置锁下重查目标配置摘要/active fingerprint/pending竞争，按既有version=1/base/items格式原子暂存到state/memes-pending.local.yaml，实际完成目标library与pending准备。可用现有stage/atomic_yaml；保护其他session的pending，不嵌套获取配置锁。
5. 若目标本来已停止、require_stopped可确认，且source/config/active/pending及本批归属校验通过，允许调用带config_guard的MemeCatalog.activate_pending进行离线目录激活。若正在运行/停止未知/锁忙，则保留已复制及暂存，交付“已准备、未激活/加载”，写清后续停机激活/正常重启步骤；绝不能为完成这一步擅自停bot或改活动目录。不要停在仅告诉用户手工复制。
6. 使用现有test_memes.py做临时根/自造图/假RPC回归，做7图/字段/hash/预算/幂等与本机设置保护检查。数据-only不跑全矩阵，不运行会覆盖旧reports的verify_lap21主入口，不复核或重跑A4；若真有小修复，只补相关合成检查。

配置合同：新增字段0。保留现有config/local/persona、模型参数、账号/额度、free触发、web及其他选择。特别memes现为true、两个图片冷却为0/0，不能用模板默认false或60/300覆盖。目录/数据保存不等于运行加载。vision、memory/learning、members、attention、bilibili均保持当前false，不自动开启。

授权逐项明确：
- 本消息授权新根内上述实际数据复制、备份、暂存、必要一次性准备脚本和离线验证/文档交付；目标本来已停时允许在既有锁下激活目录。预计不需生产代码；确有既有图库合同内小bug时，先做独立部分，登记后仅可最小修复src/qqbot_gateway/meme_catalog.py与tests/test_memes.py并验证。其他生产文件/方案变化记录具体阻断回规划，不能自行扩大归属。
- 未授权安装、真实bot/QQ/Snow启停、登录/扫码/SSH；不运行启动/关闭脚本，不修改Snow内部，不接管外部QQ实例。
- 未授权真实模型或QQ操作：真实生成0，群发送0，收藏读取/下载/真实RPC0；不要为“验一下”消耗额度或旁路裸发。需要这些时交付已准备数据和准确剩余动作，等待用户另定唯一执行session/时段/群与上限。
- 后续真实验收才检查图片同链ACK/客户端显示/GIF动画，分别记状态；本轮不得宣称Snow图片真实通过。无需把旧资格/proof/probe、全量旧验收或72h/7天长稳设为前置。

图库、标签、备份/manifest、local/persona和state均不提交。可新增tracks/laptop-workbuddy/tasks/LAP-21/SNOW_MIGRATION_RESULT.md；同步PROGRESS、工作线HANDOFF/TASKS、LAP-21交接和使用对照，明确copied/staged/activated/loaded/real_ack/client_display中哪些实际完成。
沿用长期Git授权，只提交本任务已检查的跟踪文件，commit/push到原分支后核对完整远端SHA，报告提交号和保留差异。源根只读，旧C根不碰，B/C停止，A4代码/产物/证据原样保留不读不验。
回滚只按本批备份/摘要和停机锁恢复目标catalog/pending，图片可留忽略库；不删lock/state/数据库/清理台账，不热改活动目录，不git reset/clean。能力缺口按计划第9节记录，不自行放开任意媒体、换后端/模型或增加付费API。
记忆下一优先、识图随后，但本任务交付即停止；B站字幕已按用户决定退出近期路线，本轮不删代码、不续字幕/ASR。完成LAP-21本次实际迁移交付后释放归属，等待用户下一条指令。
```
