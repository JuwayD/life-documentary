# 会话日志: Phase 34 对话面板增强

**日期**: 2026-06-12
**范围**: 前端对话历史面板增强

## 变更摘要

### app.js
- `renderAttitudeSparkline()` 增加 `large` 参数，支持 120x32 大尺寸折线图（含数据点圆圈和 hover tooltip）
- `renderDialogueHistoryPanel()` 新增：
  - 态度分布堆叠条形图（友善/中立/冷淡 NPC 计数）
  - 话题统计水平条形图（Top 5 话题按对话次数排序）
  - 搜索输入框（`data-searchable` 属性 + 实时过滤 + 匹配计数）
  - 导出按钮（Blob 生成 .txt 下载）
  - NPC 态度卡片升级为大 sparkline + 好感/恶感计数

### style.css
- 新增 15 个 Phase 34 CSS 类：
  - `.dialogue-history-npc-chart` — sparkline 容器
  - `.dialogue-history-att-dist*` — 态度分布条
  - `.dialogue-history-topic-stats*` — 话题统计条形图
  - `.dialogue-search-*` — 搜索输入框和计数
  - `.dialogue-export-btn` — 导出按钮

### test_server.py
- 4 个新测试：
  - `test_dialogue_events_have_searchable_text` — 验证玩家台词和 NPC 回应字段
  - `test_dialogue_attitude_distribution_data` — 验证态度分布计算
  - `test_dialogue_topic_statistics` — 验证话题统计计算
  - `test_dialogue_attitude_delta_present` — 验证态度变化值和对话内容

## 测试结果

- 92 个 web 测试全部通过
- 569 个单元测试通过（1 个 E2E 测试 flaky，独立运行通过）

## 文档

- ADR-0120
- .plan.md 更新
