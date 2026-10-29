# LAP-44：群长期记忆实施交接

返回 [PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [PLAN](PLAN.md) / [实施prompt](MEDIUM_START.md) / [实际报告](../../../../reports/lap-44-memory-result.md)。继承根AGENTS。

## 当前状态

2026-10-29 LAP-44已实现、启用并部署main：schema2群记忆全文/模型增改删/实际保存回执已加载，33项定向组合及真实锁定CLI零生成正反配对通过。当前running/connected/can_receive/router_ready，current_error=null、pending_restart=false；memory读写true，3文件0条0字符。初始50000 Unicode字符/1048576文件字节/8388608总字节，所选CLI524288字节政策。容量预算可扩大，100000字符/786432政策合成检查通过，真实C/F/V/O边界仍保留。最新main/df46056联网修复完整合入；其他模型/账号/low、thinking=false、free/owner、识图/表情和工具限额保持。QQ群效果由用户实测，未由离线或加载晋升真实验收。

唯一session为LAP-44-full-memory-implementation，无代理。用户已提交MEDIUM_START，同轮实现/部署/Git授权已执行；不重新规划、不追加阶段审批。最终main/实施分支push核对后释放实现/启停归属，下一步由用户群测。

## 实现与文件

- group_memory：schema2 records字典、稳定HMAC演员标记、空库有效快照、全文读取、同次增改删事务，格式/版本/字符/磁盘校验，fsync+replace失败保留原件。无语义门槛、候选/TTL/固定/FIFO，旧限额兼容但忽略。schema1含所有旧事实/未确认状态/原成员归属迁移，原件独立留本机。
- turn_v2/persona/backends/gateway/web与router：全文不因成员缺席或fit预算被裁；超限明确失败。normal/native有无工具/prepared路径保留aux。先验证gateway元数据及当前epoch/连接/权限，再保存；回执生成最终合法ReplyPlan、metadata/hash后才建立台账。hook重入不重复写，ACK及个人历史使用最终正文；silent不另发保存回执。
- config与templates/comments：max_chars_per_group默认50000，文件1048576、总8388608；正整数配置不以DEFAULTS封顶。CLI输入预算可扩大；TS native guard移除48000常量，仍校验实际C/F/V/O。runner缓冲按加载budget派生，保留df46056全部URL/session工具接线及安全诊断。
- manage/configure_bot：schema2计数/字符/配额/最近状态、本机导出及CRUD，无固定/确认旧语义。日志仅计数/枚举，不含正文或号码。
- 新增scripts/deploy_lap44_memory.py、tests/test_lap44_memory.py；当前revalidate helper/proof包含新检查，capabilities仅同步当前plugin摘要。其余精确路径以实现提交及Git diff为准。

## 验证与运行事实

生产`.venv/Scripts/python.exe -B -X utf8 scripts/revalidate_lap43_native_web.py check`：33项通过、static_missing=[]、实际预算通过。包括首次写入→清RAM/重载/新Store读回、稳定成员和跨群隔离、50000/100000字符与全文HTTP/manifest、786432原生guard合法扩容和真实容量反例、原子增改删/CAS/重入/协议/写失败保留旧文件、schema1迁移与损坏拒绝、实际AstrBot hook最终台账/hash和合成ACK、typed文字/图/@、native有无工具和prepared路径。当前43权限/发送栅栏及锁定SDK/CLI替身往返保留。

真实锁定CLI零生成probe：real_generations=0，positive_next_calls=0，两个反例user=0；配对activate使用lap43_operator_trial/pending_user_test。未主动真实生成、WebSearch/WebFetch服务或QQ消息；替身ACK不是QQ ACK，不称真实记忆效果通过。

生产代码检查点0d828829d8bb8ed45ffdfe3b79975646ba01f1ef（实现2b7bab7，合并最新df46056），binding=d12f1978907bf7dbb3a750890e0d6da6a0b5886c5285dd6ada98213a2b9b6cb9；active SHA=d94f2e4c965e81bdccaf5e7eace3f4c9aeb63acfc30620cf454b82b6a4134526。最终Git文档回执提交在该点之后，未再改运行源码。

实际status已确认running/connected/can_receive/router_ready、current_error=null、pending_restart=false。加载memory.enabled/learning_enabled=true、50000/1048576/8388608，input_budget=524288，thinking=false，两工具/3调用/4步骤/8000单结果/12000总结果/90秒保留。三份schema2合计0条0字符/606文件字节，无不可用文件；尚无新协议真实保存事件。

## 备份、保护与回滚

state/lap44-deployment/20261029-1140为停机后最新df46056基线，含23项完整本机配置/persona/图库/key/原记忆及active/offline/probe/能力表备份、baseline/migration/check/pairing/status.after/deployment-result。20261029-1136为较早备份，均忽略且不提交。并行main新增df46056导致首次快进拒绝，未覆盖生产；已在隔离分支合并，只解决能力表plugin摘要冲突，重跑33组合/静态及最终probe后部署。

保护差异只有两份授权local与三份memory.json；其余persona/模型账号参数/图库/catalog/key及其他local摘要相同。active/技术报告按当前完整绑定更新，旧IQ/unknown/原始消息证据保持。

回滚先正常stop，保存所有当前schema2内容和日志；配对恢复df46056代码基线、两份local与该备份的active/offline/probe/能力表。仅在迁移后无新记忆变化时恢复schema1原件；有新增内容时先导出/保留schema2，不能旧空库覆盖。正常start/status确认后才称回滚运行恢复，不动日常QQ/旧NapCat根。

## 剩余

用户在QQ群“记住称呼→重置本群上下文→询问”及普通自然学习/更新/遗忘实测；模型是否合理提出更新、5万字符成本/延迟和长期体验未验。扩容实际命令见使用说明/config README；100000字符/2097152文件/33554432总额/786432政策只是合成检查，生产仍用初始值。旧18/21/27/35/42验收差额保留，不作当前使用门槛。

Git交付：只提交本任务归属及当前配对技术报告；main和codex/lap-44-full-memory普通push后核对实时SHA，最终提交号以本轮回执为准，不在提交中自引用。生产与隔离树无非忽略保留差异时报告干净，运行local/备份继续忽略。
