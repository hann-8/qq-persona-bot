LAP-24可选管理token独立于五文件配置和QQ密码，仅用`scripts/configure_bot.py napcat-login set-observer-token / clear-observer-token / observer-status`管理；无回显TTY录入、停机/配置锁/原子保存，CurrentUser DPAPI密文在忽略的`secrets/napcat-observer.local.json`（schema1/16KiB）。status只检查文件schema，不解密/认证；没有token不阻断原生快登，不能解除data_scope。登录观察和Startup命令见[根说明](../README.md)，本轮仅代码/离线交付，真实录入、登录和部署未执行。

# 配置文件索引

模板和本机文件均在每个参数旁写中文注释，列表参数在列表名旁说明。注释中的“新装默认”只供参考，不会覆盖右侧当前值；既有用户备注保留。`participation.mode`控制mentions/free，`output.mode`固定plain_chat，分条方式另由`output.delivery_mode`控制。

日常流程：关闭机器人 → 编辑对应文件 → 保存 → 使用根目录“启动机器人.cmd”正常启动。没有apply步骤，不热更新。可选先运行 `.venv/Scripts/python.exe scripts/config_files.py check`。当前实例继续用启动时快照；状态页将已加载快照与磁盘候选分开显示。

| 想修改什么 | 本机文件 | 根字段 / 模板 |
| --- | --- | --- |
| QQ、授权群、管理员、前置黑名单 | `local/bot.yaml` | bot、access；[模板](examples/bot.yaml) |
| 显式选择后端、模型、双profile、预算；高级队列 | `local/models.yaml` | llm；[模板](examples/models.yaml) |
| mentions/free、临时停言、关注别名、合批/频率、自然分条、历史 | `local/chat.yaml` | chat、participation、output；[模板](examples/chat.yaml) |
| 联网、表情发送、群记忆、识图、成员/@ | `local/features.yaml` | web、memes、memory、vision、members；[模板](examples/features.yaml) |
| 高级回环连接、版本、秘密文件引用 | `local/runtime.yaml` | layout_version、schema_version、onebot、secrets_file、legacy_extensions；[模板](examples/runtime.yaml) |
| 角色正文 | `persona.md` | 独立文件，保持原路径 |
| 图库名称、标签、登记 | `memes.local.yaml` | 图库数据，由memes-admin维护；与features里的发送开关不同 |

五份`local`文件全部存在且有效才会加载；目录一旦存在就不回退、不合并`settings.local.yaml`或examples。额外YAML不会自动加载，check列出未加载文件名。不支持include、环境变量插值、锚点/别名、合并键、显式tag、重复键、跨文件字段或链接/junction。单文件最多128KiB，总计512KiB。错误只显示文件/受控字段/安全位置，不回显原行或私密值。UTF-8兼容BOM，读取/check/启动不改手写注释。

`layout_version: 1`是磁盘布局，内部仍`schema_version: 3`。`runtime.legacy_extensions`仅保留旧配置未知顶层项，不保证功能，通常不用编辑，不能与已知字段冲突。嵌套扩展沿用原验证规则。source digest覆盖原始字节和固定路径；semantic digest覆盖规范化配置；均不替代原session_version。注释或未选profile的编辑不会改变当前会话版本。

新装默认仍CodeBuddy/deepseek-v4.1-flash、mentions、single；web/memes/attention/vision/members/memory/learning默认关闭。推理强度受模型能力元数据约束；CLI原生窗口仍仅null，预算是可见UTF-8字节保守计数，不是精确token或积分。本地模型仅显式选择，不自动下载或切换；启用前须核对digest。模板每个字段标明用途、单位/选项、新装默认与重要约束。

迁移保留实际旧值，包括free、两个profile和所有开关，不能拿模板默认覆盖。私聊固定关闭、黑名单前置、单次尝试和工具隔离不变。当前web搜索须同时启用web.enabled/search_enabled，个人试用不宣称质量已过；vision true须有配对运行许可（包括LAP-43明确待用户实测试用）；members仍逐次按来源/人数/双TTL判定，不能用手写字段冒充验证。记忆学习必须同时开启读取。

