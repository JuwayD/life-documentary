# 会话日志: Phase 35 — 线索关联图可视化

## 目标

在线索面板（`renderCluesPanel`）顶部增加 SVG 线索关联图，可视化线索、来源 NPC、地点之间的连接关系。

## 变更清单

### 前端 (app.js)

- 新增 `CLUE_GRAPH_COLORS` 常量（7 种线程颜色）
- 新增 `buildClueGraph(progress, threadNames)` — 从 `story_progress` 数据构建图形节点和边
- 新增 `renderClueGraphSvg(graph)` — 生成 SVG 图形 HTML
- 扩展 `renderCluesPanel` — 在摘要条和线程列表之间插入可折叠关联图
- 新增折叠/展开交互（点击"关联图"按钮切换显示）

### 样式 (style.css)

- 新增 `.clue-graph` / `.clue-graph-toggle` / `.clue-graph-body` / `.clue-graph-svg` 等样式
- 风格与现有线索面板一致（纸张色背景、边框、朱砂色标题）

### 测试 (test_server.py)

- `test_clue_graph_data_supports_multi_thread` — 多线程线索数据结构验证
- `test_clue_graph_entity_location_edges` — 实体/地点关联边提取验证
- `test_clue_graph_empty_progress_returns_no_data` — 空线索状态返回 null

### 文档

- ADR-0121 + 本会话日志

## 测试结果

- 95 个 web 测试通过（含 3 个新增）
- 657 个非 E2E 测试全部通过
- 1 个 E2E 测试 (`test_suggestions_panel_shows_contextual_actions`) 为已有 flaky test，单独运行通过
