# ADR-0078: Phase 9 调试快照单个导入

## 状态

Accepted

## 背景

ADR-0077 已支持把单个测试快照导出为 `mingrpg.test-snapshot` JSON。为了让分享的复现盘面能直接在另一环境恢复,需要与导出格式配套的导入入口。

## 决策

为测试快照增加单个 JSON 导入能力:

1. 新增 `POST /api/debug/test-snapshots/import`,接收导出的 `mingrpg.test-snapshot` JSON。
2. 导入前校验 `format/version/save`,复用 `World.import_save` 恢复世界状态。
3. 开发者控制台测试快照区域增加“导入快照文件”按钮,选择 JSON 后导入并刷新世界、侧栏、视口和控制台。
4. 导入只恢复当前运行世界,不写入本地快照列表,避免自动持久化外部文件。

## 后果

- 单个复现盘面可以跨环境分享、导入和验证。
- 导入错误会以现有系统气泡反馈,不影响已有快照列表。
- 外部快照仍需人工选择文件,不会自动读取本地目录。
