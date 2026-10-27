# LAP-43阶段A实际结果

返回[PROGRESS](../PROGRESS.md) / [43交接](../tracks/laptop-workbuddy/tasks/LAP-43/HANDOFF.md) / [PLAN](../tracks/laptop-workbuddy/tasks/LAP-43/PLAN.md)。

2026-10-27，Asia/Shanghai；session `LAP-43-stage-a-implementation`，19:50登记及重读。起点本地/实时远端main均 `52866fe10cc654d2e12c5520f7afc5aa8bbe0179`，包含 `2986667c` 规划和main整合回执。先查本chat附件及现有worktree，无适用隔离树；新建 `C:/Users/yutha/.codex/worktrees/lap-43-stage-a/QQbot`、分支 `codex/lap-43-stage-a`。全程只领取43，归属及后续补充均先登记重读。

已实现及离线验证，**尚未部署/加载/真实验收**。生产main及运行实例未操作，原识图true未写改或重新加载验证。本轮没有公共搜索probe、真实CLI probe、原生IQ或回归helper真实动作，没有真实模型/QQ/群/SSH/登录/启停/图库激活；未复制生产local、秘密、登录或群数据作为夹具，框架测试使用临时根和自造配置/人设/图片/事件/RPC。当前persona仅在预算进程内只读，不输出或保存原文。

## 完成内容

- A1：配置要求admin去重后恰好1项合法、非bot/blocked；框架admin同源。gate仅真实sender匹配owner的定向新文字能暂停/恢复；重复同态不增代际，普通@、裸@不解禁。引用/显示名/角色/模型均不赋权，授权群/私聊边界优先。统一现有重置权限及输入分流；空@0生成短应声，不建RAM/焦点/记忆；有图沿当前cap，失败图/不支持媒体不假装理解caption。local_notice保留原事件/发送guard/队列，按实际代理回执区分sent/unknown/failed，缺ACK不称已送达。
- A1：NFKC/casefold及有限叫名词法、引用/代码/URL排除、英文边界；真@优先，at他人/未知引用不升级。ACK同人焦点支持“那怎么办/为什么呢/再详细点/继续/还有呢”，保留60秒/无插话约束，感谢/附和不强迫答。direct仍由本地must_reply固定，silent/错协议不是正常沉默；不加分类/修复模型。
- A2：`activate_lap43_memes.py`默认inspect，七项登记/图片格式尺寸帧数/hash/候选预算、当前配置/active/pending基线、重解析点、停机/内置配置锁、原字节备份/不存在标记、二次guard、激活幂等及变化拒绝。仅临时七图夹具实测；未读旧NapCat根，未执行旧迁移verify，未改真实active/pending/library。
- A3：search_enabled默认false、freshness_days=7（1..30），bing_rss唯一候选；质量常量仍false，read独立。时效意图先于搜索门槛处理；明确URL仍read，隐私/模糊对象/不联网偏好保留。事件到达时冻结requested_at，当前问题/称呼归一化、1搜索/5候选/2页及有界相关性和有限主题相关一手来源排序；未知域不冒充官方。仅相关且时效可证正文用于最新结论；旧版本资料例外仅限主题关联的一手域，仍按“截至查询看到的资料”理解，不保证全网最新。
- A3：受管HTML worker提取受限meta/JSON-LD/主文time，父schema配对；北京时间自然日/滚动小时、无时区降日精度、缺失/未来/冲突/修改日分开。来源日期/请求和获取时刻进入同一次材料、manifest日期hash及v2 metadata，来源后缀由代码追加；所有元数据/URL/标题/正文计入6000材料及最终预算。来源放不下时本地失败，不静默删一条实际使用来源。公共probe工具默认无网络，显式运行需冻结3题/期望对象/窗口/人工对照和manifest SHA，单批单次、不自动开放质量门槛。
- A4：新增 `lap43_current_regression` 固定模式分派，独立当前binding目录/授权/probe/attempt/review/candidate/配对激活备份；默认inspect。每版每例一次，人工答复hash与反馈必需，保留原IQ-01历史接受和原失败，不称当前重跑；新IQ-05及当前ingress仍待真实授权。旧42路径/常量/批次/报告未改写；新旧unknown均检查，旧ledger只读核对。新offline绑定43 verifier/tests/source摘要，probe读取同模式journal/原始receipt/wire/phase及协议摘要，prepare/生产/observe同模式配对。adapter签名仍覆盖所有gateway，并扩入43 helper/测试等依赖，不缩小集合。

## 本次实际验证

命令（已有依赖环境，仅执行自造输入及底层替身）：

