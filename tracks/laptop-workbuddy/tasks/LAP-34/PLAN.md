# LAP-34：分层配置文件与直接编辑工作流

返回[任务交接](HANDOFF.md) / [实施指引](IMPLEMENTATION_GUIDE.md) / [PROGRESS](../../../../PROGRESS.md)。

状态：本合同已实施/离线通过，证据见[HANDOFF](HANDOFF.md)与[报告](../../../../reports/lap-34-2026-10-20.md)；未迁移/加载本机，真实与完整验收待后续明确指令。下文保留规划时证据与合同。2026-10-20（Asia/Shanghai）。继承[AGENTS](../../../../AGENTS.md)的模型/档位、先规划后实施及隐私边界；会话设置由操作者选择，本文件不宣称已检测或切换模型。

## 1. 需求与非目标

用户熟悉YAML/JSON/TOML，希望直接编辑配置，不再依赖“配置机器人.cmd”，且文件层级、字段用途和生效方式清楚。

本任务使用已有YAML依赖：5份职责固定的本机配置、同结构中文注释模板、1份配置索引；沿用独立人设文件。日常流程为关闭机器人→编辑对应文件→正常启动，启动自动做本地校验，无额外“应用配置”菜单或命令。可选只读check用于编辑后提前定位错误。

不新增后端、模型/账号/额度来源、付费API、热更新或定时主动发言；不改变授权群/黑名单/私聊关闭、单次尝试、工具隔离及发送合同。既有能力门槛继续执行；不通过可编辑文件伪造“已验证”。本任务不修复LAP-18/24/28/29/31B等旧差额。

## 2. 当前代码证据

以下为2026-10-20基于`main/003f04e`的源码核对，不是本机生效或真实能力证据；未读取`settings.local.yaml`内容或任何凭据。

| 证据 | 现状及改动原因 |
| --- | --- |
| [示例](../../../../config/settings.example.yaml)、[配置加载](../../../../src/qqbot_gateway/config.py)的`normalize_settings/read_settings` | 已有schema1/2内存迁移到schema3及大量字段校验；实际设置集中在单文件，`read_settings`返回单文件原始字节摘要 |
| 同文件`save_settings` | 停机/配置锁/原摘要复核/完整备份/原子替换；YAML写回不保留原注释，不能直接用来重写多份手工维护文件 |
| [配置脚本](../../../../scripts/configure_bot.py)、`配置机器人.cmd`（实施后已退役） | cmd仅包装Python菜单；日常参数与图库/记忆/凭据等管理动作混在同一入口 |
| [生命周期](../../../../scripts/manage.py)、[框架准备](../../../../scripts/configure_astrbot.py)、[插件](../../../../plugins/qq_router/main.py) | 多次硬编码读取`config/settings.local.yaml`；只改一个加载点不足以保证一致 |
| [model入口](../../../../src/qqbot_gateway/model_gateway.py)、[gate入口](../../../../src/qqbot_gateway/onebot_gate.py)、[登录管理](../../../../src/qqbot_gateway/napcat_login.py)、[视觉观察](../../../../scripts/observe_lap28.py) | 存在通过配置路径`parent.parent`推断项目根的代码；把配置搬到更深目录会误算根路径，必须显式传项目根 |
| [会话版本](../../../../src/qqbot_gateway/persona.py)的`session_version` | 仅所选模型profile等语义字段影响版本；文件拆分、注释和未激活profile编辑不应制造新会话 |
| [成员](../../../../src/qqbot_gateway/members.py)、[视觉](../../../../src/qqbot_gateway/vision.py)、[群记忆](../../../../src/qqbot_gateway/group_memory.py) | members未验证时运行副本暂停；vision开启会被启动门槛拒绝；memory学习要求读取开关开启；不能统一改成“填true即一定可用” |
| [.gitignore](../../../../.gitignore) | 当前只明确忽略单文件本机配置、图库目录及secrets/state等；新增本机目录必须先忽略 |

开始时唯一已跟踪未提交修改为用户`config/persona.md`，不得覆盖、格式化或夹带提交。该事实不是对角色正文的审阅。

## 3. 唯一配置层级

以下路径为实施目标，目前尚未创建。文件名使用固定英文便于脚本引用，目录索引与所有字段注释用中文。

