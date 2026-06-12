# 会话日志: 2026-06-10 — 调试快照差异预览

## 目标

在开发者控制台快照列表中加入差异预览能力，开发者不需要加载快照就能了解当前世界与快照的差异。

## 实现

**后端** (`src/mingrpg/web/server.py`):
- 新增 `GET /api/debug/test-snapshots/{snapshot_id}/diff` 端点
- `_debug_snapshot_diff` 对比当前世界 `export_save` 与快照 `save` 中实体的增删改、地点的增删改、flag 的增删改，以及事件/时间是否改变
- `_diff_record_lists` / `_diff_flags` / `_stable_json` 三个辅助函数

**前端** (`src/mingrpg/web/static/app.js`):
- `renderDebugTestSnapshotRow` 增加"差异"按钮和差异预览区域
- 新增 `renderDebugSnapshotDiff` / `renderDebugDiffList` 渲染函数
- 新增 `loadDebugSnapshotDiff` 异步切换 diff 预览状态
- `refreshDebugConsole` 清理已删除快照的缓存 diff

**CSS** (`src/mingrpg/web/static/style.css`):
- `.debug-snapshot-diff` / `.debug-snapshot-actions` 样式

**测试** (`tests/web/test_server.py`):
- `test_debug_test_snapshot_diff_previews_changes_before_load` — 保存快照→改世界→diff 预览
- `test_debug_test_snapshot_diff_404_for_unknown` — 未知快照 ID 返回 404

## 测试结果

317 单元/E2E 全过, 4 LLM 集成(可选 skip)