## 首次建立与迁移（均须显式操作）

当前交付仅代码/模板；本机尚未迁移或验证加载。由操作者后续明确授权后执行；运行中或状态不明则拒绝，命令不会替你关闭机器人。

```powershell
# 新用户没有local和旧单文件时：创建五模板；填完QQ/群/管理员占位后才能启动
.venv/Scripts/python.exe scripts/config_files.py init
# 现有用户：停机与锁内保留实际旧值、原字节备份，完整目录一次发布
.venv/Scripts/python.exe scripts/config_files.py migrate
# 可选零写入校验；不读取凭据、不连接SSH/QQ/网页、不调用模型
.venv/Scripts/python.exe scripts/config_files.py check
```

`init`不生成秘密；任一旧入口已存在就拒绝。`migrate`不覆盖已有local，失败前未发布则旧源继续有效；发布后保留完整目录并明确结果。旧`settings.local.yaml`保持原字节，迁移后只供备份/回退，不再是新程序配置入口。备份在忽略的`state/config-backups/`。秘密仍只保留项目secrets内引用，persona、真实图库、群记忆、凭据不迁移。

## 需要执行的管理动作

```powershell
.venv/Scripts/python.exe scripts/configure_bot.py memes-admin
.venv/Scripts/python.exe scripts/configure_bot.py memory-admin
.venv/Scripts/python.exe scripts/configure_bot.py napcat-login status
.venv/Scripts/python.exe scripts/configure_bot.py napcat-login set-password
.venv/Scripts/python.exe scripts/configure_bot.py napcat-login clear-password
.venv/Scripts/python.exe scripts/configure_bot.py connection-init
.venv/Scripts/python.exe scripts/configure_bot.py connection-check
.venv/Scripts/python.exe scripts/configure_bot.py clear-remote-unknown REMOTE_CHECKED_STOPPED
```

以上动作继承各自停机、确认、摘要、锁、授权群与脱敏控制；connection-check是明确的零推理联网检查，不属于配置加载。图库保留导入/预览/标签/目录激活；记忆保留查看/导出/新增/确认/固定/纠正/删除/清空。先在features显式开启记忆读取才能管理。密码仍只能本机TTY无回显录入和DPAPI保护；原登录能力缺口/生产拒启规则保持。读取配置绝不执行这些动作。

无参configure_bot仅打印索引；根配置cmd已退役。旧单文件API仍供兼容；split下底层save、旧参数/名单命令和旧功能兼容导出/激活均拒写。不要在维护页找参数开关，也不要手编受保护的记忆/HMAC文件。

## 布局回滚

停机后先导出当前完整schema3（保留全部功能）：

```powershell
.venv/Scripts/python.exe scripts/config_files.py export-legacy
.venv/Scripts/python.exe scripts/config_files.py rollback-layout <export路径> <source_digest> <export_digest> 已核对
```

导出位于项目备份目录，不激活。回滚在同一锁内核对停机、源/导出双摘要并备份旧文件和五文件；先写最新单文件，最后把完整local归档至本次备份。中断于两者之间仍以local为准，保留阶段记录，可修复故障后用同一导出与摘要重试。归档后旧入口才生效；不自动启动、不删除pending/unknown/图库/记忆/清理状态。回滚目录布局不等于降级功能；更旧代码不支持某功能时，须先完成布局回滚，再按原`export-legacy-config/activate-legacy-config`审阅合同降级；不直接checkout旧代码配过期单文件启动。

正常启动只解析一次磁盘候选，在配置锁内校验和生产门槛检查后生成`state/config-runtime/<instance_id>/settings.yaml`与source.json。框架准备、gate、model、router核对同一实例路径/摘要，显式root，失败不悄悄重读。快照不内联秘密；程序仅在可证明无活动/未知归属引用时保留最近3份，其余状态仍由原机制维护。local、快照、备份、秘密均不提交。

## 群临时停言（LAP-35）

