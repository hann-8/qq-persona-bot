# LAP-41 工作区清理清单

返回[交接](HANDOFF.md) / [项目入口](../../../../PROGRESS.md)。2026-10-25，Asia/Shanghai。

## 授权与边界

用户授权整理`E:/CodexWS/QQbot_Snowluma`并删除确认无用内容，今后QQ以SnowLuma为主线。本次是工作区维护与使用对照，不调整bot聊天行为。起点`3d3361eaecae1e342bb05412c6af3ccdf6b4417b`、工作区干净，TASKS已先登记并重读。

## 执行前确认的删除清单

| 精确目标（均相对本根） | 理由与保护条件 |
| --- | --- |
| `cache/uv` | 38,269文件、656,544,555字节的安装缓存，可重建；Python本体和两个已安装环境保留。已核对环境的重解析条目不指向此缓存，使用uv自身的cache clean并显式指定该绝对缓存目录 |
| `scripts/__pycache__`、`src/qqbot_gateway/__pycache__`、`tests/__pycache__`、`plugins/qq_router/__pycache__` | 仅清理已生成的pyc/pyo；不删除源码或安装环境内的字节码。存在未知文件则保留。不会为清缓存重启bot |
| `runtime/downloads/qq-index.local.html`、`qq-page.local.html`、`qq-windows-config-refresh.local.js`、`qq-windows-config.local.js`、`snow-assets.local.html` | 已结束材料准备阶段的临时网页/索引快照；当前QQ已安装，官方Snow原包另行保留。不是登录数据或A4产物 |
| 根`开机启动机器人.cmd`及仅该文件的gitattributes条目 | 该cmd现仅打印“开机自启方案已停用”，不启动bot；本轮核对项目Startup快捷方式和本根注册台账均不存在。日常启动/查看/关闭不调用此文件；旧autostart工具/测试中的目标字符串保留作历史兼容，不支持本根开机自启 |

每个删除目标先解析为本根内的确定绝对路径，检查自身及父链不经过junction/symlink；仅用同一PowerShell/uv流程操作，不跨shell拼接删除命令，不按进程名结束程序。不删除任何不在表内的目录。缓存如有占用或失败，保留并如实记录，不停机强删。

## 归档而不丢失

将清理前README、PROGRESS、工作线HANDOFF、项目目录与日志说明保存到`docs/archive/pre-snow-mainline-2026-10-25/`；只为保持可读性重写快照的相对链接并标明历史日期/来源。随后以Snow主线重写四个当前入口，TASKS和所有旧任务交接/报告继续保留。旧计划不能再作为当前首试待办。

## 保留项

- `.git`、`uv.lock`、生产源码/插件/测试及仍被导入的NapCat兼容模块；不作本轮代码裁剪。
- `.venv`、`runtime/python`、AstrBot工具/实例、官方Snow/专用QQ、官方Snow原始zip及AstrBot版本约束/已安装列表。
- `config/local`、persona、token/其他秘密、图库、AstrBot会话库、state任务/清理台账、logs及QQ/Snow登录数据；不迁移、不清零。
- `adapters/snowluma`、`runtime/snowluma-private`及A4报告/证据原样保留，不复核或重跑。旧B/C仍停止。
- 原`E:/CodexWS/QQbot`与旧C工作根不修改。本轮只读取原NapCat非秘密业务设置、源码及图库登记数量，用于比较。

## 执行结果与验证

已完成清单中获准的清理与入口整理，未执行真实bot操作：

| 项目 | 实际结果 |
| --- | --- |
| uv安装缓存 | 固定绝对cache-dir执行`uv cache clean`，返回0；工具报告Removed 38269 files (626.1MiB)，清理后cache/uv目录不存在 |
| 临时网页/索引快照 | 精确清单5文件已逐文件删除，共76,716字节；保留Snow原zip及两份AstrBot版本材料 |
| 字节码缓存 | **保留**3个现存目录、59文件、1,311,121字节。最初批量脚本及后续固定literal目录删除均被自动审批拒绝，工具只给blocked by policy、无细化理由；拒绝动作未执行，未改用其他方式强删。plugins对应目录原本不存在 |
| 退役提示入口 | 根开机启动cmd及其单条gitattributes属性已移除；未安装/移除系统Startup链接，检查时该链接与本根注册台账均不存在 |
| 历史入口 | 四份旧文档已保存并修正相对链接，当前README/PROGRESS/工作线HANDOFF/目录说明已压缩为Snow主线入口；旧任务/报告和A4保留 |
| 运行保护 | 两根配置/persona、旧表情登记、新根token/官方账号连接/uv.lock和关键运行程序共25份文件清理前后SHA256相同；原生产scripts/src/plugins/tests/adapters/config/uv.lock无Git差异 |

缓存统计是工具报告/逻辑字节量，不等同于实际释放磁盘空间：uv可能使用硬链接。少量字节码缓存保留不作为未完成的bot功能任务，日常Python仍可自行重建它们。

归档位置：[旧README](../../../../docs/archive/pre-snow-mainline-2026-10-25/README.md)、[旧PROGRESS](../../../../docs/archive/pre-snow-mainline-2026-10-25/PROGRESS.md)、[旧工作线交接](../../../../docs/archive/pre-snow-mainline-2026-10-25/LAPTOP_HANDOFF.md)、[旧目录说明](../../../../docs/archive/pre-snow-mainline-2026-10-25/DIRECTORIES.md)。来源为整理前3d3361e工作区；原文件内容保留在快照，链接仅作位置调整。任务表和旧任务HANDOFF仍在原路径。

验证：仅本地链接/围栏、git diff --check、25份保护文件摘要和归属差异检查；未跑代码测试、A4、模型、群收发或启停。只提交本任务维护/文档改动；Git提交号、push后的远端SHA与本机差异在最终交付和Git日志中核对。

回滚：旧说明先读归档；退役提示cmd可从本轮父提交只恢复该文件及其属性行。安装缓存/网页快照可以重新取得，不恢复或覆盖运行配置、状态库、登录材料。没有必要回滚运行代码或启停服务。
