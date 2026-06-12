# 2026-06-10 Phase 8: 移动端右栏信息入口

## 本次目标

继续 Phase 8 信息展示优化。根据路线中“继续优化信息展示”和上一会话建议，选择靠前且可独立验收的最小切片：移动端右栏信息入口。

## 实现内容

- 顶部操作区新增“状态面板”按钮：
  - 仅在 `max-width: 1000px` 窄屏显示。
  - 使用 `aria-controls="side-panel"` 与 `aria-expanded` 表达抽屉状态。
- 右栏新增 `id="side-panel"`，窄屏下改为从右侧滑出的抽屉。
- 新增遮罩 `#side-panel-backdrop`：
  - 抽屉打开时显示。
  - 点击后关闭抽屉。
- 桌面端三栏布局保持不变。
- 复用已有右栏内容、折叠状态、信息密度切换与导航，不新增后端接口或规则判断。
- 补充 Playwright E2E 测试：
  - 设置移动端 viewport。
  - 验证默认右栏不在视口内。
  - 点击“状态面板”后右栏进入视口。
  - 点击遮罩后右栏关闭。
- 新增 ADR-0034。

## 设计原则

- 只改前端展示层，不新增世界状态、工具或 GM Agent 规则。
- 复用原有 side-panel，避免维护第二套移动端信息 UI。
- 保持最小安全垂直切片：HTML 入口、JS 开关、CSS 响应式抽屉、E2E 验收、文档同步。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "mobile_side_panel_drawer or info_density or side_panel_sections" -q` → 3 passed

## 下一步

Phase 8 可继续沿“信息展示优化”推进，例如更细粒度的时间线摘要或移动端抽屉内的快速关闭/分组入口优化。
