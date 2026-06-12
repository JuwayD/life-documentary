# 2026-06-10 Phase 8: 右栏导航目标高亮

## 本次目标

继续 Phase 8 信息展示优化,补强右栏导航的跳转反馈。玩家点击粘性导航跳到目标面板后,目标面板应短暂高亮,降低在密集信息栏中的定位成本。

## 实现内容

- 右栏导航点击逻辑增强:
  - 自动展开目标面板保持不变。
  - 移除其他面板的旧高亮。
  - 为目标面板添加 `focused` 状态。
  - 1.6 秒后自动移除高亮。
- 新增 `panel-section.focused` 样式:
  - 浅金色背景。
  - 左侧金色内阴影定位标记。
  - 保持与现有明代纸质风格一致。
- 补充 Playwright E2E 测试:
  - 验证导航跳转会展开已折叠目标面板。
  - 验证目标面板获得 `focused` 高亮状态。
- 新增 ADR-0032。

## 设计原则

- 只做展示层反馈,不修改后端、世界状态或 GM Agent 工具。
- 不持久化高亮状态,避免与面板折叠偏好混淆。
- 保持最小垂直切片:JS 行为、CSS 样式、E2E 验收与文档同步。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "side_nav_reopens or side_nav_badges" -q` → 2 passed
- `.venv/bin/pytest tests/web -q` → 54 passed
- `.venv/bin/pytest -q` → 259 passed, 4 skipped

## 下一步

Phase 8 后续可继续优化信息展示,例如减少大面板 DOM 重排,或提升移动端信息展示。
