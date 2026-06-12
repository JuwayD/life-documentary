# 2026-06-10 Phase 9: 出生模板应用

## 本次目标

继续 Phase 9 测试与调试工具。沿 ADR-0061 与上一切片的下一步，选择最小可独立验收内容：将已有出生模板真正应用到新游戏/测试重置流程。

## 实现内容

- `mingrpg.tools.birth` 新增 `apply_birth_template(world, template_id, entity_id="player")`：
  - 读取出生模板。
  - 覆盖玩家姓名、属性、物品、标签、初始地点与坐标。
  - 清空玩家状态效果，避免旧状态污染新出生。
  - 写入 `flags.birth_setting`，记录当前出生模板。
  - 追加 `birth_template_applied` 世界事件，便于审计与复盘。
- 工具注册表新增 `apply_birth_template`，供 GM Agent / 调试流程调用。
- Web API 新增：
  - `POST /api/birth/apply`：对当前世界应用出生模板。
  - `POST /api/reset?template_id=<id>`：重置世界后立即应用指定出生模板。
- 补充工具层与 Web API 测试，覆盖成功应用、未知模板错误、reset 带模板参数。
- 同步 README、roadmap、`.plan.md` 与 ADR-0061。

## 设计原则

- 代码只执行模板写入，不判断“哪个出身更适合剧情”。
- 出生模板应用作为测试/新游戏配置工具，保持可审计：flag + event 双记录。
- 暂不引入自定义模板编辑器，前端出生设置面板留给后续独立切片。

## 测试

- `.venv/bin/pytest tests/tools/test_birth.py tests/web/test_server.py`

结果：34 个相关测试 passed；全量测试 296 passed, 4 skipped，79 个既有 warning。

## 下一步

Phase 9 可继续实现前端出生设置面板：在 UI 中列出模板、预览属性/物品，并在新游戏重置时调用 `/api/reset?template_id=`。
