# 2026-06-10 Phase 8: 右栏导航当前分组高亮

## 本次目标

继续 Phase 8 信息展示优化。在移动端复盘阅读优化之后，选择最小且可独立验收的后续切片：让右栏导航持续标记当前查看的信息分组。

## 实现内容

- 右栏导航按钮新增 active 状态与 `aria-current`。
- 点击“局势 / 行动 / 剧情 / 复盘”导航时立即高亮对应分组。
- 监听右栏滚动，根据当前滚动位置同步高亮所属分组。
- 补充样式，让当前分组在导航条中更明显。
- 补充 Playwright E2E 测试覆盖导航高亮与 `aria-current`。
- 新增 ADR-0055。
- 同步 README、docs/04-roadmap.md 与 .plan.md。

## 设计原则

- 只做前端展示层优化，不新增后端接口。
- 不改变审计日志、世界状态、工具调用或 GM 决策。
- 复用既有导航分组映射，避免引入新的配置结构。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "side_nav_highlights_current_information_group" -q`

## 下一步

Phase 8 可继续沿“信息展示优化”推进，例如复盘筛选后的匹配跳转，或更多跨面板上下文联动。