```text
config/
├─ README.md                 配置总索引：改什么→找哪个文件、如何生效
├─ examples/                 可提交模板，只供复制/对照，不参与运行覆盖
│  ├─ bot.yaml               账号、授权群、管理员、黑名单
│  ├─ models.yaml            当前后端、两个模型profile及预算
│  ├─ chat.yaml              群聊参与、关注/续聊、回复和历史限制
│  ├─ features.yaml          联网、表情、群记忆、识图、成员/@
│  └─ runtime.yaml           回环端口、秘密文件引用、布局版本
├─ local/                    真正编辑/加载的5份本机文件，整个目录忽略
│  └─ 同名5份YAML
├─ persona.md                角色正文，维持原路径/内容
├─ memes.local.yaml          图库登记/标签数据，维持原路径，忽略
├─ settings.local.yaml       未迁移时的旧入口；迁移后只留作原始备份
├─ settings.example.yaml     旧单文件兼容模板，醒目标明新入口
└─ 现有cli-*.json等           程序能力/隔离材料，不是日常设置
secrets/                     既有连接资料、token、受保护凭据；不搬入YAML
state/config-runtime/        启动生成的只读配置快照；程序维护，禁止手改
state/config-backups/        迁移/回滚备份；忽略，不作为运行覆盖层
```

每份文件首部必须说明“管什么、对应其他文件、保存后下次启动生效、本机文件不提交”。模板中每个字段均注释含义、单位/可选值、默认值、重要约束；常用项放前，连接/队列等高级项标注后置。字段名与现有schema3保持一致，不发明中文字段别名或双向映射。

固定归属如下；组装器逐节分配，禁止后文件覆盖前文件，不扫描任意YAML、不支持include、环境变量插值或多格式混用。

| 文件 | 唯一允许的根字段 | 典型需求 |
| --- | --- | --- |
| `bot.yaml` | `bot`、`access` | 改机器人QQ/管理员、加授权群或黑名单 |
| `models.yaml` | `llm` | 在`llm.backend`选择路线；两个profile各自保存模型与预算；共享队列参数为高级项 |
| `chat.yaml` | `chat`、`participation`、`output` | mentions/free、别名/关注、合批/频率、自然分条与回复长度 |
| `features.yaml` | `web`、`memes`、`memory`、`vision`、`members` | 扩展开关与各自上限；清楚标注未验证能力 |
| `runtime.yaml` | `layout_version`、`schema_version`、`onebot`、`secrets_file`、可选`legacy_extensions` | 版本、受限回环连接和凭据文件引用；通常无需修改 |

`layout_version: 1`只标识本次文件布局；组装后移除，运行配置仍为`schema_version: 3`。`legacy_extensions`缺省`{}`，仅无损保留旧配置未知顶层字段：合入原顶层时不得与已知字段/布局元数据冲突，启动提示保留但不保证有功能。未知嵌套字段保持原校验器的保留/拒绝规则，不顺手重写全schema；索引须说明这类扩展通常无需编辑。

## 4. 字段、默认值及生效合同

新安装模板默认如下；迁移现有配置必须保留实际规范化值，绝不能用模板覆盖用户当前选择。字段完整清单以现有示例、各validator/defaults与下表共同为依据；实施时保证五模板组装后的默认值与旧模板规范化结果相同。

