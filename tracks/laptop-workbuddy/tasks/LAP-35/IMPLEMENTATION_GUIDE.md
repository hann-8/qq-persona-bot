# LAP-35 medium实施指引

返回[PROGRESS](../../../../PROGRESS.md) / [HANDOFF](HANDOFF.md) / [PLAN](PLAN.md)。用户明确Max先详细规划、medium后续实施；本轮未实现。模型/档位由操作者设置，不自动切换。

## 两项需求的实施顺序

建议先开gpt-6.1-sol/medium会话，按[LAP-34完整复制指令](../LAP-34/IMPLEMENTATION_GUIDE.md)实施分层配置；34完成交接/Git交付后，再另开medium会话实施35。两个任务分别登记/提交，一个session只推进一个任务；配置迁移/启停/真实模型与群验收仍须后续明确授权。不能把“去实施两项”理解为可以覆盖用户persona或同一session同时领取两个任务。

35在34实现后扩展chat.yaml；如果用户指定35先做，则只扩展现有单文件，交接标出待34保留silence节，勿提前实现34或创建第二套配置体系。

## 可复制的LAP-35实施指令

```text
请实施LAP-35“群临时停言、真实@恢复与重启复位”，按AGENTS.md执行。
先读PROGRESS.md、工作线HANDOFF/TASKS及tasks/LAP-35/{HANDOFF,PLAN,IMPLEMENTATION_GUIDE}.md；
涉及配置再读LAP-34方案/交接，核对34实际是否已实现，不假定规划文件就是运行能力。
登记35实施session/开始时间/文件归属后重读；保留所有用户/其他session差异，尤其config/persona.md。

严格按S35-01→05、SM-01—12实施：
1. 每授权群normal/muted RAM状态由gate唯一持有；缺省普通。
   非黑名单群友明确指向bot的停言要求即本群哑巴，0确认消息/表情/额外分类推理。
   仅下一条非黑名单原始真实@恢复普通，该@进入原must-reply；同条@+停言优先停言。
   普通不改当前free/mentions；恢复后完整普通，不是只答一次。
2. 本地有界句式识别覆盖方案正反例/礼貌请求/否定作用域/引用转述；
   mentions非@控制只在gate处理，不放普通非@进模型；黑名单在识别/材料/窗口之前。
3. gate monotonic群generation + boot/连接绑定的签名输出门票，最终出站群锁再次检查。
   覆盖正文/single/adaptive/图片/typed@/所有本地提示；停言→唤醒不能放出旧结果。
   保留原event与逐条ACK路径，不用裸API、共享类patch或缺票逃生分支。
4. 两模式router监测gate状态镜像，取消本群router本地未提交provider HTTP的等待/焦点候选；
   已提交HTTP（含网关内部排队）/runner自然收束并丢弃旧结果，不跨进程猜测是否已开始。
   不主动中断SSH造unknown、不全局取消；真正unknown/cleanup阻断不得因唤醒/重启被清除。
   启用时纯mentions/single也走已有受控ACK，仍仅一条，未发送正文不写成助手历史。
5. gate/完整bot/电脑重启回普通；WS/QQ离线/插件/model重连不解除哑巴。
   状态主数据仅RAM，磁盘元数据只读镜像不恢复；不设超时自动解除、不删持久记忆/历史。
6. 唯一新增participation.silence.enabled默认true，分层放chat.yaml；别名复用attention.aliases。
   新字段/运行态/门票不得进入persona/session_version或模型输入；不修改角色正文。
   区分34完整布局导出与35之前代码的功能兼容导出；保持旧严格字段校验。

测试仅自造数据/临时目录，完成SM-01—12及适用单元全套、两runner底层替身+实际AstrBot事件/回执链。
不能只测bool状态机就标通过，必须覆盖同条@+停言、旧结果在唤醒后返回、所有提示和ACK竞态。
在途已提交消息不能撤回，报告按实际sent/partial/unknown，已知gate拒绝不能误标unknown永久锁群。

本轮实施只交付代码/模板/文档与离线证据；不改本机运行配置或凭据/真实图库/群记忆，
不启停/登录bot、不连接SSH、不调用真实模型或发群消息。真实加载/验收等待后续明确授权。
遇到改变合同的能力缺口，完成独立部分、保持无法贯通的能力不可激活，记录并回规划；
不得自行删掉栅栏、加第二分类模型、扩大触发/账号/额度或开付费API。
结束更新HANDOFF/PROGRESS/TASKS及报告；按长期授权只提交本任务文件并push，核对远端完整SHA与保留差异。
```

## 重点审阅位置

- `admitted_message`要拆基础可控事件与普通聊天准入；去重后才变更状态，先身份/黑名单再识别。
- gate enabled时纯text/at也不能走不签票的旧快速透传；先剥原qqbot_*再附可信字段。
- typed@的精确参数集与签名票同时校验，最终发QQ前移除内部字段；send_msg(group)也有栅栏。
- local_notice/错误yield/空@/冷却/失败图片提示都要携带原event门票；普通single不可漏掉ACK/历史回收。
- 纯single受控ACK用独立本地needs_guarded_delivery贯通保存/发送/修复，不冒充qq_media_turn或改成media session_id。
- `delivery_allowed`和排队valid必须同时核对停言代际；不能“发送前取最新票”，那会复活旧输出。
- metadata监测对mentions也开启；普通disconnect invalidate只废候选/票，不抹gate主状态。
- 不直接cancel已提交模型HTTP/SSH去实现停言；结果可丢，真实清理与unknown仍走原合同。
- runtime静默不持久化、不进入群记忆；状态镜像中的群标识散列且不含原话/token，重启绝不反向恢复。
- `session_version`现复制participation，必须移除silence本地控制节；原角色文件不能编辑。
- 回旧代码的silence兼容剥除与34布局回滚是不同操作；不要让省略字段在新代码里被误认为禁用。

## 报告与验收出口

报告给出SM各项命令/结果及可证明范围，区分“已规划、已实现、离线通过、真实通过、完整验收”。实际在途消息/服务器ACK不能用单元替身保证绝无可见晚到；说明最终提交栅栏与旧结果失效的证据。

真实验收未获指令时，只留下两名群友停言/另一人@恢复/重连保持/重启复位/他群隔离的人工步骤，不执行。LAP-18搜索、24登录、28视觉、29成员、31B清理及原真人差额继续保留。
