# LAP-40 QQ安装包静态核验：G1仍未证

返回[总交接](../tracks/laptop-workbuddy/tasks/LAP-40/HANDOFF.md) / [材料报告](lap-40-stage3-materials-2026-10-24.md) / [续作计划](../tracks/laptop-workbuddy/tasks/LAP-40/STAGE3_CONTINUATION_PLAN.md)。2026-10-24，Asia/Shanghai；根`LAP-40-max-realentry-next`，A2代码仍由唯一medium实施。

只读用户已指定的Downloads/QQ_9.9.36_260924_x64_01.exe；330,446,512字节，重新SHA256仍63255c70c7ff523e7eed7d52d9708ed7a77ea346ece6474c65dded406edb3155。此报告仅公开原创元数据/结论，不保存或提交QQ源码/原包。

## 实际方法和结果

系统tar可只读列出该7z自解压包（7z签名偏移118616），没有执行安装包。目录2017项，js/json/ini/asar/html候选9项；只取包内package.json/application.json与application.asar到Python内存，不写出文件，不安装或运行任何成员。

| 成员 | 字节/SHA256 | 可证明的事实 |
| --- | --- | --- |
| resources/app/package.json | 486；24399ee1fd847232e0ea593b54c4721e1bc76342d1d2b28718a0cf606eef294d | 名称qq-chat，版本9.9.36-53644，win32，main指向application.asar/app_launcher/index.js |
| resources/app/application.json | 1451；cdf349533364325b6580964022583110d482a267e18fdb234584cf7dd8de2fc2 | 索引键包含application.asar、wrapper.node、major.node与package.json；不是用户数据目录证据 |
| resources/app/application.asar | 30,889,616；e2a43308e5a373f7225318cb3792e264f88799a0bdebde2fcdd61f734550f10b | 结构化header可解析，header_size394824、1452文件项；launcher三个成员各80字节 |

index.js的80字节内容按标准ASAR偏移读取后无法UTF-8解码。此分支以UnicodeDecodeError结束，未作额外解码、补丁、反编译或保护绕过；不能从文件名/入口指针猜测底层支持的数据路径参数。包内manifest不能单独证明原生QQ使用项目目录、免扫码或与日常QQ隔离。

首次完整tar目录输出过长，随后在进程内筛选候选，仅记录总数和上述必要项；未因目录项多而扩大到本机QQ目录。没有读取Public Documents/UserDataInfo.ini、日常登录库/认证/账号数据、注册表或运行QQ。

## 范围与下一步

这只补充原始安装包布局/版本/摘要证据，**不是干净专用QQ已准备、原生数据隔离已通过或“只差扫码”**。当前仍缺可信Windows原生数据机制及受控访问元数据互证；G1保持unverified，不自动安装试错、改共享ini/HOME/APPDATA或换系统用户/VM。A2独立代码可继续，B仅可按缺机制拒绝真实probe。

实际命令仅mmap签名/哈希、系统tar -t与tar -xO到内存及struct/JSON元数据解析。未新增工具依赖，无磁盘解压/原生复制/客户端执行/注入/端口/登录/模型/群/SSH，原E运行态及本机配置不动。
