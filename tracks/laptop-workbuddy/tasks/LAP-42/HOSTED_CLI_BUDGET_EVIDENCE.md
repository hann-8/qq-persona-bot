# 当前DeepSeek CLI视觉预算：只读证据

返回[识图收尾计划](VISION_FINISH_PLAN.md) / [42交接](HANDOFF.md) / [PROGRESS](../../../../PROGRESS.md)。核对2026-10-25，Asia/Shanghai；基线48f66bc192548184e4f88e23de6a357962bff85e。本轮只读公开文件/锁定代码和纯函数计算，未执行CLI、模型、启停或群操作。

## 1. 新取得的第一方依据

| 来源 | 已核对事实/适用边界 |
| --- | --- |
| [DeepSeek官方视觉文档](https://api-docs.deepseek.com/zh-cn/guides/vision/) | 单张图片token上限为1024，JPEG/PNG/GIF/WebP及user图片块受支持。此为图片模型token规则，不是base64字节换算；不得改用DeepSeek API Key或新直连后端 |
| [官方V4.1 Flash发布说明](https://deepseek.com/en/news/deepseek-v4-1-flash/) | 原生视觉，WorkBuddy/CodeBuddy为官方接入方。与用户确认当前模型可视觉识别相符；不单独证明本机QQ群闭环成功 |
| [官方模型页](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/) | 当前Flash上下文1M、上游最大输出384K；本项目仍以所选CLI当次有效限制为准，不把上游上限直接写进本机窗口配置 |
| [固定版本tokenizer](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/314113f8a7dadb388215396ba5fbee2c610a04d6/tokenizer.json) | BPE、空normalizer、Isolated切分、ByteLevel不加前缀空格、256个byte alphabet齐全、无subword前后缀、added token均非空；可审阅普通文本token不大于UTF-8字节的保守界 |
| [固定版本官方编码器](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/314113f8a7dadb388215396ba5fbee2c610a04d6/encoding/encoding.py) / [说明](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/314113f8a7dadb388215396ba5fbee2c610a04d6/encoding/README.md) | 模板按role/思考前缀/图片占位构造；当前单system、单user、单图、无tools可做有限模板上界。只审阅参考，不执行远程代码，不加载权重 |
| [Tokenizers ByteLevel参考实现](https://raw.githubusercontent.com/huggingface/tokenizers/v0.22.2/tokenizers/src/pre_tokenizers/byte_level.rs) | bytes_char将每个字节映射为一个初始符号；该postprocessor的added_tokens=0，只处理offset/sequence，不插入token。JSON中postprocessor的add_prefix_space=true不能误当预分词增加前缀 |

公开API文档是抓取当日的说明，固定模型源码为不可变revision。1024规则适用于所选DeepSeek原生图片契约；medium须将当前CodeBuddy路径确实转交该模型、单图不变成多图/未知OCR的来源一并记录，不能借其他提供方catalog项充当当前接入证明。

本轮公开资源仅在内存读取，没有保存下载物/安装依赖：

| revision 314113f8a7dadb388215396ba5fbee2c610a04d6内文件 | 字节 | SHA256 |
| --- | --- | --- |
| tokenizer.json | 6367257 | c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b |
| encoding/encoding.py | 37962 | 13231c592e958fb39e2af6001dae69d90e7a36b265702b9b390236fb387599e2 |
| encoding/README.md | 12164 | a34a5ca98c65e5b5b2bedd693cc2e18e732fe50192723fb6937ae07219c23739 |

tokenizer普通分词先将UTF-8字节映为符号，隔离切分不增加内容，BPE仅合并；特殊字串成为非空单token也不增加该界。BOS/role/思考/图片占位等额外内容必须另计模板项，不能从“普通文本≤字节”偷换为“整个请求没有模板成本”。这是有来源的上界推导，不是精确计费token数或平均中文换算。

## 2. 锁定CLI的来源和限制

CodeBuddy CLI 2.168.0，dist/codebuddy-headless.js SHA256：
`13e6dd30a22d2f11857675193f909a2ccb935da67a067f580fcfe764e474ff60`。本轮未改其文件/全局设置/凭据，未启动它。

- resolveEffectiveContextBudget：优先有效session override，再contextWindow.defaultLength，再多选合法长度中的最小值，否则maxInputTokens。不能假设总取最大档；项目metadata过滤当前只取default，需补defaultLength等安全字段并保留兼容。
- ModelUtils.getMaxOutputTokens：显式模型maxOutputTokens优先；环境输出覆盖只会进一步取min。模型应用接点把结果写modelSettings.maxTokens。故当次元数据128000可作为已审阅此路径的输出上界；项目output_reserve=2048不是已经下发的max_tokens。
- systemPromptFile覆盖接点读取指定system文件；当前命令无appendSystemPrompt、无resume、setting-sources=none、tools/MCP为空。medium须核对最终发送文本仍处在这些有限分支内，包含任何实际额外文字；不能把“自定义system覆盖”当成未知额外材料不计。
- 当前所选模型快照为maxInputTokens=1000000、maxOutputTokens=128000、low支持；最终发user前必须由现有0生成get_available_models握手再次验证，不能只信旧表。仅保存白名单能力字段，不保存rawModels中的URL/API Key等原值。

未采用bundle里opencode-go/openrouter等其他model catalog的同名条目作本项目提供方证据；不启用CodeBuddy HTTP/ACP新服务，不读日常WorkBuddy密码或换账号。

## 3. 当前代码中可复现的阻断

1. [production_diagnostics](../../../../src/qqbot_gateway/vision_capabilities.py)要求cfg.num_ctx或context_window_tokens；CLI的[validate_model_settings](../../../../src/qqbot_gateway/token_budget.py)却拒绝任何非null原生窗口。对当前CLI两条件不能同时满足；不能靠手填1000000解锁。
2. [text_budget](../../../../src/qqbot_gateway/vision.py)把视觉reserve=4096当数值从文字字节limit=30000中减去，得25904。当前实际persona纯函数组合，空prompt的usage已25997：无需模型就可证明此分支超限93。该计算不输出persona正文、不改settings；vision开/关纯组合的system均23895字节。
3. reviewed要求8项本地GGUF式runtime字段，而runtime_identity(CLI)只返回version/artifact_sha256/node_sha256；不应填假processor/model_digest。managed_cli_input_review还固定报告三缺项/permits_native_iq=false，需改成实际派生。
4. IQ前置/生产回查硬编码旧reports/lap-28-C-offline.json及适配器签名；修复新CLI代码后要求重跑/覆盖旧报告才可用不符合本轮边界。hosted路径应消费新的固定42视觉定向报告，旧路径/旧证据保持。

## 4. 可执行的预算分层

保留文字政策：含现有开销的可见UTF-8 usage ≤ 30000；保留请求体/图片规范化/输出参数。另对当前hosted规则计算：

```text
T_upper = 全部实际文本的UTF-8字节上界
F_upper = 已审阅有限模板/CLI附加文字的上界
V_upper = 1024（仅一张原生图片；占位可在F中重复保守计）
O_upper = max(本项目输出预留, 当次CLI生效最大输出)
C = 当次CLI有效容量与已核对模型契约的较小者
T_upper + F_upper + V_upper + O_upper <= C
```

例如在F_upper经过审阅确实≤2048、当前C=1000000/O_upper=128000时，以T_upper≤30000计算总界161072，未超容量。这只是条件算例；F必须从有限结构/来源计算，不能凭原字节预留值说已证明，也不另设2048模板硬门槛。若元数据/结构不同则重算或拒绝，不能无条件使用示例。

视觉input_reserve_tokens=4096保持为原生token的预算预留，核对V/相关标记是否容纳；不再从hosted文字UTF-8政策里混单位扣除。原本地后端和其他模型路径不因这次选择而变更。

上述事实支持下一轮实现当前hosted专用规则和真实尝试，不等于已建生产记录、IQ通过、vision开启或QQ群图像回复成功。本轮这些真实操作均未发生。
