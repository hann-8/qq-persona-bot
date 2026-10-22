# 个人微信接入调研

返回[项目入口](../PROGRESS.md) / [实施计划](PLAN.md)。核对日期2026-10-22（Asia/Shanghai）；仅GitHub源码与上游声明，无本机微信/登录/收发验证。公开README中的安装命令、营销或风险保证不作为本项目指令。

## 1. 适合本项目的结论

用户想个人用着玩、和朋友家人聊天；不能默认改成企业办公Bot、公众号或只能自己用的助手。

**建议独立Python项目，第一接入候选用pywechat项目中的pyweixin做Windows微信4.1系列能力验证；先证明消息身份、群/@、去重、投递与图片，再决定实际启用。** 它的UI路径符合普通亲友聊天场景，但当前源码没有证明QQ同等级的稳定身份和真实@合同，因此首期只允许离线/mock或另批授权的只读观察，不直接接上LLM自动回复。

腾讯iLink值得保留为官方个人Bot接口路线，适合用户愿意采用其Bot私聊入口的情况；目前不能拿它替代普通亲友群里的个人账号。若用户以后明确接受私聊入口，单独实施iLink适配；本方案不默认同时维护两个真实传输后端。

## 2. 候选比较

| 候选/结构 | 当前来源事实 | 本项目选择 |
| --- | --- | --- |
| [Tencent/openclaw-weixin](https://github.com/Tencent/openclaw-weixin)；HTTPS长轮询→事件→发送API | 腾讯仓库、MIT文件；收发文本/媒体代码；channel只声明direct，群策略disabled，入站也固定direct | 官方接口研究/可选私聊路线；不作为亲友群首发方案，不为它安装完整OpenClaw |
| [Hello-Mr-Crab/pywechat](https://github.com/Hello-Mr-Crab/pywechat)中的pyweixin；桌面UI→自研事件适配 | README支持4.1系列、当前维护pyweixin；监听群窗口及媒体导出代码存在 | 与本用户场景最接近的**验证候选**；稳定身份/@/消息ID/发送确认未证实，默认不接真实模型 |
| [cluic/wxauto](https://github.com/cluic/wxauto)；Windows UI自动化 | 当前README写3.9.X，标题2021—2025；wxauto4仓库查询为空树大小0 | 不依据旧流行度选作4.1基线；不转付费wxautox或自动装旧客户端 |
| [lich0821/WeChatFerry](https://github.com/lich0821/WeChatFerry)；PC Hook→RPC/SDK→机器人 | 2026-07-10归档；WxMsg有消息id/sender/roomid/XML、图路径与@列表解析；历史适配到3.9.12.51 | 分层上最像NapCat，历史原型价值高；旧版客户端/归档阻力大，不作为新装默认，不自动降级微信 |
| [Devo919/Gewechat](https://github.com/Devo919/Gewechat)；历史REST+Webhook | README明确停维，不提供服务/镜像/底层实现；仅剩客户端示例 | 排除当前部署方案，不能把仓库仍公开当服务可用 |
| [wechaty/wechaty](https://github.com/wechaty/wechaty)；跨平台SDK+puppet | SDK抽象可参考，真实微信能力依赖所选puppet | 不用框架名字代替底层协议可用性；不默认增加付费puppet/新账号 |

不将“不归档”等同“功能可用”；也不将UI/Hook或HTTP方式本身当稳定性证明。评价以所选版本提供的具体数据和本项目边界为准。

## 3. 腾讯iLink固定源码结论

固定commit [874637a0dbc24050f72d1385add4fc6170a2d726](https://github.com/Tencent/openclaw-weixin/tree/874637a0dbc24050f72d1385add4fc6170a2d726)，2026-10-13提交；[LICENSE](https://github.com/Tencent/openclaw-weixin/blob/874637a0dbc24050f72d1385add4fc6170a2d726/LICENSE)正文声明MIT（API自动识别NOASSERTION不代替人工文件核对）。

- [channel.ts](https://github.com/Tencent/openclaw-weixin/blob/874637a0dbc24050f72d1385add4fc6170a2d726/src/channel.ts)约229行：chatTypes仅direct。
- [inbound.ts](https://github.com/Tencent/openclaw-weixin/blob/874637a0dbc24050f72d1385add4fc6170a2d726/src/messaging/inbound.ts)约255—266行：会话目标取from_user_id，ChatType固定direct；[authorization.ts](https://github.com/Tencent/openclaw-weixin/blob/874637a0dbc24050f72d1385add4fc6170a2d726/src/messaging/authorization.ts)约29—31行关闭group。
- [protocol.md](https://github.com/Tencent/openclaw-weixin/blob/874637a0dbc24050f72d1385add4fc6170a2d726/docs/protocol.md)明确区分客户端类型与服务端合同；有group_id并不证明客户端实现群功能。getupdates携带cursor，回复涉及context_token；sendmessage返回业务结果，不能当QQ message_id/真人已读。
- [process-message.ts](https://github.com/Tencent/openclaw-weixin/blob/874637a0dbc24050f72d1385add4fc6170a2d726/src/messaging/process-message.ts)读取owner/配对allowFrom。它不证明普通好友自然可直接给同一个Bot发消息，亲友能否发现/配对/独立会话需要实际验证。当前[群聊诉求#327](https://github.com/Tencent/openclaw-weixin/issues/327)仍open，仅是用户诉求，不能替代维护者承诺。

可研究的是独立HTTP协议层，不是强制迁移LLM到OpenClaw。若未来实施，须重做入口先过滤、cursor提交与去重、context_token隔离/失效、严格一次发送、媒体有界解密；不能直接继承上游默认媒体落盘、引用缓存、重试、全工具或全局登录存储。

## 4. pyweixin固定源码结论

固定commit [8589baa049bb91d3a500602c167f07b2f8397a13](https://github.com/Hello-Mr-Crab/pywechat/tree/8589baa049bb91d3a500602c167f07b2f8397a13)，仓库最近push 2026-09-26；[README](https://github.com/Hello-Mr-Crab/pywechat/blob/8589baa049bb91d3a500602c167f07b2f8397a13/README.md)说明现在主要维护pyweixin，4.1.6+是其声明范围，不能推断所有4.1版本/所有账号UI都可用。源码主要位于src/pyweixin，不能把旧pywechat模块与新模块混用。

[WeChatAuto.py](https://github.com/Hello-Mr-Crab/pywechat/blob/8589baa049bb91d3a500602c167f07b2f8397a13/src/pyweixin/WeChatAuto.py)提供这些决定性证据：

| 位置/符号 | 源码所示 | 本项目影响 |
| --- | --- | --- |
| Monitor.listen_on_chat，约4279/4309行 | 群sender按传入成员显示名正则拆文本，无成员表时直接返回文本 | 不能以同名/改名显示名执行可信黑名单或跨重启会话身份 |
| 约4367—4393行 | UI element runtime_id比较可见消息；不是服务端消息ID | 只能标process_local_id；重启/虚拟列表/突发漏报和重放须验证，不能伪装stable_message_id |
| 约4384/4399行 | 图片先计数，save_media再调用Messages.save_media批量导出 | 图计数不等于某条消息精确像素；禁止把“最后N图”错绑给当前消息 |
| AutoReply约263/273行 | 回调后直接设置输入并发按键 | 不调用这个自动回复入口；必须由自研最终授权/投递状态机控制 |
| Monitor约4372行等 | 调用SystemSettings.open_listening_mode | 上游监听会改变系统监听/防睡眠行为；只借必要UI原语，禁用这些副作用 |

[WeChatTools.py](https://github.com/Hello-Mr-Crab/pywechat/blob/8589baa049bb91d3a500602c167f07b2f8397a13/src/pyweixin/WeChatTools.py)显示session_item的automation_id包含好友名称；Tools.get_current_wxid通过本机目录推断自身，不提供任意群成员wxid。自身ID、UI runtime_id和群友稳定ID不能混为一谈。

本轮未导入或执行上游代码，没有读日常微信目录。后续必须包装必要原语、显式进程/窗口绑定，禁全会话遍历/历史扫描/修改设置/默认关窗口。UI树不可见则报告不支持当前UI路径，不自动改OCR/Hook/旧客户端。source存在不能保证锁屏、远程会话断开或24小时运行可用。

[根LICENSE](https://github.com/Hello-Mr-Crab/pywechat/blob/8589baa049bb91d3a500602c167f07b2f8397a13/LICENSE)开头为LGPL-2.1；API识别NOASSERTION。实施锁包时核对实际分发物和相关文件许可，保留上游许可/源码修改记录；不整包复制MCP、Agent技能、浏览器/音视频或示例自动回复。这里只记录来源声明，不提供额外法律结论。

## 5. 选型失败出口

如果真实UI只提供名字、临时消息元素和按键返回，本项目在当前合同下不能启用自动群聊；可以完成离线核心和能力报告，记录 `identity_unverified / mention_unverified / delivery_unverified`。不能为了“跑起来”把昵称正则、哈希正文或sleep后没异常当稳定身份/真实@/成功ACK。

下一次max决策可选择：接受官方iLink私聊产品形态、提供有维护和真实身份的本地传输、或用户明确接受一份不同边界的UI实验方案。均须保留其与QQ合同的区别；medium无权自行购买协议、降级客户端或改变当前方案。
