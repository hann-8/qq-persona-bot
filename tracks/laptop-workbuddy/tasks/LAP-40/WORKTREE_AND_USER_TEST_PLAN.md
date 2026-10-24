# LAP-40：E盘工作根与用户实测交付

返回[项目入口](../../../../PROGRESS.md) / [总交接](HANDOFF.md) / [TASKS](../../TASKS.md) / [A4执行交接](STAGE3_A4_HANDOFF.md)。2026-10-24 22:35，Asia/Shanghai；`LAP-40-max-E-worktree-user-test`。本次用户最新指令覆盖旧入口中“不新建worktree”的限制。

## 需求与交付顺序

用户指定SnowLuma代码在`E:/CodexWS/QQbot_Snowluma`独立worktree推进。先让SnowLuma与现有AstrBot/自研gate、router、模型链完成基本接线，达到可以明确启动、收发和记录故障的阶段就交给用户实测。实际性能、回复效果和长稳由真实使用验证；用户测试后拟由Sol high调试。本次根按用户指定Sol max接续规划/复核，既有计划内实施仍串行派gpt-6.1-sol/medium；没有自动检测或切换会话设置。

可启动实测不要求预先完成72小时或7天。实际可启动、基础真实收发通过、性能满足、72小时初筛、7天完整验收分别记录。用户实测之前仍须具备合法可运行私有入口、可信受管QQ身份和原生数据范围、黑名单/私聊/授权群前置及单次发送语义；这些是接线与隔离前提，不能用离线成功代替。

不增加业务功能/触发范围/后端或付费API，不改变账号、群、黑名单、模型、额度来源、人设及现有默认值。不自动切换原运行目录、不立即启动QQ/Snow、登录或发群消息。用户本次对实测流程的说明不替代一次真实probe的具体授权。

## 当前代码与Git证据

- 新worktree由干净的`codex/lap-40-snowluma-impl` / `8a431f1018a0b26f0dadb1c5979ac2fd7d88da8b`建立；新分支`codex/lap-40-snowluma`。源分支HEAD已与origin核对一致，旧目录不切分支。
- A0/A1、旧A2组件和9162d2c期限修复已审；A3同步helper慢bind为6077ms，A4仅局部5项候选，完整A2未过。定位`src/a4-scoped-broker.mjs`、`a3-runtime.mjs`、`a3-channel.mjs`及实际固定上游接线，均仅在忽略private内。
- `transport_owner.require_runtime`仍总拒；B资格/probe执行器尚未实施，Windows原生数据机制G1未证。AstrBot与自研层已有业务实现，但不能据此推定Snow原生接口可用。
- 开始额度：5小时used2%/余98%，周used62%/余38%；未使用reset credits。沿用<=5%停止新实现/测试并交接的约定。

## 路径与私有材料迁移合同

| 路径 | 用途与本次动作 |
| --- | --- |
| `E:/CodexWS/QQbot_Snowluma` | 新的唯一活动源码/文档根；所有后续工具显式指定workdir |
| `C:/Users/yutha/.codex/worktrees/lap-40-snowluma-impl/QQbot` | 保留旧代码及私有检查点；只读，不归档、不删除、不在此继续写代码 |
| `E:/CodexWS/QQbot` | 原NapCat运行根，代码/配置/进程均不动；venv解释器可按既有约定只读借用 |
| 新根`runtime/snowluma-private/` | 迁入已核清单中的JS/TS/Python/文本工具链与合成夹具；仍忽略，绝不提交上游修改源/patch/bundle |
| 旧根`runtime/snowluma/v2.1.1`及指定Downloads原ZIP | 原位置只读核验/借用Node执行JS合成；不复制、移动、链接或加载原生组件。新根因此不宣称原包部署已完成 |

