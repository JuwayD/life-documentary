# ADR-0012: Phase 6 Step 1 — 前端剧情面板

**日期**: 2026-06-09
**状态**: accepted

## 背景

Phase 5B/C 已实现线索记录 (`record_clue`)、压力钟 (`advance_pressure_clock`)、故事种子 (`story_seeds`) 等后端数据，但前端"剧情标记"面板仅以 raw JSON 展示全部 flags，玩家无法直观理解故事进展。

Phase 6 规划中包含"前端剧情面板"，属于提升可玩性的第一步。

## 决策

将现有 `#flags-panel` 保留的同时，新增 3 个结构化面板：

1. **主线剧情面板** (`#story-panel`) — 从 `flags.story_seeds` 提取主线标题/前提 + 支线标题
2. **线索记录面板** (`#clues-panel`) — 从 `flags.story_progress` 按 thread 分组展示线索，含来源/地点/证物
3. **压力钟面板** (`#pressure-panel`) — 从 `flags.pressure_clocks` 渲染可视化进度条（绿→橙→红）

**纯前端实现，不改后端**。所有数据已通过 `/api/state` 和 WebSocket `"state"`/`"done"` 事件下发。

## 方案

- 在 `index.html` 侧栏新增 3 个 `<div class="panel-section">`，带 `data-test` 属性
- 在 `app.js` 新增 `renderStoryPanel` / `renderCluesPanel` / `renderPressurePanel`，在 `renderSidePanel` 中调用
- 在 `style.css` 新增 `.story-thread` / `.clue-card` / `.pressure-bar` 等样式，保持明代纸质风格
- `FakeAgent` 扩展：输入含"线索"→ `record_clue`，含"压力"→ `advance_pressure_clock`
- 新增 2 个 API 测试 + 3 个 E2E 测试

## 后果

- 正面：玩家首次能看到主线是什么、发现了哪些线索、压力是否危险，不再依赖 raw JSON
- 中性：面板数据全部来自现有 flags，空数据时显示"暂无"
- 负面：无。不改后端逻辑，0 回归风险

## 参考

- `docs/04-roadmap.md` Phase 6
- `src/mingrpg/tools/write.py` record_clue / advance_pressure_clock
- `src/mingrpg/scenarios/yangzhou_districts.py` story_seeds
