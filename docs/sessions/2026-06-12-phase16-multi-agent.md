# 2026-06-12 Phase 16: 多 Agent 协作

## 目标

从单 GM Agent 扩展到多 Agent 协作，引入战斗专家 Agent 处理复杂战斗场景。

## 变更

### 新增文件
- `src/mingrpg/llm/agents/__init__.py` — Agent 模块初始化
- `src/mingrpg/llm/agents/base.py` — AgentBase 抽象基类
- `src/mingrpg/llm/agents/combat.py` — CombatAgent 战斗专家
- `tests/llm/test_multi_agent.py` — 多 Agent 系统测试

### 修改文件
- `src/mingrpg/llm/tools_registry.py` — 添加 delegate_to_agent 工具
- `src/mingrpg/llm/agent.py` — 更新 GM Agent 系统提示词，添加委托工作流

## 架构设计

### AgentBase 抽象基类
- 定义统一接口: agent_id, get_system_prompt(), get_tools(), process()
- 所有专业 Agent 继承此类
- 共享 World 实例，确保状态一致性

### CombatAgent 战斗专家
- agent_id = "combat"
- 专用系统提示词: 战斗检定规则、伤害计算、状态管理
- 专用工具集: skill_check, roll_dice, apply_damage, add_status, tick_statuses
- LLM 驱动: 使用独立的 Anthropic 客户端处理战斗逻辑

### delegate_to_agent 工具
- GM Agent 可委托特定任务给专业 Agent
- 路由机制: 根据 agent_id 分发到对应 Agent
- 结果整合: 返回 narration + writes + combat_result

### GM Agent 委托工作流
- 系统提示词新增【多 Agent 协作】章节
- 工作流程第 4 步更新: 涉及战斗 → delegate_to_agent
- 简单战斗仍可自行处理，复杂场景才委托

## 测试结果

- 17 个多 Agent 测试全部通过
- 覆盖: AgentBase 抽象类、CombatAgent 工具注册、delegate_to_agent 集成、CombatAgent.process 模拟

## 决策

- 选择委托模式而非路由模式: GM 保持决策权，专业 Agent 只处理执行
- 战斗作为第一个专业 Agent: 战斗逻辑最复杂，最能体现多 Agent 价值
- 共享 World 实例: 避免状态同步问题，保持架构简单
- 简单战斗不委托: 避免过度工程化，只有复杂场景才需要专业 Agent
