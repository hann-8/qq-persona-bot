# LAP-30 群长期记忆

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)。继承AGENTS；合同为[LAP-26 PLAN7](../LAP-26/PLAN.md)、[SPEC2/4/7/9/10](../LAP-26/IMPLEMENTATION_SPEC.md)及[GUIDE](../LAP-26/IMPLEMENTATION_GUIDE.md)。

状态：**已实现/离线通过，真实/完整验收未做**。2026-10-19（Asia/Shanghai）领取，session `LAP-30-group-memory`，用户说明会话设置gpt-6.1-sol/medium，不检测/切换。起点main工作区干净；本session独占任务及共享台账写入。

目标：稳定HMAC隔离/有限JSON/只读MD、相关注入、固定proposals、宿主晋升/TTL/淘汰、固定base_revision/generation/phase事务及文字ACK、持久purge与失败禁读；默认关闭，本机管理共用锁/校验。依赖27/28/29代码，不要求视觉/成员生产启用，大群仅获准sender仍可记忆。

归属：group_memory及协议/预算/persona/config/model_gateway/router必要接线，configure_bot/configure_astrbot、示例/README、test_lap30/verify_lap30与本任务reports、PROGRESS/工作线HANDOFF/TASKS。实施前重读台账，不覆盖其他任务文件或旧报告。

验收：M01—12、组合预算/协议/实际AstrBot原event ACK与两实际runner底层替身；独立verify_lap30与reports/lap-30-*。仅自造夹具，不改忽略本机配置/凭据/真实记忆，不启停/登录真实bot，不调用真实模型/QQ/群发，不使用私密附件。31B/视觉/人数与旧差额保留。

下一步：交付本任务commit/push并核对远端；不部署，不自动开启记忆，不推进其他任务。后续真实语义/召回质量/QQ ACK需用户另定范围。

稳定命名空间为bot HMAC前缀+群HMAC（各128位），主体key以完整命名空间派生；黑名单能净化同bot撤销授权群的本机库，不碰另一个bot的namespace。来源首次received_at保留，原message hash有界去重；同源/旧时间不续TTL。自述采取保守明确句式+事实字面来源，不能宣称通用语义理解。只读MD不回导；缺key/损坏/主库缺失但副本仍在均禁读，不空库替换。

新增scripts/verify_lap30.py、verify_lap30_framework.py、tests/test_lap30.py；仅为30组合扩展verify_lap28_framework.py/verify_lap29_framework.py的默认false参数，不执行旧报告writer。其他27/28/29任务文档与旧报告未动。先前直接框架探针自动产生根data/四个自造框架模板/配置及空目录，已按精确路径删除；测试日志仅state/lap30-*，真实本机配置/凭据/记忆从未读取或修改。


最终收口：2026-10-19 00:33（Asia/Shanghai），独立verify_lap30退出0：396全套单元、68组合926实际框架；32记忆主矩阵+8成员/记忆+8视觉/记忆+20旧路径组合。31项M专项与最后管理入口修正后的全396单元也通过。报告：[说明](../../../../reports/lap-30-2026-10-19.md)、[汇总](../../../../reports/lap-30-offline.json)、[框架](../../../../reports/lap-30-framework-offline.json)、[源码摘要](../../../../reports/lap-30-source-checks.json)。命令为`.venv/Scripts/python.exe -X utf8 scripts/verify_lap30.py`、`-m unittest discover -s tests -p test_lap30.py`及`-m unittest discover -s tests`；忽略日志state/lap30-*。日志中的启动/关闭文字均为旧生命周期临时夹具，没有真实bot操作。

完成：固定record/proposal/配额与相关检索、候选晋升/单多值槽/来源TTL/稳定淘汰、base_revision/generation/phase固定事务、原event正常文字ACK、重启pending丢弃、持久purge/副本失败禁读、默认关闭配置与菜单/双摘要管理/旧配置导出。大黑名单按<=24个主体批次持久净化，不扩大为全群clear；副本失败后启动先完成旧intent，文字继续。非空黑名单的本机管理复用同一配置摘要下的恢复实例，避免每次操作重做startup purge改变已审阅摘要；动作仍持有停机/配置/JSON锁并核对两摘要。没有方案级能力缺口；保守中文自述/关键词检索的真实语义质量未验，不能保证绝对隐私识别。

修改归属：src/qqbot_gateway/{group_memory,turn_v2,config,persona,model_gateway,backends,web_retrieval}.py；plugins/qq_router/main.py；scripts/{configure_bot,configure_astrbot,verify_lap30,verify_lap30_framework,verify_lap28_framework,verify_lap29_framework}.py（28/29仅30组合默认false扩展）；config/settings.example.yaml；tests/test_lap30.py；README；reports/lap-30-*；本交接、PROGRESS、工作线HANDOFF/TASKS。未覆盖旧报告，未改其他任务HANDOFF/计划。

回滚：停受管实例后保留key/主库/purge/ACK/pending/unknown/清理台账，7→19导出移除memory/members/vision/attention的旧schema3审阅副本，双摘要核对后显式激活，不启停。旧版不能尊重未决清理时保持停机。真实/完整验收、28视觉/29人数/31B与18/24及全部旧差额保留。当前真实bot状态/加载版本未知，本机配置/凭据/人设/真实记忆未读取修改，0真实启停/登录/模型/QQ/群发/私密附件操作。
