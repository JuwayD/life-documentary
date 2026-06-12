# ADR-0012: Phase 6 Step 1 — 前端剧情面板

- **状态**: Accepted
- **日期**: 2026-06-09
- **关联**: docs/04-roadmap.md (Phase 6)

## 背景

Phase 5B/C 已提供 `story_progress`、`pressure_clocks`、`story_seeds` 三个 flag 存储剧情数据，但这些数据在前端仅以 raw JSON 展示在"剧情标记"面板中，可读性差，无法直观呈现故事脉络与紧迫感。

## 决策

### 1. 拆分剧情标记面板

将原有的 `#flags-panel` raw JSON 区域替换为 3 个独立的结构化面板：

- **`#story-panel`** — 主线剧情概览（标题 + 前提 + 当前线索数）
- **`#clues-panel`** — 线索记录（按 thread 分组，显示每条线索的来源、地点、证据）
- **`#pressure-panel`** — 压力钟（可视化进度条，危险线标记，颜色从绿色→橙色→红色渐变）

### 2. 渲染逻辑 (app.js)

在 `renderSidePanel()` 中依次调用：

- `renderStoryPanel(state)` — 从 `flags.story_seeds` 提取 main_thread 和 side_threads，同时读取 `flags.story_progress` 计算累计线索数
- `renderCluesPanel(state)` — 从 `flags.story_progress` 提取线索，按 thread 分组渲染
- `renderPressurePanel(state)` — 从 `flags.pressure_clocks` 提取时钟，渲染进度条

空数据时显示 `<em>暂无</em>` 兜底。

### 3. CSS 样式 (style.css)

新增样式类：

- `.story-thread` / `.side-thread` — 故事线程标题行
- `.clue-card` — 线索卡片（来源、地点、证据元信息行）
- `.pressure-bar .fill` — 压力钟进度条（safe/warn/danger 三档颜色）
- `.thread-group-title` — 线索分组标题

### 4. 测试覆盖

- **E2E** (`test_e2e_browser.py`): FakeAgent 在检测到"线索"关键词时调用 `record_clue`，检测到"压力"关键词时调用 `advance_pressure_clock`，然后 Playwright 断言对应面板出现内容
- **Server** (`test_server.py`): 验证快照中包含 `story_seeds`、`story_progress`、`pressure_clocks` 三个 flag

### 5. 移除 raw flags 面板

`#flags-panel` 及其在 `renderSidePanel()` 中的 raw JSON 渲染已移除。

## 不引入

- ❌ 后端 API 变更（数据已就绪）
- ❌ 新工具
- ❌ 顾问系统 / 观察系统（后续 Step）
- ❌ 多角色 / 修炼 / 存档（远期）

## 后果

### 正面

- ✓ 剧情状态对玩家可读、可理解
- ✓ 压力钟进度条提供直观紧迫感
- ✓ 线索按 thread 分组，方便追踪多个支线
- ✓ 纯前端改动，不影响任何后端逻辑或测试

### 负面

- ✗ 增加了前端渲染复杂度
  - **对策**: 保持 Vanilla JS，不引入框架