`local/chat.yaml` 中唯一新增设置为 `participation.silence.enabled: true`，缺省true。开启只表示接受控制，各授权群启动时仍为普通。仅本机access.admin_users中唯一操作者的真实sender可明确暂停/恢复。操作者发真实@加“暂停发言”后，本群不确认、不发表情；仅本人真实@加“恢复发言”或明确叫名“鱼鱼可以说话了/继续说话”才能恢复。普通成员命令和任何人的裸@均不能解除暂停；同条暂停优先。别名复用 `participation.attention.aliases`，不因此开启叫名回复。模糊、否定、引用/转述或超长表达不保证识别，不额外调用分类模型。

状态只在gate内存中。gate/完整bot/电脑重启回普通；WS、QQ离线、插件或模型重连不解除，没有自动超时。恢复后继续原有free/mentions合同；不补答哑巴期间消息、不清历史/记忆，不解除真实unknown/清理阻断。已经提交到QQ的消息可能晚到，无法撤回；旧结果不能借唤醒后的新状态发送。

配置下次正常启动生效；关闭能力须显式设false，省略仍为true。运行态、门票不进人设、模型输入或session_version。状态页只显示开关/静默群数；`state/gate-connection.json` 是散列群标识的诊断镜像，禁止手编，也不用于重启恢复。

LAP-34的 `config_files.py export-legacy` 导出完整schema3（包含silence）。退回35之前的代码时，先完成受控布局回滚，再用 `configure_bot.py export-legacy-config` 做功能兼容审阅导出；后者剥除silence及原attention/vision/members/memory节，须核对源/副本双摘要并备份后显式激活。两种导出用途不同，不直接修改启动快照。本轮仅离线交付，本机配置未改、未加载；真实QQ验收另行授权。

## 图片入站诊断字段

`features.yaml` 的 `vision.ingress_diagnostics: false` 只控制准入后封闭元数据日志，下次正常启动生效；不触发下载、推理或生产放行。本轮未改 `config/local/`。`vision.enabled` 仍默认 false，显式 true 仍因可信预算/真实质量缺项拒启。`allow_get_image_fallback` 尚未实现，不应手工加入配置；需后续真实观察证明第一图仅有安全 opaque ID 后，按 I3 单独实施。见[阶段A报告](../reports/lap-28-A-2026-10-21.md)。


LAP-18B补充：`features.yaml`新增`public_network`（resolver=system、ca_bundle_file=null）及`web.extractor=readability`、`web.long_text_policy=excerpt`。resolver仅system/cloudflare_doh；固定Cloudflare HTTPS及1.1.1.1 bootstrap，失败不切换。CA仅允许项目忽略的`secrets/public-network-ca.local.pem`，格式/路径/CA属性由公共传输严格校验；不自动创建或填写。正文模式仅readability/legacy，长文策略仅excerpt/reject。六区节选和元数据共享最多6000字节，并受最终整体预算进一步限制；完整要求超限直接拒绝。

这些字段随五文件源摘要、规范化语义摘要、实例快照、兼容单文件导出及会话版本一起生效；不会自动修改已有web.enabled。此轮没有迁移或保存真实local/CA。网络状态仍network_unverified、搜索质量门槛false，需后续本机安全TLS/公网/公开正文质量证据；详见[报告](../reports/lap-18-B-2026-10-21.md)。


## B站字幕已退役（LAP-42）

不再提供字幕运行服务或配置入口。旧 `bilibili.enabled=false` 节兼容保留，true明确拒绝启用；新模板不再提供此节。普通网页正文读取保留，视频链接不能代替视频内容。

旧报告和材料 schema 保留用于历史解释，不是恢复字幕的入口。旧专用报告脚本已不适用于当前运行版本，不重跑或覆盖其报告。

不读 SESSDATA、不抓字幕、不做 ASR；已有本机凭据文件不读取、不删除。

