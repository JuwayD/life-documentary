# 会话日志: 2026-06-08 Phase 3 — 战斗与检定系统

## 触发

按 roadmap 推进 Phase 3,为游戏加入回合制战斗框架和 D&D 风格技能检定。

## 决策

- **不引入战斗状态机**: 继续贯彻"代码是手脚,AI 是大脑",所有冲突走同一套工具组合
- **三工具正交**: skill_check(纯计算) + apply_damage(扣血) + tick_statuses(回合推进)
- **add_status 扩展**: 用 `**extra` 接收 damage_per_tick/effect_type,向后兼容
- **NPC 属性保守**: 衙役 attack 4-5 defense 12-13,平民 attack 1-2 defense 8-9
- **法条 5 条**: 斗殴杀人、持械伤人、误伤、拒捕、威力制缚

详见 `docs/decisions/0007-phase3-combat-and-checks.md`。

## 代码产出

### 工具层
- `tools/util.py`: 新增 `skill_check` (1d20+mod vs DC, 含自然20/1, advantage)
- `tools/write.py`: 新增 `apply_damage` (扣血+incapacitated标志), `tick_statuses` (duration衰减+damage_per_tick), 增强 `add_status` 支持 `**extra`

### 工具注册 & 审计
- `llm/tools_registry.py`: 注册 skill_check / apply_damage / tick_statuses, add_status schema 新增 damage_per_tick/effect_type
- `audit/logger.py`: WRITE_TOOL_NAMES 新增 apply_damage / tick_statuses

### 场景数据
- `scenarios/yangzhou_court.py`: guard_a/guard_b +attack/defense/weapon, zhifu_wang/shiye +基础属性
- `scenarios/yangzhou_market.py`: constable +attack/defense/weapon, 平民 +基础属性
- `scenarios/yangzhou_inn.py`: innkeeper/waiter/merchant +基础属性

### 法律数据
- `data/laws/04_combat.yaml` — 5 条大明律·刑律(人命+斗殴)

### GM Agent
- `llm/agent.py`: SYSTEM_PROMPT 新增"战斗与检定"章节(~30行),工作流程新增第4步和第8步

### 基础设施
- `core/world.py`: 新增 `list_entities()` 方法(支持 tick_statuses 遍历全部实体)

## 测试

| 类型 | 数量 | 新增 |
|---|---|---|
| 技能检定 (skill_check) | 8 | +8 |
| 伤害 (apply_damage) | 7 | +7 |
| 回合推进 (tick_statuses) | 8 | +8 |
| 状态增强 (add_status) | 2 | +2 |
| 场景战斗属性 | 4 | +4 |

**119 测试 (原 97 + 22 新增),全过。**

## 踩坑

- **tick_statuses 的 stale entity bug**: 第一版在循环内调用 apply_damage(会 save_entity),导致后续 status_effects 写入覆盖了 HP 变更。修复:先累加总伤害,apply_damage 一次,再 re-fetch entity 写 status_effects。
- **测试 fixture mutation bug**: `cw.get_entity("guard")["attributes"]["hp"] = 0` 这种链式写法改了 throwaway dict,不会持久化。修复:先赋值给变量,再 save。

## 下一步

Phase 4 候选:
- PixiJS 2.5D 等距瓦片渲染
- WebSocket 流式叙述
- NPC 日程系统
