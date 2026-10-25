# LAP-42：Snow既有功能整合与B站退役

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [AGENTS](../../../../AGENTS.md)。[详细PLAN](PLAN.md) / [完整medium指令](MEDIUM_START.md)。

## 当前状态

**整合详规完成，待用户下一轮选择medium实际执行；本轮未实施或启用。** 用户最新范围覆盖此前只展开一项的安排：长期群记忆、关注、成员增强均可交medium落地，图片识别也尝试，B站字幕撤下。用户明确当前deepseek-v4.1-flash支持视觉，按当前CodeBuddy路线实施，不换模型/后端/账号/额度。实际CLI图片传输与QQ闭环仍需验证。

## 领取和归属

session `LAP-42-snow-feature-rollout-plan`，2026-10-25 16:24开始只读复核，16:32（Asia/Shanghai）登记TASKS并重读。开始HEAD/实时远端均为`9bb1b58270dbcaa3c5e40c53f804d5e50c54449b`，分支`codex/lap-40-snowluma`，无非忽略差异。

42已查空闲；它负责原27/28/29/30在Snow下的组合适配、统一配置加载和06退役，旧26/38未覆盖该组合发布。不是四项从零重做；旧各任务历史/真实差额保留，medium只领42，不同时重领旧任务。

本规划仅归属7份Markdown：PROGRESS、工作线HANDOFF/TASKS、本HANDOFF、PLAN、MEDIUM_START、BOT_USAGE_COMPARISON。不改代码/local/persona/图库/历史/秘密，不安装、启停、登录/扫码、真实模型/QQ/群/SSH；不改Snow/QQ/CLI内部，不访问旧C/旧NapCat运行数据，不读验A4，不派代理或切模型。20项本机配置/persona/图库/pending及记忆key/目录/context token存在状态纳入保护。

## 核对结论

- 记忆30与关注27已有离线实现，当前关闭；新根无记忆key/目录，不迁旧聊天或HMAC key。
- 成员29硬编码生产暂停，不能只改开关。官方Snow v2.1.1只读强刷路径可供项目外部适配：get_group_info(no_cache=true)等待FetchGroupList网络结果、失败不回旧缓存；名单no_cache=true走force。1..49、双TTL与受控@门槛保留。
- 图片获取/规范化/CLI原生图片封套/原群ACK骨架已存在，GIF目前首帧。用户确认模型支持；重点验证真实像素是否进入当前CLI并由同次模型返回。生产视觉记录表为空不等于模型不支持；必要预算/质量差额仍须诚实保留。
- 旧真实intake管理路径固定拉NapCat，Snow采样要在项目外部manage/observer适配，不能照搬运行。
- B站必须从运行服务/配置入口/能力提示撤下，旧false节兼容；仅再写一遍false不算退役。
- 21交接仍为7图/7条pending准备完成，active不存在。用户“图片完成”不扩写为真实发图验收；42不动其pending，也不将这个尾项作为前置。

## 下一轮和交付边界

执行顺序：字幕退役与记忆/关注→成员外部适配→当前DeepSeek图片路径/受控尝试→组合加载与报告。某项缺口不拖住独立部分。官方Snow/QQ/CLI及高度封装内部保持原样。

新medium复制指令在用户下一轮发送时，才授予其列明的外部代码/本机开关、独立key/token、至多两次受管加载周期及有条件的受控观察；当前规划没有执行授权。普通free恢复后自然流量可能调用模型并答群，不能误报0。人工群测试不由agent代发；视觉IQ最多6次、群闭环最多2次且前置/对象明确。

文档完成检查与Git交付后释放归属并停止。逐项保留代码/离线/配置/加载/真实差别，最终SHA和保留差异见交付回执，不自引用提交号。

16:52检查点：7份Markdown、231个本地链接、4个围栏行检查通过，git diff --check通过；20项本机配置/persona/图库/pending/记忆与context存在状态前后相同。未运行代码测试，真实模型/QQ/启停操作0。仅7份已登记文档交付；当前DeepSeek视觉支持的用户补充已同步到入口/计划/medium指令。
