# LAP-24：6.1-sol/medium实施指引

2026-10-21续作：自动登录与shell:startup使用[新PLAN](AUTOSTART_PLAN.md)和[新medium指引](AUTOSTART_IMPLEMENTATION_GUIDE.md)。本页自然分条/密码回退是旧交付合同，勿重新按第7节复制全文重做；真实免扫码和数据归属仍未验收。

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [HANDOFF](HANDOFF.md) / [详细PLAN](PLAN.md)。2026-10-18由用户指定的max规划职责补齐；本文件是后续实施模板，本轮没有实施。

## 1. 授权与领取

操作者在会话设置选择gpt-6.1-sol/medium后发送第7节指令。不得声称项目文档自动检测或切换了设置，不自动创建/派发另一个聊天或sub-agent。

只领取LAP-24这一任务的实施续作。先读AGENTS→PROGRESS→工作线HANDOFF/TASKS→本目录HANDOFF/PLAN/本指引；检查最新git status及相关diff。领取时登记新的session标识/标题、开始时间和文件归属，更新现有24 HANDOFF/台账并写后重读；不新建根HANDOFF，不重复领取LAP-16/20/21/22。

默认实施范围为代码、合成离线/实际框架验证、文档、commit/push及SHA核对。**不启停/登录bot，不认证真实WebUI/QQ，不读取/保存/使用聊天中给出的密码，不填写本机凭据/身份记录或settings，不调用真实模型、SSH生成或群消息。** 不读取日常QQ/WorkBuddy资料。原AGENTS授权和不变边界全部继承。

## 2. 第一阶段：自然条数独立交付

| 步骤 | 实施与退出条件 |
| --- | --- |
| B01 共用规则 | persona.py统一生成闲聊表达约束，覆盖free、adaptive、media提前返回分支；能1条讲清就1条，确有独立补充才2/3条，不凑字数/条数/表情。single有效文字条数仍1，不能被多条示例覆盖。 |
| B02 精简人设 | persona.md移除15—60字的最低篇幅暗示，保留性格、短应声和认真解释。角色材料不固定成每轮1条，也不改变free上下文/权限；不改本机settings或图库。 |
| B03 原路径保持 | 不改协议字段、kind语义、超限合并/不丢尾、single普通纯文本、silent/@、工具隔离、可信metadata、ACK/历史恢复或延迟数值；表情只在必要时选择且计入总量。 |
| B04 离线验证 | 核24个提示组合及web/认真回答，生产两处compose结果一致；合成1/2/3文字、answer1、silent0、1文+1图/2文+1图、容量不足/图片不可用的数量与ACK。max=1不受2/3条示例误导，不新增概率或机械字数切段。 |
| B05 框架回归 | 使用现有两后端真实runner的底层替身，沿LAP-22实际run_agent生命周期验证发送，不能手动补链。运行受影响测试及LAP-20/21/22必要用例，不能只检查提示里出现了某几个字。 |

合成用例只证明路由、数量上限、ACK及保存一致；语气/条数选择仍需后续真实模型及用户接受。不要为了凑齐1/2/3比例强迫所有较丰富的问题发3条。普通single无表情时继续纯文本协议，不把本次修正扩大为协议迁移。

## 3. 第二阶段：登录数据归属与单次回退

### A01 只读归属门槛

现有启动器已传bot.qq，不再复制一个quick.bat当作持久化修复。固定安装路径≠原生QQ数据路径，NAPCAT_WORKDIR≠原生QQ登录目录。只核对有创建身份的项目进程、静态启动配置和可取得的原生路径证据；不要枚举个人目录/账号库来猜路径。

本计划尚无已验证的Windows原生data root覆盖方法。未取得可靠证据时明确data_scope=unverified，并交付已完成的B阶段/密码回退代码和离线证据；不创建伪“已核实”身份记录，不改注册表/Windows用户/日常QQ目录，不改bundle、不复制票据或Registry20、不重置GUID。缺口保持未完成，回到规划；不能借“用户给过密码”跳过目录归属。

### A02 密文配置与菜单

