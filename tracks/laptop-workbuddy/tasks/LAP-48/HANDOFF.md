# LAP-48 最终交接：QQ整块记忆、联网薄适配与指定人设

返回 [PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)，继承 [AGENTS](../../../../AGENTS.md)。

状态：planned / ready_for_medium，2026-11-04 20:25（Asia/Shanghai）。用户已明确修改并要求完成直接给medium指令，由其手动落地，不再追加review。入口：[最终评审](REVIEW.md) / [最终设计](PLAN.md) / [实施指令](MEDIUM_START.md) / [指定人设备稿](PERSONA_RESTORE.md)。规划方不自动实施、派代理或切模型。

最终选择：
- QQ号是QQ群友唯一键，name展示，memory无编号数组；按变化成员/group/unassigned整块替换，省略不改、空数组清空。用户明确不要rN/mN或逐条定位，不用下标/hash换皮恢复。
- 同块完全相同文字可轻量去重，语义相近由原Planner看全文合并；无额外调用/向量库/准确率门槛。
- 官方tool.call薄适配，删除第二计划、逐步完整历史/prefix/阶段齐全及固定10步门槛。8次真实执行和现容量作为可调预算，正常网站/预算错误给模型收尾，不毒化全任务；180秒两阶段共享、表达30/清理5、provider派生235秒。
- 成功/无变化不改正文、不播报保存；明确记忆请求失败才反馈。实际结果内部保留。
- 人设精确选ff2e348，删第十三节及开头指向它的说明，顺排说明序号；第1～12节其余角色文字保留。两阶段仍读同一人设，清理通用风格冲突，首稿439字候选废止。

证据：天气样例CLI trace 7c84eda6a5为tool_plan_missing→native_ready，本地拒绝非总超时；后续天气属另一任务，具体原始SDK顺序未留摘要。当前旧HMAC关联只读核对一群5/5、另一群2/3，有一位待关联；保留unassigned及内部legacy_links，不猜QQ不阻塞部署。QQ号/key/原文未输出或提交。运行中的自然记忆写入及用户后续名单变化不由本轮覆盖。

人设备稿：源ff2e348d236613ab74990edd3386dafb06b149ed，备稿8,896字符/17,575 UTF-8字节，SHA256 82a9378d450388a8c08cb30481ee42c8666c3a4b8758293a014d243a75ced430；当前运行短稿仍1,502字节。备稿增加后续输入成本，不能声称去掉编号的节省抵消它。PERSONA_RESTORE只是交接文档，不是第二个运行配置。

归属：当前会话唯一文档写入者，无代理。首稿交付e81c15e；本次修订起点main/e81c15e与实时origin/main一致，仅原用户未跟踪启动bat保留。此次只拥有八文档：PROGRESS、工作线HANDOFF/TASKS、本目录HANDOFF/REVIEW/PLAN/MEDIUM_START/PERSONA_RESTORE。没有改源码、local、运行persona或实际记忆，没有启停、真实模型/搜索或QQ/微信测试消息。独立WeChatbot不操作；本根已有WX-Akasha映射纳入实施兼容范围。

验证：八文档295个本地链接、两处JSON示例及QQ整块结构通过；备稿与指定版本仅删第十三节/失效说明并顺排说明编号的转换逐字节相符；入口/medium链接和Git范围通过，git diff --check无空白错误。只改八份Markdown，不跑实现测试，不把只读状态当真实质量验收。

Git：仅提交八份归属Markdown，说明“docs: finalize LAP-48 QQ memory and medium handoff”；最终SHA以本轮回执/git log为准，commit/push并核对main实时远端一致后释放文档归属，未跟踪用户bat不提交。

下一步：用户手动把MEDIUM_START交给medium。实施同轮完成实现/必要回归/迁移/当前零生成技术配对/启用受管部署/Git，质量由用户群测；不重开规划、不补历史大矩阵、不增加审批或真实样本。
