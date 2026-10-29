# LAP-44 群长期记忆实施与部署

2026-10-29 LAP-44已实现、启用并部署main：schema2群记忆全文/模型增改删/实际保存回执已加载，33项定向组合及真实锁定CLI零生成正反配对通过。当前running/connected/can_receive/router_ready，current_error=null、pending_restart=false；memory读写true，3文件0条0字符。初始50000 Unicode字符/1048576文件字节/8388608总字节，所选CLI524288字节政策。容量预算可扩大，100000字符/786432政策合成检查通过，真实C/F/V/O边界仍保留。最新main/df46056联网修复完整合入；其他模型/账号/low、thinking=false、free/owner、识图/表情和工具限额保持。QQ群效果由用户实测，未由离线或加载晋升真实验收。

实现：schema2字典与稳定HMAC成员标记，全文快照/manifest/fit/metadata，增改删原子事务/CAS/同请求去重，先保存再组装回执/投递台账；native有无工具/prepared计划贯通，不修改persona。初始容量/文件/总配额50000字符/1048576/8388608字节，所选CLI政策524288字节；旧语义和小限额停用，配置可继续扩大但受实际C/F/V/O限制。

检查命令：`.venv/Scripts/python.exe -B -m unittest test_lap44_memory test_lap43 test_cli_native_web -q`，33通过。包括首次保存/清RAM重载、跨群隔离/稳定身份、50000与100000字符、全文/HTTP/manifest、786432合法原生政策及真实容量反例、合并/删除/CAS/写失败、schema1无损迁移/损坏拒绝、实际AstrBot hook最终回执hash与合成ACK/重入、owner暂停重置/发送栅栏，以及锁定SDK/CLI两工具替身往返。无主动真实模型/联网服务/QQ群消息。

生产备份：忽略的state/lap44-deployment/20261029-1136（23项配置/人设/图库/key/记忆/active/技术资料）。停机前只读记忆3文件均schema1且0条；running/connected/can_receive/router_ready、pending_restart=false。已正常stop后快进main、两份local精确改值、迁移、当前完整check/probe/activate和正常start/status；实际运行证据在该目录最终status.after/deployment-result。

回滚必须正常stop，先保存后续schema2新内容，配对恢复本轮代码基线/两份local/active/技术报告与probe。只有没有后续记忆变化时才可恢复schema1原件；不能用旧空库覆盖新内容。真实模型遵循与QQ效果由用户群测。


最终部署：期间新增main/df46056已合并到0d82882后再快进生产，未覆盖最新URL/session工具回执修复。最新停机基线及回滚使用state/lap44-deployment/20261029-1140；1136为较早备份。当前完整binding d12f1978907bf7dbb3a750890e0d6da6a0b5886c5285dd6ada98213a2b9b6cb9，active SHA d94f2e4c965e81bdccaf5e7eace3f4c9aeb63acfc30620cf454b82b6a4134526。生产33检查/static通过；真实零生成probe正例0 next、两个反例0 user、生成0，已配对activate。status实际running/connected/can_receive/router_ready，current_error=null、pending_restart=false。schema2三文件606字节，0条/0字符；无真实记忆保存/QQ效果接受事实。保护差异仅两份授权local和三memory文件，persona/key/图库/其他local摘要相同，active及技术报告为本轮必要配对更新。最终文档/Git交付后释放唯一执行归属。
