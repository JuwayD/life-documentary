# 2026-06-09 Phase 6 Step 7: 可分享存档

## 本次目标

按 roadmap 推进 Phase 6 可分享存档:让玩家能导出当前世界状态,并在另一会话导入恢复。

## 实现内容

- `World.export_save()` 导出带格式与版本号的完整世界 JSON。
- `World.import_save()` 校验格式/版本并替换当前世界数据。
- 新增 `GET /api/save` 导出存档。
- 新增 `POST /api/save/import` 导入存档并返回最新快照。
- Web 顶栏新增“导出存档 / 导入存档”按钮。
- 导出为本地 JSON 文件;导入 JSON 后刷新状态面板和渲染场景。
- 新增 World 与 Web API 覆盖测试。

## 设计原则

- 存档只保存数据层事实:entities / locations / events / flags / time。
- 代码不解释剧情含义,不判断哪些结局或任务有效。
- 使用本地 JSON 文件完成分享,不引入账号、云端或外部凭据依赖。

## 下一步

Phase 6 roadmap 项已全部完成,后续可进入新阶段规划或做玩法打磨。
