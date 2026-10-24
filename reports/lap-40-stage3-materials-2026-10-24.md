# LAP-40 阶段3材料核验与接续规划

返回[任务交接](../tracks/laptop-workbuddy/tasks/LAP-40/HANDOFF.md) / [续作计划](../tracks/laptop-workbuddy/tasks/LAP-40/STAGE3_CONTINUATION_PLAN.md)。2026-10-24，Asia/Shanghai；session `LAP-40-max-realentry-next`，接手基线`f2bdb0c7096ea8f606e18f18f2926e5c8b680025`。

## 本次事实

用户明确提供Downloads内两个文件的完整路径，本次只读这些指定文件。先核验下载原件，再由用户手动解压；用户明确回复“接受，并且已经解压完成”，指本会话提问中的EULA和PRIVACY两份条款。没有代其点击接受、写consent.json或设置真实运行环境。

| 文件 | 字节数 | SHA256/版本证据 |
| --- | --- | --- |
| SnowLuma-v2.1.1-win-x64.zip | 42,694,125 | `c739171f95c27706767e69ba36099707c222fcec639b46f4d59689997b527772`，与固定计划完全一致 |
| QQ_9.9.36_260924_x64_01.exe | 330,446,512 | `63255c70c7ff523e7eed7d52d9708ed7a77ea346ece6474c65dded406edb3155`；Authenticode Valid/Tencent；FileVersion 9.9.36.53644、ProductVersion 9.9.36.53644-aff854e8 |

ZIP目录72项，无绝对/上级/反斜杠/冒号路径、大小写冲突或symlink条目。通过.NET ZipFile/Python zipfile在内存读取目录、package/EULA与选定成员，未写出任何组件。包manifest为`@snowluma/runtime`2.1.1，engines `^24.22.1 || >=26.12.1`；Node PE版本为24.22.1.0，此时未执行。

用户确认后12:43复核工作worktree的`runtime/snowluma/v2.1.1`，实际执行其中`node.exe --version`返回**v24.22.1**。这只验证Node，未运行Snow index/launcher、未dlopen/inject任何Snow组件。

| 原包成员 | 解压后与原ZIP相同的SHA256 |
| --- | --- |
| node.exe | `d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5` |
| index.mjs | `e23ed3d4aa7e01e7f45400a7ffe6b0c4b67bb6d011f776f2fd04b959510435e6` |
| EULA.md | `373c4f7c5d87da116fa4444ce45b3f41a0cf238ec4ee3f993a2123bfc945a5b6` |
| PRIVACY.md | `d36474445ce510e27e64fbe76609cc088c75b1dfa3dfb6c257241598749f08fd` |
| native/snowluma-win32-x64.dll | `986312643ec533f57de31681218739853a8fdc259db8d5a5897212b5a133f8a8` |
| native/snowluma-win32-x64.node | `6d8aa2479d774f333e76cc158ff09a5dc95e8b69074c73ea71865d7d7122b806` |
| native/websocket-win32-x64.node | `6e71a14b1d28a6259bc1fb52dea2bdf13f100b326c04b14132f7a53b64fe9383` |
| native/ffmpeg/ffmpegAddon.win32.x64.node | `80a4dfbb170f093f4a64fe241b8583fb630c58219100cad7a3cad798f71864db` |
| native/sqlite/prebuilds/win32-x64/@appthreat+sqlite3.node | `e8898fd92aebbecdc946c14e2a9f9c481946de3cbde1ebc3c647c02892640598` |

项目runtime内原ZIP、`runtime/qq-snowluma/QQ.exe`、`runtime/snowluma-private`、`state/qq-transport/proof.local.json`本次检查仍不存在。`git check-ignore`命中原版index，未进入public跟踪。原ZIP下载/解压通过不等于干净QQ、数据范围、私有构建或真实准入通过。

## 新增源码结论及续作范围

通过GitHub连接器只读固定提交源码，未保存上游源或native到public。官方存在两份同意的环境声明入口，私有早期bootstrap可保留此机制，仍需实现/执行核验；默认WebUI缺文档fail-open不可沿用为项目放行。Windows默认账号数据检测读共享ini/当前用户Documents，源码/合成Linux隔离测试都不能证明本机QQ隔离；没有读取本机这些路径、登录库或凭据。

`require_runtime`生产总拒和`capability-probe`共用总拒是实际项目代码缺项；v1静态proof仅hash检查。新增续作计划区分JS-only/私有接线、probe前置、DROP真实probe、生产资格、实时channel_ready，避免先有probe资格才能probe的循环。A0可先独立实施，B精确schema再根审，C真实前置仍缺；原1/2/4/5交付不重做。

核验过的固定源码包括core/vite配置、runtime-integrity、LICENSE、README、injector、HookManager、native-path、core入口、core/webui/consent、Windows数据paths和路径合成测试。两次猜测文件路径返回404后已用固定Git tree metadata定位真实路径，未对错误路径推断能力。未运行任何上游构建、安装脚本或真实native测试。

## 归属、验证与限制

12:38领取并写后重读TASKS/PROGRESS/工作线/任务HANDOFF；开始Git干净，HEAD与对应远端分支均为f2bdb0c。12:34账户300分钟used11%/剩89%，未触发<=5%阈值，未使用reset credit或购买。

本检查点只改本任务规划/报告/入口文档。实际命令类别：Get-Item、Get-FileHash、Get-AuthenticodeSignature、VersionInfo、ZipFile/zipfile内存目录与哈希、用户解压后的固定Node `--version`、限定Test-Path、git状态/分支/HEAD/ls-remote/ignore。初次PowerShell foreach直接接管道发生解析错误，未执行文件操作；改为赋值后管道，核验成功。

0agent原生下载/解压/复制部署、0QQ安装/注入/启停/登录/扫码、0Snow运行/真实端口/模型/群消息/SSH；原运行目录未修改。用户手工解压与agent只读核验分别记录，不称为已切换；长期/免扫码及全部旧差额保留。检查点9份Markdown/404个本地链接及围栏通过，git diff --check通过；12:48额度300分钟used21%/剩79%。只交付本任务9份文档，Git提交/推送后核对对应分支SHA，实际回执以Git及后续HANDOFF记录为准。
