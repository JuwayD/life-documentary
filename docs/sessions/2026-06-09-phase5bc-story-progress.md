# 会话日志: 2026-06-09 Phase 5B/C — 剧情进度与压力钟

## 触发

README 与 roadmap 指向 Phase 5B/C:主线与涌现支线素材结构。此前已完成经济系统小切片,但线索推进仍主要依赖 `log_event` / `set_flag` 的通用记录。

## 决策

- **做最小剧情进度切片**:只记录线索和压力钟,不做任务状态机。
- **线索存 flag**:`story_progress[thread_id].clues` 保存已发现事实、来源 NPC、地点和证物。
- **压力钟存 flag**:`pressure_clocks[clock_id]` 保存当前值和危险线。
- **仍由 GM 判断后果**:代码不判断任务完成、不自动升级剧情。

## 代码产出

### 工具

- `tools/write.py`
  - 新增 `record_clue(world, thread_id, clue, source_entity, location_id, evidence_item)`。
  - 新增 `advance_pressure_clock(world, clock_id, amount, reason, danger_at)`。

### GM Agent 接入

- `llm/tools_registry.py`
  - 注册 `record_clue` 与 `advance_pressure_clock`。
- `llm/agent.py`
  - 更新系统提示词:线索推进使用 `record_clue`,情势升温使用 `advance_pressure_clock`。

### 测试

- `tests/tools/test_write.py`
  - 覆盖线索记录、去重、压力钟推进、危险线触发。
- `tests/llm/test_agent_stream.py`
  - 固定 Phase 5B/C 剧情进度工具已注册。

## 测试

```bash
.venv/bin/pytest tests/tools/test_write.py tests/llm/test_agent_stream.py
# 53 passed
```

## 下一步

可继续把前端状态面板扩展为展示 `story_progress` / `pressure_clocks`,或继续增加更多支线素材与法律/商业细节。
