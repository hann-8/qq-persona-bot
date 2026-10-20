# LAP-35 群临时停言、真实@恢复与重启复位

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承[AGENTS](../../../../AGENTS.md)，合同见[PLAN](PLAN.md)/[IMPLEMENTATION_GUIDE](IMPLEMENTATION_GUIDE.md)。

## 当前检查点

2026-10-20 20:35（Asia/Shanghai）领取实施，session `LAP-35-group-silence-implementation` / “群临时停言实施”。20:58交接：S35-01→05已实现/离线通过；440单元/44组合918实际框架通过，20组合460关闭能力兼容回归通过，见[报告](../../../../reports/lap-35-2026-10-20.md)/[摘要](../../../../reports/lap-35-offline.json)。未修改本机配置、未迁移/启动加载，真实/完整未验。会话设置由用户选择，不声称自动检测或切换模型。

起点只有用户 `config/persona.md` 未提交差异；保留，不改写/格式化/暂存/提交。34已实际实现/离线通过，源码与交接已核对；本轮仅35。先登记session/20:35时间/文件归属并重读，未另建根HANDOFF，无子代理或真实服务操作。

## 已实现与关键检查

- S35-01：有界本地句式/否定作用域/引用排除、每授权群RAM normal/muted、monotonic generation、boot/连接/身份绑定的HMAC封闭票据；默认开关与严格校验。
- S35-02：基础身份/黑名单→去重→控制→普通准入；同条@停言优先，mentions非@仅控制，哑巴不发框架/材料；最终群锁再次验票，send_group_msg/send_msg均覆盖，内部参数剥离。只读散列镜像不作恢复源。材料/成员RPC捕获代际，旧cap/权限逐群撤销，不影响其他群。
- S35-03：三router分支/提示/媒体统一原event门票；镜像监测两模式启用，代际变化清本群窗口/焦点/本地候选；本地队列和provider提交前再检。已提交HTTP包括网关内部排队继续自然收束，不cancel SSH，不清旧unknown/cleanup。纯single用独立needs_guarded_delivery建账与历史修复，不冒充media协议。
- 最终发送提交后不因代际变化取消ACK等待；明确gate拒绝为failed未发送，真正缺ACK仍unknown，不重试。剩余prepared部件结束记failed；已成功ACK保留sent/partial和对应助手历史。
- S35-04：chat模板/索引与状态群数、persona/session_version排除、完整布局导出与功能兼容导出分开，旧严格字段不放宽；角色正文未修改。
- S35-05：新增 `test_group_silence.py`、独立 `verify_lap35.py` 与 `verify_lap35_framework.py`。旧fixtures显式silence=false验证关闭兼容，不把旧测试当新能力证据；新矩阵使用真实gate入站/出站与AstrBot事件、事件hook dispatcher/build_main_agent/run_agent、原event/逐条ACK，真实两runner仅替换CLI脚本/原生HTTP底层。

## 文件归属

实际修改：`src/qqbot_gateway/{group_silence,participation,config,config_comments,onebot_gate,event_guard,reply_delivery,session_queue,task_store,persona}.py`；`plugins/qq_router/{main,provider}.py`；`scripts/{manage,configure_bot,verify_lap35,verify_lap35_framework}.py`；chat/旧单文件模板、配置索引、根README/目录日志说明；新测试与受影响gate/participation/27/28/29/memes旧测试；旧16/17/18/20/21/27/28/29/30框架fixtures显式关闭能力的兼容适配；报告、PROGRESS/工作线HANDOFF/TASKS/本交接。未改PLAN/指引历史规划正文。

不归属：用户persona、本机local/settings、secrets、真实图库/记忆/运行态。仅临时目录/自造数据和忽略测试日志，0真实bot启停/探活/登录、0SSH连接/真实模型/QQ消息。

## 剩余与下一步

代码/模板/文档及SM-01—12离线交付完成；`.venv/Scripts/python.exe -X utf8 scripts/verify_lap35.py`通过，兼容矩阵独立调用34的frameworks-only（不运行旧main现场路径）通过。旧固定长度人设测试用已提交HEAD夹具，工作区角色未作为验收/未改写。差异/隐私/链接检查与Git交付见末节。真实加载和两群友停言/另一人@恢复/重启复位/重连保持/另群隔离须后续明确授权；不因离线或push标已启用。LAP-18搜索/24登录/28视觉/29人数新鲜度/31B完整清理及旧真人差额保留。自然话覆盖只限本地有界句式；已提交QQ消息不能撤回，实际可见晚到/真实ACK时序待验。

历史规划：2026-10-20 19:18领取/19:26完成 `LAP-35-group-silence-plan`；规划内容 `0126780ca200d59ed296d63e9f11c69497d8f939` 已推送，未实施或启用；现实施由用户新指令授权。

## Git与保留差异

提交前复核仅本任务归属，测试夹具与报告均自造数据/临时目录；用户config/persona.md未暂存。本轮已检查440单元、44/918新能力与20/460兼容证据，Git diff --check/本地文档链接/围栏/忽略与提交清单检查。内容提交与远端完整SHA在推送后补记；本地唯一需保留差异为用户persona。Git交付不等于真实加载/验收。
