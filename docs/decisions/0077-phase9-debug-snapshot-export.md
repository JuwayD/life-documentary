# ADR-0077: Phase 9 调试快照单个导出

## 状态

Accepted

## 背景

开发者控制台已经支持保存、筛选、排序、详情预览、差异预览和加载测试快照。但当需要把某个复现盘面单独发给他人或归档到 issue/测试记录时,只能依赖调试包整体导出或直接访问运行目录文件,不够聚焦。

## 决策

为测试快照增加单个 JSON 导出能力:

1. 新增 `GET /api/debug/test-snapshots/{id}/export` 返回指定快照内容。
2. 导出载荷保留原快照 `id/name/note/created_at/save`,并补充 `format: mingrpg.test-snapshot`、`version: 1`、`exported_at`。
3. 开发者控制台每条快照增加“导出”按钮,下载 `mingrpg-test-snapshot-<快照名>.json`。
4. 该切片只导出,不新增导入流程,避免扩大状态恢复入口。

## 后果

- 单个复现盘面可以独立分享和归档,比完整调试包更轻量。
- 不改变现有测试快照存储格式和加载流程。
- 后续如需跨环境导入测试快照,可在该导出格式上继续扩展。