| 所在文件/字段 | 新安装默认与约束 |
| --- | --- |
| bot：`bot.qq`、`access.allowed_groups/admin_users` | 必填；模板用说明性占位，不放实际账号群号；授权群/管理员非空；建议引号字符串，沿用numeric ID校验 |
| bot：`access.blocked_users/private_enabled` | `[]` / `false`；入口前置过滤；私聊不能通过手改开启 |
| models：`llm.backend` | `codebuddy_cli`；只允许`codebuddy_cli`/`ollama_ssh`，无失败自动切换 |
| models：`profiles.codebuddy_cli` | `model: deepseek-v4.1-flash`，`reasoning_effort: auto`，`context_window_tokens: null`，`run_timeout_seconds: 90`；具体强度受已有能力元数据校验，原生窗口仍仅null/auto合同 |
| models：CLI `input_budget` | 输入16384、开销2048、输出2048；字段依次`context_input_limit_tokens/context_overhead_reserve_tokens/output_reserve_tokens`；可见UTF-8字节保守估算，不称精确token/credits |
| models：`profiles.ollama_ssh` | `model: qwen3.5:9b-q4_K_M`、`expected_digest: null`、`access_file: secrets/home-5070-runtime.local.json`；启用前digest必须明确，真实凭据仍在原secrets保护文件 |
| models：本地模型参数 | `num_ctx: 16384`、`think: false`、`num_predict: 1024`、`keep_alive_seconds: 300`、`temperature: 0.7`、`top_p: 0.8`、`top_k: 20`、超时120秒；预算12288/2048/2048；只允许已计划think=false，预算/上下文关系不变 |
| models：共享高级项 | `host: 127.0.0.1`、`port: 8765`、`max_concurrency: 1`、`queue_limit: 5`、`queue_wait_seconds: 30`、`cleanup_seconds: 5`；保留180秒provider总预算约束 |
| chat：`chat` | `history_turns: 8`、`user_cooldown_seconds: 5`、`session_queue_limit: 2`、`session_queue_timeout_seconds: 600`；不把限额误述为实际生成/上游调用次数 |
| chat：`participation` | `mode: mentions`；debounce 2秒、最大等待5秒、评估间隔5秒/每分钟12次、自发冷却15秒/每分钟4轮；只在授权群新消息驱动 |
| chat：窗口/队列等 | `context_messages: 60`、`context_ttl_seconds: 900`、`context_max_bytes: 32768`、`message_max_chars: 2000`、`mention_queue_limit: 8`、`max_ambient_age_seconds: 90`、`allow_ambient_web: true`；后者仍要求web开启 |
| chat：`participation.attention` | `enabled: false`；别名沿用肥鱼/大肥鱼/鱼鱼/鲸鱼娘/小鲸鱼/DSH；焦点60秒、允许插入0条、direct队列4、候选每分钟4次；仅free显式启用生效 |
| chat：`output` | `mode: plain_chat`、`quote_reply: false`、`max_reply_chars: 1200`、`delivery_mode: single`、`max_bubbles: 3`、`casual_max_chars: 80`、`bubble_max_chars: 40`、间隔800..1600毫秒；最大条数不强制凑条 |
| features：`web` | `enabled: false`、`trigger: auto`、`provider: bing_rss`；搜索1次/结果5/正文2页/超时15秒/重定向2/响应1048576字节/单页4000字节/证据6000字节/来源2；搜索质量门槛未过，开关不能越过代码禁用门槛 |
| features：`memes` | `enabled: false`；路径仍为assets/memes/inbox、assets/memes/library、config/memes.local.yaml；候选16/提示2000字节/每轮1图/冷却60秒/同图300秒/允许仅图true/单文件8388608字节/导入48；固定路径与格式/hash/像素等已有约束保持 |
| features：`memory` | enabled/learning_enabled均false；max_records 64、max_fact_bytes 16384、max_group_file_bytes 65536、max_groups 16、max_total_bytes 8388608、max_prompt_records 8、max_prompt_bytes 1536、max_proposals_per_turn 3、max_record_bytes 240；学习要求读取开启 |
| features：`vision` | `enabled: false`、`input_reserve_tokens: 4096`；4096是假设，不是已验证上界；true仍启动拒绝，不自动验证/降级/调用模型 |
| features：`members` | enabled/mentions_enabled均false；人数阈值50、count TTL60秒、roster TTL300秒、提示8项/768字节；手改desired开启时保持当前生产暂停合同，明确desired/effective差异 |
| runtime：版本/连接 | `layout_version: 1`、`schema_version: 3`；onebot host 127.0.0.1、port6200、upstream ws://127.0.0.1:6199/ws；`secrets_file: secrets/local-tokens.json`；保留回环与secrets路径边界 |

所有范围/字段组合依旧调用现有validator，不放松think、@、私聊、固定路径等限制。新模板不嵌实际账号、密码、token、家庭SSH地址或已验证标记。QQ密码保护初始化继续原机制，不把DPAPI密文或明文搬进YAML。

编辑保存只改变下一次启动候选；运行实例继续用启动快照。正常重启加载新值，不做热更新，不因提交/迁移自动启用任何开关。配置语义相同的拆分/注释/键序变更保持`session_version`；激活profile实际参数与已有相关行为字段变更仍按旧规则新建当前上下文，旧历史保留。

## 5. 发现、校验与一致加载

