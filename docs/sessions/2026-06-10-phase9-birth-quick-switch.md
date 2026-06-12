# 2026-06-10 Phase 9: 出生配置快速切换

## 本次目标

继续 Phase 9 测试与调试工具，在已完成前端出生设置面板后，实现管理界面快速切换出生配置的最小可独立验收切片。

## 实现内容

- 出生设置弹层顶部新增“当前出生”管理区。
- 管理区读取 `flags.birth_setting.template_id`，展示当前应用的出生模板名称。
- 每个出生模板提供一个快速切换按钮。
- 当前模板按钮高亮。
- 点击快速切换按钮后直接调用 `POST /api/reset?template_id=<id>`：
  - 清空聊天。
  - 显示系统提示。
  - 按新身份/地点显示开场提示。
  - 刷新右栏状态面板与 Pixi 视口。
  - 关闭出生设置弹层。
- 补充 Playwright E2E 覆盖当前模板显示、高亮与一键切换到乞儿模板后的状态变化。

## 设计原则

- 快速切换复用既有 reset 模板参数，不新增并行的新游戏流程。
- 前端只展示和应用数据，不判断模板强弱或剧情适配性。
- 该切片服务测试/调试效率，避免引入自定义模板编辑器等更大范围工作。

## 测试

- `tests/web/test_e2e_browser.py::test_birth_settings_modal_applies_selected_template[chromium]`
- `tests/web/test_e2e_browser.py::test_birth_settings_quick_switch_applies_template[chromium]`

执行结果：2 passed, 57 deselected。

## 下一步

Phase 9 可继续推进开发者控制台：世界状态查看器、工具调用日志或性能监控面板。
