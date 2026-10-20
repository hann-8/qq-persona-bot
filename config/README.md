# 配置文件索引

日常流程：关闭机器人 → 编辑对应文件 → 保存 → 使用根目录“启动机器人.cmd”正常启动。没有apply步骤，不热更新。可选先运行 `.venv/Scripts/python.exe scripts/config_files.py check`。当前实例继续用启动时快照；状态页将已加载快照与磁盘候选分开显示。

| 想修改什么 | 本机文件 | 根字段 / 模板 |
| --- | --- | --- |
| QQ、授权群、管理员、前置黑名单 | `local/bot.yaml` | bot、access；[模板](examples/bot.yaml) |
| 显式选择后端、模型、双profile、预算；高级队列 | `local/models.yaml` | llm；[模板](examples/models.yaml) |
| mentions/free、关注别名、合批/频率、自然分条、历史 | `local/chat.yaml` | chat、participation、output；[模板](examples/chat.yaml) |
| 联网、表情发送、群记忆、识图、成员/@ | `local/features.yaml` | web、memes、memory、vision、members；[模板](examples/features.yaml) |
| 高级回环连接、版本、秘密文件引用 | `local/runtime.yaml` | layout_version、schema_version、onebot、secrets_file、legacy_extensions；[模板](examples/runtime.yaml) |
| 角色正文 | `persona.md` | 独立文件，保持原路径 |
| 图库名称、标签、登记 | `memes.local.yaml` | 图库数据，由memes-admin维护；与features里的发送开关不同 |

五份`local`文件全部存在且有效才会加载；目录一旦存在就不回退、不合并`settings.local.yaml`或examples。额外YAML不会自动加载，check列出未加载文件名。不支持include、环境变量插值、锚点/别名、合并键、显式tag、重复键、跨文件字段或链接/junction。单文件最多128KiB，总计512KiB。错误只显示文件/受控字段/安全位置，不回显原行或私密值。UTF-8兼容BOM，读取/check/启动不改手写注释。

`layout_version: 1`是磁盘布局，内部仍`schema_version: 3`。`runtime.legacy_extensions`仅保留旧配置未知顶层项，不保证功能，通常不用编辑，不能与已知字段冲突。嵌套扩展沿用原验证规则。source digest覆盖原始字节和固定路径；semantic digest覆盖规范化配置；均不替代原session_version。注释或未选profile的编辑不会改变当前会话版本。

新装默认仍CodeBuddy/deepseek-v4.1-flash、mentions、single；web/memes/attention/vision/members/memory/learning默认关闭。推理强度受模型能力元数据约束；CLI原生窗口仍仅null，预算是可见UTF-8字节保守计数，不是精确token或积分。本地模型仅显式选择，不自动下载或切换；启用前须核对digest。模板每个字段标明用途、单位/选项、新装默认与重要约束。

迁移保留实际旧值，包括free、两个profile和所有开关，不能拿模板默认覆盖。私聊固定关闭、黑名单前置、单次尝试和工具隔离不变。web搜索质量门槛仍关闭；vision true仍拒启动；members desired开启仍生产暂停，不能用手写字段冒充验证。记忆学习必须同时开启读取。

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
