# LAP-21续作：Snow主线受控表情资产迁移计划

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [本任务交接](HANDOFF.md)。执行入口：[完整medium指令](SNOW_MEDIUM_START.md)。原行为合同：[LAP-19第6—8节](../LAP-19/GROUP_CHAT_PLAN.md)。

2026-10-25，Asia/Shanghai。session `LAP-21-snow-controlled-memes-plan`，15:46开始只读复核、15:49登记文档归属并重读。基线分支`codex/lap-40-snowluma`，本地HEAD及实时`git ls-remote`均为`e2d9a0c082f3400904d8a4032eb01b4290ef08a8`，开始无非忽略Git差异。会话模型/推理档位由用户设置，本轮未检测或切换，不派子代理。

**结论：续原LAP-21，下一轮实际迁移7条登记及其7个文件。当前证据支持仅做数据准备，不重做图库、模型协议或发送架构。本轮仅规划，尚未复制、暂存、激活或发送。** 不新开任务ID，不同时领取其他功能实施。

## 1. 后续候选与推荐顺序

以下只确定排序、含义和差额；本计划仅展开第1项。

| 顺序/原任务 | 当前磁盘与原合同状态 | 接续建议 |
| --- | --- | --- |
| 1，LAP-21受控表情 | 代码已实现/旧离线通过；两根memes=true；旧根7条、新根0条，资产未迁移；Snow真实发图未验 | 先执行本计划，复用现有业务链，默认0生产代码修改 |
| 2，LAP-30长期群记忆 | 已实现/离线通过；当前读取与学习均false；真实语义/召回/ACK未验 | 下一项优先续30，规划新根独立有界记忆的启用与真实验收；不把迁旧聊天库当其前置，不要求成员或视觉开启 |
| 3，LAP-28识图 | 已有入站/原生材料/质量与预算门槛代码，部分后续适配尚待实施；当前vision=false，真实输入/所选模型原生能力/可信容量与质量未过 | 尽快续28核对当前所选模型路径的能力缺口；不能只改true，也不能为开图自动换模型、后端或付费API |
| 4，LAP-27关注增强 | 已实现/离线通过；attention=false；真实语义效果未验 | 在现有free之上改善叫名、引用bot消息、短时第二人称续聊的对象判断；不是后台主动发言，现有free不依赖开启它 |
| 5，LAP-29成员增强 | 已实现/离线通过；members=false；生产人数新鲜度缺证，代码会暂停功能 | 为少于50人的授权群提供有界成员名册候选与受控@；不是入群/拉人/管理群，也不是当前真实@bot必答的前置 |
| 退出近期路线，LAP-06/07 | 字幕06已有代码/离线通过、当前false且真实未验；ASR07仍延期 | 用户决定B站字幕先撤下、以后再说；后续如清理入口/代码，单独界定兼容范围。本轮及下一轮表情任务都不删相关代码、不补字幕/ASR验收 |

网页材料读取当前true，继续使用，不重做接入或通用聊天；搜索真实质量门槛未通过仍保留。历史差额不抹除，也不把全部旧验收、资格/proof/probe或72h/7天长稳转成此次迁移前置。

## 2. 需求、非目标和交付层级

需求是把旧根**已登记的7条**及其对应图片安全带入Snow新根，使既有受控发送逻辑有候选可用。保留`id/name/context/tags/enabled/file/sha256/media_type`及原图字节，不重新扫描命名、不重新标注、不转码，保留已确认的7条enabled=true。

下一轮按真实状态分别交付：

1. **数据已准备**：7个文件已校验并复制入新根受控library，完整目录表按既有pending格式暂存，备份和本机manifest可恢复。
2. **目录已激活**：仅当新根本来已停止且既有停机校验通过时，在配置锁下将pending激活；不为此停止或启动bot。
3. **运行已加载**：须以后经授权正常启动/重启后才可确认。保存或激活目录不等于运行进程已加载。
4. **真实发送通过**：另获授权后，既有链路的图片ACK及客户端实际显示分别记录；动画表现也单列。

本次规划不承诺第2—4层已发生；下一轮若运行中，完成第1层就是可独立交付的实际迁移准备，须明确“尚未激活/加载/真实验收”，不能只写一份新计划或笼统说恢复完成。