缓存仅RAM的有界编码材料，键含群隔离epoch、bvid/cid/P、语言、认证模式/凭据RAM摘要、配置/网络/提取版本；600秒内最多32条/4MiB，每条含预留开销不超过128KiB，0禁缓存，重启清空。只共享材料，不共享最终问题或答案；配置/认证变化不复用。配置进入快照/版本及五文件映射；旧代码回滚用原有双摘要审阅导出的兼容副本，先正常停止并保留unknown/pending/清理账，不直接删除字段或历史。首次启用使用已有v2材料/ACK管道，不依赖开启图片/群记忆/成员能力。

## 网页相关选材（LAP-18C）

`features.yaml`的`web.selection_policy`仅coverage/question，默认coverage；缺字段的旧配置保持六区节选。question从当前目标问题提取最多32个英文/数字/代码词项或中文二元词组，只在RAM选相关完整段落/相邻上下文，不使用历史或额外模型。纯总结/无词项保留coverage；无可靠命中或节选不足1200字节明确失败。所有元数据共用最多6000 UTF-8字节及最终输入预算，完整要求仍超限拒绝。

字段随原五文件源摘要、语义摘要、实例快照、兼容导出和会话版本保存；下次正常启动生效，不热更新。readability模式内部升级为显式main/role=main/article优先，候选不合格/不确定才对同一RAM文档用readability；legacy仍为操作者显式回滚选择。full仅表示提取主体全部入包。公开模板/中文旁注已同步，本机local/persona未改；web默认false、搜索质量门槛false不变。

当前网络证据以[LAP-38](../tracks/laptop-workbuddy/tasks/LAP-38/EVIDENCE.md)为准：部分公共正文成功且仍超时，不再沿用18B当时全非公网结论。18C仅代码/离线通过，真实材料质量、模型与QQ/ACK验收未完成，见[18C报告](../reports/lap-18-C-2026-10-23.md)。

## LAP-40 QQ传输静态接口

阶段4A补充：独立控制秘密文件只读接受`{"schema":1,"key":"64位小写十六进制"}`，32字节密钥不得复用模型/OneBot/admin/context token，不通过命令行或环境值传递。缺失/字段异常/复用均closed。当前真实Snow启用仍总拒绝，尚无合格私有入口；原创固定spec/owner writer/控制消费仅离线验证，不应手写runtime owner或伪造proof绕过。管理状态使用已加载snapshot的provider；snapshot丢失/损坏时报unknown且关闭准入，停止仍按已登记创建身份回收，不读磁盘provider猜测。

`runtime.yaml`可选增加`qq_transport`，旧单文件也识别同名根节。缺少此节时仍为NapCat；消费层解析默认值，不向旧规范化对象或实例快照回填字段，因此旧schema1/2/3的语义摘要不变。只有实际存在的节参与校验；旧`legacy_extensions.qq_transport`会报冲突，须人工审阅。示例完整字段均有同行中文说明，现有local与人设不会自动重写。

当前LAP-40阶段1/2已交付配置/provider/静态检查，以及原创早期策略、独立健康协议、实际gate/router时效栅栏；4A补齐初始owner登记、固定spec、nonce轮询与drain/stop消费的项目侧离线闭环。上游私有接线、真实控制监听/受管启动、恢复和activate/rollback仍待后续阶段。默认没有受管健康绑定就关闭Snow准入，不能把文件存在当作已部署或切换。所有设置在显式停机保存、下次受管启动后才可生效，不热更新，不自动fallback。

4B1恢复预算/监督已项目侧离线验证，默认`recovery.enabled=false`保持；启用但未明确停机准备的预算为closed，watch不补空账。首次准备API供后续4B2 CLI接入，本阶段没有activate/rollback/trial或采样命令。每事故一次动作，QQ恢复同时占Node与QQ预算；坏账、时钟回拨、cleanup/发送未知只转人工。原生/私有资格仍未满足，真实恢复与QQ3/3免扫码均未通过，不能因已有恢复代码或allow_qq_restart=true启动真实组件。

