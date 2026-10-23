# 原创SnowLuma私有接线接口

这些文件是本项目原创合同与自造测试，不含上游修改源码/patch/native。阶段2只完成接口，尚未在固定上游v2.1.1接线，不能称Snow适配或真实部署通过。阶段3须在忽略runtime中按PLAN核对最早分支、所有store/logger/补史/内置答复及原生保护，缺证据保持阻断。

`createProjectPolicy`要求已核对的受管实例/代际及实时`identityCurrent`回调，只有授权group新事件、匹配账号、非self/黑名单、合法ID与有界message通过。私有适配必须在任何转换/store/logger/history/model回调前调用`admitEnvelope/processEnvelope`，拒绝事件不会进入convert、metadata或forward回调。唯一forward只收到净化后的当前事件；引用只保留ID，当前image仅限长最小元数据，其余媒体/转发占位，无原始昵称/正文日志、内置#sl答复、文件写入或回拉API。`allowsRpc`是内部同样必须遵循的动作白名单，不能以其代替gate的参数、身份与最终发送许可校验。

`admitEnvelope`不需要message数组，只核验原生身份信封；`processEnvelope`先准入，再调用convert，再限长sanitize/forward。time保留正整数Unix秒；image只透传当前事件限长file/url元数据给既有gate校验，不缓存/下载；非法at丢弃，合法all可保留。

实际RAM接口将message/media/reaction/temp/RKey元数据共享在512条/2MiB/300秒上界；发送关联另128条/64KiB/600秒。全部Map内存，淘汰/时钟回拨/TTL执行，无磁盘回退。只存ID/受控类型/时间和计数，不保存正文或URL。`status()`仅输出封闭计数/容量，无QQ/群/正文/任意异常字符串。

`createHealthProducer`与Python `HealthProducer/HealthVerifier`使用同一8KiB、nonce挑战、HMAC-SHA256规范化JSON合同。创建时间是Unix整数毫秒，PID与创建时间均来自受管登记和实际进程核验；不从QQ事件接受自报身份。固定字段在PLAN基础上加入`config_digest`及`listener_port`，绑定加载快照与监听归属；每个nonce最多3秒、一次使用，seq严格增加，健康按配置TTL15..30秒生效，mirror不超过该证明剩余有效期。生产端必须从真实私有pipe/login/armed/rx/outbound观测取值，不得把初始good当armed。

Python verifier的`identity_current(binding)`由后续唯一受管owner接入registry、实际PID创建身份及监听归属，每次accept/ready均重新核验。默认gate无verifier、无密钥或无受管绑定时closed；没有公开的“提交自己签名healthy就放行”HTTP接口。实际listener/poll与独立秘密读取尚属阶段4；阶段2通过函数接口和自造生产端连通验证，不打开真实端口。

测试：`node --test adapters/snowluma/project_policy.test.mjs`。本机Node24.22.0仅执行这些原创无依赖测试，不满足Snow实际运行引擎，不作为其构建/运行通过证据。