- 按PLAN A4的精确schema实现`secrets/napcat-login.local.json`，密文内部为qq_password/webui_token；缺失/关闭默认不启用。基于CurrentUser DPAPI、禁止UI、stdlib ctypes实现；合成数据可做本机DPAPI往返测试，不接触真实密码。
- 提供`napcat-login status / set-password / clear-password`，连接页增加子入口并保留原1—6编号。只允许本机getpass无回显录入，不做password argv/stdin重定向/回显或聊天取密，不自动扫描旧秘密。取消/异常不破坏原文件。
- 复用configuration_lock/require_stopped及摘要冲突检查；启动已经持锁时不再次重入。私密原子文件/备份只在secrets内，不写通用state配置备份。资源上限、未知字段/布尔/账号校验、路径归属按PLAN。
- 归属未证实可保存为关闭，但不得启用；实现阶段不替操作者实际保存任何秘密/启用回退。clear只移除回退密文，不删设备、历史或尝试账本。

### A03 固定WebUI客户端与账本

**本版明确禁止把QQ密码放入NapCat环境。** 安装包会重启并继承Worker环境；父进程删变量不是一次性保证。采用PLAN A2/A3已核对的固定WebUI方案，不由medium临场在两方案中选。

| 决策点 | 要求 |
| --- | --- |
| 触发 | 只在用户日后启动一个新项目实例、显式启用回退、凭据匹配、项目数据归属和6099受管监听身份核验通过时执行。status/健康/预检/幂等start/模型请求均不触发。 |
| 原生快登 | 先让原生流程尝试；已在线/二维码已扫描/正在初始化或重连就不提交密码。至少连续两次明确未登录、扫码未接受且waiting_qrcode才满足稳定条件；未知/缺字段不满足，不登出其他账号。 |
| 认证 | 固定127.0.0.1:6099/api/auth/login，hash为SHA256(WebUI token+'.napcat')，只在内存使用data.Credential作Bearer。QQ passwordMd5与WebUI hash是不同协议数据，不混用。 |
| 成败包络 | HTTP200仍须验证整数code=0、data类型及允许字段；code=-1不是成功。2FA/验证码/新设备要求均转人工普通二维码，不获取种子/签名URL，不自动调用挑战后续接口。 |
| 请求上限 | PLAN A3固定5类路由、合计最多8次HTTP、20秒总期限、单次≤3秒/正文≤64KiB，状态检查最多4次。无代理/重定向/可配置任意路由，无后台登录循环。 |
| 尝试占位 | 在已有启动锁内、PasswordLogin POST前原子写`state/napcat-login-attempts/<instance_id>.json`，记录本实例+目标摘要的attempting；占位失败不发。重复/中断/超时/坏账本不可重放；新实例另建记录，保留旧unknown。 |
| 环境 | 清理所有受管子进程继承的NAPCAT_QUICK_PASSWORD、NAPCAT_QUICK_PASSWORD_MD5、NAPCAT_QUICK_ACCOUNT；不设置新的秘密环境变量，不改全局环境。 |
| 确认 | 接受密码请求≠在线；核对GetQQLoginInfo.uin与gate self_id/在线。通道未就绪显示channel_waiting，无二次认证。停止/身份失效可取消，有结果不明则记unknown。 |
| 输出 | 仅固定类别/布尔/计数，不记录昵称、头像、账号列表、密文/摘要/挑战/原始错误；process_host日志白名单保持。 |

客户端不提供任意HTTP代理或OneBot/模型调用入口。已记录attempt不能因Worker重启、重复启动、clear-password或异常删除而再试。自动回退不可用时保持现有快登/人工扫码流程，记录原因，不为恢复登录反复启停整套bot。

## 4. 文件归属与验证

预期实现文件：persona.py、persona.md、新napcat_login.py及必要的napcat_login_client.py、manage.py、configure_bot.py、新scripts/verify_lap24.py；相关测试、README、新LAP-24报告、本目录交接与进度索引。仅发现受影响缺陷且合同已覆盖时才改reply_plan/media_protocol/router；不要预先重写这些正常路径。保留已交付LAP-21标签菜单修复。

最低验证应能抓住以下失败，而非只测试函数返回自身输入：

1. 某个compose提前返回导致自然表达约束丢失；max=1却提示3条；single被要求JSON；图片被默认补满。
2. 模型1/2/3段在真实框架链变成固定3段、重复hook发两遍、失败后补整段、ACK前保存了未发正文。
3. QQ密码或WebUI token进入argv/所有子进程环境/日志，或写在secrets外；保存中断/并发覆盖原凭据，getpass取消仍保存。
4. 假WebUI返回code=-1/2FA/新设备/错账号/超大响应/重定向，或监听不是受管PID时依然发密码。
5. 密码POST超时后再次调用、Worker重启/幂等start/状态页触发第二次尝试，或者占位写失败后仍发出请求。

