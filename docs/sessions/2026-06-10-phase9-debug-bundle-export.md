# 2026-06-10 Phase 9: 调试包导出

## 本次目标

按 Phase 9 “调试体验继续打磨”推进一个最小可验收切片：开发者控制台支持导出当前调试包，便于保存问题现场与工具调用证据。

## 实现内容

- 后端新增 `GET /api/debug/export`：
  - 复用 `GET /api/debug/console` 的聚合数据。
  - 保留当前 `tool` / `q` 筛选条件与筛选后的工具调用。
  - 增加 `format`、`version`、`exported_at` 元数据。
- 前端开发者控制台新增导出区域：
  - “导出调试包”按钮。
  - 说明导出内容包含世界摘要、实体/flag、筛选后的工具调用与性能指标。
  - 点击后下载本地 JSON 文件，不上传到外部服务。
- 样式补充导出区域的独立展示。

## 设计原则

- 保持只读调试能力：导出不改变世界状态、审计日志或测试快照。
- 保持本地优先：只下载 JSON，不生成外链、不依赖外部凭据。
- 复用现有控制台筛选逻辑，避免新增复杂查询规则。

## 测试

- `tests/web/test_server.py::test_debug_console_export_returns_filtered_debug_bundle` passed
- `tests/web/test_server.py::test_debug_console_endpoint_filters_tool_calls` passed
- `tests/web/test_e2e_browser.py::test_debug_console_exports_filtered_debug_bundle` passed

## 下一步

Phase 9 可继续打磨调试体验，例如更长审计窗口、工具调用详情展开或失败调用标记。