非目标：重装Snow、重复文字首试、QQ收藏RPC/下载/重新导入、复制inbox或整棵assets、迁聊天/历史/长期记忆、开启识图/记忆/关注/成员、修改B站实现、改人设/模型/额度/free规则、改Snow内部或日常QQ/WorkBuddy全局设置。

## 3. 当前证据：只读结果与代码依据

### 3.1 当前文件事实

源根`E:/CodexWS/QQbot`，目标根`E:/CodexWS/QQbot_Snowluma`。通过新根现有Python，使用`-B`与`PYTHONDONTWRITEBYTECODE=1`、`read_project`、`MemeCatalog.preview`、`plain_path`做本地只读核对；不接gate、不发HTTP、不加载账号秘密、不输出标签或图片。

| 项目 | 2026-10-25本轮观察 |
| --- | --- |
| 源目录表 | `config/memes.local.yaml`，version=1，7条；7个ID唯一，7条已启用且名称/标签符合既有校验 |
| 源图片 | 仅目录表引用的library文件：5 GIF、2 JPEG，共4,100,086字节，约3.91 MiB；7/7路径、真实类型、尺寸/帧数限制及SHA256通过 |
| 目标目录表 | 不存在，加载为0条；不是“发送代码缺失” |
| 现有pending | 两根`state/memes-pending.local.yaml`均不存在；下一轮必须重查，不能据此覆盖后来数据 |
| 候选预算 | 源7项均可进入当前候选；按现有紧凑JSON计1,134 UTF-8字节，未超2000字节/16项上限 |
| 当前memes设置 | 两根true，固定默认路径；每轮1图；候选16/2000字节；冷却保存值0/0秒；allow_meme_only=true；单文件8MiB；import_count=48 |
| 其他选择 | 两根free，web=true；vision/members/memory/learning/attention/bilibili均false；persona各19,256字节且摘要相同 |
| 共用源码 | meme_catalog、media_protocol、reply_plan、reply_delivery、group_protocol、group_memory、model_gateway共7份与旧根字节相同；不推断Snow真实图片ACK已通过 |

这些是当前磁盘/静态解析结果，未查询实时在线状态、运行目录表或真实模型。用户已确认的Snow文字可回复沿用，不重复试验。源本机标签、完整资产哈希/清单只留下一轮忽略的manifest；跟踪文档只写数量、类型、总字节和校验结论。

### 3.2 复用点

- [meme_catalog.py](../../../../src/qqbot_gateway/meme_catalog.py)：`validate_memes`固定忽略位置；`controlled_path`/`inspect_image`/`preview`校验路径、类型和hash；`add`按内容hash写库；version=1、ID=`m_`加完整SHA256；`stage`/`activate_pending`已有暂存/激活合同。
- [config.py](../../../../src/qqbot_gateway/config.py)：`configuration_lock`、`require_stopped`；gate按启动配置构造MemeCatalog。[config_files.py](../../../../src/qqbot_gateway/config_files.py)的`read_project`只读配置/摘要，`plain_path`检查已有路径各级重解析点，不读取秘密内容。
- [router](../../../../plugins/qq_router/main.py)：启动时构造图库，目录fingerprint参与人设会话版本；没有目录表热更新承诺。不得运行中替换活动目录而让不同组件各用不同集合。
- [media_protocol.py](../../../../src/qqbot_gateway/media_protocol.py) / [reply_delivery.py](../../../../src/qqbot_gateway/reply_delivery.py)：模型只选候选ID；统一typed plan、冻结文件、SDK图片转换校验和逐条ACK，不增第二次模型选择。
- [onebot_gate.py](../../../../src/qqbot_gateway/onebot_gate.py)：出站图片仅允许已登记库文件或对应冻结文件URI，复核hash；无任意URL/base64/本机文件旁路。官方Snow对本次图片的真实显示仍需实测。
- [.gitignore](../../../../.gitignore)：用户library/inbox、目录表、config/local与state已忽略；不必新增数据目录、schema或依赖。

## 4. 配置默认值及生效合同

**新增配置字段为0；既有local/persona完全保留。** 特别不要拿模板重建features.yaml或重新保存所有配置。

