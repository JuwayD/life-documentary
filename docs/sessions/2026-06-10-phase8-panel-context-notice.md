# 2026-06-10 Phase 8: 右栏上下文提示条

## 本次目标

继续 Phase 8 信息展示优化。在右栏搜索、搜索结果和折叠提示之后，选择最小且可独立验收的后续切片：右栏上下文提示条。

## 实现内容

- 在右栏搜索区下方新增上下文提示条。
- 搜索隐藏面板时显示“搜索已隐藏 X/Y 个面板”。
- 存在折叠面板时显示“X 个面板已折叠”。
- 提供“清除搜索”和“全部展开”两个就地恢复入口。
- 复用既有 `data-panel-section`、折叠状态和搜索状态，不新增后端接口。
- 补充 Playwright E2E 测试，覆盖搜索隐藏提示、清除搜索、折叠提示与全部展开。
- 新增 ADR-0048。

## 设计原则

- 只改前端展示层，不引入新的游戏规则判断。
- 提示条只解释当前 UI 状态，不改变世界状态或 AI 决策。
- 恢复入口靠近搜索/筛选控件，降低信息被隐藏后的迷失感。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "panel_context_notice or panel_search_filters_sections_by_content or side_panel_bulk_controls_expand_and_collapse_all"`

## 下一步

Phase 8 可继续沿“信息展示优化”推进，例如复盘中按回合类型分组、线索/事件跨面板联动，或进一步优化移动端复盘阅读。
