# 调研报告与选型依据

调研日期：2026-10-15（Asia/Shanghai）。关联：[需求基线](REQUIREMENTS.md)、[项目入口](../PROGRESS.md)。

## 1. 证据等级与调研范围

- **已核实**：官方文档、固定版本源码、GitHub API 元数据、本机安装包静态代码/软件元数据。
- **设计判断**：根据需求作出的工程取舍，不代表已有运行结果。
- **待验证**：必须由后续实施阶段运行证明；本轮未调用任何模型或连接QQ协议端。

按“需求澄清 → 现成项目比较 → WorkBuddy能力核实 → 视频提取链路 → 环境盘点 → 可行性门槛 → 实施计划”开展。没有以项目README的宣传语替代运行验证。

## 2. 结论

可以复用成熟 QQ 协议端和聊天框架，真正需要小范围自研的是严格消息入口、WorkBuddy 适配和视频插件的精简/ASR适配。

建议两条线都采用 **NapCat + 严格入口过滤 + AstrBot**。笔记本通过本机文本模型网关尝试调用 WorkBuddy 内置 CLI；PC 使用本地模型端点。人设、会话和视频提取保持同一套契约。

这是有条件的路线：WorkBuddy CLI 的独立鉴权、账号额度归属和工具隔离仍须先验证。**当前只能称为“调研后推荐”，不能称为已经跑通。**

## 3. 现成 GitHub 项目比较