1. 唯一发现规则：`config/local/`完全不存在时兼容旧单文件；一旦存在，只读取该目录固定5份文件。缺失/空文件/损坏/越界等一律报错，不补读examples、旧文件或系统配置。额外YAML文件不自动加载；check列出未加载文件名，帮助发现改错文件。
2. 分层文件采用UTF-8（兼容BOM）与安全YAML映射；拒绝重复键、merge键、alias/自定义tag、错误文件归属及未知根字段。每文件≤128KiB、5份总计≤512KiB，超过就报告限额。legacy读取保持旧兼容规则，不借本任务批量重写原格式。
3. 所有分层文件必须为项目config/local下的普通文件；拒绝symlink/junction及解析后越界。秘密引用沿用secrets约束，不允许任意include、执行表达式或读取其他用户目录。
4. 先读全部字节并记固定相对路径→SHA256，再组装到现有schema3、执行`normalize_settings`与原路径校验；重新比对全部文件摘要，检测到读取中变更就失败，请保存完后再试，不自动重读循环。报错显示固定相对文件名、字段路径和可取得的行列号；不显示原行/字段值、完整YAML异常或堆栈。
5. 源摘要与语义摘要分开：source digest覆盖布局版本、固定路径及原始字节，用于并发检测；semantic digest使用规范化配置，忽略文件排版。均不代替现有session_version。只读check不打开凭据内容、不连接SSH/QQ/网页、不启动模型、不创建state或备份。
6. 正常启动在现有configuration_lock内、任何运行配置写入/进程启动之前完成全部校验与已有生产门槛检查。创建本次instance_id，将同一份规范化schema3写到忽略的`state/config-runtime/<instance_id>/settings.yaml`，记录源文件摘要、快照摘要和布局来源。快照不内联秘密，仅原引用。
7. 框架准备、gate、model及插件必须加载这同一不可变快照；显式传递项目根/instance_id/快照路径和摘要，禁止从深层快照路径反推root。现有QQBOT_ROOT可继续使用；新增环境元数据不得携带凭据。程序创建的旧快照在确认无受管引用后保留最近3次；活动/归属未知的快照不删除。state总体历史清理由原机制负责，不顺手清理旧状态。
8. 各消费者启动核对快照位置、instance_id与摘要；不匹配就正常失败退出，不能悄悄重读local凑出一套配置。启动失败只清理本次创建身份明确的进程。独立手工入口/测试可显式传legacy文件或项目根加载，不要求真实bot；不能绕过生产门槛或单独启动第二套项目。
9. 状态页只区分“当前实例已加载的快照”与“磁盘配置待下次启动”，不把读到新文件当已生效；可显示来源文件名、摘要、需重启状态与desired/effective能力状态，不输出完整配置/真实ID/秘密。

实现建议在config.py保留旧`read_settings/load_settings`签名供既有夹具，新增以明确root为参数的项目/快照解析入口；源信息用独立结构保存，不注入模型prompt或业务字段。管理写操作拿项目source digest，不能误拿启动快照digest当磁盘配置版本。

## 6. 迁移与首次初始化

仅后续明确授权后操作本机配置。实现提供`python scripts/config_files.py check`、`migrate`、`init`三个显式入口；本轮不运行。用户日常不必调用这些命令。migrate/init只写本项目配置，不启停、登录或调用模型。

`migrate`流程：持configuration_lock并require_stopped→读取旧源原字节/摘要→按旧规则规范化（含旧缺省与未知扩展）→完整原字节及摘要备份至state/config-backups→在config内唯一临时目录生成5份带中文注释的文件→重新读取并验证组装后的规范化结果与旧源相等、session_version不变→复核停机和旧源摘要→在local尚不存在时发布完整目录。必须在发布点再次确认目标不存在，不覆盖其他session/用户新目录。

模板渲染器只用于首次生成，采用固定受控模板槽位与安全序列化，保证后续值含换行/冒号/引号时仍为同一个YAML值；不得把用户文本拼成可执行语句或任意YAML结构。不依赖新包保留注释，后续加载/check/启动从不重写手工文件。

发布前失败：local不存在，旧单文件继续有效，保留备份并移除本次临时文件；发布后失败：保留完整local并明确迁移结果，由check诊断，不自动删除/回退运行。旧settings.local.yaml原字节仍保留，但新程序不再读取/合并/写它；在索引中注明只供回退，防止误以为双入口。重复migrate看到local已存在即拒绝覆盖，可运行只读check。

