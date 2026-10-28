# LAP-43 R2：新材料合同唯一公共批次

返回[PROGRESS](../PROGRESS.md) / [43交接](../tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md) / [材料计划](../tracks/laptop-workbuddy/tasks/LAP-43/MATERIALS_CHAT_PLAN.md)。

## 结论

2026-10-28，session `LAP-43-materials-r2-public`。本次有限验证已结束，**搜索门槛未过，URL gist门槛尚未证实**。不改质量常量、不保存生产search_enabled=true、不部署、不合main、不推进R3。

搜索：按冻结题目完整可回答标准，确认通过0/3，另1题仅取得部分现行资料；即使把该部分计入，最多1/3，仍低于2/3。URL：1题提取失败，另1题取得正文和选材，但留证不足以完成人工gist判断，确认通过0/2，不能声称达到1/2。后一项是审阅证据缺口，不等同已证明长页正文不可用。旧B的0/3及其manifest/attempt/result保留，不按新标准重写。

## 冻结、源码与一次性边界

- 工作根 `C:/Users/yutha/.codex/worktrees/lap-43-stage-a/QQbot`，分支 `codex/lap-43-stage-a`；R1最终HEAD/实时远端一致：`854fef4eef14a5795c3674d85e3bc6cae6e7e262`，初始干净。20:01:36（Asia/Shanghai）登记精确9文件并重读；没有其他session修改夹带。
- 先读PROGRESS、工作线/43交接、TASKS、MATERIALS_CHAT_PLAN及R1实际报告，核对最终代码。R1新74单元/6组合78框架是历史离线证据，本轮没有借它作为真实公共通过，也没有覆盖其报告。
- [冻结manifest](lap-43-materials-r2-manifest.json) 于 **20:04:43.667306+08:00** 落盘；SHA-256 `c3d510b72173d28b836f511d654afc7ca78b98193d47f4ffafe64af3b07d84b8`。包含5项对象/时间意图/期望/人工对照锚点，固定网络与限额、R1 HEAD和完整gateway源码+新probe指纹 `af3e1a717d627b35279e793e771b8a599a7843039686b3cc336e5f714386c5f6`。冻结后未改源码或题目。
- 新入口 [probe_lap43_materials.py](../scripts/probe_lap43_materials.py)，默认inspect不联网；执行前校验manifest SHA、HEAD及源码指纹，以exclusive create预占 `state/lap43-materials-r2/<manifest-sha>/attempt.json`。中断/未知亦占批次，不重放。结果原件同目录result/completed保留，本轮另交付[机器报告](lap-43-materials-r2-public.json)。旧probe没有运行。
- 该独立operator probe仅调用Retriever的既有私有_fetch阶段；PublicHTTP、搜索解析/排序、worker、日期、gist预算均用实际项目代码。probe配置中的search_enabled仍false；生产retrieve无绕过参数，质量常量仍false。没有改正常生产入口。
- 人工对照依据在请求前固定为官方页面结构和题目要求，没有预填未经验证的当前版本/当天事件，也没有浏览器或额外对照请求。因此它们是内容审阅锚点，不是独立实时真值核验。

## 实际逐项结果

| 项 | 冻结问题与意图 | 实际材料 | 人工判定 |
| --- | --- | --- | --- |
| S1 | Python最新稳定版本；current_status | Python官方中文文档首页page_excerpt，semantic_main，1319字节；第二页菜鸟教程body/internal_error。文档自报版本存在，日期unknown | 部分现行资料，未明确支持“最新稳定版”；不能把文档版本认作稳定版公告，不计通过 |
| S2 | Mozilla Firefox近期发布公告；recent_hint | Mozilla产品页/组织首页均body/internal_error，退化为2条search_snippet；日期unknown | 摘要是组织/产品介绍，没有近期发布或更新命题。机器topic_match/substantive=true仍不计人工质量通过 |
| S3 | 中国空间站最近动态；recent_hint | 搜索返回5个中国通用百科/门户等候选，全部未过主题相关；0页面入口/0来源 | 无可回答的空间站动态，失败 |
| U1 | Python What is Python短介绍；none | PublicHTTP成功取得34030字节HTML，仅RAM；worker body/internal_error，0来源 | 未取得gist，失败；不借meta或搜索摘要过关 |
| U2 | Python More Control Flow Tools长页；none | PublicHTTP成功，semantic_main正文35698字节、选材1910字节page_excerpt/excerpt；日期unknown | 留存的三段仅章名、while引言和if标题，未足以证明冻结要求的两个构造/用途。人工gist未验证，不能据hash/字节数判过 |

U2的限制来自本probe的审阅留证设计：每来源最多3个短摘录/600字符且不超过原选材一半，优先主题匹配；泛化中文URL问题没匹配到英语构造正文，保留了过少实质要点。正文和完整选材只在RAM，进程结束后不能复核。没有重新抓取、改题、补跑或把未用页面额度当追加诊断授权。报告中的URL `topic_match=false/substantive=false`是通用检索词启发式结果，不单凭它判URL内容失败；此项独立记为证据不足。

