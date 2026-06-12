# 会话日志: 2026-06-10 — 调试工具调用 JSON 复制

## 目标

开发者控制台工具调用日志增加输入/输出 JSON 一键复制能力，排查工具副作用或分享调试片段时减少手动选中文本成本。

## 实现

**前端** (`src/mingrpg/web/static/app.js`):
- 工具调用卡片的“输入 / 输出”标签改为标签行
- 每段 JSON 增加“复制输入 / 复制输出”按钮
- 点击按钮后调用统一 `copyText`，优先使用 `navigator.clipboard.writeText`，必要时回退到隐藏 textarea 复制，并显示“已复制输入/输出”反馈

**样式** (`src/mingrpg/web/static/style.css`):
- 新增 `.debug-tool-label-row` 和按钮样式
- 保持原有输入/输出 JSON 展示结构不变

**后端**: 无改动 — 复用已有 `/api/debug/console` 的 `recent_tool_calls[].input/output`

**测试** (`tests/web/test_e2e_browser.py`):
- `test_debug_console_modal_shows_world_tools_and_performance` 增加复制按钮可见断言
- 点击“复制输出”后断言按钮反馈为“已复制输出”

## 测试结果

- 相关测试通过：`tests/web/test_e2e_browser.py -k debug_console_modal_shows_world_tools_and_performance`
