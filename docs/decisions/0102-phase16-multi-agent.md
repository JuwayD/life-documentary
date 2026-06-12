# ADR-0102: Phase 16 多 Agent 协作

## 状态

Accepted

## 背景

当前系统只有一个 GM Agent 处理所有事务：叙事、战斗、法律、社交等。随着游戏复杂度增加，单一 Agent 的系统提示词越来越长，战斗逻辑（攻击检定、伤害计算、状态管理）占用了大量提示词空间，且战斗场景需要精确的规则执行。

项目的核心原则是**代码不做决策**：代码是手脚，AI 是大脑。多 Agent 系统需要在不违反这一原则的前提下，提升专业化程度。

## 决策

引入**委托模式**的多 Agent 协作系统，GM Agent 保持决策权，可将特定任务委托给专业 Agent。

### 架构模式选择

考虑过三种模式：

| 模式 | 描述 | 优劣 |
|---|---|---|
| **路由模式** | 路由器决定哪个 Agent 处理整个回合 | GM 失去全局视角 |
| **委托模式** | GM 保持决策权，委托子任务给专业 Agent | ✅ 选择 |
| **管道模式** | 多个 Agent 依次处理 | 过于复杂 |

选择**委托模式**因为：
1. GM Agent 保持全局视角和最终决策权
2. 专业 Agent 只处理执行层任务，不做叙事决策
3. 与现有架构兼容，不破坏已有功能

### AgentBase 抽象基类

```python
class AgentBase(ABC):
    agent_id: str = ""

    def __init__(self, world: World):
        self.world = world

    @abstractmethod
    def get_system_prompt(self) -> str: ...

    @abstractmethod
    def get_tools(self) -> list[dict]: ...

    @abstractmethod
    def process(self, context: dict) -> dict: ...
```

所有专业 Agent 继承此类，共享 World 实例确保状态一致性。

### CombatAgent 战斗专家

第一个专业 Agent，处理复杂战斗场景：

- **agent_id**: `"combat"`
- **专用系统提示词**: 战斗检定规则、伤害计算、状态管理
- **专用工具集**: skill_check, roll_dice, apply_damage, add_status, tick_statuses
- **LLM 驱动**: 使用独立 Anthropic 客户端处理战斗逻辑

### delegate_to_agent 工具

GM Agent 的新工具，用于委托任务：

```json
{
  "name": "delegate_to_agent",
  "input_schema": {
    "properties": {
      "agent_id": {"type": "string", "description": "专业 Agent ID"},
      "context": {"type": "object", "description": "委托上下文"}
    }
  }
}
```

路由机制根据 `agent_id` 分发到对应 Agent。

### 委托工作流

GM Agent 系统提示词新增【多 Agent 协作】章节：

1. 涉及复杂战斗 → `delegate_to_agent(agent_id="combat", context={...})`
2. 接收结果后，将战斗专家的叙述融入最终输出
3. 战斗专家已执行的写操作不需要重复执行
4. 简单战斗（推搡、扇耳光）仍可自行处理

### 上下文传递

CombatAgent 接收的 context：
```python
{
    "attacker_id": "player",      # 攻击方 ID
    "defender_id": "bully",       # 防御方 ID
    "player_input": "我冲上去给赵三一拳",  # 原始输入
    "combat_state": {...}         # 可选附加状态
}
```

返回结果：
```python
{
    "narration": "赵三挥刀砍来...",      # 战斗描写
    "writes": [...],                     # 执行的写操作
    "combat_result": {                   # 结构化结果
        "attacker_hp": 100,
        "defender_hp": 45,
        "attacker_incapacitated": False,
        "defender_incapacitated": False
    }
}
```

## 后果

- 复杂战斗场景有专业处理，提升战斗质量和一致性
- GM Agent 提示词更精简，专注于叙事和全局决策
- 专业 Agent 可独立迭代，不影响 GM 核心逻辑
- 共享 World 实例避免状态同步问题
- 委托模式保持"代码不做决策"原则
- 简单场景不委托，避免过度工程化
