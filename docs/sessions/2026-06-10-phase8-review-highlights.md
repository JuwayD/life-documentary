# 2026-06-10 Phase 8: 复盘重点摘录

## 本次目标

继续 Phase 8 信息展示优化。在复盘统计摘要、筛选与右栏搜索结果之后，选择最小且可独立验收的后续切片：复盘重点摘录。

## 实现内容

- 完整复盘弹层顶部新增“重点摘录”。
- 自动摘录最近 3 个回合，按新到旧展示回合号、玩家行动短句与 GM 叙述短句。
- 长文本压缩为单行截断，详细内容仍保留在下方完整时间线。
- 补充响应式样式，窄屏下摘录卡片改为单列。
- 补充 Playwright E2E 测试，覆盖最近 3 回合摘录、不展示更早回合，以及与既有统计/筛选共存。
- 新增 ADR-0047。

## 设计原则

- 只改前端展示层，不引入新的后端接口。
- 复用 `/api/audit` 已有回合数据，保持审计来源单一。
- 摘录用于快速定位，不改变世界状态、AI 决策或导出的复盘文本。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "review_modal_shows_recent_highlights or review_modal_shows_summary_stats or review_modal_filters_turns_by_text" -q`

## 下一步

Phase 8 可继续沿“信息展示优化”推进，例如复盘中按回合类型分组、线索/事件跨面板联动，或进一步优化移动端复盘阅读。
