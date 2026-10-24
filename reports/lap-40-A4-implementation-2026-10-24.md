# LAP-40 A4 实施与离线证据

返回[项目入口](../PROGRESS.md) / [A4交接](../tracks/laptop-workbuddy/tasks/LAP-40/STAGE3_A4_HANDOFF.md)。session `LAP-40-A4-medium-implementation`；唯一工作根 E:/CodexWS/QQbot_Snowluma。

## 检查点一：异步 helper 生命周期

2026-10-24，已领取并写后重读。HEAD/远端起点 74b3c777b78ab170ce21cf07aa94a3b80996a756，分支 codex/lap-40-snowluma；5小时额度剩73%。逐项核对迁移2901文本摘要和27 junction，零变化。原C工作根、原E运行根只读保留。

未审草稿确认为部分prepare输出：仍未接异步channel，且native/Highway等编辑未执行。原稿完整保存在忽略private/a4-draft-archive，未直接执行原prepare/build。

新增私有 src/a4-channel.mjs、check-a4-channel.test.mjs：异步初始化/封闭schema和实际spawn PID/parent/created核验，ALS逻辑许可与100ms短scope分开；并发1/队列16/每helper最多2秒且受操作deadline限制，控制优先；取消立即撤销等待并仅kill自身child handle，退出未知封闭broker且禁止再spawn。同步current只读scope，不递归helper；登记图像读取保留原12MiB/8MiB边界。

命令（cwd新根）：原C工作根 runtime/snowluma/v2.1.1/node.exe --test runtime/snowluma-private/check-a4-channel.test.mjs。8/8通过：120ms helper不阻塞、100ms过期后在持续许可内刷新、close在途取消/迟到、hang期限、并发/控制优先、假PID/epoch/超限/回拨。只用合成child，无真实spawn/监听/native/QQ/模型/群/SSH。

本检查点只证明上述组件；控制/入站/RPC/最终栅栏和完整A4矩阵尚待实施。production qualification仍closed，不进入B/C，不把旧A3分项计为A4通过。

## 检查点二：全链接线与定向执行

控制HTTP壳改为从收到请求计3秒（含body/排队/fresh/handler/ACK）；沿用public原HMAC/seq/nonce/ownerLease，未修改public业务代码。异步初始化仍由正式Python loader投影和独立秘密产生，生产入口继续拒绝。watcher/串行HookSession操作独立取得短scope；操作取消有同步清理钩子，事件pipeline异步转换纳入操作寿命。

原包在上游完整协议处理前进入16条/256KiB/单包64KiB队列，排队中项也计费。去除HookSession的准入前正文复制，队列仅保留一份固定快照；私有2MiB预算扣除队列256KiB和发送索引64KiB。断连/登录代际切换撤销旧队列及许可。受认证gate保留固定动作/16 pending；登记图像改异步读取。最终注入、精确PID pipe connect、实际writeControl取出队列、Highway connect/write均fresh后同turn复核；messageSubmitted只在实际socket.write前登记，成功/unknown ACK单次尝试。

阶段验证：实际316模块私有装配；慢120ms helper的合法bind约1.2秒成功，窗口内11次helper启动（包含并行gate工作），不是拒绝及时。实际类已覆盖允许入站、文字/群别名、授权群元数据、受限收藏、登记图像、unknown/前拒绝、stop/epoch/socket/account/disconnect、scope过期队列恢复与pipe socket替换。原包队列压力和RPC第17条拒绝通过；channel/control当前15项通过；实际gate/CQHTTP/AstrBot/TaskStore/Router/MemoryStore四种ACK结果13项通过，partial只保留确认前缀，未确认部分不晋升、不重发。

上述为中间定向结果；最终固定源码、慢图像/压力矩阵和完整摘要另见下节。曾发现慢图像fake响应早于读监听而丢帧，已使合成socket模拟真实缓冲顺序；不把该测试夹具现象当作真实QQ故障。原件/旧A0-A3与运行环境继续保留。

## 最终执行与验收状态

2026-10-24 23:34（Asia/Shanghai），A4代码已实现、下表合成验证通过，**尚待Sol max独立复核**。不自动派代理或切换模型，不进入B/C。公开业务代码零修改；全部上游改动/构建产物/测试及依赖仅在本机忽略private，Git只交原创报告及交接。原C与原E根Git仍干净，本机local/persona未改。

