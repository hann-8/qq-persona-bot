# LAP-46 实施结果

返回[PROGRESS](../../../../PROGRESS.md) / [交接](HANDOFF.md) / [执行合同](PLAN.md)。2026-11-03完成实现与受管部署，源码提交bbe728d；真实群体验仍待用户试用。

## 已修正

- 锁定CLI的WebSearch有别名read。原disallowedTools含Read，CLI大小写无关的别名匹配会把WebSearch一并禁用。去掉CLI参数中的冲突项，仍以精确--tools和调用guard仅允许WebSearch/WebFetch。init注册目录出现Read不等于Read可被模型使用；锁定SDK实际启用函数回归证明：修前搜索false、修后搜索true、文件Read仍false、WebFetch true。
- 删除数字、token/secret与标识匹配式工具内容拦截；移除来源尾巴、统一标题和前插URL，材料保留真实标题/正文，成功链接不再只留最先两条。普通SDK错误可交还模型继续处理。
- 兼容并行WebFetch内置网页处理发起步骤时工具结果尚未齐全的情况，不再因此终结整轮。实际捕获暴露了该问题，锁定SDK的并行/嵌套离线回归通过。
- 思考实际开启、强度low，最终正文与思考分离；精简搜索/失败表达，工具选择由模型完成。损坏v2 JSON中完整字符串正文可恢复，记忆/提及/工具等辅助动作不从损坏结构恢复，无额外模型润色或修复调用。
- 原图32MiB、处理后8MiB/4194304像素（默认最长边2048），JPEG保留标准JPEG编码；PNG体积超限时可编码为JPEG，避免固定PNG膨胀直接拒绝。帧和RAM额度随配置派生，不另建图片系统。

## 实际保存/加载

config/local仅9个计划字段变化：运行期限120秒；web 8调用/10步骤/单65536字节/总262144字节；vision原图33554432/处理后8388608字节/4194304像素；正文4000字符。其他保护文件与群记忆摘要未变。模型、账号、人设、授权名单、owner/free、记忆容量不变。

部署后独立status：process_state=running，channel_state=connected，can_receive_group_messages=true；model.alive/router_ready=true、current_error=null；thinking_enabled=true，web工具两项及8/10/65536/262144已加载；vision.enabled=true、memory读取/学习true；pending_restart=false、source_changed=false。识图仍标记lap43_operator_trial/pending_user_test，不晋升历史完整验收。

## 验证和证据边界

- 72项原生/视觉/图像材料组合通过（含图片配置扩大、JPEG、内存释放、SDK嵌套/并行），后续新增别名/正文恢复后最终当前技术检查36项通过；runner/桌面33项通过；模板/ingress定向28项通过。组合有重叠，不相加成独立测试总数。
- 最终真实锁定CLI正反零生成probe通过：real_generations=0、positive_next_calls=0、negative_users=[0,0]，完成当前源码/配置/active配对。
- 最多8项业务任务全部留账：3旧路径查询、3修改后查询、2图片。旧游戏查询复现模型两次WebFetch自拼Bing搜索URL，正文为“菜”字百科/菜谱；其他内容页可读。修改后一个游戏任务暴露并行工具完整性拒绝，已修并离线回归。不能用这8项宣称全部搜索质量通过，也未将本次复现冒充白天原请求的完整还原。
- 两张真实原生图片输入均被模型正确理解：1600×1200 JPEG处理后1278451字节，明确超过旧512KiB；4000×2300截图缩至2048×1177，标题/数字/箭头方向正确。第一项附带联网问题的最终JSON少]，原wrapper丢正文，现已用该实际捕获离线重放验证正文恢复、辅助动作为空。
- 别名冲突是在上述8项之后定位修正；修正后的WebSearch可用性由锁定SDK实际权限逻辑和零生成接线验证，**未新增真实WebSearch服务成功样本**。实际相关性/回答质量交用户自然群测，不保证每次搜索命中。
- 扩展配置批次中的6个旧失败（把唯一owner加入黑名单的旧fixture、CF05缺platform_settings、两处过时注释断言）在811e70d原代码隔离副本逐项重现；未为本任务改无关旧断言。两个与新模板/图像尺寸有关的差额已修并定向通过。

## 交付与恢复

原始捕获、8项台账、保护摘要、当前probe/activate/start/status均仅在忽略的state/lap46-deployment。没有主动QQ发送，没有新增常驻详细原文日志。未跟踪用户启动bat保留、不执行、不提交。

回滚须受管停止，配对恢复811e70d代码、旧offline/probe/active以及本任务9个配置字段，再正常启动；先核对用户是否有后续修改，不整份覆盖新配置，不回滚群记忆。恢复材料在该目录before。源码已快进main；文档收尾提交号以Git及会话回执为准。