| 字段/数据 | 新装默认 | 当前保存值/迁移处理 |
| --- | --- | --- |
| `memes.enabled` | false | true；保持，不为了迁移改false/true |
| `.inbox_dir` / `.library_dir` / `.catalog_file` | assets/memes/inbox、assets/memes/library、config/memes.local.yaml | 同默认固定路径；仅复制catalog引用的library文件，不改引用到旧根，不建链接/junction |
| `.max_candidates` / `.catalog_prompt_max_bytes` | 16 / 2000 | 保持16 / 2000；迁后重新检查全部7候选及预算 |
| `.max_images_per_turn` / `.max_file_bytes` | 1 / 8388608 | 保持；不放宽格式、动画、像素等限制 |
| `.cooldown_seconds` / `.same_meme_cooldown_seconds` | 60 / 300 | 本机0 / 0必须保留，不悄悄恢复模板默认 |
| `.allow_meme_only` / `.import_count` | true / 48 | 保持；此次不用QQ收藏导入 |
| 目录表 | version=1，items空 | 保留7条原字段和顺序；已有目标条目按下节保护，不重新生成标签或ID |
| pending | 既有version=1/base/items | base为目标当前catalog fingerprint；只在忽略state暂存，不作为已生效证据 |

配置改动原合同为停机保存、下次正常启动生效。本任务不改配置；目录激活仍须停机锁和竞争摘要检查，运行加载仍需以后的授权启动。不运行`memes-admin`交互菜单：扫描会产生禁用的新行并丢失原标签确认，不适合本次原样迁移。

## 5. 文件归属与最小范围

本规划session只归属7份Markdown：PROGRESS、工作线HANDOFF/TASKS、LAP-21/HANDOFF、本PLAN/medium指令、BOT_USAGE_COMPARISON。LAP-41交接保留为已完成的历史，不重写其清理结果；AGENTS/旧任务合同也不改。

下一轮medium开始后重新登记同一LAP-21及当轮时间、session和归属：

| 范围 | 可写内容 |
| --- | --- |
| 目标忽略数据 | `assets/memes/library/<目录表验证过的hash文件名>`最多源7项；`state/memes-pending.local.yaml`；停机条件满足时`config/memes.local.yaml` |
| 当轮本机工件 | 新根`state/meme-migration/<本轮session>/`中的备份、manifest、必要一次性准备脚本/离线日志；该目录应精确限定，不递归覆盖任何其他state内容 |
| 跟踪交付 | 上述入口/交接/对照的相关状态；可新增本任务`SNOW_MIGRATION_RESULT.md`记录实际数量、状态和限制，Git不包含用户标签/图片/完整私密清单 |
| 源根 | 只读源catalog和7个引用文件；不对旧根加写锁、生成pycache、写备份/状态，也不启停它 |

预期生产代码修改数为0，不必新增通用迁移器。可在新根忽略目录写小型一次性数据准备脚本，重用现有类/校验/原子写入。若发现既有图库校验/暂存/激活合同内可复现小缺陷，先完成不受阻的数据准备，登记后仅允许最小修复`src/qqbot_gateway/meme_catalog.py`及对应`tests/test_memes.py`，补针对性合成验证。其他生产文件先记录具体阻断返回规划，不凭“换Snow”批量改gate/router/SDK；变更协议、能力门槛、后端或Snow内部也按第9节返回规划。

## 6. 下一轮实际实施顺序

### M1：恢复上下文与预检，不重复首次试用

1. 重查新根路径、分支、HEAD、实时远端和非忽略差异。远端推进先只读查明；只快进明确的同线提交，不切main、不覆盖或强推其他session内容。
2. 按PROGRESS读取本任务入口；登记本次medium归属并重读。独占的是本次数据迁移，不自动获得真实实例执行权。
3. `read_project`读取两根配置、`MemeCatalog`解析源/目标；检查精确路径及所有已有祖先无symlink/junction/其他reparse越界。保存两根local/persona和源catalog/7图摘要，以及目标catalog/pending的存在状态、原字节和摘要；不输出秘密或标签。
4. 源仍须是预期7条、7图完整有效。源在复制期间不能加锁写入；采用前后重读源catalog和各文件摘要确认取得稳定快照。若发生变化，停止该批激活，不自行猜测哪份才是用户最新版本。
5. 重查目标现有library、catalog和pending。目标新增无冲突条目须保留并合并；同ID且字段/字节全同视为已迁移可跳过；同ID标签等字段不同或已有不同pending，保持其内容，不能静默覆盖。可完成自有隔离工件，报告冲突后停止活动目录变更。

