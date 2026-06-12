# 2026-06-11 Phase 9 调试快照索引导出

## 本次目标

继续打磨 Phase 9 开发者控制台调试体验,实现最小切片:调试快照索引导出。

## 完成内容

- 新增 `GET /api/debug/test-snapshots/export-index`
- 导出 `mingrpg.test-snapshot-index` JSON,包含快照数量、汇总计数和快照摘要列表
- 索引仅包含元数据与规模计数,不包含完整 `save` 内容
- 开发者控制台测试快照区域增加“导出索引”按钮
- 补充 FastAPI 单元测试与 Playwright E2E 覆盖
- 新增 ADR-0079

## 验收方式

- 打开开发者控制台
- 保存至少一个测试快照
- 点击“导出索引”
- 验证下载 `mingrpg-test-snapshot-index-*.json`,且页面出现“已导出 ... 个测试快照索引”提示
