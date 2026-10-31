# WX-AKASHA-ALL：QQ/AstrBot 侧

返回 [本项交接](../tracks/laptop-workbuddy/tasks/WX-AKASHA-ALL/HANDOFF.md) / [微信总报告](E:/CodexWS/WeChatbot/docs/WX-AKASHA-ALL-REPORT.md)。

2026-10-31，本会话 Codex，唯一任务 WX-AKASHA-ALL。开工 main=42911af 且干净；隔离 codex/wx-akasha-all 实现后普通快进 main。未操作旧 NapCat 根。

独立 akasha-wechat/11229 已增量加入当前 AstrBot。自有插件各钩子按平台及真实绑定分派，微信调用现有 Attention/ReplyPlan/MemoryStore/provider/gateway；QQ 原 Snow 票据/名单/owner 栅栏保留。微信配对只引用既有记忆服务的 namespace/actor，不复制库或 key。新增一次性当前图和公开成员来源；原生@关闭。当前模型、low、thinking=false、524288字节政策及工具限额保持。

当前检查：原生/QQ/schema2定向34通过；新微信当前图/共享上下文3通过；微信根实际AstrBot适配/provider＋替身端到端3通过。额外旧test_transport_router的17项有10失败/2错误，原始42911af隔离副本完全复现，保留记录，不称通过。

按当前binding `1c8d1f3724243023ef4f3ba11e39861c4f19df8061308480f9dfe45aef94a8cc` 完成现有check/probe/activate；真实锁定CLI零生成握手 passed，real_generations=0、positive_next_calls=0、negative_users=[0,0]，operator_trial质量待用户实测。没有主动生成/联网服务/群发样本。

受管重启已完成，6199与11229监听，gateway/router_ready=true，current_error=null，QQ connected/online/channel_ready=true。原QQ平台、provider/provider_sources/provider_settings/agent_runner/admins_id逐字段与备份相同；所有config/local与persona摘要未变，原memory和vision仍启用。修复日常实际启动路径会重建单QQ平台的问题：沿共享配置接点保留其他平台，存在Akasha时不重跑旧全量AstrBot生成器。

备份和保护摘要仅在忽略的state/akasha-deployment。操作者已完成微信账号/密钥及facts_only＋1 actor_link，原选定群实际WeFlow/SSE/11229 WS均正常；当前微信配置摘要已加载，共享MemoryStore检查200，QQ仍connected/online/ready。没有主动真实生成/群发样本，交用户自然实测，具体故障继续本任务。

Git推送结果在交接/最终回执更新，Git交付与运行状态分别记录。