### M2：校验、备份与复制

1. 用现有`preview/inspect_image`校验每张原图，再读取并冻结本批字节/原登记字段；只选catalog引用的7张，不遍历复制源inbox、未登记library、历史或登录目录。
2. 在新根忽略的session目录保存目标catalog/pending原字节或“原先不存在”标记、目标配置摘要和源快照manifest。操作前确认工件及用户资产仍被Git忽略。
3. 复用`MemeCatalog.add(data, suffix)`按hash写入目标library，新文件用排他创建；同名且字节完全相同才复用，已有不同字节时拒绝覆盖。给新条目保留源完整字段，已有目标行保持原样，禁止扫描后把7条默认为disabled或重新要求打标签。
4. 复制后按目标root调用校验，确认每图字节/hash/类型与源一致；验证目录表全部引用在新根内，无旧根绝对路径、URL或指向源的链接。失败不得激活半套目录表；已复制的有效文件可保留在忽略库，报告真实进度。

### M3：按既有格式暂存，运行中不改活动目录

1. 候选并集准备完后，在新根`configuration_lock`下重读目标配置source_digest、活动catalog fingerprint及pending状态，拒绝竞争。metadata/manifest记录本批归属和期望摘要，不新增运行时schema。
2. 使用既有`version: 1 / base: <目标活动fingerprint> / items: <目标原行与源新增行>`格式，原子写入唯一pending。可复用`MemeCatalog.stage()`；须先保护已有不同pending，不能依靠它的合并行为覆盖别人的标签。若为在同一锁内核对竞争而直接调用现有`atomic_yaml`写此既有结构，不改变格式，也不要在外层锁内再嵌套调用stage/activate。
3. 复核pending自身摘要与本批manifest、base和items，图片全可解析；活动catalog仍保持原字节或原先不存在。数据准备应实际落到目标library和pending，而非只生成待办说明。

### M4：只在本来已停止时激活

1. 不安装、不停bot、不登录、不调用模型或QQ来迁移。用既有`require_stopped`检查目标受管创建身份；不按进程名查杀，不删除状态以制造“已停”。本轮规划没有预先判断现在是否停止。
2. 若运行中、停止状态未知或配置锁被其他session占用：保留已准备数据，交付“7图已复制/目录已暂存，未激活”，写清以后需停机激活与正常重启的精确一步，不在此等待循环或擅自启停。
3. 若目标本来已停：核对源稳定快照、目标配置摘要、active base、pending及本批所有权后，使用带config_guard的`MemeCatalog.activate_pending()`。该方法自己持锁并再验停止/竞争，不在外层锁重复调用；guard在锁内核对本批pending摘要和配置。不得用直接覆盖活动YAML绕过检查。
4. 激活后重载校验源7项均存在、字段与字节一致、resolve有效、候选预算合格；报告“目录已激活，尚未启动加载/真实发送”。同批重跑应识别全同数据并无操作，不重置标签、启用状态或冷却。

### M5：记录、Git交付并停止

更新PROGRESS、工作线HANDOFF/TASKS、LAP-21/HANDOFF和使用对照，按实际结果区分copied/staged/activated/loaded/real_ack/client_display；即便只是暂存也交付数据与摘要结果。仅提交本任务已检查的文档和确有必要的小修复；图库、标签、备份/manifest/local/persona/原始消息不入Git。commit/push并核对完整远端SHA后释放归属，停止，不自动转LAP-30/28或真实测试。

## 7. 必要验证与通过出口

| 检查 | 最小要求 |
| --- | --- |
| 数据完整性 | 源7条/7图在稳定快照内有效；目标每个迁入ID原字段/原字节/hash一致；正常基线下是7条、5 GIF+2 JPEG、4,100,086字节；若下一轮来源变化按实记录并停止扩大批次 |
| 候选可用 | 用准备出的目录和目标设置做只读解析，7个启用源ID均可resolve；当前基线7候选/1134字节。存在目标新资产时保留它们并报告候选预算影响，不扩大上限 |
| 保护/竞争 | local/persona前后摘要相同；旧根本session只读；已有目标资产/非本批pending不覆盖；source/active/config摘要变化时拒激活；幂等重跑无多余行 |
| 既有校验回归 | 下一轮用现有`.venv/Scripts/python.exe -B -X utf8 -m unittest discover -s tests -p test_memes.py`，仅临时根/自造图与假RPC；不把它当真实Snow ACK，不新增镜像式测试 |
| 范围检查 | `git diff --check`、本轮Markdown链接/围栏、`git check-ignore`精确数据路径、暂存文件名单/差异；不用全库测试或运行会覆写旧reports的verify_lap21主入口 |

