# 2026-06-09 Phase 7: 行动建议入口

## 本次目标

继续 Phase 7 玩法打磨,选择 roadmap 中最靠前的可独立验收小切片:更清晰的行动建议入口,让玩家从当前局势直接发起常见行动。

## 实现内容

- Web 右栏新增“行动建议”面板。
- 面板根据当前 `/api/state` 快照事实展示最多 4 个可点击入口:
  - 仔细观察
  - 询问在场者
  - 请教附近顾问
  - 梳理线索或查看出口
- 点击建议复用普通自然语言 `handleTurn`,仍由 GM Agent 决策。
- 补充 Playwright E2E 覆盖建议展示与点击发送。
- 新增 ADR-0021。

## 设计原则

- 不新增后端 API,继续复用 `/api/state`。
- 不做剧情优先级或规则裁决;代码只把已有事实转化为行动入口。
- 保持最小垂直切片,可由浏览器测试独立验收。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -q`
- 结果:20 passed。
- `.venv/bin/pytest tests/web/test_server.py tests/web/test_e2e_browser.py -q`
- 结果:41 passed。

## 下一步

继续 Phase 7 玩法打磨,优先选择“回放/复盘体验增强”作为下一项独立切片。
