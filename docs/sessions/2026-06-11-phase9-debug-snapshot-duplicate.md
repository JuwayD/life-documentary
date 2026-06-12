# 2026-06-11 Phase 9 调试快照复制

## 目标

继续打磨 Phase 9 调试体验，为测试快照增加复制能力，方便从稳定盘面派生多个回归快照。

## 本次完成

- 新增 `POST /api/debug/test-snapshots/{snapshot_id}/duplicate`。
- 复制快照时保留源快照 `save` 内容、备注和标签，并生成新的 id / created_at / updated_at。
- 支持复制时覆盖名称、备注、标签，并保留 `duplicated_from` 来源信息。
- 开发者控制台快照行新增“复制”按钮，复制后刷新列表并显示系统提示。
- 新增后端和 E2E 覆盖测试。

## 验证

- `.venv/bin/pytest tests/web/test_server.py -q` — 69 passed。
- `.venv/bin/pytest tests/web/test_e2e_browser.py::test_debug_console_duplicates_test_snapshot -q` — 1 passed。
