# ADR-0080: Phase 9 调试快照列表摘要

## 状态

Accepted

## 背景

ADR-0079 已支持导出调试快照索引,但开发者控制台列表本身仍需要人工扫读每条快照,才能判断当前快照库规模、最近是否有更新、累计覆盖了多少实体/地点/事件/Flag。

## 决策

为调试快照列表增加轻量摘要:

1. `GET /api/debug/test-snapshots` 在 `snapshots` 外返回 `summary`。
2. `summary` 包含 `snapshot_count`、`latest_updated_at` 和累计 `totals`。
3. `GET /api/debug/test-snapshots/export-index` 复用同一摘要计算,额外输出 `latest_updated_at`。
4. 开发者控制台测试快照区域顶部展示总数、累计实体/地点/事件/Flag 与最近更新时间。

## 后果

- 打开控制台即可快速判断快照库规模与新鲜度。
- 摘要只复用已有快照元数据和计数,不读取或展示完整存档细节。
- 不改变快照保存、加载、导入、导出语义。