旧源无法规范化、存在未能完整保留的扩展或语义/session差异：不发布，报告具体文件/字段类别，留下脱敏证据；不能为迁移悄悄改模式/模型/上限或丢字段。顶层未知项放runtime.legacy_extensions，嵌套未知项留原节；原始字节备份保留注释和旧写法。

首次无配置用户可`init`复制5模板，占位身份在填写前不能启动；init既不生成秘密也不自动切本地模型。local或legacy任一已存在就拒绝init，转向编辑或migrate。本机现有token、SSH/QQ凭据、persona、图库与记忆数据不迁移不改写。

## 7. 配置cmd退役与管理动作

后续实现删除根`配置机器人.cmd`，启动/关闭/状态cmd继续保留。普通操作文档只引导到config/README与对应YAML，不再要求菜单保存；原Python脚本无参数时显示配置文件索引，不弹日常参数菜单。

现有`save_settings`和所有旧参数/群名单写命令，在local布局存在时必须拒写并指向对应文件；旧单文件兼容函数/测试可保留。只封堵显式命令不够，还要封堵底层写入，防止旧菜单或其他调用把快照/旧文件当活动配置覆盖。

需要动作的管理能力保留在原Python脚本：现有connection-init/check、clear-remote-unknown、napcat-login显式子命令继续；增加`memes-admin`与`memory-admin`，复用现有图库导入/预览/标签/目录激活与记忆CRUD/导出/确认流程，移除这些页里的普通配置开关编辑。不能因退役cmd失去LAP-21/30既有管理能力；也不要求用户通过编辑state数据库/HMAC文件来删记忆。

管理入口继承原确认、停机、摘要/锁、授权群与脱敏规则。配置读取绝不触发导入、下载、凭据初始化、unknown解除或记忆删除。memes.local.yaml作为原图库数据另在索引说明，不能和features.yaml中的发送开关混淆。维护页不能成为修改分层参数的第二写入来源。

LAP-27等旧`export-legacy-config/activate-legacy-config`不能直接套在分层快照上。分层布局中拒绝旧activate；通过下一节受控导出回单文件后，才能按既有合同做功能兼容导出/激活，不自动丢弃attention/vision/members/memory。

## 8. 回滚与兼容

当前新代码继续支持未迁移的schema1/2/3单文件；分层只改变磁盘布局，内部schema3不变。不能将layout_version称为schema4，也不能让老代码直接读取local目录。

提供`scripts/config_files.py export-legacy`：停机+锁+source摘要核对，将当前5文件组装为完整schema3，导出到忽略备份目录并报告导出/源摘要；不激活、不剥除功能、不启动。提供`rollback-layout`：操作者基于该导出明确执行，停机+锁+源/导出双摘要复核、备份当前旧文件和完整5文件；原子替换settings.local.yaml，复核导出与源未变后将local目录归档到本次备份下，旧代码才能读取最新设置。目标归档路径须确认位于项目state/config-backups；中途失败有记录可重试，不覆盖未知目标。

顺序必须是先把最新schema3写好，最后撤去local入口；若中断于中间，新程序仍以完整local为准并报告回滚未完成，不自动启动或用旧值。不要只git checkout旧代码留下过期settings.local.yaml后就启动。回退到不支持schema3或某项功能的更旧代码仍走原审阅导出/账本兼容合同；布局回滚不等于功能降级或清除unknown。

## 9. 涉及文件与实施顺序

