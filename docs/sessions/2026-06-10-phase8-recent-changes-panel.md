# 2026-06-10 Phase 8: 最近变化面板

## 本次目标

继续 Phase 8 信息展示优化。在复盘筛选匹配跳转之后，选择最小且可独立验收的后续切片：右栏增加“最近变化”面板，让玩家快速恢复最近事件、线索与压力钟上下文。

## 实现内容

- 在右栏“待处理重点”之后新增“最近变化”面板。
- 前端新增 `renderRecentPanel`，从当前 state 聚合：
  - 最新事件（summary/action_type/type + 回合信息）
  - 最新线索（clue + 来源/地点）
  - 当前最高压力钟（id + value/danger_at + 危险提示）
- 将 `recent` 纳入“局势”导航分组与折叠更新提示体系。
- 补充 `.recent-card` 等样式，保持与右栏现有纸面卡片风格一致。
- 补充 Playwright E2E 测试覆盖空状态与事件/线索/压力聚合展示。
- 新增 ADR-0057。
- 同步 README、docs/04-roadmap.md 与 .plan.md。

## 设计原则

- 只做前端展示层优化，不新增后端接口。
- 不改变世界状态、工具调用、审计日志或 GM 决策逻辑。
- 与“局势摘要/待处理重点”互补：最近变化强调“刚发生了什么”。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "recent_panel_summarizes_latest_changes" -q`

## 下一步

Phase 8 可继续沿“信息展示优化”推进。后续可考虑复盘与右栏更多交叉跳转、或进一步减少长会话恢复上下文的成本。
