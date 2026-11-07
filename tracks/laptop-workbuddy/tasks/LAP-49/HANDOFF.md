# LAP-49：自然表达与大肥鱼角色提示优化

返回 [PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md)，继承 [AGENTS](../../../../AGENTS.md)。

状态：implemented / stopped_for_user_start，2026-11-07（Asia/Shanghai）。用户确认候选、指定当前会话实施并明确完事不要启动bot。本会话LAP-49-persona-implementation已完成替换/必要配对/受管停止；36项定向检查和当前零生成配对通过，最终AstrBot/model/gate均0。详见[RESULT](RESULT.md)。无代理/切模型，Git核对后释放本轮唯一执行归属。

用户反馈：Planner→Replyer分工认可；此前精简persona时特别像真人，但缺失颜文字武器库和熟悉的大肥鱼特征，后来恢复完整人设，当前又显得不自然。本任务规划以短稿为底保留自然表达、补回角色素材。这个自然感比较是用户体验反馈，不是受控实验的因果结论。

规划基线main/0fed7c9，实施基线main/07e1589，tracked干净。原三项用户未跟踪文件保留。规划时未查健康；实施起点为partial（AstrBot仍运行，model/gate为0），已由原管理入口按创建身份停止；当前最终状态见RESULT。

实施归属：config/persona.md、必要现有技术报告、PROGRESS.md、tracks/laptop-workbuddy/{HANDOFF,TASKS}.md及本任务文档；忽略归属state/lap49-deployment精确备份和当前技术配对。源码/local/长期记忆/图库不改；不调用远端真实生成/工具服务或发送QQ/微信消息。零生成CLI检查可执行，bot不启动。

## 方案与当前证据

交付 [评审稿](REVIEW.md) 与 [完整候选人设](PERSONA_DRAFT.md)，评审稿同时承担本项设计合同。唯一拟实施的业务文件为`config/persona.md`；无新配置/风格选择器/模型调用，Planner→Replyer与既有能力/预算不改。候选以LAP-47自然接话原则为底，补角色形象、性格、用词和完整颜文字库；去掉开发者说明、固定反应/密度/长示例。没有另建运行角色入口。

决定性只读证据：

- `git show 78da4ea:config/persona.md`为514字符短稿；4810912恢复历史完整版。对应[LAP-47结果](../LAP-47/RESULT.md)与[LAP-48交接](../LAP-48/HANDOFF.md)记录部署，但此前自然感差异仅是本次用户反馈，不是本轮模型实测。
- 替换前[persona](../../../../config/persona.md)第13～17行是开发者使用说明；第95行规定每条1～3个颜文字；第196～281行情绪状态机包括固定任务开场、夸奖顺序与第243行固定三段式。（这些行号指实施前Git版本07e1589，不是替换后的正文。）
- [persona.py](../../../../src/qqbot_gateway/persona.py)第53～57行将角色全文拼给Planner；[dialogue.py](../../../../src/qqbot_gateway/dialogue.py)第45～51行将角色全文拼给Replyer。两处均不解析/过滤开发者说明，故替换文件正文即可，不需改阶段提示构建。
- [model_gateway.py](../../../../src/qqbot_gateway/model_gateway.py)第545/557行、[router](../../../../plugins/qq_router/main.py)第67～68行启动读取原文件并计算会话版本；[persona.py](../../../../src/qqbot_gateway/persona.py)第119行版本含prompt；[wechat.py](../../../../plugins/qq_router/wechat.py)第145/159行复用本根router和persona。角色变化同时影响本根QQ/微信，独立WeChatbot根不在范围。
- [vision.py](../../../../src/qqbot_gateway/vision.py)第87～105行签名包含`config/persona.md`。未来实施必须重做当前技术配对，不能静默关闭识图；复用`scripts/revalidate_lap43_native_web.py`、`scripts/probe_lap42_vision_contract.py`与既有activate流程，不重跑历史IQ/质量大矩阵。发现旧配对/部署问题按实际证据处理，不因本规划预先扩建脚本。

配置默认值/迁移/回滚/分支合同见评审；无新默认值、不改local，正常启动加载，短期上下文按原机制刷新，长期记忆/图库不动。真实自然感、角色强度、颜文字密度与延迟尚未验证。

## 规划验证与Git交付

已核对当前运行稿17,575 UTF-8字节，候选3,901字节；原库15情绪组/64条素材与候选逐项同序一致，缺失0。这个计数只是文档完整性，不证明模型采用率或自然感。六文档严格UTF-8解码、41个本地链接与`git diff --check`通过，业务源码/config/scripts/tests无diff；本轮没有运行功能测试或启动真实CLI。本轮内容检查点仅这六文档，main起点与实时origin/main均为0fed7c9316c6eaec7529b11cd257bdae4e3d29fa；commit/push后核对完整SHA，最终提交号与远端一致结果以会话回执和Git为准。原三项用户未跟踪文件保留。

下一步：用户自行正常手动启动，再自然群测。当前启动加载、连接就绪和真实群聊效果均未验证，不把离线/零生成晋升群聊验收。代码与本机配对已就位，无需再给medium重复实施。

## 实施结果

确认候选原字节已部署；业务改动仅config/persona.md，现有技术报告和忽略配对随当前版本刷新。备份state/lap49-deployment/before，保护检查无意外差异；local/记忆/图库/秘密摘要保持。36项现有定向检查通过，Planner正反与Replyer零生成检查通过，real_generations=0；Replyer无工具/图片、thinking=false。当前配对load_production缺失项为空，quality_state仍pending_user_test；未启动bot或发消息。完整命令、绑定和回滚见[RESULT](RESULT.md)。
