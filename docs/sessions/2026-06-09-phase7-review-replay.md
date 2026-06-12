# 2026-06-09 Phase 7: 回放/复盘体验增强

## 本次目标

继续 Phase 7 玩法打磨,选择 roadmap 中最靠前的可独立验收小切片:回放/复盘体验增强。

## 实现内容

- Web 右栏新增“故事回顾”面板。
- 面板展示当前世界快照中的复盘指标:
  - 回合数
  - 线索数
  - 涉及 NPC 数
- 新增“查看完整回顾”按钮和复盘弹层。
- 弹层复用 `/api/audit?limit=50`,按时间顺序展示玩家输入与 GM 叙述。
- 补充 Playwright E2E 覆盖复盘面板与复盘弹层。
- 新增 ADR-0022。

## 设计原则

- 不新增后端 API,继续复用现有 `/api/state` 与 `/api/audit`。
- 不做剧情推理、优先级判断或规则裁决;只把已有事实重排成玩家可读回顾。
- 技术审计与玩家复盘分层:审计日志保留工具细节,故事回顾只展示叙事过程。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -q` → 22 passed
- `.venv/bin/pytest tests/web/test_server.py tests/web/test_e2e_browser.py -q` → 43 passed
- `.venv/bin/pytest -q` → 248 passed, 4 skipped

## 下一步

Phase 7 当前 roadmap 条目已全部完成,后续可继续追加打磨项,例如文本复盘导出或复盘筛选。
