# Phase 8: 演化面板增强

## 目标
优化世界演化面板信息展示,展示上次演化回合与距今回合数。

## 变更

### 前端 (app.js)
- `renderEvolutionsPanel` 增加 `last_evolved_turn` 展示
- 替换冗余"有备注/无备注"为"上次演化: 回合 N (X 回合前)"
- 通过 `flags.turn_index` 或 `events.length` 计算当前回合

### 测试 (test_e2e_browser.py)
- 新增 `test_evolutions_panel_shows_registered_entities` E2E 测试
- 验证演化面板展示已注册实体、频率标签、备注与回合信息

## 测试结果
83 E2E 测试全部通过(原 82 + 新增 1)。
