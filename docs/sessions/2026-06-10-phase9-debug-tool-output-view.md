# 会话日志: 2026-06-10 — 调试工具调用输出查看

## 目标

开发者控制台工具调用日志增加输出展示，排查工具副作用时直接对照输入与结果，减少切换审计 JSON 的成本。

## 实现

**前端** (`src/mingrpg/web/static/app.js`):
- 工具调用卡片拆分为“输入 / 输出”上下两段 `<pre>`，标记 `data-test="debug-tool-input"` / `data-test="debug-tool-output"`
- 输入输出前加 `<label>` 标签

**样式** (`src/mingrpg/web/static/style.css`):
- 新增 `.debug-tool-call label` 样式（金色标签，轻量视觉层级）

**后端**: 无改动 — 复用已有 `/api/debug/console` 的 `recent_tool_calls[].output`

**测试** (`tests/web/test_server.py`):
- `test_debug_console_endpoint_returns_world_audit_and_performance` 新增 output 断言：检查 `log_event` 的输出事件摘要

**测试** (`tests/web/test_e2e_browser.py`):
- `test_debug_console_modal_shows_world_tools_and_performance` 新增浏览器断言：标签“输入”“输出”以及输出内容

## 测试结果

- 相关测试通过：`tests/web/test_server.py`、`tests/web/test_e2e_browser.py -k debug_console_modal_shows_world_tools_and_performance`
- 全量测试通过：322 passed, 4 skipped