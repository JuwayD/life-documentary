# 2026-06-10 Phase 8: 移动端复盘阅读优化

## 本次目标

继续 Phase 8 信息展示优化。在压力钟行动联动之后，选择最小且可独立验收的后续切片：移动端长复盘阅读体验。

## 实现内容

- 完整复盘操作区新增“跳到最新”按钮。
- 点击按钮滚动到复盘列表最后一个回合，便于从摘要快速回到最近进展。
- 窄屏下复盘弹层全屏化，减少可视区域浪费。
- 窄屏下复盘操作区改为粘性显示，并允许按钮换行。
- 补充 Playwright E2E 测试覆盖移动端“跳到最新”行为。
- 新增 ADR-0054。
- 同步 README、docs/04-roadmap.md 与 .plan.md。

## 设计原则

- 只做前端展示层优化，不新增后端接口。
- 不改变审计日志、世界状态、工具调用或 GM 决策。
- 保持桌面端复盘结构不变，仅增加快捷入口。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "review_modal_shows_recent_highlights or review_modal_jump_latest_scrolls_to_recent_turn" -q`

## 下一步

Phase 8 可继续沿“信息展示优化”推进，例如复盘筛选后的跳转定位，或更多跨面板上下文联动。
