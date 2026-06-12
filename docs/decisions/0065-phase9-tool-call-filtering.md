# ADR-0065: Phase 9 工具调用筛选

## 状态

已接受

## 背景

Phase 9 的开发者控制台已经提供世界状态查看器、实体/flag 浏览、工具调用日志、性能监控、测试快照和预设测试用例。随着工具数量和调试回合增加，单纯展示最近工具调用不足以快速定位某个工具或某类参数/结果。

## 决策

在开发者控制台中加入工具调用筛选的最小切片：

- `GET /api/debug/console` 增加可选查询参数：
  - `tool`：按工具名精确筛选。
  - `q`：按工具调用完整 JSON（turn/name/input/output）做文本筛选。
- 调试 API 返回 `tool_names`、`tool_filter`、`query`、`filtered_tool_count`，供前端展示筛选状态与匹配数量。
- 前端“工具调用日志”新增工具名下拉、内容搜索框、清空按钮与匹配数量摘要。
- 筛选只影响开发者控制台的工具调用列表，不改变审计日志文件和游戏世界状态。

## 约束

- 不新增规则判断；只读取并过滤已有审计轨迹。
- `tool` 使用精确匹配，避免模糊匹配造成误判。
- `q` 面向调试便利，使用当前 audit JSON 文本筛选，不引入查询 DSL。
- 保持 `/api/debug/*` 调试定位，不影响正式游玩接口。

## 后果

### 正面

- 测试者可以快速定位某个工具（如 `record_clue`、`discover_observation`）的调用。
- 可以按参数或输出内容检索，例如观察细节 id、线索文本、实体 id。
- 与测试快照/预设配合后，更容易验证复杂局面的工具链路。

### 负面

- 目前筛选范围仍限定在最近 `limit` 个审计回合内，不做全量日志检索。
- 内容筛选基于 JSON 文本，足够直观但不适合复杂结构化查询。

## 测试

- `tests/web/test_server.py::test_debug_console_endpoint_filters_tool_calls`
- `tests/web/test_e2e_browser.py::test_debug_console_filters_tool_calls`
