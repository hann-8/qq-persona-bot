# LAP-48 实施与部署结果

返回 [PROGRESS](../../../../PROGRESS.md) / [HANDOFF](HANDOFF.md) / [PLAN](PLAN.md) / [TASKS](../../TASKS.md)。

2026-11-04（Asia/Shanghai），implemented_and_deployed / ready_for_user_test。本会话为唯一实施、迁移、配对和受管启停执行者；未派代理、未切模型，未主动真实模型生成、公共搜索或发送QQ/微信测试消息。

## 已实现与启用

- schema3沿原namespace/key保存，QQ号字符串为成员唯一键，name展示，memory/group/unassigned为无记录ID的文本数组。模型只回写变化成员或整块，省略不改、[]清空；全文交Planner，_meta仅宿主，fact_refs为空。整块同文轻量去重，语义合并仍由原Planner完成，无新增调用。
- 旧HMAC只用现有本机数字候选按原算法验证。实际两份有效记忆39条全部保留：35条对应5位成员及8条群内容；另一份4条对应2位成员、1条群内容和1条待关联。待关联原文/旧关联保留在宿主元数据，模型看可读待关联内容；后续只匹配仍存在且未改写的文本，不复活已删除内容。既有0字节退役文件原样保留，status仍计1个unavailable，不阻塞当前两群。
- 保留显式WX-Akasha映射；未配对来源使用wechat:身份。独立WeChatbot和旧QQbot未修改。
- 原生WebSearch/WebFetch采用官方tool.call，删除第二计划、pending等待、完整历史重演/prefix相等、阶段齐全和固定10步门槛；cli_max_turns仅兼容。8次真实工具执行及64KiB单次/256KiB总材料预算保留可调。网站/执行预算错误作为普通工具结果交模型收尾，parser不再以调用预算或完整工具历史拒绝整项；其它工具/MCP仍关闭。真实本地适配错误使用WEB_ADAPTER_ERROR，与后端错误区分。
- CLI运行默认及本机120→180秒，两阶段共享同一deadline；表达预留30秒、每阶段清理5秒在期限内，Planner默认约145秒。provider等待由queue_wait＋run_timeout＋25推导，本机235秒，实际provider_sources已加载235。旧Python网页15秒不作为CLI整项期限。
- 运行复核发现已有微信配置的启动分支保留了旧provider source；已在原受管启动路径只更新对应source timeout，保留平台/账号/其它字段，并完成定向回归与必要空闲重启。
- saved/unchanged直接返回原回复plan，不追加提示、不截正文、不改气泡/表情/@。内部MEMORY_SAVE及memory-last-save保留实际结果；明确记忆请求失败才附一次说明，后台失败静默。
- config/persona.md与PERSONA_RESTORE逐字节一致，17575字节，SHA256 82a9378d450388a8c08cb30481ee42c8666c3a4b8758293a014d243a75ced430。保留ff2e348第1～12节，仅删指定节/失效说明；Planner→Replyer共用完整人设，删通用风格冲突，未加正文过滤器或风格计数器。长人设增加两阶段及工具往返输入成本，不保证编号节省抵消它。

## 检查与实际加载

- 当前定向组合36项通过：整块记忆/冲突/容量/持久化与投递接点、两阶段、owner/muted/触发、锁定SDK的无第二计划/流式并行/内嵌摘要/网站错误/执行预算及超过10步；另11项runner/配置通过，实际provider保留分支1项通过。没有重做旧六例IQ、全库或长稳矩阵。
- 当前锁定CLI零生成配对一轮通过：Planner图片正向、缺插件/错回执负向和Replyer正向；positive_next_calls=0、negative_users=[0,0]、远端生成0。既有识图机制已重新绑定并激活b2212e35cf2cf84593eea38969cc5010c201f8e73cf128f703439eeed19285b7，仍为lap43_operator_trial/pending_user_test，旧证据未改写。
- 最终独立status/health为running、connected、can_receive_group_messages=true、router_ready=true、current_error=null、pending_restart=false、source_changed=false；实际planner_replyer/30、thinking=true，provider source timeout=235。当前模型/账号/low/额度、访问/唯一操作者、识图/记忆/表情及WX配对保留。
- 停机时读取的五份local与当前语义比较，仅CLI运行期限改变；key/图库及已激活、待激活表情的保护摘要一致，人设与指定备稿一致，offline_current/probe_current均true。

上述为离线、零生成、迁移及运行加载证据，不证明真实搜索、识图、角色自然感或群聊质量。真实体验与延迟交用户自然群测。

## 备份、回退与交付

精确资料在忽略目录state/lap48-deployment：before含五份local、原人设、实际记忆/key、图库/表情、active/技术配对和原AstrBot实例配置；另有stopped-files、migration、check-final、probe、activate、provider-check、runner-check、stop/start及最终status/health/protection。原私密内容、QQ号和凭据未写入提交。301个本地文档链接已核对，无缺失；两个当前配置群的记忆均可用，unavailable仅为上述退役空文件。

回退先受管停止，保留当前schema3及部署后新增事实；旧代码不直接读取新格式，必须配对恢复代码、期限/provider、人设和技术材料。已有新事实先导出保留增量，不能用旧备份覆盖丢失，也不能覆盖用户后续配置或清会话/图库/登录。

Git按授权仅提交本任务已核对文件，从短期codex/lap48-memory-web-persona快进回main、推送并清理已合入短期分支；最终提交号见交付回执与git log。原用户未跟踪启动机器人_workbuddyDeepseek.bat保留、不执行、不提交。剩余质量项仅用户自然群测，不追加实施审批。
