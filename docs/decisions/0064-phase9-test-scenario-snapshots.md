# ADR-0064: Phase 9 测试场景快照

## 状态

已接受

## 背景

Phase 9 的目标是提供便捷的测试和调试工具。出生设置与开发者控制台已能帮助测试者快速切换身份、查看世界状态、审计工具调用，但在验证特定局面时仍需要手动重复铺垫剧情。Roadmap 中“测试场景快照”的下一项是保存/加载测试场景。

## 决策

在开发者控制台中加入测试场景快照的最小切片：

- 新增 `GET /api/debug/test-snapshots` 列出已保存快照。
- 新增 `POST /api/debug/test-snapshots` 将当前世界保存为命名测试快照。
- 新增 `POST /api/debug/test-snapshots/load` 按快照 id 恢复世界。
- 快照文件保存在运行目录下的 `test_snapshots/`，内容复用 `World.export_save()` 的完整世界存档，并附带名称、备注与创建时间。
- 前端开发者控制台新增“测试场景快照”分区，可输入名称/备注保存当前局面，并从列表加载快照。
- 新增 `GET /api/debug/test-presets` 与 `POST /api/debug/test-presets/load` 提供最小预设测试用例入口。
- 首批预设包含“府衙线索压力局”和“顾问同行观察局”，覆盖剧情/压力钟/时间线与队伍/观察/关系动态两类高频验证场景。

## 约束

- 快照接口只在调试命名空间下提供，定位为测试辅助工具。
- 不引入游戏规则判断；保存/加载复用现有 `export_save` / `import_save`。
- 本切片不实现删除快照，避免误删测试素材。
- 加载快照会覆盖当前世界状态；这是显式调试动作，不自动触发。
- 加载预设会先重置为默认种子世界，再应用固定调试状态，保证可重复验收。

## 后果

### 正面

- 测试者可以把某个复杂局面固定下来，重复验证 UI、工具和 LLM 行为。
- 出生设置、剧情 flag、队伍、线索和压力钟的组合状态更容易回归。
- 常用局面可以一键加载，减少手动铺垫剧情状态的重复劳动。

### 负面

- 运行目录会积累快照文件，需要后续再提供清理或删除能力。
- 快照是完整世界拷贝，不适合长期作为内容迁移格式；正式分享仍使用存档导出。
- 预设目前写在调试服务内，后续若数量增加可再迁移为数据文件。

## 测试

- `tests/web/test_server.py::test_debug_test_snapshots_save_list_and_load_current_world`
- `tests/web/test_server.py::test_debug_test_snapshots_reject_empty_name`
- `tests/web/test_server.py::test_debug_test_snapshots_load_404_for_unknown`
- `tests/web/test_e2e_browser.py::test_debug_console_saves_and_loads_test_snapshot`
- `tests/web/test_server.py::test_debug_test_presets_list_defaults`
- `tests/web/test_server.py::test_debug_test_preset_load_resets_and_applies_clue_pressure_state`
- `tests/web/test_server.py::test_debug_test_preset_load_applies_party_observation_state`
- `tests/web/test_server.py::test_debug_test_preset_load_404_for_unknown`
- `tests/web/test_e2e_browser.py::test_debug_console_loads_test_preset`
