# 2026-06-11 Phase 8 关系面板历史 NPC

## 本次目标

实现关系面板历史 NPC 功能：展示曾互动但当前不在场的 NPC，帮助玩家回忆之前遇到的角色。

## 完成内容

- 修改 `renderRelationshipsPanel` 函数，将 NPC 分为"在场"和"曾互动"两组
- 添加 `findLocationName` 辅助函数，用于查找位置名称
- 添加 CSS 样式：
  - `.relationship-historical`：历史 NPC 卡片样式（左侧灰色边框、略微透明）
  - `.relationship-location`：位置提示样式（斜体灰色）
  - `.relationship-divider`：分隔线样式（虚线分隔带"曾互动"文字）
- 添加 E2E 测试 `test_relationships_panel_shows_historical_npcs`：
  - 先与顾问互动产生记忆
  - 移动顾问到其他位置
  - 验证"曾互动"分隔线出现
  - 验证历史 NPC 卡片显示正确信息

## 技术实现

历史 NPC 判断逻辑：
```javascript
const historical = allNpcs.filter((e) =>
  e.location !== player.location && (e.attributes?.memories?.length || 0) > 0
);
```

位置显示：
```javascript
const locationHint = isHistorical ? `<div class="relationship-location">当前在: ${escapeHtml(findLocationName(state, e.location) || "未知")}</div>` : "";
```

## 验收方式

- 运行关系面板测试：`.venv/bin/pytest tests/web/test_e2e_browser.py -k "relationship" -xvs`
- 运行完整测试套件：`.venv/bin/pytest tests/ -q`（387 passed, 1 failed pre-existing, 4 skipped）

## 测试总数

387 单元/E2E + 4 LLM 集成（可选 skip），新增 1 个测试。
