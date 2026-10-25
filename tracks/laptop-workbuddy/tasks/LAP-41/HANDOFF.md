# LAP-41：SnowLuma主线工作区整理与bot使用对照

返回[项目入口](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [任务台账](../../TASKS.md)。继承本根AGENTS及用户最新指令。

## 当前任务

**整理与使用对照已完成，QQ以后以本SnowLuma工作根为主线。** 日常入口/进度已重写，旧入口归档、确定的无用缓存/临时网页/退役提示删除；运行代码和数据保留。详细实际删除/保留/审批限制及回滚见[清单](CLEANUP.md)，用户比较见[bot使用对照](../../../../docs/BOT_USAGE_COMPARISON.md)。

session `LAP-41-snow-mainline-cleanup-comparison`，2026-10-25 12:03（Asia/Shanghai）登记；起点本地/远端`3d3361eaecae1e342bb05412c6af3ccdf6b4417b`、工作区干净。用户要求整理SnowLuma工作区、删除确认无用内容，此后QQ以SnowLuma为主线；整理重点是旧NapCat bot与当前Snow bot的实际使用差异。

## 范围与执行顺序

先只读盘点与配置/业务源码对照，再将精确删除/保留清单落到CLEANUP；保存旧入口文档快照并压缩当前入口；只删除清单中可重建缓存、失败下载网页快照与确认已退役的提示cmd；修复必要引用，验证后按长期授权只提交本任务文件并推送。

保留现有本机配置/token/persona、安装环境、官方包、专用QQ、AstrBot/state/logs/群历史/图库和A4代码/产物/证据。不修改运行代码或原NapCat/旧C根，不启停、登录/模型/群/SSH，不派代理或切模型。NapCat仅留历史/兼容参考，不删除仍被共用代码或测试引用的模块。模型与触发等业务选择不随主线整理自动改变。

## 已只读确认

两边磁盘配置与最近启动快照的非秘密业务投影一致：CodeBuddy/deepseek-v4.1-flash/low，free，adaptive最多3条、闲聊80字，16轮历史、1秒同人冷却、输入预算30000/开销2048/输出预留2048、90秒；web/memes打开，attention/vision/members/memory/B站字幕关闭，私聊关闭。人设19,256字节且SHA256相同；9个共用业务源文件一致，router差异是Snow状态/连接适配。

实际资产差额：旧NapCat有7条登记表情；Snow新根无表情登记文件、0条，虽开关为true也不能直接发送旧图库。两个根的数据目录各自独立，不会自动迁移旧会话；本轮不迁移。Snow官方目标账号保留默认开启的#sl状态命令，这是官方额外答复路径，不能用其回复证明项目AI链路成功；不在本轮修改它。

## 验证与后续

uv自带cache clean返回0，报告删除38,269文件、626.1MiB；5份临时网页快照76,716字节删除，根退役自启提示cmd及属性行删除。四份旧入口说明归档，README/PROGRESS/本工作线交接/目录说明压缩并以Snow主线组织；AGENTS、使用说明、TASKS同步。生产Python/插件/测试、旧任务/报告、A4和其他工作根保留。

自动审批拒绝最初批量删除脚本及后续固定路径字节码目录删除，只返回blocked by policy、无细化原因。批量脚本未执行，后用显式cache-dir的uv命令和精确文本文件补丁完成获准项；字节码3目录59文件1,311,121字节仍保留，没有换其他手段强删。

25份保护文件（两根配置/persona/旧图库登记、本根token/账号连接/uv.lock/关键程序）前后SHA256相同；生产scripts/src/plugins/tests/adapters/config/uv.lock与起点无Git差异。Markdown本地链接/围栏及git diff --check核对，不运行代码测试、A4、模型/群收发或bot启停。未通过比较自动迁移历史/图库或切换功能。

最终文档核对14份Markdown、505个本地链接及围栏通过；归档新头部的混合换行已规范为LF，暂存diff --check通过。五个日常启动/查看/关闭/Snow辅助cmd与基线无差异。退役开机提示是本轮唯一删除的根cmd。

本任务文件：根README/PROGRESS/AGENTS/目录说明/使用说明、工作线HANDOFF/TASKS、本HANDOFF/CLEANUP、docs/BOT_USAGE_COMPARISON、4份历史快照、退役开机cmd删除与gitattributes单行调整。只提交归属文件，按长期授权commit/push并核对远端；交付后停止/释放归属。下一步正常使用Snow，其他功能/图库或历史迁移等用户后续明确指令。
