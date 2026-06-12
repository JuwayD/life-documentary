# 2026-06-10 Phase 8: 右栏快捷键提示

## 本次目标

继续 Phase 8 信息展示优化。在右栏搜索、搜索结果、上下文提示条之后，选择最小且可独立验收的后续切片：右栏快捷键提示。

## 实现内容

- 右栏搜索区下方新增“快捷键”提示块。
- 静态展示 `⌘/Ctrl + K` 搜索面板与 `Enter` 提交行动。
- 补充样式，使提示块与既有纸质风格和右栏密度一致。
- 补充 Playwright E2E 测试，覆盖提示块可见与快捷键文案。
- 新增 ADR-0049。
- 同步 README、docs/04-roadmap.md 与 .plan.md。

## 设计原则

- 只改前端说明层，不新增后端接口。
- 不改变世界状态、工具调用或 GM 决策。
- 让已存在的快捷操作更容易被玩家发现。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "keyboard_help_lists_available_shortcuts or panel_search_keyboard_shortcut_focuses_search" -q`

## 下一步

Phase 8 可继续沿“信息展示优化”推进，例如复盘中按回合类型分组、线索/事件跨面板联动，或进一步优化移动端复盘阅读。