默认测试秘密/账号/群消息/图片均人工构造；管理API用替身或临时本机假服务，绝不连接真实6099。使用项目.venv运行受影响单元；实际AstrBot框架用runtime/astrbot-tool/astrbot/Scripts/python.exe、按原验证脚本要求在runtime/astrbot工作目录运行。不要以--real作为健康检查或验证参数。

新verify_lap24.py可复用`verify_lap20.verify(root, backend, mode, full_lifecycle=True)`和`verify_lap21.verify(root, backend, mode, participation)`，用临时项目/禁用metrics并加本任务1/2/3条场景，结果仅写新lap-24报告。旧20/21/22脚本的main硬编码旧报告路径，不直接执行这些入口覆写历史证据；也不把既有历史通过数量抄成24本次通过数量。单元命令从项目根使用`.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests`，框架入口使用新verify_lap24.py。

B阶段能独立完成；A01能力缺口不取消B交付。A阶段可标“客户端/配置已实现、离线通过”，但数据目录未核实或未做实际登录时，“登录持久化真实通过”必须保留未完成。没有真实模型时不得标“固定三条问题已被真实修复”。

## 5. 完成、Git与回滚

完成后在HANDOFF逐项列B阶段、数据目录、密文配置、客户端/账本、离线、真实验收的状态和剩余；同步TASKS/PROGRESS/README。保留LAP-10/18及旧真人差额，明确未改本机配置/未操作bot。执行检查后只提交本任务文件，commit/push并核对完整SHA，报告其他差异；不夹带秘密、原始群消息、用户图片或其他session修改。

回滚沿PLAN第7节：只撤本任务代码/提示词与启用设置，先协调本项目实例；保留设备/历史/图库/pending/unknown账本。不能删除账本重试结果不明的密码请求，不用重置GUID/复制日常QQ票据解决失败。

## 6. 用户日后另行指定的真实验收

默认实施指令不含此节执行。登录验收须明确实例负责人、允许启停/登录的范围及最终状态；先暂停模型准入，操作者通过本机无回显入口录入，必要时人工扫码，再在同Windows身份/同已核实目录下正常重启两次观察。每次只记录快登是否成功、是否扫码/验证码及账号/通道匹配，不输出秘密。仍需反复验证就记录差额，不循环尝试。

自然表达先在脱离QQ群的合成窗口做所选后端真实生成，待用户另外给出后端/请求上限/可用时段后执行；群验收再单独指定授权群和是否允许发图。短应声/感谢通常1条，有补充可2条，真正需要时3条；不要求人为配比。记录脱敏计数和用户接受，不保存私密正文。

## 7. 给medium的可复制指令

```text
阅读 E:\CodexWS\QQbot\AGENTS.md 和 PROGRESS.md，按 tracks\laptop-workbuddy\tasks\LAP-24\PLAN.md 与 IMPLEMENTATION_GUIDE.md，仅领取并实施LAP-24。先读活动HANDOFF/TASKS和24交接，登记session/时间/文件归属并重读。
先修自然分条：最多三条只作上限，短应声一句即可，有实际补充才两三条，认真回答完整单条；统一free/adaptive/media提示，移除最低字数暗示，表情不凑数。保留single/协议/ACK/历史/触发/黑名单/后端与现有配置数值。
再做登录独立部分：先核实项目QQ数据归属，缺口如实回规划；实现本机DPAPI无回显配置及固定WebUI单次密码回退，先记账后POST，同实例不重试，不向NapCat或其他组件环境注入口令。当前计划没有证实Windows原生数据目录覆盖方式，不得猜路径迁移、改日常QQ或重置GUID。
完成受影响单元、两后端runner底层替身和实际run_agent合成回归、文档及commit/push并核对完整远端SHA。只用合成秘密/图片/群消息；不填写本机凭据或运行配置，不读取/使用聊天密码，不启停/登录/认证真实bot，不调用真实模型或发群消息。保留其他session修改与未验差额，不自动进入真实验收。
```
