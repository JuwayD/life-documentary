# 2026-06-11 Phase 9 调试快照标签管理

## 目标

继续打磨 Phase 9 调试体验，为测试快照增加轻量标签，方便大量复现盘面归类、筛选和分享。

## 本次完成

- 后端测试快照元数据新增 `tags` 字段。
- 创建 / 更新快照支持标签归一化与去重。
- 快照列表、详情、单个导出、索引导出、批量导入预览、批量导入结果保留标签。
- 前端开发者控制台新增标签输入框、标签胶囊展示、按标签筛选下拉框。
- 快照文本筛选同时匹配标签内容。
- 新增后端和 E2E 覆盖测试。

## 验证

- `.venv/bin/pytest tests/web/test_server.py -q` — 65 passed。
- `.venv/bin/pytest tests/web/test_e2e_browser.py::test_debug_console_filters_tool_calls -q` — 1 passed。
- `.venv/bin/pytest tests/web/test_e2e_browser.py::test_debug_console_manages_test_snapshot_tags -q` — 1 passed。

说明：全量 `tests/web/test_e2e_browser.py -q` 曾出现一次既有工具筛选用例异步刷新竞态失败；复跑该用例通过，新增标签用例通过。
