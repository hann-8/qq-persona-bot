# LAP-40 旧材料准备指令（已完成）

2026-10-25 11:18：以下材料准备任务已交付，QQ/local现也已存在，不再重复执行。本轮用户要求补日常启动入口，**当前下一轮请复制[DESKTOP_MEDIUM_START](DESKTOP_MEDIUM_START.md)**，按[DESKTOP_PLAN](DESKTOP_PLAN.md)实际落地脚本；下文仅为历史指令，不覆盖新合同。

返回[项目入口](../../../../PROGRESS.md) / [当前交接](HANDOFF.md) / [操作步骤](TRYOUT.md)。2026-10-25，Asia/Shanghai。

用户在新会话手工选择`gpt-6.1-sol/medium`后，可复制下文。当前会话不切换模型、不派代理。下一轮仍是LAP-40材料准备，不重复领取已经完成的最小接入代码实施；准备完后才由用户亲自或另行明确授权真实启动/登录/文字试用。

```text
接续LAP-40官方原版SnowLuma最小OneBot接入。本轮请实际补齐能够准备的环境和链路材料，先让最小文字链具备运行条件，不再只列环境缺项或规划完整功能。

工作根：E:/CodexWS/QQbot_Snowluma
分支：codex/lap-40-snowluma
接入代码检查点：89b7dfae0efcd1949fe8289aa76ed1492bdfd8ab；其后只读复核文档以当前Git日志为准。重新核对当前HEAD、远端和工作区，不用历史干净状态代替当前核对。

先读PROGRESS顶部、AGENTS、工作线HANDOFF顶部/TASKS的LAP-40行，再读LAP-40/HANDOFF.md、TRYOUT.md和本文件。只按实际缺口检索，不重读全部历史。登记本session、时间与文件归属，写后重读。不派子代理、不切换模型，不修改E:/CodexWS/QQbot原运行根或旧C根。

本次授权：在新根下载/解压官方材料、创建Python 3.12项目虚拟环境、安装AstrBot 4.29.0隔离工具环境、用官方init和配置类生成新根基础实例。严格按TRYOUT中的本根目录和命令执行，缺项可以补，不能把“不存在”再次只交给我自行处理。可做本地包导入/配置/容量核对，不启服务，不登录，不调用模型。

已核对的起点：C:/Users/yutha/.local/bin/uv.exe存在但不在PATH；Node/CodeBuddy锁定文件存在且headless摘要匹配，不重新安装或升级CLI，不更改账号/站点/额度来源，不读取WorkBuddy或日常QQ密码/登录资料。新根Python、AstrBot环境/实例、官方Snow完整包、专用QQ、本机local/token仍须重新查存在性后准备。

按顺序完成：
1. 用本根uv.lock准备.venv；用新根UV_TOOL_DIR/UV_TOOL_BIN_DIR安装AstrBot 4.29.0及项目所需yaml/markdown_it依赖；Python与缓存目录也定向新根，不改全局PATH。不得改锁、静默升级版本或改用其他后端。
2. 在runtime/astrbot执行不启动服务的官方init，确认.astrbot、data/plugins和cmd_config.json齐备；按TRYOUT通过官方配置类生成基础配置并绑定dashboard回环6185。已有材料先保留并核对归属，不覆盖。初始密码和日志只留忽略目录，不打印或提交。
3. 下载官方v2.1.1 Windows x64完整包，核对官方asset摘要，完整展开到runtime/snowluma/v2.1.1，不用私有产物、不构建Snow、不运行launcher。下载腾讯官方QQ安装材料；仅在能保证只写新根且不自动启动QQ时完成专用安装，否则完成其他材料并给我精确的手工安装位置。不要猜静默参数、复制旧patched QQ或触碰日常QQ安装。
4. 我提供或手工放入新根当前业务配置后，才准备本根local；保留账号/授权群/管理员、既有blocked_users、mentions/free、模型/推理/预算/超时/输出和功能开关，只显式选择provider=snowluma、私聊维持false。缺这些值时列最小待提供项，同时继续1—3。不从旧根自动读取/迁移，不把模板默认当成我现用值。已有local/persona不覆盖；config/persona.md全程原样保留。
5. 若本根secrets/local-tokens.json缺失，本次允许在进程内生成三个独立随机token（onebot_inbound/onebot_upstream/model_gateway，各至少32字符），仅写本根忽略文件、不回显；已有文件原样保留。不得生成旧Snow控制密钥/proof或登录凭据。
6. 在实际业务值齐备后做config_files.py check及一次零模型人设容量核对。当前人设19,256 UTF-8字节，新装模板16,384输入预算确定装不下；优先保留我现用预算，未提供或仍不足就报告字节差额和参数选项，由我决定，不删人设、不静默调参。check不读token，另在内存核对三个键/长度/互异，只报告通过或缺项。

本次不授权：manage start/stop、AstrBot run、QQ/Snow启动或接入进程、登录/扫码、CLI认证/真实生成、SSH、群消息或自动试用。全部材料齐备也停止并交接；下一轮真实start-text一旦接通可能按保留的free规则消费模型并群答，不能只按“启动服务”授权后擅自开放。没有必要接入代码缺陷时不新增代码/测试任务。

唯一链路：官方原版Snow现成OneBot → 既有gate/AstrBot/router → gateway/CodeBuddy CLI。账号屏蔽由我在QQ客户端拉黑；旧私有路线整体取代，B/C停止，A4代码/产物/证据原样保留、不复核不重跑不修改。不增资格/proof/probe、零日志/存储、原生数据证明、自动恢复、72h/7天或完整旧功能前置。只有实际必须改Snow内部，才交具体阻断及已尝试的外部解决结果给我决定。

准备结束给出：已实际准备的位置与结果、仍需我提供/手工保留的配置或QQ安装步骤、未启动/未登录/未生成/未群发边界，以及TRYOUT中的准确start-text/status/stop与一次目标群真实@文字步骤。同步PROGRESS、工作线HANDOFF/TASKS和LAP-40交接；长期Git授权只提交本任务已检查文件，commit/push并核对远端SHA。runtime/local/secrets/persona不提交。完成材料准备后停止，不自动部署或推进其他功能。
```

材料齐备后的真实试用由[TRYOUT](TRYOUT.md)规定：用户明确允许新根项目启停及接通后按既有合同进行真实模型/群答，QQ/Snow正常启动与登录/扫码由用户亲自操作；在安静目标群时间窗发一次新真实@文字。保留free时其他新消息也可能触发，不能擅改模式或保证总调用恰好一次。若只允许通道，则另行授权start-channel，之后stop再start-text；通道单独验收不作首试硬前置。
