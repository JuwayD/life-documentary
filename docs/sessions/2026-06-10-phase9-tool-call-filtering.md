# 2026-06-10 Phase 9: 工具调用筛选

## 本次目标

按 Phase 9 roadmap 推进“工具调用筛选”，在现有开发者控制台工具调用日志基础上实现最小可验收筛选能力。

## 实现内容

- 后端 `GET /api/debug/console` 新增筛选参数：
  - `tool`：按工具名精确筛选最近工具调用。
  - `q`：按工具调用 JSON 文本筛选输入/输出内容。
- 调试 API 返回筛选元信息：
  - `tool_names`：当前最近审计窗口内出现过的工具名列表。
  - `tool_filter` / `query`：当前筛选条件。
  - `filtered_tool_count`：筛选后的工具调用数量。
- 前端开发者控制台“工具调用日志”新增：
  - 工具名下拉筛选。
  - 输入/输出内容搜索框。
  - 清空筛选按钮。
  - 匹配数量摘要与空状态。
- 样式补充桌面与窄屏布局。

## 设计原则

- 保持调试工具定位：只过滤已有 audit 轨迹，不影响世界状态。
- 保持最小垂直切片：精确工具名 + 文本内容筛选，不引入复杂查询语言。
- 与现有测试快照/预设配合，方便快速定位特定局面的工具调用。

## 测试

- `tests/web/test_server.py::test_debug_console_endpoint_filters_tool_calls` passed
- `tests/web/test_e2e_browser.py::test_debug_console_filters_tool_calls` passed

## 下一步

Phase 9 可继续打磨调试体验，例如更长审计窗口、工具调用详情展开或失败调用标记。
