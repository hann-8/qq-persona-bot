# LAP-46 整体CLI搜索表达与图片预算交接

返回 [PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [计划](PLAN.md)。继承根AGENTS，最新用户修订优先。

状态：planned / awaiting_user_review。session LAP-46-web-quality-plan，当前会话负责人，无代理。首版5b8c601已交付；本次起点main/5b8c601与实时origin/main一致。用户明确不修专名/游戏特例，要求整体搜索/表达和预算合理化；已选择思考开启、low，覆盖旧关闭偏好。整体仍先review再实施。

实证：bot是锁定CLI的WebSearch/WebFetch，用户对照为REPL→Search；bot替换system、关闭思考、要求群JSON、截工具材料为8000/12000、只留前两URL、部分校验失败终结任务、来源尾巴代码追加。当前图片8MiB原始/16MP解码、1024边/1MP处理、PNG512KiB/帧2MiB；文字524288字节/视觉预留4096。不能把问题缩成专名消歧或一概归咎文字预算。

11:38:53固定失败句对应CLI generation=success，不能确认图片预算失败；中午bot自述预算只是聊天。纯文字图后追问不重带原像素。离线高细节1600×1200 JPEG（1721958字节）normalize拒绝IMAGE_BLOB_INVALID，同尺寸纯色图成功：小字节门槛真实存在，但不证明今日特定图根因。今日两次搜索完整工具/模型原文未保留。

计划精简过窄适配/表达约束、允许普通工具错误纠正、思考true/low；试用8调用/10步/120秒、单64KiB/总256KiB、图原32MiB/处理8MiB/2048边与4MP、正文4000。同步实际校验/期限/来源和配置，避免仅改local；这些是可调默认而非新封顶。账号/准入/两工具边界保持，不开放REPL/本机执行。最多8项本机业务测试，含非原例查询和两类图，无主动群发。细节见PLAN。

本次只拥有AGENTS、PROGRESS、工作线HANDOFF/TASKS、本目录PLAN/HANDOFF六文档。用户未跟踪启动bat保留、不执行、不提交。未改代码/local/角色材料/采集开关，无启停/真实模型/原生联网工具/QQ输出。读取公开官方资料并核对锁定编码源hash，API支持不冒充CodeBuddy能力。

验证与Git：六文档/256个本地链接无缺失，git diff --check及归属检查通过，未改代码或配置；最终提交号见Git和本次回复。本次不是实施，核对后释放文档归属。

下一步：用户review修订方案后，当前会话依PLAN完成最小实现、必要验证、配对部署和Git。不要按首版旧预算/思考false保持执行；实施前重新取Git/配置/运行基线。
