# LAP-24 P1/P3 自动登录观测与Startup独立交付

日期2026-10-21（Asia/Shanghai），session `LAP-24-autostart-independent-implementation`，19:21:05领取，基线main/b23d961。合同为AUTOSTART_PLAN及新实施指引；旧自然分条不重做。

## 状态和边界

已实现/离线通过：受管NapCat固定脱敏事件、独立只读WebUI观察、CurrentUser DPAPI管理token、受控login-check-only、锁外有界QQ等待、一次启动包装器、当前用户自有Startup链接注册/状态/移除。**免扫码未修复验收，未部署，真实及完整验收未通过。**

0真实bot启停/认证/登录/6099连接、0真实凭据读写、0真实Startup操作、0Windows重启、0SSH/真实模型/QQ消息。测试仅临时根、假进程、动态端口假WebUI/OneBot及合成秘密；DPAPI仅加解密自造token。账号/模型/额度/授权群/黑名单/私聊/人设/群协议/runner/vendor及本机配置未改。data_scope仍unverified，旧密码回退门槛保留。

## 实现证据

- process_host重建固定枚举/白名单码，去ANSI，不存原文、URL、账号、票据；16KiB输入缓冲，溢出整逻辑行丢弃至换行，尾部不能拼成事件；每host最多32条并按事件去重，每条小于256字节。成功hint不是在线证明，伪造行不能触发登录/密码/重启。
- 观察器独立四路由，只复用旧客户端的有界socket读取底层。固定127.0.0.1:6099，无代理/重定向；3秒/64KiB，120秒/16请求（认证1/状态12/缓存2/信息1），状态间隔至少5秒。输出仅固定状态、白名单码、账号匹配布尔、缓存present/missing/unknown。管理2FA直接交人工；缓存missing不是原生历史缺失证据。
- 认证/请求前后验证监听PID、创建时间及冻结受管后代集合；PID复用、Worker换代、停止标记变化、实例变更取消，不追随新Worker继续认证。只有本实例gate在线才能就绪。
- 管理token单独schema1/16KiB密文文件，拒未知键。无回显TTY、停机/同配置锁、配置及文件摘要冲突检查、临时密文fsync后复核原子替换；status不解密/认证。空输入/EOF/中断取消，不导入旧密码、不向组件环境传密。
- 新实例在锁内固定instance/账号/受管身份，锁外观察/等待；状态原子写只有短临界区。公开login-check-only仅channel，保留旧内部full+paused测试兼容。停止后迟到ready写被拦，旧实例不覆盖新状态。
- login-check-only在首个子进程前写既有暂停标记，provider关闭，规格不含model。实际gate的合成free入站在reserve/上游前阻断，观察器仍可报告qq_session_ready。正常qq_ready还须stopping=false；组件phase另列。status实时通道优先，保存的原因/包装器结果明确显示历史。
- 包装器默认30秒延迟/120秒活跃本机接口等待/一次start-text/120秒QQ等待，诊断共享QQ等待预算。独立wrapper排他锁覆盖长等待，配置/停止可进入；生命周期锁及快照仍走manage。partial/端口冲突/清理未决不清账本、不kill、不重试、不换后端。无pause/TTY/浏览器/后台循环。
- 当前用户唯一QQbot-managed-startup.lnk，固定目标/参数/工作目录、归属台账和字节摘要匹配才幂等或移除；同名外部项/变更项/符号链接拒绝操作。固定PowerShell文件和结构化参数、隐藏执行，不改全局执行策略/注册表/服务。测试用临时Startup和替身链接API；真实COM/Windows登录触发未验。
- 原生路径只留本机scope、最多4个路径摘要与前次路径比较；摘要不从包装器JSON或status展示，不解除data_scope。

## 离线验证

新增观察器27项、Startup/暂停gate12项均在最终组合中通过；此前独立26项和12项也分别通过。最终受影响组合回归171项通过，耗时见任务交接。范围：新增两组、process_host、生命周期、旧登录HTTP/单次账本、LAP-24、配置/分层快照/旁注/菜单及OneBot gate。没有修改聊天/runner，未重跑全部群聊框架，未运行覆写旧报告的verify入口。

