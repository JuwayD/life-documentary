# 会话日志: 2026-06-08 Phase 5A — 世界扩展与 NPC 日程

## 触发

Phase 4 渲染层与流式叙述已完成,根据 roadmap 进入 Phase 5: 世界扩展。

## 决策

- **先做 Phase 5A 小切片**:只推进 20+ 地点与 NPC 日程,暂不实现完整经济系统和任务系统。
- **扩展区域采用数据表 seed**:`LOCATIONS` / `ENTITIES` + 循环写入,减少大量重复手写 seed。
- **NPC 日程放在 `attributes.schedule`**:保持现有 JSON 实体模型,不新增数据库表。
- **日程由 `advance_time` 自动触发**:代码只按时辰执行确定性移动,不判断剧情意义。
- **支线只埋素材字段**:`rumor_hooks` 提供 AI 叙事线索,不硬编码 quest state machine。

## 代码产出

### 场景

- `scenarios/yangzhou_districts.py`
  - 新增 10 个地点:书院、医馆、运河码头、渡口、货栈、城隍庙。
  - 新增 8 个 NPC:顾先生、林生员、何郎中、药童阿七、钱把头、牛脚夫、周船夫、庙祝沈老。
  - 为 `constable`、`inn_waiter`、`vendor_food` 和部分新 NPC 合并时辰日程。
  - 设置 `phase5a_world_expanded` 标记。

### 启动接入

- `web/server.py`: `seed_all()` 接入 `seed_yangzhou_districts()`。
- `cli.py`: CLI 初始化接入 `seed_yangzhou_districts()`。

### 工具

- `tools/write.py`
  - 新增 `tick_npc_schedules(world)`。
  - `advance_time()` 设置新时辰后自动调用日程 tick,返回 `schedule_tick`。

### 测试

- `tests/scenarios/test_scenarios.py`
  - 全场景实体数更新为 21。
  - 地点数断言更新为 20+。
  - 新增扩展区域地点、双向出口、新 NPC 契约测试。
- `tests/tools/test_write.py`
  - 新增 `tick_npc_schedules` 移动测试。
  - 新增缺失地点跳过测试。
  - 新增 `advance_time` 自动触发日程测试。

### 文档

- `README.md`: 当前阶段更新为 Phase 5A 进行中,测试总览更新。
- `docs/04-roadmap.md`: Phase 5 标记为进行中,Phase 5A 两项完成。

## 测试

```bash
.venv/bin/pytest tests/scenarios/test_scenarios.py tests/tools/test_write.py
# 50 passed

.venv/bin/pytest
# 139 passed, 4 skipped
```

## 下一步

Phase 5B 可继续推进经济系统:物价、雇佣、服务购买和更明确的主线/支线素材结构。