数据迁移本身不要求重跑全部LAP-20/21/27—31矩阵。若确有小修复，只补受影响的协议/投递测试和使用自造图的框架路径，不接真实端口、不覆盖旧报告，不启动A4复核。下一轮临时测试的fake RPC不等于请求运行bot。

本轮规划的验证仅包含只读数据解析/源文件比较、文档与保护摘要核对，不执行上述代码测试。本地Python现成可用；不安装包、不改uv.lock，不把新根运行态未知误写成已停。

## 8. 真实验收授权边界

| 动作 | 下一轮复制指令授予的范围 |
| --- | --- |
| 代码/数据准备 | 新根内上述实际复制、备份、暂存、离线检查/文档；目标本来已停止时可按既有锁激活目录；不改local/persona或现有功能开关 |
| 安装/真实启停/登录扫码 | **未授权**。需要时交付已准备数据和具体待执行步骤；用户后续另定唯一执行session与时段，不重复索要已授予的数据准备授权 |
| 真实模型 | **未授权，调用数0**。不做“先离群试一下”，不换账号、后端或额度，不加模型做表情识别/标注 |
| 群操作/QQ接口 | **未授权，发送/收藏读取/真实RPC均0**；不裸发图片或用收藏导入代替本地迁移 |

以后用户明确受测授权群、唯一执行session、时段和调用上限后，再以现有free/真实@和统一投递链做最小真实验收。可先选1张JPEG和1张GIF，各一次明确要图请求、每次最多一次既有模型尝试；失败/unknown仍消耗授权次数，不自动重试或补发。不要求一口气测完7张或重做全部旧验收。

分开记录：目录是否加载、候选/typed plan是否有效、同链图片ACK是否成功、QQ客户端能否看到图、GIF是否动画。模型没选图、ACK unknown或客户端只见静态帧都按事实保留，不从本地哈希/合成回执推成真实成功；不读取全群历史补查ACK。真实安装/启停也不能由本计划文件自行授权。

## 9. 回滚、能力缺口与停止规则

回滚只处理本批目标数据：暂存未激活时保留活动目录原样；需撤回本批pending时先核对其当前摘要与manifest，仅撤回确定属于本批的那个文件。图片可留在忽略library，不必为回滚删除。不要删除configuration.lock、数据库、会话/清理台账或其他state。

若已激活，要恢复活动目录须再次满足目标停止、配置锁、当前目录仍为本批期望摘要，按备份原字节恢复；原先不存在则在明确校验的目标路径恢复“不存在”。若运行中，先交付回滚材料，等待真实停机授权，不能热替换；不擅自改memes=false或任何其他local字段。保留所有非本批资产与并行修改，不动源根，不git reset/clean，不批量递归删除。

以下是能力出口：

- 路径/格式/hash失败或源资料变化：报告哪一类校验失败及已完成数量；保留有效复制/备份，不放宽限制、不激活残缺批次。
- 当前bot运行/停止未知：已复制和暂存仍可交付；停机激活/重启作为明确剩余，不冒称迁移已生效。
- 既有图库合同内小缺陷：留最小可复现的自造夹具证据，先完成独立部分；只在第5节限定的meme_catalog/test_memes内登记后最小修复，其他生产文件返回规划，不新设计架构。
- 官方Snow真实图片URI/ACK若以后出现具体阻断：先在既有外部接点定位；若必须改协议、放开任意路径/base64、裸发、改Snow内部、换模型/后端/付费来源，停止该部分并交用户决定/回规划。当前没有这样的真实阻断证据，不预先制造兼容补丁。
- 记忆/识图/成员/关注、B站清理以及旧差额都不是本轮扩项理由。完成本计划和medium指令的Git交付即停止；后续由用户发出实施指令。
