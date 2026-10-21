# LAP-36 只读证据与开源选型

返回[总计划](PLAN.md) / [图片合同](IMAGE_PLAN.md) / [网页/B站合同](WEB_VIDEO_PLAN.md) / [HANDOFF](HANDOFF.md)。日期：2026-10-21（Asia/Shanghai）。只记录结构/计数，不保留私密群消息、图片URL、文件名、账号或凭据。

## 1. 本机图片证据分层

| 来源 | 本轮实际观察 | 能证明/不能证明 |
| --- | --- | --- |
| 根AGENTS/PROGRESS与28交接 | 28已实现/离线；native未做/生产拒启 | 323单元/56组合900框架及22补验是历史结果，本轮未重跑 |
| `config/local/features.yaml`选定字段 | vision.enabled=false；web.enabled=true | 保存快照；未探活、不证明当前进程加载了此值 |
| 项目NapCat WS配置选定字段 | 一个启用反向WS客户端，messagePostFormat=array，reportSelfMessage=false；disableGetUrl无显式值 | 有结构化事件配置；不是某条真实图片事件的证据 |
| 安装的NapCat bundle | image映射包含summary/file/sub_type/url/file_size；url默认通过FileApi.getImageUrl，disableGetUrl分支可返回filePath | 静态实现有附件地址；实际成功率、URL可下载性、当前参数有效值未验证 |
| 本机4份受管日志结构扫描 | 所扫image段/CQ:image/图片占位/base64/URL字段/视觉状态模式命中均0 | 没有可用的历史原始载荷证据；不能推出NapCat没收图 |
| NapCat项目源码目录的原生日志文件 | 扫描时0份`.log` | 没有现成原生图片事件记录；未搜索日常QQ、全盘或未提供的导出附件 |
| `scripts/process_host.py`基线 | 只放行固定连接/请求/清理元数据，其他上游细节抑制 | 受管日志设计上不会保留图片事件/模型原始输入；不建议打开全文日志 |
| `onebot_gate.py`基线268—344附近 | 先准入，再把image等替换为`[非文本未解析]`；vision开启时才issue cap；raw_message清空 | 下游占位是项目剥离行为，不能当NapCat原事件形态 |
| `vision.py`基线 | 只取第一图data.url，精确2个HTTPS域；RAM下载/规范化/cap/原生输入；require_production恒拒true | 现有实现不接受文件名作像素；没有真实图片质量/容量放行来源 |

日志扫描时的非原子快照：astrbot 4,207字节/111行；gate 7,069/175；model 105,967/1,421；napcat 12,503/236。读取过程中日志可能被现有实例追加，未冻结/清空；这些计数仅用于说明检查范围，不是bot健康、请求总数或图片数量。没有输出原行。

本机bundle位置：`runtime/napcat/installer/NapCat.52230.Shell/versions/9.9.33-52230/resources/app/napcat/napcat.mjs`；版本锁记录NapCat v4.18.38。源码片段是程序，不是群消息。`file`是文件名不等于二进制；URL必须实际取回并通过图片解码才能进入“材料真实通过”。

## 2. 网络诊断与限制

本轮使用Python socket只输出地址分类，对`cn.bing.com`、`docs.python.org`、`www.bilibili.com`、`api.bilibili.com`、`gchat.qpic.cn`各进行一次系统解析：每域2地址、公网0、非公网2。没有打印地址、改DNS/代理、下载网页或QQ群图片。

另做两次无隐私小型DoH只读诊断（每种形式一次）：固定公网IP HTTPS、固定域名/SNI+公共bootstrap。均使用默认TLS校验、项目PublicConnector peer检查、trust_env=false、无Cookie、5秒/32KiB限制/无重定向。两者均ClientConnectorCertificateError；带域名的验证码20。未取消校验或轮询其他服务。不是当前项目已具备DoH能力的证明，也不能据此确认证书失败根因。

LAP-18历史三类搜索blocked_ip结论保留；本轮不是相关性/时效/正文质量复测。浏览器/连接器的联网成功与本机受控HTTP路径不同，不可互相代替。新解析/CA方案必须先通过TLS与公共正文探测，搜索仍另验。

## 3. 开源一次来源核对

