# 微信项目规划交接

返回[PROGRESS](../../PROGRESS.md) / [TASKS](../../TASKS.md)。继承[AGENTS](../../AGENTS.md)。状态：WX-00详细规划完成，未实施/真实验证。

2026-10-22，session `LAP-38-vision-web-wechat-plan`；用户要求sol/max规划，后续sol/medium实施。用户说明个人娱乐、和朋友家人聊天。项目初始空目录 `E:\CodexWS\WeChatbot`，本轮仅建立七份引导文档，不装依赖/写运行配置、不建remote、不登录/触碰微信、不调用LLM或家庭SSH。

已完成：[PLAN](../../docs/PLAN.md)规定需求/非目标、轻量独立router、固定QQ源码快照复用、规范事件/稳定身份/@/去重/投递/图像、五份配置默认、分阶段任务/验收/回滚；[RESEARCH](../../docs/RESEARCH.md)核对腾讯iLink/pyweixin/wxauto/WeChatFerry/Gewechat/Wechaty；[指令](../../docs/IMPLEMENTATION_GUIDE.md)给各阶段完整复制文本。

关键选择：pyweixin是普通亲友聊天的验证候选，默认只mock；其群sender显示名/UI临时消息ID/按键结果不满足生产合同。腾讯iLink当前direct only，普通亲友群不应承诺；原WeChatFerry归档、Gewechat停维排除默认基线。源码可用不代表本机/账号可用。

修改文件仅本引导包七份Markdown。其QQ版本化快照在LAP-38，复制到微信目标后逐文件hash比对；QQ快照的Git交付见QQ任务交接，不表示微信目录有独立远端。后续以微信目录实际代码/文档继续，不双向覆盖镜像。

验证：本轮没有微信代码或测试，不借QQ历史测试计数。文档本地链接/围栏、相对root和快照hash由LAP-38收口核对；真实所有能力均unverified。没有用户/其他session原有文件被覆盖。

下一步：用户在会话设置选择gpt-6.1-sol/medium，在本目录按指引只领取WX-01；先登记/建任务交接，做完整离线mock闭环，再提交本地可审阅检查点。没有remote时不臆造推送地址；不自动开始WX-02/真实UI/登录/发消息/模型调用。
