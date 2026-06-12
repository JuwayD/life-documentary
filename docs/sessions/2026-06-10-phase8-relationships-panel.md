# 2026-06-10 Phase 8: 关系动态面板

## 本次目标

继续 Phase 8 信息展示优化,补足在场 NPC 的关系/记忆可见性,让玩家更容易判断当前人际局势。

## 实现内容

- 右栏新增“关系动态”面板,位于“附近的人”之后。
- 新增前端渲染逻辑:
  - 展示在场 NPC 的姓名、身份。
  - 展示 `personality` 作为态度线索。
  - 展示最近一条 `memories` 互动记忆、记忆数量与重要度。
  - 无记忆时明确显示“尚无互动记忆”。
- 新增关系卡片样式。
- 补充 Playwright E2E 测试:
  - 初始场景显示王知府身份、态度线索、无互动记忆。
  - 请教刘师爷后,关系动态面板显示最近互动记忆。
- 新增 ADR-0030。

## 设计原则

- 只复用现有 `/api/state` 快照,不新增后端接口、工具或持久化字段。
- 前端只展示 NPC 既有资料和记忆,不推导好感、敌意或剧情后果。
- 保持最小垂直切片:HTML 容器、JS 渲染、CSS 样式、E2E 验收与文档同步。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "relationships_panel"` → 2 passed
- `.venv/bin/pytest tests/web -q` → 53 passed
- `.venv/bin/pytest -q` → 258 passed, 4 skipped

## 下一步

Phase 8 后续可继续优化信息展示,例如线索/事件筛选、面板内快速跳转,或减少大面板 DOM 重排。
