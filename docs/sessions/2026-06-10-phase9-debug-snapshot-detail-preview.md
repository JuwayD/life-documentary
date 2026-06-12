# 会话日志: 2026-06-10 — 调试快照详情预览

## 目标

开发者控制台支持在加载测试快照前预览快照内容，避免调试多个相似盘面时只能依赖名称、计数或直接加载确认。

## 实现

**后端** (`src/mingrpg/web/server.py`):
- 新增 `GET /api/debug/test-snapshots/{id}` 只读详情端点
- 返回快照元数据、实体/地点/事件/Flag 计数、Flag 键列表、玩家、当前位置和最近 5 条事件
- 未找到快照时返回 404

**前端** (`src/mingrpg/web/static/app.js`):
- 测试快照列表新增“详情”按钮
- 点击后展开/收起详情预览，展示玩家位置、计数、Flag 和最近事件
- 快照加载、删除、元数据更新时清理详情缓存

**样式** (`src/mingrpg/web/static/style.css`):
- 详情预览复用调试快照卡片中的浅色说明块样式

**测试**:
- `tests/web/test_server.py` 覆盖详情端点内容与 404
- `tests/web/test_e2e_browser.py` 覆盖控制台详情按钮与预览内容

## 测试结果

- 相关后端测试通过：`tests/web/test_server.py -k 'debug_test_snapshot_detail or debug_test_snapshot_update or debug_test_snapshot_delete or debug_test_snapshot_diff'`
- 相关 E2E 测试通过：`tests/web/test_e2e_browser.py -k 'debug_console_previews_test_snapshot_detail'`
- Python 编译检查通过：`python -m compileall src/mingrpg/web/server.py`
- JS 语法检查因环境未安装 `node` 跳过
