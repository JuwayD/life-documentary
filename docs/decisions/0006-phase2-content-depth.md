# ADR-0006: Phase 2 内容深度 — 多场景、时间系统、金钱交易

- **状态**: Accepted
- **日期**: 2026-06-08
- **关联**: docs/04-roadmap.md (Phase 2)

## 背景

Phase 0 (MVP CLI) 和 Phase 1 (Web UI) 已完成,但游戏只有 1 个场景(扬州府衙大堂)。原 roadmap 中 Phase 1 规划的"内容深度"(3 场景、5+ NPC、时辰系统、货币)被 Web UI 提前插入时搁置。现在补齐。

## 决策

### 1. 多场景通过 seed 函数组合

每个场景一个 seed 函数(如 `seed_yangzhou_court(world)`),场景之间通过 `exits` 字段自然连接。所有场景通过 `seed_all(world)` 一次性加载。

- **不引入场景加载器/场景管理器** — seed 函数是纯数据填充,World 只负责存储
- **出口连接在种子层处理** — `street_main` 的 `"south": "market_gate"` 出口由种子数据定义,AI 通过 `move_entity` 和 `get_location` 发现和使用

### 2. 时间系统: day_index 追踪

`world_time` JSON blob 新增 `day_index: int` 字段:
- `advance_time(units="day")` 直接增加 day_index
- `advance_time(units="shichen")` 从 亥时 绕回 子时 时自动 +1
- `_ensure_default_time()` 确保 `day_index: 0` 向后兼容

### 3. 金钱交易: transfer_money 工具

新增 `transfer_money(from_entity, to_entity, amount, reason)` 写工具:
- 纯机械操作:减法+加法,不判断交易公平性(AI 判断)
- 错误时返回 `{"error": ..., "suggestion": ...}` 而非抛异常
- 符合"代码是手脚,AI 是大脑"原则

### 4. 商业法条

新增 `data/laws/03_commerce.yaml` 5 条大明律·户律:
- 私充牙行埠头、把持行市、私造斛斗秤尺、匿税、违禁取利
- 不引入新代码 — `query_laws` 自动扫描 `data/laws/` 目录

### 5. 场景链可视化

前端新增面包屑式场景链指示器:
- 纯展示层,从 location 数据推导
- 不引入新的后端端点
- 高亮当前所在场景

## 不引入

- ❌ NPC 日程系统(Phase 4)
- ❌ 战斗系统(Phase 3)
- ❌ PixiJS 瓦片渲染(Phase 3)
- ❌ WebSocket 流式(后续)
- ❌ 存档/读档系统

## 后果

### 正面
- ✓ 3 场景 12 地点 13 实体,世界可探索
- ✓ 金钱系统让交易、贿赂、行赏成为可能
- ✓ 商业法条让市场行为有法可依
- ✓ 时间追踪支持昼夜循环和夜禁
- ✓ 97 测试(从 69 增长),全过

### 负面
- ✗ 多场景使 system prompt 更长(增加 ~300 tokens)
  - **对策**: prompt 增长在可接受范围内,且 token 成本低
- ✗ seed_all 每次重置重建全量世界,随着场景增多可能变慢
  - **对策**: 当前 12 个地点 13 个实体重建耗时 <1ms,远未到需要优化的地步