| 顺序 | 归属文件/操作 | 完成出口 |
| --- | --- | --- |
| C34-01 | config.py及可拆出的config_files.py模块、tests/test_config_files.py | 固定映射/受限解析、source信息、兼容legacy、root显式传递；没有运行副作用 |
| C34-02 | .gitignore、config/examples/*.yaml、config/README.md、scripts/config_files.py | 注释模板、init/migrate/check、完整备份及并发/失败处理；本机文件不提交 |
| C34-03 | manage.py、configure_astrbot.py、model_gateway.py、onebot_gate.py、plugins/qq_router/main.py及实际框架夹具 | 正常启动一次解析/统一快照、实例摘要核对、真实设置生效口径；不启动本机bot验证 |
| C34-04 | configure_bot.py、napcat_login.py、observe_lap28.py及其他实际根路径调用点 | 管理动作适配项目root/source digest、split拒旧写；视觉观察仍需原独立授权，不执行 |
| C34-05 | 配置机器人.cmd、README.md、项目目录与日志说明.md、settings.example.yaml | 删除日常配置cmd；管理子命令帮助、旧入口标注与完整配置查找表；不改历史任务文档中的历史记录 |
| C34-06 | 相关tests、scripts/verify_lap34.py、reports/lap-34-*、本任务交接及进度台账 | 受影响离线回归与差异/隐私检查、commit/push；真实迁移/启动按后续授权单列 |

实施首次领取另登记session/文件归属，先核对共享文件改动。对下列合同内一般实现选择可自行处理；如果发现任何已运行入口无法绑定同一快照、迁移不能无损保留、管理动作不能保留原控制，先完成独立部分并记录缺口，不能静默降级/扩大本任务。

## 10. 验证与验收

只用临时目录、自造账号/文本与受控替身；不读取真实配置/图库/历史、执行真实migrate、SSH预检、QQ启动或模型生成。计划文档本轮只做链接/结构/差异检查，下表是实施待跑项。

| ID | 必须验证的行为 |
| --- | --- |
| CF-01 | 五模板与旧示例规范化相等；说明占位替换成自造ID后才可过校验；所有已有字段与未知扩展不丢；迁移保留当前模式/两profile/disabled状态 |
| CF-02 | 只改一个文件里的对应值，仅该设置变化；跨文件重复根节、重复键、错误归属、缺文件/损坏、越界/alias/merge/tag/超限均准确拒绝且不回退旧配置 |
| CF-03 | check零写入、零网络/模型/凭据读取；错误包含文件/字段/可得行列号，不含原始值、身份号、原行或token；新增文件未加载提示不暴露内容 |
| CF-04 | 临时目录发布前各失败点、并发改源/目标已存在、进程状态不明/在运行、磁盘写失败均不覆盖；备份原字节相等、重跑不覆盖；发布后结果可识别 |
| CF-05 | 实际启动编排替身覆盖框架准备+gate/model/router全消费者：同一快照/摘要；源文件在启动中改动不混用；缺/篡改快照使启动失败并只清理本次身份；深层路径不误算root |
| CF-06 | 注释/键序/拆分迁移不变session_version；未选profile修改不改变现有版本；所选参数变更按旧合同处理；运行实例不热更新、状态正确标待重启 |
| CF-07 | split下所有旧save/参数/名单/activate路径拒写；无参脚本给索引；图库/记忆/凭据管理仍可用且保持原确认/停机/授权/摘要约束；配置读取不执行动作 |
| CF-08 | 私聊true拒绝、黑名单仍在框架/窗口/模型/记忆前、回环与secrets路径约束；vision true拒启动、members true生产暂停、web搜索关闭门槛保持；不自动切模型/开关 |
| CF-09 | export完整schema3且不激活；rollback双摘要/备份/归档中断分支、无越界覆盖；恢复后的规范化值/session一致；pending/unknown/记忆/图库等状态未改 |
| CF-10 | Git忽略覆盖local、快照/备份/秘密；只有模板/代码/文档/自造测试可提交；保留用户persona差异，所有配置索引/说明与实际文件一一对应 |

先跑新测试及tests/test_config.py、test_configure_menu.py、test_lifecycle.py、test_lap24.py/27.py/28.py/29.py/30.py受影响部分，再用独立verify_lap34复用现有真实框架测试夹具覆盖两runner与mentions/free关键组合；不运行旧verify主程序触碰现场。loader变更影响范围大，单元全套适用；框架验证只覆盖配置加载/管理改动相关路径，不重复无关真人验收。

实施通过出口为“已实现/离线通过”；本机迁移、正常启动加载、文件层级人工接受分别记录。只有操作者后续真实使用产生证据才能标对应真实通过；本任务不能顺手关掉其他任务差额。

## 11. 规划轮交付与当时未验证项（历史）

本轮仅6份规划/交接/索引文档，按长期Git授权commit并push，核对本地与对应远端完整SHA；保留用户persona差异。未创建5份活动配置或模板、未删除cmd、未改变任何功能默认值或运行行为。

本机配置具体值/当前运行状态、模板最终可读性、迁移/回滚/快照实现、真实启动加载均尚未验证。后续由操作者设置gpt-6.1-sol/medium，按[实施指引](IMPLEMENTATION_GUIDE.md)和新的实施指令推进；不把本规划当真实迁移或启停授权。