迁移前记录源文件集合/摘要，逐一检查绝对路径和reparse点。仅迁移私有文本闭包；不复制`.pyc`、native、secrets、运行配置、真实state/log/cache或原始消息。现有27个上游包junction若需要，先核其目标都在旧private，再映射为新private内部目标，禁止跟随链接递归复制。新副本摘要应与源相同，路径重定位修改另外列明；旧原件前后摘要一致。

旧A0/A1/A2/A3证据带旧路径，只作为历史，不改写成新根已通过。新A4使用独立overlay/产物和证据，固定项目root改为新根；开发材料核验如需旧原包，仅用明确固定只读anchor，不能新增动态搜索/可写配置或放宽生产资格。缺本地独立venv/官方包时生产继续closed；不得为开发测试给新根链接整套运行态。

## 行为与接口合同

沿用[续作计划](STAGE3_CONTINUATION_PLAN.md)A2和[原A2续作](STAGE3_A2_CONTINUATION_HANDOFF.md)的3秒控制总期限、单次撤销、持续owner lease、固定PID/pipe、认证gate、允许动作与ACK合同。修复同步helper属于原计划范围，不重设计public wire/配置。

非阻塞helper限定并发、输出、创建身份及总deadline；一次操作的短原子观测与持续逻辑许可分开。原始包必须有界排队且未准入不进历史/正文窗口；新pipe、注入、敏感native提交前须fresh，停止/失效不可因新观测恢复旧scope。长图片操作不能靠延长旧证明绕过提交前复核。控制3秒从收到请求开始计算，不能用增加deadline掩盖阻塞。超时/unknown/partial不重试；只清理本次创建handle，不按进程名终止。

## 任务顺序、涉及文件与验收

1. 根登记新根与用户测试流程，更新PROGRESS/工作线HANDOFF/TASKS/总HANDOFF/MAX_START；本计划落盘后才派实施。
2. 一个medium独占新private、[A4交接](STAGE3_A4_HANDOFF.md)和专属原创报告，先完成无native迁移/路径复核和现候选审查，再集成完整异步链；根独占共享文档，不并写private。
3. 实际固定上游overlay中穿过控制、入站、单PIDpipe、注入、允许动作、最后native和ACK。慢helper至少覆盖120ms基线、总期限超时、取消/换代/停机、并发高频有界准入、长图片fresh和stop ACK；实际框架unknown不得写助手历史/记忆或重发。分别记录测试合同与重复组合，不累加虚大计数。
4. 根审实际diff/证据并重放决定性测试后，才能接受A2；B仍按[资格合同](STAGE3_QUALIFICATION_SPEC.md)串行实施并fake验证。真实机制缺口准确记录，不把未写代码推成用户待办。
5. 满足真实前置后，给用户明确的安装/准备最小待办、启动/停止方式、当前支持功能、一次基础收发步骤及日志位置，再由用户启动实测。测试后的Sol high只接具体故障与可复现材料；未测性能和长稳保持未验证。

迁移文档只检查Git归属、链接、路径和差异；实现只跑受影响/决定性验证，已过旧全量不为计数重跑。public不应出现上游派生源码、凭据或私有消息。按长期Git授权分可审检查点commit/push，核对应远端分支；Git交付不等于运行部署。

## 配置、兼容、回滚与未验证能力

无新增public配置字段；provider默认napcat、恢复/QQ重启默认false，用户local/persona不迁移、不重写，未来显式加载按现有停机事务。新worktree不自动继承旧进程、owner、健康、proof、预算或发送未决记录，也不能将它们清空后启动同账号。旧运行目录与分支保留，失败时停止新根开发即可；将来真实切换后的回滚仍须先证明受管退出、保留unknown，再显式恢复有限provider字段。

仍未验证：Snow原生保护允许、干净QQ与Windows数据范围、helper/QQ完整退出、真实WS/收发/受控表情/收藏ACK、实际性能、免扫码与72小时/7天。若原生数据机制需系统用户/VM或改共享数据，应回到用户决策；不能凭本计划创建环境或猜参数。
