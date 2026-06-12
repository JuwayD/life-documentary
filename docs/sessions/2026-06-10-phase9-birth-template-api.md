# 2026-06-10 Phase 9: 出生模板只读 API

## 本次目标

启动 Phase 9 测试与调试工具。按 ADR-0061 选择最小可独立验收切片：先提供出生模板预设、只读工具和 Web API，让后续“应用出生设置”和前端面板有稳定数据来源。

## 实现内容

- 新增 `data/birth_templates/default.yaml`，包含 4 个出生模板：
  - 落第书生：讼学/书法、50 文、府衙大堂开局。
  - 商人之子：商贸/口才、180 文、街市开局。
  - 武将后代：武艺/阵法、较高 HP/攻防、府衙院子开局。
  - 城中乞儿：市井/潜行、低钱物、高观察、街市开局。
- 新增 `mingrpg.tools.birth`：
  - `list_birth_templates` 返回模板摘要。
  - `get_birth_template` 返回完整模板，未知 ID 返回结构化错误。
- 工具注册表新增 `list_birth_templates` / `get_birth_template`，供 GM Agent 查询出生配置素材。
- Web API 新增：
  - `GET /api/birth/templates`
  - `GET /api/birth/templates/{template_id}`
- 补充单元测试与 Web API 测试。

## 设计原则

- 本切片只读取模板，不修改世界状态，避免半成品出生应用流程影响现有开局。
- 模板数据使用 YAML，与现有法条数据组织方式一致。
- 出生模板只提供属性、技能、物品、背景与初始位置；是否应用、何时重置世界留给后续独立切片。

## 测试

- `.venv/bin/pytest tests/tools/test_birth.py tests/web/test_server.py`

结果：27 passed，1 个既有 Starlette/httpx deprecation warning。

## 下一步

Phase 9 可继续实现：将出生模板应用到新游戏/重置流程，并在前端提供出生设置面板。
