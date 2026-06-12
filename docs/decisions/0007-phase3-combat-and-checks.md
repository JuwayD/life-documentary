# ADR-0007: Phase 3 战斗与检定系统

- **状态**: Accepted
- **日期**: 2026-06-08
- **关联**: docs/04-roadmap.md (Phase 3)

## 背景

Phase 0/1/2 已完成三层架构、Web UI、3 场景 12 地点 13 实体、时辰/金钱/法条。现在按 roadmap 推进 Phase 3: "让'打'和'赌'有质感"。

## 决策

### 1. 不引入战斗状态机

继续贯彻 ADR-0001 "代码是手脚,AI 是大脑"原则。不创建 combat session 表、不写伤害公式、不区分"战斗中/非战斗中"状态。所有冲突都走同一套工具组合: skill_check → roll_dice → apply_damage → tick_statuses。LLM 负责判断时机、合理性、叙事。

### 2. 新增 3 个工具

- **skill_check** (util.py): 1d20 + attribute_value + modifier vs DC, 返回 success/margin/critical。纯函数,不动 world。自然 20 = 大成功(无视 DC),自然 1 = 大失败(无视 modifier)。advantage=True 时掷两次取高。

- **apply_damage** (write.py): 扣减 HP, clamp 到 0, 返回 incapacitated 标志。**不自动**添加"昏迷"/"死亡"状态 — 由 LLM 根据情境决定后续 add_status/log_event/query_laws。

- **tick_statuses** (write.py): 对全部实体或单个,decrement duration, auto-remove expired, damage_per_tick>0 的造成对应伤害。跳过 duration=-1 的永久效果。

### 3. 增强 add_status

兼容 `damage_per_tick` 和 `effect_type` 两个新字段,通过 `**extra` 接收。向后兼容,原有调用不受影响。

### 4. NPC 战斗属性

在所有 NPC 的 attributes 中补 attack/defense 值:
- 衙役/捕快: attack 4-5, defense 12-13, weapon_damage "1d6"
- 平民: attack 1-2, defense 8-9
- 玩家保持原有 str=10, dex=12, int=16, cha=13

### 5. 战斗法条

新增 `data/laws/04_combat.yaml` 5 条大明律·刑律:
- 斗殴杀人(绞监候)
- 持械伤人(杖八十徒二年)
- 误伤旁人(按斗殴论)
- 拒捕伤差(加二等,致伤绞)
- 威力制缚(绞,正当理由减等)

### 6. System Prompt 更新

新增约 30 行"战斗与检定"章节,覆盖:冲突进入条件、攻击检定流程、回合管理、持续状态用法、HP 归零处理、攻击方属性参考、优势/劣势规则。

## 不引入

- ❌ 装备系统(武器/护甲自动加属性)
- ❌ 主动技能
- ❌ AI 主动行为(NPC 自己掏刀)
- ❌ 战斗特殊地形
- ❌ 多目标 AOE
- ❌ 战斗 UI 特殊面板

## 后果

### 正面
- ✓ 25 个战斗单元测试,全过
- ✓ 119 总测试(原 97 + 22 新增),全过
- ✓ skill_check 让检定结果结构化、可审计
- ✓ tick_statuses 让持续效果真的会衰减并造成伤害
- ✓ 战斗法条让暴力行为有律例可依
- ✓ 不影响原有工具和场景数据,完全向后兼容

### 负面
- ✗ system prompt 增加约 30 行(~400 tokens)
  - **对策**: token 成本低,且战斗指引减少 LLM 临场发挥的不稳定性
- ✗ tick_statuses 中 apply_damage 会触发额外的 entity save/load
  - **对策**: 当前最多 13 实体,全部 tick 耗时 <1ms
