# LAP-43 阶段B实际结果

返回[43交接](../tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md) / [PROGRESS](../PROGRESS.md)。

## 结论：本批次公共搜索质量未通过，未部署

2026-10-28，session `LAP-43-stage-b-public-quality`。阶段A隔离分支 `codex/lap-43-stage-a` 起点本地/实时远端 `17d44dc6a3cab81016bda16dcd91920dfe4b5087`，初始干净。生产Snow main本地/实时远端仍 `52866fe10cc654d2e12c5520f7afc5aa8bbe0179`，本轮没有写生产文件或调用运行管理。登记时间18:42:46 Asia/Shanghai，TASKS写后重读。

PLAN 5.5一般相关可读正文 **0/3**，时效相关正文及可核对日期 **0/3**，均低于2/3。不是所有公网不可达：3搜索及4页面传输都返回成功；4页面全部在正文提取阶段返回 `extract_failed`。第三题未选出可读取候选。没有可核对正文/日期/关键事实，不能晋升质量通过或推断全网最新覆盖。`SEARCH_QUALITY_PASSED=False`保留；本机`web.search_enabled`缺省false且未保存任何值，不部署、不推进C。

## 冻结与一次执行

[冻结清单](lap-43-stage-b-manifest.json) SHA256 `80ed99fb80b9b58402a627dda9068f74ab9eb4bd2a1abc23fa5f4ddf04cc9904`，先落盘公共对象、日期窗及人工对照入口，再做人工对照及项目客户端批次；结果出现后没有换题。软件题明确日期窗覆盖默认“版本可早于7天”例外。

| 固定题 | 北京日期窗（末端截于请求时刻） | 实际页面入口 | 正文/日期结论 | 单题总耗时 |
| --- | --- | --- | --- | --- |
| NASA官方公告 | 10-22—10-28 | nasa.gov首页、首页?m=0 | 2次extract_failed，未取得目标公告正文 | 4.188秒 |
| Python最新稳定发布 | 10-01—10-28 | python.org首页、downloads | 2次extract_failed，未取得发布正文 | 1.875秒 |
| UN News苏丹公开新闻 | 10-22—10-28 | 无 | 候选筛选后无页面，日期未证 | 0.218秒 |

只执行一次 `scripts/probe_lap43_search.py --run --manifest reports/lap-43-stage-b-manifest.json --expected-sha256 <上述SHA>`；真实客户端结果及独立审阅见[机器报告](lap-43-stage-b-public.json)。`raw_batch_result.human_review=pending`忠实保留工具原输出；外层review已明确failed，不改写原证据。忽略目录 `state/lap43-search/<SHA>/attempt.json`、result.json、completed.json保留；同一SHA的x模式预占阻止第二次尝试。

实际 **3搜索入口+4页面入口**（授权上限3+6），**7次HTTP尝试、0重定向、0 DoH HTTP、7次系统解析调用、4次提取失败、0传输失败、0重试**。HTTP尝试指PublicHTTP的session.get尝试计数，不冒充TCP包数、连接数或系统DNS底层请求总数；`audit.dns_calls`本实现计DoH而非系统解析。页面失败后未取第3页补数，各查询整体均小于15秒，单入口最多2重定向，现有不透明RSS跳转拒绝保持。

只读生产features的public_network/search开关字段：未覆盖网络政策，沿项目默认system/null；PublicHTTP `trust_env=False`、Cookie禁用、TLS校验、公网解析/peer和URL限制保持。不改DNS/代理/CA/账号/凭据，不复制生产配置到隔离根。

## 人工公共对照与证据限制

预先冻结对照为NASA News、Python downloads及UN News官方入口，不预设具体事件。独立浏览器搜索3题仅作人工对照，未替代项目实测，亦不计入项目HTTP预算：NASA返回日历等非目标材料，未建立本窗公告对照；UN News受robots限制，未建立本窗新闻对照。Python返回[官方3.15.0发布页](https://www.python.org/downloads/release/python-3150/)（2026-10-09）及其他版本材料，可供发布类型/日期对照，不能凭此独立证明当前最新补丁。没有因对照不足换题或追加浏览/项目请求。

缺口有两层：本批次候选落到首页/列表页或无符合筛选候选，未提供足够目标文章；4次worker统一extract_failed未暴露内部异常，且未留整页正文，本轮不能唯一归因于页面结构、内容限制或提取器具体分支。合成worker通过不解释这4个真实失败，不擅自降级legacy、放宽安全检查或换服务。若未来需要继续搜索实测，须另选明确授权的有界批次；本轮不重跑或用剩余页面名额补题。

## 合同内修复与离线验证

- 最新版本无显式时间窗仍可保留官方version_dated合同；出现ISO窗/今天/本周/近N天时不再覆盖stale为version_dated。修复近N天已解析后仍落到WINDOW_UNSUPPORTED的错误。
- 公共批次仅用其本地ObservedHTTP/ObservedRetriever包装真实PublicHTTP，记录每入口HTTP尝试/跳转/DoH/耗时/失败、系统解析调用和筛选前有界公共正文摘录/hash/日期；未给正常生产入口新增绕过参数。
- 8项`test_web_freshness.py`、2项`test_lap43_search_probe.py`、15项`test_lap43.py`，**共25项通过**。实际受管worker+替身HTTP验证无日期、仅modified、日期冲突、窗外旧页、未来页均无合格source且返回本地说明；日期纯函数另验滚动24小时精度/错误日期。冻结SHA不匹配在网络前拒绝；同SHA第二次预占拒绝；正常生产即使search_enabled=True仍因代码质量false不发请求。
- 全部测试命令使用 `E:/CodexWS/QQbot_Snowluma/runtime/astrbot-tool/astrbot/Scripts/python.exe -B -X utf8 -m unittest discover -s tests -p <上述文件名> -v`；只是读取既有解释器，临时夹具不读生产persona/群数据。首次新增反例暴露近N天异常，修后最终25项通过。
- 本轮未重跑阶段A框架矩阵/视觉完整报告。gateway日期源码改变意味着旧阶段A视觉报告的完整源码binding已过期；未来用户选择部署前须最终源码冻结后重新取得当前离线/契约/视觉配对证据，不能沿用旧report冒充当前有效。本轮不调用真实CLI或视觉回归helper。

0真实模型、0QQ、0SSH、0登录、0bot启停；未读取/上传群历史、记忆、名册、真实身份；未改生产main/local/persona/图库/pending/运行实例。未探活或统计自然free流量，0为本session主动调用，不对自然业务调用作推断。搜索失败不阻碍独立owner/输入/表情以后被单独选择部署，旧任务差额不变。

## 交付和停止点

只交付本阶段登记文件到隔离分支，不合main。11份归属文件、212本地链接及false门槛核对通过。冻结manifest保留最初CRLF字节及原SHA，不为消除CR显示而改写冻结证据；使用 `git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --cached --check` 检查实际空白错误。最终差异/隐私/链接/冻结SHA检查通过后commit、push并核对实时远端SHA，回执以分支tip与会话答复为准；不自引用提交。保留忽略的公共批次证据及阶段A旧日志。完成Git核对后释放session归属并停止，不自动推进C或其他真实验收。
