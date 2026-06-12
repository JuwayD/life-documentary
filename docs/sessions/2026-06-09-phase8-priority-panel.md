# 2026-06-09 Phase 8: 待处理重点面板

## 本次目标

继续 Phase 8 信息展示优化,在已有局势摘要与右栏导航基础上,把最值得注意的信息聚合到右栏顶部。

## 实现内容

- 右栏新增“待处理重点”面板,位于局势摘要之后。
- 新增前端聚合渲染逻辑:
  - 高压力钟显示为重点事项。
  - 最新线索单独提示。
  - 最新事件单独提示。
  - 基于当前快照显示一条下一步建议摘要。
- 新增重点卡片样式,按压力、线索、事件、建议区分左侧色条。
- 补充 Playwright E2E 测试,验证压力/线索/事件/建议可在同一面板中看到。
- 新增 ADR-0029。

## 设计原则

- 只使用现有 `/api/state` 快照,不新增后端接口或持久化字段。
- 前端只做信息聚合和展示优先级,不替 GM Agent 判断剧情后果。
- 保持最小垂直切片:HTML 容器、JS 渲染、CSS 样式、E2E 验收与文档同步。

## 测试

- `.venv/bin/python -m pytest tests/web/test_e2e_browser.py -x -v -k "priority_panel or summary_panel or side_nav_badges"` → 4 passed
- `.venv/bin/python -m pytest tests/web -q` → 51 passed

## 下一步

Phase 8 后续可继续做线索/事件筛选、面板内快速跳转,或减少大面板 DOM 重排。
