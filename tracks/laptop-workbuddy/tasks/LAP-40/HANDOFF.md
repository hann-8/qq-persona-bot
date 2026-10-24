# LAP-40 SnowLuma：max接续交接

返回[项目入口](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [任务台账](../../TASKS.md) / [新会话入口](MAX_START.md) / [阶段3续作计划](STAGE3_CONTINUATION_PLAN.md) / [材料报告](../../../../reports/lap-40-stage3-materials-2026-10-24.md)。继承AGENTS。2026-10-24，Asia/Shanghai；session `LAP-40-max-realentry-next`已接手材料核验与阶段3续作规划，根独占共享3入口及本任务交接/规划报告。首个可审检查点前不派代码实施。

## 当前状态与路径

**独立集成与A0/A1已离线根审；A2部分组件已子测，整体未装配。** 用户17:24指令“继续”，根`LAP-40-max-realentry-next`已重新领取A2复核/续作，额度余99%，b605d03与远端一致、Git干净；private暂根审/复现，后续逐阶段移交medium。上轮95%停工是历史检查点。Snow尚未真实接入，完整适配/B资格/probe仍缺，72h/7天未开始，生产require_runtime仍总拒。

17:29根已重放A2既有组件并发现异步bind期限漏洞；9162d2c已修复，根17:44重跑20新JS/旧control20+竞态2及Python16+20均过。见[根复核](../../../../reports/lap-40-stage3R-A2-root-review-2026-10-24.md)。[同一medium续作](STAGE3_A2_CONTINUATION_HANDOFF.md)继续Node装配/单PIDpipe/gate允许动作/最终栅栏ACK；private与原创control/test归medium，根独占共享入口，整体仍未完成。

- 实际工作目录：`C:/Users/yutha/.codex/worktrees/lap-40-snowluma-impl/QQbot`，分支`codex/lap-40-snowluma-impl`。复用此worktree，不新建、不归档。
- 原运行目录：`E:/CodexWS/QQbot`，`codex/lap-40-snowluma-trial` / `a798e62498a60b8d061e917d1d8242f42d564ef0`；保持不动。本轮两目录Git均干净。
- 初次接手基线f2bdb0c、原独立集成代码0250f54/总审144b968；17:24重领基线b605d03，公开原创控制期限修复9162d2c已根审。精确当前HEAD/远端以Git为准。
- 原规划分叉已由`1d5dafa38cdf15e9a57146544e551578da5d1cfa`协调；a798已是实现分支祖先，未部署到原checkout。
- A0 871e3de/A1 add12af已推送；根13:30:43完整重放315模块/61 A1/10路径/A0 21+5通过、生产入口退出1。A2最终`f23eac6642523f720504f0b0745d6157edb62607`已推送核对，部分组件自测，根因额度阈值未审/未重放；详见[A2交接](STAGE3_A2_HANDOFF.md)/[报告](../../../../reports/lap-40-stage3R-A2-2026-10-24.md)。本轮全部agent释放写入；下次重新领取后再改共享文件/private。

## 用户意图与最新输入

用户要试用SnowLuma替代NapCat，**长期运行优先**；已授权branch、详细规划后由根agent逐步派sol/medium实施复核，以及本项目归属修改commit/push。当前请求换一个max session以减少上下文，不是批准立即启动/扫码或接受许可。

用户本会话已提供Downloads内`SnowLuma-v2.1.1-win-x64.zip`和`QQ_9.9.36_260924_x64_01.exe`两个明确路径。Snow ZIP大小/固定SHA256匹配，QQ安装包腾讯签名Valid/版本9.9.36.53644。随后用户明确接受EULA/PRIVACY并手动解压；12:43指定runtime的官方index/两协议/Node/5原生摘要均与ZIP一致，Node实际`--version`为v24.22.1。原ZIP仍仅Downloads，runtime内未保留；干净QQ/私有入口/proof仍无、扫码窗口未定。**只通过材料/同意/Node前置，未运行Snow或QQ、未取得私有接线/数据范围/生产资格。** 详情见材料报告；不泛扫其他目录。

用户要求5h剩余<=5%交接；本轮从used11%推进到used95%已停止。13:43工具预计该窗口2026-10-24 17:18:47（Asia/Shanghai）重置，仅为当时账户采样，下次必须重查。旧07:10等待已执行、一次性automation已删除，不重建/不自动安排后续，不reset credit或购买。

## 已交付和验证

| 范围 | 实现/证据 |
| --- | --- |
| 1/2 | 可选provider/旧snapshot摘要兼容；原创早期policy、独立HMAC健康、gate/router统一时效/最终发送栅栏；见[阶段1](../../../../reports/lap-40-stage1-2026-10-24.md)、[阶段2](../../../../reports/lap-40-stage2-2026-10-24.md) |
| 3 | 初轮仅固定源码/[15项清单](PRIVATE_WIRING_CHECKLIST.md)；续作A0最小同意/bootstrap执行通过，完整上游消息/健康接线仍缺；[初轮报告](../../../../reports/lap-40-stage3-2026-10-24.md)/[A0](../../../../reports/lap-40-stage3R-A0-2026-10-24.md) |
| 4A | 原锁lease唯一writer、fake管理创建/spec、跨客户端持久控制seq、drain/stop ACK、封闭Snow环境；716dd47/01af982；[续作报告](../../../../reports/lap-40-stage4A-continuation-2026-10-24.md)：128 Python/9 JS，小修41定向 |
| 4B1 | 持久事故/预算、gate任务监督、唯一writer恢复/新epoch；fff64b7；[报告](../../../../reports/lap-40-stage4B1-2026-10-24.md)：163核心/92框架组合/9 JS |
| 4B2 | 有限配置事务/回滚、正常text trial入口、封闭ACK/unknown指标与有界采样；0250f54；[报告](../../../../reports/lap-40-stage4B2-2026-10-24.md)：最终23专项、此前145受影响组合 |
| 5 | 根审/隐私/全分支diffcheck；144b968时467本地链接通过、47变更路径无私有运行区；原checkout未改 |

上述测试组合有重叠，不能累加。均是temp/fake离线；实际AstrBot库仅只读导入，无真实服务/端口/模型/QQ群消息/SSH/native动作。旧PersonaMatrix 23393字节对8192断言失败与LAP-18/24/28/29/31B差额保留，未改人设凑绿。

阶段3续作已增加[A0报告](../../../../reports/lap-40-stage3R-A0-2026-10-24.md)：固定官方同意纯函数精确片段+原创bootstrap的最小JS闭包，21项执行/5项构建拒绝，根已复现。私有入口只接受synthetic snapshot/owner且永远拒绝生产；所有sink为0仅表示A0没有导入它们，不代表15项上游sink已验证。根审修复清除环境后漏补AUTOLOAD/TELEMETRY及NODE_OPTIONS/NODE_PATH的问题，恶意大小写继承用例通过。完整core/parser/protobuf/Bridge/OneBot、正式owner/观测和真实资格仍缺。

随后[A1报告](../../../../reports/lap-40-stage3R-A1-2026-10-24.md)已完成官方Proton转换和315模块私有图，实际Bridge/parser/OneBot/network/Hook构造链61项执行+10路径元数据，根重放通过；419固定文本blob核验、原版71+ZIP不变。只有TypeScript6.0.2本地禁脚本依赖，private inventory SHA `f3a6e3b33c79af5aaeb2a175eea9699b4cae1866f383564576e6a3f7c0101105`；完整原/修改源/产物摘要在忽略证据及报告。当前仍为入站隐私中间态，所有RPC closed，不称完整transport可用。

A2阈值检查点：独立a2-work/a2-dist 315模块；上游HookSession/HookManager定PID分源只读观测10项、control壳20项+竞态2项、Python正式快照/owner/RuntimeOwner loader10项、继承A1 61项子测通过，计数单位分列且非真实运行。原71/ZIP不变，无真实native/网络/QQ/模型/群操作。**根尚未审，也未重放。** 私有a2-checkpoint-evidence.json及报告记录精确文件/摘要；缺Node正式消费/整体装配、实际Windows单PID创建/pipe提供器、受认证gate允许RPC、最终native提交栅栏/ACK。不要把这些缺项写成“只差用户扫码”。

## 下一步顺序

1. 接手/材料核验/阶段3续作规划已完成，读取本交接与[续作计划](STAGE3_CONTINUATION_PLAN.md)即可续作。操作者后续手动将原ZIP保留到runtime检查器指定位置，agent不自动搬运原生包。
2. 新接续先核额度/Git，重新领取后先读A2交接/报告，根审已交付部分及必要复现；再继续Node正式消费/整体装配、实际单PID/pipe、gate允许动作和最终栅栏ACK。健康/控制壳存在不等于装配完成；保持历史/普通APIHub/磁盘store/原始日志/广域发现关闭。改版只留忽略runtime，不进public，不重做1/2/4/5。
3. B的[资格/probe合同](STAGE3_QUALIFICATION_SPEC.md)已独立细化，尚未实施，领取须等待A1/A2根审；区别probe前置与生产资格、固定受审构建profile及单次DROP证据。当前require_runtime总拒、capability-probe只调用总拒，属于代码未写；Windows默认账号检测共享路径、可信原生重定向机制未证，属于真实前置。不得改共享ini/HOME/APPDATA或猜参数；QQ安装包暂保留。
4. 原生数据范围需可信依据及一次受控探针，最多240秒、全入站DROP、无模型/发群；需要扫码就等操作者，不循环登录。QQ3/3免扫码未证，QQ自动重启保持false。
5. 所有真实前置通过后，才停机/干净快进部署、显式activate、一次正常trial-start并验实际收发。随后72h初筛包含于168h；安静群不判失败，也不能冒充7天实际收发通过。扫码变化观测与8h资源趋势自动判断尚未交付。

## 必须保留的决定

- 固定SnowLuma v2.1.1 / `f8cb15c27bca3d2d1bd044a921e55bfc44bb5e60`；官方完整包`SnowLuma-v2.1.1-win-x64.zip`，42,694,125字节，SHA256 `c739171f95c27706767e69ba36099707c222fcec639b46f4d59689997b527772`。
- public只交原创适配/测试/文档；不自动下载/解压/复制/部署原生组件，不公开上游修改源/patch/bundle/native，不绕保护或伪造EULA同意。普通core build也复制native，不能直接运行试错。
- 现NapCat QQ已patched，不能直接再次注入；只创建/操作明确登记的项目PID+创建时间，不adopt、全局扫描或按名称kill，不触日常QQ/WorkBuddy。
- 账号/群/黑名单前置/私聊关闭、mentions/free、一次模型尝试、backend/model/persona均不变；unknown/partial不重试、不清账。
- 监测/恢复/采样是gate任务，无watch PID；gate自身退出需人工。新绑定/代际不复活旧事件/模型结果。恢复默认false；每事故1动作，24h Node<=2/QQ<=1、间隔1800，QQ动作同时占两预算，坏账/回拨不补空。
- 缺G0/G1/私有证据时真实启动总拒；prepare-policy不是授权或部署证明。任何能力缺口必须明确区分“项目代码未写”与“真实前置未证”。

## 按需定位

配置/静态检查`qq_transport.py`；owner/控制`transport_owner.py`；唯一writer/spec/恢复动作`transport_launch.py`；监督`transport_supervisor.py`；事务`transport_cli.py`；采样`transport_trial.py`，均在`src/qqbot_gateway/`。实际入口`scripts/manage.py`/`scripts/transport.py`；原创JS在`adapters/snowluma/`；gate/router在`onebot_gate.py`/`plugins/qq_router/main.py`。

后续需要命令时按报告读取，不为交接重跑已通过全量测试。一般离线解释器可只读借`E:/CodexWS/QQbot/.venv/Scripts/python.exe`，cwd/PYTHONPATH指向worktree、PYTHONDONTWRITEBYTECODE=1；禁止依赖真实组件作fixture。

早期细节保存在[交接前历史版本](https://github.com/hann-8/qq-persona-bot/blob/144b96861462d839e519cd8bedcfe97316cac0bd/tracks/laptop-workbuddy/tasks/LAP-40/HANDOFF.md)和各阶段报告，不默认全文加载。
