# LAP-08：试用体验改进规划

返回[全局PROGRESS](../../../../PROGRESS.md) / [任务台账](../../TASKS.md) / [工作线HANDOFF](../../HANDOFF.md)。继承全局规则；详细合同在[UX_PLAN.md](../../UX_PLAN.md)。

状态：**completed，仅规划完成，新增功能未实施。** 用户本轮仅授权计划和文档，后续由用户启动gpt-6.1-sol/medium会话实施。规划要求为gpt-6.1-sol/max及以上，模型档位由会话设置控制，不由文档自动切换。

更新时间：2026-10-16 22:10（Asia/Shanghai）。本任务session为当前“试用体验改进规划”会话；未替其他session领取LAP-09—12。

## 目标与范围

把纯文本聊天、群/用户权限、模型三项参数、一键启停、QQ共存和参考人设v2拆成可实施合同，保留旧验收差额，并建立AGENTS先规划后实施准则。本轮不修改config/persona.md、settings.local.yaml、源代码、脚本或运行状态。

## 已核对与决定

- Start-Bot.ps1已经编排四组件；Stop入口存在，但发现和提示需改善。blacklist与Markdown转换尚未实现；模型ID已有入口，context/effort未接通。
- 用户明确上下文重点是模型输入上限；记忆轮数为辅助。用户指定Obsidian人设v2，已只读核对，hash见计划，未改原文。
- 采用鲸鱼娘、鱼片称呼和自然短句；不采用参考中的群旁听、概率/喊名/引用触发、主动冒泡和多条消息。
- 用户说明旧报错时未登录NapCat；记录为现场说明，LAP-01并入LAP-12登录/状态提示。旧模型trace因果关系未从日志证实，不能伪报技术根因已复现。
- CLI 2.168.0源码存在effort和contextWindow控制候选；只有只读证据，原生窗口/控制初始化次序需实施时先零推理验证，不能把本轮规划当已通过。

## 代码与工作区

基线为main/4560ab6，未更改代码。开始时已有PROGRESS、REQUIREMENTS、ACCEPTANCE、工作线HANDOFF、IMPLEMENTATION_PLAN的5份修改及未跟踪TASKS.md，属于前一进度盘点检查点，已保留。

本轮新增AGENTS.md、UX_PLAN.md、本文件；同步上述进度/需求/验收文档及TASKS。没有commit/push，没有启停、扫码、模型请求或群消息。

## 验证与最后检查点

- git diff --check通过；9份变更文档的77个本地链接有效，PROGRESS与LAP-08双向可达。
- UX_PLAN与ACCEPTANCE的U01—U20编号完全一致；所有新增验收保持待实施，没有复用旧测试伪报通过。
- git diff/未跟踪文件清单仅Markdown；src/plugins/scripts/config/pyproject无改动。原参考人设SHA256未变，见计划。
- 本轮仅做只读源码/官方文档核对和文档一致性检查，未运行新代码测试、真实CLI控制、模型推理、群验收或启停。

## 下一步

用户后续启动实施时，推荐LAP-09→10→11→12；一session一任务。原LAP-02/03/04/05继续保留，新功能不抹掉真人隔离、风格接受和恢复/长稳验收。第一个medium会话先读AGENTS→PROGRESS→本线HANDOFF/TASKS→UX_PLAN，领取LAP-09并建立其HANDOFF。
