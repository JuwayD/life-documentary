# 2026-06-09 Phase 8: 右栏面板折叠

## 本次目标

继续 Phase 8 信息展示优化,选择 roadmap 中最靠前且可独立验收的“优化信息展示”,实现最小安全垂直切片。

## 实现内容

- 右栏所有 `panel-section` 增加可点击标题按钮。
- 每个面板可独立折叠 / 展开。
- 折叠状态写入 `localStorage`,刷新页面后保持偏好。
- 默认全部展开,避免首次进入时隐藏信息。
- 补充 Playwright E2E 测试,验证折叠、`aria-expanded` 和刷新持久化。
- 新增 ADR-0025。

## 设计原则

- 只优化浏览器端信息展示,不改变世界状态、工具层、GM Agent 或审计日志。
- 不把折叠偏好写入存档,避免 UI 偏好污染可分享游戏状态。
- 保持现有面板内容渲染函数不变,只在外层添加展示控制。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -q` → 25 passed
- `.venv/bin/pytest tests -q` → 251 passed, 4 skipped

## 下一步

Phase 8 后续可继续追加小切片:重要信息摘要、面板分组置顶、线索/事件的更清晰筛选或减少大面板 DOM 重排。
