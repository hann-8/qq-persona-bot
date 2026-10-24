# LAP-40：E盘迁移根复核

返回[项目入口](../PROGRESS.md) / [总交接](../tracks/laptop-workbuddy/tasks/LAP-40/HANDOFF.md) / [执行计划](../tracks/laptop-workbuddy/tasks/LAP-40/WORKTREE_AND_USER_TEST_PLAN.md) / [A4交接](../tracks/laptop-workbuddy/tasks/LAP-40/STAGE3_A4_HANDOFF.md)。2026-10-24，Asia/Shanghai；根`LAP-40-max-E-worktree-user-test`。

## Git、目录和最新用户材料

根先读取实际旧工作根入口/AGENTS/MAX_START、精简交接和LAP-40行，未重读全部历史。旧实现分支Git干净、HEAD/远端均为8a431f1018a0b26f0dadb1c5979ac2fd7d88da8b；原运行分支为codex/lap-40-snowluma-trial/a798e62，未更改。目标目录经绝对路径/空目录/非reparse核验，使用`git worktree add -b codex/lap-40-snowluma E:/CodexWS/QQbot_Snowluma 8a431f1018a0b26f0dadb1c5979ac2fd7d88da8b`建立。

新根迁移/用户实测计划及共享入口7文件已commit/push `b890bd9210ddf5ba37ddf71b198c2af852c28705`，ls-remote一致，414个本地文档链接通过、diffcheck通过。开始额度5h余98%/周余38%；未消费reset credits。

用户指定Downloads两包再次只读核验：

| 材料 | 当前证据 |
| --- | --- |
| SnowLuma-v2.1.1-win-x64.zip | 42,694,125字节；SHA256 c739171f95c27706767e69ba36099707c222fcec639b46f4d59689997b527772，与固定版本一致 |
| QQ_9.9.36_260924_x64_01.exe | 330,446,512字节；SHA256 63255c70c7ff523e7eed7d52d9708ed7a77ea346ece6474c65dded406edb3155；Authenticode Valid，签名主体Tencent Technology (Shenzhen) Company Limited |
| 旧C官方包node.exe | 原位置执行`--version`得到v24.22.1；未运行Snow入口或加载native |

材料核验不等于安装/运行/原生范围通过。新根没有复制原官方包、ZIP、QQ安装文件或运行配置。

## 旧A4候选的根复核

从新E根cwd，用旧官方Node执行旧private的`--test check-a4-scoped.test.mjs`：5项通过、0失败，约455ms。这仅验证候选局部，不是完整控制/入站/pipe/native/ACK链。

额外stdin合成复现：fresh启动fake helper，5ms后`close()`，120ms后helper回包。结果`resolvedAfterClose=true / scopeCurrent=false / killCount=0 / elapsedMs=123`；broker最终revoked。该结果没有授予有效scope，但close没有立即取消自己创建的在途handle/等待，且返回了closed scope。已交medium在A4整体实现中修复并回归close/stop/超时的不可逆取消。所有process/事件均为fake，无真实监听或native动作。

另须把100ms短观测证明与持续逻辑操作许可分开，长图片操作最终提交前fresh；不能简单扩大短scope时限或复活已撤销操作。上述合同已写执行计划，未据5项通过接受整个A2。

## 归属与下个检查点

medium `/root/snowluma_a4` 于2026-10-24 22:40:31 +08:00领取新private/A4交接/专属报告；只串行执行，根独占共享3入口/总交接/MAX_START/计划/本报告。先迁纯文本闭包并报告摘要与junction核验，根审后才做完整A4改造；没有派发B/C。

当前仍未具备可启动实测资格：A2全链未过、B资格/probe代码未实现、G1真实原生数据机制未证。基础可启动条件通过即交用户实测，性能与72h/7天后验；生产总拒不变。0真实QQ/Snow启停、登录、模型、群消息、SSH或原运行配置修改。

## 私有迁移独立根审通过

根依据忽略a4-migration-evidence.json独立重新计算2901个源文件及对应目标文件的字节数/SHA256，检查UTF-8/NUL、相对路径唯一与根内解析；合计101173397字节，集合SHA256 a500823f5096cd560cb2edc54c0a4b3c5c4d76f81ae05276bc46f1e4a87e8a30。27个实际reparse点均分别核对源/目标指向与根内真实目录，不仅相信JSON布尔。全部通过，源字节不变。

operator-acceptance.local.json和旧pyc未复制；新根没有官方runtime或venv链接，private的源/证据仍被git check-ignore排除，diffcheck通过。迁移可接受；A4改造尚未发生，A2仍未通过。根完成本小检查点Git后再准medium串行继续独立A4 overlay，不能据迁移成功放开真实启动。

## 用户纠正后的当前边界（22:49）

用户明确Sol max当前只做详细规划，实施指令交用户另开Sol medium执行。根已interrupt自动续派代理，状态interrupted，无活动实施写入；本报告此前“根续派/等根核后继续”安排不再适用。本次后续只读盘点/文档/Git，没有继续改代码、构建或实施测试。

只读盘点2901迁移基线未改；忽略区另有a4-work 424文件、prepare-a4.py/build-a4.mjs及5个src/a4-*准备文件，没有a4-dist或A4执行证据。保留为未审准备稿，不删除、不算已实现/离线通过。公开业务代码未在本轮修改，原运行根未动。

详细规划与用户可复制指令已单独落盘，见LAP-40/STAGE3_A4_PLAN.md与SOL_MEDIUM_START.md；不自动resume、派代理或进入B/C。Git文档交付沿长期授权执行，不构成实施或部署。

## 规划收口验证（22:58）

本次13份归属Markdown的495个本地链接全部存在、LF/UTF-8与diffcheck通过；对8a431f1基线核对，新分支所有已跟踪差异均为Markdown。旧C工作根仍8a431f1、原E运行根仍a798e62，两者Git干净。A4实施代理状态interrupted，当前不续派；私有未审草稿保持原样，后续由用户另行指令medium先审。只提交本次规划/指令/边界纠正文档，未运行后续实现验证。
