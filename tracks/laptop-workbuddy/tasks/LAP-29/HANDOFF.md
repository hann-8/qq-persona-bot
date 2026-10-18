# LAP-29：小群成员与受控@实施交接

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md)。继承根AGENTS。

状态：已实现/离线通过；生产人数新鲜度未证、不可启用。355单元/52组合790实际框架（成员32组合288例），末次32专项补验通过。[报告](../../../../reports/lap-29-2026-10-18.md) / [汇总](../../../../reports/lap-29-offline.json)。session `LAP-29-members-typed-mention`，2026-10-18 23:20（Asia/Shanghai）领取，2026-10-18 23:50收口；根session独占，起始main/7061149、工作区干净。

合同：[PLAN6](../LAP-26/PLAN.md)、[SPEC2/5/6/9/10](../LAP-26/IMPLEMENTATION_SPEC.md)、[GUIDE](../LAP-26/IMPLEMENTATION_GUIDE.md)。依赖27/28代码，不要求vision生产启用。

目标：gate固定成员服务/独立token/一次cap、1..49及双TTL、RAM全量与最多8/768字节候选、RPC防旁路、v3受控mention与一次send许可、文字同链ACK/同次剥@。

能力出口：NapCat缓存人数无观测时间/最大陈旧度证明；生产capability_unverified，菜单拒开、手改desired仅暂停成员功能。不得增加来源或接受received_at冒充观测。

文件归属：members.py、onebot_gate/config/turn_v2/reply_plan/media_protocol/event_guard/reply_delivery/task_store、model_gateway/router/persona、configure_astrbot/configure_bot、settings.example/README、test_lap29/verify_lap29、reports/lap-29-*与本交接及三份进度索引。

验证：仅自造夹具/假OneBot；MEMB-01—04、候选/ref/ACK/错误及旧文字/表情回归。0真实人数/名单/@、bot/登录/模型/群发；不改忽略配置/凭据，不开始30。

当前实现：固定bind/resolve/permit、独立认证/一次cap、缓存门槛/候选、v3 plan/guard/proxy/单次ACK与mention_receipt表；生产启动仅暂停members，菜单/save拒激活，双摘要旧配置导出移除members。ambient合并同时替换成员cap，gateway按原source_digest兑换，再对effective候选裁剪。

验证命令与结果：`.venv/Scripts/python.exe -X utf8 scripts/verify_lap29.py`成功（355单元/52组合790框架）；`.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_lap29.py`末次32项通过；compileall与diff检查通过。实际AstrBot/provider/run_agent、CLI/local两runner底层替身，经假gate原event的OneBot/ACK；成员32组合288例、篡改metadata 8例零发送/零额外通知，另旧v1/关注/文字表情/视觉回归。只写reports/lap-29-*，旧报告不改，细目见报告。

最后修正：AST人设构造兼容；夹具图库登记/冷却/锚点/HTTP trace；联网来源追加保留未截断正文的mention依赖；坏aux容器仅丢aux；旧窗口优先裁剪；count变化名单长度不一致重新list、list中成员事件失效拒用、随机名册revision拒旧映射；最长明确名称/ASCII边界采用有界匹配。末次32项补验覆盖这些成员边界和实际菜单拒开/手改启动暂停。

剩余：人数观测时间/最大陈旧度证明未有可信来源，生产固定capability_unverified，不能用received_at、重复请求或手写配置解锁。真实人数/名单/ACK/@/群效果未验；未来来源需补规划，随后另行授权真实验证。28视觉/31B/18/24与全部旧真人差额保留，不自动开始30。

回滚：先停受管实例并保留pending/unknown/清理账本；7→19导出移除members/vision/attention的旧schema3审阅副本，双摘要/停机锁核对后才显式激活，不自动启停。新mention_receipt表只记录结果，不删除旧ACK/历史。旧代码不能尊重未知清理时保持停机。

Git交付：待本轮归属/文档检查后提交推送，核对origin/main完整SHA；末期检测并行LAP-32-cleanup-ledger-debug：其HANDOFF明确归属cleanup_identity.py/process_host.py/test_lap32.py与根目录说明，共享三台账仅追加32登记。本任务保留其全部差异；共享台账只暂存29归属段，32前缀/文件不夹带。忽略本机配置/凭据/自造测试临时文件继续保留、不纳入提交。最终审阅又收紧发送者/群准入/连接失效整票拒发（目标@名单/人数失效仍同次剥@），独立verify_lap29最终复跑已成功（355单元/52组合790框架），32专项也通过。250链接/围栏/diff检查通过。下一步完成Git交付；之后人数能力缺口回规划，30等待用户新指令。
