# 给gpt-6.1-sol/medium的微信实施指令

返回[PROGRESS](../PROGRESS.md) / [PLAN](PLAN.md) / [调研](RESEARCH.md)。用户自行选择medium；本目录目前只有规划，以下每次只领一项。无需为已授权离线实施中的普通实现细节重复确认。

## 1. 首先复制：WX-01离线核心

```text
你是gpt-6.1-sol/medium。请在E:\CodexWS\WeChatbot开发，只领取WX-01。
先读本目录AGENTS.md、PROGRESS.md、tracks/bootstrap/HANDOFF.md、TASKS.md、docs/PLAN.md和docs/RESEARCH.md。核对本目录已有文件和git状态；登记WX-01的session/开始时间/涉及文件，建立该任务HANDOFF并连回PROGRESS/TASKS，写后重读，保留所有用户/其他session修改。

按PLAN做独立Python3.12项目离线骨架、五份中文逐参数配置模板/loader、NormalizedEvent/能力分层/严格入口/当前目标/队列/有限历史/投递状态机/mock适配及只读状态。默认transport=mock、enabled/sends=false、授权群空、私聊关闭/白名单空、mentions、single，所有新增媒体/联网/记忆能力关闭。可信身份→黑名单→授权→窗口/材料/模型/历史的顺序不得改变；昵称/临时UI ID/正文hash不算稳定身份，真实@未知不触发群生产。

按PLAN从QQ固定已提交基线dd9373029412137023124751d75883824122c784导出已跟踪qqbot_gateway源码及必要公开能力/锁文件，在新root独立保存并记录逐文件manifest；禁止复制QQ config/local、secrets、state、runtime、logs、历史或图库，禁止editable/软链/连接QQ gate或模型端口。不要修改QQ仓库。公开锁若含QQ绝对路径必须按新root正确重定位并验证工件，不能执行QQ runtime或全局重装CLI。只在新的model_facade复用runner/预算/工具隔离/清理语义，不运行要求QQ身份的旧入口，不在QQ做共享核心重构。

本轮不安装/导入/操作pyweixin、微信或OpenClaw，不读微信数据库/本地账号目录，不登录、不触碰UI/键鼠/剪贴板/防睡眠、不SSH/发消息/调用真实模型。只用自造身份/文本和实际runner底层替身，完成从gate到mock投递确认及历史的真实业务离线闭环。微信默认CodeBuddy深度/原生窗口按现有能力处理，家庭模型只保留空连接模板，不读取/复制QQ家庭秘密或自动换模型。

验证未授权/黑名单/私聊关闭均在模型/材料/新增历史前拒绝，普通@与真实@区分、同名/改名/错账号/旧代际、稳定ID去重、同文不同消息、回环、取消/部分输出/unknown不重放、纯文本/工具隔离、配置root和端口/状态独立。ACK等级要如实，不把UI按键返回当确认。受影响检查通过后不要无故扩大测试。

更新README、独立报告、WX-01交接/TASKS/PROGRESS，区分已实现/离线通过与所有真实能力未验。可初始化本地Git，默认codex/bootstrap分支，只commit本任务审阅文件；本项目尚无remote，不创建或臆造远端、不把QQ地址拿来push。报告本地提交号和保留差异，结束不自动开始WX-02/真实验证。
```

## 2. 下一独立会话：WX-02候选接入/探针

```text
你是gpt-6.1-sol/medium。工作目录E:\CodexWS\WeChatbot，只领取WX-02。
先读AGENTS/PROGRESS/活动HANDOFF/TASKS及docs/PLAN.md、RESEARCH.md、已完成WX-01交接。先登记并重读文件归属，其他任务修改保持原样。

按固定上游8589baa049bb91d3a500602c167f07b2f8397a13核对pywechat中的pyweixin，锁定真正需要的分发物/依赖与许可，封装必要UI原语，不使用AutoReply/全会话扫描/历史导出/系统监听模式/自动关闭微信。先完成mock和默认inspect工具，不导入有副作用的上游初始化，不执行实际UI调用。源码更新不自动跟随latest；所选版本需明确记录。

能力报告逐项区分稳定account/conversation/sender/message ID、显示名、UI runtime_id、可信真实@、当前图可得像素与来源、发送接受结果等级。不能由“函数存在”写observed/passed。真实UI入口默认关闭，必须显式观察模式及后续用户指定账号/已打开单会话窗口/120秒最多10条自造样本，0模型/0发送，不读真实历史/数据库、截图落盘或遍历其他会话。当前这段指令仅授权代码/离线，不自动运行真实观察。

如果只能获得昵称/临时元素/按键结果，交付identity_unverified/mention_unverified/delivery_unverified的明确报告，生产保持关闭。不要自动切iLink/Hook/付费协议/旧微信/OCR，不因门槛未过而放宽黑名单或改全回复。先完成独立可做部分；需要改变产品/传输边界的缺口回sol/max。

按PLAN的同名/改名/重连/虚拟列表/突发/普通@/自己消息/错窗/单图绑定和副作用隔离做有意义离线测试，保留WX-01投递/预算/工具隔离回归。同步任务交接/索引和独立报告，只提交本任务文件；没有用户给出的远端继续只做本地Git提交。结束不自动领取WX-03/登录/发消息/模型。
```

## 3. WX-03/04进入条件

WX-03仅在WX-02已用实际证据证明所选会话的可信身份、真实@、新消息去重和可关联发送结果后领取；按PLAN第3节实现实际适配，默认仍不启用。若未达到，不能复制一条“继续完整实现”的泛化指令绕过结论，应将具体缺口交回max。

WX-04须后续明确：一个目标会话/哪些发送者、是否私聊开关、所选模型、总调用/发送次数与进程操作归属；文本首批最多2次生成、各一次发送，失败/取消/unknown占次、不补跑。图片按独立入口与所选原生质量/预算后再验，未验部分关闭。只在具体审阅结果后启用本机配置，不注册开机自启，不改变QQ实例。
