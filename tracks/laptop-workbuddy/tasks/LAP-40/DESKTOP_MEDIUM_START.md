# LAP-40 medium：实际补齐双击启动/查看/关闭

返回[项目入口](../../../../PROGRESS.md) / [详细计划](DESKTOP_PLAN.md) / [交接](HANDOFF.md)。2026-10-25，Asia/Shanghai。

用户手工在新会话选择`gpt-6.1-sol/medium`后复制下文；当前会话不派代理、不切换模型。此指令授权代码与离线验证，不授权真实启停/登录或模型/群操作。

```text
接续LAP-40，请实际实现类似NapCat的SnowLuma日常启动入口。上一交付只有协议接入和材料，用户不会自行运行launcher、配置OneBot或复制token；这次必须落地脚本，不能再只交使用命令或环境清单。

工作根：E:/CodexWS/QQbot_Snowluma
分支：codex/lap-40-snowluma
起点以当前Git日志为准，材料提交47342ac之后的DESKTOP_PLAN/本指令为本项规划。重新核对HEAD、远端和工作区；先读PROGRESS顶部、AGENTS、工作线HANDOFF顶部/TASKS的LAP-40行，再读LAP-40/HANDOFF、DESKTOP_PLAN和本文件，只按缺口检索。

登记session、时间和文件归属并重读。只在本根实施；不派子代理、不切模型，不修改E:/CodexWS/QQbot或旧C根。先按DESKTOP_PLAN登记manage.py、新官方启动helper、必要cmd/PS入口、使用说明、专项测试和交接文档，再改代码。

交付用户操作：
1. 双击本根“启动机器人.cmd”，按当前provider处理。NapCat原行为保留；Snow自动准备本项目目标账号反向WS（从现有忽略文件在内存读inbound token，不让用户手填JSON/token），复用或启动项目组件，启动缺少的专用QQ和官方Snow，打开官方本机管理页。
2. 项目三个组件已经running时，也能只补启QQ/Snow，不能直接“已运行”就结束，不先停机重建。重复双击不创建重复组件/连接。用包内node.exe和原版index.mjs、包根cwd，不改PATH或Snow内部；后台隐藏窗口，专用QQ保留交互窗口。
3. 新增“打开SnowLuma管理页.cmd”“查看Snow本机日志.cmd”和简短“SnowLuma使用说明.md”。首次只留用户在官方页面阅读/确认条款、登录管理页、选择专用QQ和扫码；密码在本机官方日志中看，不在统一状态/agent输出显示。不自动接受协议，不启全局自动注入或密码登录。
4. “查看状态.cmd”清楚区分组件运行、Snow管理页、QQ/OneBot未接通/就绪；修掉Snow路径上的NapCat登录和私有运行前置错误提示。健康检查0模型。
5. “关闭机器人.cmd”先停止本根模型/入口，再处理脚本有创建身份依据的官方Snow/专用QQ及其已识别子进程；手工已运行的外部实例保留并给正常退出提示。禁止按QQ/Node/Python名字批量结束。部分失败只回收本次新增且身份已登记的进程，不碰原先running组件。

实现接口、配置精确合同、候选文件、幂等与归属/失败分支、必要验证和回滚均按DESKTOP_PLAN执行；建议manage新增start-desktop作为日常入口，原start-text/start-channel保留高级含义。复用已有PID/创建时间登记与锁，不建私有控制/health/proof/supervisor。只同步目标账号名为qqbot-gate的一条连接，先备份再原子写，不删无关设置，不覆盖现有token。配置一致零写；真实Snow已外部运行时按计划给出具体正常同步分支。

保持local/persona、模型/推理/预算、账号/额度、触发模式及现有业务开关原样；不得擅自修人设预算或切mentions/free。本根QQ/local现在已存在，旧MATERIALS缺项是历史，不能重复安装或覆盖环境。官方原版OneBot仍接既有gate/AstrBot/router/gateway/CodeBuddy，账号屏蔽由用户QQ拉黑。A4不复核/重跑/修改，B/C停止；不加资格/probe/零日志/存储或长稳前置。

本次实际实施仅代码、用户说明和临时根的必要离线验证：用模拟进程/浏览器/假账号token检查正确路径、已有实例只补缺项、重复点击、配置保留/保密、外部实例不杀、PID变化、局部失败回收、中文状态和NapCat兼容；不跑A4或全量回归。不启停当前真实实例，不执行新启动脚本，不打开真实登录页，不写实际Snow/local配置，不登录/扫码/调用模型/发群/SSH。

交付时明确“脚本已实现/离线通过，真实双击登录收发未验”，给用户从双击到首次选进程扫码的简短步骤和准确停止行为。同步PROGRESS、工作线HANDOFF/TASKS、LAP-40交接/TRYOUT；按长期Git授权只提交本任务已检查文件，commit/push并核对远端SHA，报告保留差异，原本机文件原样保留。交付后停止，真实首次启动及群试用由用户新授权或亲自点击，不自动部署/推进其他功能。
```
