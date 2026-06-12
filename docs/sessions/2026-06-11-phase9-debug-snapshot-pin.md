# 2026-06-11 Phase 9 调试快照置顶

## 目标

继续打磨 Phase 9 调试体验，为常用测试快照增加置顶能力，减少回归盘面增多后的查找成本。

## 本次完成

- 快照元数据新增 `pinned` 字段，默认未置顶。
- `PATCH /api/debug/test-snapshots/{snapshot_id}` 支持置顶 / 取消置顶。
- 测试快照列表和前端排序保持置顶快照优先显示。
- 快照详情、索引导出、单个导出、复制、批量导入预览与导入均保留置顶元数据。
- 开发者控制台快照行新增“置顶 / 取消置顶”按钮和“置顶”徽标。
- 新增后端和 E2E 覆盖测试。

## 验证

- `.venv/bin/pytest tests/web/test_server.py -q` — 70 passed。
- `.venv/bin/pytest tests/web/test_e2e_browser.py::test_debug_console_pins_test_snapshot_first -q` — 1 passed。
