# 2026-06-10 Phase 8: 线索事件联动

## 本次目标

继续 Phase 8 信息展示优化。在复盘筛选空状态清空入口之后，选择最小且可独立验收的后续切片：线索与事件时间线的跨面板联动。

## 实现内容

- 线索卡片新增“查看事件”按钮。
- 前端基于现有 `state.events` 中的 `record_clue` 事件，将线索与对应事件关联。
- 点击后自动将事件时间线筛选恢复为“全部”，展开并聚焦事件时间线面板，高亮对应事件。
- 事件时间线卡片新增 `data-event-id`，用于前端定位。
- 补充 Playwright E2E 测试覆盖线索按钮跳转与事件高亮。
- 新增 ADR-0052。
- 同步 README、docs/04-roadmap.md 与 .plan.md。

## 设计原则

- 只做前端展示层联动，不新增后端接口。
- 不改变世界状态、工具调用、审计日志或 GM 决策。
- 如果对应事件不在当前快照中，线索仍正常显示，只是不展示跳转入口。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "clues_panel_updates_after_clue_input or clue_event_link_focuses_timeline_event or timeline_filters_events_by_type" -q`

## 下一步

Phase 8 可继续沿“信息展示优化”推进，例如移动端复盘阅读优化，或压力钟/行动建议的联动提示。