| 项目 | 已核实能力 | 与本项目的匹配与决定 |
| --- | --- | --- |
| [NapCatQQ](https://github.com/NapNeko/NapCatQQ) | 个人QQ协议实现、OneBot v11、Windows Shell/OneKey | 选作两线共用协议端；独立目录运行，不改日常QQ |
| [AstrBot](https://github.com/AstrBotDevs/AstrBot) | OneBot、人格、历史、多模型、插件、MCP | 选作共用聊天框架；仍需严格触发入口，不能直接消费WorkBuddy订阅 |
| [Koishi](https://github.com/koishijs/koishi) / [ChatLuna](https://github.com/ChatLunaLab/chatluna) | 跨平台框架和LLM插件生态 | 可行；本项目Python视频/ASR适配更顺手，暂不双栈实现 |
| [NoneBot2](https://github.com/nonebot/nonebot2) | Python异步消息框架 | 可精确控制触发，但人格/模型管理需组合更多代码，作为替代参考 |
| [MaiBot](https://github.com/Mai-with-u/MaiBot) | 拟人群聊、记忆、主动交互 | 用户当前强调被@才说话和工具，第一版不选主动交互路线 |
| [storyAura/biliVideo](https://github.com/storyAura/astrbot_plugin_biliVideo) | URL/短链解析、平台字幕、音频转写、总结、缓存 | 首选复用视频提取模块；需精简额外功能，替换必剪云ASR |
| [RankoP-114视频总结](https://github.com/RankoP-114/astrbot-plugin-bilibili-video-summary) | OpenAI-compatible音频转写适配 | 仅参考ASR适配设计；验证规模较小，不同时安装两个视频插件 |
| [workbuddy-acp-bridge](https://github.com/jie023/workbuddy-acp-bridge) | MCP→WorkBuddy本机ACP Gateway | 实验后备/协议参考；不是现成QQ bot，也不是稳定公开API |
| [mcp-chat](https://github.com/maile456/mcp-chat) | MCP等待循环+外部聊天API | 当前实现丢失system/history、并发路由弱，排除常驻主线 |
| [Xadeus-QQ-MCP](https://github.com/mouse114514/Xadeus-QQ-MCP) | NapCat收发、MCP、自动唤醒 | 自动唤醒依赖窗口/模拟键盘，不用于笔记本常驻主线 |
| [LinHaiJ/workbuddy-mcp](https://github.com/LinHaiJ/workbuddy-mcp) | 包装codebuddy命令为MCP工具 | 可参考子进程结构；名字不能证明与本机桌面产品/额度等价，默认跳过权限的做法不照搬 |

上述“选用/排除”是对本需求的判断，不代表项目普遍优劣。

## 4. WorkBuddy 与个人QQ的真实边界

### 4.1 官方QQ接入不符合账号要求

WorkBuddy 官方 QQ 指南要求在 QQ 开放平台创建机器人，配置 AppID/AppSecret。这条线属于官方机器人，不能满足用户个人账号要求。

来源：[WorkBuddy QQ指南](https://www.workbuddy.cn/docs/workbuddy/QQ-Guide)；实施时应复核页面实际入口，不使用该路径替代NapCat。

### 4.2 MCP提供工具，不自动提供消息唤醒或模型API

[WorkBuddy连接器文档](https://open.workbuddy.cn/docs/connector)明确MCP连接器是给Agent调用的服务。支持stdio、SSE和streamableHttp不等于个人QQ入站会创建一轮对话。

[MCP tools规范](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)也不能证明某个宿主有常驻聊天调度。用提示词令Agent循环等待消息可作演示，但任务结束、取消、断网、休眠和额度限制均可打断。延长工具timeout不能解决自动恢复。

因此本项目由确定性的事件入口触发独立推理；视频能力可以后续再包装成MCP，不把MCP作为第一版消息循环。

### 4.3 本机内置CLI：值得优先验证，但不是已成功

静态证据来自当前安装包，不是混用普通CodeBuddy文档：

- `D:\WorkBuddyAI\resources\app.asar.unpacked\cli\product.json`：产品WorkBuddy，数据目录`.workbuddy`，版本5.8.2，构建日期2026-10-12。
- `cli\package.json` 内核包版本2.161.0，不应与桌面5.8.2混淆。
- `cli\bin\codebuddy` 路由至 `cli\dist\codebuddy-lite-wb.mjs`，优先使用WorkBuddy精简bundle。

bundle静态注册的能力包括单次`-p`、`stream-json`、system prompt、MCP配置、工具控制。进一步读取实际实现发现：

| 发现 | 对实施的直接要求 |
| --- | --- |
| `--tools`空字符串令内置工具检查返回false | 必须保留空参数；通过原生Node+参数数组执行，避免Windows shell吞空串 |
| `--strict-mcp-config`屏蔽PLUGIN/USER/PROJECT/LOCAL来源，INTERNAL/SDK仍可能保留 | 必须检查初始化工具列表并做无害哨兵测试，不能只看flag名称 |
| `json`输出可能是history数组加末尾result | 推荐逐行解析`stream-json`，不能只`json.loads(stdout)['result']` |
| 认证/模型错误可能输出error事件但仍退出0 | 同时检查事件、result、terminal_reason、非空回答和退出码 |
| 取消可能返回success subtype但无有效回答 | 成功不能只靠subtype判断 |
| `total_cost_usd`在此实现中固定0 | 不能据此声称免费、无消耗或额度不变 |
| 认证支持共享登录存储，但桌面sidecar可能经握手获取加密配置 | 独立CLI是否恢复现有登录仍未知；禁止抽取保护密钥或关闭凭据保护来凑通 |

静态定位关键字：`FileAuthenticationStorage`、`createCredentialFieldCodec`、`workbuddy-auth-session`、`CODEBUDDY_SIDECAR_CREDENTIAL_BOOTSTRAP_SOCKET`、`createIsEnabledChecker`、`setStrictDynamic`、`ResultMessageUtils`、`executeSingleRequest`。

只读确认了代码路径，**没有读取实际凭据、解密登录数据、运行CLI或验证消耗额度**。

### 4.4 ACP后备：不能原样当成群聊服务

审查固定commit：[e232749](https://github.com/jie023/workbuddy-acp-bridge/tree/e2327499273efa093ebdcbffde9a4c8833e26e76)。实际模块：[gateway.py](https://github.com/jie023/workbuddy-acp-bridge/blob/e2327499273efa093ebdcbffde9a4c8833e26e76/src/workbuddy_acp_bridge/gateway.py)、[acp_client.py](https://github.com/jie023/workbuddy-acp-bridge/blob/e2327499273efa093ebdcbffde9a4c8833e26e76/src/workbuddy_acp_bridge/acp_client.py)、[server.py](https://github.com/jie023/workbuddy-acp-bridge/blob/e2327499273efa093ebdcbffde9a4c8833e26e76/src/workbuddy_acp_bridge/server.py)。

它从本地session元数据发现HTTP回环Gateway，通过HTTP/SSE调用ACP。当前源码的全局共享session和每轮`/clear`不适合作为多用户记忆；status只验证元数据心跳；缓存客户端遇到WorkBuddy重启可能先失败；cancel没有远端停止确认。期限也没有覆盖所有排队/初始化/清理。

`permission_mode=deny`只拒绝新权限请求，不能证明禁用已经授权或免询问的Read/exec/连接器。即使CLI失败，也不能把这个项目直接接到群里。仓库声明接口不保证第三方稳定性，且当前tree未发现LICENSE和tests目录；不默认拥有源码再发布授权，也不声称上游pytest覆盖存在。

### 4.5 MCP-chat为何未选

审查固定commit：[7a87e20](https://github.com/maile456/mcp-chat/tree/7a87e20b9719a4aa4878a145c29c74b0bbdcdc1a)。[server.py](https://github.com/maile456/mcp-chat/blob/7a87e20b9719a4aa4878a145c29c74b0bbdcdc1a/server.py)的API只提取最后user文本，未传system/history；选择任意waiting listener，并发请求可能争用单个等待槽。仍依赖Agent持续调用chat工具，不是独立推理服务。作者的“无限调用”描述不能外推为WorkBuddy套餐事实。

## 5. QQ/AstrBot的重要源码发现

调研锁定：

| 组件 | 调研基线 | 用途 |
| --- | --- | --- |
| NapCat | [v4.18.38](https://github.com/NapNeko/NapCatQQ/releases/tag/v4.18.38)，commit `bbd0d2aca3d470c20b33b1d4f95123335633bf26` | Windows OneKey、OneBot v11 |
| AstrBot | [v4.29.0](https://github.com/AstrBotDevs/AstrBot/releases/tag/v4.29.0)，commit `db4ce0c4b0ae94f443c641f0f78cc9228ddabbeb` | 聊天和人格 |
| biliVideo | commit `7cfb5ef0c365e35949e8afd5ff0eca7a513924cb` | 参考字幕/下载/缓存模块 |

这些是调研时基线，不是要求未来盲目使用陈旧版本。实施时记录实际tag、commit、asset SHA256；只有发现兼容性/安全问题才调整并重跑相关验收。

- [OneBot官方接入文档](https://docs.astrbot.app/platform/aiocqhttp.html)：AstrBot为反向WebSocket服务端，NapCat为客户端，路径`/ws`。
- [AstrBot唤醒逻辑](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.0/astrbot/core/pipeline/waking_check/stage.py)：引用、前缀、插件handler也可能唤醒，所以额外过滤是必要的设计。
- [AstrBot默认配置](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.0/astrbot/core/config/default.py)：白名单空数组不等于拒绝全部；管理员可有白名单豁免。默认同群共享已触发对话上下文，本计划选`unique_session=true`。
- [NapCat配置schema](https://github.com/NapNeko/NapCatQQ/blob/v4.18.38/packages/napcat-onebot/config/config.ts)：当前使用`network.websocketClients`，不照抄旧`reverseWs`键。

交叉审阅又确认了几项会直接影响落地的事实，已反映在实施计划：

- 模型能力必须显式`modalities=["text"]`，空数组按兼容所有能力处理；只清空人设tools仍可能有内部工具注入。依据：[tool runner](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.0/astrbot/core/agent/runners/tool_loop_agent_runner.py#L677)。
- 默认模型请求有多次重试，默认溢出压缩会额外调用LLM；复用订阅额度时应设一次尝试、无fallback、截旧轮。依据：[agent_runner](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.0/astrbot/core/config/agent_runner.py)。
- 上游视频provider使用全局session，不自动继承当前UMO；最终摘要必须接回当前conversation。瞬时证据可放本轮system，历史保存跳过首条system，避免长字幕入库。依据：[上游provider](https://github.com/storyAura/astrbot_plugin_biliVideo/blob/7cfb5ef0c365e35949e8afd5ff0eca7a513924cb/bilivideo/llm/astrbot_provider.py)、[历史保存](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.0/astrbot/core/pipeline/process_stage/method/agent_sub_stages/internal.py#L503)。
- `stop_event()`可能使框架跳过后续发送，成功路径用禁止默认LLM＋显式ProviderRequest，不提前停止事件。依据：[scheduler](https://github.com/AstrBotDevs/AstrBot/blob/v4.29.0/astrbot/core/pipeline/scheduler.py#L55)。

## 6. B站“看视频”的实际实现

第一版以内容大意为目标：**先字幕；没有字幕时下载音频，本地ASR转写；再总结正文**。无需WorkBuddy亲自控制浏览器播放。

优先复用storyAura插件的链接/字幕/下载模块。其[转写pipeline](https://github.com/storyAura/astrbot_plugin_biliVideo/blob/7cfb5ef0c365e35949e8afd5ff0eca7a513924cb/bilivideo/transcription/pipeline.py)包含必剪转写；[必剪provider](https://github.com/storyAura/astrbot_plugin_biliVideo/blob/7cfb5ef0c365e35949e8afd5ff0eca7a513924cb/bilivideo/transcription/bcut_provider.py)调用非公开服务，不能承诺稳定免费，也会上传音频。

本计划主ASR选择[faster-whisper](https://github.com/SYSTRAN/faster-whisper)本地`small`/CPU/int8，GPU作为后续优化。媒体下载可复用插件并参考[yt-dlp](https://github.com/yt-dlp/yt-dlp)，所需ffmpeg使用可记录版本的本地二进制。自动字幕和ASR均可能错词，回复标注来源。

只拿标题/简介/热评/平台现成AI摘要的插件不满足本项目的视频正文验收。无声画面、图表细节暂不保证，后续如需要另加抽帧和视觉模型。

## 7. 周末PC路线依据

[Ollama硬件文档](https://docs.ollama.com/gpu)列出RTX5070；[Windows文档](https://docs.ollama.com/windows)支持原生Windows和NVIDIA GPU。PC实际系统/驱动仍须确认。

[qwen3:8b官方分发页](https://ollama.com/library/qwen3:8b)提供Q4_K_M约5.2GB权重，可作为12GB显存的保守起点。权重大小不等于运行显存占用；上下文、并发、KV缓存和其他GPU任务都影响峰值。本计划不预先承诺tokens/s，也不把14B/32B列作首装默认。

## 8. 仍未解决、必须在计划中有退出条件的问题

1. WorkBuddy内置CLI能否在不导出凭据、不使用额外API Key的情况下生成回答？
2. 是否为同一WorkBuddy账号可用的套餐额度，是否需要单独官方登录？精确计费是否可观察？
3. 内置/MCP/内部工具能否确实关闭？
4. stream-json真实字段、取消/重启/中文编码行为是否与静态观察一致？
5. 目标B站样本的字幕/登录/下载是否可用，CPU ASR速度是否可接受？

先过1—4的可行性关，再安装整套QQ/视频链路。失败时报告证据和候选，不以换收费API、键盘自动点击或复制登录密钥掩盖问题。