| 候选 | 核对资料/版本 | 取舍及真实限制 |
| --- | --- | --- |
| python-readability / readability-lxml | [README](https://github.com/buriy/python-readability/blob/3e7a8321383b9f5e2c5a5a887f940f864c5c73d0/README.md)、[setup.py](https://github.com/buriy/python-readability/blob/3e7a8321383b9f5e2c5a5a887f940f864c5c73d0/setup.py)、[0.9发布](https://github.com/buriy/python-readability/releases/tag/0.9)；Apache-2.0 | 首选本地正文提取。依赖chardet、lxml[html_clean]、cssselect等；没有浏览器/模型。上游性能自述不是本项目中文质量结论 |
| trafilatura | [依赖声明](https://github.com/adbar/trafilatura/blob/master/pyproject.toml)；Apache-2.0 | 可用但核心直接依赖更多：courlan/htmldate/justext等；首版不同时安装，readability失败回规划 |
| yt-dlp | [B站源码固定快照](https://github.com/yt-dlp/yt-dlp/blob/897341241f2bfb2439fe0367f4c7c9ccd29a3828/yt_dlp/extractor/bilibili.py)、[依赖](https://github.com/yt-dlp/yt-dlp/blob/897341241f2bfb2439fe0367f4c7c9ccd29a3828/pyproject.toml)、[许可](https://github.com/yt-dlp/yt-dlp/blob/897341241f2bfb2439fe0367f4c7c9ccd29a3828/LICENSE) | Python包核心无强制依赖，但全下载器功能很宽；只复用字幕最小片段，不引入下载运行栈 |
| Nemo2011/bilibili-api | [仓库API状态](https://api.github.com/repos/Nemo2011/bilibili-api)本轮archived=true/size=0；pyproject入口404 | 老教程不可直接照搬；不假设历史包仍有可用维护源 |
| bilibili-api-zoku | [依赖](https://github.com/bromothymolb/bilibili-api-zoku/blob/main/pyproject.toml)，GPL-3.0-or-later | 覆盖动态/直播等大量API；多项与字幕无关依赖，首版不选 |
| VincenttHo AstrBot字幕插件 | [README](https://github.com/VincenttHo/astrbot_plugin_bilibili_summary/blob/main/README.md) | 要求外部模型API和SESSDATA，并有引用/转发解析；不直接安装 |
| DIO-goo AstrBot总结插件 | [README](https://github.com/DIO-goo/astrbot_plugin_bilibili_summary/blob/main/README.md) | 默认自动触发、Whisper API/音频/热评/图片卡片；超出当前轻量及权限合同 |

固定yt-dlp快照的`_get_subtitles`请求`/x/player/wbi/v2`，检查`need_login_subtitle`，读取subtitle_url/lan，并循环下载各字幕；同时构造danmaku条目。本计划只复用字幕字段/端点部分，改成先选择单轨再下载，不下载弹幕。其`_sign_wbi`是另一路播放信息流程，当前字幕方法没有调用它；不能为了“可能有风控”自动加入播放参数、指纹伪装或认证重试。

B站真实字幕获取、匿名可用率、SESSDATA有效性均未在本轮验证；接口来自第三方维护开源实现，**不称B站官方稳定API**。本轮仅读公共代码，不访问用户B站账号或视频。

## 4. 规范及原生能力来源

- [OneBot 11图片段规范](https://github.com/botuniverse/onebot-11/blob/master/message/segment.md#图片)：接收file及url；base64是允许的发送表示之一，不能据此强制接收帧内嵌字节。
- [NapCat图片映射源码](https://github.com/NapNeko/NapCatQQ/blob/main/packages/napcat-onebot/api/msg.ts)：picElement映射file/url/file_size，与本机安装bundle结构相符；上游main不是本机版本的替代证据。
- [Ollama v0.40.5模型渲染](https://github.com/ollama/ollama/blob/v0.40.5/model/renderers/qwen35.go)：处理image占位/图像偏移；渲染支持不等于完整视觉处理预算已证明。
- [Ollama v0.40.5源码树](https://github.com/ollama/ollama/tree/v0.40.5)：Qwen图像处理含不同运行路径；Mac MLX的像素/patch公式不能未经确认用于Windows/NVIDIA GGUF运行路径。
- [Cloudflare DoH JSON文档](https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/make-api-requests/dns-json/)：是规划候选解析接口；本机TLS未通过，不能声称已接入。

家庭Ollama0.40.5/Qwen3.5 9B Q4_K_M及digest等仅继承17日[工作线元数据](../../../local-5070/HANDOFF.md)；本轮没有SSH、没有重新检查加载/容量。CLI基线2.168.0/deepseek-v4.1-flash的原生image输入编码已有离线证据，但所选模型的真实图像支持及预算上界未证。

## 5. 本轮证据与后续更新规则

证据类型分为用户说明、提交基线源码推断、本轮静态检查、本轮真实公开网络元数据、离线替身结果、真实模型/群证据。后两类本轮没有新增。引用代码以main/b23d961为规划基线；并行LAP-24正在改日志/管理入口，medium实施前重读，不沿用“当前文件哈希已锁定”的说法。

后续每条真实证明记录能力/配置/适配器签名、有限计数、状态、失败类别和人工验收结论。私密图片/URL/字幕/模型回答仅在经批准的本机临时操作中处理；不把原文写入reports、提交或全局记忆。可提交自造夹具与公开源码来源/哈希，不能提交本机真实配置与凭据。
