# 2026-06-10 Phase 9: 测试场景快照

## 本次目标

按 Phase 9 roadmap 推进“测试场景快照”，实现保存/加载测试场景的最小可验收切片。

## 实现内容

- 后端新增调试快照 API：
  - `GET /api/debug/test-snapshots`：列出运行目录中的测试快照。
  - `POST /api/debug/test-snapshots`：保存当前世界为命名测试快照。
  - `POST /api/debug/test-snapshots/load`：按快照 id 恢复世界。
- 快照文件写入 `runtime/test_snapshots/`（测试中使用临时 audit/runtime 目录），内容包含：
  - `id` / `name` / `note` / `created_at`
  - `save`：复用 `World.export_save()` 的完整世界数据。
- 前端开发者控制台新增“测试场景快照”分区：
  - 输入名称和备注保存当前局面。
  - 展示快照列表、创建时间、实体/地点/事件/flag 数量。
  - 点击“加载”恢复快照并刷新右栏、渲染视口与控制台内容。
- 新增预设测试用例最小切片：
  - `GET /api/debug/test-presets`：列出预设测试用例。
  - `POST /api/debug/test-presets/load`：重置默认世界并加载指定预设局面。
  - 首批预设“府衙线索压力局”覆盖线索/压力钟/时间线验证。
  - 首批预设“顾问同行观察局”覆盖队伍/观察/关系动态验证。
  - 开发者控制台新增“预设测试用例”分区，可一键加载并刷新面板。

## 设计原则

- 保持最小垂直切片：快照不做删除，预设只做两组高频验收场景。
- 复用现有存档导入导出能力，不新增规则判断。
- 快照和预设都属于调试工具，挂在 `/api/debug/*` 命名空间下。
- 避免误删测试素材，快照只保存和加载。

## 测试

- `tests/web/test_server.py` 37 passed
- `tests/web/test_e2e_browser.py` 63 passed
- 新增覆盖：
  - `test_debug_test_snapshots_save_list_and_load_current_world`
  - `test_debug_test_snapshots_reject_empty_name`
  - `test_debug_test_snapshots_load_404_for_unknown`
  - `test_debug_console_saves_and_loads_test_snapshot`
  - `test_debug_test_presets_list_defaults`
  - `test_debug_test_preset_load_resets_and_applies_clue_pressure_state`
  - `test_debug_test_preset_load_applies_party_observation_state`
  - `test_debug_test_preset_load_404_for_unknown`
  - `test_debug_console_loads_test_preset`

## 下一步

Phase 9 可继续在开发者控制台补充工具调用筛选。
