# LAP-06 轻量B站字幕总结

返回[PROGRESS](../../../../PROGRESS.md) / [TASKS](../../TASKS.md) / [工作线](../../HANDOFF.md) / [合同](../LAP-36/WEB_VIDEO_PLAN.md) / [报告](../../../../reports/lap-06-2026-10-22.md)。继承根AGENTS；本任务不启用07。

## 当前状态

2026-10-22（Asia/Shanghai）：代码/模板已实现、离线通过，未部署/真实验收。session `LAP-06-light-subtitles`，20:37:21首次领取，起点ed26d9e3ed2c79c096e376269aa8a02c0700953e、工作区干净；本session唯一归属写入者，未覆盖其他session/用户修改。只本任务，不操作真实实例。

当前文字BV/av/长短链、单视频/P/cid、单轨语言/人工优先、固定API/CDN用途和Cookie隔离、6次HTTP/两次短链跳转/15秒/1MiB/20分钟/10000行均已实现。复用18安全传输和现有v2预算/一次生成/ReplyPlan/最终哑巴栅栏/ACK；字幕独立启用即可使用v2，不要求图片/记忆/成员开启。六时间区完整窗口裁选、完整请求拒超限、最终预算重选、封闭字幕manifest/程序来源与真实范围落地。缓存仅RAM编码材料，scope/P/语言/认证修订/网络配置隔离、TTL/LRU、共享取消；无答案缓存/额外模型/下载器/ASR。

默认bilibili.enabled=false、trigger=explicit、auth_mode=none。none不读文件；显式sessdata才读固定忽略路径，Cookie仅固定API，绝不发短链/CDN/模型。未读/写真实凭据，未改真实local/人设/28能力表，未热加载或启用。新配置/同行中文旁注/五文件映射/快照版本/兼容审阅导出与README同步，正常启动后才生效。

## 文件归属与来源

新增bilibili_policy.py、bilibili_subtitles.py、vendor/bilibili_fields.py及Unlicense/来源哈希；test_bilibili.py、verify_lap06.py、verify_lap06_unit.py、verify_lap06_regression.py、measure_lap06.py、报告与5份JSON。必要接点public_http/web_retrieval/web_policy/evidence_selection、config/config_files/config_comments/persona/model_gateway、qq_router/main及configure_astrbot；两个配置示例、README/配置说明、ACCEPTANCE仅增量说明、TASKS/PROGRESS/工作线和本交接。最终文件以本任务提交diff为准。

固定yt-dlp提交897341241f2bfb2439fe0367f4c7c9ccd29a3828，仅复用字幕端点/need_login_subtitle/subtitle.subtitles/lan/subtitle_url最小字段，未安装包/插件或复用播放器。源码与许可各一次公开读取、哈希核验，原文件只留忽略state；[来源/修改记录](../../../../src/qqbot_gateway/vendor/YT_DLP_SOURCE.md)。0新增运行依赖/常驻worker。

## 验证及最后检查点

- `.venv/Scripts/python.exe -X utf8 scripts/verify_lap06_unit.py`：273受影响单元通过/26.297秒，[JSON](../../../../reports/lap-06-unit.json)。最后审阅新增旧eligible视频反例并收紧manifest URL类型/字幕证明检查，`-m unittest tests.test_bilibili tests.test_lap18_body.EvidenceTests -q`末次25专项（20字幕+5网页材料）通过/0.557秒；不累加次数。日志忽略state/lap06-unit-final.log、lap06-final-manifest.log。
- 框架Python运行`scripts/verify_lap06.py`：两实际runner底层替身+实际AstrBot/provider/build_main_agent/run_agent，single/adaptive×mentions/free共8组合88例，末次16.422秒，[JSON](../../../../reports/lap-06-framework-offline.json)。包括bilibili独立v2、原生Ollama wire预算、cache独立生成、正文/标题矛盾输入、来源/范围/manifest/ACK与unknown持久保留。全自造，0真实模型/QQ。
- 同Python运行`scripts/verify_lap06_regression.py`：8组合118例/23.547秒，[JSON](../../../../reports/lap-06-regression-offline.json)；bilibili=false的图片+正文worker+记忆+表情，以及成员+哑巴+web兼容。未冒充同一事件真实字幕+图片验收。
- `.venv/Scripts/python.exe -X utf8 scripts/measure_lap06.py`：[资源JSON](../../../../reports/lap-06-resources.json)。10000行691573字节JSON解析规范化0.180秒、选择0.001秒、最终材料4159字节，RAM cache编码条109669字节、trace峰值9.31MB；非硬RSS上界。uv lock --check（29包）/compileall/diff、文档本地链接和归属核对通过。

失败历史与限制：误列不存在test_persona模块、旧test_lap28跨模块import路径失败已纠正固定入口；一次既有test_lap29随机ref恰含444导致子串断言误报，[原结果](../../../../reports/lap-06-unit-prior.json)保留，定向一次及后续全影响集通过，未改其代码/测试。资源对比发现cache前tuple/后list不同，规范材料已固定list且复验一致。末次通过不抹掉这些记录；旧正文worker临时目录ResourceWarning单列在报告。

## 真实证据与剩余

anonymous未验；auth未验；真实字幕正文材料未验；真实生成/群ACK未验。0 B站业务读取/真实模型/SSH/QQ/登录/真实bot启停/本机配置凭据修改。只有公开GitHub源/许可读取及Git网络交付；未指定允许视频样本，未额外探测网络。18仍network_unverified、SEARCH_QUALITY_PASSED=false。

原V矩阵适用字幕项仅有离线证据；07 ASR/V04、V06画面、完整V11多段归纳合并、V13/18音频/多段与O10完整观察及旧真人差额全部保留，完整第一版未完成。轻量节选不称全片；标题矛盾用例没有真实模型质量结论。24登录、28真实路径/可信上界、31B与18搜索旧差额不变。

下一步：先由操作者解决合法公网/TLS并明确允许样本/认证意愿和零模型材料批次；失败只记录不绕过/重试。真实生成/群ACK另需明确样本、所选后端/模型、总次数和唯一负责人。本session完成独立代码/离线交付后等待新指令，不自动启用或推进07。

回滚：操作者正常停止并保留pending/unknown/清理账，显式关闭bilibili或恢复配对旧代码/审阅兼容配置后正常启动；不删除历史/记忆/图库/凭据，不改全局网络。

Git交付：37份归属文件内容提交`9ae6688e466aa21bc7f0eb5b9de61358d90fda9e`已推送origin/main；git rev-parse HEAD与git ls-remote origin refs/heads/main完整SHA一致，内容检查点git status --short为空。408个本地Markdown链接核对无缺失，diff/compileall/uv检查通过。没有夹带其他session/人设/local/secrets，既有忽略配置/凭据与本轮state测试/源码工件保留。随后仅本交接和报告补Git记录，记录提交由main/HEAD恢复，不自引用；无新增业务网络/模型/QQ/SSH/部署操作。提交不代表真实验收。
