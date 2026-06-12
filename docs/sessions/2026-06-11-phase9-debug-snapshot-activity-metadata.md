# 2026-06-11 Phase 9 调试快照活动时间元数据

## 本次目标

继续打磨 Phase 9 开发者控制台调试体验,实现最小切片:让测试快照列表显示最近加载/导出/导入活动时间。

## 完成内容

- 测试快照加载时记录 `last_loaded_at`
- 单个测试快照导出时记录并返回 `last_exported_at`
- 单文件导入与快照包导入记录/返回 `last_imported_at`
- 快照列表/详情暴露活动时间元数据
- 前端快照行展示“加载 / 导出 / 导入”时间
- 导出单个快照后刷新开发者控制台列表
- 新增 ADR-0096
- 补充后端测试覆盖加载/导出活动时间

## 验收方式

- 打开开发者控制台并保存测试快照
- 点击“加载”并确认后,该快照行显示“加载 YYYY-MM-DD...Z”
- 点击“导出”,该快照行显示“导出 YYYY-MM-DD...Z”
- 导出的 JSON 中包含 `last_exported_at`
- 运行相关测试:
  - `.venv/bin/pytest tests/web/test_server.py::test_debug_test_snapshots_save_list_and_load_current_world tests/web/test_server.py::test_debug_test_snapshot_export_returns_shareable_snapshot_file -q`
