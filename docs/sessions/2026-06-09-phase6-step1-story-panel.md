# Phase 6 Step 1 — 前端剧情面板

**日期**: 2026-06-09

## 做了什么

在 Phase 5C 全部完成的基础上，按 roadmap 推进 Phase 6 第一步：前端剧情面板。

## 为什么这样做

Phase 5B/C 已经在后端实现了 `story_seeds`、`record_clue`、`advance_pressure_clock` 等剧情数据，但前端只是 raw JSON dump。Phase 6 的核心目标是提升可玩性，第一步应该是让玩家能看懂故事进展。

选择纯前端方案的原因是：所有数据已通过 `/api/state` 和 WebSocket 下发，不需要新增后端端点。

## 具体改动

1. **HTML** — 新增 3 个面板 section：主线剧情、线索记录、压力钟，各带 `data-test` 属性
2. **CSS** — 新增 `.story-thread` / `.clue-card` / `.pressure-bar` 等样式，保持明代纸质风格
3. **JS** — 新增 `renderStoryPanel` / `renderCluesPanel` / `renderPressurePanel`，在 `renderSidePanel` 中调用
4. **测试** — 扩展 `FakeAgent` 支持剧情关键词，新增 2 个 API 测试 + 3 个 E2E 测试
5. **后端** — 仅暴露 `app.state.world` 一行，供测试使用

## 关键决策

- 保留 `renderSidePanel` 调用模式不变，3 个新函数独立可测试
- 压力钟用 3 色渐变（绿安全 / 橙警告 / 红危险）
- 线索面板按 thread 分组，显示来源/地点/证物
- 空数据统一显示"暂无"

## 测试结果

171 passed, 4 skipped (LLM 集成，需 MINGRPG_RUN_LIVE=1)
