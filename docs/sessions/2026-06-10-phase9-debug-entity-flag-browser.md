# 2026-06-10 Phase 9: 开发者控制台实体/Flag 浏览

## 本次目标

按 Phase 9 roadmap 继续细化开发者控制台，实现“实体/flag 浏览与筛选”的最小可验收切片。

## 实现内容

- 后端 `GET /api/debug/console?limit=` 扩展返回：
  - `world.entities`：当前世界实体完整快照。
  - `world.flags`：当前 flag 字典。
- 前端开发者控制台新增“实体 / Flag 浏览”分区：
  - 实体列表显示名称、id、类型、位置、HP 和标签。
  - Flag 列表显示 key、概要和截断 JSON 预览。
  - 本地搜索框可筛选实体与 flag。
  - 筛选时显示匹配实体数/flag 数，无匹配时显示空状态。
- 样式沿用开发者控制台纸质卡片风格，并适配窄屏单列展示。

## 设计原则

- 控制台仍然只读，不提供修改世界或执行工具能力。
- 复用世界快照，不在后端增加规则判断。
- 搜索在前端完成，保持小切片闭环。
- Flag 内容只做截断预览，避免调试 UI 被大型 JSON 淹没。

## 测试

- `tests/web/test_server.py::test_debug_console_endpoint_returns_world_audit_and_performance`
- `tests/web/test_e2e_browser.py::test_debug_console_filters_entities_and_flags[chromium]`
- 相关全量：
  - `tests/web/test_server.py` 30 passed
  - `tests/web/test_e2e_browser.py` 61 passed

## 下一步

Phase 9 可继续推进“测试场景快照”，或在开发者控制台补充工具调用筛选。
