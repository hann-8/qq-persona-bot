# LAP-49：自然表达与大肥鱼角色提示优化

返回 [PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)，继承 [AGENTS](../../../../AGENTS.md)。

状态：planned / awaiting_user_review，2026-11-07（Asia/Shanghai），20:03领取。当前会话 `LAP-49-persona-naturalness-plan` 为唯一文档写入者，无代理/切模型；只读核对和文档，不实施。Git核对后释放本轮文档写入归属；实现/启停归属未领取。

用户反馈：Planner→Replyer分工认可；此前精简persona时特别像真人，但缺失颜文字武器库和熟悉的大肥鱼特征，后来恢复完整人设，当前又显得不自然。本任务规划以短稿为底保留自然表达、补回角色素材。这个自然感比较是用户体验反馈，不是受控实验的因果结论。

基线：main/0fed7c9，开始tracked干净。用户未跟踪的`.workbuddy/memory/2026-11-06.md`、`reports/vision-probe-gate-fix-plan-2026-11-06.md`和启动bat保留、不纳入本任务。当前运行健康未复核，不能把11月4日部署状态写成今天的运行验证。

本轮归属仅六文档：PROGRESS.md、tracks/laptop-workbuddy/{HANDOFF,TASKS}.md、tasks/LAP-49/{HANDOFF,REVIEW,PERSONA_DRAFT}.md。运行`config/persona.md`、源码、local、记忆、图库、会话与进程不动，不调用真实模型/工具服务或发送QQ/微信消息。

## 方案与当前证据

交付 [评审稿](REVIEW.md) 与 [完整候选人设](PERSONA_DRAFT.md)，评审稿同时承担本项设计合同。唯一拟实施的业务文件为`config/persona.md`；无新配置/风格选择器/模型调用，Planner→Replyer与既有能力/预算不改。候选以LAP-47自然接话原则为底，补角色形象、性格、用词和完整颜文字库；去掉开发者说明、固定反应/密度/长示例。没有另建运行角色入口。

决定性只读证据：

- `git show 78da4ea:config/persona.md`为514字符短稿；4810912恢复历史完整版。对应[LAP-47结果](../LAP-47/RESULT.md)与[LAP-48交接](../LAP-48/HANDOFF.md)记录部署，但此前自然感差异仅是本次用户反馈，不是本轮模型实测。
- 当前[persona](../../../../config/persona.md)第13～17行是开发者使用说明；第95行规定每条1～3个颜文字；第196～281行情绪状态机包括固定任务开场、夸奖顺序与第243行固定三段式。
- [persona.py](../../../../src/qqbot_gateway/persona.py)第53～57行将角色全文拼给Planner；[dialogue.py](../../../../src/qqbot_gateway/dialogue.py)第45～51行将角色全文拼给Replyer。两处均不解析/过滤开发者说明，故替换文件正文即可，不需改阶段提示构建。
- [model_gateway.py](../../../../src/qqbot_gateway/model_gateway.py)第545/557行、[router](../../../../plugins/qq_router/main.py)第67～68行启动读取原文件并计算会话版本；[persona.py](../../../../src/qqbot_gateway/persona.py)第119行版本含prompt；[wechat.py](../../../../plugins/qq_router/wechat.py)第145/159行复用本根router和persona。角色变化同时影响本根QQ/微信，独立WeChatbot根不在范围。
- [vision.py](../../../../src/qqbot_gateway/vision.py)第87～105行签名包含`config/persona.md`。未来实施必须重做当前技术配对，不能静默关闭识图；复用`scripts/revalidate_lap43_native_web.py`、`scripts/probe_lap42_vision_contract.py`与既有activate流程，不重跑历史IQ/质量大矩阵。发现旧配对/部署问题按实际证据处理，不因本规划预先扩建脚本。

配置默认值/迁移/回滚/分支合同见评审；无新默认值、不改local，正常启动加载，短期上下文按原机制刷新，长期记忆/图库不动。真实自然感、角色强度、颜文字密度与延迟尚未验证。

## 规划验证与Git交付

已核对当前运行稿17,575 UTF-8字节，候选3,901字节；原库15情绪组/64条素材与候选逐项同序一致，缺失0。这个计数只是文档完整性，不证明模型采用率或自然感。六文档严格UTF-8解码、41个本地链接与`git diff --check`通过，业务源码/config/scripts/tests无diff；本轮没有运行功能测试或启动真实CLI。本轮内容检查点仅这六文档，main起点与实时origin/main均为0fed7c9316c6eaec7529b11cd257bdae4e3d29fa；commit/push后核对完整SHA，最终提交号与远端一致结果以会话回执和Git为准。原三项用户未跟踪文件保留。

下一步：用户review角色味道与取舍，按反馈修改评审和候选；确认无问题再给medium实施指令，由用户手动提交，不自动实施或派发。当前无MEDIUM_START，不能把候选落盘当作部署授权。
