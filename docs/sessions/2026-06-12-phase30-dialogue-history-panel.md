# 会话日志: Phase 30 — 对话历史面板

**日期**: 2026-06-12
**目标**: 添加对话历史面板,展示对话记录时间线和态度变化趋势

## 完成内容

### 1. HTML 结构 (index.html)
- 在 dialogue-panel 后新增 dialogue-history-panel 面板区块
- 侧栏导航新增"对话"按钮(dialogue-history),位于剧情和调查之间
- 导航按钮显示对话次数徽标

### 2. 渲染函数 (app.js)
- `renderDialogueHistoryPanel(state)`: 对话历史面板主渲染函数
  - 从事件日志筛选 type="dialogue" 的事件
  - 构建态度历史(attitudeHistory),追踪每个NPC的态度值变化
  - 渲染对话统计摘要(对话总数、交谈NPC数量)
  - 渲染态度趋势面板(每个NPC的当前态度、趋势箭头、对话次数、最近话题)
  - 渲染最近对话时间线(最近5条对话的玩家台词和NPC回应)
- `renderSideNavBadges` 更新: 新增 dialogue-history 徽标,显示对话次数
- `renderSidePanel` 调用链更新: 新增 renderDialogueHistoryPanel 调用

### 3. CSS 样式 (style.css)
- `.dialogue-history-summary`: 统计摘要样式(flex布局)
- `.dialogue-history-attitudes`: 态度趋势容器
- `.dialogue-history-npc`: NPC态度卡片(背景、圆角)
- `.dialogue-history-npc-header`: NPC名称和态度标签
- `.dialogue-history-npc-stats`: 对话次数和最近话题
- `.dialogue-history-timeline`: 对话时间线容器
- `.dialogue-history-entry`: 对话条目(左边框 accent 色)
- `.dialogue-history-entry-header`: NPC标签、话题、态度变化
- `.dialogue-history-player`: 玩家台词(左边框灰色)
- `.dialogue-history-npc-response`: NPC回应(左边框 accent 色)
- `.dialogue-history-topic`: 话题标签(灰色背景)
- `.dialogue-history-attitude-delta`: 态度变化值(正/负颜色)

### 4. 测试验证
- 708+ 测试全部通过(1个flaky E2E测试单独运行通过)
- 无新增测试(前端面板为UI展示,复用现有事件数据)

## 设计决策

1. **数据来源**: 复用现有事件日志(type="dialogue"),无需新增后端工具或API
2. **态度追踪**: 从dialogue事件的attitude_delta字段累积计算当前态度值
3. **信息层级**: 摘要→态度趋势→最近对话,从宏观到微观
4. **导航位置**: 放在剧情和调查之间,符合"社交互动"的语义位置

## 文件变更

- `src/mingrpg/web/static/index.html`: 新增面板区块和导航按钮
- `src/mingrpg/web/static/app.js`: 新增渲染函数和导航徽标更新
- `src/mingrpg/web/static/style.css`: 新增对话历史面板样式
- `.plan.md`: 更新至 Phase 30