日期逐项：S1/S2/U2最终来源共4条均published_at/modified_at=null、date_source=none、precision/status=unknown；S3/U1无来源。RSS原始reported_date含本地化星期/月格式，当前规范化未得到reported_at，不能把它当目标页日期。本次复用RAM材料分别执行今天/滚动24小时严格检查，4条来源的8项结果全部usable=false，无新增网络。只能在实际内容支持范围内限定表述；严格时点结论缺证据须拒答，抓取时间不证明事件发生时间。没有实际模型答案可作风格/日期措辞验收。

## 请求、失败与计数

北京时间 **20:04:55.892515** 开始，约20:05:06完成。每项实际耗时为S1 2.344s、S2 4.953s、S3 0.187s、U1 1.078s、U2 2.016s，均低于15秒。搜索落地页分别2/2/0，直链1/1。

| 计数 | 实际 | 授权边界/含义 |
| --- | ---: | --- |
| 搜索入口 | 3 | 最多3，每题1次 |
| 页面入口 | 6 | 最多8；4个搜索落地页+2直链 |
| HTTP尝试 | 10 | 3搜索+6页面+1重定向后的HTTP，失败照计 |
| 重定向跳数 | 1 | Python文档/zh-cn/到/zh-cn/3/；每入口最多2 |
| DoH尝试 | 0 | 保持system/null，无DoH配置变化 |
| 系统解析调用 | 10 | 单独观测resolver.resolve；不等同底层DNS数据包数 |
| 重试/额外诊断请求 | 0/0 | 无换题、无第三页、无浏览器替代 |

3搜索、6页面下载都由原PublicHTTP成功。6次HTML worker中2成功、4次新失败均封闭为 `extract_failed / body / internal_error`；受影响页面为菜鸟教程、Mozilla产品/首页、Python短介绍。6个worker均exited=true/cleanup=true，峰值RSS最高37,654,528字节，worker最高约0.203秒。新诊断能收窄到body阶段，不能定位唯一内部异常；没有原HTML、异常消息或堆栈可据此回填旧B原因。不能把“HTTP成功”作为内容质量通过。

报告仅保存必要URL、枚举/日期、计数、hash/字节、相关性和少量公共片段；不存整页HTML、完整选材或RSS全文。候选仅保留URL/hash/长度/相关性/实质性布尔及报告日期。未产生网页归档或长期记忆。

## 离线验证与保护

实际离线命令（既有解释器，不安装依赖）：

```powershell
& E:/CodexWS/QQbot_Snowluma/runtime/astrbot-tool/astrbot/Scripts/python.exe -B -X utf8 -m unittest tests.test_lap43_materials_probe tests.test_lap43_materials tests.test_web_freshness
& E:/CodexWS/QQbot_Snowluma/runtime/astrbot-tool/astrbot/Scripts/python.exe -B -X utf8 scripts/probe_lap43_materials.py
```

31项通过（新probe边界6项、既有材料/日期定向25项），4.294秒；inspect无网络。覆盖manifest漂移/固定上限/源码版本、exclusive attempt、中断不能重放、有限摘录、严格unknown/旧日/冲突/未来/日精度不支持24h及RSS不能代替页日期、生产质量门槛即使配置true也拒绝网络/拒绝绕过参数。没有为本次失败重跑网络或调整断言。

唯一真实批次命令：

```powershell
& E:/CodexWS/QQbot_Snowluma/runtime/astrbot-tool/astrbot/Scripts/python.exe -B -X utf8 scripts/probe_lap43_materials.py --run --manifest reports/lap-43-materials-r2-manifest.json --expected-sha256 c3d510b72173d28b836f511d654afc7ca78b98193d47f4ffafe64af3b07d84b8
```

旧B manifest/public/result、原旧probe state中的attempt/result/completed及R1报告等共14个历史工件hash前后一致。生产6项现存配置/persona文件hash一致，生产HEAD仍 `52866fe10cc654d2e12c5520f7afc5aa8bbe0179`、tracked干净；未探查运行状态，不对自然流量作推断。0真实CLI/模型/QQ/SSH/登录/启停/部署/图库激活；不读群历史、记忆事实或凭据，不改生产代码/数据/网络/CA/代理/账号/费用/provider。

## 交付与停止

本任务仅9文件：新probe/test、3个R2报告工件，以及PROGRESS、工作线HANDOFF/TASKS、43 HANDOFF。搜索仍关闭；URL读取原能力保留，不把本次长页HTTP/正文提取成功扩写成gist质量已验。缺口分别为：候选排名/摘要与题目可回答性、body/internal_error的进一步离线定位、本批U2人工留证不足、所有来源时点能力unknown。需要改变方案或另一次实际验证时回规划/另授权，不消耗本批剩余额度。

最终机器核对通过：manifest与源码指纹未变、5项计数/重定向/worker清理/日期与报告等级一致、未持久化HTML/完整文本字段、14历史工件与6生产文件保护一致；5份本轮Markdown严格UTF-8/围栏及236本地链接通过，冻结manifest保留原CRLF字节以维持已执行SHA；普通暂存差异检查将其CR报作行尾空白，未改写manifest，改用 `git -c core.whitespace=cr-at-eol diff --cached --check` 核对并通过。最终差异/manifest/hash/旧证据/生产保护核对后，精确白名单commit/push到已有隔离分支并核对实时远端SHA，回执以分支tip/会话答复为准；释放归属停止。没有合main或自动R3。生产部署前仍须对最终全部新源码/配置做完整视觉配对验证，不能复制旧active或用R1离线报告替代当前真实契约/图像与人工接受。
