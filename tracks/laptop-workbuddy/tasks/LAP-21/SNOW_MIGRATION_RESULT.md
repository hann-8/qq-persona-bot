# LAP-21 Snow受控表情实际迁移结果

返回[PROGRESS](../../../../PROGRESS.md) / [工作线](../../HANDOFF.md) / [TASKS](../../TASKS.md) / [本任务交接](HANDOFF.md) / [迁移计划](SNOW_MIGRATION_PLAN.md)。

2026-10-25（Asia/Shanghai），session `LAP-21-snow-memes-data-migration`，16:07登记并重读归属。工作根为`E:/CodexWS/QQbot_Snowluma`，分支`codex/lap-40-snowluma`；实际起点HEAD和实时远端均为`dc79796642371ee72945457b0a4c1bcd94164801`，起始无非忽略差异。未回退规划起点、未切分支、未派代理或切模型。

## 实际交付

| 状态 | 结果 |
| --- | --- |
| copied | 7/7文件已实际复制入目标受控library，复用已有文件0；5 GIF、2 JPEG，共4,100,086字节 |
| staged | 已在既有配置锁下原子写入`state/memes-pending.local.yaml`；version=1/base/items，7条原字段及顺序保留 |
| activated | 未激活；`require_stopped`确认目标项目仍有身份匹配的运行进程，活动catalog仍不存在/0条 |
| loaded | 未确认加载；本轮没有启动/重启，pending不是运行候选 |
| real_ack | 未验；真实模型、群发送、收藏读取、下载及真实RPC均0 |
| client_display / GIF动画 | 均未验；本机解码/hash及合成ACK不构成Snow真实图片成功 |

源catalog与其7张引用图片在复制前后及独立复核中摘要一致；没有遍历迁移inbox、未登记素材、聊天或历史。7条均保留`id/name/context/tags/enabled/file/sha256/media_type`，无重标注、转码或ID变化。各级路径/reparse、真实格式、大小、尺寸/帧数、hash及目标引用通过现有`plain_path`、`MemeCatalog.preview/resolve`、`inspect_image`校验。全部7项可进入候选，紧凑JSON为1134 UTF-8字节，保持16项/2000字节上限。

目标原catalog/pending均不存在，先保存不存在标记及配置摘要/私密manifest，才复制与暂存。完整标签、资产清单、图片和摘要留在目标忽略目录`state/meme-migration/LAP-21-snow-memes-data-migration/`，未进入文档/Git。目标既有非本批数据未覆盖；暂存前锁内复核配置source_digest、活动fingerprint、pending竞争与源稳定性。独立复核确认同批合并无重复行，既有图片字节全同，原配置与persona保护摘要保持。

生产代码修改0、新增配置字段0、依赖修改0。memes=true、两个图片冷却0/0、free/web与模型/人设/账号额度均保留；vision、memory/learning、members、attention、bilibili仍保持关闭。源根只读，没有加源写锁、生成源pycache或备份；旧C根未访问，A4未读取/测试，B/C停止路线未续作。

## 验证

- 在现有目标Python中设置`PYTHONDONTWRITEBYTECODE=1`、`PYTHONPATH=E:/CodexWS/QQbot_Snowluma/src`，均使用`-B -X utf8`。
- `-m unittest discover -s tests -p test_memes.py`：20项通过，临时根/自造图片/假RPC；未运行全矩阵、verify_lap21主入口或A4，没有覆盖旧reports。
- 忽略目录中的`prepare.py`完成备份、排他复制、锁内暂存；`verify.py`独立只读重查7图/字段/hash/预算、源稳定性、配置/persona保护及幂等合并，全部通过。停机检查结果为running，未调用激活。
- 6份交付文档的208个本地链接、2行围栏及10个精确数据路径忽略检查通过，`git diff --check`通过；精确暂存名单在交付前核对；只提交本任务6份文档，完整提交号与远端SHA一致性由最终回执报告。

## 剩余动作

以后由用户另定唯一执行session与时段，授权正常停止本项目后，在目标根运行以下本机既有批次激活辅助脚本；它复核manifest/配置/源数据/active/pending归属，调用带config_guard的`activate_pending`，由该方法自己获取配置锁并再验停止。若摘要或数据有变化，拒绝并重新核对，不覆盖新标签或别人的pending。

```powershell
Set-Location E:/CodexWS/QQbot_Snowluma
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='E:/CodexWS/QQbot_Snowluma/src'
.venv/Scripts/python.exe -B -X utf8 state/meme-migration/LAP-21-snow-memes-data-migration/verify.py --activate
```

本轮没有执行`--activate`。激活成功以后，再在授权范围正常启动/重启并确认加载；真实图片验收须另授权群/时段/调用上限，沿既有统一投递链分别确认图片ACK、客户端显示与GIF动画，失败/unknown不自动重试。不要求全量旧验收或72h/7天作为前置。

回滚只在停机及既有配置锁下，根据本批备份/不存在标记和摘要恢复目标catalog/pending；先核对当前仍属于本批，不恢复覆盖后来的修改。当前原catalog不存在、pending为本批新增；图片可留在忽略库。不得热改目录、删除lock/state/数据库或使用git reset/clean。本轮不执行回滚。

本次迁移准备已完成，真实加载与发送差额保留；Git交付后释放归属并停止。后续仍推荐记忆优先、识图随后，等待用户下一条指令；B站字幕退出近期路线，本轮不删代码、不续字幕/ASR。
