# 2026-06-10 Phase 8: 时间线类型图例

## 本次目标

继续 Phase 8 信息展示优化。选择最小且可独立验收的后续切片：让事件时间线直接解释“剧情/社交/战斗/交易/其他”这些类型标签与筛选的含义。

## 实现内容

- 前端事件时间线新增类型图例，位于时间线摘要与筛选按钮之间。
- 图例覆盖 5 类事件：
  - 剧情：线索、结局与主线推进。
  - 社交：请教、交谈与人物互动。
  - 战斗：攻击、受伤与战斗后果。
  - 交易：买卖、雇佣与钱物变化。
  - 其他：移动、观察及未归类记录。
- 新增 `renderTimelineLegend`，复用既有类型标签体系。
- 增加 `.timeline-legend` 与类型圆点样式，保持右栏信息密度轻量。
- 补充 Playwright E2E 测试，验证图例可见且包含关键说明。
- 新增 ADR-0060。

## 设计原则

- 只解释已有分类，不新增规则来源。
- 只改前端展示层，不影响世界状态、工具调用或 AI 决策。
- 图例服务于首次理解与扫读，不替代筛选按钮和事件卡片。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k 'timeline_legend_explains_event_types or timeline_groups_events_by_turn or timeline_filters_events_by_type'`

## 下一步

Phase 8 可继续沿“信息展示优化”推进，例如进一步优化复盘阅读、线索关系聚合或时间线定位能力。
