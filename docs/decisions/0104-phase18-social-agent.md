# ADR-0104: 社交专家 Agent

## 状态

已接受

## 背景

Phase 16 引入了多 Agent 协作架构，目前只有 CombatAgent 一个专业 Agent。
社交互动（说服、欺骗、威吓、议价）是游戏核心玩法之一，但目前由 GM Agent 自行处理，
缺乏专业化的检定流程和 NPC 态度管理。

## 决策

新增 SocialAgent 作为第二个专业 Agent，处理社交与人际互动场景。

### 架构

- 继承 `AgentBase` 抽象基类
- `agent_id = "social"`
- 复用现有 `skill_check` / `add_memory` / `set_attribute` / `add_status` / `transfer_money` / `log_event` 工具
- 通过 `delegate_to_agent(agent_id="social", context={...})` 调用

### 支持的互动类型

| 类型 | 说明 | 主要属性 |
|------|------|----------|
| persuasion | 说服 | CHA |
| deception | 欺骗 | CHA |
| intimidation | 威吓 | STR/CHA |
| negotiation | 议价 | CHA |
| insight | 察言观色 | WIS |

### NPC 态度系统

- 态度值范围: -100（仇恨）到 +100（崇拜）
- 社交检定结果改变态度值：大成功 +15~+20，成功 +5~+10，失败 -5~-10，大失败 -15~-20

## 后果

- GM Agent 系统提示词已更新，增加社交 Agent 委托指引
- delegate_to_agent 工具描述已更新，支持 combat 和 social 两个 agent_id
- 测试从 516 增加到 535（+19 个 SocialAgent 测试）
