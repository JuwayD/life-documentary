# 技术方案

## 一、总体架构

```
┌─────────────────────────────────────────────────────┐
│                  Player Input                        │
│                  (自然语言)                          │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              GM Agent (Claude Sonnet)                │
│                                                      │
│   Loop:                                              │
│   1. 看到玩家输入和当前世界快照                       │
│   2. 决定要读什么 → 调用 read tools                  │
│   3. 思考 + 必要时检索法条/民俗                      │
│   4. 决定后果 → 调用 write tools                     │
│   5. 生成叙述返回玩家                                │
└──────────────────────┬──────────────────────────────┘
                       ↓ tool_use
┌─────────────────────────────────────────────────────┐
│                  Tool Layer                          │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ Read Tools │  │ Write Tools│  │ Util Tools   │  │
│  │ get_entity │  │ set_attr   │  │ roll_dice    │  │
│  │ query_laws │  │ move_entity│  │ calc_distance│  │
│  │ list_nearby│  │ add_status │  │ ...          │  │
│  │ ...        │  │ ...        │  │              │  │
│  └────────────┘  └────────────┘  └──────────────┘  │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              State Layer (SQLite + JSON)             │
│         entities | locations | events | flags        │
│       法条/民俗 TF-IDF 索引 (jieba + numpy, naïve)     │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│           Audit Log (JSONL, append-only)             │
│  每轮: input, snapshot, agent_trace, writes, output  │
└─────────────────────────────────────────────────────┘
```

## 二、关键模块职责

### 2.1 State Layer (世界状态)
- **职责**: 纯数据存储,无任何逻辑
- **实现**: SQLite (entities/locations/events/flags) + 法条 YAML
- **不允许**: 触发器、约束、存储过程
- **API**: 通过 Tool Layer 访问,不直接暴露给 GM Agent

### 2.2 Tool Layer (工具层)
- **职责**: 提供 GM Agent 调用的所有原子操作
- **实现**: Python 纯函数,接受参数,操作 State,返回 JSON
- **三类工具**:
  - **Read**: 读世界、查法条、列资源
  - **Write**: 改属性、移动、加状态、记录事件
  - **Util**: 掷骰、算距离、视线判断
- **绝对禁止**: 工具内部做任何"游戏规则"判断(如"血量不能为负")

### 2.3 GM Agent (游戏主持人)
- **职责**: 唯一的决策者
- **实现**: Claude Sonnet 4.6 + Tool Use,系统提示词约束其行为
- **关键约束** (写入 system prompt):
  - 调用 write 之前必须先调用相关 read 工具
  - 涉及法律/礼制的判定必须先查 `query_laws`
  - 必须给出叙述,叙述要符合明代语境
  - 重大后果(死亡、入狱)必须可逆地标记并日志

### 2.4 Audit Layer (审计层)
- **职责**: 记录一切以供回放和复盘
- **实现**: JSONL 追加写入 + 每轮快照
- **CLI 工具**: `review-log`、`replay-turn`、`diff-snapshot`

## 三、数据模型 (草案)

### Entity
```json
{
  "id": "zhifu_wang",
  "name": "王知府",
  "type": "npc",
  "location": "court_hall",
  "pos": [3, 7],
  "attributes": {
    "hp": 80, "max_hp": 80,
    "rank": "四品", "status": "在任",
    "reputation": 60
  },
  "status_effects": [],
  "inventory": [],
  "tags": ["official", "ming_dynasty", "yangzhou"]
}
```

### Location
```json
{
  "id": "court_hall",
  "name": "扬州府衙大堂",
  "type": "indoor_official",
  "size": [10, 10],
  "exits": {"south": "court_yard"},
  "tags": ["public", "official", "high_security"]
}
```

### Event (append-only)
```json
{
  "turn": 42,
  "timestamp": "万历十年秋八月辛卯 巳时",
  "actor": "player",
  "action_type": "attack",
  "summary": "玩家殴打王知府",
  "writes": [...]
}
```

### Law (YAML, RAG-indexed)
```yaml
- id: 大明律.刑律.斗殴.殴制使及本管长官
  category: 斗殴
  text: "凡杖殴本属知府、知州、知县者,杖一百,徒三年"
  applies_to: [violence, against_official]
  embedding: [pre-computed]
```

## 四、核心循环 (Pseudo-code)

```python
def game_turn(player_input: str) -> str:
    snapshot = world.snapshot()
    audit.start_turn(player_input, snapshot)
    
    # GM Agent 自主循环 (Claude Tool Use)
    response = claude.messages.create(
        model="claude-sonnet-4-6",
        system=GM_SYSTEM_PROMPT,
        tools=ALL_TOOLS,
        messages=[{
            "role": "user",
            "content": f"玩家输入: {player_input}\n\n当前快照: {snapshot}"
        }]
    )
    
    # Claude 自己决定调多少工具、调哪些
    while response.stop_reason == "tool_use":
        tool_results = execute_tools(response.content)  # 仅执行,不判断
        audit.record_tools(tool_results)
        response = claude.messages.create(..., previous=response, tool_results=tool_results)
    
    narration = extract_text(response)
    audit.end_turn(world.snapshot(), narration)
    return narration
```

## 五、技术风险与对策

| 风险 | 对策 |
|---|---|
| AI 调用工具失控(无限循环) | 设置每轮最大工具调用数 (e.g. 20),超出截断并要求收尾 |
| AI 写出不合理状态(hp=-9999) | 工具不阻止,但快照检测+日志告警,审计时人工标记 |
| 法条 RAG 检索不准 | TF-IDF + jieba 语义检索 + 关键词匹配混合模式兜底 (ADR-0101) |
| Claude API 延迟/成本 | 缓存常见场景、对话简短化、关键时刻才用大模型 |
| 状态不一致 (race condition) | 单线程游戏,无并发问题;每轮事务化写入 |
| 审计日志过大 | 按天分文件,旧文件压缩归档 |

## 六、暂不引入的复杂度

为保持 Phase 0 简洁,以下暂不做:

- ❌ 向量数据库 (用关键词检索代替)
- ❌ 多 Agent 协作 (只有一个 GM Agent)
- ✅ NPC 独立行动 → Phase 10 演化注册表机制 (ADR-0097)，AI 决策 NPC 行为
- ❌ 时间自动推进 (玩家每个动作推进时间)
- ❌ 渲染 (Phase 0 纯文字)
- ❌ 战斗系统的特殊化 (战斗也走通用 Action 流程)