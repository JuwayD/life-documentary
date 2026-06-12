# 2026-06-10 Phase 9: 开发者控制台最小切片

## 本次目标

按 Phase 9 roadmap 继续推进“开发者控制台”，实现可独立验收的最小切片：世界状态查看器、工具调用日志、性能监控面板。

## 实现内容

- 后端新增 `GET /api/debug/console?limit=`：
  - 聚合当前世界快照中的实体/地点/事件窗口/flag 数量。
  - 返回玩家实体与当前位置，便于快速判断测试场景。
  - 读取审计 JSONL，统计总回合数并提取最近工具调用。
  - 返回轻量性能指标：审计日志字节数、快照事件窗口大小。
- 前端顶部新增“开发者控制台”按钮。
- 新增开发者控制台弹层，包含：
  - 世界状态查看器。
  - 工具调用日志。
  - 性能监控。
- 样式复用现有纸质风格弹层，不引入新的交互框架。

## 设计原则

- 只读调试入口，不允许修改世界状态、删除日志或执行工具。
- 复用 `/api/state` 和审计日志数据，不改变 GM Agent 决策路径。
- 控制台做概览，既有“查看日志”继续承担完整审计阅读。
- 工具调用只展示近期窗口，避免 UI 一次性渲染过大日志。

## 测试

- `tests/web/test_server.py::test_debug_console_endpoint_returns_world_audit_and_performance`
- `tests/web/test_e2e_browser.py::test_debug_console_modal_shows_world_tools_and_performance[chromium]`

## 下一步

Phase 9 可继续扩展开发者控制台：更细的实体/flag 浏览、工具调用筛选，或推进“测试场景快照”。
