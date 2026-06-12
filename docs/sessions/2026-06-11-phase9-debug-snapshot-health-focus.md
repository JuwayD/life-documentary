# 2026-06-11 Phase 9 调试快照健康问题定位

## 本次目标

继续打磨 Phase 9 开发者控制台调试体验,实现最小切片:从快照健康校验结果直接定位问题快照。

## 完成内容

- 健康校验问题列表为每个问题快照新增“定位”按钮
- 点击定位后自动用问题快照 id 筛选快照列表
- 定位时自动显示归档快照,避免问题快照被默认隐藏
- 目标快照滚动到视野中并短暂高亮
- 新增 ADR-0093
- 补充 Playwright E2E 覆盖定位交互

## 验收方式

- 打开开发者控制台
- 创建两个同名测试快照
- 点击“校验快照”,确认报告展示重复命名问题
- 点击问题项“定位”,确认快照列表筛选为对应快照并显示匹配 1 条
- 运行相关测试:
  - `.venv/bin/pytest tests/web/test_e2e_browser.py::test_debug_console_exports_test_snapshot_health_report -q`
  - `.venv/bin/pytest tests/web/test_server.py::test_debug_test_snapshot_health_export_returns_shareable_report tests/web/test_server.py::test_debug_test_snapshot_health_reports_ok_and_problem_snapshots -q`
