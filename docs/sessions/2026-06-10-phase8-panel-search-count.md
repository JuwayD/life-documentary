# 2026-06-10 Phase 8: 右栏搜索命中数量

## 本次目标

继续 Phase 8 信息展示优化。在已有右栏搜索和命中高亮基础上，选择最小且可独立验收的后续切片：搜索命中数量。

## 实现内容

- 右栏搜索框下方新增命中数量提示：
  - 默认显示当前总面板数。
  - 输入搜索词后显示匹配面板数与总面板数。
  - 无匹配时保留既有“无匹配面板”提示。
- 前端 `applyPanelSearch` 在已有筛选遍历中同步计算 `matched/total`，避免额外 DOM 扫描。
- 新增紧凑样式 `.panel-search-count`，与现有搜索空状态视觉保持一致。
- 补充 Playwright E2E 测试，覆盖默认总数、搜索命中、无匹配和清空搜索后的提示。
- 新增 ADR-0043。

## 设计原则

- 只改前端展示层，不新增 AI 决策逻辑。
- 复用已有搜索逻辑，避免引入新的匹配规则。
- 命中数量是辅助信息，不改变面板折叠、导航或搜索高亮行为。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "panel_search_filters_sections_by_content or panel_search_highlights_matching_text" -q`

## 下一步

Phase 8 可继续沿“信息展示优化”推进，例如复盘筛选体验或更细的关系/事件摘要。