首次166项中旧PersonaMatrix读取用户未提交长人设导致预算断言失败；未修改人设。另一失败为新检查过度限制旧内部full+paused，已修正为仅CLI限制。随后167项通过；补慢响应/迟到写等测试后最终171项通过。旧248/324仅历史数字。

项目根PowerShell可重现命令；仅在测试进程内把PersonaMatrix的单一路径读取替换为已提交基线，不修改/读取用户人设正文：

```powershell
@'
import unittest,sys,subprocess
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=['tests','src','.']
baseline=subprocess.check_output(['git','show','HEAD:config/persona.md']).decode('utf-8')
original=Path.read_text;persona=Path('config/persona.md').resolve()
def read(path,*args,**kwargs):
 if path.resolve()==persona:return baseline
 return original(path,*args,**kwargs)
patterns=['test_napcat_login_observer.py','test_autostart.py','test_process_host.py','test_lifecycle.py','test_napcat_login_http.py','test_lap24.py','test_config.py','test_config_files.py','test_config_comments.py','test_configure_menu.py','test_onebot_gate.py']
suite=unittest.TestSuite(unittest.defaultTestLoader.discover('tests',pattern=p) for p in patterns)
with patch.object(Path,'read_text',read):result=unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(not result.wasSuccessful())
'@ | .venv/Scripts/python.exe -X utf8 -
```

额外检查：PowerShell Parser.ParseFile仅解析辅助脚本，未执行COM；锁定bundle SHA256仍为f80e4be3e8640369d23846cf3e8bcfd2a5b6dc5920f50d7ad733d7cca18179e6。源码复核四路由/状态字段/快登与验证日志。提交前检查本任务Markdown链接、差异空白及文件归属。

## 能力缺口及下一步

1. stdout是否穿过host未真实验证，Worker/named pipe可能绕开；没有日志只能telemetry_unavailable。格式/版本变化须复核，不能自动升级或改vendor。
2. psutil.open_files仅尽力取得已核身份后代的路径元数据，Windows可能漏共享句柄/拒访问。无匹配nt_qq或超过4根即unknown，不扫描全盘。只留scope/路径摘要，不读账号库、Registry20或票据，不写外部根。没有完整句柄枚举、设备有效性/连续性或可强制原生路径绑定的可信报告，须回规划；路径相等不证明GUID/票据/设备信任相同。
3. 外部原生根为历史观察，本轮未重新探测，保持unverified。若仍每次needNewDevice，保留资料回规划，不切Docker/Windows用户/QQ框架。
4. 真实WebUI兼容、免人工正常重启两次、Windows重启恢复、真实Startup安装/触发及3个实际使用日均未验。仍无本账号真实快登失败码/资格证据。
5. Startup仅Windows用户登录后触发，E盘须先可用；不处理未登录开机/解锁磁盘。COM依赖本机PowerShell策略，失败固定阻断、不修改策略。安装中断留下无台账链接时拒认领/删除，转人工核对。

回滚先remove自有链接/停用包装器，再按创建身份停止本项目并回旧代码；保留原生资料、设备、历史和pending/unknown/清理/密码尝试账本。真实D/R批次等待用户后续指令及唯一实例负责人；P1/P3不代替P2/P4/P5。

## 文件与Git

归属：scripts/{manage,configure_bot,process_host,autostart}.py、scripts/startup_shortcut.ps1、开机启动机器人.cmd、src/qqbot_gateway/napcat_login_observer.py、tests/test_napcat_login_observer.py、tests/test_autostart.py、README.md、config/README.md、本报告、24 HANDOFF及PROGRESS/工作线HANDOFF/TASKS的LAP-24差异。

并行LAP-36规划段落/文档归其session，仅按差异块暂存本任务共享索引；保留用户config/persona.md。提交/推送/完整SHA核对见[任务交接](../tracks/laptop-workbuddy/tasks/LAP-24/HANDOFF.md)。Git交付不等于部署或真实验收。