```powershell
& E:/CodexWS/QQbot_Snowluma/runtime/astrbot-tool/astrbot/Scripts/python.exe -B -X utf8 scripts/verify_lap43.py --current-persona E:/CodexWS/QQbot_Snowluma/config/persona.md
```

当前结果：47个定向单元，74项实际AstrBot/provider/run_agent/发送栅栏场景，四个必要组合（两后端各控制/成员/记忆/表情/网页、图片传递各一组）。CodeBuddy通过真实runner底层假CLI，Ollama通过真实runner底层假transport；模型、SSH、QQ均为0。没有运行旧报告脚本主入口或A4，也没有全量重跑无关旧矩阵。旧单元仅选择现有表情协议/路径、视觉Mod和旧人工接受/图片成员cap必要回归。

| 合同 | 实测范围与证据边界 |
| --- | --- |
| O-01..04 | 合成gate真实sender控制/暂停中@及图片拦截、旧排队/生成/图片/typed@输出代际、重连和unknown、三模式重置公共入口owner/非owner；不冒充真实他人群验收 |
| O-05 | 临时根实际configure/隔离数据库保存两组内置插件禁用、同源admins、实际registry排除及未知插件拒绝；另有实际run_agent链工具隔离。没有启动完整QQ框架实例 |
| I/A | 占位文字/空白/媒体caption、正负词法表、ACK焦点同人/插话/超时/at他人/未知引用/重连；direct silent≤1生成/无修复；队列失效/模型中暂停/发送unknown保留 |
| M | 临时7图inspect/锁内激活/原manifest重复激活幂等、缺图/hash/路径/候选/配置竞争、运行身份拒绝；真实原事件文字/仅图/失败图/最多部件/认真来源无图协议；无生产7图激活或图片ACK |
| W | 冻结时钟意图/日期窗口/隐私长数字；真实受管worker及父schema、HTTP替身1+2上限/过期排除、日期manifest篡改/后缀、两runner材料/metadata/原事件ACK；公共查询W-05未执行 |
| V | 旧offline遇新签名拒绝；独立路径/排他attempt/缺授权和人工测量拒绝；新配对active事务的成功/加载失败回滚/并发保护/陈旧candidate反例；当前真实probe/IQ/群图均未执行 |

机器结果：[lap-43-vision-offline.json](lap-43-vision-offline.json)；来源继承/模式范围：[lap-43-vision-sources.json](lap-43-vision-sources.json)。本报告是隔离源码签名的离线证据，不是生产最终配置的回归凭证；阶段C须最终源码/配置冻结后重新核对当前报告及实际契约。

当前persona仅进程内读取19256 UTF-8字节。CodeBuddy/DeepSeek/low采用48000字节政策，attention+1000×1000图片+768成员+1536记忆+2网页日期材料+7表情候选测得33846政策字节；native边界T=31350/F=8985/V=1024/O=128000/C=1000000（O为模型真实最坏输出上界，项目输出reserve仍2048）。Ollama使用12288字节**公开示例政策**，当前persona加必需输入即 `INPUT_TOO_LONG`，按既有失败分支0生成；没有读取或声称核对家庭实际运行配置、扩大预算或修改人设。两后端框架可用不等于两者当前persona都可容纳。

## 未验、后续及回滚

搜索候选公共质量未过，search_enabled及SEARCH_QUALITY_PASSED均保持false；当前网络/正文与时效质量只能由后续选中的B有限公共批次证明。新版本没有当前真实视觉probe/授权/人工IQ-05/配对active/群图，不能合main后直接启动，也不能静默关闭原识图。既有7图仍待明确运行授权及JPEG/GIF实际ACK/客户端动画；真实owner/非owner、空@、叫名和搜索内容均未在QQ验收。旧18/21/27/35/42差额保留，不批量领取或改历史结论。

阶段A只保留隔离分支。回滚此交付不需要碰生产：继续使用未变main即可。未来C按PLAN先停受管实例、最终配置冻结、配对新证据/图库和正常启动；失败按拥有摘要恢复配对代码/配置/active，不能整份覆盖后续local、删除unknown/证据或重试洗批次。Ollama当前persona容量限制需要以后明确选定该后端时单独处理，本轮不改方案/预算。

## Git交付

提交范围仅TASKS已登记归属，旧报告/原证据/local/persona/秘密/图库不进入本轮差异。推送 `codex/lap-43-stage-a` 后核对远端SHA；生产main持续为基线 `52866fe1` 且工作树干净。实际代码提交及回执见43 HANDOFF/会话最终答复，Git交付不代表部署或真实验收。阶段A交付后释放归属停止，不自动推进B/C/D。
