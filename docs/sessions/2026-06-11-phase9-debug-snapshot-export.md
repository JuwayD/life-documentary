# 2026-06-11 Phase 9 调试快照单个导出

## 本次目标

继续打磨 Phase 9 开发者控制台调试体验,实现一个可独立验收的最小切片:测试快照单个导出。

## 完成内容

- 新增 `GET /api/debug/test-snapshots/{id}/export`
- 导出单个测试快照 JSON,包含原快照内容与 `format/version/exported_at` 元数据
- 开发者控制台快照列表增加“导出”按钮
- 点击后下载 `mingrpg-test-snapshot-<快照名>.json`
- 补充 FastAPI 单元测试与 Playwright E2E 覆盖
- 新增 ADR-0077

## 验收方式

- 打开开发者控制台
- 保存一个测试快照
- 点击该快照“导出”
- 验证浏览器下载单个 JSON 文件,文件名以 `mingrpg-test-snapshot-` 开头
- 验证页面出现“已导出测试快照”提示
