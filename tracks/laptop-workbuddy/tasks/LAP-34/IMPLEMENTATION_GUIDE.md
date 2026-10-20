# LAP-34 medium实施指引

返回[PROGRESS](../../../../PROGRESS.md) / [HANDOFF](HANDOFF.md) / [PLAN](PLAN.md)。本文件保留实施合同；现已实现/离线通过，交付证据与下一步见[HANDOFF](HANDOFF.md)。本机迁移/正常加载仍待后续明确授权。操作者按[AGENTS](../../../../AGENTS.md)将会话设为gpt-6.1-sol/medium；agent不得声称自动切换/检测。

## 可复制实施指令

```text
请实施LAP-34“分层配置文件取代日常配置菜单”，严格遵循AGENTS.md。

先读PROGRESS.md、tracks/laptop-workbuddy/HANDOFF.md、TASKS.md，以及
tracks/laptop-workbuddy/tasks/LAP-34/{HANDOFF,PLAN,IMPLEMENTATION_GUIDE}.md。
一个session只推进LAP-34；核对git status和文件归属，登记实施session/开始时间/涉及文件后重读。
保留已有用户或其他session差异，尤其不要覆盖/格式化/夹带提交config/persona.md。

按PLAN的C34-01→06顺序实现：
1. config/local中的bot/models/chat/features/runtime五份YAML与同名中文注释模板、config/README索引。
2. 固定字段归属/安全解析/整体校验/语义与源摘要、兼容单文件、无副作用check，以及无损init/migrate。
3. 正常启动一次解析，框架准备、gate、model、router同用一个实例快照；显式项目root，不从深层路径猜根。
4. 管理动作适配root/source digest，封堵split模式所有旧配置写入；无参脚本给文件索引。
5. 删除根配置机器人.cmd，保留启动/关闭/状态cmd；保留图库/记忆/凭据/连接管理动作与既有控制。
6. 完成export-legacy/rollback-layout、适用离线回归与文档/台账/交接，commit/push并核对远端SHA。

内部仍是schema3，layout_version单独为1。不自动改模型/后端/触发范围/账号/额度，不增付费API。
默认值沿用现有模板；迁移时用用户实际旧值，绝不把free等设置恢复成模板默认。
不热更新；日常只需关闭→编辑文件→正常启动，不加必需的apply命令或配置菜单。
未知/错误分层配置不回退旧文件；中文错误只显示文件/字段/安全位置，不输出原行/私密值。
保持web/vision/members生产门槛、私聊关闭、黑名单前置、工具隔离、单次尝试和旧验收差额。

只在临时目录和自造数据完成CF-01—10、适用单元全套及实际框架替身验证。
本实施指令先交付代码/模板/文档，不自行迁移本机运行配置、不启停/登录bot、
不读写凭据/真实图库/群记忆、不连接SSH或调用真实模型/群消息。
真实迁移/正常加载待用户后续明确指令；不能因没有做真实迁移就写成“已启用/完整验收”。
发现会改变合同的能力缺口先完成独立部分、记录并回规划，一般实现细节自行完成。
```

## 开始前的归属检查

- 本轮规划起点`main/003f04e`只有`config/persona.md`用户差异，后续以新git status为准，不假定仍相同。
- 查TASKS与PROGRESS，确认没有其他session正在改config.py、manage.py、插件或共享索引。Markdown登记不等于锁。
- 实施领取后先更新本HANDOFF与TASKS，再开始代码；不要重领LAP-18/24/28/29/31B。
- 真实bot运行状态未知；不为代码验收探活、启动或关闭现场。停机判断只在自造夹具中验证。

## 容易漏掉的实现点

1. 不能只拆模板或修改model入口：框架准备/插件/gate/model及管理脚本均要用正确root和统一来源。
2. 深层快照不再满足`config_path.parent.parent == project_root`。旧显式文件API保留兼容，新的项目root入口单独设计；测试覆盖所有实际入口。
3. config.local目录存在但缺文件必须报错，绝不把examples当运行默认覆盖层。模板5文件语义必须等于规范化后的旧示例。
4. source digest覆盖原始字节，用于迁移/管理并发复核；session_version按现有语义函数，不能改用文件hash。
5. check必须零写入。正常启动可生成忽略快照，但不得重写用户注释文件。快照/备份不内联秘密，也不提交。
6. 模板渲染按安全序列化写槽位；字符串带换行/冒号/引号不会注入新字段。拒绝重复键/alias/merge/tag。
7. split存在时在底层拒绝save_settings与旧activate；旧参数写命令不得绕过。保留的admin动作不能成为第二套参数编辑器。
8. 菜单原来拥有图库/群记忆管理能力；退役cmd后给memes-admin/memory-admin入口，复用动作/确认/锁，不要求编辑受保护记忆文件。
9. 不用require_members生产激活门槛把原本可暂停的手改desired配置一律改成全bot启动失败；保持既有desired/effective合同。vision则保持原启动拒绝。
10. rollback-layout导出的是当前完整schema3；不调用旧“剥除新功能”导出来充当布局回滚。所有pending/unknown/clean-up与数据状态保留。

## 验证记录与交接

报告按CF-01—10列出命令、结果、可证明范围与未做项。先针对新测试/受影响单元修复，再跑适用单元全套与独立实际框架夹具；不要运行可能连真实环境的旧verify主程序。

交接至少记录代码/模板是否实现、离线结果、本机是否迁移/加载、真实/完整验收是否发生，以及保留的用户差异与旧差额。Git只提交本任务归属文件；push后git ls-remote核对对应分支完整SHA。

## 实现后由操作者执行的日常流程

首次迁移须先完成上述离线验证；用户明确授权后，持锁确认项目已停机再运行`migrate`。若运行中或状态不明，只报告不能迁移，不擅自停进程。迁移不能丢当前free/后端/profile等实际值，也不自动启动。

之后打开config/README查表，编辑config/local下对应文件，保存后正常启动即可；check为可选提前校验。角色正文仍编辑config/persona.md。需要收藏导入或删除记忆时另用明确的管理动作，读配置不执行这些动作。
