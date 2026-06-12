# 2026-06-10 Phase 8: 时间线组内类型摘要

## 本次目标

继续 Phase 8 信息展示优化。在时间线回合分组基础上，选择最小且可独立验收的后续切片：让每个时间线分组直接显示组内事件数量与类型构成。

## 实现内容

- 前端事件时间线分组标题新增右侧摘要：
  - 展示分组内总事件数。
  - 展示剧情/社交/战斗/交易/其他的类型计数。
  - 示例：“2件 · 剧情2”“3件 · 剧情2 / 社交1”。
- 摘要基于当前筛选后的可见事件计算，切换类型筛选后自动收敛到剩余事件。
- 新增 `summarizeTimelineGroups`，复用既有时间线类型识别和标签。
- 调整 `.timeline-group` 样式为左右布局，保留虚线分隔。
- 补充 Playwright E2E 测试：
  - 验证回合分组显示组内摘要。
  - 验证筛选后摘要随可见事件重新计算。
- 新增 ADR-0059。

## 设计原则

- 只改前端展示层，不新增 AI 决策逻辑。
- 复用已有事件类型体系，避免引入新的规则来源。
- 摘要服务于扫读，不替代事件卡片细节。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k 'timeline_groups_events_by_turn or timeline_summary_shows_filtered_count_and_dominant_type or timeline_filters_events_by_type'`

## 下一步

Phase 8 可继续沿“信息展示优化”推进，例如进一步优化复盘阅读、关系/线索聚合视图或时间线细节定位。