只读检查：`python scripts/transport.py inspect --json`（可用`--root`指定项目根）。输出当前选择的provider及`snowluma_candidate`静态检查范围；`channel_ready`始终false，与现有NapCat在线状态无关。不联网、不启动进程、不读控制密钥、不读取QQ认证数据、不写配置/状态。缺包等返回封闭阻断码；CLI退出0表示检查完成，不表示真实准入。无有效配置时退出1，仅输出`transport_config_invalid`。

`snowluma`路径相对项目根：官方包根在runtime，干净专用QQ入口在runtime，证明在state，独立控制密钥引用在secrets。拒绝越界、Windows设备名/备用数据流、链接/重解析点及端口碰撞（含6185/6099和现有gate/model端口）。控制密钥不能复用OneBot/SSH/B站凭据引用；其32字节内容与运行监听身份由后续阶段核验，本检查不打开秘密文件。默认控制端口5098、采样5秒/TTL15秒、等待180秒，TTL至少为采样的3倍。恢复默认false、QQ重启默认false；标志本身不能证明3/3免扫码或授予动作资格。

本机静态证明格式固定为`qqbot-snowluma-static-proof-v1`，JSON拒重复/未知/缺失字段，最多16KiB。根字段为`format/release/tag_sha/bundle/native_deployment/clean_qq/data_scope/private_build`：

- `release=v2.1.1`、`tag_sha=f8cb15c27bca3d2d1bd044a921e55bfc44bb5e60`固定在代码；不允许配置跳过。
- `bundle`严格含`file/sha256/size`，文件须为官方`SnowLuma-v2.1.1-win-x64.zip`，42,694,125字节、SHA256 `c739171f95c27706767e69ba36099707c222fcec639b46f4d59689997b527772`；只哈希操作者自行准备的原包，不下载/解压/复制。
- 其余四节必须有`evidence_file/evidence_sha256`，引用`state/qq-transport/`中的本机证据（每份最多1MiB）。`clean_qq`另有`executable_sha256`绑定配置QQ入口；`private_build`另有`build_file/build_sha256/policy_file/policy_sha256/policy_version`，文件须在忽略的`runtime/snowluma-private/`，策略版本固定`qqbot-snowluma-policy-v1`。

`static_evidence_checked=true`仅表示所有所引文件的实际摘要匹配，不证明证据内容的真实性、许可适用、干净QQ/原生数据归属、真实私有接线或实时健康。检查始终保留`native_deployment_unverified/clean_qq_unverified/data_scope_unverified/private_build_unverified/operator_scan_required`；后续受控审阅与独立健康不能被静态JSON代替。没有预备材料时保持缺失，不生成或填写伪造证明；本机证明、原包、私有构建与账号资料不提交Git。

Snow运行准入另要求online/good、已armed且pipe/login/rx/outbound健康、独立nonce/HMAC/严格seq、加载快照/策略/构建摘要及受管PID创建身份/监听归属共同成立。证明TTL按配置15..30秒，router镜像按同一证明剩余期限关闭，不沿用旧45秒。没有新WS帧时gate也按证明/online实际到期定时撤销能力并轮换事件代际；新证明不会复活旧事件或迟到模型结果。入站、free窗口、成员/视觉/收藏RPC、最终发送都检查同一准入；健康/控制ACK继续可观测。NapCat分支保留旧行为，不要求Snow证明。协议字段/接口与自造测试见[原创适配说明](../adapters/snowluma/README.md)，实际上游接线与真实验收仍未通过。

### LAP-40 有限CLI事务与采样

尚未切换SnowLuma；生产资格仍总拒。命令均为`python scripts/transport.py <command>`，可加`--json`；`--root`是项目根目录。inspect/`verify --offline`/trial-status只读本项目配置与封闭证据，不读登录资料或调用模型。

