# ADR-0014: Phase 6 Step 3 观察系统

日期: 2026-06-09
状态: accepted

## 背景

Phase 6 的目标是提升可玩性。路线图要求加入观察系统:默认场景只展示部分事物,玩家通过“仔细观察”发现更多,但发现能力有上限。项目第一原则仍是“代码是手脚,AI 是大脑”:代码只能暴露可观察素材与记录发现,不能判断线索价值或任务完成。

## 决策

实现最小垂直切片:

1. 地点支持 `observable_details`。
2. NPC 支持 `attributes.observable_details`。
3. 玩家增加 `attributes.observation` 作为观察基准值。
4. 新增 read tool `list_observables(actor_id="player", include_discovered=True)`:
   - 返回玩家当前位置可见或已发现细节。
   - 基于 `discovery_value <= observation` 做可见性过滤。
5. 新增 write tool `discover_observation(detail_id, target_id=None, actor_id="player", source="observe")`:
   - 写入 `flags.observations[actor_id]`。
   - 追加 `discover_observation` 事件。
   - 不生成线索、不判断意义。
6. GM prompt 增加观察流程:
   - 玩家观察时先读取状态与 `list_observables`。
   - 仔细搜查可用 `skill_check` 对抗 `discovery_value`。
   - 发现后调用 `discover_observation`。
   - 只有构成案情事实时再调用 `record_clue`。
7. 前端增加“观察”面板与“仔细观察”快捷按钮。

## 取舍

- 不新增数据库 schema,继续使用 JSON 字段和 flags。
- 不在代码里做“隐藏线索是否应该出现”的叙事判断;代码只做可见性过滤与持久化。
- 不新增 API endpoint,继续复用现有 turn loop。
- 不把所有观察自动升级为 `story_progress` 线索,避免代码替 GM 判断。

## 后果

玩家可在开场场景看到低门槛细节,点击“仔细观察”通过正常 WebSocket/REST 回合进入 GM 流程。未来可逐步扩展更多地点/NPC 的观察素材,并让 GM 用检定发现高门槛细节。
