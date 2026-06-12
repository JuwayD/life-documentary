# 2026-06-11 Phase 9 调试快照批量导出

## 本次目标

继续打磨 Phase 9 开发者控制台调试体验，实现最小切片: 调试快照批量导出。

## 完成内容

- 新增 `POST /api/debug/test-snapshots/bulk-export`
- 支持按 `snapshot_ids` 去重后导出完整测试快照包
- 导出格式为 `mingrpg.test-snapshot-bundle`，包内保留每个快照完整 `save`
- 开发者控制台测试快照批量操作区新增“导出所选”
- 批量导出复用筛选 + 选择当前列表工作流
- 补充 FastAPI 单元测试与 Playwright E2E 覆盖
- 新增 ADR-0082

## 验收方式

- 打开开发者控制台
- 创建多个测试快照
- 使用筛选定位一组快照
- 点击“选择当前列表”后点击“导出所选”
- 验证浏览器下载 `mingrpg-test-snapshot-bundle-*.json`
- 验证原快照仍保留在列表中
- 运行相关测试通过