- `prepare-policy`：必须停止自有实例；仅写原创policy、全新32字节独立控制key、候选记录和首次预算。已准备或部分失败不能自动重置预算/事故，不复用现有凭据，不复制原生组件。
- `activate --provider snowluma`：资格齐全且停止后才可提交。当前私有入口缺失，资格总拒在任何激活状态/配置写入之前；无自填manifest旁路。未来事务仅拥有provider标量，原字节备份在忽略state，五文件只改runtime.yaml，单文件也支持；实际候选字节整体校验，源摘要变化拒绝。
- `capability-probe --authorize-owned-qq --timeout 240`：当前前置缺失直接返回阻断；尚未交付真实QQ探测执行，不扫描/绑定现有QQ。
- `trial-start`：仅已选Snow、旧实例确认退出和真实资格才调用既有管理创建一次；源摘要在管理锁内再查。当前总拒，无实际试验。trial-status报告UNKNOWN/连续段及封闭计数，不能把安静群当故障。
- `rollback`：只接受本任务完整激活账本；若有已完成登记的trial，仅停止该instance的受管进程，再核验确退。未知/部分/实例变化拒绝。恢复仅本次provider字段；无后改时原字节还原（含BOM/引号/无尾换行），无关后改保留，provider后改拒绝覆盖。不自动启动NapCat，不清理登录、人设、记忆或事故预算。

采样由gate既有健康任务消费，没有新增进程/监听/nonce客户端。从首次真实channel_ready开始，每60秒记录封闭布尔/计数、核验PID的RSS/句柄与允许项目目录的元数据字节；不存QQ号、消息ID/echo、正文或栈。每条<=512B，采样日志总<=16MiB，按日桶保留至多14天；容量/资源/时钟/覆盖缺口UNKNOWN并断开连续段。QQ/Node/epoch/build/policy/配置摘要变化另起段，旧失败计数保留。QQ发送ACK/失败/unknown及延迟与控制ACK分开；未知不重试。72h包含于168h，但这些时间标记仍不能替代真实新消息驱动的7天收发验收。8小时中位数资源趋势须由操作者评估，不自动重启抹平；真实重新扫码的观测接线仍受阶段3缺口阻断。

## LAP-43原生联网与识图试用（2026-10-29）

`web.engine`缺省gateway兼容旧配置，本机已保存codebuddy_cli并加载。只有CodeBuddy后端支持原生engine；web.enabled=true/search_enabled=true恰开放WebSearch/WebFetch，search_enabled=false仅WebFetch，enabled=false不开放工具。其余工具/MCP禁用，dontAsk配合固定显式许可及NoDefer直接暴露；原gateway的trigger/provider/freshness/提取字段保留但不作用于原生模式，原搜索质量false不控制原生工具。

新增cli_max_tool_calls默认3且1..3，cli_max_turns默认4且1..4，cli_tool_result_bytes默认8000且1000..8000；本机均取默认。失败计数不退还、重放不重复执行、总工具结果12000字节硬限、90秒总deadline、每步48000可见政策（含真实历史和工具描述/锁定参数schema上界），不自动扩大预算。WebFetch可能内部处理材料，限额不承诺精确HTTP/内部模型数或credits。

子进程alwaysThinkingEnabled=false，DeepSeek/low配置保留；群memory.enabled/learning_enabled均true。正常停机保存后重启，health展示engine/有效工具/限额/思考开关/记忆加载值。当前已部署的识图仍为完整绑定lap43_operator_trial、pending_user_test；使用`scripts/revalidate_lap43_native_web.py`做当前check/probe/activate配对，旧43/42报告保留。联网后最终answer单条、meme_id=null、memory_proposals=[]，实际工具服务与效果由用户群测。

`access.admin_users`字段保持，但去重后必须恰好1项，不等于bot、不在blocked_users；框架名单与router/记忆管理员同源。群角色、昵称、引用或模型均不授予控制权。

识图当前`lap43_operator_trial`为操作者显式试用许可，质量pending_user_test。它绑定完整源码/配置/实际runtime/所选记录、当前定向检查与真实CLI零生成接线，继续保留预算/工具隔离/unknown限制；不代表新IQ或人工评分通过。固定私有材料位于state/lap43-vision-trial，旧IQ和人工记录不改。详情及配对备份位置见[43交接](../tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md)。旧任务段落按其日期解释。
