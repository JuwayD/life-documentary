# 2026-06-10 Phase 8: 压力钟行动联动

## 本次目标

继续 Phase 8 信息展示优化。在线索事件联动之后，选择最小且可独立验收的后续切片：高压力钟与行动建议之间的联动入口。

## 实现内容

- 压力钟达到半数危险线时显示“应对行动”按钮。
- 按压力比例生成自然语言行动文案：半数以上为“需要尽快处理”，接近危险线为“当务之急”。
- 点击按钮直接提交行动，让 GM 处理对应压力钟的线索梳理、关键人物安抚与局势降温。
- 新增压力钟行动按钮样式。
- 补充 Playwright E2E 测试覆盖按钮显示与点击提交。
- 新增 ADR-0053。
- 同步 README、docs/04-roadmap.md 与 .plan.md。

## 设计原则

- 只做前端展示层联动，不新增后端接口。
- 不在代码中判断压力钟是否应降温；实际处理仍由 GM Agent 决策。
- 低压力钟不显示行动按钮，避免把普通状态误导为紧急任务。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -k "pressure_panel_updates_after_pressure_input or pressure_clock_action_button_sends_response_turn or priority_panel_surfaces_actionable_items" -q`

## 下一步

Phase 8 可继续沿“信息展示优化”推进，例如移动端复盘阅读优化，或更多跨面板上下文联动。
