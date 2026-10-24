# LAP-40 SnowLuma：max接续交接

返回[项目入口](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [任务台账](../../TASKS.md) / [新会话入口](MAX_START.md) / [阶段3续作计划](STAGE3_CONTINUATION_PLAN.md) / [材料报告](../../../../reports/lap-40-stage3-materials-2026-10-24.md)。继承AGENTS。2026-10-24，Asia/Shanghai；session `LAP-40-max-realentry-next`已接手材料核验与阶段3续作规划，根独占共享3入口及本任务交接/规划报告。首个可审检查点前不派代码实施。

## 当前状态与路径

**项目侧独立集成已实现、离线通过并根审；SnowLuma尚未真实接入，waiting_operator。** 阶段3上游私有适配、真实probe执行与资格判定仍未交付；72h/7天未开始，生产`require_runtime`仍总拒，不能填true放行。

- 实际工作目录：`C:/Users/yutha/.codex/worktrees/lap-40-snowluma-impl/QQbot`，分支`codex/lap-40-snowluma-impl`。复用此worktree，不新建、不归档。
- 原运行目录：`E:/CodexWS/QQbot`，`codex/lap-40-snowluma-trial` / `a798e62498a60b8d061e917d1d8242f42d564ef0`；保持不动。本轮两目录Git均干净。
- 接手基线：`f2bdb0c7096ea8f606e18f18f2926e5c8b680025`，2026-10-24 12:35已核对对应远端分支SHA、工作区干净；最终代码仍`0250f548f4e96484bef12096895e337e103bdd44`，总审`144b96861462d839e519cd8bedcfe97316cac0bd`。
- 原规划分叉已由`1d5dafa38cdf15e9a57146544e551578da5d1cfa`协调；a798已是实现分支祖先，未部署到原checkout。
- 当前无实施子代理运行。旧根agent在交接交付后停止编辑；新max session领取LAP-40后负责共享3入口。实施仍按原授权逐阶段派`gpt-6.1-sol/medium`，串行根审，不创建额外用户chat作子任务。

## 用户意图与最新输入

用户要试用SnowLuma替代NapCat，**长期运行优先**；已授权branch、详细规划后由根agent逐步派sol/medium实施复核，以及本项目归属修改commit/push。当前请求换一个max session以减少上下文，不是批准立即启动/扫码或接受许可。

用户本会话已提供Downloads内`SnowLuma-v2.1.1-win-x64.zip`和`QQ_9.9.36_260924_x64_01.exe`两个明确路径。Snow ZIP大小/固定SHA256匹配，QQ安装包腾讯签名Valid/版本9.9.36.53644。随后用户明确接受EULA/PRIVACY并手动解压；12:43指定runtime的官方index/两协议/Node/5原生摘要均与ZIP一致，Node实际`--version`为v24.22.1。原ZIP仍仅Downloads，runtime内未保留；干净QQ/私有入口/proof仍无、扫码窗口未定。**只通过材料/同意/Node前置，未运行Snow或QQ、未取得私有接线/数据范围/生产资格。** 详情见材料报告；不泛扫其他目录。

用户要求5h剩余<=5%交接；历史07:10等待已执行，一次性automation `lap-40-snowluma`已删除。12:34重查300分钟窗口used11%/剩89%、周窗口used33%/剩67%；不循环按已过期07:10唤醒，不reset credit/购买。额度仅本次采样，后续按阶段检查。

## 已交付和验证

| 范围 | 实现/证据 |
| --- | --- |
| 1/2 | 可选provider/旧snapshot摘要兼容；原创早期policy、独立HMAC健康、gate/router统一时效/最终发送栅栏；见[阶段1](../../../../reports/lap-40-stage1-2026-10-24.md)、[阶段2](../../../../reports/lap-40-stage2-2026-10-24.md) |
| 3 | 仅固定源码核对和[15项私有清单](PRIVATE_WIRING_CHECKLIST.md)，无私有改版/构建/执行级接线；见[阶段3](../../../../reports/lap-40-stage3-2026-10-24.md) |
| 4A | 原锁lease唯一writer、fake管理创建/spec、跨客户端持久控制seq、drain/stop ACK、封闭Snow环境；716dd47/01af982；[续作报告](../../../../reports/lap-40-stage4A-continuation-2026-10-24.md)：128 Python/9 JS，小修41定向 |
| 4B1 | 持久事故/预算、gate任务监督、唯一writer恢复/新epoch；fff64b7；[报告](../../../../reports/lap-40-stage4B1-2026-10-24.md)：163核心/92框架组合/9 JS |
| 4B2 | 有限配置事务/回滚、正常text trial入口、封闭ACK/unknown指标与有界采样；0250f54；[报告](../../../../reports/lap-40-stage4B2-2026-10-24.md)：最终23专项、此前145受影响组合 |
| 5 | 根审/隐私/全分支diffcheck；144b968时467本地链接通过、47变更路径无私有运行区；原checkout未改 |

上述测试组合有重叠，不能累加。均是temp/fake离线；实际AstrBot库仅只读导入，无真实服务/端口/模型/QQ群消息/SSH/native动作。旧PersonaMatrix 23393字节对8192断言失败与LAP-18/24/28/29/31B差额保留，未改人设凑绿。

## 下一步顺序

1. 接手/材料核验/阶段3续作规划已完成，读取本交接与[续作计划](STAGE3_CONTINUATION_PLAN.md)即可续作。操作者后续手动将原ZIP保留到runtime检查器指定位置，agent不自动搬运原生包。
2. 根审/交付计划后串行派medium A0私有bootstrap/同意/固定native解析/JS-only，再A1隐私接线、A2真实观测控制源；均先执行级合成，不重做1/2/4/5。改版只在忽略runtime，不进public。
3. 再B补资格/probe实现并先落精确schema根审。当前require_runtime总拒、capability-probe只调用总拒，属于代码未写；Windows默认账号检测共享路径、可信原生重定向机制未证，属于真实前置，不能混为安装包缺失。不得改共享ini/HOME/APPDATA或猜参数；QQ安装包暂保留。
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
