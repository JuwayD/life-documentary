# ADR-0105: 法律专家 Agent

## 状态

已接受

## 背景

Phase 16-18 建立了多 Agent 协作框架，包含战斗专家 (CombatAgent) 和社交专家 (SocialAgent)。法律事务是游戏中最复杂的领域之一——涉及法条检索、量刑分析、司法程序等多个环节，目前由 GM Agent 直接处理简单法律场景，但复杂案件（多条法条竞合、正式告状/辩护程序）需要更专业的处理。

## 决策

新增 LawAgent 作为第三个专业 Agent，专门处理法律事务。

### 设计要点

1. **agent_id**: `"law"`，继承 AgentBase
2. **工具集**: 5 个工具
   - `query_laws`: 法条检索（复用现有 read 工具，支持关键词+语义混合模式）
   - `log_event`: 记录法律事件（审讯、判决等）
   - `add_memory`: 为实体添加法律记忆
   - `set_attribute`: 修改属性（声望、通缉等级等）
   - `add_status`: 添加法律状态（imprisoned/wanted/on_trial）
3. **案件类型**: criminal(刑事)/civil(民事)/procedural(程序)/administrative(行政)
4. **上下文**: 支持 defendant_id、charges、legal_context(含 victim_id/witness_ids/evidence/severity)
5. **输出**: narration + writes + law_result(含 case_type、applicable_laws、defendant_id、player_id)
6. **法条提取**: 从 writes 中自动提取 query_laws 返回的适用法条，方便 GM 融入叙述

### 与现有 Agent 的区别

- CombatAgent: 5 个工具（战斗相关）
- SocialAgent: 6 个工具（社交相关，含金钱交易）
- LawAgent: 5 个工具（法律相关，含法条检索），无战斗/社交专属工具

### 委托触发条件

GM Agent 在以下场景委托 law agent:
- 复杂法律案件（多条法条竞合、需要量刑分析）
- 玩家告状、申诉、辩护等司法程序场景
- 需要系统性检索法条并给出专业法律意见
- 简单违法警告（如夜禁提醒）由 GM 自行处理

## 后果

- 多 Agent 系统扩展为 3 个专业 Agent
- GM Agent 系统提示词增加 law agent 委托指引和工作流步骤 3b
- delegate_to_agent 工具描述和上下文说明同步更新
- 测试数: 535 → 550 (+15 law agent 测试 + 2 delegate 集成测试)
