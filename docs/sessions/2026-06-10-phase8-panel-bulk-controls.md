# 2026-06-10 Phase 8: 面板批量展开/折叠

## 本次目标

继续 Phase 8 信息展示优化。在已有右栏折叠、密度切换和搜索能力基础上，选择最小且可独立验收的后续切片：面板批量展开/折叠。

## 实现内容

- 前端右栏新增批量控制：
  - “全部展开”按钮。
  - “全部折叠”按钮。
- 新增 `setPanelCollapsed` helper：
  - 同步面板 `collapsed` class。
  - 同步对应 toggle 的 `aria-expanded`。
  - 复用于单面板折叠、侧栏导航自动展开和批量控制。
- 批量控制复用现有 `mingrpg.panelCollapsed` localStorage 持久化，刷新后保留批量结果。
- 新增样式 `panel-bulk-controls`，沿用右栏按钮的纸面/朱砂风格。
- 补充 Playwright E2E 测试：
  - 点击“全部折叠”后多个面板隐藏。
  - 刷新后仍保持折叠。
  - 点击“全部展开”后面板恢复可见。
- 新增 ADR-0037。

## 设计原则

- 只改前端展示层，不新增世界状态、工具或 GM Agent 规则。
- 复用现有单面板折叠持久化键，避免引入第二套状态来源。
- 批量控制覆盖单面板偏好，符合玩家主动批量操作的语义。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "bulk_controls or collapse" -q` → 3 passed

## 下一步

Phase 8 可继续沿“信息展示优化”推进，例如面板搜索快捷键、移动端抽屉内快速关闭体验，或时间线摘要。
