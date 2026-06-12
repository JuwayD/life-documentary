# ADR-0018: Phase 6 可分享存档

## 状态

Accepted

## 背景

Phase 6 最后一项是可分享存档。玩家需要把当前世界状态导出为文件,发给他人后能恢复同一进度继续游玩。

## 决策

- 在 `World` 状态层新增 `export_save` / `import_save`。
- 存档采用 JSON 对象,带 `format=mingrpg.save` 与 `version=1`。
- 存档包含实体、地点、完整事件、flags 与世界时间。
- Web 层新增 `GET /api/save` 和 `POST /api/save/import`。
- 前端提供“导出存档 / 导入存档”按钮,导出本地 JSON,导入后刷新世界面板与场景。

## 后果

- 存档仍是纯数据搬运,不把剧情规则或胜负判断写进代码。
- 分享、备份、迁移进度不需要外部账号或服务。
- 后续若 schema 变化,可通过 `version` 增加迁移逻辑。
