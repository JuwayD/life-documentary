# 2026-06-11 Phase 9 调试快照健康报告导出

## 本次目标

继续打磨 Phase 9 开发者控制台调试体验,实现最小切片:调试快照健康报告导出。

## 完成内容

- `GET /api/debug/test-snapshots/health/export` 导出健康校验 JSON
- 导出报告包含 `format`、`version`、`exported_at` 与健康校验统计/问题列表
- 开发者控制台新增“导出校验报告”按钮
- 导出时刷新并展示当前健康校验结果
- 复用既有健康校验逻辑,不自动修复、不删除、不加载快照
- 新增 ADR-0092
- 补充 FastAPI 单元测试与 Playwright E2E 覆盖

## 验收方式

- 打开开发者控制台
- 创建两个同名测试快照
- 点击“校验快照”,确认报告展示重复命名问题
- 点击“导出校验报告”,下载 `mingrpg-test-snapshot-health-*.json`
- 运行相关测试:
  - `.venv/bin/pytest tests/web/test_server.py::test_debug_test_snapshot_health_export_returns_shareable_report -q`
  - `.venv/bin/pytest tests/web/test_e2e_browser.py::test_debug_console_exports_test_snapshot_health_report -q`
