# 2026-06-10 Phase 8: 搜索命中高亮

## 本次目标

继续 Phase 8 信息展示优化。在 ADR-0035 右栏面板搜索筛选之后，选择最小且可独立验收的后续切片：搜索命中高亮。

## 实现内容

- 前端搜索筛选新增命中高亮：
  - `applyPanelSearch` 在匹配面板内调用高亮逻辑。
  - `clearPanelSearchHighlights` 在重新搜索前移除旧高亮。
  - `highlightPanelSearchMatches` 遍历文本节点并定位匹配。
  - `highlightTextNode` 将匹配片段包裹为 `mark.panel-search-highlight`。
- 新增样式：`panel-search-highlight` 使用浅金色背景突出命中词。
- 补充 Playwright E2E 测试：
  - 搜索“线索”后出现可见高亮。
  - 清空搜索后高亮全部移除。
- 新增 ADR-0036。

## 设计原则

- 只改前端展示层，不新增世界状态、工具或 GM Agent 规则。
- 保留 ADR-0035 的本地 DOM 搜索策略，不引入索引或后端查询。
- 高亮逻辑在每次应用搜索前先清理旧标记，避免重复嵌套。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "panel_search" -q` → 2 passed

## 下一步

Phase 8 可继续沿“信息展示优化”推进，例如时间线摘要、移动端抽屉内快速关闭体验，或面板搜索快捷键。
