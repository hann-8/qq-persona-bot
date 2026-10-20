# LAP-35 群内临时停言与真实@恢复

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承[AGENTS](../../../../AGENTS.md)。

## 当前状态

2026-10-20 19:18（Asia/Shanghai）领取，19:26详细规划完成；session `LAP-35-group-silence-plan`，标题“群临时停言/真实@恢复规划”。用户明确本会话承担Max详细规划，后续交给medium实施；不声称自动检测/切换模型。本轮只规划第二项，已完成的[LAP-34配置规划](../LAP-34/HANDOFF.md)保留。

需求：各群初始为普通；非黑名单群友明确要求肥鱼不要参与讨论后，本群停止全部输出，直到下一次非黑名单群友真实@恢复普通；bot进程/电脑重启回普通。识别/并发/重连重启/旧结果失效与在途消息边界已在[PLAN](PLAN.md)固定；仅已规划，未实现/未离线功能验收/未真实验收。

起点`main/29f75ff`，只有用户`config/persona.md`未提交差异；保留，不读正文、不修改、不提交。没有其他任务实施改动。本轮独占6份文档：本HANDOFF/PLAN/IMPLEMENTATION_GUIDE、PROGRESS、工作线HANDOFF/TASKS。不改34文档、代码/模板/本机配置，不启停/登录/SSH/模型/QQ操作，不读取私密群消息或凭据。

## 已完成与证据

- 重读AGENTS、PROGRESS、活动线HANDOFF/TASKS与34交接。
- 只读核对gate入站/去重/出站、Participation/Attention失效、router三个处理分支、EventSendGuard/逐条ACK代理、登录/生命周期及session_version。
- 发现mentions模式当前在gate提前丢弃非@，必须为停言控制增加仅入口本地识别；仅router加bool无法立即拦截所有输出，且唤醒后会放出旧任务结果。
- 确认连接断开会使窗口/票据失效，不能将其等同bot重启或自动解除哑巴；旧单条mentions发送也需纳入代际/ACK保护。
- 明确本地受控句式/否定作用域、停言优先于同条@、全输出门票与gate最终群锁、boot/代际失效、RAM主状态/不恢复诊断镜像，以及仅取消router尚未提交provider HTTP的工作。
- 固定participation.silence.enabled默认true、34的chat.yaml归属、persona/session_version排除、回滚/功能兼容导出、5实施步骤与12验收项；[medium复制指令](IMPLEMENTATION_GUIDE.md)完成，推荐34→35分别实施。

## 下一步

规划已完成，Git交付待本次检查点确认。后续由用户另开medium会话，先按34指引实施分层配置，再另会话按35指引实施临时停言；若用户改顺序，35兼容单文件且交接给34保留新节。规划不是部署/真实迁移/启停/模型或群测试授权。

## 验证

19:25初检：6份归属文档267个本地链接、围栏配对、S35-01—05/SM-01—12集合与隐私模式检查通过；同步最终索引后276个链接、合同标记/编号/围栏/根入口与隐私模式检查全部通过，git diff --check通过。只检查文档，不运行功能测试。当前bot状态未知；保留34及LAP-18/24/28/29/31B和全部旧真人差额。
