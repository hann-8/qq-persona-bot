# LAP-44 群长期记忆实施与部署

当前检查点：实现及33项定向组合通过，生产备份已保存，尚未执行stop/迁移/启动。生产起点main/远端b0b4573，隔离分支codex/lap-44-full-memory保留全部main修复及465e76a详细规划。

实现：schema2字典与稳定HMAC成员标记，全文快照/manifest/fit/metadata，增改删原子事务/CAS/同请求去重，先保存再组装回执/投递台账；native有无工具/prepared计划贯通，不修改persona。初始容量/文件/总配额50000字符/1048576/8388608字节，所选CLI政策524288字节；旧语义和小限额停用，配置可继续扩大但受实际C/F/V/O限制。

检查命令：`.venv/Scripts/python.exe -B -m unittest test_lap44_memory test_lap43 test_cli_native_web -q`，33通过。包括首次保存/清RAM重载、跨群隔离/稳定身份、50000与100000字符、全文/HTTP/manifest、786432合法原生政策及真实容量反例、合并/删除/CAS/写失败、schema1无损迁移/损坏拒绝、实际AstrBot hook最终回执hash与合成ACK/重入、owner暂停重置/发送栅栏，以及锁定SDK/CLI两工具替身往返。无主动真实模型/联网服务/QQ群消息。

生产备份：忽略的state/lap44-deployment/20261029-1136（23项配置/人设/图库/key/记忆/active/技术资料）。停机前只读记忆3文件均schema1且0条；running/connected/can_receive/router_ready、pending_restart=false。下一步严格正常stop后快进main、两份local精确改值、迁移、当前完整check/probe/activate和正常start/status。最终结果将追加本报告及44 HANDOFF。

回滚必须正常stop，先保存后续schema2新内容，配对恢复本轮代码基线/两份local/active/技术报告与probe。只有没有后续记忆变化时才可恢复schema1原件；不能用旧空库覆盖新内容。真实模型遵循与QQ效果由用户群测。
