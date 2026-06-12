# ADR-0063: Phase 9 开发者控制台实体/Flag 浏览

## 状态

已接受

## 背景

ADR-0062 已提供开发者控制台最小切片，能查看世界概览、近期工具调用与轻量性能指标。Phase 9 roadmap 中“开发者控制台”的下一项是更细的实体/flag 浏览与筛选，用于在调试出生设置、剧情 flag、队伍、线索和压力钟时快速确认状态。

## 决策

在开发者控制台中扩展只读实体/Flag 浏览器：

- `GET /api/debug/console?limit=` 的 `world` 返回完整 `entities` 与 `flags` 快照。
- 前端控制台新增“实体 / Flag 浏览”分区。
- 实体列表展示名称、id、类型、位置、HP 与标签。
- Flag 列表展示 flag key、概要与截断 JSON 预览。
- 提供本地筛选输入框，可按实体 id/name/location/tag 或 flag key/content 过滤。
- 筛选后同步显示匹配实体数和 flag 数，并在无匹配时显示空状态。

## 约束

- 控制台保持只读，不提供修改实体、改 flag、删除日志或执行工具能力。
- 不新增游戏规则判断；后端只聚合已有快照字段。
- Flag JSON 预览在前端截断，避免大型 flag 影响弹层可读性。
- 筛选在前端完成，保持最小垂直切片，不引入额外查询 API。

## 后果

### 正面

- 测试者能在一个入口快速定位玩家/NPC 状态与关键剧情 flag。
- 出生模板、队伍、线索、压力钟等系统更容易被手动验证。
- 为后续工具调用筛选或测试场景快照提供调试基础。

### 负面

- 调试接口返回内容变多；当前世界规模较小，可接受。
- 前端渲染了截断 JSON，适合浏览但不是完整结构化编辑器。

## 测试

- `tests/web/test_server.py::test_debug_console_endpoint_returns_world_audit_and_performance`
- `tests/web/test_e2e_browser.py::test_debug_console_filters_entities_and_flags[chromium]`