| 验证 | 最终结果 |
| --- | --- |
| 最终执行入口 | check-a4-final.py：21个命令全部通过；逐命令argv/退出码/耗时保存在a4-final-evidence.json |
| 语法与构建 | 316模块闭包构建，321个ESM纯语法解析通过（不执行模块）；固定Node v24.22.1 / TypeScript 6.0.2 |
| channel/control | 15项；close在途kill/迟到、hang/未知禁止再spawn、控制优先、回拨/伪PID/epoch/超限、body从收到起3秒、非法stop零副作用、取消后零提交、长许可/retained转换均过 |
| 实际类场景 | 15场景各30项，共用用例很多，不能累加为独立用例总数；load/load-slow各34项、pipe-connect31项。stop/slow/put/put-fence/put-slow/load/load-slow/epoch/socket/account/disconnect/inject/queue-expiry/pipe-swap/pipe-connect均过 |
| 慢120ms合法bind | slow 1336ms，bind响应窗口实际启动12次helper；put-slow/load-slow 1334ms/12次，全部200成功；初始化另计，不是拒绝及时 |
| 新操作health与发送 | HTTP health在bind结束后超过100ms仍200，slow 121ms/1次helper；文字及群别名成功。scope过期的native排队动作重新fresh后成功，旧scope不续期 |
| 高频原包/RPC | 实测队列峰值16条/262144字节；超限不进完整转换，pending上限16，第17条1403。load-slow压力中HTTP health 238ms，未超过3秒 |
| 长图像 | put-slow的helper120ms、socket写callback150ms，2次Highway write和最终消息成功；put-fence第一write后撤销，零后续body/最终消息。未引入上传重试 |
| 实际提交点 | writeControl排队中stop/epoch/gate socket/账号/断连/pipe socket替换阻断；native提交后仅一次unknown、不重发；注入实际函数配假addon调用1次（150ms跨scope），实际connectSocket仅精确登记PID pipe一次，任意pipe/其他PID拒绝 |
| 正式Python提供器 | 10类合成owner/父PID/创建时间/路径/stop/快照/精确pipe/gate；额外核scope投影。WaitNamedPipe/native均由fake替代 |
| 框架ACK | 实际gate/CQHTTP/AstrBot Event.send/TaskStore/Router/MemoryStore，前拒绝/成功/unknown/partial四结果13项；pending收束、重复delivery不重发。unknown无assistant/记忆晋升，partial仅已ACK前缀进历史，未确认部分无晋升 |
| public兼容 | 原control/policy14项通过，HMAC/seq/nonce/3秒/停言及业务合同未改 |
| 生产入口 | 退出1、A4_PRODUCTION_QUALIFICATION_REQUIRED；没有参数/JSON布尔绕过 |
| 原件/迁移 | 2901文本、27旧内部junction、官方71文件及原ZIP摘要全部不变；private源/产物无native/EXE/ZIP/pyc |

bind窗口的12次包含实际装配的并行gate/owner工作。最终slow全场景98次helper，put-slow105次、load-slow158次；数量未隐藏。每次kind/boundary/耗时在各a4-runtime-evidence-*.json的helperLifecycle.trace，bindTrace单列；不把全场景次数混称单次bind。收束仅证明合成进程handle；真实helper退出覆盖/31B仍未证。

## 可复现命令、源码和依赖摘要

所有命令cwd均为E:/CodexWS/QQbot_Snowluma，Python设置PYTHONDONTWRITEBYTECODE=1、PYTHONPATH指新根src；只读借原E venv与原C官方Node，不复制运行态。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='E:/CodexWS/QQbot_Snowluma/src'
& 'E:/CodexWS/QQbot/.venv/Scripts/python.exe' -B runtime/snowluma-private/prepare-a4-reviewed.py --check
& 'C:/Users/yutha/.codex/worktrees/lap-40-snowluma-impl/QQbot/runtime/snowluma/v2.1.1/node.exe' runtime/snowluma-private/build-a4.mjs
& 'E:/CodexWS/QQbot/.venv/Scripts/python.exe' -B runtime/snowluma-private/check-a4-final.py
& 'E:/CodexWS/QQbot/.venv/Scripts/python.exe' -B runtime/snowluma-private/audit-a4.py
```

当前424源文件中13个A4 overlay修改，其余A3文本原样；私有a4-source-manifest.json逐项列base/source/overlay SHA256，a4-reviewed-overlay保留受审源。prepare-a4-reviewed.py --check只核验，--prepare仅在a4-work不存在时创建，拒绝覆盖现存树。早期prepare-a4.py/finish-a4.py/make-a4-check.py为过程稿，**不再用于重建或覆写**；原a4-draft-archive保留未审历史。build-a4只写A4输出及A4内部依赖junction，既有toolchain只读复用。

| 集合 | SHA256 |
| --- | --- |
| 424源文件规范JSON集合 | f86489260a2f5d43eae9790e03909152ee353d3db2ae1d6b7833d0e4a24c9888 |
| A4产物集合 | fe5cea20d9a1a8709ae7079cd7fa362324e52a10581c0fd34603f5493e7249e1 |
| A4原创运行/检查脚本集合 | 64f45eb4aa47b1a17cd933922f3b92a53b402d12c008f2cb2bda8d1a9dfc6722 |
| TypeScript工具锁 | a7ef81e7ce270aa6c5e1ee81089cf0b580e5b626b5374eab062ecc84553430eb |
| 固定上游依赖锁 | 5d17a2c1ef0d8ec308bb9c479c6465fb9c1ba2b04db147bafb472ef0a3c427ee |

完整输入/产物/外部builtin列表在a4-build-evidence.json，所有迁移原件与脚本摘要在a4-integrity-evidence.json；没有新增第三方依赖、联网安装或package生命周期。源集合核对不代替语义审阅。公开报告不附上游源/patch/bundle，不包含凭据或原始私密消息。

## 交Sol max复核与剩余边界

见[Sol max复核入口](../tracks/laptop-workbuddy/tasks/LAP-40/SOL_MAX_REVIEW_START.md)。优先复核操作引用/取消与helper未知退出、bind生命周期/长期ownerLease、早期队列预算/代际、实际writeControl/Highway注入最后栅栏、单次ACK及未确认历史/记忆。无需重读全部历史；只在发现差额时扩大检索。

A4离线实现交付不等于A2已获max接受，不等于B资格/G1真实机制、原生保护/完整退出、真实pipe/数据范围/QQ收发或性能通过；生产资格继续closed。未安装/链接官方运行态、启停QQ/Snow、扫码、真实监听、调用模型、发群消息或SSH；72h/7天未开始。旧18/24/28/29/31B及人设预算失败差额保留。回滚本阶段只停止使用独立A4候选，不改A3或原运行根；不执行真实部署回滚。

Git检查点：b5b0bc4（channel生命周期）、806c981（全链接线）；最终提交号由交付消息和Git记录给出。所有public文件仅本任务归属，private材料必须留在本机新根，不能归档/清理工作根导致忽略材料丢失。
