# WX-AKASHA-ALL 实施

返回[PROGRESS](../../../../PROGRESS.md)；继承根AGENTS。

状态：active，2026-10-31T10:25:51.763167+08:00，负责人本会话Codex，session WX-AKASHA-ALL-20261031。


2026-10-31T10:25:51.763167+08:00：唯一任务 **WX-AKASHA-ALL**，负责人本会话Codex，session WX-AKASHA-ALL-20261031。起点QQbot_Snowluma main=42911af。归属：plugins/qq_router/{main,provider,wechat}.py、必要src/qqbot_gateway/{model_gateway,turn_v2,group_memory,persona}接点、scripts/configure_akasha.py、定向测试与报告、PROGRESS/工作线HANDOFF/TASKS/本项HANDOFF；运行配置仅增量平台/插件，原QQ local保留。完整执行微信计划；已有微信9份规划差异保留，QQ开工干净。不操作旧NapCat根。只管理有创建身份的项目进程；授权受管部署/检查/提交普通push，真实聊天交用户。

总入口：[微信实施交接](E:/CodexWS/WeChatbot/tracks/tasks/WX-AKASHA-ALL/HANDOFF.md)。对应[QQ实施交接](E:/CodexWS/QQbot_Snowluma/tracks/laptop-workbuddy/tasks/WX-AKASHA-ALL/HANDOFF.md)。

目标：WeFlow公开API/SSE→固定Akasha薄补丁→现有AstrBot独立平台→既有provider/业务/MemoryStore→回源UIA。用户指定全部增强、必要组合检查和部署同轮完成；上游内核不改，不主动造真实生成/群发样本。

当前：QQ侧实现与受管部署完成，6199/11229监听；QQ connected/online/channel_ready、router_ready=true，current_error=null。微信账号/真实映射待操作者向导，同任务继续；见reports/wx-akasha-all.md。

## Implementation checkpoint

Protocol overlay and transport-bound existing router methods implemented. Real AstrBot adapter/provider metadata + fake model/UIA two-round combination passed (3 tests); current one-use image normalizer and explicit shared-context isolation passed (2 tests); existing schema2 suite passed (10 tests). No live model generation or message samples. WeFlow setup 18108 and local panel 18766 are identity-managed and running; robot account/key configuration not saved yet. Operator setup question pending. Next: native/QQ regression, current zero-generation binding, incremental managed deployment after actual selection. Source changes still uncommitted; no activation claimed.

## Pre-deployment checkpoint

Current native/QQ/schema2 suite: 34 passed; new WeChat material/shared-context suite: 3 passed; WeChat real-adapter/provider + synthetic model/UIA suite: 3 passed. Additional legacy test_transport_router: 17 run, 10 failures/2 errors, exactly reproduced at clean baseline 42911af in QQbot_Akasha_baseline; no legacy contract rewrite. Managed live gateway idle/ready/router_ready, current_error=null before stop. Baseline config/persona/local hashes and exact plugin/config backups: state/akasha-deployment. Operator account setup still pending, so platform listener can deploy independently; no real WeChat-ready claim.

Actual source ownership includes plugins/qq_router/wechat.py; src/qqbot_gateway/{wechat_materials,cli_web_policy,workbuddy_cli_runner,reply_delivery,backends,model_gateway,group_memory}.py; scripts/{configure_akasha,manage}.py; tests/test_wechat_materials.py; reports/lap-43-native-web-offline.json and task report/entries. No QQ local/persona/credentials/memory content changes.

## Runtime checkpoint

Current CLI zero-generation probe passed and active paired to c74ccff25c769e27dd55af1e84d74dc59cd9e1ff45c986b3c00845523eba72da. Actual source daily startup initially replaced the new platform; corrected the active _start_channel path to reuse incremental configure helper (not the retired path alone), then normal managed restart. Both 6199/11229 listen; QQ connected/online/channel_ready and router_ready true. Source QQ platform/provider/preferences and local/persona protection checks unchanged. Details: [QQ report](../../../../reports/wx-akasha-all.md). Operator account setup remains pending; no real WeChat reply asserted.
