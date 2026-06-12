# ADR-0010: Phase 5B/C 剧情进度与压力钟

- **状态**: Accepted
- **日期**: 2026-06-09
- **关联**: docs/04-roadmap.md (Phase 5B/C)

## 背景

Phase 5A 已提供世界地点、NPC 日程与 rumor_hooks。Phase 5B 经济系统已让购买、雇佣能真实结算。下一步需要让主线与涌现支线能被持续追踪,但仍不能变成代码层任务状态机。

## 决策

### 1. 新增 record_clue 工具

`record_clue(thread_id, clue, source_entity, location_id, evidence_item)` 只做机械记录:

1. 将线索写入 `story_progress[thread_id].clues`。
2. 按线索文本去重。
3. 追加一条 `record_clue` 事件。

工具不判断线索是否真实、是否足够结案、是否完成任务;这些仍由 GM Agent 根据玩家行动、NPC 利益、近期事件、法律和掷骰决定。

### 2. 新增 advance_pressure_clock 工具

`advance_pressure_clock(clock_id, amount, reason, danger_at)` 记录叙事压力:

- 例如 `witness_pressure`、`official_patience`、`public_rumor`。
- 写入 `pressure_clocks[clock_id] = {value, danger_at}`。
- 返回 `danger_reached`,提示 GM 情势已到升级边缘。

代码不自动触发抓捕、证人失踪、NPC 变敌对等后果;只提供可审计的计数事实。

### 3. GM Agent 指引用法

- 发现事实/证词/证物时用 `record_clue`。
- 玩家行动导致局势升温时用 `advance_pressure_clock`。
- NPC 印象仍用 `add_memory`。
- 重大事实仍可用 `log_event` / `set_flag`。

## 不引入

- ❌ 任务完成条件判断
- ❌ 自动剧情分支状态机
- ❌ 固定任务 UI
- ❌ 自动 NPC 变更立场
- ❌ 自动生成奖励

## 后果

### 正面

- ✓ 主线/支线推进有持久化、可审计记录。
- ✓ GM Agent 能在后续回合读取已发现线索和压力钟。
- ✓ 仍遵守“代码是手脚,AI 是大脑”。

### 负面

- ✗ GM Agent 需要主动调用工具,否则线索仍可能只停留在叙述中。
  - **对策**: 系统提示词明确要求线索推进使用 `record_clue`,情势升温使用 `advance_pressure_clock`。
