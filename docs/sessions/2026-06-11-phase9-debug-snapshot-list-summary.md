# 2026-06-11 Phase 9 调试快照列表摘要

## 本次目标

继续打磨 Phase 9 开发者控制台调试体验,实现最小切片:调试快照列表摘要。

## 完成内容

- `GET /api/debug/test-snapshots` 新增 `summary`
- `summary` 展示快照总数、累计实体/地点/事件/Flag 数、最近更新时间
- `GET /api/debug/test-snapshots/export-index` 复用摘要并输出 `latest_updated_at`
- 开发者控制台测试快照区域顶部新增摘要条
- 补充 FastAPI 单元测试与 Playwright E2E 覆盖
- 新增 ADR-0080

## 验收方式

- 打开开发者控制台
- 保存至少一个测试快照
- 验证“测试场景快照”区域顶部显示总数、实体、地点、事件、Flags、最近更新
- 运行 `.venv/bin/pytest -q`,结果为 334 passed,4 skipped
