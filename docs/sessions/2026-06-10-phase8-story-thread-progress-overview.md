# 2026-06-10 Phase 8: 线索线程进度概览

## 本次目标

按 Phase 8 “继续优化信息展示”推进一个最小可验收切片：在主线剧情面板中补充线索线程进度概览，让玩家快速判断主线/支线线索分布。

## 实现内容

- 前端主线剧情面板新增 `story-progress-overview`：
  - 展示线索总数。
  - 展示活跃线程 / 全部线程。
  - 展示未触发线程数。
- 已有线索时新增线程进度列表：
  - 按线索数量展示当前最活跃线程。
  - 详细模式最多显示 4 个，精简模式最多显示 2 个。
- 样式补充概览卡片与线程进度行。
- 新增 E2E 覆盖：验证初始无进度、记录线索后显示主线/支线线程进度。

## 设计原则

- 只读取 `story_seeds` / `story_progress`，不新增状态字段。
- 不判断任务是否完成，不改变 GM Agent、工具层或审计日志。
- 作为 Phase 8 信息展示增强，保持轻量、可独立验收。

## 测试

- `tests/web/test_e2e_browser.py::test_story_panel_shows_thread_progress_overview` passed
- `tests/web/test_e2e_browser.py::test_story_panel_shows_main_thread` passed
- `tests/web/test_e2e_browser.py::test_clues_panel_updates_after_clue_input` passed

## 下一步

Phase 8 可继续打磨信息展示，例如剧情线程筛选、支线分组折叠或线索密度提示。
